# Mapanare v4.111.0 — Self-Hosted Golden: Target 64/64

> **Phase D release 1.** Phase A (v4.100.0-v4.103.0) fixed the 5
> critical/high docket items including the tagged-pointer cascade that
> caused 0/61 golden to pass on the native binary. Phase B
> (v4.104.0-v4.106.0) rebuilt, verified, and panel-confirmed those fixes.
> Phase C (v4.107.0-v4.110.0) ran Go+C benchmarks, fixed string
> performance, investigated optimizer, and refreshed benchmarks. Phase D
> focuses on self-hosted compiler maturity. This release tests whether
> mnc-stage1 built from the self-hosted pipeline now passes all 64 golden
> tests.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.110.0
**Delta review:** No
**Full panel:** No (v4.114.0)
**Estimated work:** 1 sprint
**Theme:** Self-hosted compiler golden parity — does the compiler that compiles itself produce correct output?

---

## Scope

After Phase A, the tagged-pointer cascade that caused 0/61 golden failures should be resolved. The self-hosted compiler (`mapanare/self/*.mn`, 38,824 lines) compiles itself via `bash scripts/rebuild.sh`. Phase B confirmed 64/64 golden through the Python-bootstrapped mnc-stage1. Phase D asks: does mnc-stage1 built from the self-hosted pipeline also pass 64/64?

This release rebuilds from the self-hosted pipeline, runs every golden test, documents any failures with root cause analysis, and fixes critical blockers. It also runs stage2 validation to confirm self-compilation health.

## Phase 1 — Rebuild mnc-stage1 from self-hosted pipeline

- [ ] Full rebuild: `bash scripts/rebuild.sh full`
- [ ] Record build time, binary size, any warnings or errors during compilation
- [ ] Verify the binary exists: `ls -la mapanare/self/mnc-stage1`
- [ ] Smoke test: compile `tests/golden/01_hello.mn` through mnc-stage1, verify output is correct
- [ ] If rebuild fails, document the failure mode and fix before proceeding

## Phase 2 — Run all 64 golden tests through self-hosted mnc-stage1

- [ ] Run ALL 64 golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record per-test result: PASS / FAIL / CRASH / TIMEOUT
- [ ] Record aggregate: N/64 pass
- [ ] Update `tests/golden/BENCHMARKS.md` with fresh metrics
- [ ] Compare results against Phase B baseline (v4.104.0 results) — identify any regressions

## Phase 3 — Failure analysis

- [ ] For each failing test, capture the exact error output
- [ ] Categorize each failure:
  - **Emitter bug**: self-hosted `emit_llvm.mn` generates wrong IR (wrong types, missing instructions, bad GEPs)
  - **MIR lowering bug**: self-hosted `lower.mn` produces incorrect MIR (wrong control flow, missing variables)
  - **Parser bug**: self-hosted `parser.mn` misparses syntax that Python handles correctly
  - **Other**: runtime issue, linker issue, test harness issue
- [ ] For each category, note whether the fix belongs in `mapanare/self/*.mn` or elsewhere
- [ ] Document all failures in `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`

## Phase 4 — Fix critical failures

- [ ] Identify failures that block a majority of tests (shared root causes)
- [ ] Fix those root causes in the self-hosted sources (`mapanare/self/*.mn`)
- [ ] After each fix, re-run the full golden suite to measure progress
- [ ] Target: 64/64. If some tests fail due to unrelated self-hosted emitter gaps, document and move on.
- [ ] Do NOT fix by working around in the test harness — fix in the compiler

## Phase 5 — Stage2 validation

- [ ] Run stage2 validation: `python scripts/ir_doctor.py stage2`
- [ ] Record result: does stage2 IR validate with llvm-as?
- [ ] If stage2 fails, document which modules fail and why
- [ ] Run `culebra scan mapanare/self/main.ll` for IR health check
- [ ] Compare culebra findings against Phase B baseline

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.111.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | mnc-stage1 rebuilt from self-hosted pipeline | build log, binary exists |
| 2 | All 64 golden tests run through self-hosted mnc-stage1 | test log with per-test results |
| 3 | Golden pass count recorded (target: 64/64) | aggregate in test log |
| 4 | Any failures documented with root cause category | `GOLDEN_FAILURES.md` |
| 5 | Critical shared-root-cause failures fixed | diffs of `mapanare/self/*.mn` |
| 6 | Stage2 validation run and result recorded | `ir_doctor.py stage2` output |
| 7 | Culebra scan run, findings recorded | culebra output |
| 8 | `tests/golden/BENCHMARKS.md` updated | diff |
| 9 | Integration pipeline tested on pass/fail boundary | test output |

---

## What this release does NOT do

- **Fix the byref size heuristic** — that is v4.112.0 (docket item #7).
- **Run fixed-point verification** — that is v4.112.0.
- **Touch the coroutine frame** — that is v4.113.0 (docket item #8).
- **Run a panel** — the Phase D panel is v4.114.0.
- **Modify the Python bootstrap** — this release tests the self-hosted pipeline. Python bootstrap changes are out of scope.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Self-hosted mnc-stage1 fails on tests that Python-bootstrapped mnc-stage1 passes | medium | high | Categorize failures. If the root cause is shared (e.g., emitter gap), one fix may unblock many tests. |
| Rebuild itself fails (self-hosted cannot compile itself after Phase A changes) | low | high | Fall back to `python scripts/build_stage1.py` for a Python-bootstrapped binary; debug self-hosted build separately. |
| Stage2 validation regresses from Phase B baseline | low | medium | Compare culebra findings delta. Phase A fixes should not have introduced new IR pathologies. |
| Fixing critical failures in self-hosted sources breaks other tests | medium | medium | Run full golden suite after every fix. Small, targeted changes. |
| Some failures are genuine self-hosted emitter gaps unrelated to tagged-pointer | high | low | Document these as future work. Do not block the release on long-standing gaps. |

---

## After v4.111.0

v4.112.0 runs fixed-point verification: does stage1-from-Python == stage1-from-self? Fixes docket item #7 (byref size heuristic divergence) where the self-hosted emitter returns 256 for all named structs instead of computing actual sizes. After v4.112.0, the two compilation paths should converge.
