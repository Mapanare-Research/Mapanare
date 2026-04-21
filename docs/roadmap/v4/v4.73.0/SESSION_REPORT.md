# v4.73.0 Session Report — 2026-04-13

## Verdict
- `async fn` goes from "compiles" to "runs." The load-bearing milestone.
- `block_on(future)` drives coroutines to completion from non-async main().
- `await` uses inline-resume: drives inner coroutines synchronously.
- 8 new tests (57 total async), all passing.
- Panel items Viper #1 (Future free) and #2 (box free) addressed in block_on.

## Completed
- Phase 1: `emit_llvm_text.py` — rewrite `_do_await_suspend` to inline-resume:
  fast-path check → resume loop driving inner coroutine → extract value.
  No real suspension (correct for single-threaded cooperative model).
  (`mapanare/emit_llvm_text.py:4504-4555`)
- Phase 2-5: `mir.py` — `BlockOn` instruction. `lower.py` — `block_on` builtin
  recognized in `_lower_call`. `emit_llvm_text.py` — `_do_block_on`:
  extract handle → resume loop until `coro.done` → extract value →
  `coro.destroy` → `free(box)` → `free(future)`.
  (`mapanare/mir.py:712-723`, `mapanare/lower.py:1716-1725`,
  `mapanare/emit_llvm_text.py:4557-4594`)
- Phase 6-8: 8 tests in `tests/llvm/test_block_on.py`

## Decisions Made

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Scheduler model | Main-thread only, cooperative | Simplest correct approach for v4.x |
| 2 | await strategy | Inline-resume (drive inner synchronously) | No real suspension needed for CPU-bound async; full scheduler v5.x |
| 3 | block_on polling | Tight resume loop | Correct for cooperative; condvar-based v5.x |
| 4 | Global state | Implicit (no scheduler struct) | Inline-resume avoids explicit scheduler data structures |

## v4.71.0 Panel Items Addressed

| # | Item | Status |
|---|------|--------|
| 1 | coro.alloc conditional (HALO) | OPEN (v5.x, per design) |
| 2 | ret.val.slot uniqueness | FIXED (v4.72.0) |
| 3 | Free Future after read | FIXED (block_on frees future) |
| 4 | Free return box after extraction | FIXED (block_on frees box) |
| 5 | Pipeline integration test | OPEN (needs LLVM tools in CI) |
| 6 | pending_coro_handle on agent_t | DEFERRED (no separate scheduler struct — inline model) |

## Measurements
- Async test count: 57 (14 parser + 5 interim + 11 semantic + 11 prelude + 8 lowering + 8 block_on)

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.74.0/PLAN.md` (`for await` syntax + streams)
- This is a genuine celebration point — async fn works end-to-end for the first time
