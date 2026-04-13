# v4.70.0 Session Report — 2026-04-13

## Verdict
- First real coroutine IR emitted. async fn produces structurally correct LLVM IR
  with the full coroutine prelude/epilogue wrapper.
- presplitcoroutine attribute, 6 coro intrinsics used, 12 declared.
- 11 new tests (coroutine prelude verification), all passing.
- 41 total async tests across all releases.
- await still errors — suspension lowering arrives at v4.72.0.

## Completed
- Phase 1: `mir.py` — `MIRFunction.is_async` field (`mapanare/mir.py:771`)
- Phase 2: `lower.py` — AsyncFnDef now calls `_lower_fn()` + sets `is_async=True`.
  Replaced "under construction" error. await error updated to v4.72.0 target.
  (`mapanare/lower.py:846-852,1432-1446`)
- Phase 3-5: `emit_llvm_text.py` — coroutine prelude/epilogue for async fns:
  - `presplitcoroutine` attribute on `define` line
  - `coro.entry:` block with `coro.id`, `coro.alloc`, `coro.begin`
  - Future struct allocation (`malloc(16)`, `{i8, ptr}`)
  - Initial suspend (`coro.save` + `coro.suspend`)
  - Return rewriting: stores value in Future + branches to `coro.final`
  - `coro.final:` block with final suspend
  - `coro.cleanup:` block with `coro.free` + `free`
  - `coro.ret:` block with `coro.end`
  - 12 coroutine intrinsic declarations
  - malloc/free auto-declared for async modules
  (`mapanare/emit_llvm_text.py:857-870,2175-2275`)
- Phase 6-8: 11 tests in `tests/llvm/test_coroutine_prelude.py` + updated 2 interim tests

## Decisions Made

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Frame allocation | Always heap via malloc | Simpler; stack optimization (HALO) is v5.x |
| 2 | Pass pipeline | Trust LLVM default -O1 | presplitcoroutine attribute is sufficient |
| 3 | Frame layout | Opaque (trust CoroSplit) | Drop glue in cleanup block per LLVM ABI |

## Measurements
- IR line count: async fn adds ~30 lines of coroutine wrapper per function
- Golden test count: unchanged (no golden tests use async yet)
- Pytest new: 11 tests
- Culebra findings: unchanged (main.ll not affected)

## Verification Results
- 41/41 async tests pass (14 parser + 5 interim + 11 semantic + 11 prelude)
- `presplitcoroutine` present on async fn `define` lines
- `coro.id`, `coro.begin`, `coro.suspend`, `coro.end` emitted in correct order
- Future `{i8, ptr}` struct allocated and initialized
- Return values stored into Future before final suspend
- sync functions unaffected (no coro intrinsics in their IR)
- await errors with v4.72.0 pointer

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.71.0/PLAN.md` (Arc 8 panel release)
- Arc 8 panel grades v4.68.0-v4.70.0 (grammar → semantic → lowering)
