# Mapanare v4.126.0 — Golden Test Push: Target 40/64+ Native

> **Buffer release 1.** The v4.120.0 panel closed at 8.21 with Option B.
> The closeout arc (v4.121.0-v4.129.0) hardens the codebase before the
> next v5 gate at v4.130.0. This release pushes native golden test
> pass count higher. Starting from ~26/64 through mnc-stage1, the
> target is 40/64+ by fixing the easiest failures first.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.125.0
**Delta review:** No
**Full panel:** No (deferred to v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Low-hanging golden test fixes. Push 26 -> 40+ through mnc-stage1.

---

## Scope

The self-hosted compiler (mnc-stage1) passes ~26/64 golden tests natively.
The remaining ~38 fail for a mix of reasons: missing runtime function
exports, wrong types in specific codegen paths, missing feature flags,
lowerer gaps, and genuine emitter bugs. This release triages all 64
tests, categorizes every failure, and fixes the easiest ones first.
The target is at least 14 additional passes (from ~26 to 40+).

This is triage + fix work, not systemic refactoring. If a test fails
because of a deep architectural issue (e.g., cross-module generics),
it gets documented and deferred. If it fails because of a missing
`declare` for a runtime function, that gets fixed in minutes.

## Phase 1 — Run all 64 golden tests, categorize failures

- [ ] Build mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run all 64 golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record exact pass/fail for each test
- [ ] For each failure, classify into one of:
  - **E** (emitter bug) — wrong IR generation for a specific construct
  - **L** (lowerer bug) — MIR lowering produces incorrect output
  - **M** (missing feature) — feature not yet implemented in self-hosted compiler
  - **R** (runtime gap) — missing runtime function export or declaration
  - **T** (type error) — wrong type in a specific codegen path
- [ ] Write `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` with per-test classification

## Phase 2 — Fix the easiest failures (category R + T)

- [ ] **Runtime gaps (R)**: add missing `declare` statements for runtime functions in `mapanare/self/emit_llvm.mn` or `emit_llvm_ir.mn`
- [ ] **Type errors (T)**: fix wrong type annotations or casts in specific codegen paths
- [ ] Re-run golden tests after each batch of fixes
- [ ] Target: clear all R and T failures

## Phase 3 — Fix emitter + lowerer bugs (category E + L, easy cases)

- [ ] For each E/L failure, estimate fix complexity (1 = trivial, 2 = moderate, 3 = hard)
- [ ] Fix all complexity-1 issues
- [ ] Fix complexity-2 issues if time permits
- [ ] Skip complexity-3 issues — document them for future releases
- [ ] Re-run golden tests after each fix

## Phase 4 — Document remaining failures

- [ ] Update `GOLDEN_TRIAGE.md` with final status:
  - Passed (with which fix)
  - Failed — category + root cause + estimated complexity
- [ ] Record final pass count: target 40/64+
- [ ] Compare with v4.125.0 baseline

## Phase 5 — LOW sweep + closeout

- [ ] `make test` — all green
- [ ] `make lint` — all clean
- [ ] Rebuild mnc-stage1 with all fixes: `bash scripts/rebuild.sh`
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.126.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Golden pass count improved by >= 14 (from ~26 to 40+) | test log before/after |
| 2 | All 64 failures categorized (E/L/M/R/T) | `GOLDEN_TRIAGE.md` |
| 3 | Remaining failures documented with root cause + complexity | `GOLDEN_TRIAGE.md` |
| 4 | No regressions in previously-passing golden tests | test log |
| 5 | `make test` green | CI logs |
| 6 | `make lint` clean | CI logs |
| 7 | Standard closeout clean | CHANGELOG + SESSION_REPORT + VERSION bump |

---

## What this release does NOT do

- **Fix systemic issues.** If a test fails because of cross-module generics or full trait dispatch in the self-hosted compiler, that is documented and deferred.
- **Refactor the emitter.** Only targeted, per-test fixes. No architectural changes to `emit_llvm.mn`.
- **Touch the Python bootstrap.** All changes are in the self-hosted compiler sources (`mapanare/self/*.mn`).
- **Run a panel.** The next panel is v4.130.0.
- **Guarantee 64/64.** 40+ is the target. Each additional test above 40 is bonus.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Actual baseline is lower than ~26 (regressions from v4.121.0-v4.125.0 changes) | low | medium | Phase 1 establishes the real baseline before any fixes |
| Most failures are category M (missing feature), not fixable with targeted patches | medium | high | Document and defer. Even 30/64 with a complete triage is valuable for the v4.130.0 panel. |
| Fixing one test breaks another (emitter changes have side effects) | medium | medium | Re-run full golden suite after every fix batch, not just the target test |
| Rebuild cycle too slow for iterative fixing | low | low | Use `bash scripts/rebuild.sh quick` for fast iteration, full rebuild only at end |

---

## After v4.126.0

v4.127.0 — self-hosted fixed-point refinement. Push toward cleaner stage2-vs-stage3 diff. The golden test triage from v4.126.0 feeds directly into understanding which emitter behaviors diverge.
