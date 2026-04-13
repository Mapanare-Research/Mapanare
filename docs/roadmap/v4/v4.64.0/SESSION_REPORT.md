# v4.64.0 Session Report — 2026-04-12

## Verdict
- All 12 exit criteria green
- Every source-origin instruction has !dbg attachment
- llvm-dwarfdump --verify passes with line table populated
- DWARF line table shows correct source lines

## Completed
- Phase 1: _get_debug_location with scope-aware cache (from v4.62.0 infrastructure)
- Phase 2: _L() hook auto-appends !dbg when debug enabled + span available
- Phase 3: _current_span set before each instruction dispatch
- Phase 4: ret void patching and _is_term() fixed for !dbg suffixes
- Phase 5: 6 new tests in test_dwarf_line_info.py (28 total DWARF tests)

## Measurements
- Instructions with !dbg: all source-origin instructions
- Prologue allocas: no !dbg (synthesized, no span) — acceptable
- llvm-dwarfdump --verify: "No errors"
- DWARF line table: populated with correct source lines

## Decisions Made
- Line metadata via _L() hook (minimal change surface — all instruction emitters benefit)
- Synthesized instructions without spans get no !dbg (acceptable for prologues)
- ret void patching preserves !dbg suffix

## Next Session Should Start With
- Read docs/roadmap/v4/v4.65.0/PLAN.md (DILocalVariable + llvm.dbg.declare)
