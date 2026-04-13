# Mapanare v4.67.0 — Coroutine Design Document

> **Arc 8 release 1. Design-only.** No code changes. Produces
> `docs/roadmap/v4/v4.67.0/DESIGN.md`, the single most important
> document in arcs 8 and 9. Every subsequent coroutine release
> references it.

**Status:** DONE (2026-04-12)
**Session log:** DESIGN.md written (8 sections, ~7500 words). 4 reviewers signed off. Rattler approved, no veto.
**Decisions taken:** Switched-resume ABI, Option A scheduler, {i8,ptr} Future, -O1 default pipeline, dedicated AsyncFnDef node, async debug info deferred to v5.x.
**Breaking:** No (no code)
**Prerequisite:** v4.66.0 (arc 7 panel PASS)
**Delta review:** No (no syntax — design review only)
**Full panel:** No (v4.71.0)
**Estimated work:** 2 sprints (full-time reading + writing, no code)
**Theme:** Read the LLVM coroutine spec. Decide how `async fn` lowers. Pick the runtime scheduler model. Write it all down so 5 subsequent releases can follow it.

---

## Why design-only

Coroutines are the hardest feature Mapanare has ever attempted. The v4.30.0 retrospective on the failed `await` identity lowering established the pattern: features with hollow syntax are worse than absent features. Arc 8 starts with a design doc specifically to prevent a v4.68.0 that ships grammar without a plan for lowering.

LLVM's coroutine infrastructure is the canonical approach (used by Clang's coroutine TS, Swift, Rust async, Crystal). It is not small. The v4.67.0 work is: **read it, understand it, and write down exactly what Mapanare will do with it.**

Every subsequent coroutine release in arcs 8 and 9 references specific sections of DESIGN.md for rationale. If the design is right, v4.68.0-v4.75.0 are execution. If the design is wrong, we find out at design-review time instead of at v4.71.0 panel time.

---

## Scope — the DESIGN.md

### Section 1: LLVM coroutine spec summary (~1500 words)

- Read https://llvm.org/docs/Coroutines.html end-to-end
- Summarize the 8 key intrinsics:
  - `llvm.coro.id` — identifies the coroutine
  - `llvm.coro.alloc` — returns i1 indicating whether allocation is needed
  - `llvm.coro.size.i64` — size of the coroutine frame
  - `llvm.coro.begin` — begins the coroutine, returns the handle
  - `llvm.coro.save` — returns a token representing a suspend point
  - `llvm.coro.suspend` — actually suspends; returns i8 indicating resume/cleanup/destroy
  - `llvm.coro.end` — marks the end of the coroutine
  - `llvm.coro.free` — returns the frame pointer for freeing
  - (plus `llvm.coro.resume`, `llvm.coro.destroy`, `llvm.coro.promise`, etc.)
- The coro-split optimization: must run before inlining. Takes a `ramp` function + `resume` / `destroy` / `cleanup` functions.

### Section 2: Existing state of runtime scheduler (~500 words)

- `runtime/native/mapanare_runtime.c` has a cooperative scheduler for the mobile target (`MAPANARE_MOBILE` build flag).
- Current scope: spawn agents, poll inboxes, run handlers synchronously.
- What it lacks: no coroutine handle tracking, no resume-at-yield support.
- Extension needed for desktop: register coroutine handles, drive them via `llvm.coro.resume`, call `llvm.coro.destroy` on cleanup.

### Section 3: Mapanare's target async semantics (~1000 words)

Decide the user-visible semantics:
- **`async fn`**: a function that can suspend. Its return type `T` is sugar for `Future<T>`.
- **`await expr`**: suspends the current coroutine until `expr` (which must be `Future<U>`) resolves. Returns the `U`.
- **Runtime**: the scheduler drives coroutines when they're ready to resume. Cooperative only — no preemption.
- **Interaction with agents**: an `async` agent handler yields at `await` points; the agent scheduler resumes it when the awaited future is ready.
- **Interaction with streams**: `Stream<T>` gets an `next() -> Future<Option<T>>` method. `for await chunk in stream { ... }` desugars to a loop calling `await stream.next()`.

### Section 4: Lowering strategy (~2000 words)

The hardest section. For each piece:

1. **`async fn` definition**: compile to a coroutine:
   - Emit the coro-split prelude (`llvm.coro.id`, `llvm.coro.alloc`, `llvm.coro.begin`)
   - Body lowers normally, with `await` points inserted as suspends
   - Emit the coro-split epilogue (`llvm.coro.end`)
   - Return a `Future<T>` wrapping the coroutine handle
2. **`await expr`**:
   - Call `expr` (which returns a `Future<U>`)
   - Check if the future is already ready — if yes, extract the value directly
   - If not, emit `llvm.coro.save` + `llvm.coro.suspend`
   - On resume, extract the value from the now-ready future
3. **`Future<T>` representation**:
   - A struct with a state machine: `Pending { coroutine_handle }`, `Ready { value }`, `Done`
   - Or simpler: a struct with `{state: i8, value_storage: T}` where `state = 0` means pending, `state = 1` means ready
   - **Pick one**, document why
4. **Pass pipeline placement**:
   - Coro-split must run before the inliner. LLVM's default pipeline puts it at `-O1`; Mapanare's current pipeline doesn't have this stage.
   - Add `coro-split` as a required pass when any `async fn` is present in the module.
5. **Interaction with drop glue**:
   - A coroutine's frame may hold references to heap-allocated values (strings, lists).
   - When the coroutine is destroyed (via `llvm.coro.destroy`), those references must be freed.
   - LLVM's coroutine cleanup path is the right place — emit drop glue in the `cleanup` block.

### Section 5: Runtime scheduler extension (~800 words)

- Extend the mobile cooperative scheduler to desktop:
  - Add `scheduler_register_coroutine(handle)`
  - Add `scheduler_resume_ready()` — main loop that walks registered handles and resumes those whose awaited futures are ready
  - Add `scheduler_destroy_coroutine(handle)` — calls `llvm.coro.destroy`
- **Key question**: when is the scheduler driven? Options:
  - **A**: Inline in `main()` — after `main()` body runs synchronously, enter a scheduler loop until all registered coroutines complete
  - **B**: Background thread — scheduler runs on a separate thread, main thread blocks on futures via condition variables
  - **C**: Event-driven — scheduler runs in response to I/O completions from epoll/kqueue
- **Decision**: A for v4.67.0-v4.75.0 simplicity. B and C are v5.x optimizations.

### Section 6: Risk register (~500 words)

Known hard problems:
- **Debug info for coroutines**: `llvm.dbg.value` after a suspend point can reference a value that's been spilled to the coroutine frame. DWARF can encode this but it's complex. **Scope decision: debug info for async fns is v5.x. In v4.67.0-v4.75.0, debug info is emitted pre-coro-split and whatever survives survives.**
- **Recursive async functions**: a coroutine that awaits itself (or a chain) can blow the heap frame allocation. Document but don't fix in v4.67.0-v4.75.0.
- **Exception safety**: Mapanare has no exceptions; `Result<T, E>` is the error model. No special handling needed.
- **Generic async functions**: `async fn foo<T>() -> T` — each specialization is its own coroutine. Standard monomorphization.
- **`async` agent handlers**: the agent scheduler and the coroutine scheduler must coexist. Document the interaction.

### Section 7: Verification plan (~300 words)

Per release in arcs 8 + 9, what verifies the slice works:
- **v4.68.0** (grammar): parse tests; compile attempt produces a "not yet lowered" rustc-quality error at lower time
- **v4.69.0** (semantic): type check tests
- **v4.70.0** (lowering pt 1): prelude appears in IR; compile attempt may still fail at run time or link time
- **v4.72.0** (lowering pt 2): complete coroutine IR; `llvm-as` clean
- **v4.73.0** (scheduler): runs a minimal `async fn foo() { await delay(100) }` and completes without crashing
- **v4.74.0** (stream): `for await` works with `Stream<T>`
- **v4.75.0** (end-to-end): the golden test `53_real_await.mn` runs with multiple suspension points

### Section 8: Rejected options (~400 words)

- **Green threads** — considered, rejected. Stack-switching adds complexity that LLVM coroutines avoid.
- **State-machine generation without LLVM coroutines** — considered, rejected. Would require Mapanare to reimplement coro-split by hand, re-deriving what LLVM already does.
- **CPS transformation** — considered, rejected. CPS-style transformation is elegant but has worse codegen than LLVM coroutines.
- **Poll-based futures (Rust-style, no coro-split)** — considered. Rejected because Rust's approach requires `Pin<&mut Self>` and self-referential structs, which Mapanare's type system doesn't currently support. LLVM coroutines abstract this.
- **Fibers via `makecontext`/`swapcontext`** — considered, rejected. Portable but slow; also deprecated in POSIX.

---

## Phase 1 — Study

- [ ] Read `https://llvm.org/docs/Coroutines.html` end-to-end (~3 hours)
- [ ] Read Clang's coroutine lowering: `clang/lib/CodeGen/CGCoroutine.cpp` + `llvm/lib/Transforms/Coroutines/*.cpp` (~6 hours)
- [ ] Compile a simple C++20 coroutine with `clang++ -S -emit-llvm -O0 -std=c++20 -fcoroutines` and read the generated IR (~2 hours)
- [ ] Compile a simple Rust async fn with `rustc -C opt-level=0 --emit=llvm-ir` and compare (~2 hours)
- [ ] Read the Swift async lowering notes (public design docs)
- [ ] Read Gor Nishanov's 2016 coroutine-split patches commit messages on LLVM
- [ ] Read the Carruth review comments from 2016 — they anticipate many of the pitfalls

## Phase 2 — Write DESIGN.md

- [ ] All 8 sections per the scope above
- [ ] Target: ~7500 words
- [ ] Code examples in each lowering section

## Phase 3 — Review

- [ ] Rattler (LLVM lens) reads the whole document, flags concerns
- [ ] Anaconda (toolchain) reviews the pass pipeline section
- [ ] Coral (language design) reviews the semantics section
- [ ] Mamba (runtime) reviews the scheduler section
- [ ] Iterate based on review comments — the design doc should be robust enough that implementation phase can follow it without surprises

## Phase 4 — Fixed-point

- [ ] No code changes; fixed-point unchanged trivially

## Phase 5 — Closeout

- [ ] Standard closeout (lint, tests — no functional changes)
- [ ] `VERSION` → 4.67.0
- [ ] `CHANGELOG.md [4.67.0]` — design-only release. Recovery-arc precedent: SESSION_REPORT is the design doc plus a one-page summary.
- [ ] `docs/roadmap/v4/v4.67.0/SESSION_REPORT.md` — one page summary of decisions made in DESIGN.md, plus the review feedback

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | DESIGN.md exists with all 8 sections | file exists + section headers |
| 2 | LLVM coroutine intrinsic summary section complete | grep section headers |
| 3 | Runtime scheduler extension plan documented | section 5 |
| 4 | Lowering strategy documented with IR examples | section 4 |
| 5 | Risk register includes debug info + recursion + generics | section 6 |
| 6 | Verification plan per arc 8+9 release | section 7 |
| 7 | Rejected options documented | section 8 |
| 8 | Review feedback from 4 reviewers (Rattler, Anaconda, Coral, Mamba) recorded | SESSION_REPORT notes |
| 9 | Design approved by at least Rattler (veto authority on LLVM decisions) | sign-off in SESSION_REPORT |

---

## What v4.67.0 does NOT do

- **Any code changes**
- **Grammar changes**
- **Runtime changes**
- **Tests beyond existing ones**
- **User-visible features**

Literally nothing ships except DESIGN.md and SESSION_REPORT.md. The value is in the plan.

---

## Reference

- LLVM Coroutines — https://llvm.org/docs/Coroutines.html
- Clang `CGCoroutine.cpp` — `clang/lib/CodeGen/CGCoroutine.cpp`
- LLVM `CoroSplit.cpp` — `llvm/lib/Transforms/Coroutines/CoroSplit.cpp`

---

## After v4.67.0

v4.68.0 ships grammar + AST + parser for `async fn` / `await expr`. Delta review mandatory (new keywords). Implementation follows DESIGN.md §3 precisely.
