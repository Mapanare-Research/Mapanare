# Mapanare v4.133.0 — An.1 test hygiene reduction

> **Test hygiene release.** 38 deterministic pytest failures outside
> the bootstrap subset remain as carry-forward from the v4.120.0 panel
> (Anaconda NEEDS WORK 7.6). Three flaky audits (v4.117.0, v4.125.0,
> v4.130.0) confirmed they are deterministic — not flaky, just
> **unfixed**. v4.121.0 closed 22 audit-subset failures. v4.133.0
> closes the out-of-subset bucket that Anaconda originally flagged.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.132.0
**Estimated work:** 1 sprint (no compiler changes; per-family triage + fix)
**Theme:** `make test` becomes green (or as close as physically possible without touching the compiler).

---

## Why v4.133.0 exists

The v4.120.0 panel returned 8.21/10 with **Anaconda NEEDS WORK** on
CI/testing. Anaconda's core finding was that the v4.117.0 audit's 22
deterministic failures were a SUBSET (9 subdirectories, 1,501 tests);
the full `pytest tests/` run showed 73 failures. v4.121.0 closed 22.
Three subsequent flaky audits confirmed the remaining 38+ are
deterministic. **The reason the panel didn't clear 9.0 at v4.120.0
was Anaconda. If An.1 is not closed to single-digits, v4.136.0 won't
clear 9.0 either.**

## Evidence — the 38 failures categorized

Per v4.130.0 FLAKY_AUDIT + v4.131.0 post-fix pytest run
(`/tmp/v4131_failures.txt`):

| Family | Count | Source of failure | Triage |
|---|---|---|---|
| test_runner CLI legacy | 7 | `tests/test_runner/test_test_runner.py` | pre-v3.x test runner CLI; API changed; rewrite tests |
| db native env | 6 | `tests/native/test_db_sqlite.py`, `test_db_dlopen.py` | need sqlite3/pq shared libs present; fail gracefully + skip |
| filesystem env | 5 | `tests/native/test_fs_extended.py` | realpath/tmpfile behave differently in WSL; skip or fix |
| sanitizer env | 3 | `tests/native/test_c_hardening.py::TestCRuntimeASan/TSan/Plain` | ASan/TSan toolchain-dependent; condition on environment |
| e2e LLVM stale | 5 | `tests/e2e/test_e2e_llvm.py` | stale expected IR; regenerate reference |
| doc links stale | 3 | `tests/test_doc_links.py` | relative links to deleted/moved files; fix or update tests |
| CI env | 3 | `tests/test_ci.py::TestToolsRunLocally::test_{black,ruff,mypy}_check_passes` | require clean `make lint`; tied to An.2 |
| bind | 1 | `tests/bind/test_python_binding.py::test_struct_with_string_field` | pre-existing UTF-8 binding issue |
| memory stress | 1 | `tests/native/test_memory_stress.py` | environmental memory-bound test |
| runtime version | 1 | `tests/runtime/test_user_agent.py` | version string sync (cosmetic) |
| SPEC | 3 | `tests/spec/test_spec_compliance.py::test_arithmetic_compiles`, `tests/spec/test_spec_crossref.py::test_status_is_final`, `test_version_is_1_0_0` | stale SPEC header version or status |
| TOTAL | **38** | | |

Per-family triage strategy:

- **Real bugs** (need code fix): bind UTF-8 (1), e2e LLVM stale (5 — regenerate), SPEC stale (3 — header was updated in v4.129.0 to 4.129.0, tests expect 1.0.0) → **9 closures**
- **Environmental** (condition/skip): db native (6), filesystem (5), sanitizer (3), memory stress (1) → **15 closures via conditional skip with clear reason + CI lane tag**
- **Test rewrites** (code is right, test is wrong): test_runner CLI (7), doc links (3), runtime version (1) → **11 closures**
- **Gated on An.2**: CI env (3) → **3 closures IF An.2 also lands this release; otherwise defer to v4.134.0+**

## Phase 1 — Classify + plan per-family

- [ ] Inspect each failure, confirm it matches the triage above
- [ ] For "real bug" family: identify the fix (compiler unchanged — these are bindings / test-reference updates / SPEC test expectations)
- [ ] For "environmental" family: decide skip-condition vs env fix (prefer skip with clear reason — we're not in the business of making every environment pass)
- [ ] For "test rewrites" family: rewrite tests against current API
- [ ] Document the v4.120.0 → v4.133.0 An.1 delta in `docs/roadmap/v4/v4.133.0/AN1_REDUCTION.md`

## Phase 2 — Implement per-family

Work in independent commits per family so reverts are surgical:

- [ ] **Real bugs (9 tests)**:
  - bind UTF-8: either fix the `_MnString.to_str()` to handle non-UTF-8 gracefully or the producer to emit valid UTF-8
  - e2e LLVM stale: run tests with `--bless` if harness supports it; otherwise regenerate expected files
  - SPEC header: `test_spec_crossref.py` reads `docs/SPEC.md` header; align expected to current header
- [ ] **Environmental (15 tests)**:
  - db native: `pytest.importorskip` on dlopen of sqlite3/pq; skip with reason="sqlite3 not available" where indicated
  - filesystem: detect WSL realpath behavior, skip affected assertions
  - sanitizer: only run when `CC=clang` and `-fsanitize=address` is supported
  - memory stress: mark as `@pytest.mark.slow` and exclude from default lane
- [ ] **Test rewrites (11 tests)**:
  - test_runner CLI: current CLI is `mapanare test`, not the deprecated runner; rewrite tests against current
  - doc links: update test to permit the 3 known-stale files or update the files
  - runtime version: keep test but update reference file

## Phase 3 — Verification

- [ ] `python3 -m pytest tests/ --ignore=tests/bootstrap -q` — target ≤ 15 failures
- [ ] If An.2 is bundled: `make lint` green → CI env family closes 3 more (≤ 12 failures)
- [ ] No goldens regress (still 53+/65 through mnc-stage1)
- [ ] Sanitizer sweeps unchanged from v4.132.0 (this release touches no compiler code)
- [ ] Bootstrap unchanged (still 212 passing)

## Phase 4 — Closeout

- [ ] `SESSION_REPORT.md` with per-family close counts
- [ ] `CHANGELOG.md [4.133.0]` entry
- [ ] Roadmap status updates
- [ ] Bump to 4.134.0

---

## Exit criteria

| # | Check | Target | Stretch | Downside |
|---|---|---|---|---|
| 1 | An.1 failures | ≤ 15 | ≤ 10 | > 20 → scope shortfall, v4.133.1 continues |
| 2 | Per-family close counts documented | all 10 families | — | mandatory |
| 3 | No compiler code touched | yes | — | if touched → different release |
| 4 | No golden regressions | 53/65 | — | mandatory |
| 5 | No sanitizer regression | same as v4.132.0 | — | mandatory |
| 6 | Bootstrap subset unchanged | 212/13 | — | mandatory |

---

## What this release does NOT do

- Touch the compiler (no `mapanare/` or `runtime/` code changes)
- Rewrite the entire test suite — only the failing tests in An.1 families
- Make every environment pass (WSL-specific, container-specific, etc. — skip with reason)
- Close An.2 (lint debt) unless bundled (decision in Phase 1)
- Panel anything

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| A "real bug" fix requires compiler change | low | high | Descope that test family; document as v4.134.0+ item |
| Skipping tests masks real regressions | medium | medium | Every skip has `reason=` with docket tag; CI lane + full lane separated |
| Test rewrites don't actually match new API | low | medium | Run each family in isolation to verify |
| An.2 bundling blows scope | medium | medium | Phase 1 decides; default is "defer to v4.134.0" |

---

## After v4.133.0

- v4.134.0 — Sh.11 investigation + fix (fixed-point blocker)
- v4.135.0 — Pre-panel refresh (flaky audit #4, fresh sanitizer, benchmarks)
- v4.136.0 — THE PANEL (v5 gate attempt 3)

If An.1 lands ≤ 10 and An.2 is bundled: the panel's biggest historical
blocker is gone. Combined with v4.131.0's Sh.2 close and v4.134.0's
Sh.11 close, the panel aggregate should clear 9.0.
