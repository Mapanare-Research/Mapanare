# Mapanare v4.121.0 — Test + Lint Hygiene Sweep

> **Phase G release 1.** The v4.120.0 panel closed at 8.21 with one
> NEEDS WORK from Anaconda (CI / testing). Aggregate repeated
> v4.114.0's score. The blocker is test + lint hygiene:
> `make test` red with 73 failures, `make lint` red with 302
> findings (64 black + 204 ruff + 34 mypy). This release closes
> An.1, An.2, An.3 and the stale-test dockets from the v4.117.0
> flaky audit. The goal is simple: `make test` green, `make lint`
> green.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.120.0 (panel result: Option B, no v5 tag)
**Delta review:** No
**Full panel:** No (deferred to v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Move `make test` and `make lint` from red to green. Catalogue or close everything outside prior audit scope.

---

## Scope

The v4.120.0 panel's Anaconda review (NEEDS WORK @ 7.6) identified
five concrete items: An.1 (51 uncatalogued failures), An.2 (lint
debt), An.3 (test_fibonacci_run regression), An.4 (expand flaky
audit to full tests/), An.5 (decide CI self-tests).

This release closes those five items. It also rolls in test-update
carry-forwards from the v4.117.0 flaky audit (14 stale CLI tests +
4 count-drift assertions + 1 overly-specific linkage assertion) and
the three Boa / Coral documentation precision items (Bo.2, Co.1,
Cb.1 — all one-paragraph edits).

No compiler or runtime code changes. Test rewrites, lint auto-fixes,
and documentation precision only. One release, one theme.

## Phase 1 — Triage: catalogue the 51 un-audited failures

- [ ] Run full pytest with failure capture:
  ```bash
  pytest tests/ --tb=short -n auto 2>&1 | tee /tmp/v4121_failures.log
  ```
- [ ] For each FAILED test in the 51 extras, classify:
  - Stale assertion (delete / rewrite)
  - Feature gap (docket exists / open new docket)
  - Real regression (investigate)
- [ ] Extend `tests/FLAKY_AUDIT.md` (or write `tests/TEST_AUDIT_v4.121.md`) with the full 73-item catalogue. Each row: test name, category, action.
- [ ] Investigate `test_fibonacci_run` specifically — is this a known gap or a real regression?

## Phase 2 — Close the 22 stale-assertion failures (from v4.117.0 audit)

- [ ] **14 CLI tests** — rewrite `tests/cli/test_cli.py::TestArgparse*`, `TestCompile*`, `TestOptLevelFlags*` against `mapanare transpile` (the current subcommand; `compile` was renamed and deprecated)
- [ ] **2 drop-glue count assertions** — update `tests/llvm/test_drop_glue.py::TestStringDropGlue::test_returned_string` + `test_str_concat` for v4.101.0 move-semantics counts
- [ ] **1 cross-module linkage** — relax `tests/llvm/test_cross_module.py::TestPubVisibility::test_non_pub_gets_internal_linkage` to accept either `internal` or `private`
- [ ] **1 emitter hardening** — update `tests/llvm/test_emitter_hardening.py::TestEmitterOutputSuite::test_multiple_functions` for v4.108.0 StringBuilder + coroutine helpers
- [ ] **1 bounded-generic trait** — investigate `tests/semantic/test_traits.py::test_trait_with_bounded_generic_fn`; may be a real monomorphization edge case
- [ ] **3 DWARF** — either implement the `-g` deferral warning (per SPEC §21.3) or mark the tests `@pytest.mark.skip(reason="feature deferred to v5.x")`

## Phase 3 — Close the 51 un-audited failures

- [ ] Phase 1 triage output drives Phase 3 action:
  - **Stale assertions** → update tests
  - **Known gaps** → mark `@pytest.mark.skip(reason="<docket ID>")`
  - **Struct-literal syntax** (3 tests) → decision with Coral's Co.2: implement in grammar or delete tests
  - **Bootstrap verification** (5 tests touching Sh.8) → skip with reason pointing to docket
  - **CI meta-tests** (2 tests that run `ruff`/`mypy` subprocesses) → either fix the underlying lint issues (Phase 4) or skip with reason
  - **Real regressions** → fix

## Phase 4 — Close lint debt (An.2)

- [ ] `black .` — reformats all 64 files. Target: Python 3.12 compatible; leave `target-version` unset in `pyproject.toml` (continue auto-detecting)
- [ ] `ruff check --fix .` — auto-fixes ~104 of 204 errors (unused imports, import sort, f-strings)
- [ ] Manually address the remaining ~100 ruff errors:
  - E501 line-too-long (81) — wrap or disable per-line if semantically meaningful
  - E701 multiple-statements (10) — split or disable
  - E741 ambiguous-variable-name (6) — rename
- [ ] `mypy mapanare/ runtime/` — investigate 34 errors in `mapanare/lsp/*`. Options:
  - Fix type annotations in `mapanare/lsp/server.py:403`, `419`, `489`, `rename.py:85`
  - OR exclude `mapanare/lsp/` from mypy scope (it's a WIP module not in the core compilation pipeline)

## Phase 5 — Expand flaky audit (An.4)

- [ ] Re-run the 5-run pairwise-diff audit against the **full** `tests/` suite (not just 9 subdirectories)
- [ ] Update `tests/FLAKY_AUDIT.md` with the expanded scope
- [ ] Confirm: zero flaky tests across the full suite

## Phase 6 — Documentation precision (Bo.2, Co.1, Cb.1)

- [ ] **Bo.2**: add "Prerequisites for Native Mode" section to `docs/guides/getting_started.md` — explain that `mnc-stage1` must be built before `mnc run` works, with the build command and expected outcome
- [ ] **Co.1 / Cb.1**: edit README's "the compiler compiles itself" sentence. Replace with: "The compiler compiles user `.mn` programs natively via `mnc-stage1` (26/64 golden tests pass literally, 39/64 semantically; see `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`). Full self-compilation (stage1 → stage2 → stage3 fixed-point convergence) is tracked under docket Sh.8 and scheduled for v5.x."
- [ ] **SPEC §29**: add a one-paragraph "Self-hosting status" note with the same precision

## Phase 7 — LOW sweep + closeout

- [ ] `make test` — **expected to pass** after Phases 2+3+4
- [ ] `make lint` — **expected to pass** after Phase 4
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.121.0]` entry
- [ ] `SESSION_REPORT.md` written
- [ ] Carry-forward ledger updated: An.1-An.5, Bo.2, Co.1, Cb.1, the 22 v4.117.0-audit items all CLOSED

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `pytest tests/` reports 0 failures | CI logs |
| 2 | `make lint` reports 0 findings (black clean, ruff clean, mypy scope decision made) | CI logs |
| 3 | 51 un-audited failures catalogued and closed (fixed / skipped / xfail) | `tests/TEST_AUDIT_v4.121.md` or equivalent |
| 4 | 22 stale-assertion failures from v4.117.0 audit closed | per-test diff |
| 5 | `test_fibonacci_run` investigated and resolved (fixed or catalogued as docket) | commit or docket |
| 6 | Full `tests/` suite flaky audit run — 0 flaky | `tests/FLAKY_AUDIT.md` update |
| 7 | README + SPEC §29 self-hosted wording corrected | README diff |
| 8 | Getting-started guide has native-mode prerequisite section | guide diff |
| 9 | Standard closeout clean | CHANGELOG + SESSION_REPORT + VERSION bump |

---

## What this release does NOT do

- **No compiler or runtime code changes.** Every change is in `tests/`, `docs/`, or auto-formatted source files.
- **Does not fix Qs.1, Rt.1, Sh.2, Sh.8.** Those are v4.122.0+ scope.
- **Does not run a panel.** v4.121.0 is a cleanup release; the next panel is v4.130.0 after the closeout arc (v4.121.0–v4.129.0).
- **Does not add language features.** Struct-literal-syntax (Co.2) is deferred to a future release if the lead + Coral want it; this release only deletes the tests or marks them skip.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `make lint` still red after auto-fix | low | medium | Manual pass on the ~100 non-auto-fixable errors is bounded; ~4 hours work |
| `test_fibonacci_run` is a real regression that takes a release to fix | medium | high | If investigation reveals real compiler regression, split into v4.121.0 + v4.122.0 |
| `mapanare/lsp/` mypy errors are real API drift, not just annotations | low | medium | Either fix or exclude from scope; both are acceptable for a WIP module |
| Expanding flaky audit to full suite reveals real flakes | low | medium | Unlikely given 5 releases of stability; but the audit would catch them |
| Struct-literal-syntax 3 tests + decision blocks closeout | medium | low | Default action: skip with reason, defer decision to v4.122.0+ |

---

## After v4.121.0

- **v4.122.0** — Qs.1 fix + DWARF warning implementation
- **v4.123.0** — Rt.1 (boxed-enum unbox where payload fits in pointer)
- **v4.124.0** — Sh.8 (self-hosted semantic.mn constructor registration)
- **v4.125.0** — benchmark refresh + updated panel-prep docs
- **v4.126.0** — dead-code sweep (optimizer.py, TBAA decision)
- **v4.127.0 – v4.129.0** — buffer for Sh.2 / polish
- **v4.130.0** — v5 gate attempt 3 (panel)

The cadence holds. Every release: one PLAN, one PROMPT, one SESSION_REPORT, one CHANGELOG entry, one commit stack.
