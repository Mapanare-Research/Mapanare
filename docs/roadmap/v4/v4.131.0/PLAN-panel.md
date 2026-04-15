# Mapanare v4.131.0 — Panel: v5 Gate Attempt (Target >= 9.0)

> **THE PANEL.** Seven reviewers grade v4.121.0-v4.130.0 holistically.
> The v4.120.0 panel returned 8.21/10 with one NEEDS WORK (Anaconda
> 7.6). The closeout arc addressed Anaconda's concerns (test hygiene
> sweep, three flaky audits, full sanitizer coverage) plus GitNexus
> codebase audit, golden test push, fixed-point refinement,
> documentation sync, and pre-panel verification. This is the v5 gate.
> The mechanical rule applies. 131 releases deep.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.130.0
**Delta review:** No
**Full panel:** **YES** -- 7 reviewers (Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba)
**Estimated work:** 1 sprint
**Theme:** 131 releases deep. The evidence is in. The panel decides.

---

## Scope

This is a panel release. The scope is:

1. Pre-panel sweep: full test suite, all sanitizers, all benchmarks, fixed-point, stage2
2. MEASUREMENTS.md: finalize the comprehensive snapshot (draft from v4.130.0)
3. Panel execution: 7 reviewers grade v4.121.0-v4.130.0 holistically
4. v5 decision: mechanical rule applied to the aggregate score
5. If v5 is tagged: VERSION bump, README update, CHANGELOG entry
6. If v5 is not tagged: document what's still needed, plan v4.132.0+

The v4.130.0 pre-panel audit, valgrind report, ASan report, flaky
audit, and MEASUREMENTS.md draft are the evidence base. The panel
reads them and renders judgment.

## Phase 1 — Pre-panel sweep

- [ ] Full test suite: `make test` (all must pass)
- [ ] Valgrind sweep: reference v4.130.0 `VALGRIND_REPORT.md` (refresh if any changes since v4.130.0)
- [ ] ASan sweep: reference v4.130.0 `ASAN_REPORT.md` (refresh if any changes)
- [ ] Benchmarks: verify cross-language benchmark data is current (from v4.125.0)
- [ ] Fixed-point: `bash scripts/verify_fixed_point.sh` -- reference v4.128.0 `FIXEDPOINT_BASELINE.md`
- [ ] Stage2: `python scripts/ir_doctor.py stage2` -- self-hosted modules compile through mnc-stage1
- [ ] Golden tests: through both pipelines (Python bootstrap and mnc-stage1)
- [ ] CI: all jobs green on the current commit

## Phase 2 — Finalize MEASUREMENTS.md

- [ ] Finalize `docs/roadmap/v4/v4.131.0/MEASUREMENTS.md` (from v4.130.0 draft):
  - **Test count**: total pytest tests, golden tests
  - **Golden count**: N/64 through mnc-stage1, N/64 through Python bootstrap
  - **Self-hosted compiler**: lines of `.mn` code, module count, binary size
  - **Benchmark summary**: Mapanare position on C -> Rust -> Go -> Mapanare -> Python spectrum
  - **Fixed-point status**: diff size, divergence categories, delta since v4.128.0
  - **Flaky audit**: result from v4.130.0 third audit (0/5 or N findings)
  - **Sanitizer results**: valgrind clean count, ASan clean count
  - **Dead-code metrics**: lines removed in v4.123.0
  - **GitNexus audit summary**: key findings from v4.127.0 (severity breakdown, dead code, ABI, community)
  - **Carry-forward state**: open items, closed since v4.120.0
  - **Panel score history**: every panel score (v4.26.0, v4.36.0, v4.46.0, v4.56.0, v4.66.0, v4.76.0, v4.99.0, v4.106.0, v4.114.0, v4.120.0 -> now v4.131.0)

## Phase 3 — Panel run

- [ ] Execute the 7-reviewer panel. Each reviewer grades v4.121.0-v4.130.0 holistically:

  **Rattler** (LLVM IR correctness):
  - Is the IR correct at -O2? Does it survive `opt -O2 -> llc -> clang -> run`?
  - Enum unboxing (v4.124.0) -- is the IR representation sound?
  - Fixed-point (v4.128.0) -- is the diff improving? Are remaining divergences cosmetic?

  **Viper** (Memory safety):
  - Sanitizers clean? Valgrind report (v4.130.0) and ASan report (v4.130.0)?
  - No new memory safety issues introduced in v4.121.0-v4.130.0?
  - List indexing fix (v4.122.0) -- correct and safe?

  **Anaconda** (CI / Testing):
  - `make test` green? (The v4.120.0 NEEDS WORK item)
  - Three flaky audits (v4.117.0, v4.125.0, v4.130.0) -- consistent 0 flaky?
  - CI gates complete? Integration pipeline solid?

  **Cobra** (Bootstrap / Self-hosted):
  - Fixed-point measured and documented (v4.128.0)?
  - ABI stable? Enum unboxing ABI compatible (v4.124.0)?
  - Golden count through mnc-stage1 (from v4.126.0 push)?

  **Coral** (Language design):
  - Language complete for v5? Qs.1 resolved (v4.122.0)?
  - SPEC current (v4.129.0 sync)?
  - Any language-level gaps that would embarrass a v5 label?

  **Boa** (Documentation / DX):
  - Documentation current (v4.129.0 sync)?
  - Getting-started guide works end-to-end?
  - Error messages useful?

  **Mamba** (C runtime / Performance):
  - Dead code removed (v4.123.0)?
  - Benchmark numbers honest (v4.125.0 refresh)?
  - Runtime clean under sanitizers?

- [ ] Each reviewer provides: score (1-10), grade (MEETS/NEEDS WORK/EXCEEDS), specific findings, carry-forward items (if any)
- [ ] Compute aggregate score: mean of 7 scores

## Phase 4 — v5 decision

- [ ] Apply the mechanical rule:

  **Option A (tag v5.0.0):**
  - Aggregate >= 9.0 AND 0 NEEDS WORK grades
  - All carry-forward items from v4.120.0 addressed
  - Golden tests passing through both pipelines
  - Sanitizers clean or documented
  - Fixed-point measured and stable

  **Option B (continue v4.132.0+):**
  - Aggregate < 9.0 OR any NEEDS WORK grade
  - Document what's still needed
  - Plan v4.132.0+ to address gaps

  **Option C (both):**
  - Aggregate >= 8.5 but < 9.0 AND 0 NEEDS WORK
  - Tag v5.0.0-rc1 (release candidate, not final)
  - Plan v5.0.0 final after remaining items close

- [ ] Write `.reviews/v4.131.0/V5_DECISION.md` with the decision, rationale, and evidence

## Phase 5 — If Option A or C: tag v5.0.0 (or v5.0.0-rc1)

- [ ] Update `VERSION` to `5.0.0` (or `5.0.0-rc1`)
- [ ] Update `README.md` with v5 announcement
- [ ] Write `CHANGELOG.md [5.0.0]` entry summarizing the entire v4.x arc
- [ ] Create git tag `v5.0.0` (or `v5.0.0-rc1`)
- [ ] Update `CLAUDE.md` current version section
- [ ] Update `docs/roadmap/ROADMAP.md` with v5 entry

## Phase 6 — If Option B: plan v4.132.0+

- [ ] Document what the panel identified as remaining gaps
- [ ] Create `docs/roadmap/v4/v4.132.0/` directory
- [ ] Write preliminary PLAN.md for v4.132.0 addressing the highest-priority gap
- [ ] Update `docs/roadmap/ROADMAP.md` with the continued v4.x plan

## Phase 7 — Closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit (to 5.0.0, 5.0.0-rc1, or 4.132.0 depending on decision)
- [ ] `CHANGELOG.md [4.131.0]` entry
- [ ] `SESSION_REPORT.md` written
- [ ] All panel documents committed
- [ ] `.reviews/v4.131.0/README.md` with verdict table

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Pre-panel sweep complete: all tests pass | test logs |
| 2 | MEASUREMENTS.md finalized | file exists in v4.131.0 directory |
| 3 | Panel executed: 7 reviewers, 7 scores, 7 grades | panel output |
| 4 | Aggregate score recorded | V5_DECISION.md |
| 5 | v5 decision documented with rationale | V5_DECISION.md |
| 6 | All v4.120.0 carry-forward items addressed or explicitly deferred | carry-forward audit |
| 7 | Benchmarks verified (from v4.125.0) | reference to benchmark data |
| 8 | Golden count documented (both pipelines) | MEASUREMENTS.md |
| 9 | Fixed-point status documented | MEASUREMENTS.md |
| 10 | Sanitizer results documented (valgrind + ASan) | MEASUREMENTS.md |
| 11 | `make test` green | CI logs |
| 12 | ROADMAP.md updated | diff |
| 13 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change the compiler or runtime.** This is a panel + decision release. No code changes except VERSION and documentation.
- **Override the mechanical rule.** If the aggregate is below 9.0, v5 does not ship. No exceptions, no pleading.
- **Extend the panel indefinitely.** 7 reviewers, 7 scores. One decision. Done.
- **Retroactively edit history.** SESSION_REPORTs, audit notes, and evidence documents are final. The panel sees everything as-is.
- **Implement v5 features.** The v5 decision is about the current state, not future plans.
- **Guarantee a particular outcome.** The numbers are the numbers. The process is the process.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel returns < 9.0 again | medium | high | The closeout arc (11 releases, including GitNexus audit) directly addressed every v4.120.0 finding. If the score is still low, the gaps are real and v4.132.0+ continues. |
| One reviewer gives NEEDS WORK on a domain that improved but isn't perfect | medium | medium | Option C (>= 8.5 with 0 NEEDS WORK) provides a middle path via release candidate. |
| Pre-panel sweep reveals a regression from v4.121.0-v4.130.0 changes | low | high | Fix the regression before running the panel. Do not run the panel on broken code. |
| v4.130.0 pre-panel audit found discrepancies that weaken the evidence | low | medium | Discrepancies are documented, not hidden. The panel respects honesty over optimism. |
| The v5 decision is ambiguous (exactly 9.0, or edge cases in the rule) | low | low | The rule is mechanical. >= 9.0 and 0 NEEDS WORK = v5. No interpretation needed. |
| Anaconda still gives NEEDS WORK despite three flaky audits and full test hygiene | low | medium | The evidence is comprehensive. If Anaconda is still unsatisfied, the findings define v4.132.0 scope. |

---

## After v4.131.0

The cadence works. Whatever the panel decides, we keep shipping.

If **v5.0.0**: the v5 era begins. New roadmap, new arcs, new panel cadence. The v4.x line closes at 131 releases -- the longest, most disciplined arc in the project's history.

If **v5.0.0-rc1**: one more release (v4.132.0 or v5.0.0) to close the remaining items. The release candidate signals confidence.

If **v4.132.0+**: the recovery continues. The gaps the panel identified become the next phase. The cadence is the cadence. Every release has a PLAN.md, a PROMPT.md, a SESSION_REPORT.md. Every claim is verifiable. The process that built 131 releases can build 132.
