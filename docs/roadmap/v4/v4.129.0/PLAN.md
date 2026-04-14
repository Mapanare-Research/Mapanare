# Mapanare v4.129.0 — Pre-Panel Prep + Third Flaky Audit

> **Buffer release 4.** Final verification before the v4.130.0 panel.
> Third flaky audit (5x clean), valgrind + ASan on golden tests,
> pre-panel audit that fact-checks every claim from v4.120.0-v4.128.0
> SESSION_REPORTs, and MEASUREMENTS.md preparation for the panel.
> This release produces evidence, not code.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.128.0
**Delta review:** No
**Full panel:** No (this release prepares for v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Verify everything. Document everything. Fix nothing new.

---

## Scope

The v4.130.0 panel is the next v5 gate attempt. The panel reads
MEASUREMENTS.md, PRE_PANEL_AUDIT.md, and the SESSION_REPORTs from
the entire closeout arc (v4.121.0-v4.129.0). This release produces
those evidence artifacts.

The flaky audit (third since v4.117.0) must show 0 failures across
5 consecutive `make test` runs. The sanitizer runs (valgrind + ASan)
must show clean-or-documented results on all golden tests through
mnc-stage1. The pre-panel audit must fact-check every claim made in
the v4.120.0-v4.128.0 SESSION_REPORTs -- if a SESSION_REPORT says
"42/64 golden pass," the audit verifies that number.

## Phase 1 — Third flaky audit

- [ ] Run `make test` 5 times consecutively:
  ```bash
  for i in 1 2 3 4 5; do make test 2>&1 | tee /tmp/flaky_run_$i.log; done
  ```
- [ ] Compare results across all 5 runs: same test count, same pass/fail set
- [ ] Record in `docs/roadmap/v4/v4.129.0/FLAKY_AUDIT_3.md`:
  - Total tests per run
  - Any failures (with test name, run number, and classification: flaky vs deterministic)
  - Verdict: CLEAN (0 flaky) or FINDING (N flaky tests identified)
- [ ] If any flaky tests found: investigate and fix (this is the one exception to "fix nothing new")

## Phase 2 — Valgrind on golden tests

- [ ] Build mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run valgrind on each golden test through mnc-stage1:
  ```bash
  for f in tests/golden/*.mn; do
    python scripts/ir_doctor.py valgrind "$f" 2>&1 | tee /tmp/valgrind_$(basename "$f").log
  done
  ```
- [ ] Classify each result: CLEAN / WARNING / ERROR
- [ ] Record in `docs/roadmap/v4/v4.129.0/VALGRIND_REPORT.md`:
  - Per-test status table (test name, status, finding summary if not clean)
  - Overall verdict: N/64 clean, M warnings, P errors

## Phase 3 — ASan on golden tests

- [ ] Rebuild mnc-stage1 with AddressSanitizer:
  ```bash
  # Build with -fsanitize=address
  python scripts/build_stage1.py  # then relink with ASan flags
  ```
- [ ] Run ASan-instrumented golden tests
- [ ] Classify each result: CLEAN / FINDING
- [ ] Record in `docs/roadmap/v4/v4.129.0/ASAN_REPORT.md`:
  - Per-test status table
  - Overall verdict

## Phase 4 — Pre-panel audit

- [ ] Read every SESSION_REPORT.md from v4.120.0 through v4.128.0
- [ ] For each factual claim (test count, golden count, benchmark number, fix description), verify:
  - Is the claim still true on the current codebase?
  - Was the claim accurate when it was made?
  - Has any subsequent release invalidated the claim?
- [ ] Write `.reviews/v4.130.0/PRE_PANEL_AUDIT.md`:
  - Per-release table: release, key claims, verified (Y/N), notes
  - Overall integrity verdict
  - Any discrepancies found (with explanation)

## Phase 5 — Prepare MEASUREMENTS.md for v4.130.0

- [ ] Write `docs/roadmap/v4/v4.130.0/MEASUREMENTS.md` (draft, to be finalized in v4.130.0):
  - **Golden count**: N/64 through mnc-stage1 (from v4.126.0), N/64 through Python bootstrap
  - **Test count**: total pytest tests collected
  - **Benchmark summary**: Mapanare's position on the C -> Rust -> Go -> Mapanare -> Python spectrum
  - **Fixed-point status**: baseline diff from v4.127.0, current diff
  - **Flaky audit result**: 0/5 or N/5 (from Phase 1)
  - **Valgrind result**: N/64 clean (from Phase 2)
  - **ASan result**: N/64 clean (from Phase 3)
  - **Dead-code metrics**: lines removed in v4.123.0
  - **Carry-forward state**: open items, closed items since v4.120.0
  - **Panel score history**: every panel score from v4.26.0 through v4.120.0

## Phase 6 — LOW sweep + closeout

- [ ] `make test` — all green (verified 5x in Phase 1)
- [ ] `make lint` — all clean
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.129.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 5x flaky audit: 0 failures across 5 runs | `FLAKY_AUDIT_3.md` |
| 2 | Valgrind report: per-test status for all golden tests | `VALGRIND_REPORT.md` |
| 3 | ASan report: per-test status for all golden tests | `ASAN_REPORT.md` |
| 4 | Pre-panel audit: every v4.120.0-v4.128.0 claim fact-checked | `PRE_PANEL_AUDIT.md` |
| 5 | MEASUREMENTS.md draft prepared for v4.130.0 | file exists |
| 6 | Panel score history recorded | in MEASUREMENTS.md |
| 7 | No new bugs introduced (document only) | no compiler/runtime diffs |
| 8 | `make test` green | CI logs |
| 9 | Standard closeout clean | CHANGELOG + SESSION_REPORT + VERSION bump |

---

## What this release does NOT do

- **Fix new bugs.** This release produces evidence documents. The only exception: flaky tests found in Phase 1 get fixed because a flaky test suite undermines the entire panel.
- **Change compiler or runtime code.** All output is documentation and verification artifacts.
- **Run the panel.** That is v4.130.0.
- **Finalize MEASUREMENTS.md.** The draft is prepared here; v4.130.0 finalizes it with fresh numbers from the pre-panel sweep.
- **Promise a v5 outcome.** The numbers are the numbers. The panel decides.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Flaky tests found in 5x audit | low | high | Fix them -- this is the exception to "fix nothing new." A flaky suite is a panel finding. |
| Valgrind finds real memory errors in golden tests | medium | medium | Document them in the report. These become carry-forward items for the panel. |
| ASan build fails (toolchain issue) | low | medium | Fall back to valgrind-only. Document the ASan build failure. |
| Pre-panel audit finds a factual discrepancy in a SESSION_REPORT | low | medium | Document the discrepancy honestly. The panel respects corrections more than cover-ups. |
| MEASUREMENTS.md preparation reveals metrics worse than expected | medium | low | Report the real numbers. The panel grades honesty, not optimism. |

---

## After v4.129.0

v4.130.0 — THE PANEL. v5 gate attempt (target >= 9.0). Seven reviewers. The evidence from v4.121.0-v4.129.0 is the input. The mechanical rule is the decision framework. Whatever the panel decides, the cadence holds.
