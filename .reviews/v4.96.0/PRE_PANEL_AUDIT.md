# v4.96.0 Pre-Panel Audit — Arc 13 Runtime + Concurrency Maturity

**Date:** 2026-04-13
**Arc:** 13 (v4.92.0-v4.95.0) — Async runtime + StringBuilder
**Prior panel:** v4.91.0 (Arc 12, MIR optimizer) — 8.57/10 PASS

## What this panel grades

| Version | Feature | Lines | Tests |
|---------|---------|-------|-------|
| v4.92.0 | Real suspension at await (coro.suspend) | +579 | 6 updated, llvm-as clean |
| v4.93.0 | Multi-threaded work-stealing scheduler | +482 | Golden 59, llvm-as clean |
| v4.94.0 | Async benchmark suite (5 x 3 languages) | +978 | Python baselines measured |
| v4.95.0 | StringBuilder + O(n^2) string fix | +282 | MIR tests pass, stdlib refactored |

**Total new code:** ~2,321 lines across 4 releases.

## Pre-panel verification

| Check | Result |
|-------|--------|
| Core compiler tests | 1412/1412 PASS (8 pre-existing failures) |
| Async golden tests (55-59) | 5/5 llvm-as OK |
| C runtime compile (core.c) | Clean |
| C runtime compile (runtime.c) | Clean |
| MIR optimizer tests | 73/73 PASS |
| Emitter imports | Clean |

## Key questions for the panel

1. **Suspension correctness (Rattler):** Does the real coro.suspend emission match DESIGN.md 4.7.2? Does the fast-path readiness check + drive-once-then-suspend pattern preserve semantics?
2. **Scheduler safety (Viper):** Can a coroutine frame be resumed on two threads simultaneously? Is the Chase-Lev deque correctly implemented? Does condvar parking avoid missed wakeups?
3. **StringBuilder quality (Mamba):** Is the exponential growth strategy correct? Does to_string transfer ownership safely? Does the AI stdlib refactoring actually eliminate O(n^2)?
4. **ABI stability (Cobra):** Do the __mn_coro_scheduler_* symbols maintain backward compatibility from v4.92.0 through v4.93.0?
5. **Benchmark validity (Anaconda):** Are the 5 async benchmarks representative? Is the Python-only baseline sufficient, or is the Go gap a problem?
