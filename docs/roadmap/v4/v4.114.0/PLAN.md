# Mapanare v4.114.0 — Panel: Self-Hosted Works, Medium Items Closed

> **Phase D panel.** Seven reviewers grade v4.111.0-v4.113.0: self-hosted
> golden parity, fixed-point convergence, coroutine frame decoupling,
> docket closure. Phase D is the self-hosted compiler maturity arc.
> After Phase A fixed critical bugs, Phase B verified, Phase C
> benchmarked, Phase D closes the remaining docket items and proves the
> self-hosted compiler works end-to-end.

**Status:** DONE (panel returned NEEDS WORK @ 8.21 < 8.5 — v4.114.1 patch scheduled)
**Breaking:** No
**Prerequisite:** v4.113.0
**Delta review:** No
**Full panel:** **YES** — Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba
**Estimated work:** 1 sprint + external panel
**Theme:** Self-hosted compiler works. Fixed-point holds. Medium items closed. The v4.99.0 docket is empty.

---

## Phase D scope the panel grades

- **v4.111.0**: Self-hosted golden — rebuilt mnc-stage1 from self-hosted pipeline, ran all 64 golden tests, fixed critical failures, ran stage2 validation
- **v4.112.0**: Fixed-point verification — 3-stage self-compilation, byref size heuristic fix (docket #7), convergence measurement
- **v4.113.0**: Coroutine frame decoupling (docket #8), SPEC reserved-keywords section (docket #10), improved async error messages (docket #11)

Panel-specific questions:
- Does the self-hosted mnc-stage1 produce correct IR for all 64 golden tests? Are the failure modes (if any) understood and documented?
- Is the fixed-point real? Does stage2 == stage3? If not, are the remaining divergences cosmetic or semantic?
- Is the byref size heuristic actually fixed? Does the self-hosted emitter compute real struct sizes?
- Is the coroutine frame stable? No hardcoded byte offsets anywhere in the codebase?
- Does the SPEC keyword section match the actual lexer (both pipelines)?
- Are the async error messages genuinely improved? Can a user understand what went wrong?
- **Is the v4.99.0 docket fully addressed?** Walk every item. Any item claimed CLOSED that is not actually closed is a panel finding.

---

## Phase 1 — Pre-panel sweep

- [ ] Run full test suite: `make test`
- [ ] Run golden tests through BOTH pipelines:
  - Python-bootstrapped: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v` (after `python scripts/build_stage1.py`)
  - Self-hosted: `bash scripts/rebuild.sh full` then `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record pass rate for both: target 64/64 for both pipelines
- [ ] Run stage2 validation: `python scripts/ir_doctor.py stage2`
- [ ] Run fixed-point: `bash scripts/verify_fixed_point.sh`
- [ ] Valgrind on struct-return, async, and coroutine golden tests
- [ ] AddressSanitizer: rebuild with `-fsanitize=address`, run golden subset

## Phase 2 — MEASUREMENTS.md

- [ ] Write `docs/roadmap/v4/v4.114.0/MEASUREMENTS.md`:
  - Golden pass rate: Python-bootstrapped pipeline (N/64)
  - Golden pass rate: self-hosted pipeline (N/64)
  - Fixed-point status: CONVERGED / DIVERGENT (with divergence count)
  - Fixed-point delta: divergent functions before vs after byref fix
  - Docket closure: items #1-#12 status (CLOSED / ACCEPTED / OPEN)
  - Test count: current pytest collected vs v4.99.0 baseline (5,374)
  - Self-hosted .mn line count (vs 38,824 at v4.99.0)
  - Sanitizer results: valgrind errors, ASan findings

## Phase 3 — Update docket

- [ ] Walk every item from the v4.99.0 docket (11 items):
  - #1 (CRITICAL, tagged-pointer UB) — CLOSED by v4.100.0
  - #2 (CRITICAL, list indexing) — CLOSED by v4.101.0
  - #3 (HIGH, async linking) — CLOSED by v4.102.0
  - #4 (HIGH, else/sino) — CLOSED by v4.103.0
  - #5 (HIGH, closure types) — CLOSED by v4.103.0
  - #6 (MEDIUM, README disclosure) — CLOSED by Phase C
  - #7 (MEDIUM, byref size heuristic) — verify CLOSED by v4.112.0
  - #8 (MEDIUM, coroutine frame coupling) — verify CLOSED by v4.113.0
  - #9 (MEDIUM, string concat perf) — verify addressed by Phase C investigation
  - #10 (LOW, keyword collision SPEC) — verify CLOSED by v4.113.0
  - #11 (LOW, async error messages) — verify CLOSED by v4.113.0
- [ ] For each item marked CLOSED: verify the fix is still present (code change, test exists)
- [ ] Update `.reviews/v4.99.0/` docket document with closure evidence

## Phase 4 — Pre-panel audit

- [ ] Fact-check every v4.111.0-v4.113.0 SESSION_REPORT claim
- [ ] Verify all exit criteria from each release are still true
- [ ] Write `.reviews/v4.114.0/PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.114.0. Arc: Phase D (Self-Hosted + Testing).
- [ ] `mkdir -p .reviews/v4.114.0/` + pre-populate
- [ ] Spawn 7 reviewers with focus assignments:
  - **Rattler (LLVM)** — PRIMARY for self-hosted IR quality. Does mnc-stage1 produce correct IR? Fixed-point convergence? Are the emitted types, instructions, and calling conventions correct?
  - **Viper (memory safety)** — PRIMARY for coroutine frame fix. No hardcoded offsets? No fragility? Valgrind clean on async tests?
  - **Anaconda (toolchain)** — Golden pass rate both pipelines? CI coverage? Is the golden test harness reliable?
  - **Cobra (C++/ABI)** — PRIMARY for byref size heuristic. Real struct sizes computed? Fixed-point delta? ABI correctness of the self-hosted binary?
  - **Coral (language design)** — Language completeness: do all features work end-to-end in both pipelines? SPEC keyword section quality?
  - **Boa (Python/DX)** — Error messages improved? Documentation gaps (SPEC keywords) closed? Developer experience of the self-hosted workflow?
  - **Mamba (C runtime)** — Coroutine frame changes clean? No leaks? Runtime changes tested under sanitizers?
- [ ] Panel reads `MEASUREMENTS.md` and docket closure evidence as primary artifacts

## Phase 6 — Closeout

- [ ] `.reviews/v4.114.0/README.md` written with verdict table
- [ ] If PASS: Phase D closes. Proceed to Phase E (polish).
- [ ] If NEEDS WORK: address findings in v4.114.1 patch before moving to Phase E.
- [ ] Standard release closeout
- [ ] `SESSION_REPORT.md` with Phase D retrospective

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full test suite passes | `make test` output |
| 2 | Golden 64/64 through Python-bootstrapped pipeline | test log |
| 3 | Golden pass count through self-hosted pipeline recorded | test log |
| 4 | Fixed-point verification result recorded | script output |
| 5 | Valgrind clean on async + coroutine golden tests | valgrind output |
| 6 | ASan clean on golden subset | ASan output |
| 7 | `MEASUREMENTS.md` written with all metrics | file |
| 8 | Docket items #1-#11 verified (each CLOSED with evidence or ACCEPTED) | docket audit |
| 9 | `PRE_PANEL_AUDIT.md` written | file |
| 10 | Panel prompt retargeted + 7 reviewer files | `.reviews/v4.114.0/` |
| 11 | Panel aggregate recorded in `.reviews/v4.114.0/README.md` | file |

---

## What this release does NOT do

- **New features** — panel release, zero new code.
- **Fix self-hosted emitter gaps** — any remaining gaps are documented in v4.111.0's GOLDEN_FAILURES.md and carried forward.
- **Achieve perfect fixed-point** — cosmetic divergences (temp names, block ordering) are acceptable. Only semantic divergences are findings.
- **Start Phase E** — Phase E begins at v4.115.0 if the panel says PASS.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel finds docket item #7 (byref) is not actually fixed | low | high | Phase 2 measurements include before/after culebra diff evidence. If the fix is incomplete, it becomes a Phase E item. |
| Panel finds coroutine frame still has hardcoded offsets | low | high | Phase 1 grep audit catches any remaining offsets. If missed, immediate hotfix. |
| Self-hosted golden count is below 64 | medium | medium | The panel grades whether failures are understood and documented, not whether the count is perfect. |
| Fixed-point still diverges after byref fix | medium | medium | Remaining divergences are classified as cosmetic or semantic. Cosmetic is acceptable. Semantic becomes Phase E work. |
| Panel score < 8.5 | low | medium | Pre-panel sweep and audit reduce surprises. Phase D made concrete, measurable fixes. |
| A reviewer flags a new issue not on the v4.99.0 docket | medium | low | New findings go to the next docket. The panel grades Phase D's work, not the entire project. |

---

## If the panel says PASS

Phase D closes. The self-hosted compiler is verified working. The v4.99.0
docket is fully addressed. Proceed to Phase E (polish) at v4.115.0.

Phase E theme candidates:
- **Optimizer improvements** — raise MIR optimization quality, reduce emitted IR size
- **CI hardening** — sanitizer jobs in CI, flakiness elimination
- **v5.0.0 prep** — final polish before tagging a major release
- **Performance** — string concat optimization, compilation speed

## If the panel says NEEDS WORK

v4.114.1 opens as a patch release addressing the panel's findings. Phase D
does not close until all findings are addressed. The next scheduled panel
shifts accordingly.

---

## After v4.114.0

If PASS, Phase E begins at v4.115.0. If NEEDS WORK, v4.114.1 addresses
findings. Either way, the project is within striking distance of v5.0.0 —
every critical and high bug is fixed, the self-hosted compiler works, and
the docket is clean.
