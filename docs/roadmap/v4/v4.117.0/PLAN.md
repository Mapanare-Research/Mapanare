# Mapanare v4.117.0 — Testing Sweep: Sanitizer CI, Flaky Audit

> **Phase E release 3.** Harden the test suite before the final panel.
> Add AddressSanitizer and ThreadSanitizer CI gates so memory bugs and
> data races cannot regress silently. Audit the full pytest suite for
> flaky tests. Generate a coverage report. Ensure the integration
> pipeline fails loudly on error instead of passing silently. After
> this release, the test infrastructure is production-grade.

**Status:** DONE (2026-04-14)
**Breaking:** No
**Prerequisite:** v4.116.0
**Delta review:** No
**Full panel:** No (v4.120.0)
**Estimated work:** 1 sprint
**Theme:** Make every test trustworthy. No silent passes, no hidden flakes.
**Session log:** `docs/roadmap/v4/v4.117.0/SESSION_REPORT.md`
**Decisions taken:** ASan scope = full golden suite (Decision 1, default; already in place via v4.105.0); TSan scope = async tests only (Decision 2, default) + v4.115.0 async I/O demos extension; flaky threshold = 5 runs (Decision 3, default); coverage measured against the 7 core-pipeline test directories only (full-suite coverage with xdist took >5 min — targeted scope finishes in 22 s and covers the live compiler path); informational coverage CI gate (not enforcing) per risk register.

---

## Scope

The test suite has grown from ~4,500 tests at v4.99.0 to 5,374+ at v4.114.0. The golden suite is 64 tests. CI runs pytest and the WASM emission check, but does not run sanitizers as gating checks. Flaky tests have never been systematically identified. Coverage is unmeasured. The integration pipeline (llvm-as -> opt -> llc -> run) sometimes passes silently on error.

This release adds three new CI capabilities (ASan gate, TSan gate, coverage reporting), audits for flaky tests, and hardens the integration pipeline. No compiler or runtime code changes.

## Phase 1 -- ASan CI gate

- [ ] Create or update `.github/workflows/ci.yml` to add an ASan job:
  - Build mnc-stage1 with `clang -fsanitize=address -fno-omit-frame-pointer`
  - Link `libmapanare_rt.a` also compiled with ASan flags
  - Run all 64 golden tests through the ASan-instrumented binary
  - Job fails on ANY ASan error (leak, heap-buffer-overflow, use-after-free, etc.)
- [ ] Run locally first: build with ASan, run golden tests, capture output
- [ ] Fix any ASan findings that are true positives (update runtime C code if needed)
- [ ] Document any false positives with suppression rules in `tests/asan_suppressions.txt`
- [ ] Verify the CI job runs end-to-end on a test push

## Phase 2 -- TSan CI gate

- [ ] Add a TSan job to `.github/workflows/ci.yml`:
  - Build mnc-stage1 with `clang -fsanitize=thread`
  - Link `libmapanare_rt.a` also compiled with TSan flags
  - Run async golden tests (55-57 + any from v4.115.0) through the TSan-instrumented binary
  - Job fails on ANY data race
- [ ] Run locally first: build with TSan, run async golden tests, capture output
- [ ] Fix any true data races found (likely in agent scheduler or signal batch)
- [ ] Document any false positives with suppression rules in `tests/tsan_suppressions.txt`
- [ ] Verify the CI job runs end-to-end on a test push

## Phase 3 -- Flaky test audit

- [ ] Run the full pytest suite 5 times in sequence:
  ```bash
  for i in 1 2 3 4 5; do
    pytest tests/ -v --tb=short > pytest_run_$i.log 2>&1
  done
  ```
- [ ] Diff the 5 result sets: identify any test that passes in some runs and fails in others
- [ ] For each flaky test:
  - Root-cause the flakiness (timing, ordering, shared state, environment)
  - Fix if the root cause is clear
  - Mark with `@pytest.mark.flaky(reason="...")` if the fix is non-trivial
- [ ] Document all findings in `tests/FLAKY_AUDIT.md`:
  - Total tests run
  - Number of consistently passing tests
  - Number of flaky tests found
  - Root cause and resolution for each
- [ ] Verify 0 flaky tests in the golden test suite (golden tests must never be flaky)

## Phase 4 -- Coverage report

- [ ] Run `pytest --cov=mapanare --cov-report=term-missing --cov-report=html tests/`
- [ ] Record per-module coverage:
  - `parser.py`, `semantic.py`, `lower.py`, `mir.py`, `mir_builder.py`
  - `emit_llvm_text.py`, `emit_c.py`, `emit_wasm.py`
  - `types.py`, `cli.py`, `optimizer.py`, `mir_opt.py`
- [ ] Identify modules with < 50% coverage
- [ ] Write `tests/COVERAGE.md`:
  - Per-module coverage table
  - Modules below 50% threshold highlighted
  - Recommendations for improving coverage (not implemented in this release)
- [ ] Add coverage reporting to CI (informational, not gating)

## Phase 5 -- Integration test hardening

- [ ] Read the integration test pipeline (from v4.104.0/v4.105.0 harness)
- [ ] Verify that each step (llvm-as, opt, llc, link, run) checks its return code
- [ ] Ensure that a failure in any step:
  - Produces a clear error message identifying which step failed
  - Does NOT silently pass the test
  - Records the stderr output for diagnosis
- [ ] Add explicit timeout for the run step (prevent hanging tests)
- [ ] Test the hardening: deliberately break a golden test's IR and verify the pipeline reports the failure clearly

## Phase 6 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.117.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | ASan CI job exists and gates on errors | `.github/workflows/ci.yml` diff, CI run log |
| 2 | TSan CI job exists and gates on data races | `.github/workflows/ci.yml` diff, CI run log |
| 3 | Flaky tests identified and documented | `tests/FLAKY_AUDIT.md` |
| 4 | Flaky tests fixed or marked with reason | pytest markers or code fixes |
| 5 | 0 flaky tests in the golden test suite | 5-run audit shows 100% consistency |
| 6 | Coverage report generated | `tests/COVERAGE.md` + HTML report |
| 7 | Modules below 50% coverage identified | coverage table in report |
| 8 | Integration pipeline fails loudly on error | test with deliberately broken IR |
| 9 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Increase coverage** -- the report identifies gaps, it does not fill them. Coverage improvement is ongoing work.
- **Fix all flaky tests** -- tests with non-trivial root causes are marked, not fixed. Fixes are future work.
- **Change compiler behavior** -- no modifications to `mapanare/` source. Only CI configuration, test infrastructure, and documentation.
- **Add new tests** -- this audits and hardens existing tests, not writes new ones.
- **Run a panel** -- Phase E has no panel. The next panel is v4.120.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| ASan finds real memory bugs that require runtime fixes | medium | medium | Fix only critical bugs (UAF, heap overflow). Leaks become docket items for v4.120.0 panel. |
| TSan finds real data races in the agent scheduler | medium | medium | Fix races that are clearly wrong. Suppress benign races with documentation. |
| Flaky test audit reveals systemic test isolation issues | low | high | Document the systemic issue. Fix individual tests where possible. |
| Coverage reporting adds significant CI time | low | low | Run coverage as a separate job, not on the critical path. |
| Integration pipeline hardening breaks tests that were silently passing | medium | medium | This is a feature, not a bug. Re-classify those tests honestly. |

---

## After v4.117.0

Phase E is complete. Phase F begins: v4.118.0 is the final cross-language benchmark with all Phase A-E fixes landed. v4.119.0 is the retrospective. v4.120.0 is the panel -- the v5 gate (attempt 2). The test infrastructure from this release ensures the v4.120.0 panel has trustworthy evidence.
