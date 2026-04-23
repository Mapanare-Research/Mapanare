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

## Expected panel impact

- All reviewers: +0.05–0.1 (clean docs, no stale claims)
- Primary beneficiaries: Boa (docs), Coral (SPEC), Anaconda (audit)

## Exit criteria

- SPEC version header matches v5.7.1
- `docs/known_issues.md` has no items closed by v5.4.0–v5.7.0
- README benchmark table current
- `PARITY_GAPS.md` audit pass — all v5.4.0–v5.7.0 closures verified
