# v4.99.0 Session Report — 2026-04-13

## Verdict

**Panel aggregate: 6.59/10. Option B: continue v4.100.0+. v5.0.0 NOT tagged.**

3 NEEDS WORK (Rattler 6.5, Viper 5.5, Anaconda 6.5), 1 conditional pass
(Mamba 6.1), 1 pass with significant notes (Cobra 6.5), 2 pass with
notes (Coral 7.5, Boa 7.5).

## Panel Results

| Reviewer | Grade | Verdict | Key Finding |
|----------|-------|---------|-------------|
| Rattler | 6.5/10 | NEEDS WORK | Binary broken by tagged-pointer UB; O2 speedup claims overstated |
| Viper | 5.5/10 | NEEDS WORK | Tagged pointer UB is confirmed production regression; coroutine frame coupling fragile |
| Anaconda | 6.5/10 | NEEDS WORK | 0/61 golden tests pass; async can't link; test pass rate unknown |
| Cobra | 6.5/10 | PASS WITH NOTES | Fixed-point is real but byref size heuristic diverges; tagged pointer is impl-defined not UB |
| Coral | 7.5/10 | PASS WITH RESERVATIONS | Language design solid; else/sino, closure types, list indexing are gaps |
| Boa | 7.5/10 | PASS WITH NOTES | DX good via Python bootstrap; native binary path broken and undisclosed |
| Mamba | 6.1/10 | CONDITIONAL PASS | Tagged pointer fix is 3-4 hours; scheduler export already in source; arena excellent |

## Completed

- Phase 1-2: MEASUREMENTS.md with line counts, test counts, benchmarks, known blockers
- Phase 3: RETROSPECTIVE.md — full v4.x journey (99 releases)
- Phase 4: PRE_PANEL_AUDIT.md — fact-checked arc 10-14 claims; found 3 FAILED items
- Phase 5: 7-reviewer panel run in parallel
- Phase 6: V5_DECISION.md — Option B applied, v4.100.0 opens
- Phase 7: Closeout (CHANGELOG, roadmap, CLAUDE.md, SESSION_REPORT)

## Measurements

- Self-hosted .mn: 38,824 lines
- Python bootstrap .py: 38,526 lines
- C runtime: 14,243 lines
- pytest collected: 5,374 tests
- Golden tests: 61 programs
- Panel aggregate: 6.59/10 (lowest since v4.26.0 crisis at 8.2)

## Decisions Made

- **Panel scope:** Holistic with arc-level commentary (as planned)
- **Decision rule:** Option B (6.59 < 9.0, 3 NEEDS WORK)
- **VERSION:** 4.100.0 (Option B)
- **v5 tag:** NOT created

## Known Issues (Panel Docket, 11 items)

1. CRITICAL: Tagged-pointer UB in mapanare_core.c
2. CRITICAL: List indexing bug
3. HIGH: Rebuild libmapanare_rt.a with scheduler
4. HIGH: Verify else/sino end-to-end
5. HIGH: Fix closure type annotations
6. MEDIUM: Disclose binary corruption in README
7. MEDIUM: Fix byref size heuristic divergence
8. MEDIUM: Coroutine frame layout coupling
9. MEDIUM: String concat performance
10. LOW: Document keyword collision space
11. LOW: Async error messages

## Next Session Should Start With

- Fix tagged-pointer UB (v4.100.0 — the single highest-impact fix)
- Replace `mn_tag_heap` bit-tagging with `int8_t is_heap` field in MnString
- Rebuild mnc-stage1, re-run golden tests
- This unblocks everything: golden tests, fixed-point, async linking
