# Mapanare v4.99.0 — Final Panel + v5 Gate Decision

> **Arc 14 release 3. The final release in the v4.x extended plan.**
> Seven reviewers grade Arcs 10-14 holistically (v4.77.0-v4.98.0:
> integration tests, carry-forward debt zero, LLVM optimizer, MIR
> passes, real async, multi-threaded scheduler, string pathology fix,
> self-hosted optimizer propagation, final benchmarks). The panel's
> aggregate score determines the v5 decision. This is where the v4.x
> journey either graduates to v5.0.0 or continues.

**Status:** DONE (2026-04-13)
**Session log:** `docs/roadmap/v4/v4.99.0/SESSION_REPORT.md`
**Decisions taken:** Holistic grading with arc-level commentary; Option B (6.59/10, 3 NEEDS WORK); VERSION → 4.100.0
**Breaking:** No
**Prerequisite:** v4.98.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Grade everything. Decide v5. The cadence carries forward regardless.

---

## Scope

v4.99.0 is not a feature release. It is a reckoning: 22 releases of
post-plan work (v4.77.0-v4.98.0) across 5 arcs, graded by the same
7-reviewer panel that has judged every major milestone since the recovery
arc.

The panel grades:
- **Arc 10** (v4.77.0-v4.81.0): Integration test harness + carry-forward debt zero
- **Arc 11** (v4.82.0-v4.86.0): Baseline benchmarks + LLVM IR quality improvements
- **Arc 12** (v4.87.0-v4.91.0): MIR optimizer passes (inlining, LICM, escape analysis)
- **Arc 13** (v4.92.0-v4.96.0): Real async suspension + multi-threaded scheduler
- **Arc 14** (v4.97.0-v4.99.0): Self-hosted propagation + final benchmarks + this panel

After the panel, the lead makes the v5 decision:

- **Option A (tag v5.0.0):** The v4.x line ends. v4.99.0 is the last release. Next work opens as v5.1.0. **Default if aggregate >= 9.0 and 0 NEEDS WORK.**
- **Option B (continue v4.100.0+):** More arcs before v5. The panel found gaps that need closing. **Default if aggregate < 9.0.**
- **Option C (both):** Tag v5.0.0 as a milestone marker, open v4.100.0 (or v5.1.0) for continued development. **Default if aggregate >= 8.5 but < 9.0.**

---

## What the panel grades

This is the largest scope any panel has graded: 5 arcs, 22 releases. Each
reviewer has specific questions:

**Rattler (LLVM):** Is the IR now LLVM-optimizable? Do nsw/nuw, TBAA,
inbounds, and function attributes survive `opt -O2` correctly? Are the
MIR inlining, LICM, and escape analysis passes correct? Does the
benchmark data prove the optimization thesis from Arc 11?

**Viper (memory safety):** Is memory safety preserved across all new
features? The multi-threaded scheduler, StringBuilder, coroutine
suspension/resume -- do any of these introduce UAF, double-free, or
data races? Is valgrind clean on the full golden suite?

**Anaconda (toolchain):** Does the integration test pipeline from Arc 10
give confidence? Is CI coverage sufficient? Do the 57+ golden tests,
integration tests, and benchmark suite form a credible quality gate?

**Cobra (C++/ABI):** Is the ABI stable across the self-hosted and Python
bootstrap compilers? Does the fixed-point hold after optimizer
propagation? Are struct layouts, calling conventions, and sret handling
consistent?

**Coral (language design):** Is the language design complete for v5.0.0?
Are there any grammar or semantic gaps that would embarrass a 5.0 label?
Is the async/await surface production-quality?

**Boa (developer experience):** Is the documentation sufficient for
external adoption? Can a developer who has never seen Mapanare pick up
the language from the docs, spec, and cookbook? Are error messages clear?

**Mamba (C runtime):** Is the C runtime production-quality? Arena
allocator, SPSC ring buffers, thread pool, agent scheduler, string
interning -- are these robust under stress? Are there known failure
modes under extreme load?

---

## Phase 1 -- Pre-panel sweep

- [ ] Full test suite: `make test` (all ~4,900+ tests pass)
- [ ] Integration tests: `pytest tests/integration/ -v` (all golden tests through full pipeline)
- [ ] Golden tests: 57/57 through mnc-stage1 + llvm-as
- [ ] Stage2 validation: `python scripts/ir_doctor.py stage2`
- [ ] All benchmarks reproducible: `python benchmarks/run_final.py` completes with correct checksums
- [ ] Valgrind clean on full golden suite: `bash scripts/valgrind_all_goldens.sh`
- [ ] TSan clean on async golden tests: no data races
- [ ] Fixed-point holds: stage1-from-Python == stage1-from-self (from v4.97.0, re-verify)

## Phase 2 -- Comprehensive measurement refresh

- [ ] Test count: total pytest count, golden count, integration count, benchmark count
- [ ] Line count: self-hosted compiler (.mn), Python bootstrap (.py), C runtime (.c/.h), total
- [ ] Benchmark summary: headline numbers from `benchmarks/FINAL_REPORT.md`
- [ ] Carry-forward state: should be 0 Mapanare-owned open items. Verify.
- [ ] Culebra summary: `culebra summary mapanare/self/main.ll`
- [ ] Write `docs/roadmap/v4/v4.99.0/MEASUREMENTS.md` with all of the above

## Phase 3 -- Retrospective

- [ ] Write `docs/roadmap/v4/v4.99.0/RETROSPECTIVE.md` -- the full v4.x journey:
  - **The beginning** (v4.0.0): production release, 45-release plan starts at v4.32.0
  - **The crisis** (v4.26.0): 8.2/10 aggregate, hollow features discovered, recovery arc triggered
  - **The recovery** (v4.27.0-v4.31.0): 9.343/10, the discipline installed
  - **The plan** (v4.32.0-v4.76.0): 45 releases, 9 arcs, every feature real and tested
  - **The extension** (v4.77.0-v4.98.0): 22 more releases, 5 arcs, optimization + async + maturity
  - **The numbers**: test count over time, panel scores over time, carry-forward items over time
  - **What worked**: the cadence, the panel system, the carry-forward ledger, Culebra, the PLAN.md discipline
  - **What didn't**: things that took too long, false starts, features that had to be redone
  - **What v5.0.0 means**: if tagged, what does the label signify? What is the bar?
- [ ] Keep it factual. Numbers, version tags, session report references. Not prose poetry.

## Phase 4 -- Pre-panel audit

- [ ] Fact-check every SESSION_REPORT.md claim from v4.77.0-v4.98.0 (spot-check at minimum)
- [ ] Verify each arc's stated outcomes against actual artifacts:
  - Arc 10: does `tests/integration/` exist and run? Is CARRY_FORWARD.md at 0?
  - Arc 11: does `benchmarks/optimizer/BASELINE.md` exist? Do nsw/nuw flags appear in emitted IR?
  - Arc 12: does `mir_opt.py` have inlining + LICM + escape analysis?
  - Arc 13: does `53_real_await.mn` demonstrate real suspension? Does the scheduler pass stress tests?
  - Arc 14: does `mir_opt.mn` have all 4 passes? Does `FINAL_REPORT.md` exist with 15 benchmarks?
- [ ] Write `.reviews/v4.99.0/PRE_PANEL_AUDIT.md`

## Phase 5 -- Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.99.0. Arc: Arc 14 (Final Polish + v5 Gate).
  - Scope: grade Arcs 10-14 holistically (v4.77.0-v4.98.0)
  - Primary context: `FINAL_REPORT.md`, `RETROSPECTIVE.md`, `MEASUREMENTS.md`
- [ ] `mkdir -p .reviews/v4.99.0/` + pre-populate with context files
- [ ] Spawn 7 reviewers with specific questions (listed above in "What the panel grades")
- [ ] Each reviewer grades:
  - The work in their domain across all 5 arcs
  - Whether the quality bar is sufficient for a v5.0.0 label
  - Any remaining gaps that would block v5.0.0
- [ ] Collect verdicts. Compute aggregate.

## Phase 6 -- v5 decision

- [ ] Record the aggregate score in `.reviews/v4.99.0/README.md`
- [ ] Apply the decision rule:
  - **Aggregate >= 9.0 AND 0 NEEDS WORK -> Option A (tag v5.0.0)**
  - **Aggregate < 9.0 -> Option B (continue v4.100.0+)**
  - **Aggregate >= 8.5 AND < 9.0 -> Option C (tag v5.0.0 + open v4.100.0)**
- [ ] Document the decision in `.reviews/v4.99.0/V5_DECISION.md`:
  - The aggregate score
  - Which option was selected
  - If Option B: what the panel says needs fixing before v5
  - If Option A or C: the v5.0.0 tag commit message
- [ ] If Option A or C: prepare the tag (do not push -- the lead pushes the tag manually)
  ```bash
  git tag -a v5.0.0 -m "Mapanare v5.0.0 — tagged from v4.99.0 panel (aggregate X.XX/10)"
  ```

## Phase 7 -- Closeout

- [ ] `.reviews/v4.99.0/README.md` written with full panel summary
- [ ] `CARRY_FORWARD.md` final audit -- should show 0 open items
- [ ] Update `docs/roadmap/ROADMAP.md` with final v4.x status:
  - Total releases in v4.x
  - Total panel reviews
  - Final aggregate score
  - v5 decision
- [ ] Update `CLAUDE.md` current version section
- [ ] Archive Culebra: `cp .culebra-journal.jsonl docs/roadmap/v4/v4.99.0/culebra-journal.jsonl`
- [ ] `SESSION_REPORT.md` written -- the final v4.x session report
- [ ] `CHANGELOG.md [4.99.0]` entry
- [ ] `VERSION` bumped to either `5.0.0` (Option A), `4.100.0` (Option B), or `5.0.0` (Option C)

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Pre-panel sweep clean: all tests pass, valgrind clean, TSan clean | test logs, valgrind output |
| 2 | Measurements recorded | `MEASUREMENTS.md` |
| 3 | Retrospective written | `RETROSPECTIVE.md` |
| 4 | Pre-panel audit complete | `PRE_PANEL_AUDIT.md` |
| 5 | Panel runs: 7 reviewers file verdicts | `.reviews/v4.99.0/*.md` |
| 6 | Aggregate score recorded | `.reviews/v4.99.0/README.md` |
| 7 | v5 decision documented | `V5_DECISION.md` |
| 8 | Decision rule applied correctly (A/B/C based on aggregate) | `V5_DECISION.md` references score + rule |
| 9 | All benchmarks verified reproducible | `benchmarks/run_final.py` completes |
| 10 | Carry-forward at 0 Mapanare-owned open items | `CARRY_FORWARD.md` audit |
| 11 | `ROADMAP.md` updated with final v4.x status | diff |
| 12 | `CHANGELOG.md` entry for v4.99.0 | diff |
| 13 | `SESSION_REPORT.md` written | file |

---

## What this release does NOT do

- **Implement v5 features** -- this is a decision, not a development release.
- **New optimizations** -- the optimization work ended in v4.97.0.
- **New benchmarks** -- the benchmark work ended in v4.98.0.
- **Fix panel findings** -- if the panel identifies issues, those are v4.100.0 or v5.1.0 work. v4.99.0 records the findings; it does not fix them.
- **Change the cadence** -- whether the outcome is v5.0.0 or v4.100.0, the discipline (PLAN.md + PROMPT.md + SESSION_REPORT.md + panel every 5 minors + carry-forward ledger) continues unchanged.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel aggregate falls below 8.5 (Option B, no v5 tag) | medium | medium | This is the system working, not a failure. Option B means more work before v5. The arcs continue. |
| One reviewer gives NEEDS WORK, dragging aggregate below 9.0 | medium | medium | Option C covers this case -- tag v5.0.0 as a milestone, continue fixing. |
| Retrospective is too long or too self-congratulatory | low | low | Stick to numbers and version references. One page of tables, one page of analysis. |
| Pre-panel audit discovers a SESSION_REPORT claim that was false | low | high | Fix the record. Note the correction in the audit. Honesty above optics. |
| The v5 decision is contentious (panel disagrees on readiness) | low | medium | The decision rule is mechanical: aggregate + NEEDS WORK count. No ambiguity. The lead executes the rule. |
| The retrospective reveals that some optimization claims were overstated | medium | medium | Re-run the specific benchmark. Correct the FINAL_REPORT.md if needed. Ship honest numbers. |

---

## If the panel says PASS (aggregate >= 9.0)

**Option A executes.** v5.0.0 is tagged from v4.99.0. The v4.x line ends
at 99 releases (or however many there actually were). The next work opens
as v5.1.0. The cadence -- PLAN.md, PROMPT.md, SESSION_REPORT.md, panels,
carry-forward -- carries forward unchanged.

v5.0.0 is not a new architecture. It is a label that says: "the 67+
releases of post-recovery discipline produced a compiler that passes
external review." The work continues.

## If the panel says NEEDS WORK

**Option B executes.** v4.100.0 opens. The panel's docket becomes the
scope for Arc 15. The next scheduled panel is v4.104.0 (5-minor cadence).
No shame. The cadence works regardless of the label.

---

## After v4.99.0

Whatever the panel decides, the cadence carries forward. The system works.

The 45-release POST_RECOVERY_ROADMAP ended at v4.76.0. Arcs 10-14 were
the lead's choice to continue. v4.99.0 is the natural checkpoint: grade
the extension, decide the label. Whether the next release is v5.1.0 or
v4.100.0, the discipline is the same:

- **PLAN.md + PROMPT.md + SESSION_REPORT.md per release**
- **Delta review per new syntax**
- **Full panel every 5 minors**
- **CARRY_FORWARD.md as single source of truth**
- **Culebra as primary IR diagnostic**
- **Validation before every commit**

The plan was never about reaching v5. It was about the cadence.
**The cadence works.**
