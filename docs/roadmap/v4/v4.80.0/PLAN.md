# Mapanare v4.80.0 — Documentation: Async Cookbook + SPEC Futures + gdb Tutorial

> **Arc 10 release 4.** The carry-forward ledger is at zero. The
> integration test harness is running. This release addresses the
> documentation gaps that Boa has flagged at every panel since Arc 3:
> no async cookbook chapter, no formal SPEC section on futures, no
> debugger tutorial using the DWARF output from Arc 7.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.79.0
**Delta review:** No
**Full panel:** No (v4.81.0)
**Estimated work:** 1 sprint
**Theme:** Three documentation deliverables that close recurring panel feedback.

---

## Scope

This is a documentation-only release. No compiler changes, no runtime changes, no new tests (beyond verifying that code examples in the docs compile and run). The three deliverables are:

1. **Async cookbook chapter** (`docs/cookbook/async.md`) — progressive tutorial from basic `async fn` through `await`, `block_on`, fan-out patterns, and `for await`. Code examples drawn from golden tests 55-57.

2. **SPEC Futures section** (`docs/SPEC.md` new section) — formal specification of `Future<T>` type semantics, `await` suspension model, `block_on` runtime behavior, coroutine frame lifecycle, and memory model. This is the normative reference that the cookbook teaches from.

3. **Debugging tutorial** (`docs/guides/debugging.md`) — gdb/lldb walkthrough using the `-g` DWARF output from Arc 7 (v4.62.0-v4.65.0). Shows how to set breakpoints on `.mn` functions, inspect variables, step through async code, and use `bt` on crash dumps.

## Phase 1 — Async cookbook chapter

- [ ] Create `docs/cookbook/async.md`
- [ ] Structure:
  1. **Introduction** — what async/await means in Mapanare, when to use it
  2. **Basic async fn** — `async fn compute() -> Int`, calling from `main` via `block_on`
     - Code: adapted from `tests/golden/55_async_basic.mn`
  3. **Await chains** — `async fn` calling another `async fn` with `await`
     - Code: adapted from `tests/golden/56_async_await.mn`
  4. **Fan-out pattern** — launching multiple async fns, awaiting all results
     - Code: new example showing concurrent computation
  5. **`for await` loops** — consuming async streams
     - Code: adapted from golden tests using `for await`
  6. **`block_on` from sync code** — the bridge between sync `main` and async functions
     - Code: adapted from `tests/golden/57_real_await.mn`
  7. **Common pitfalls** — blocking in async, deadlock patterns, memory considerations
- [ ] Every code example must be a complete, compilable `.mn` program
- [ ] Every code example verified: `python -m mapanare emit-llvm <example> -o /dev/null` succeeds

## Phase 2 — SPEC Futures section

- [ ] Add new section to `docs/SPEC.md`: "Futures and Async"
- [ ] Subsections:
  1. **`Future<T>` type** — definition, type rules, relationship to `async fn` return types
  2. **`async fn` declaration** — syntax, semantic constraints (cannot be `main`, must return a type)
  3. **`await` expression** — suspension semantics, type inference (`await expr` where `expr: Future<T>` yields `T`)
  4. **Suspension model** — LLVM coroutine intrinsics as the implementation strategy; split into ramp/resume/destroy; frame allocation
  5. **`block_on` builtin** — blocks current thread until future resolves; drives the cooperative scheduler
  6. **`for await` loops** — syntactic sugar for `loop { match stream.next_async() { ... } }`
  7. **Memory model** — coroutine frame is heap-allocated via `llvm.coro.alloc`; freed via `llvm.coro.free` after final suspend or cancellation; drop glue runs in cleanup path
  8. **Cancellation** — v5.x (document as future work with a note that coroutine frames are properly freed on scope exit)
- [ ] Cross-reference the cookbook chapter for tutorial-style explanations
- [ ] Cross-reference DESIGN.md (`docs/roadmap/v4/v4.67.0/DESIGN.md`) for the original design rationale

## Phase 3 — Debugging tutorial

- [ ] Create `docs/guides/debugging.md`
- [ ] Structure:
  1. **Prerequisites** — `mapanare build -g` flag (DWARF emission from v4.62.0+), gdb/lldb installed
  2. **Compiling with debug info** — `mapanare build -g hello.mn -o hello`
  3. **Setting breakpoints on .mn functions** — `break mn_user_main`, `break my_function`
  4. **Inspecting variables** — `info locals`, `print x`, struct field access
  5. **Stepping through code** — `next`, `step`, `continue`, `finish`
  6. **Debugging async code** — breakpoints in async fn bodies, inspecting coroutine state
  7. **Crash debugging** — `bt` on segfault, mapping stack frames to `.mn` source lines
  8. **Using Valgrind** — `valgrind ./my_program`, common patterns (uninit reads, leaks)
  9. **Tips** — `MAPANARE_DEBUG=1` env var, runtime assertion messages, common gdb scripts
- [ ] Include terminal screenshots or `asciinema`-style session transcripts where helpful
- [ ] All example sessions use code from the golden test corpus

## Phase 4 — Update cookbook index

- [ ] Update `docs/cookbook/README.md` (or create if it does not exist) with table of contents including the new async chapter
- [ ] Update `docs/guides/README.md` (or create if it does not exist) with the debugging tutorial
- [ ] Ensure cross-links from `docs/README.md` or `docs/SPEC.md` to the new content
- [ ] Check all internal links (`[text](path)`) resolve to real files

## Phase 5 — Verify code examples

- [ ] Extract every code block from `docs/cookbook/async.md` into temporary `.mn` files
- [ ] Compile each: `python -m mapanare emit-llvm <file> -o /dev/null`
- [ ] For examples that are meant to run: verify through the integration pipeline (v4.77.0 harness)
- [ ] Fix any compilation failures in the examples (adjust the docs, not the compiler)

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.80.0]` entry — "Documentation: async cookbook, SPEC Futures section, gdb/lldb debugging tutorial"
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `docs/cookbook/async.md` exists with 7 sections | file + word count |
| 2 | `docs/SPEC.md` has a Futures and Async section | grep for section heading |
| 3 | `docs/guides/debugging.md` exists with 9 sections | file + word count |
| 4 | All code examples in the cookbook compile | compilation log |
| 5 | Cookbook index updated with async chapter | diff |
| 6 | SPEC Futures section cross-references cookbook and DESIGN.md | link check |
| 7 | No broken internal links in new docs | manual or scripted check |
| 8 | `make test` + `make lint` pass (no regressions) | CI log |

---

## What this release does NOT do

- **New features** — no compiler changes, no runtime changes.
- **Fix anything** — this is documentation-only. If code examples reveal bugs, file them for the next arc.
- **Structured concurrency** — the cookbook documents what exists (cooperative, single-threaded async). Structured concurrency is v5.x.
- **Full API reference** — the debugging guide is a tutorial, not a reference manual. API reference is separate work.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Code examples in the cookbook do not compile due to recent changes | medium | medium | Verify every example as part of Phase 5. Fix the docs to match the compiler, not vice versa |
| SPEC Futures section contradicts DESIGN.md | low | high | Cross-reference DESIGN.md explicitly. Any contradiction is resolved in favor of the implementation |
| Debugging tutorial assumes gdb features not available on all platforms | medium | low | Note platform-specific commands (gdb on Linux, lldb on macOS). WSL users get gdb |
| Large doc surface increases maintenance burden | low | medium | Keep examples minimal. Reference golden tests rather than duplicating code |

---

## After v4.80.0

v4.81.0 is the Arc 10 panel. Seven reviewers grade v4.77.0-v4.80.0: integration test harness, carry-forward zero, and documentation. Special focus: Anaconda (integration pipeline), Boa (documentation quality), Viper (items 49/50 memory fixes).
