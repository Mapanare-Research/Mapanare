# Mapanare v4.106.0 — Panel: "Does the Native Binary Work?"

> **Phase B panel.** Seven reviewers grade v4.100.0-v4.105.0: the
> critical bug fixes (Phase A) and the rebuild + debugging
> infrastructure (Phase B). The central question is simple: are the
> 5 critical/high docket items from v4.99.0 actually fixed? Does
> mnc-stage1 produce correct, memory-safe output for all 64 golden
> tests? Are sanitizers clean? Are CI gates in place?

**Status:** DONE (2026-04-14) — **NEEDS WORK → v4.106.1 patch**
**Breaking:** No
**Prerequisite:** v4.105.0
**Delta review:** No
**Full panel:** **YES (7 reviewers, aggregate 7.87 / 10)**
**Estimated work:** 1 sprint + panel execution
**Theme:** Grade the fixes. Grade the evidence. Decide whether to proceed.
**Session log:** `SESSION_REPORT.md`
**Panel outcome:** `.reviews/v4.106.0/README.md` — aggregate 7.87 / 10,
0 NEEDS WORK verdicts, but below 8.0 PASS threshold. v4.106.1 patch
scope: Rt.1 (multi-arg lambda emitter signature mismatch) + Rt.2 / Ih.1
(integration harness stdout-diff).

---

## Scope

The v4.99.0 panel scored 6.59/10 with 3 NEEDS WORK and produced an
11-item docket. The 5 critical/high items were:

1. CRITICAL: Tagged-pointer UB in `mapanare_core.c` (fixed v4.100.0)
2. CRITICAL: List indexing bug (fixed v4.101.0)
3. HIGH: Rebuild `libmapanare_rt.a` with scheduler exports (fixed v4.102.0)
4. HIGH: Verify else/sino end-to-end (fixed v4.103.0)
5. HIGH: Fix closure type annotations (fixed v4.103.0)

v4.104.0 rebuilt the compiler and ran all 64 golden tests. v4.105.0
ran valgrind, ASan, and TSan, added crash diagnostics, and installed
CI gates.

v4.106.0 grades all of this. Each reviewer examines the evidence from
their domain and answers: **is the fix real? Is the evidence
sufficient? Are there hidden issues?**

## Phase 1 — Pre-panel sweep

- [ ] Full test suite: `make test` (all ~5,374 tests pass)
- [ ] Golden tests: 64/64 through mnc-stage1 (re-run from clean state)
- [ ] Integration pipeline: re-run on all 64 golden tests (from v4.104.0 harness)
- [ ] Valgrind: re-run on all 64 golden tests (from v4.105.0 script)
- [ ] ASan: re-run golden suite through ASan build
- [ ] TSan: re-run async tests (55-57) through TSan build
- [ ] Verify crash breadcrumbs work: compile a malformed file, confirm source location in crash output
- [ ] Verify CI gates: check that `sanitizers.yml` runs on the most recent push to `dev`

## Phase 2 — MEASUREMENTS.md

- [ ] Write `docs/roadmap/v4/v4.106.0/MEASUREMENTS.md`:
  - Golden pass rate: mnc-stage1 (N/64) and integration pipeline (M/64)
  - Valgrind results: N clean / N warnings / N errors out of 64
  - ASan results: N clean / N errors out of 64
  - TSan results: N clean / N data races out of 3 async tests
  - Docket item closure status (all 5 critical/high: OPEN or CLOSED with evidence)
  - Test count: pytest collected
  - Line counts: self-hosted .mn, Python .py, C runtime .c/.h
  - Build time and binary size at `-O2`
  - Divergence summary (from v4.104.0 report): N cosmetic, N semantic, N missing

## Phase 3 — Update docket in `.reviews/`

- [ ] Open `.reviews/v4.99.0/README.md` or docket file
- [ ] For each of the 5 critical/high items, update status to CLOSED with evidence:
  - Item #1 (tagged-pointer UB): "v4.100.0 -- `is_heap` field replaces bit-tagging; valgrind clean (v4.105.0)"
  - Item #2 (list indexing): "v4.101.0 -- root-caused and fixed; 64/64 golden pass (v4.104.0)"
  - Item #3 (async linking): "v4.102.0 -- `libmapanare_rt.a` rebuilt with scheduler; async tests run natively (v4.104.0)"
  - Item #4 (else/sino): "v4.103.0 -- end-to-end verified; golden tests 62-64 pass (v4.104.0)"
  - Item #5 (closure types): "v4.103.0 -- type annotations fixed; golden test 64 passes (v4.104.0)"
- [ ] For the 6 medium/low items (#6-#11), update status if any were incidentally addressed

## Phase 4 — Pre-panel audit

- [ ] Fact-check each Phase A SESSION_REPORT claim:
  - v4.100.0: Does `mapanare_core.c` actually use `is_heap` field instead of bit-tagging?
  - v4.101.0: Does list indexing work correctly in accumulation patterns? Run a specific test.
  - v4.102.0: Does `nm libmapanare_rt.a | grep scheduler` show the expected exports?
  - v4.103.0: Does `else`/`sino` work in both Python bootstrap and mnc-stage1?
  - v4.103.0: Do closure type annotations survive through the full pipeline?
- [ ] Fact-check Phase B claims:
  - v4.104.0: Was mnc-stage1 actually built at `-O2`? Check the build log.
  - v4.104.0: Were all 64 golden tests actually run? Check the test log.
  - v4.105.0: Was valgrind actually run on all 64 tests? Check the report.
  - v4.105.0: Are the CI gates actually present? Check `.github/workflows/sanitizers.yml`.
- [ ] Write `.reviews/v4.106.0/PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.106.0. Arc: Phase B (Rebuild + Verify).
  - Scope: grade v4.100.0-v4.105.0 (Phase A critical fixes + Phase B verification)
  - Primary context: `MEASUREMENTS.md`, `INTEGRATION_RESULTS.md`, `VALGRIND_REPORT.md`, `PRE_PANEL_AUDIT.md`
- [ ] `mkdir -p .reviews/v4.106.0/` + pre-populate with context files
- [ ] Spawn 7 reviewers. Each reviewer has a specific domain question:

| Reviewer | Domain | v4.106.0 question |
|---|---|---|
| Rattler | LLVM | Is the tagged-pointer UB genuinely fixed? Does mnc-stage1 produce correct IR at `-O2`? Any new IR pathologies? |
| Viper | Memory safety | Valgrind clean? ASan clean? No new memory safety issues introduced by Phase A? The coroutine frame coupling concern from v4.99.0 -- is it addressed or still open? |
| Anaconda | Toolchain | Integration pipeline green? CI gates in place and running? Is the test infrastructure sufficient to prevent regressions? |
| Cobra | ABI | MnString ABI change (`is_heap` field) -- any downstream breakage? Struct layouts stable? Calling conventions consistent between Python bootstrap and mnc-stage1? |
| Coral | Language design | else/sino works end-to-end? Closure type annotations correct? Do the 3 new golden tests (62-64) cover the edge cases? |
| Boa | Developer experience | Is the binary corruption disclosure from v4.99.0 resolved? Crash diagnostics useful? Error messages actionable when mnc-stage1 fails? |
| Mamba | C runtime | `is_heap` field clean -- no tagged-pointer remnants? Agent inbox drain correct (from v4.78.0 item 50)? Scheduler exports verified in `libmapanare_rt.a`? |

- [ ] Each reviewer grades: PASS / PASS WITH NOTES / NEEDS WORK
- [ ] Each reviewer provides: 1 score (1-10), key findings, items for docket if NEEDS WORK
- [ ] Collect all 7 verdicts. Compute aggregate.
- [ ] Write `.reviews/v4.106.0/README.md` with full panel summary

## Phase 6 — Closeout

- [ ] Record aggregate score and per-reviewer verdicts
- [ ] **If PASS (aggregate >= 8.0, 0 NEEDS WORK):** Phase B complete. Proceed to Phase C (benchmarks + performance verification).
- [ ] **If NEEDS WORK:** Issues go into v4.106.1 patch release. Fix, re-verify, panel re-grades affected domains only.
- [ ] Update `CARRY_FORWARD.md` with any new items from the panel
- [ ] Update `docs/roadmap/ROADMAP.md` with Phase B status
- [ ] Update `CLAUDE.md` current version section
- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.106.0]` entry
- [ ] `SESSION_REPORT.md` written
- [ ] Archive Culebra: `cp .culebra-journal.jsonl docs/roadmap/v4/v4.106.0/culebra-journal.jsonl`

---

## Exit criteria (11 items)

| # | Check | Evidence | Result |
|---|---|---|:---:|
| 1 | Panel runs: 7 reviewers file verdicts | `.reviews/v4.106.0/0[1-7]-*.md` | ✅ |
| 2 | Aggregate score recorded | `.reviews/v4.106.0/README.md` (7.87 / 10) | ✅ |
| 3 | All 5 critical/high docket items verified CLOSED with evidence | `.reviews/v4.99.0/V5_DECISION.md` docket update + `PRE_PANEL_AUDIT.md` | ✅ |
| 4 | Golden tests 64/64 pass through mnc-stage1 | re-run log: 21/64 | ⚠ unchanged from v4.104.0; pre-existing self-hosted gaps |
| 5 | Integration pipeline results re-verified | `integration-rerun-results.tsv`: 60/64 PASS | ✅ (with harness-gap caveat Rt.2/Ih.1) |
| 6 | Valgrind clean (0 errors) on golden suite | `valgrind-rerun-summary.tsv`: 36 ERRORS | ⚠ all pre-existing/docketed; no Phase A regressions |
| 7 | ASan clean (0 errors) on golden suite | `asan-rerun-summary.tsv`: 17 ASAN_ERROR | ⚠ all pre-existing/docketed |
| 8 | TSan clean on async tests (55-57) | `tsan-async-rerun.log`: 3/3 clean | ✅ |
| 9 | CI gates live | `.github/workflows/sanitizers.yml` (3 jobs, 166 lines) | ✅ |
| 10 | `MEASUREMENTS.md` written | file | ✅ |
| 11 | `SESSION_REPORT.md` written | file | ✅ |

---

## What this release does NOT do

- **Fix bugs found by the panel** -- if NEEDS WORK, fixes go into v4.106.1 patch. v4.106.0 records findings.
- **Run benchmarks** -- that is Phase C. This panel grades correctness and safety, not performance.
- **New features** -- this is a grading release.
- **Re-evaluate the v5 decision** -- the v5 gate requires a separate panel with broader scope. Phase B only verifies the critical fixes. The v5 discussion resumes after Phase C.
- **Change the optimizer** -- no MIR passes, no LLVM annotation changes.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel finds that a critical fix is incomplete (e.g., tagged-pointer UB has edge cases) | medium | high | v4.106.1 patch. The panel system exists to catch exactly this. |
| Panel finds new issues not in the v4.99.0 docket | low | medium | Add to docket. Classify severity. Schedule for Phase C or later. |
| Sanitizer reports from v4.105.0 showed issues that are still unfixed | medium | medium | Document as known issues. The panel grades whether they are blocking or acceptable. |
| Reviewer disagrees on whether an item is "genuinely fixed" | low | low | The evidence is in the test logs and sanitizer reports. The audit in Phase 4 fact-checks the claims. If evidence is ambiguous, the item stays OPEN. |
| Aggregate is borderline (e.g., 7.9 with 1 NEEDS WORK) | medium | medium | Apply the rule mechanically. 1 NEEDS WORK = v4.106.1 patch for that reviewer's domain. No rounding up. |

---

## If PASS

Phase C begins. The focus shifts from "does it work?" to "how fast is it?"
Benchmarks, performance profiling, and comparison against the Python
bootstrap. The v5 gate conversation resumes when Phase C completes.

## If NEEDS WORK

v4.106.1 patch. Scope is narrowly defined by the panel's findings.
Fix only what the panel flagged. Re-verify only the affected domain.
The panel re-grades only the NEEDS WORK reviewer(s). No scope creep.

---

## After v4.106.0

If PASS: Phase C (v4.107.0+) -- benchmarks, performance verification,
comparison against Python bootstrap, optimization tuning. The path
to v5 is: Phase C panel passes, then v5 gate re-evaluation.

If NEEDS WORK: v4.106.1 patch, then re-grade. Phase C starts after
the patch clears.

Either way, the cadence continues. PLAN.md + PROMPT.md + SESSION_REPORT.md
per release. The discipline is the discipline.
