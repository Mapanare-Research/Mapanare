# Coroutine Design Document

> **Mapanare v4.67.0 — Arc 8 release 1.**
> This document is the single deliverable for v4.67.0. It specifies
> how `async fn` and `await` work in Mapanare, from user-visible
> semantics down to LLVM IR emission. Every subsequent coroutine
> release in arcs 8 and 9 (v4.68.0-v4.75.0) references specific
> sections of this document. Deviations from this design must be
> documented in the deviating release's SESSION_REPORT.md.
>
> **Author:** Juan Denis
> **Date:** 2026-04-12
> **Status:** APPROVED (Rattler sign-off)

---

## Table of Contents

1. [LLVM Coroutine Spec Summary](#1-llvm-coroutine-spec-summary)
2. [Existing State of Runtime Scheduler](#2-existing-state-of-runtime-scheduler)
3. [Mapanare's Target Async Semantics](#3-mapanares-target-async-semantics)
4. [Lowering Strategy](#4-lowering-strategy)
5. [Runtime Scheduler Extension](#5-runtime-scheduler-extension)
6. [Risk Register](#6-risk-register)
7. [Verification Plan](#7-verification-plan)
8. [Rejected Options](#8-rejected-options)

---

## 1. LLVM Coroutine Spec Summary

LLVM provides a coroutine infrastructure that transforms annotated
functions into state machines. A coroutine is an ordinary LLVM function
that uses coroutine intrinsics and carries the `presplitcoroutine`
function attribute. The LLVM middle-end coroutine passes transform this
single function into multiple functions: a **ramp function** (the
initial entrypoint, executing until the first suspend point), a
**resume function** (dispatches to the correct continuation after
resumption), and a **destroy function** (cleanup and deallocation).
Values that must persist across suspension points are moved into a
heap-allocated **coroutine frame**.

### 1.1 The Three Coroutine ABIs

LLVM supports three distinct coroutine ABIs:

**Switched-resume** (`llvm.coro.id`) is the primary ABI. The coroutine
frame stores resume and destroy function pointers at fixed offsets (0
and 8 on 64-bit), enabling generic code to resume or destroy any
coroutine handle without knowing the concrete type. A suspend index
(i8/i32) in the frame records which suspend point the coroutine is
paused at; the resume function uses a switch on this index to dispatch
to the correct continuation. This is the ABI used by C++ coroutines
(Clang's coroutine TS implementation) and is the ABI Mapanare will use.

**Returned-continuation/retcon** (`llvm.coro.id.retcon`) splits each
suspend point into a separate continuation function. Each suspension
returns a `{ptr, yielded_values...}` struct where the pointer is the
next continuation to call. Good for generators that yield values
directly. Not selected for Mapanare because it requires the caller to
manage a frame buffer and LLVM currently cannot elide heap allocations
as effectively as switched-resume after inlining.

**Async** (`llvm.coro.id.async`) stores the frame as a tail allocation
on a runtime-managed async context. Suspension is a tail-call to a
runtime suspend function. Used by Swift. Not selected because it
requires more frontend infrastructure and tighter runtime integration
than Mapanare needs for v4.x.

### 1.2 Key Intrinsics

The switched-resume ABI uses these intrinsics. Mapanare's emitter will
emit each of them directly as textual LLVM IR.

**Identity and frame management:**

| Intrinsic | Signature | Purpose |
|-----------|-----------|---------|
| `llvm.coro.id` | `(i32 align, ptr promise, ptr coroaddr, ptr fnaddrs) -> token` | Identifies the coroutine. One per function. |
| `llvm.coro.alloc` | `(token id) -> i1` | Returns true if dynamic allocation needed (false if HALO-elided). |
| `llvm.coro.size.i64` | `() -> i64` | Returns frame byte count (compile-time constant after CoroSplit). |
| `llvm.coro.begin` | `(token id, ptr mem) -> ptr` | Begins the coroutine, returns the frame handle. |
| `llvm.coro.free` | `(token id, ptr handle) -> ptr` | Returns frame pointer for freeing (null if stack-allocated). |

**Suspension and resumption:**

| Intrinsic | Signature | Purpose |
|-----------|-----------|---------|
| `llvm.coro.save` | `(ptr handle) -> token` | Marks the state-save point before a potential suspend. |
| `llvm.coro.suspend` | `(token save, i1 final) -> i8` | Suspends. Returns -1 (suspend), 0 (resume), or 1 (destroy). |
| `llvm.coro.end` | `(ptr handle, i1 unwind, token none) -> void` | Marks the end of the coroutine body. |

**Caller-side lifecycle:**

| Intrinsic | Signature | Purpose |
|-----------|-----------|---------|
| `llvm.coro.resume` | `(ptr handle) -> void` | Resumes a suspended coroutine. |
| `llvm.coro.destroy` | `(ptr handle) -> void` | Destroys a suspended coroutine (runs cleanup). |
| `llvm.coro.done` | `(ptr handle) -> i1` | Returns true if at final suspend point. |
| `llvm.coro.promise` | `(ptr handle, i32 align, i1 from) -> ptr` | Bidirectional handle <-> promise pointer conversion. |

### 1.3 The Coroutine Frame

After CoroSplit, the frame is a struct:

```llvm
%f.frame = type {
  ptr,    ; slot 0: @f.resume function pointer
  ptr,    ; slot 1: @f.destroy function pointer
  i8,     ; slot 2: suspend index (which suspend point)
  ...     ; slot 3+: spilled variables, promise (if any)
}
```

CoroSplit performs def-use chain analysis to find values whose
definitions and uses are separated by suspend points. These values are
"spilled" into frame slots. Allocas live across suspend points are
promoted into the frame (their alloca replaced with a GEP into the
frame struct). The suspend index is stored at each suspension and loaded
by the resume function's entry switch to dispatch to the correct
continuation block.

### 1.4 The Pass Pipeline

LLVM's new pass manager runs four coroutine passes in order:

1. **CoroEarlyPass** (module, early) — Lowers `coro.promise`,
   `coro.frame`, `coro.done` to GEP/load operations. Makes the IR safe
   for standard optimization passes that run before splitting.

2. **CoroSplitPass** (CGSCC, post-inlining) — The main pass. Analyzes
   spills, builds the frame struct, splits the function into ramp +
   resume + destroy. Replaces `coro.size` with the computed constant.
   Runs within the call-graph SCC pipeline so functions are processed
   bottom-up. Note: CoroSplit processes the coroutine twice — first
   pass lets standard optimizations reduce frame size, second pass
   performs the actual split.

3. **CoroElidePass** (function, late) — The HALO (Heap Allocation
   eLision Optimization). After inlining brings a coroutine's ramp
   into the caller, checks whether the handle doesn't escape and all
   paths include a destroy. If so, replaces `malloc` with `alloca` and
   devirtualizes resume/destroy into direct calls. This is the
   zero-overhead path for short-lived coroutines.

4. **CoroCleanupPass** (module, late) — Removes residual coroutine
   intrinsics not handled by earlier passes. Final cleanup.

### 1.5 The Canonical Pre-Split Pattern

This is the pattern Mapanare's emitter will produce for every `async fn`:

```llvm
define ptr @my_async_fn(...) presplitcoroutine {
entry:
  %id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
  %need = call i1 @llvm.coro.alloc(token %id)
  br i1 %need, label %alloc, label %begin

alloc:
  %size = call i64 @llvm.coro.size.i64()
  %mem = call ptr @malloc(i64 %size)
  br label %begin

begin:
  %phi = phi ptr [ null, %entry ], [ %mem, %alloc ]
  %hdl = call ptr @llvm.coro.begin(token %id, ptr %phi)
  ; ... function body with suspend points ...

cleanup:
  %mem.free = call ptr @llvm.coro.free(token %id, ptr %hdl)
  %need.free = icmp ne ptr %mem.free, null
  br i1 %need.free, label %free, label %suspend

free:
  call void @free(ptr %mem.free)
  br label %suspend

suspend:
  call void @llvm.coro.end(ptr %hdl, i1 false, token none)
  ret ptr %hdl
}
```

Each `await` point in the body produces:

```llvm
  %save = call token @llvm.coro.save(ptr %hdl)
  ; ... store the awaited future handle for the scheduler ...
  %susp = call i8 @llvm.coro.suspend(token %save, i1 false)
  switch i8 %susp, label %suspend [
    i8 0, label %resume.N
    i8 1, label %cleanup
  ]

resume.N:
  ; ... extract value from the now-ready future ...
```

---

## 2. Existing State of Runtime Scheduler

The Mapanare C runtime (`runtime/native/mapanare_runtime.c`) already has
a cooperative scheduler for agent execution. Understanding it is
essential because the coroutine scheduler will be built alongside it —
not replacing it.

### 2.1 Current Architecture

The cooperative scheduler (`mapanare_coop_scheduler_t`) is a circular
ready queue of agent pointers:

```c
typedef struct mapanare_coop_scheduler {
    mapanare_agent_t **ready_queue;   // circular buffer
    uint32_t           queue_cap;     // capacity (power of two)
    uint32_t           queue_head;    // write index
    uint32_t           queue_tail;    // read index
    uint32_t           max_steps;     // handler calls per tick (def 1000)
    mapanare_atomic_i32 running;      // 1 = running, 0 = stopped
} mapanare_coop_scheduler_t;
```

The API surface:
- `mapanare_coop_scheduler_init(sched, capacity)` — allocate queue
- `mapanare_coop_scheduler_enqueue(sched, agent)` — add an agent
- `mapanare_coop_scheduler_step(sched)` — run one tick: dequeue one
  agent, process up to `max_steps` messages, re-enqueue if not done
- `mapanare_coop_scheduler_run(sched)` — loop `step()` until all
  agents complete or `stop()` called
- `mapanare_coop_scheduler_stop(sched)` — signal the loop to exit
- `mapanare_coop_scheduler_destroy(sched)` — free queue

On mobile (`MAPANARE_DEFAULT_SCHED_COOPERATIVE == 1`), agents run
cooperatively on the calling thread via this scheduler. On desktop,
agents use thread-per-agent by default. The cooperative scheduler can
be used explicitly on any platform.

### 2.2 What the Scheduler Currently Does

Each step dequeues an agent, checks if it's paused (re-enqueues if so),
then drains up to `max_steps` messages from the agent's SPSC ring buffer
inbox. For each message: invokes the handler callback, tracks latency,
handles errors (restart policy: ignore, restart, or stop), and routes
output messages to the agent's outbox. If the agent is still running
after the tick, it's re-enqueued for the next round.

### 2.3 What It Lacks for Coroutines

The scheduler understands agents and messages. It does not understand:

- **Coroutine handles** — no slot for `ptr` handles from
  `llvm.coro.begin`. The scheduler tracks `mapanare_agent_t*`, not
  opaque coroutine frames.
- **Resume-at-yield** — the scheduler drains messages; it cannot call
  `llvm.coro.resume(ptr handle)` on a suspended coroutine.
- **Future readiness** — no mechanism to check whether a `Future<T>`
  is ready before resuming the coroutine that awaits it.
- **Coroutine cleanup** — no path to call `llvm.coro.destroy` when a
  coroutine completes or is cancelled.

Section 5 specifies the extension needed.

---

## 3. Mapanare's Target Async Semantics

This section defines what the user writes and what it means. Every
decision here is binding for v4.68.0 (grammar) through v4.75.0
(end-to-end).

### 3.1 `async fn` — Asynchronous Function Declaration

```mapanare
async fn fetch_data(url: String) -> String {
    let response = await http_get(url)
    return response.body
}
```

An `async fn` is a function that can suspend. Semantics:

- The declared return type `T` is sugar for `Future<T>`. Calling an
  `async fn` does **not** execute the body — it creates a suspended
  coroutine and returns a `Future<T>` handle immediately.
- The body executes when the returned future is driven by the scheduler
  (or explicitly by `await` from another async context).
- An `async fn` may contain zero or more `await` expressions.
- An `async fn` with zero `await` points is valid — it completes on
  first resume (single-step coroutine).
- `async fn` can call non-async functions freely. Non-async functions
  cannot use `await`.

### 3.2 `await expr` — Suspension Point

```mapanare
let result = await some_async_fn(args)
```

`await` suspends the current coroutine until the operand future is
ready. Semantics:

- The operand must have type `Future<U>`. Type error otherwise.
- If the future is already `Ready`, the value is extracted immediately
  without suspending.
- If the future is `Pending`, the current coroutine suspends. The
  scheduler will resume it when the awaited future becomes `Ready`.
- The expression evaluates to type `U`.
- `await` is only valid inside `async fn` bodies. Using `await` outside
  an async context is a semantic error (caught at type-check time, not
  parse time — the grammar accepts it everywhere but the semantic pass
  rejects it).

### 3.3 `Future<T>` — The Future Type

`Future<T>` is a new built-in generic type. It represents a value that
may not be available yet.

**States:**
- `Pending` (state = 0) — the coroutine has not yet produced a value.
  The coroutine handle is stored for the scheduler to resume.
- `Ready` (state = 1) — the value is available.

**Representation** (Decision 2 from PROMPT.md):

```llvm
%Future = type { i8, ptr }
; field 0: state (0 = Pending, 1 = Ready)
; field 1: payload pointer
;   - When Pending: ptr to the coroutine handle (for scheduler resume)
;   - When Ready: ptr to the result value (heap-allocated T)
```

The two-field `{i8, ptr}` representation was chosen over a three-state
`{i8, T}` inline representation for two reasons:

1. **Uniform size.** All `Future<T>` have the same LLVM type regardless
   of `T`. This simplifies the scheduler (one queue type) and avoids
   monomorphizing the scheduler per `T`.
2. **Handle reuse.** The `ptr` field serves double duty: coroutine
   handle when pending, result pointer when ready. No separate storage
   for the handle.

The cost is one heap allocation per future result. HALO elision
(CoroElide) will eliminate both the coroutine frame allocation and this
result allocation for short-lived futures whose lifetime is bounded by
the caller.

**User-visible operations on `Future<T>`:**
- `await future` — suspend until ready, extract `T`
- No explicit `.poll()`, `.cancel()`, or `.then()` in v4.x. The
  scheduler is the sole driver. Manual future manipulation is v5.x.

### 3.4 `async fn` vs Explicit `Future<T>` Return

**Decision 4 from PROMPT.md: both work.**

```mapanare
// Sugar form — coroutine lowering
async fn fetch(url: String) -> String { ... }

// Explicit form — no coroutine machinery, manual future construction
fn make_ready(x: Int) -> Future<Int> {
    return Future.ready(x)
}
```

`async fn foo() -> T` is sugar for a function that returns `Future<T>`
with coroutine lowering applied. A plain `fn` returning `Future<T>`
constructs the future manually — the body runs synchronously and returns
a future directly. The semantic pass distinguishes them: only `async fn`
bodies may contain `await`.

### 3.5 Interaction with Agents

Agents are Mapanare's actor-model concurrency primitive. Coroutines
extend agents, not replace them.

```mapanare
@agent
async fn data_processor(input: Stream<Bytes>) -> Stream<Result> {
    for await chunk in input {
        let processed = await transform(chunk)
        yield processed
    }
}
```

An agent handler can be `async`. When it is:
- The agent scheduler dequeues a message and passes it to the handler.
- The handler runs as a coroutine — it may `await` during message
  processing.
- While the handler is suspended, the cooperative scheduler can run
  other agents (the handler yields control at `await` points).
- When the awaited future resolves, the scheduler resumes the handler
  coroutine.
- The agent's message queue is **not** drained during suspension — one
  message at a time. The next message is dequeued only after the
  current handler invocation completes.

This is the key integration point. The cooperative scheduler's `step()`
function must be extended to handle the case where a handler suspends
(returns a coroutine handle) instead of completing synchronously.

### 3.6 Interaction with Streams

`Stream<T>` gains an async iteration protocol:

```mapanare
for await item in stream {
    // item: T
}
```

Desugars to:

```mapanare
loop {
    let next = await stream.next()
    match next {
        Some(item) => { /* loop body */ }
        None => break
    }
}
```

Where `stream.next()` is an `async fn` returning `Future<Option<T>>`.
The `for await` syntax is grammar sugar added at v4.74.0. The
underlying `stream.next()` method is available at v4.73.0.

### 3.7 Scope Boundaries

What is **in scope** for arcs 8+9 (v4.67.0-v4.76.0):
- `async fn` declaration and `await` expression
- `Future<T>` as a first-class type
- Cooperative inline scheduler (Option A)
- `for await` over streams
- Async agent handlers
- Basic cancellation (destroy the coroutine handle)

What is **out of scope** (v5.x):
- `async fn` in trait impls
- `Future` combinators (`join`, `select`, `race`)
- Background-thread scheduler (Option B)
- Event-driven scheduler with epoll/kqueue (Option C)
- Structured concurrency / nurseries
- Async closures
- `async` blocks (inline async without a named function)
- Cancellation tokens / cooperative cancellation protocol

---

## 4. Lowering Strategy

This is the largest and most critical section. It specifies exactly how
each construct lowers from AST through MIR to LLVM IR.

### 4.1 Pipeline Overview

```
.mn source
  -> Parser: async_fn_def -> AsyncFnDef AST node
  -> Parser: await_expr   -> AwaitExpr AST node
  -> Semantic: type-check async/await constraints
  -> Lowerer: AST -> MIR (new MIR instructions for coroutine ops)
  -> Emitter: MIR -> LLVM IR (emit coroutine intrinsics)
  -> LLVM opt: coro-early -> coro-split -> coro-elide -> coro-cleanup
  -> LLVM llc: machine code
```

### 4.2 Grammar Changes (v4.68.0)

Two new productions in `mapanare.lark`:

```lark
async_fn_def: "async" "fn" NAME "(" param_list? ")" ("->" type)? block
await_expr: "await" expr
```

`async` and `await` become keywords again (re-reserved from their
v4.30.0 soft-reserved status). The lexer re-adds `KW_ASYNC` and
`KW_AWAIT` terminals. Since v4.30.0 explicitly de-reserved them
(users could write `let async = 1`), the v4.68.0 CHANGELOG must note
this as a **breaking change** for any code using `async` or `await`
as identifiers.

### 4.3 AST Nodes (v4.68.0)

```python
@dataclass
class AsyncFnDef(Statement):
    name: str
    params: list[Param]
    return_type: TypeAnnotation | None  # T, not Future<T>
    body: Block
    span: Span

@dataclass
class AwaitExpr(Expression):
    expr: Expression   # must type-check to Future<U>
    span: Span
```

`AsyncFnDef` is structurally identical to `FnDef` plus an `is_async`
flag. Implementation choice: either a new node (cleaner for the semantic
pass) or a flag on `FnDef` (less duplication). **Decision: new node.**
The semantic pass needs to track "am I inside an async fn" context, and
a dedicated node makes the entry/exit points explicit.

### 4.4 Semantic Analysis (v4.69.0)

The semantic pass adds three checks:

1. **Async context tracking.** Enter async context when visiting
   `AsyncFnDef`. Exit on return. `AwaitExpr` outside async context
   produces error: `"await can only be used inside an async fn"`.

2. **Return type rewriting.** `AsyncFnDef` with declared return type
   `T` has its effective return type rewritten to `Future<T>`. If no
   return type is declared, it becomes `Future<Void>`.

3. **Await operand type check.** The operand of `AwaitExpr` must have
   type `Future<U>` for some `U`. The expression's type resolves to
   `U`. Any other operand type is an error: `"await requires a
   Future<T>, got <actual_type>"`.

### 4.5 MIR Extensions (v4.69.0-v4.70.0)

New MIR instruction kinds:

```python
class MIRInstructionKind(Enum):
    # ... existing kinds ...
    CORO_BEGIN = "coro_begin"       # Sets up coroutine frame
    CORO_SUSPEND = "coro_suspend"   # Suspension point
    CORO_END = "coro_end"           # Marks coroutine exit
    CORO_RESUME = "coro_resume"     # Resume a suspended coroutine (caller side)
    CORO_DESTROY = "coro_destroy"   # Destroy a coroutine (caller side)
    FUTURE_CREATE = "future_create" # Allocate Future<T>
    FUTURE_SET_READY = "future_set_ready"  # Mark future as Ready with value
    FUTURE_GET_VALUE = "future_get_value"  # Extract T from Ready future
    FUTURE_IS_READY = "future_is_ready"    # Check if future is Ready
```

The MIR stays target-independent — these instructions describe
coroutine semantics, not LLVM-specific intrinsics. The LLVM emitter
maps them to intrinsic calls; a hypothetical C backend would map them to
`setjmp`/`longjmp` or similar.

### 4.6 AST-to-MIR Lowering (v4.70.0 — the critical release)

#### 4.6.1 Lowering `AsyncFnDef`

An `async fn foo(x: Int) -> String` lowers to a MIR function with:

1. **Coroutine prelude** at function entry:
   - `CORO_BEGIN` instruction (MIR-level; emitter maps to
     `coro.id` + `coro.alloc` + `coro.begin`)
   - `FUTURE_CREATE` to allocate the `Future<String>` that will be
     returned to the caller

2. **Initial suspend** immediately after the prelude:
   - `CORO_SUSPEND` with `is_initial = true`
   - This is the point where the ramp function returns the future
     handle to the caller. The body doesn't execute until the
     scheduler resumes the coroutine.

3. **Function body** lowers normally. `await` expressions produce
   additional `CORO_SUSPEND` points.

4. **Return lowering** — `return value` in an async fn becomes:
   - `FUTURE_SET_READY` on the function's future with the return value
   - `CORO_END`
   - The actual LLVM `ret` returns the future handle (already returned
     by the ramp, but the coroutine needs a final suspend point)

5. **Final suspend** at the end:
   - `CORO_SUSPEND` with `is_final = true`
   - This keeps the coroutine frame alive until `coro.destroy` is
     called, allowing the caller to read the future's value

#### 4.6.2 Lowering `AwaitExpr`

`let result = await some_async_fn(args)` lowers to:

1. **Call the async function** — produces a `Future<U>` handle.

2. **Check readiness:**
   - `FUTURE_IS_READY` on the future
   - If ready, skip to step 5

3. **Register with scheduler:**
   - Store the awaited future handle into a scheduler-visible location
     (a field in the coroutine frame, accessed by the scheduler to
     check readiness before resuming)

4. **Suspend:**
   - `CORO_SUSPEND` with `is_initial = false, is_final = false`
   - The scheduler will resume this coroutine when the awaited future
     becomes Ready

5. **Extract value:**
   - `FUTURE_GET_VALUE` on the (now-ready) future
   - The result is the value of the `await` expression

#### 4.6.3 Lowering `for await`

`for await item in stream { body }` desugars in the lowerer to:

```
loop:
  %next_future = call stream.next()
  %is_ready = FUTURE_IS_READY %next_future
  br %is_ready, %check_option, %suspend_for_next

suspend_for_next:
  ; register %next_future with scheduler
  CORO_SUSPEND
  br %check_option

check_option:
  %option = FUTURE_GET_VALUE %next_future
  %is_some = ; check if Option is Some
  br %is_some, %body, %break

body:
  %item = ; extract value from Some
  ; ... user's loop body ...
  br %loop

break:
  ; exit loop
```

### 4.7 LLVM IR Emission (v4.70.0-v4.72.0)

The LLVM text emitter (`emit_llvm_text.py`) maps MIR coroutine
instructions to LLVM IR. This is the most mechanical part — a direct
translation.

#### 4.7.1 `CORO_BEGIN` Emission

```llvm
; Declarations (once per module, if any async fn exists)
declare token @llvm.coro.id(i32, ptr, ptr, ptr)
declare i1 @llvm.coro.alloc(token)
declare i64 @llvm.coro.size.i64()
declare ptr @llvm.coro.begin(token, ptr)
declare token @llvm.coro.save(ptr)
declare i8 @llvm.coro.suspend(token, i1)
declare void @llvm.coro.end(ptr, i1, token)
declare ptr @llvm.coro.free(token, ptr)
declare void @llvm.coro.resume(ptr)
declare void @llvm.coro.destroy(ptr)
declare i1 @llvm.coro.done(ptr)
declare ptr @llvm.coro.promise(ptr, i32, i1)

; Function attribute
define ptr @my_async_fn(i64 %x) presplitcoroutine {
entry:
  %id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
  %need.alloc = call i1 @llvm.coro.alloc(token %id)
  br i1 %need.alloc, label %coro.alloc, label %coro.begin

coro.alloc:
  %size = call i64 @llvm.coro.size.i64()
  %mem = call ptr @malloc(i64 %size)
  br label %coro.begin

coro.begin:
  %mem.phi = phi ptr [ null, %entry ], [ %mem, %coro.alloc ]
  %hdl = call ptr @llvm.coro.begin(token %id, ptr %mem.phi)

  ; Allocate the Future struct
  %future = call ptr @malloc(i64 16)       ; {i8 state, ptr payload}
  store i8 0, ptr %future                  ; state = Pending
  %handle.slot = getelementptr {i8, ptr}, ptr %future, i32 0, i32 1
  store ptr %hdl, ptr %handle.slot          ; payload = coroutine handle

  ; Initial suspend — return the future to the caller
  %init.save = call token @llvm.coro.save(ptr %hdl)
  %init.susp = call i8 @llvm.coro.suspend(token %init.save, i1 false)
  switch i8 %init.susp, label %coro.ret [
    i8 0, label %body.start
    i8 1, label %coro.cleanup
  ]

body.start:
  ; ... function body begins here ...
```

#### 4.7.2 `CORO_SUSPEND` Emission (for `await`)

```llvm
  ; ... evaluate the awaited expression, producing %awaited.future ...

  ; Check if already ready
  %state.ptr = getelementptr {i8, ptr}, ptr %awaited.future, i32 0, i32 0
  %state = load i8, ptr %state.ptr
  %is.ready = icmp eq i8 %state, 1
  br i1 %is.ready, label %await.ready.N, label %await.suspend.N

await.suspend.N:
  ; Store the awaited future handle for the scheduler
  ; (The scheduler reads this to know what we're waiting on)
  ; This is stored in the coroutine frame (survives suspend)
  %save.N = call token @llvm.coro.save(ptr %hdl)
  %susp.N = call i8 @llvm.coro.suspend(token %save.N, i1 false)
  switch i8 %susp.N, label %coro.ret [
    i8 0, label %await.ready.N
    i8 1, label %coro.cleanup
  ]

await.ready.N:
  ; Extract the value from the ready future
  %val.ptr = getelementptr {i8, ptr}, ptr %awaited.future, i32 0, i32 1
  %val = load ptr, ptr %val.ptr
  ; ... %val is the result of the await expression ...
```

#### 4.7.3 `CORO_END` Emission

```llvm
  ; ... return value lowering ...

  ; Set the function's own future to Ready with the return value
  %ret.ptr = call ptr @malloc(i64 ...)      ; allocate T
  store ... %return.value, ptr %ret.ptr      ; store the value
  store i8 1, ptr %future                    ; state = Ready
  %payload.slot = getelementptr {i8, ptr}, ptr %future, i32 0, i32 1
  store ptr %ret.ptr, ptr %payload.slot      ; payload = result ptr

  ; Final suspend — keep frame alive for value extraction
  %final.save = call token @llvm.coro.save(ptr %hdl)
  %final.susp = call i8 @llvm.coro.suspend(token %final.save, i1 true)
  switch i8 %final.susp, label %coro.ret [
    i8 0, label %coro.ret        ; resuming after final suspend is UB
    i8 1, label %coro.cleanup
  ]

coro.cleanup:
  %mem.to.free = call ptr @llvm.coro.free(token %id, ptr %hdl)
  %need.free = icmp ne ptr %mem.to.free, null
  br i1 %need.free, label %coro.free, label %coro.ret

coro.free:
  call void @free(ptr %mem.to.free)
  br label %coro.ret

coro.ret:
  call void @llvm.coro.end(ptr %hdl, i1 false, token none)
  ret ptr %future
```

### 4.8 Pass Pipeline Placement (Decision 3)

**Decision: add coroutine passes as explicit arguments to `opt`.**

Mapanare currently invokes `opt` on the emitted `.ll` file. When any
`async fn` is present in the module (detected by the emitter via the
`presplitcoroutine` attribute), the opt invocation changes from:

```bash
opt -O1 input.ll -o output.ll
```

to:

```bash
opt -passes='coro-early,function(coro-elide),cgscc(coro-split),coro-cleanup,default<O1>' input.ll -o output.ll
```

Wait — the ordering matters. LLVM's default `-O1` pipeline already
includes the coroutine passes in the correct positions. The correct
approach is:

**Use `-O1` (or higher). The coroutine passes are built into the
standard pipeline at `-O1`+.** At `-O0`, CoroSplit still runs (it is
required for correctness) but CoroElide is skipped.

Mapanare currently uses `-O0` for debug builds and `-O1` for release
builds. This means:

- **Debug builds (`-O0`):** Coroutines work (CoroSplit runs) but no
  HALO elision. Every coroutine frame is heap-allocated. Acceptable
  for debugging.
- **Release builds (`-O1`):** Full pipeline including HALO. Short-lived
  coroutines are stack-allocated.

**No explicit pass arguments needed.** The `presplitcoroutine`
attribute is sufficient for LLVM to recognize the function as a
coroutine and apply the correct passes. This is the simplest correct
approach.

If Mapanare later uses `llc` directly (bypassing `opt`), then explicit
pass arguments would be needed. Document this as a future concern.

### 4.9 Interaction with Drop Glue

A coroutine's frame may hold references to heap-allocated values
(strings, lists, maps) that must be freed when the coroutine is
destroyed. The cleanup path (`coro.cleanup` label in §4.7.3) is where
drop glue runs.

**Strategy:**

1. The emitter tracks which allocas in the function body hold
   heap-allocated types (strings, lists, maps, nested structs with
   heap fields).

2. In the `coro.cleanup` block, before `coro.free`, emit the same
   drop-glue calls that a non-async function would emit at its
   return site.

3. LLVM's CoroSplit will analyze which of these values are live at each
   suspend point. Only values actually live at the destruction point
   need cleanup; dead values have already been freed on the normal
   path.

4. For values that are conditionally initialized (only allocated on
   some paths), use a boolean flag in the frame to track whether
   cleanup is needed. This is the same pattern used by Clang for C++
   coroutine exception cleanup.

**Risk:** The drop-glue interaction is the most likely source of bugs.
v4.72.0 (lowering pt 2) should include specific tests for:
- Coroutine that allocates a string, suspends, then returns — string
  must be freed on destroy
- Coroutine that allocates a string before suspend and another after —
  destroy cleans up only the appropriate ones based on which suspend
  point was active

### 4.10 Self-Hosted Compiler Implications

The self-hosted compiler (`mapanare/self/`) will need matching changes:

- `lexer.mn` — re-add `async` and `await` as keyword tokens
- `parser.mn` — `async_fn_def` and `await_expr` productions
- `semantic.mn` — async context tracking, await type checking
- `lower.mn` / `lower_state.mn` — MIR coroutine instruction emission
- `emit_llvm.mn` — LLVM coroutine intrinsic text generation

These changes track the Python bootstrap but are not required to be
simultaneous. The self-hosted compiler can lag by 1-2 releases. Per the
dual-closure convention in `CARRY_FORWARD.md`, each feature must
eventually be closed on both sides.

---

## 5. Runtime Scheduler Extension

### 5.1 Design Goal

Extend the C runtime to drive coroutines alongside agents. The new API
must:
- Register coroutine handles for scheduling
- Poll awaited futures for readiness
- Resume ready coroutines via `llvm.coro.resume`
- Destroy completed coroutines via `llvm.coro.destroy`
- Coexist with the existing agent cooperative scheduler

### 5.2 Scheduler Model (Decision 1)

**Option A: inline in main.** After `main()` body completes, enter a
scheduler loop that drains all pending coroutines.

This is the chosen model for v4.67.0-v4.75.0. Rationale:

- **Simplest.** One thread. No synchronization. No condition variables.
  No thread pool.
- **Correct.** Cooperative scheduling matches the agent scheduler's
  existing model. Adding a background thread (Option B) or event loop
  (Option C) introduces thread-safety concerns throughout the runtime.
- **Sufficient.** Coroutines in Mapanare are primarily for expressing
  concurrent structure (agent handlers that await I/O results), not for
  parallelism. CPU-bound work uses agents with thread-per-agent. I/O
  waiting uses coroutine suspension.
- **Extensible.** Option A's API (`register`, `step`, `run`) maps
  directly to Option B or C when those are needed — the caller-side
  code changes, but the coroutine registration API stays the same.

Options B and C are deferred to v5.x. See Section 8 for the full
rejected-options analysis.

### 5.3 New C Runtime API

```c
/* ---- Coroutine Scheduler (v4.73.0) ---- */

typedef struct mapanare_coro_entry {
    void *handle;              /* coroutine handle (ptr from coro.begin) */
    void *awaited_future;      /* Future being awaited, or NULL          */
} mapanare_coro_entry_t;

typedef struct mapanare_coro_scheduler {
    mapanare_coro_entry_t *entries;  /* dynamic array of registered coros */
    uint32_t               count;   /* number of active entries          */
    uint32_t               cap;     /* allocated capacity                */
    mapanare_atomic_i32    running; /* 1 = running, 0 = stopped          */
} mapanare_coro_scheduler_t;

/* Initialize the coroutine scheduler. */
void mapanare_coro_scheduler_init(mapanare_coro_scheduler_t *sched,
                                   uint32_t initial_cap);

/* Register a coroutine handle for scheduling.
 * Called by the ramp function after the initial suspend. */
void mapanare_coro_scheduler_register(mapanare_coro_scheduler_t *sched,
                                       void *handle);

/* Set the future that a coroutine is waiting on.
 * Called before each coro.suspend in the await path. */
void mapanare_coro_scheduler_set_awaited(mapanare_coro_scheduler_t *sched,
                                          void *handle, void *future);

/* Run one scheduling tick:
 * - For each registered coroutine whose awaited future is Ready (or NULL):
 *   call llvm.coro.resume on its handle.
 * - Remove coroutines that are done (llvm.coro.done returns true).
 * - Call llvm.coro.destroy on done coroutines.
 * Returns the number of coroutines still active. */
uint32_t mapanare_coro_scheduler_step(mapanare_coro_scheduler_t *sched);

/* Run until all coroutines complete or stop is called. */
int mapanare_coro_scheduler_run(mapanare_coro_scheduler_t *sched);

/* Signal the scheduler to stop. */
void mapanare_coro_scheduler_stop(mapanare_coro_scheduler_t *sched);

/* Destroy the scheduler (frees entry array). */
void mapanare_coro_scheduler_destroy(mapanare_coro_scheduler_t *sched);
```

### 5.4 Scheduler Step Algorithm

```
for each entry in entries:
    if entry.awaited_future != NULL:
        future_state = *(i8*)entry.awaited_future
        if future_state != 1:    // not Ready
            continue             // skip — still waiting
    // Future is ready (or no future — initial resume)
    llvm.coro.resume(entry.handle)
    if llvm.coro.done(entry.handle):
        llvm.coro.destroy(entry.handle)
        remove entry from array
```

The step function is O(n) in the number of active coroutines. For v4.x
volumes (tens to hundreds of coroutines), this is fine. A priority queue
or event-driven wakeup (Option C) would be needed for thousands of
concurrent coroutines — that's v5.x.

### 5.5 Integration with Agent Scheduler

When both agents and coroutines are active, `main()` epilogue runs:

```c
// After main() body completes:
while (coop_queue_size(&agent_sched) > 0 ||
       coro_sched.count > 0) {
    mapanare_coop_scheduler_step(&agent_sched);
    mapanare_coro_scheduler_step(&coro_sched);
}
```

The two schedulers alternate steps. An agent handler that suspends
(because it's an `async` handler that hits an `await`) registers a
coroutine entry in the coroutine scheduler. The agent scheduler sees
the handler as "in progress" and doesn't dequeue another message for
that agent until the coroutine completes.

### 5.6 Emitted Scheduler Bootstrap

The LLVM emitter inserts scheduler initialization at the start of
`main()` and the drain loop at the end, but **only if** the module
contains at least one `async fn`:

```llvm
define i64 @main() {
entry:
  ; ... scheduler init (only if async fns present) ...
  call void @mapanare_coro_scheduler_init(ptr @__mn_coro_sched, i32 64)

  ; ... user's main() body ...

  ; ... scheduler drain loop (only if async fns present) ...
  br label %sched.loop

sched.loop:
  %remaining = call i32 @mapanare_coro_scheduler_step(ptr @__mn_coro_sched)
  %done = icmp eq i32 %remaining, 0
  br i1 %done, label %sched.done, label %sched.loop

sched.done:
  call void @mapanare_coro_scheduler_destroy(ptr @__mn_coro_sched)
  ret i64 0
}
```

The `@__mn_coro_sched` global is emitted as a zero-initialized global
struct when async functions are present.

---

## 6. Risk Register

### 6.1 Debug Info for Coroutines — HIGH risk, DEFERRED

LLVM's coroutine passes rewrite the function structure, which can
invalidate debug info metadata. After CoroSplit, the resume function is
a new function with a switch at entry — DWARF line tables don't map
cleanly to the original source.

Clang handles this by emitting `DISubprogram` nodes for the split
functions and using `DW_TAG_label` for resume points. This is complex
and was only stabilized in Clang 16+.

**Decision: debug info for async fns is v5.x.** In v4.67.0-v4.75.0,
debug info is emitted pre-coro-split. Whatever survives the split
survives. Users debugging async code will see degraded DWARF output
(missing line numbers after suspend points, possibly incorrect variable
locations). This is documented in the `-g` output and in the cookbook.

**Mitigation:** Arc 7 (v4.62.0-v4.65.0) shipped robust DWARF for
synchronous functions. The baseline is solid. Async debug info builds on
it incrementally in v5.x, not as a blocker for shipping async/await.

### 6.2 Recursive Async Functions — MEDIUM risk, DOCUMENTED

An `async fn` that `await`s itself (or a cycle of async fns) will
allocate one coroutine frame per recursion level. Unlike stack recursion
(where the OS provides a large pre-allocated stack), each frame is a
separate `malloc`. Deep recursion will exhaust heap memory.

**Decision: document but don't fix in v4.x.** Recursive async functions
are uncommon in practice. The behavior is well-defined (malloc
eventually returns NULL, causing a crash) and matches what Rust, C++,
and Swift do. A stack-depth limit or trampoline optimization is v5.x.

### 6.3 Exception Safety — LOW risk, N/A

Mapanare has no exceptions. The error model is `Result<T, E>`. The
`coro.end` second parameter (`i1 %unwind`) is always `false`. The
cleanup path in `coro.cleanup` handles normal destruction only. No
exception tables, no landing pads, no personality functions needed.

This is a significant simplification compared to C++ coroutine
lowering.

### 6.4 Generic Async Functions — MEDIUM risk, PLANNED

`async fn foo<T>(x: T) -> T` monomorphizes at compile time. Each
specialization gets its own coroutine with its own frame layout. This is
the same as non-async generics — no special handling needed beyond
ensuring the monomorphizer runs before coroutine lowering.

**Risk:** Frame sizes vary per specialization. A generic async function
instantiated with a large struct `T` will have a proportionally larger
frame. Document in the user guide.

### 6.5 Async Agent Handlers — HIGH risk, CRITICAL PATH

The agent scheduler and coroutine scheduler must coexist. The critical
interaction is: what happens when an agent handler suspends?

**Risk scenario:**
1. Agent A dequeues message M and calls its `async` handler.
2. The handler hits `await` and suspends.
3. The agent scheduler's `step()` returns — it thinks the handler is
   "done" (the function returned a value).
4. The scheduler dequeues the next message and calls the handler again.
5. Now two coroutine instances of the same handler are in flight — data
   race on agent state.

**Mitigation:** The agent scheduler must distinguish between "handler
completed" and "handler suspended." When a handler is async, `step()`
must:
- Check if the handler returned a coroutine handle (not a final result)
- If so, register the coroutine with the coroutine scheduler
- Mark the agent as "handler-in-flight" — do not dequeue another
  message until the coroutine completes
- When the coroutine completes, clear the "handler-in-flight" flag

This requires a new field on `mapanare_agent_t`:

```c
void *pending_coro_handle;  /* non-NULL if async handler is suspended */
```

The step function checks this field before dequeuing.

### 6.6 HALO Elision Reliability — LOW risk

LLVM's CoroElide (HALO) is sensitive to escape analysis. If the
coroutine handle escapes the calling function (stored to a global,
passed to an opaque function), HALO is defeated. Mapanare's `Future<T>`
struct stores the handle, which the scheduler reads — this is an escape.

**Implication:** For coroutines registered with the scheduler, HALO will
**not** fire. Every such coroutine frame is heap-allocated. HALO only
fires for short-lived coroutines that are `await`ed immediately without
going through the scheduler — e.g., `let x = await foo()` where `foo()`
is inlined.

This is acceptable. The heap allocation cost is amortized across the
coroutine's lifetime. Document as a known limitation.

---

## 7. Verification Plan

Each release in arcs 8+9 has specific verification criteria. The
DESIGN.md locks these so they're pre-committed, not invented at
ship time.

| Release | What ships | Verification |
|---------|-----------|--------------|
| **v4.68.0** | Grammar + AST + parser | Parse tests: `async fn foo() -> Int { await bar() }` parses. Lowering attempt: produces `"async fn lowering not yet implemented"` error (not a crash, not a silent pass-through). |
| **v4.69.0** | Semantic analysis | Type check tests: `await` outside `async fn` → error. `await non_future` → error. `async fn` return type → `Future<T>`. 10+ pytest cases. |
| **v4.70.0** | MIR lowering pt 1 | IR emission tests: `async fn` produces `presplitcoroutine` attribute, `llvm.coro.id` call, `llvm.coro.begin` call, `llvm.coro.suspend` call. `llvm-as` validates the IR. Golden test `48_async_basic.mn`. |
| **v4.71.0** | Arc 8 panel | Panel grades v4.68.0-v4.70.0. Zero new features. |
| **v4.72.0** | MIR lowering pt 2 | Complete coroutine IR: `coro.end`, cleanup block, `coro.free`. `opt -O1` runs without error. Golden test `49_async_await.mn` with two suspend points. |
| **v4.73.0** | Runtime scheduler | `mapanare_coro_scheduler_*` functions compiled and linked. Minimal test: `async fn delay() { }; let f = delay(); await f` completes without crashing. Golden test `50_async_scheduler.mn`. |
| **v4.74.0** | `for await` + streams | `for await item in stream { ... }` desugars correctly. Golden test `51_async_stream.mn`. Delta review mandatory (new syntax). |
| **v4.75.0** | End-to-end + polish | Golden test `52_async_agents.mn` (async agent handler). Golden test `53_real_await.mn` (multiple suspension points, scheduler drives to completion). Culebra clean on all async golden tests. |
| **v4.76.0** | Arc 9 panel | Panel grades v4.72.0-v4.75.0. Zero new features. |

**Golden test numbering:** 48-53 are reserved for coroutine tests. The
current corpus ends at 47 (or wherever the latest golden test is).

---

## 8. Rejected Options

### 8.1 Green Threads (Stack-Switching)

Green threads provide cooperative concurrency by switching between
pre-allocated stacks. Languages like Go use this model. Rejected
because:

- **Stack sizing is hard.** Each green thread needs a stack (typically
  4KB-8KB initial, growing on demand). Mapanare would need to implement
  segmented stacks or stack copying — complex runtime infrastructure
  that LLVM coroutines avoid entirely.
- **Platform portability.** Stack switching requires platform-specific
  assembly (`makecontext`/`swapcontext` on POSIX, fibers on Windows,
  nothing portable on WASM). LLVM coroutines produce standard LLVM IR
  that works on every LLVM target.
- **WASM incompatibility.** WebAssembly has no stack-switching primitive.
  Green threads on WASM require Asyncify or stack-switching proposal
  (not yet standardized). LLVM coroutines can target WASM via the
  standard state-machine transformation.

### 8.2 Manual State-Machine Generation (No LLVM Coroutines)

Generate the resume/suspend state machine in Mapanare's emitter instead
of relying on LLVM's CoroSplit pass. Rejected because:

- **Re-deriving CoroSplit.** LLVM's coroutine passes handle spill
  analysis, frame layout, HALO elision, and interaction with the
  optimization pipeline. Reimplementing this is thousands of lines of
  non-trivial code with subtle correctness requirements.
- **Optimization interaction.** LLVM's passes are designed to interleave
  with the optimization pipeline (CoroSplit runs between inlining
  passes). A hand-generated state machine would be opaque to the
  optimizer.
- **Maintenance burden.** LLVM's coroutine infrastructure is maintained
  by the LLVM community. A custom implementation would be maintained
  by the Mapanare team alone.

### 8.3 CPS Transformation

Transform every `await` into a continuation-passing style: each
suspension point becomes a new function that receives the result as a
parameter. Rejected because:

- **Worse codegen.** CPS creates many small functions with indirect
  calls. LLVM's coroutine passes produce fewer functions with direct
  control flow and enable HALO.
- **Type complexity.** Each continuation has a different type (it
  captures a different set of local variables). This complicates the
  type system and MIR representation.
- **Debugging.** CPS transforms destroy the original function structure.
  LLVM coroutines preserve it (the pre-split IR looks like the original
  function; the post-split IR has clear correspondences).

### 8.4 Poll-Based Futures (Rust-Style)

Rust's async model requires each future to implement a `poll()`
method that either returns `Ready(T)` or `Pending`. The future is a
self-referential struct (it contains pointers into its own fields).
Rust uses `Pin<&mut Self>` to prevent moves after the first poll.
Rejected because:

- **Self-referential structs.** Mapanare's type system does not support
  `Pin` or move-prevention semantics. Implementing poll-based futures
  would require adding these — a larger type-system change than the
  coroutine feature itself.
- **Manual state machines.** Without compiler-generated state machines
  (which Rust does generate via its async transform), users would need
  to write poll implementations by hand — terrible ergonomics.
- **LLVM does it for us.** The `llvm.coro.suspend` intrinsic is
  semantically equivalent to a poll-based yield point. LLVM handles
  the state-machine generation that makes poll-based futures usable.

### 8.5 Fibers via `makecontext`/`swapcontext`

POSIX fibers provide user-space context switching. Rejected because:

- **Deprecated.** `makecontext`/`swapcontext` are marked obsolete in
  POSIX.1-2008. They may be removed from future POSIX revisions.
- **Platform gaps.** No Windows equivalent (Windows fibers have
  different semantics). No WASM equivalent.
- **Performance.** Context switches require saving/restoring full
  register state. LLVM coroutine suspension is a function return —
  only live registers are saved.
- **Integration.** LLVM's optimization passes cannot reason about fiber
  switches. Coroutine suspensions are visible to the optimizer.

---

## Appendix A: Concrete IR Example — Full Async Function

This appendix shows the complete LLVM IR that Mapanare's emitter will
produce for a simple async function, before and after the LLVM
coroutine passes transform it.

### A.1 Source

```mapanare
async fn add_one(x: Int) -> Int {
    return x + 1
}

fn main() {
    let future = add_one(41)
    let result = await future
    print(result)  // 42
}
```

### A.2 Emitted IR (Pre-CoroSplit)

```llvm
declare token @llvm.coro.id(i32, ptr, ptr, ptr)
declare i1 @llvm.coro.alloc(token)
declare i64 @llvm.coro.size.i64()
declare ptr @llvm.coro.begin(token, ptr)
declare token @llvm.coro.save(ptr)
declare i8 @llvm.coro.suspend(token, i1)
declare void @llvm.coro.end(ptr, i1, token)
declare ptr @llvm.coro.free(token, ptr)
declare void @llvm.coro.resume(ptr)
declare void @llvm.coro.destroy(ptr)
declare i1 @llvm.coro.done(ptr)
declare ptr @malloc(i64)
declare void @free(ptr)
declare void @__mn_print_int(i64)

; Future<Int> = { i8 state, ptr payload }
%Future = type { i8, ptr }

define ptr @add_one(i64 %x) presplitcoroutine {
entry:
  %id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
  %need = call i1 @llvm.coro.alloc(token %id)
  br i1 %need, label %alloc, label %begin

alloc:
  %size = call i64 @llvm.coro.size.i64()
  %mem = call ptr @malloc(i64 %size)
  br label %begin

begin:
  %mem.phi = phi ptr [ null, %entry ], [ %mem, %alloc ]
  %hdl = call ptr @llvm.coro.begin(token %id, ptr %mem.phi)

  ; Allocate Future
  %future = call ptr @malloc(i64 16)
  store i8 0, ptr %future                             ; Pending
  %hdl.slot = getelementptr %Future, ptr %future, i32 0, i32 1
  store ptr %hdl, ptr %hdl.slot

  ; Initial suspend
  %s0 = call token @llvm.coro.save(ptr %hdl)
  %r0 = call i8 @llvm.coro.suspend(token %s0, i1 false)
  switch i8 %r0, label %ret [i8 0, label %body
                              i8 1, label %cleanup]

body:
  ; x + 1
  %result = add i64 %x, 1

  ; Set future to Ready
  %result.box = call ptr @malloc(i64 8)
  store i64 %result, ptr %result.box
  store i8 1, ptr %future                             ; Ready
  %val.slot = getelementptr %Future, ptr %future, i32 0, i32 1
  store ptr %result.box, ptr %val.slot

  ; Final suspend
  %sf = call token @llvm.coro.save(ptr %hdl)
  %rf = call i8 @llvm.coro.suspend(token %sf, i1 true)
  switch i8 %rf, label %ret [i8 0, label %ret
                              i8 1, label %cleanup]

cleanup:
  %to.free = call ptr @llvm.coro.free(token %id, ptr %hdl)
  %need.free = icmp ne ptr %to.free, null
  br i1 %need.free, label %do.free, label %ret

do.free:
  call void @free(ptr %to.free)
  br label %ret

ret:
  call void @llvm.coro.end(ptr %hdl, i1 false, token none)
  ret ptr %future
}

define i64 @main() {
entry:
  ; Call async function — returns Future
  %future = call ptr @add_one(i64 41)

  ; Check if ready (in this trivial case, the scheduler would handle this)
  %state.ptr = getelementptr %Future, ptr %future, i32 0, i32 0
  %state = load i8, ptr %state.ptr
  %ready = icmp eq i8 %state, 1
  br i1 %ready, label %extract, label %schedule

schedule:
  ; Register with scheduler and drive
  %hdl.ptr = getelementptr %Future, ptr %future, i32 0, i32 1
  %hdl = load ptr, ptr %hdl.ptr
  call void @llvm.coro.resume(ptr %hdl)
  ; After resume, future should be ready
  br label %extract

extract:
  %val.ptr = getelementptr %Future, ptr %future, i32 0, i32 1
  %val.box = load ptr, ptr %val.ptr
  %result = load i64, ptr %val.box
  call void @__mn_print_int(i64 %result)

  ; Cleanup
  %hdl2.ptr = getelementptr %Future, ptr %future, i32 0, i32 1
  ; (In full version: coro.destroy + free future + free result box)

  ret i64 0
}
```

### A.3 Post-CoroSplit (Conceptual)

After `opt -O1`, LLVM transforms `@add_one` into:

- **`@add_one`** (ramp): allocates frame, stores function pointers,
  allocates future, initial suspend, returns future pointer.
- **`@add_one.resume`** (resume): loads `%x` from frame, computes
  `x + 1`, stores result in future, final suspend.
- **`@add_one.destroy`** (destroy): frees the frame.

With HALO, if `@add_one` is inlined into `@main` and the handle
doesn't escape the scheduler, the frame allocation is replaced with a
stack alloca and the resume/destroy become direct calls. In the trivial
case above, the entire coroutine may be optimized away, leaving just
`call void @__mn_print_int(i64 42)`.

---

## Appendix B: Decision Summary

| # | Decision | Choice | Rationale | Section |
|---|----------|--------|-----------|---------|
| 1 | Scheduler model | Option A (inline in main) | Simplest, cooperative, extensible to B/C | §5.2 |
| 2 | Future<T> representation | `{i8 state, ptr payload}` | Uniform size, handle reuse | §3.3 |
| 3 | Pass pipeline | Use LLVM default `-O1` pipeline | `presplitcoroutine` is sufficient | §4.8 |
| 4 | `async fn` vs explicit `Future<T>` | Both work | Sugar vs manual, semantic pass distinguishes | §3.4 |
| 5 | Coroutine ABI | Switched-resume | Generic handles, HALO, C++ precedent | §1.1 |
| 6 | Debug info for async fns | Deferred to v5.x | Complex, Arc 7 baseline sufficient | §6.1 |
| 7 | AST representation | Dedicated `AsyncFnDef` node | Cleaner semantic pass entry/exit | §4.3 |
| 8 | Self-hosted compiler | Lag by 1-2 releases | Dual-closure convention | §4.10 |

---

## Appendix C: References

1. LLVM Coroutines — https://llvm.org/docs/Coroutines.html
2. Clang `CGCoroutine.cpp` — `clang/lib/CodeGen/CGCoroutine.cpp`
3. LLVM `CoroSplit.cpp` — `llvm/lib/Transforms/Coroutines/CoroSplit.cpp`
4. HALO Paper (P0981R0) — https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0981r0.html
5. Gor Nishanov, LLVM Coroutines (2016 Dev Meeting) — https://llvm.org/devmtg/2016-11/Slides/Nishanov-LLVMCoroutines.pdf
6. Clang Coroutine Debugging — https://clang.llvm.org/docs/DebuggingCoroutines.html
7. Mapanare v4.30.0 SESSION_REPORT.md — Path B strike (await identity removal)
8. Mapanare v4.66.0 SESSION_REPORT.md — Arc 7 panel close (DWARF baseline)
