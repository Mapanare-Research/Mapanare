# Mapanare v4.121.0 — DWARF Warning + Bounded-Generic Trait Fix

> **Post-panel closeout release 1.** v4.120.0 returned 8.21/10 with
> Option B (continue v4.121.0+). v4.120.0 also shipped the test
> hygiene sweep: 14 CLI tests rewritten against `transpile`, 4
> count-drift assertions fixed, 1 linkage assertion relaxed. That
> closed 20 of the 22 deterministic failures from the v4.117.0 flaky
> audit. This release closes the remaining: 3 DWARF `-g`
> deferral-warning tests and 1 bounded-generic trait monomorphization
> edge case. After v4.121.0, the 22-failure list is fully resolved.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.120.0
**Delta review:** No
**Full panel:** No (v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Close the last 22 deterministic test failures. Zero known flakes.

> **Shipped 2026-04-14.** Scope expanded mid-release: in addition to
> the planned 4 failures (3 DWARF + 1 bounded-generic trait), the 18
> hygiene cases the v4.120.0 SESSION_REPORT claimed but never
> actually shipped (4 stale-assertion failures + 14 stale CLI tests
> against the removed `compile` subcommand) were also closed here so
> the audit-subset exit criterion ("0 failures") could be met
> honestly. See `SESSION_REPORT.md` for the full ship summary.

---

## Scope

The v4.117.0 flaky audit identified 22 deterministic test failures. v4.120.0 resolved 20 of them (14 stale CLI tests, 4 count-drift assertions, 1 linkage assertion, 1 emitter hardening count). Two failure classes remain:

**3 DWARF `-g` deferral-warning tests.** SPEC section 21.3 specifies that when the `-g` flag is passed, the compiler should emit a stderr warning: "debug info deferred to v5.x -- compiling without DWARF." The CLI does not currently emit this warning. Three tests assert on it and fail.

**1 bounded-generic trait monomorphization edge case.** A generic function with trait bounds fails to monomorphize in certain contexts. The root cause is likely in `mapanare/semantic.py` (trait bound resolution during monomorphization) or `mapanare/emit_llvm_text.py` (generic function instantiation).

Both are small, well-scoped fixes. This is a cleanup release, not a feature release.

## Phase 1 — Implement `-g` deferral warning in CLI

- [ ] Read `mapanare/cli.py` — find where the `-g` / `--debug` flag is parsed
- [ ] Add stderr warning when `-g` is passed: `"warning: debug info (-g) deferred to v5.x -- compiling without DWARF"`
- [ ] The warning must go to stderr (not stdout) to avoid polluting program output
- [ ] The flag should still be accepted (not rejected) — the warning is informational, not an error
- [ ] Verify the warning text matches what SPEC section 21.3 specifies

## Phase 2 — Fix the 3 DWARF deferral-warning tests

- [ ] Find the 3 failing DWARF tests (likely in `tests/` — grep for `-g` or `DWARF` or `debug info`)
- [ ] Verify each test now passes with the Phase 1 change
- [ ] If tests assert on exact warning text, ensure the text matches
- [ ] Run the 3 tests individually to confirm

## Phase 3 — Investigate bounded-generic trait monomorphization

- [ ] Find the failing test (grep for `bounded` or `trait` in test names, or check v4.117.0 audit notes)
- [ ] Reproduce the failure: `pytest <test_file>::<test_name> -v`
- [ ] Read the test to understand what bounded-generic pattern it exercises
- [ ] Trace through `mapanare/semantic.py` — find where trait bounds are checked during generic monomorphization
- [ ] Compare with non-bounded generics (which work) to identify the divergence point

## Phase 4 — Fix bounded-generic trait monomorphization

- [ ] Implement the fix in `mapanare/semantic.py` and/or `mapanare/emit_llvm_text.py`
- [ ] Verify the failing test now passes
- [ ] Add a regression test if the existing test is insufficient
- [ ] Run the full generics test suite: `pytest tests/semantic/test_generics.py -v` (or similar)

## Phase 5 — Full test suite verification

- [ ] `make test` — target: 0 failures
- [ ] `make lint` — clean
- [ ] Verify all 22 deterministic failures from v4.117.0 are now resolved:
  - 14 CLI tests (v4.120.0) -- confirmed
  - 4 count-drift (v4.120.0) -- confirmed
  - 1 linkage (v4.120.0) -- confirmed
  - 1 emitter count (v4.120.0) -- confirmed
  - 3 DWARF warning (this release) -- confirmed
  - 1 bounded-generic trait (this release) -- confirmed
- [ ] Run `make test` 3 times to confirm no flaky failures

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.121.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `-g` deferral warning implemented in CLI | diff of `cli.py` |
| 2 | Warning goes to stderr, not stdout | test captures stderr |
| 3 | 3 DWARF tests pass | pytest output |
| 4 | Bounded-generic trait edge case fixed | pytest output |
| 5 | `make test` green (0 failures) | test log |
| 6 | `make lint` clean | lint log |
| 7 | All 22 deterministic failures resolved (20 in v4.120.0 + 4 here) | audit checklist |
| 8 | 3x `make test` with 0 flaky failures | 3 test logs |

---

## What this release does NOT do

- **Implement DWARF debug info** — the `-g` flag prints a deferral warning. Actual DWARF emission is v5.x.
- **Fix Qs.1 (List<Int> indexing)** — that is v4.122.0.
- **Delete optimizer.py** — that is v4.123.0.
- **Touch performance** — no benchmark work. Pure correctness.
- **Run a panel** — the next panel is v4.130.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| DWARF warning text doesn't match what existing tests expect | medium | low | Read the tests first, match the expected text exactly |
| Bounded-generic trait fix introduces a regression in non-bounded generics | low | high | Run full generics test suite after the fix |
| The trait edge case is deeper than semantic.py (touches lower.py or emit) | medium | medium | Phase 3 investigation traces the full path before coding |
| 3x test run reveals a new flaky test unrelated to these fixes | low | medium | Document the flake, don't block the release on pre-existing flakes |

---

## After v4.121.0

v4.122.0 fixes Qs.1: `List<Int>` indexing in argument position returns wrong value on the native pipeline. This is the highest-impact correctness bug remaining — it was called out in V5_READINESS as "would embarrass a v5 label." With all 22 deterministic test failures closed, the test suite is stable enough to confidently validate the Qs.1 fix.
