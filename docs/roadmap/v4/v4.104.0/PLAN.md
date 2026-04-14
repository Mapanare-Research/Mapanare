# Mapanare v4.104.0 — Rebuild mnc-stage1 + Golden Verification

> **Phase B release 1.** Phase A (v4.100.0-v4.103.0) fixed the five
> critical and high docket items from the v4.99.0 panel: tagged-pointer
> UB, list indexing, async linking, else/sino, closure types. Phase B
> verifies the fixes actually work. This release rebuilds mnc-stage1
> from scratch with `-O2`, runs all 64 golden tests through both
> mnc-stage1 and the full integration pipeline, and produces a
> divergence report comparing Python bootstrap output vs native output
> for every test.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.103.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Rebuild everything. Run everything. Trust nothing until measured.

---

## Scope

Phase A made five targeted fixes across four releases. Each fix was
tested in isolation during its own release. v4.104.0 is where we
verify the whole picture: does the compiler, built from the fixed
sources at `-O2`, produce correct output for all 64 golden tests?
Does the output survive the full LLVM integration pipeline? Does the
native binary match the Python bootstrap?

This is not a feature release. It is a verification release. The only
artifacts are test logs, pipeline results, and a divergence report.

## Phase 1 — Full rebuild

- [ ] Clean build environment: remove old `mapanare/self/mnc-stage1` and all cached `.ll` / `.o` files
- [ ] Full rebuild: `python scripts/build_stage1.py` with `-O2` optimization
- [ ] Verify the binary exists and runs: `./mapanare/self/mnc-stage1 --version` (or equivalent)
- [ ] Smoke test: compile a trivial `.mn` file through mnc-stage1, verify output is not garbled
- [ ] Record build time, binary size, and any warnings emitted during compilation

## Phase 2 — Golden test suite (64/64 target)

- [ ] Run ALL 64 golden tests through mnc-stage1: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record each test's result: PASS / FAIL / CRASH / TIMEOUT
- [ ] For any failures: capture the error output, do NOT attempt to fix (document only)
- [ ] Target: 64/64 pass. If fewer, record the exact count and the specific failures.
- [ ] Update `tests/golden/BENCHMARKS.md` with fresh metrics

## Phase 3 — Integration pipeline (llvm-as + opt + llc + run)

- [ ] For each of the 64 golden tests, run the full integration pipeline:
  ```bash
  llvm-as <test>.ll -o <test>.bc
  opt -O2 <test>.bc -o <test>.opt.bc
  llc <test>.opt.bc -o <test>.s
  clang <test>.s -o <test> -lmapanare_rt -lm -lpthread
  ./<test>
  ```
- [ ] Record per-test result: PASS / FAIL / CRASH / LINK_ERROR / TIMEOUT
- [ ] Separate failures into categories: llvm-as error, opt error, llc error, link error, runtime crash, wrong output
- [ ] Write integration results table to `docs/roadmap/v4/v4.104.0/INTEGRATION_RESULTS.md`

## Phase 4 — Async golden tests (55-57) native execution

- [ ] Compile async golden tests (55_async_await.mn, 56_async_channels.mn, 57_async_spawn.mn) through full native pipeline
- [ ] Link against `libmapanare_rt.a` (must include scheduler exports from v4.102.0 fix)
- [ ] Run each binary, capture stdout
- [ ] Verify output matches expected results (from the Python bootstrap reference)
- [ ] Record: compiles? links? runs? correct output?

## Phase 5 — Divergence report (Python bootstrap vs mnc-stage1)

- [ ] For each of the 64 golden tests:
  - Compile through Python bootstrap (`mapanare emit-llvm`)
  - Compile through mnc-stage1
  - Diff the emitted LLVM IR
- [ ] Classify divergences:
  - **Cosmetic**: different temp names, different block ordering (acceptable)
  - **Semantic**: different types, different instructions, missing functions (investigate)
  - **Missing**: mnc-stage1 fails to compile a test that Python bootstrap handles (critical)
- [ ] Write `docs/roadmap/v4/v4.104.0/DIVERGENCE_REPORT.md` with per-test findings
- [ ] Any semantic divergences become docket items for the v4.106.0 panel

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.104.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | mnc-stage1 rebuilt with `-O2`, binary is clean (no garbled output) | build log, smoke test |
| 2 | 64/64 golden tests pass through mnc-stage1 | test log |
| 3 | Integration pipeline results recorded for all 64 tests | `INTEGRATION_RESULTS.md` |
| 4 | Async golden tests (55-57) compiled, linked, and run natively | test output |
| 5 | Divergence report written (Python bootstrap vs mnc-stage1) | `DIVERGENCE_REPORT.md` |
| 6 | Semantic divergences (if any) documented as docket items | divergence report |
| 7 | `tests/golden/BENCHMARKS.md` updated | diff |
| 8 | `CHANGELOG.md` entry for v4.104.0 | diff |
| 9 | `SESSION_REPORT.md` written | file |

---

## What this release does NOT do

- **Fix new bugs found** -- this is a measurement release. Bugs discovered during verification are documented, not fixed. Fixes go into v4.105.0 or later.
- **Change the optimizer** -- no modifications to `mir_opt.py`, `optimizer.py`, or any MIR pass.
- **Change the runtime** -- no modifications to `runtime/native/`. Phase A already made the C runtime changes.
- **Add new golden tests** -- the 64-test corpus from v4.103.0 is the fixed target.
- **Attempt self-compilation** -- fixed-point verification is a future milestone. This release verifies the binary works, not that it can compile itself.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Some golden tests fail through mnc-stage1 despite Phase A fixes | medium | medium | Document exact failures. The panel at v4.106.0 will evaluate whether the count is acceptable. |
| Integration pipeline fails on tests that pass through mnc-stage1 alone | medium | medium | Separate the failure category (llvm-as vs opt vs llc vs link vs runtime). Many integration failures are known LLVM version issues, not compiler bugs. |
| Async tests fail to link despite v4.102.0 fix | low | high | Verify `libmapanare_rt.a` was rebuilt with scheduler exports. If not, rebuild is Phase 1 work, not a new bug. |
| Divergence report shows widespread semantic differences | low | high | Classify severity. Cosmetic differences are expected. Semantic differences become v4.106.0 docket items. |
| Build takes too long at `-O2` | low | low | Record build time. If over 10 minutes, note it. `-O1` is an acceptable fallback. |

---

## After v4.104.0

v4.105.0 builds debugging infrastructure: valgrind, ASan, TSan on the full golden suite. v4.106.0 is the Phase B panel where 7 reviewers grade whether the critical bugs are actually fixed and the native binary works.
