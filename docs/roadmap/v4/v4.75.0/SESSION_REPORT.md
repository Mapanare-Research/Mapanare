# v4.75.0 Session Report — 2026-04-13

## Verdict
- **A1 CLOSED.** The v4.19.0 hollow-feature ghost is finally laid to rest.
  56-release carry-forward (longest in project history after A2's 6 cycles)
  resolved with real LLVM coroutine intrinsics backing the async/await syntax.
- 3 async golden tests: 55_async_basic, 56_async_await, 57_real_await.
- 8 new verification pytests. 70 total async tests across arcs 8+9.

## A1 Closure — The Story

**v4.19.0** (2026-04-09): `async`/`await` keywords added. Lowerer treats
`await expr` as pure identity — `return self._lower_expr(expr.expr)`.

**v4.24.0**: CHANGELOG claims "async/await wired." False.

**v4.26.0**: 7-reviewer panel flags hollow feature (Viper H2, Rattler #5).
Aggregate drops from 9.79 to ~8.2. Recovery arc begins.

**v4.30.0**: Path B strike — `async`/`await` removed from grammar entirely.
Soft-reserved for "v5.0.0 roadmap item." Golden tests 44 and 46 deleted.

**v4.67.0**: DESIGN.md locks LLVM switched-resume ABI. 4 reviewers approve.

**v4.68.0**: Grammar + AST + parser return. Delta review PASS.

**v4.69.0**: `Future<T>` type. Semantic analysis. Three rustc-quality errors.

**v4.70.0**: Coroutine prelude emits. `presplitcoroutine` + `coro.id`/`begin`/`end`.

**v4.71.0**: Arc 8 panel. PASS WITH NOTES (8.29/10). Foundation approved.

**v4.72.0**: `await` compiles to real suspension IR.

**v4.73.0**: `block_on(future)` + inline-resume. **async fn runs end-to-end.**

**v4.74.0**: `for await` syntax. Delta review PASS.

**v4.75.0**: Golden tests 55-57. **A1 CLOSED.** 70 async tests.

## Completed
- Phase 3: `tests/golden/55_async_basic.mn` — simple async fn + block_on
- Phase 3: `tests/golden/56_async_await.mn` — nested await chain
- Phase 3: `tests/golden/57_real_await.mn` — 3 await points, fanout pattern
  (the test the v4.26.0 panel flagged as missing)
- Phase 8: A1 CLOSED in `.reviews/CARRY_FORWARD.md`
- Phase 9: 8 tests in `tests/llvm/test_async_golden.py`

## Measurements
- Golden test count: 57 (was 54 — +3 async)
- Async test count: 70 (62 prior + 8 golden verification)
- A1 cycle count at closure: 56 releases (v4.19.0 → v4.75.0)

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.76.0/PLAN.md` (Arc 9 panel — FINAL panel of 45-release plan)
- The v4.76.0 panel grades the complete coroutine feature across arcs 8+9
