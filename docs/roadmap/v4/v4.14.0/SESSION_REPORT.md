# v4.14.0 Session Report — 2026-04-09

## Completed

- Fixed null pointer dereference in `mn_list_detach` (`runtime/native/mapanare_core.c:874`) — added NULL check after `mn_list_rc()` when COW magic is corrupted
- Fixed cross-module list push element type in `emit_list_push_call` (`mapanare/self/emit_llvm.mn:1352`) — added fallback to list type args when element MIR type resolves to i64
- main.mn stage2: COMPILE_FAIL (Signal 11) → OK (749 fn, 109,347 lines)
- 40/40 golden tests pass
- 11/11 stage2 modules valid
- Added regression test: `tests/llvm/test_break_nested.py` (3 tests)
- Version bumped to 4.14.0

## Issues Found

- Culebra `break-inside-nested-control` template has 42 false positives: it flags `return` statements inside for loops (which produce `ret` in LLVM IR) as "dropped break". Actual `break` statements are correctly lowered to `br label %for_exit`. The template cannot distinguish `ret` (from return) from a missing `br %for_exit` (dropped break).
- The original plan expected 3 CRITICAL findings; the actual count was 42, all false positives.
- The Python lowerer's break handling is correct — verified by IR inspection of `collect_targets` (mir_opt.mn) and `types_compatible` (semantic.mn).

## Decisions Made

- Skipped .mn loop rewrites (Phase 2 of plan) — unnecessary since break lowering is correct
- Skipped Python lowerer break fix (Phase 5 of plan) — no bug exists
- Treated Culebra false positives as known issue rather than trying to modify all 42 .mn sites
- Fixed the root cause of main.mn crash (NULL check in runtime) rather than the planned approach (escape analysis in emit_llvm_text.py)
- The IR type mismatch was a separate bug in the self-hosted emitter (cross-module type resolution), not related to drop glue

## Next Session Should Start With

- Read `docs/roadmap/v4/v4.15.0/PLAN.md` and `PROMPT.md`
- v4.15.0: Module-Level Let + MIRType Enum — LetDef AST, parser support, MIRType kind from String to TypeKind enum
