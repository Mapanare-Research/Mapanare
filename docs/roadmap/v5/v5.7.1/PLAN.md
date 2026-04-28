# v5.7.1 — SPEC + docs polish (pre-panel)

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.7.0 shipped (66/66 goldens)
**Estimated work:** 1–2 hours

---

## Goal

Final docs + SPEC refresh before the v5.8.0 re-panel. Same pattern as
v5.3.3 (which polished before the originally-planned panel). With
66/66 goldens and all Sh.* items closed, the SPEC and docs should
reflect the full feature surface.

## Items

| ID | Severity | Fix | Effort |
|----|----------|-----|--------|
| **SPEC refresh** | LOW | Bump SPEC version to v5.7.1; update sections for async, tensor, closure-typed, or-pattern to reflect self-hosted parity | 1 hour |
| **README 66/66** | LOW | Verify 66/66 badge, benchmark numbers current, feature list reflects async + tensor + drop-glue | 15 min |
| **PARITY_GAPS audit** | LOW | Verify all Sh.* items in Historical; verify no open items remain except Li.1 and v6.0 scope | 15 min |
| **Known issues cleanup** | LOW | Remove closed items from `docs/known_issues.md` | 10 min |
| **Culebra clean-baseline** | LOW | Final culebra baseline + triage on the 66/66 stage2.ll. Save to `docs/roadmap/v5/v5.7.1/culebra/`. This becomes the **panel input** for v5.8.0 — every reviewer can compare against the v5.6.10 anchor. Aggregate the v5.6.9–v5.7.1 journals into `arc-journal.jsonl`. | 30 min |
| **Culebra docs page** | LOW | Add `docs/guides/culebra.md` describing the v3.0.0 workflow Mapanare uses (triage → bisect → fixedpoint, journal, FP suppression). Cross-reference from CLAUDE.md and the contributor guide. | 30 min |

## Expected panel impact

- All reviewers: +0.05–0.1 (clean docs, no stale claims)
- Primary beneficiaries: Boa (docs), Coral (SPEC), Anaconda (audit)
- **NEW: Rattler / Cobra / Anaconda get culebra triage as primary
  diagnostic input** — eliminates "no measurement methodology" objections
  and gives reviewers a structured artifact to grade.

## Exit criteria

- SPEC version header matches v5.7.1
- `docs/known_issues.md` has no items closed by v5.4.0–v5.7.0
- README benchmark table current
- `PARITY_GAPS.md` audit pass — all v5.4.0–v5.7.0 closures verified
- `docs/roadmap/v5/v5.7.1/culebra/baseline-end.json` saved
- `docs/roadmap/v5/v5.7.1/culebra/arc-journal.jsonl` aggregated
  (concatenates v5.6.9 → v5.7.1 per-release journals)
- `docs/guides/culebra.md` published; CLAUDE.md cross-references it
- `.culebra-ignore` reviewed; any v5.6.x-era stale entries pruned
