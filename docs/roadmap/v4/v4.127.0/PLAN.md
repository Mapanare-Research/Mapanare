# Mapanare v4.127.0 — Self-Hosted Fixed-Point Refinement

> **Buffer release 2.** Push toward a cleaner stage2-vs-stage3 diff.
> The fixed-point verification script (`verify_fixed_point.sh`) runs
> 3-stage self-compilation. This release measures the current diff,
> categorizes divergences, fixes the cosmetic ones, and records the
> delta. No expectation of perfect convergence -- just measurable
> progress.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.126.0
**Delta review:** No
**Full panel:** No (deferred to v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Measure, categorize, and reduce the fixed-point diff.

---

## Scope

The self-hosted compiler's fixed-point verification compiles
mnc-stage1 through itself three times: stage1 (from Python) produces
stage2 IR, stage2 produces stage3 IR. Perfect convergence means
stage2 == stage3. In practice, the diff contains cosmetic divergences
(different label names, constant emission order, attribute sets) and
possibly semantic divergences (different code generation decisions).

This release establishes a precise measurement of the current diff,
categorizes every divergence, and fixes the cosmetic ones that are
cheap to resolve. The goal is not perfection -- it is measurable
reduction and honest documentation for the v4.130.0 panel.

## Phase 1 — Measure baseline diff

- [ ] Run fixed-point verification: `bash scripts/verify_fixed_point.sh --keep`
- [ ] Record diff between stage2.ll and stage3.ll: `diff stage2.ll stage3.ll | wc -l`
- [ ] Save baseline diff: `diff stage2.ll stage3.ll > /tmp/fixedpoint_baseline.diff`
- [ ] Record total divergent functions: `python scripts/ir_doctor.py diff-ir stage2.ll stage3.ll`
- [ ] Write initial metrics in `docs/roadmap/v4/v4.127.0/FIXEDPOINT_BASELINE.md`

## Phase 2 — Categorize divergences

- [ ] For each divergent function in the diff, classify:
  - **L** (label names) — different temp/block label numbering
  - **C** (constant order) — same constants, different emission order
  - **A** (attributes) — different function/parameter attributes
  - **S** (semantic) — genuinely different code generation
  - **W** (whitespace/formatting) — trivial formatting differences
- [ ] Count per category
- [ ] Identify the top 3 categories by frequency
- [ ] Update `FIXEDPOINT_BASELINE.md` with category breakdown

## Phase 3 — Fix cosmetic divergences

- [ ] **Label naming (L)**: if the self-hosted compiler uses a different label counter than the Python bootstrap, normalize the naming convention in `emit_llvm.mn`
- [ ] **Constant ordering (C)**: if constants are emitted in hash-map iteration order, sort them before emission
- [ ] **Attribute sets (A)**: align function attributes between the two pipelines (e.g., `nounwind`, `norecurse`)
- [ ] **Whitespace (W)**: normalize whitespace in IR emission
- [ ] After each category of fixes, rebuild and re-measure: `bash scripts/verify_fixed_point.sh --keep`

## Phase 4 — Re-measure and record delta

- [ ] Run fixed-point verification again: `bash scripts/verify_fixed_point.sh --keep`
- [ ] Record new diff size
- [ ] Compute delta: baseline diff lines - current diff lines
- [ ] If semantic divergences remain, document each one with root cause
- [ ] Update `FIXEDPOINT_BASELINE.md` with final metrics and delta
- [ ] Use `culebra diff stage2.ll stage3.ll` for structural comparison

## Phase 5 — LOW sweep + closeout

- [ ] `make test` — all green
- [ ] `make lint` — all clean
- [ ] Rebuild mnc-stage1: `bash scripts/rebuild.sh`
- [ ] Golden tests: no regressions from v4.126.0
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.127.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Fixed-point baseline diff measured (line count + function count) | `FIXEDPOINT_BASELINE.md` |
| 2 | All divergences categorized (L/C/A/S/W) | category breakdown in `FIXEDPOINT_BASELINE.md` |
| 3 | Top 3 divergence categories identified | `FIXEDPOINT_BASELINE.md` |
| 4 | Cosmetic fixes applied (at least one category reduced) | commit diffs |
| 5 | Post-fix diff measured, delta recorded | `FIXEDPOINT_BASELINE.md` before/after |
| 6 | No regressions in golden tests | test log |
| 7 | Standard closeout clean | CHANGELOG + SESSION_REPORT + VERSION bump |

---

## What this release does NOT do

- **Achieve perfect fixed-point.** That may require deep changes to label allocation, constant interning, or code generation order. This release reduces the diff; it does not eliminate it.
- **Fix semantic divergences.** If the two pipelines genuinely generate different code for the same input, that is documented and deferred to a future release.
- **Change the Python bootstrap.** All fixes are in the self-hosted compiler (`mapanare/self/*.mn`). The Python pipeline is the reference; the self-hosted compiler converges toward it.
- **Run a panel.** Next panel is v4.130.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Fixed-point verification script fails to complete (timeout, OOM) | low | high | Use `--keep` to save intermediate files; investigate failures before attempting the full 3-stage run |
| Most divergences are semantic, not cosmetic | medium | medium | Document them honestly. Even a complete categorization without fixes is valuable for v4.130.0. |
| Fixing label naming in emit_llvm.mn breaks golden tests | medium | medium | Re-run golden suite after every change; revert if regressions appear |
| Diff is already very small (< 50 lines) — not much to optimize | low | low | Document the success. A small diff is good news for the panel. |
| Fixing constant order requires changes to the MIR data structures | low | medium | If the fix is non-trivial, document it and defer. This is a buffer release. |

---

## After v4.127.0

v4.128.0 — documentation and SPEC sync. Close documentation gaps before the v4.130.0 panel. The fixed-point metrics from this release feed into MEASUREMENTS.md for the panel.
