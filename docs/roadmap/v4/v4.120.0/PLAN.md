# Mapanare v4.120.0 — Panel: v5 Gate (Attempt 2)

> **Phase F panel. THE FINAL PANEL of the v4.x extended line.** Seven
> reviewers grade the entire recovery arc (v4.100.0-v4.119.0). The
> v4.99.0 panel returned 6.59/10 with 3 NEEDS WORK. Twenty releases
> later, Phase A fixed 5 critical/high bugs, Phase B rebuilt and
> verified, Phase C benchmarked against 5 languages, Phase D completed
> 64/64 self-hosted with fixed-point, Phase E proved async I/O and
> hardened testing, Phase F measured everything and wrote the
> retrospective. This is the gate.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.119.0
**Delta review:** No
**Full panel:** Yes -- 7 reviewers
**Estimated work:** 1 sprint
**Theme:** 120 releases deep. The evidence is in. The panel decides.

---

## Scope

This is a panel release. The scope is:

1. Pre-panel sweep: full test suite, all sanitizers, all benchmarks, fixed-point, stage2
2. MEASUREMENTS.md: comprehensive snapshot of the project's current state
3. Panel execution: 7 reviewers grade v4.100.0-v4.119.0 holistically
4. v5 decision: mechanical rule applied to the aggregate score
5. If v5 is tagged: VERSION bump, README update, CHANGELOG entry
6. If v5 is not tagged: document what's still needed, plan v4.121.0+

The retrospective, statistics, v5 readiness assessment, FINAL_REPORT, and audit notes from v4.119.0 are the evidence base. The panel reads them and renders judgment.

## Phase 1 -- Pre-panel sweep

- [ ] Full test suite: `make test` (5,374+ tests, all must pass)
- [ ] ASan sweep: build with `-fsanitize=address`, run golden tests (64/64)
- [ ] TSan sweep: build with `-fsanitize=thread`, run async golden tests
- [ ] All benchmarks: verify `benchmarks/FINAL_REPORT_v4.120.md` is current (from v4.118.0)
- [ ] Fixed-point: `bash scripts/verify_fixed_point.sh` -- mnc-stage1 compiles itself, output matches
- [ ] Stage2: `python scripts/ir_doctor.py stage2` -- self-hosted modules compile through mnc-stage1
- [ ] Golden tests: 64/64 through both pipelines (Python bootstrap and mnc-stage1)
- [ ] CI: all jobs green on the current commit

## Phase 2 -- MEASUREMENTS.md

- [ ] Write `docs/roadmap/v4/v4.120.0/MEASUREMENTS.md`:
  - **Test count**: total pytest tests, golden tests, integration tests
  - **Golden count**: X/64 through mnc-stage1, X/64 through integration pipeline
  - **Self-hosted compiler**: lines of `.mn` code, module count, binary size
  - **Benchmark summary**: Mapanare's position on the C -> Rust -> Go -> Mapanare -> Python spectrum (reference FINAL_REPORT)
  - **Carry-forward state**: open items, closed items, net change since v4.99.0
  - **Docket closure**: all 11 items from v4.99.0 docket -- status of each
  - **CI gate status**: which checks are gating (pytest, ASan, TSan, WASM, native, android)
  - **ASan/TSan results**: clean or findings documented
  - **Fixed-point status**: achieved or not, with evidence
  - **Panel score history**: every panel score from v4.26.0 through v4.114.0

## Phase 3 -- Panel run

- [ ] Execute the 7-reviewer panel. Each reviewer grades v4.100.0-v4.119.0 holistically and answers their domain question:

  **Rattler** (LLVM IR correctness):
  - Is the LLVM IR correct, optimizable, and producing the right output at -O2?
  - Are there any IR pathologies remaining (ALLOCA_ALIAS, RET_TYPE_MISMATCH, etc.)?
  - Does the IR survive `opt -O2 -> llc -> clang -> run` for all 64 golden tests?

  **Viper** (Memory safety):
  - Is mnc-stage1 valgrind clean? ASan clean?
  - Are async tests TSan clean?
  - Are there any known memory leaks, use-after-free, or double-free issues?

  **Anaconda** (CI / Testing):
  - Is the CI pipeline complete? pytest, native, WASM, android, ASan, TSan?
  - Are integration tests fail-loud? Is the golden suite 100% consistent (0 flaky)?
  - Is test coverage measured and documented?

  **Cobra** (Bootstrap / Self-hosted):
  - Has fixed-point been achieved? Does mnc-stage1 compile itself?
  - Is the ABI stable between Python bootstrap and self-hosted compiler?
  - 64/64 golden through both pipelines?

  **Coral** (Language design):
  - Is the language feature-complete for v5? All features work end-to-end?
  - Is the SPEC current (synced in v4.116.0)?
  - Are there any language-level gaps that would embarrass a v5 label?

  **Boa** (Documentation):
  - Is documentation sufficient for external adoption?
  - Does the getting started guide work end-to-end?
  - Are all code examples in docs verified?

  **Mamba** (C runtime / Performance):
  - Is the C runtime production-quality? String performance fixed?
  - Is the cooperative scheduler stable for async workloads?
  - Where does Mapanare sit on the performance spectrum vs C/Rust/Go/Python?

- [ ] Each reviewer provides: score (1-10), grade (MEETS/NEEDS WORK/EXCEEDS), specific findings, carry-forward items (if any)
- [ ] Compute aggregate score: mean of 7 scores

## Phase 4 -- v5 decision

- [ ] Apply the mechanical rule:

  **Option A (tag v5.0.0):**
  - Aggregate >= 9.0 AND 0 NEEDS WORK grades
  - All 11 v4.99.0 docket items resolved
  - 64/64 golden both pipelines
  - Fixed-point achieved
  - ASan + TSan clean

  **Option B (continue v4.121.0+):**
  - Aggregate < 9.0 OR any NEEDS WORK grade
  - Document what's still needed
  - Plan v4.121.0+ to address gaps

  **Option C (both):**
  - Aggregate >= 8.5 but < 9.0 AND 0 NEEDS WORK
  - Tag v5.0.0-rc1 (release candidate, not final)
  - Plan v5.0.0 final after remaining items close

- [ ] Write `docs/roadmap/v4/v4.120.0/V5_DECISION.md` with the decision, rationale, and evidence

## Phase 5 -- If Option A or C: tag v5.0.0 (or v5.0.0-rc1)

- [ ] Update `VERSION` to `5.0.0` (or `5.0.0-rc1`)
- [ ] Update `README.md` with v5 announcement
- [ ] Write `CHANGELOG.md [5.0.0]` entry summarizing the entire v4.x arc
- [ ] Create git tag `v5.0.0` (or `v5.0.0-rc1`)
- [ ] Update `CLAUDE.md` current version section
- [ ] Update `docs/roadmap/ROADMAP.md` with v5 entry

## Phase 6 -- If Option B: plan v4.121.0+

- [ ] Document what the panel identified as remaining gaps
- [ ] Create `docs/roadmap/v4/v4.121.0/` directory
- [ ] Write preliminary PLAN.md for v4.121.0 addressing the highest-priority gap
- [ ] Update `docs/roadmap/ROADMAP.md` with the continued v4.x plan

## Phase 7 -- Closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit (to 5.0.0, 5.0.0-rc1, or 4.121.0 depending on decision)
- [ ] `CHANGELOG.md [4.120.0]` entry
- [ ] `SESSION_REPORT.md` written -- the most important SESSION_REPORT of the v4.x line
- [ ] All panel documents committed

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Pre-panel sweep complete: all tests pass, sanitizers clean | test logs, ASan/TSan output |
| 2 | MEASUREMENTS.md published | file exists in v4.120.0 directory |
| 3 | Panel executed: 7 reviewers, 7 scores, 7 grades | panel output |
| 4 | Aggregate score recorded | V5_DECISION.md |
| 5 | v5 decision documented with rationale | V5_DECISION.md |
| 6 | Retrospective linked (from v4.119.0) | reference in panel docs |
| 7 | Benchmarks verified (from v4.118.0) | reference to FINAL_REPORT |
| 8 | All 11 v4.99.0 docket items resolved or explicitly deferred | docket status table |
| 9 | Golden: 64/64 through both pipelines | test logs |
| 10 | ASan + TSan clean | sanitizer output |
| 11 | CI gates live (pytest, ASan, TSan, WASM, native) | CI configuration |
| 12 | ROADMAP.md updated | diff |
| 13 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change the compiler or runtime** -- this is a panel + decision release. No code changes except VERSION and documentation.
- **Override the mechanical rule** -- if the aggregate is below 9.0, v5 does not ship. No exceptions, no pleading.
- **Extend the panel indefinitely** -- 7 reviewers, 7 scores. One decision. Done.
- **Retroactively edit history** -- SESSION_REPORTs, audit notes, and the retrospective are final. The panel sees everything as-is.
- **Promise v5 features** -- the v5 decision is about the current state, not future plans.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel returns < 9.0 again | medium | high | The recovery arc addressed every docket item. If the score is still low, the gaps are real and v4.121.0+ continues. |
| One reviewer gives NEEDS WORK on a domain that improved but isn't perfect | medium | medium | Option C (>= 8.5 with 0 NEEDS WORK) provides a middle path via release candidate. |
| Pre-panel sweep reveals a regression not caught during Phases A-E | low | high | Fix the regression before running the panel. Do not run the panel on broken code. |
| Retrospective or audit notes reveal embarrassing discrepancies | low | medium | Discrepancies are documented, not hidden. The panel respects honesty. |
| The v5 decision is ambiguous (exactly 9.0, or edge cases in the rule) | low | low | The rule is mechanical. >= 9.0 and 0 NEEDS WORK = v5. No interpretation needed. |

---

## After v4.120.0

Whatever the panel decides, the cadence carries forward. 120 releases deep, the system works.

If **v5.0.0**: the v5 era begins. New roadmap, new arcs, new panel cadence. The v4.x line is closed with honor.

If **v4.121.0+**: the recovery continues. The gaps the panel identified become the next phase. The cadence is the cadence.

Either way: the retrospective is written, the numbers are published, the evidence is committed. The work speaks for itself.
