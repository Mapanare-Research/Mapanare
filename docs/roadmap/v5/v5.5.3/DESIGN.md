# v5.5.3 — Self-Hosted Coroutine Emission Design

> **Zero-code release. Pure design + phase plan for v5.5.4+.**
>
> v5.5.0–v5.5.2 shipped a working-but-synchronous async frontend:
> `block_on` + `await` are registered, lowered, and emit correct
> values for the 5 Sh.4 goldens. The cost: async fns aren't
> actually coroutines — they compile as plain functions and
> `await`/`block_on` degenerate to copies. This works because
> every Sh.4 golden uses `return <const>` async fns with no real
> suspension points. The moment a future golden exercises real
> I/O suspension, Option A breaks.
>
> v5.5.3 is the research + design gate before we ship the real
> thing. This document:
>
> 1. Re-validates v4.67.0 DESIGN.md against current state
> 2. Documents the gap between v5.5.2 (Option A) and full
>    LLVM-coroutine parity with the Python bootstrap
> 3. Surveys how Rust / Go / C++20 / Zig handle async, validates
>    Mapanare's original choice (LLVM switched-resume coroutines
>    via `presplitcoroutine`) against modern alternatives
> 4. Specifies the self-hosted implementation phases v5.5.4
>    through v5.5.9 with concrete deliverables and verification
>    per phase
> 5. Enumerates risks specific to self-hosted porting
>    (drop-glue interaction, inliner interaction, fixed-point
>    shift, sret/ABI clash)
> 6. Defines go/no-go criteria per phase
>
> **No code changes. No VERSION bump in this release** — v5.5.3
> ships as a design-only commit.

**Status:** DRAFT → PROPOSED
**Owner:** Juan Denis
**Date:** 2026-04-23
**Authoritative upstream design:** `docs/roadmap/v4/v4.67.0/DESIGN.md`
**Reference implementation:** `mapanare/emit_llvm_text.py` lines
2490–2685 (async fn emission) + 5285–5484 (AwaitSuspend +
BlockOn)
**C runtime:** `runtime/native/mapanare_runtime.c` lines
1846–2049 (scheduler API, complete and TSan-clean since v5.1.4)

---

## Table of Contents

1. [Why this release exists](#1-why-this-release-exists)
2. [State-of-the-art survey (Rust / Go / C++20 / Zig)](#2-state-of-the-art-survey)
3. [Validation of the original v4.67.0 choice](#3-validation-of-the-original-v4670-choice)
4. [Gap analysis: Option A → full coroutines](#4-gap-analysis)
5. [Phase plan v5.5.4 through v5.5.9](#5-phase-plan)
6. [Risk register (self-hosted specific)](#6-risk-register-self-hosted-specific)
7. [Verification per phase](#7-verification-per-phase)
8. [Open questions](#8-open-questions)

---

## 1. Why this release exists

### 1.1 Option A bites us later (user's words)

v5.5.2 shipped "Option A — synchronous async" — a pragmatic
stub that makes the 5 Sh.4 goldens pass harness + llvm-as +
execution correctness, but only because those goldens use
`return <const>` async fns. The deliberate non-coverage:

| Scenario | Option A result |
|---|---|
| `async fn foo() -> Int { return 42 }` | ✅ returns 42 |
| `async fn foo() -> String { return http_get("...") }` | ❌ runs synchronously, blocks main thread |
| `block_on(foo())` where `foo` does I/O | ❌ no scheduler, no true concurrency |
| `spawn(foo())` for parallel fanout | ❌ single-threaded, defeats the point |
| `for await chunk in stream { ... }` | ❌ each chunk blocks the whole pipeline |
| `async fn` as agent handler | ❌ agent scheduler can't detect suspension |

Every one of these is a real use case documented in
`docs/guides/async.md` and `docs/cookbook/async.md`. Shipping
Option A as the final answer means every stdlib module that
touches network I/O, file I/O, or multi-agent fanout will
silently degrade to single-threaded blocking. That's the "bites
us later" the user warned against.

### 1.2 What the Python bootstrap does (and what we ported)

**Python side (reference):**

| Concern | Python location | Self-hosted (v5.5.2) |
|---|---|:---:|
| Semantic: register `block_on` | `semantic.py` (implicit in builtin set) | ✅ v5.5.0 `semantic.mn` |
| Semantic: register `spawn`/`join` | `semantic.py` | ❌ (not used by goldens) |
| Lowerer: `block_on(call)` → MIR `BlockOn` | `lower.py:1836–1845` | ✅ v5.5.1 `lower.mn` |
| Lowerer: `await expr` → MIR `AwaitSuspend` | `lower.py` (implicit) | ✅ v5.5.1 `lower.mn` |
| MIR variants | `mir.py:724–748` | ✅ v5.5.1 `mir.mn` |
| **Emitter: coro intrinsic decls** | `emit_llvm_text.py:898–908` | ✅ v5.5.2 (declared unused) |
| **Emitter: async fn prologue (coro.id/size/begin + initial suspend)** | `emit_llvm_text.py:2568–2593` | ❌ **v5.5.4** |
| **Emitter: ret → future.payload rewrite** | `emit_llvm_text.py:2610–2667` | ❌ **v5.5.4** |
| **Emitter: coro.final/cleanup/ret epilogue** | `emit_llvm_text.py:2668–2685` | ❌ **v5.5.4** |
| **Emitter: AwaitSuspend (save/suspend/switch)** | `emit_llvm_text.py:5291–5414` | ❌ **v5.5.5** |
| **Emitter: BlockOn (scheduler_register/run/destroy)** | `emit_llvm_text.py:5416–5484` | ❌ **v5.5.6** |
| **Emitter: scheduler_init/destroy in main** | `emit_llvm_text.py:2499–2520` | ❌ **v5.5.6** |
| **Inliner: skip async fns** | `mir_opt.py` (implicit via frame) | ❌ **v5.5.4** |
| Runtime scheduler (C) | `mapanare_runtime.c:1846–2049` | ✅ v5.1.4 (no changes needed) |

6 of 13 emitter-side concerns are still gaps. The remaining
work is not architectural — the design is settled — but it IS
the high-risk surface where drop-glue (v5.4.0–v5.4.4), sret
(v5.0.4), and inliner (v5.1.2) interact.

### 1.3 What the user asked for

> "no no i dont want cheap shit that will bites use later i want
> the rreal thing evne if you need to create a v5.5.3, v5.5.4
> and more version but the right way even if you need to do
> investigations with go or how rust does it as i know we did
> something similar in v4 and it helped a lot"

The "something similar in v4" is v4.67.0 DESIGN.md. That doc
is 1,398 lines covering LLVM coroutine spec, runtime scheduler
design, rejected options (Green threads, manual state machines,
CPS, Rust-style poll, fibers), concrete IR example, and
appendix with decision summary. It's still authoritative.

This v5.5.3 release re-validates that design for the v5.5.x
era and translates it into concrete self-hosted porting work.

---

## 2. State-of-the-art survey

Re-evaluating the v4.67.0 §8 rejected-options section against
current (2026-04) language design work to confirm the decision
still holds.

### 2.1 Rust — Poll-based Future + async/await desugaring

**Model:** `async fn f() -> T` desugars to `fn f() -> impl
Future<Output=T>`. Each `await` is a call to `Future::poll()`
that either returns `Poll::Ready(T)` or `Poll::Pending`. The
compiler generates a state machine struct per `async fn`; each
field is a live variable across suspend points; each variant
represents a suspend point. The struct is self-referential —
it may contain pointers into its own fields (the "pinned
future" problem). `Pin<&mut Self>` is the solution — a type
system guarantee that `Self` won't move after the first `poll`.

**Executor:** External (tokio, async-std, smol). The language
provides no default. `.await` desugars to a loop that polls +
yields control to whoever called `poll`. Executors provide the
outer loop.

**Strengths vs Mapanare:**
- Zero heap allocation for the future itself (stack-allocated
  state machine, only the executor's task queue heap-allocates).
- Cancellation is structural: drop the future, drop the state
  machine.
- Mature ecosystem.

**Weaknesses vs Mapanare:**
- `Pin` is a heavy type system addition. Requires `Unpin`
  auto-trait, pin-projection macros, `pin!()` macro. Mapanare
  would need equivalents.
- Executor-agnostic means every async stdlib must be
  generic-over-executor or tie to one. That's a design burden.
- Self-referential structs are a known foot-gun that took Rust
  years to get right.

**Verdict: still rejected.** The type-system work to add `Pin`
semantics is larger than the LLVM-coroutine infrastructure work
and would delay async shipping by multiple arcs. v4.67.0's
analysis holds in 2026.

### 2.2 Go — Goroutines + GMP scheduler

**Model:** Every function can block. `go fn(args)` spawns a
goroutine — a user-space green thread with its own stack
(initially 2KB–8KB, grows on demand via segmented-stack or
stack-copying). Scheduler (GMP: Goroutines, Machines=OS threads,
Processors=logical CPUs) multiplexes M goroutines over N OS
threads.

**Executor:** Built in. One scheduler per process, preemptive
(since Go 1.14 via async signals at GC safepoints).

**Strengths vs Mapanare:**
- No `async` keyword — every function is potentially
  suspending. "Colorblind" code.
- Simple mental model: `go` spawns, channels sync.
- Preemption means a tight loop can't starve the scheduler.

**Weaknesses vs Mapanare:**
- **Stack growth is runtime-specific.** Mapanare targets WASM,
  mobile, desktop. Segmented stacks need per-platform assembly
  (setjmp on POSIX, fibers on Windows, not possible on WASM).
  LLVM coroutines work uniformly on all three.
- **GC interaction.** Go's preemption relies on GC safepoints.
  Mapanare is arena+refcount, no GC. The preemption story would
  have to be invented.
- **Runtime overhead.** GMP needs a full runtime (global queue,
  per-P queue, netpoller, sysmon). LLVM coroutines are
  zero-runtime at the language level — the scheduler is
  user-controlled.
- **WASM.** Go's WASM target uses Asyncify (a post-processing
  pass that turns every call into a potential suspend point,
  via a large lookup table). Massive binary bloat.

**Verdict: still rejected.** v4.67.0 §8.1 rejected green
threads on WASM compatibility grounds alone. The GC interaction
adds a second rejection — Mapanare's memory model is too
different from Go's to share the preemption infrastructure.

### 2.3 C++20 — Stackless coroutines + `co_await`

**Model:** Essentially identical to LLVM coroutines (same
`presplitcoroutine` + `llvm.coro.*` intrinsics under the hood
when compiled with Clang). User-facing: `co_await`,
`co_return`, `co_yield`. Promise types (user-defined) control
suspension semantics, return-value handling, and resumption
logic.

**Executor:** User-provided. Standard library has `std::future`
but no scheduler. Boost.Asio, libunifex, stdexec proposals
provide executor abstractions.

**Strengths vs Mapanare:**
- Same ABI as LLVM coroutines, so bytecode-compat with C++
  coroutine tooling (debuggers, profilers).
- Zero language-runtime overhead.
- HALO (Heap Allocation eLision Optimization) elides the frame
  heap alloc when the handle doesn't escape.

**Weaknesses vs Mapanare:**
- Promise type machinery is complex. `initial_suspend`,
  `final_suspend`, `return_void`/`return_value`,
  `unhandled_exception`, `get_return_object`, `await_ready`,
  `await_suspend`, `await_resume`. Mapanare doesn't need most
  of these (no exceptions, no custom awaitables in v4.x).

**Verdict: the mechanism is perfect; the user-facing API is
overbuilt for our needs.** Mapanare uses the mechanism directly
without exposing the promise-type machinery — exactly what
v4.67.0 §1.1 specified.

### 2.4 Zig — `async` blocks + explicit frames

**Model:** `async foo()` returns a `@Frame(foo)` — a
compiler-computed struct sized to hold the function's state
machine. The frame is stack-allocated or user-managed.
`@await` resumes + extracts. `suspend { }` blocks are explicit
suspension points.

**Executor:** Completely user-provided. Zig's stdlib has no
scheduler. Event loops are ecosystem (e.g., `async-await`,
`zigtoolkit`).

**Strengths vs Mapanare:**
- Explicit frame sizing: no heap allocation surprise.
- "Colorblind" async via `asyncify` — a function can be called
  sync or async based on context.

**Weaknesses vs Mapanare:**
- **Status unclear.** Zig removed `async/await` from the
  language in v0.11 (2023), shipped as "will come back" but
  timeline uncertain as of 2026-04. The feature isn't shipped
  in current stable.
- Frame-size computation requires whole-program analysis. Not
  a good fit for separate compilation.

**Verdict: Zig's async is currently speculative. The explicit
frame model is interesting for future exploration but not a
candidate to replace LLVM coroutines in v5.x.**

### 2.5 Survey conclusion

v4.67.0's choice (LLVM switched-resume coroutines via
`presplitcoroutine`) is still correct in 2026:

- **Rust's poll-based model** needs `Pin` — too much type-system
  work.
- **Go's green threads** don't fit WASM / Mapanare's memory
  model.
- **C++20's mechanism** is what we're using (directly, without
  the promise-type user API).
- **Zig** is not ready.

The Python bootstrap already implements this. The self-hosted
compiler needs to catch up. No redesign needed at the
language level — this is a porting exercise.

---

## 3. Validation of the original v4.67.0 choice

Re-reading v4.67.0 DESIGN.md Appendix B (Decision Summary):

| # | Decision | v4.67.0 choice | v5.5.x still valid? |
|---|---|---|:---:|
| 1 | Scheduler model | Option A (inline in main) | **No → Option B.** The C runtime as of v5.1.4 is a full multi-threaded work-stealing scheduler (`runtime/native/mapanare_runtime.c:1846–2049`). Option A was "cooperative inline in main" but v4.150.0 already upgraded this to threaded + lazy. Self-hosted emitter targets the v5.1.4 API. |
| 2 | Future<T> representation | `{i8 state, ptr payload}` | ✅ Unchanged. Python uses this layout. |
| 3 | Pass pipeline | LLVM default `-O1` pipeline | ✅ Unchanged. `presplitcoroutine` triggers the passes. |
| 4 | `async fn` vs explicit `Future<T>` | Both work | ✅ Unchanged. |
| 5 | Coroutine ABI | Switched-resume | ✅ Unchanged. |
| 6 | Debug info for async fns | Deferred to v5.x | **Still deferred.** v5.5.x doesn't fix this either; debug info for async remains a known-broken area. |
| 7 | AST representation | Dedicated `AsyncFnDef` | **Not followed.** Self-hosted parser uses `"async"` decorator on FnDef (parser.mn:797–798). Works; less intrusive. |
| 8 | Self-hosted lag | 1–2 releases behind Python | **Violated.** We're currently 30+ releases behind — Python shipped full async at v4.73.0–v4.75.0, we're porting in v5.5.x. Acceptable because the Sh.4 goldens never regressed silently; we're just closing the gap now. |

The two divergences (Decision 1: Option A → Option B, and
Decision 7: AsyncFnDef → decorator) are both safe —
Decision 1 got *stronger* guarantees (real multi-threaded
scheduling) and Decision 7 is a stylistic simplification.

### 3.1 One correction to Appendix A

The v4.67.0 concrete IR example (Appendix A.2) uses
`br i1 %need, label %alloc, label %begin` for conditional
allocation. The current Python bootstrap (`emit_llvm_text.py:
2575–2578`) emits unconditional `malloc` instead:

```llvm
%coro.id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
%coro.size = call i64 @llvm.coro.size.i64()
%coro.mem = call ptr @malloc(i64 %coro.size)
%coro.hdl = call ptr @llvm.coro.begin(token %coro.id, ptr %coro.mem)
```

The optional `coro.alloc` branch exists to allow LLVM's HALO
pass to elide the heap alloc when the handle doesn't escape.
Python's unconditional malloc is a (minor) regression vs the
design — HALO can't fire, every async fn pays for a heap
frame.

**v5.5.4 decision:** match Python (unconditional malloc). Fix
HALO later — Own.1 v6.0 borrow-checker work will make handle
escape analysis more tractable.

---

## 4. Gap analysis

The 6 missing emitter-side concerns from §1.2, in dependency
order:

### 4.1 Inliner: skip async fns

**Python:** The Python bootstrap doesn't have an inliner
(inlining happens post-emission in LLVM opt passes). The
self-hosted MIR optimizer (`mir_opt.mn`) has a v5.1.2 inliner.

**Problem:** If the inliner inlines `async fn foo()` into a
non-async caller, the coroutine intrinsics + future alloc +
ret-rewrite land in the caller's body — which is **not**
`presplitcoroutine`. LLVM's CoroSplit won't transform it, and
the IR will reference intrinsics in a non-coroutine function.
That's malformed IR.

**Fix:** `inline_small_functions::can_inline(f)` returns false
when `fn_is_async(f)` is true. ~5 LOC.

### 4.2 Emitter: async fn structural rewrite

**Python:** `emit_llvm_text.py::_emit_fn` line 2568 branches on
`fn.is_async` and emits the presplit-coroutine scaffolding.

**Components:**
- Return type: `T` → `ptr` (the Future<T>)
- Function attr: add `presplitcoroutine`
- Prologue (new `coro.entry:` block):
  - `%coro.id = call token @llvm.coro.id(...)`
  - `%coro.size = call i64 @llvm.coro.size.i64()`
  - `%coro.mem = call ptr @malloc(i64 %coro.size)`
  - `%coro.hdl = call ptr @llvm.coro.begin(%coro.id, %coro.mem)`
  - `%future = call ptr @malloc(i64 16)` + `store i8 0` + store
    `%coro.hdl` into payload slot
  - Initial suspend: `%save0 = coro.save`, `%susp0 =
    coro.suspend(%save0, false)`, `switch`
- `pre_entry:` label preserves existing body entry point
- Every `ret <ty> <val>` in the body gets rewritten:
  - `%box = malloc(sizeof T)`
  - `store <val> into box`
  - `store i8 1 into future` (state = Ready)
  - `store box into future.payload`
  - `br label %coro.final`
- `ret void` similarly but without box (or with null payload)
- Epilogue blocks appended:
  - `coro.final:` — final suspend
  - `coro.cleanup:` — `coro.free` + `free`
  - `coro.ret:` — `coro.end` + `ret ptr %future`

**LOC:** ~150 in `emit_llvm.mn::emit_mir_function`. High-risk
because this interleaves with:
- Drop-glue (v5.4.0–v5.4.4) emission at `ret`
- Entry-block buffering (`entry_prelude_lines`,
  `entry_block_body`, `in_entry_block` fields)
- sret returns (Cb.15 v5.0.4) — async fns always return ptr, so
  sret is N/A for async fns; need explicit bypass

### 4.3 Emitter: AwaitSuspend full emission

**Python:** `emit_llvm_text.py:5291–5414`. Two paths:
- **In-async context** (`_fn_is_async == true`): real suspend
  via `coro.save` + `coro.suspend` + switch.
- **Non-async context** (fallback): inline resume loop.

**In-async pattern (the real path):**

1. Load `%future.state`, check == 1 (ready); if so `br %ready`
2. `%drive:` resume the inner coroutine once (`coro.resume`),
   re-check state
3. `%check:` if ready now, `br %ready`; else `br %suspend`
4. `%suspend:` register wait via `__mn_coro_register_wait`,
   save + suspend the outer coroutine (`coro.save` +
   `coro.suspend`), switch
5. `%resume_N:` post-scheduler-resume, `br %ready`
6. `%ready:` load `%future.payload → box`, `load box → val`

**LOC:** ~80 in `emit_llvm.mn`. Medium-high risk — 6 new basic
blocks per await point, SSA name collision is easy.

### 4.4 Emitter: BlockOn full emission

**Python:** `emit_llvm_text.py:5416–5484`.

**Pattern:**
1. Load `%future.handle` (payload slot while state=0)
2. `call void @__mn_coro_scheduler_register(%hd)`
3. `call void @__mn_coro_scheduler_run()`
4. Load `%future.payload → box`, `load box → val`
5. `call void @llvm.coro.destroy(%hd)` (uses the handle loaded
   in step 1 — v4.102.0 fix, critical)
6. `call void @free(box)`, `call void @free(future)`

**LOC:** ~40. Medium risk. The v4.102.0 note about not
reloading the handle after scheduler_run (because the payload
slot is now the result pointer, not the handle) is a known
foot-gun — mirror the Python carefully.

### 4.5 Emitter: main() scheduler lifecycle

**Python:** `emit_llvm_text.py:2499–2520`. When
`_module_has_async == true`:
- Prepend `call void @__mn_coro_scheduler_init(i32 0)` to main's
  entry block (first instruction)
- Rewrite every `ret void` / `ret <val>` in main to call
  `__mn_coro_scheduler_destroy()` before the ret

**LOC:** ~20. Low-medium risk. Need to detect
`_module_has_async` at module-entry time (before individual fn
emission).

### 4.6 Emitter: drop-glue in cleanup block

**Critical interaction with v5.4.0–v5.4.4.** The coroutine's
cleanup path (`coro.cleanup`) runs when the coroutine is
destroyed. Any heap-allocated values the body allocated before
the destruction point need to be freed.

v4.67.0 DESIGN.md §4.9 specifies this: drop-glue emission in
the coro.cleanup block before coro.free.

**Current state:** `emit_mir_return` already emits drop glue
(v5.4.1 shadow-slot, v5.4.3 loop-depth tracking). For async
fns, the `ret` is rewritten to `br %coro.final` — so drop glue
needs to fire in the coro.final path, not at `ret`. But also
at coro.cleanup (for cancellation / destroy-before-complete
cases).

**v5.5.4 decision:** ship the prologue/epilogue structure first
**without** async-aware drop glue. Add async drop glue in
v5.5.5 as its own phase (see §5).

---

## 5. Phase plan

Each phase is a standalone release with independent commit +
verification. Phases are ordered so that each leaves the
compiler in a buildable, self-hosting state.

### v5.5.4 — Inliner gate + async fn shell

**Scope:**
- `mir_opt.mn::inline_small_functions` — skip when
  `fn_is_async(callee)`
- `emit_llvm.mn::emit_mir_function` — is_async branch with full
  coroutine wrapping (prologue + ret-rewrite + epilogue), but
  AwaitSuspend + BlockOn still use v5.5.2 Option A copies

**Deliverable:** async fns emit as proper
`define ptr @foo() presplitcoroutine` with working coroutine
body. The 5 Sh.4 goldens still execute correctly (because
Option A's BlockOn/AwaitSuspend copies still work — they just
now operate on `ptr %future` values).

**LOC:** ~155 (~5 inliner + ~150 emitter)
**Risk:** High. Drop-glue + sret + entry-block buffering
interact.
**Verification:**
- Stage1 rebuilds cleanly
- 5 Sh.4 goldens: compile, `llvm-as` clean, execute correctly
- `opt -O1 /tmp/55_async_basic.ll -o /dev/null` clean (LLVM
  coroutine passes must accept the pre-split IR)
- Stage2 (`mnc_all.mn`) compiles via stage1, stage2.ll
  `llvm-as` clean, self-hosting preserved
- Non-bootstrap pytest 0 failures
- Valgrind clean on 55_async_basic
- Goldens 59/66 harness PASS preserved

**Exit criteria:** `opt -O1` on each Sh.4 golden produces
post-split functions named `@foo.resume` / `@foo.destroy`.
Pre-split IR executes correctly; post-split IR executes
correctly (proves LLVM accepts our shape).

### v5.5.5 — Real AwaitSuspend emission

**Scope:**
- `emit_llvm.mn::emit_mir_by_kind` — replace `"await_suspend"`
  Option A copy with real save/suspend/switch pattern
- Must detect `_fn_is_async` in current emit state so emission
  branches to real vs. (retained) fallback
- Async drop-glue in cleanup path

**Deliverable:** `await inner()` inside an async fn generates
real LLVM coroutine suspension. The scheduler still isn't
called by anyone (BlockOn is still Option A), so Sh.4 goldens
still run synchronously — but the IR now contains real
`@llvm.coro.save`/`@llvm.coro.suspend` sequences.

**LOC:** ~90 (80 AwaitSuspend + 10 drop-glue hook)
**Risk:** Medium-high. 6 new BBs per await; SSA collision.
**Verification:**
- 5 Sh.4 goldens still compile + execute correctly
- `opt -O1` still clean
- IR inspection: each `await` produces
  `%aw.save.N = call token @llvm.coro.save`

**Exit criteria:** 56_async_await's IR contains
`call token @llvm.coro.save(ptr %coro.hdl)` in every await
block. Goldens execute.

### v5.5.6 — Real BlockOn + main scheduler lifecycle

**Scope:**
- `emit_llvm.mn::emit_mir_by_kind` — replace `"block_on"`
  Option A copy with scheduler_register + scheduler_run +
  extract + destroy + free
- `emit_llvm.mn::emit_mir_function` (main branch) — inject
  `__mn_coro_scheduler_init(0)` at main entry,
  `__mn_coro_scheduler_destroy()` before every main exit,
  gated on `_module_has_async`
- Add `_module_has_async: Bool` field to `EmitState`,
  compute once at module-emission start

**Deliverable:** `block_on(future)` actually drives the
scheduler. 5 Sh.4 goldens now execute **through the full
Python-parity coroutine pipeline**: scheduler init → async
fn returns future (at initial suspend) → scheduler resumes →
body runs → final suspend → BlockOn extracts → destroy → free.

**LOC:** ~80 (40 BlockOn + 25 main init/destroy + 10
_module_has_async + 5 EmitState plumbing)
**Risk:** Medium. Main-entry prepend must not collide with
drop-glue. v5.4.0–v5.4.4 patterns are in the same code paths.
**Verification:**
- 5 Sh.4 goldens execute correctly **via scheduler** (not via
  Option A copy). Can be verified by setting
  `MAPANARE_ASYNC_THREADS=4` and watching thread creation via
  `strace`/`ltrace`.
- TSan clean on all 5 async goldens
- Benchmark: `benchmarks/async/run_async_benchmarks.py`
  geomean within ±5% of v5.1.4 baseline (since the scheduler
  is unchanged, only the emitter; we shouldn't regress perf).
- stage2.ll self-hosting preserved

**Exit criteria:** On an async golden, `ltrace -e malloc+free
/tmp/golden.bin` shows the expected malloc/free pattern
(coroutine frame + future + box), AND TSan reports 0 races.

### v5.5.7 — Sanitizer + fixed-point hardening

**Scope:** No new features. Stabilization.
- Valgrind sweep all 66 goldens, document any new leaks
- ASan sweep, document any new findings
- TSan sweep the 5 async goldens specifically
- Fixed-point verification: stage2 → stage3 → stage4; NEAR or
  STRICT expected
- Any bugs found in v5.5.4–v5.5.6 get fixed here

**Deliverable:** Production-ready async emitter.
**LOC:** TBD (bug fixes only)
**Verification:** All sanitizer gates from the `make lint` /
`make leak-check` / CI workflows pass.

**Exit criteria:** Zero new valgrind ERRORS, zero new ASan
findings, zero TSan races, stage3.ll == stage2.ll (Ve.1 NEAR
or STRICT).

### v5.5.8 — Parity gap closure: spawn + join

**Scope:**
- `semantic.mn` — register `spawn` / `join` builtins
- `lower.mn` — lower `spawn(async_call())` to MIR `Spawn(dest,
  future)` variant
- `mir.mn` — add `Spawn(Value, Value)` variant
- `emit_llvm.mn` — emit `call void @__mn_coro_spawn(ptr)`
- Add a new golden `60_async_multi_fanout.mn` that uses
  `spawn()` explicitly for parallel fanout. Verify via
  `MAPANARE_ASYNC_THREADS=N` that N workers run concurrently.

**Deliverable:** Full Python-parity surface for async. Sh.4
closes definitively in PARITY_GAPS.md.

**LOC:** ~60 (~20 semantic + 15 lower + 5 MIR + 20 emit)
**Risk:** Low. Additive.
**Verification:** New golden runs correctly; `ltrace` shows
multiple worker threads active simultaneously.

### v5.5.9 — Docs + release polish

**Scope:**
- `docs/guides/async.md` — remove "LLVM backend only" caveats;
  document self-hosted support
- `docs/SPEC.md` §async — cross-reference v5.5.4–v5.5.8
- `docs/roadmap/v5/PARITY_GAPS.md` — move Sh.4-async row to
  Historical (GOLDEN_TRIAGE.md also updated if present)
- `CLAUDE.md` — prepend v5.5.4–v5.5.9 entries
- `README.md` + localized — badge bump if goldens count changed

**Deliverable:** Clean docs, clear release notes.
**LOC:** docs only.
**Verification:** `make lint` clean, doc links validate.

---

## 6. Risk register (self-hosted specific)

### R1 — Drop-glue in coroutine cleanup path (HIGH)

v5.4.0–v5.4.4's drop glue fires at `ret`. For async fns, `ret`
is rewritten to `br %coro.final`. The drop-glue hook needs to
fire:
- On the normal completion path (before `br %coro.final`)
- On the cleanup/destroy path (in `coro.cleanup` block)

These are two different locations with different available SSA
values (some locals may be dead on one path but live on the
other). Mitigation: v5.5.5 handles this as its own phase.

**Early warning sign:** if v5.5.4's valgrind sweep shows new
leaks on 55/56/57/58/59, it's this bug.

### R2 — Inliner + monomorphization interaction (MEDIUM)

If a generic `fn foo<T>(...)` is called from inside an async
fn and the monomorphizer creates `foo$Int`, the new
monomorphic copy may or may not be `async` depending on
whether the source was `async fn foo<T>`. v5.5.4's
`fn_is_async(f)` check runs on the MIRFunction, so as long as
the decorator propagates to the monomorphic copy, the check
works.

**Verify:** `lower.mn:1673` —
`new_fn_def_data(gfn.span, mangled, gfn.public, empty_tp,
new_params, new_ret, gfn.body, gfn.decorators)` — the
decorator list is passed through. OK.

### R3 — Fixed-point shift (MEDIUM)

Every emit_llvm.mn change shifts stage2.ll. v5.4.1 saw +33%,
v5.4.4 saw +54%. v5.5.4's structural async rewrite will
affect every async fn — for the current corpus, only 10 async
fns (in 55–59). stage2.ll size delta should be small.

**However**: if the `mnc_all.mn` source ever contains an
async fn in the self-hosted compiler itself (it doesn't today,
but v5.x stdlib may), fixed-point gets interesting.

Mitigation: v5.5.7 verifies stage3.ll.

### R4 — sret ABI collision (LOW)

Async fns always return `ptr` (Future). sret (Cb.15 v5.0.4)
applies when return type is a large aggregate. Async's ptr
return type is small enough to skip sret. Need to verify the
sret classifier doesn't fire on async fns. One-line fix in
`emit_mir_function::use_sret` — skip when
`fn_is_async(f)`.

### R5 — Entry-block buffering interaction (MEDIUM)

v5.4.1 added `entry_prelude_lines`, `entry_block_body`, and
`in_entry_block` EmitState fields. These buffer the function
body while `emit_track_*` fires tracking allocas. The async
prologue needs to emit `coro.entry:` block **before** the
existing entry block, which means either:

(a) Emit `coro.entry:` directly to `s.lines` (bypass
    buffering), then let buffering continue for `pre_entry:`
    and the rest
(b) Add a new buffer for `coro.entry`

**v5.5.4 decision:** (a). The coro prologue doesn't contain
any user-allocated resources that need drop-glue tracking, so
bypassing the buffer is safe.

### R6 — Stage1 binary size (LOW)

The self-hosted compiler is currently ~5MB stripped. Adding
emitter changes adds ~500 LOC → maybe +50KB to the binary.
Negligible.

### R7 — v4.102.0 handle-reload foot-gun (MEDIUM)

Python `_do_block_on` comment at line 5459 explicitly warns:
> "the coroutine's final-suspend path overwrites
> `future.payload` (slot 1 of the {i8, ptr} Future) with the
> boxed return value — so after scheduler_run completes, that
> slot no longer holds the coroutine handle. The old code
> reloaded slot 1 a second time for llvm.coro.destroy, which
> handed the destroy intrinsic a pointer to an 8-byte malloc'd
> int and segfaulted at destroy_fn. Reuse the ``hd`` loaded
> before scheduler_run — that's the real handle."

**v5.5.6 MUST mirror this exactly.** Load handle once before
scheduler_register, reuse for coro.destroy.

---

## 7. Verification per phase

| Phase | Unit | Integration | Sanitizer | Self-host | Benchmark |
|---|---|---|---|---|---|
| v5.5.4 | llvm-as on each golden | 5 Sh.4 exec | — | stage2 llvm-as | — |
| v5.5.5 | `coro.save` grep in IR | 5 Sh.4 exec | valgrind 55 | stage2 llvm-as | — |
| v5.5.6 | `scheduler_register` grep in IR | 5 Sh.4 exec via scheduler | TSan 5 async | stage2 llvm-as | async geomean ±5% |
| v5.5.7 | — | 66 goldens | valgrind+ASan 66 | stage3 fixed-pt | async geomean ±2% |
| v5.5.8 | `spawn` MIR + emit tests | new 60_async_multi_fanout | TSan 6 async | stage2 llvm-as | — |
| v5.5.9 | doc link check | — | — | — | — |

**Common gates for every phase:**
- Stage1 binary rebuilds
- `python3 scripts/test_native.py --stage1 mnc-stage1` →
  59/66 or better, no regressions
- `make lint` clean
- `python3 scripts/check_struct_registry.py` clean (Reg.1 gate)
- Non-bootstrap pytest 0 failures
- Goldens harness PASS count ≥ v5.5.2 baseline (59/66)

---

## 8. Open questions

Before starting v5.5.4, these should be answered:

### Q1 — Do we need the optional `coro.alloc` branch?

Python bootstrap skips it (unconditional malloc). v4.67.0
DESIGN.md Appendix A included it but the rationale was HALO
elision. HALO doesn't fire in Mapanare (handle escapes to
scheduler). Recommend: skip, match Python.

### Q2 — What about `opt -O1` invocation?

v4.67.0 §4.8 said `-O1` is sufficient — LLVM's default
pipeline includes CoroSplit/CoroElide/CoroCleanup at `-O1+`.
But the goldens harness uses `llc -O2` directly (per my v5.5.2
manual run). Need to verify `llc` alone runs the coro passes,
or whether we need an explicit `opt -passes=default<O1>` step
in between.

**Recommend testing at v5.5.4:** compile a Sh.4 golden with
`llc` alone vs `opt | llc`, confirm both work.

### Q3 — Does Ve.1 (stage3 segfault, open since v5.4.4) affect
async?

v5.4.4's SESSION_REPORT notes mnc-stage2 segfaults during lex
of mnc_all.mn. That's unrelated to async (it's drop-glue
infrastructure). But if v5.5.4 adds another 150 lines of
emit_llvm.mn, we may trigger an adjacent bug.

**Recommend:** run `scripts/verify_fixed_point.sh` at v5.5.4
Phase 0 to establish baseline, check at v5.5.4 end.

### Q4 — Should v5.5.4 ship incrementally within itself?

v5.5.4's scope (~155 LOC in emitter) is bigger than v5.5.0
(~17) or v5.5.1 (~44). Worth splitting into:
- v5.5.4a: inliner gate + prologue only (reject async fns
  that would fail to wrap)
- v5.5.4b: ret-rewrite
- v5.5.4c: epilogue

Too granular? Counter: v5.5.0/1/2 succeeded with small steps.
Recommend: ship v5.5.4 as one release if the first pass is
clean, split if it drags.

### Q5 — What do we do if the user adds an async golden that
really suspends (I/O-bound)?

v5.5.6 enables real scheduling. A golden that does real I/O
would exercise the scheduler fully. If no such golden exists
after v5.5.6, consider adding one at v5.5.8:
`60_async_multi_fanout.mn` could be augmented with
`read_file_async`-like calls.

**Recommend:** v5.5.8 creates `60_async_real_io.mn` if the
async stdlib (`stdlib/async/`, `stdlib/net/`) has async
entry points that the goldens can call directly.

---

## Appendix A: Concrete next-action map

What the v5.5.4 implementor should read, in order:

1. This doc (§4–5 specifically)
2. `docs/roadmap/v4/v4.67.0/DESIGN.md` §4.7 (LLVM IR emission)
   and Appendix A (concrete IR example)
3. `mapanare/emit_llvm_text.py:2568–2685` (Python
   reference — the exact code to port)
4. `mapanare/self/emit_llvm.mn:4147–4351` (self-hosted
   `emit_mir_function` — the injection site)
5. `mapanare/self/mir_opt.mn` (inliner — §4.1 of this doc)
6. `runtime/native/mapanare_runtime.c:1846–2049` (scheduler
   API — unchanged)

Starting point for v5.5.4: `emit_mir_function`. Branch on
`fn_is_async(f)` at line 4148. Emit alternate prologue +
rewrite rets + append epilogue. Keep non-async path
byte-identical.

## Appendix B: Why this isn't just "port the Python code"

The self-hosted emitter uses different primitives:
- `emit_line` writes to either `entry_block_body` (during
  buffered emission) or `s.lines` (direct). Async prologue
  needs direct write; ret-rewrite happens during buffered
  emission.
- Value objects (`Value` struct) carry MIR type; Python uses
  string types. Conversion needed at each intrinsic call site.
- SSA name management: Python uses `self._f(prefix)`,
  self-hosted uses `make_value(ty, prefix)`. Different return
  shape.

So 350 LOC of Python translates to ~250–300 LOC of Mapanare,
but with structural translation at each line — not
mechanical.

---

## Appendix C: Rejected alternatives for v5.5.x specifically

### Option A forever

Just keep v5.5.2's synchronous stubs. Rejected per user
directive ("no cheap shit that bites us later"). Async with
real I/O would silently block. Stdlib async modules would be
unusable in the self-hosted build.

### Option B-Lite (heap-allocated futures without LLVM coroutines)

Proposed at the start of v5.5.3. Real Future<T> allocation but
no scheduler, no concurrency. Rejected because:
- Still degrades to synchronous under I/O
- `spawn()` still can't multi-thread
- ~100 LOC that has to be thrown away when real coroutines
  ship

### "Wait for v6.0 then do a big rewrite"

Rejected because v6.0 is Own.1 (borrow checker) — unrelated
scope, many releases away. Async in self-hosted is blocking
stdlib migration work now.

### Port to a different coroutine model (e.g., Rust poll)

Rejected per §2 survey. Too much type-system work.

---

## Sign-off

This design doc replaces the v5.5.3 PROMPT.md / PLAN.md
placeholders. When v5.5.4 ships, reference this doc's §5 for
scope and §6 for risks. When v5.5.9 closes Sh.4 in
PARITY_GAPS.md, link back to this doc.

**End of v5.5.3 DESIGN.md.**
