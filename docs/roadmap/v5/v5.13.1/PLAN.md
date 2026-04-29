# v5.13.1 — `@test` runtime fix (patch)

**Status:** PLANNING
**Breaking:** No. Pure bug fix; `@test` is currently fully broken
on the simplest possible test case in both compilers, so this can
only improve from "doesn't work" to "works."
**Prerequisite:** v5.13.0 shipped (`mnc fmt`). Independent of the
Te.* arc — patch can ship at any point after v5.13.0.
**Estimated effort:** 3–6h, single session.

---

## Why this exists

The v5.13.0-prep audit on 2026-04-28 verified that `@test`
**discovery** works in both the Python bootstrap and native
`mnc-stage1` (the parser + decorator handler find every
`@test`-marked function correctly), but the **runtime path** is
broken on both sides:

```bash
$ python3 -m mapanare test test_at_test.mn
  test_at_test.mn
    FAIL  test_passes (0.0ms)
           clang compile error: /usr/bin/ld: ... undefined reference to `main'

$ mnc-stage1 test test_at_test.mn
FAIL test_at_test.mn
error: clang failed:
  /tmp/mnc_test.ll:204:13: error: use of undefined value '@__mn_assert_fail'
```

This means `@test` is **specified, parsed, and discovered**, but
nobody can actually run a test. SPEC §6.4 lists `@test` as a
built-in decorator. The discrepancy between spec promise and
runtime reality has gone unnoticed long enough that there's
clearly no CI coverage for it. v5.13.1 closes both bugs and adds
the smoke test that should have prevented them.

This is a patch release because:
- It's strictly bug-fix scope; no design decisions
- `mnc fmt` (v5.13.0) and `@test` runtime are unrelated and
  shouldn't share a release window
- Patch releases ship fast — users with broken `@test` shouldn't
  wait for v5.14.0 (Te.1) to ship
- It makes future SPEC audits more credible (we say "@test works"
  and demonstrate it works)

---

## Goal

1. `python3 -m mapanare test foo.mn` runs `@test` functions and
   reports per-test pass/fail correctly, including assertions
   that pass and assertions that fail with custom messages.
2. `mnc-stage1 test foo.mn` does the same.
3. Both compilers ship a CI smoke test that compiles + runs a
   3-function `@test` file (passing assert, failing assert with
   message, equality assert) and validates the output.
4. The smoke test is robust enough to catch regression: any
   future change that re-breaks `@test` runtime trips CI.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **At.1** | HIGH | Python bootstrap: `mapanare test` per-test compilation must wrap each `@test` function in a synthetic `main` that calls it, captures the assertion result, and exits with the right code. Currently the linker errors on missing `main`. | 1–2h |
| **At.2** | HIGH | Native `mnc-stage1`: the test runner emits `call void @__mn_assert_fail(...)` but never declares the extern. Add the `declare void @__mn_assert_fail({ptr, i64})` line to the prelude of generated test IR (or, equivalently, ensure the runtime `.c` file is linked into the test binary). | 1–1.5h |
| **At.3** | HIGH | New test: `tests/test_at_test_runtime.py`. Compiles a fixture `tests/fixtures/at_test_smoke.mn` with one passing assert, one failing assert with a message, and one equality assert. Runs through both `mapanare test` and `mnc-stage1 test`. Asserts: passing test prints "pass", failing test prints "fail" + the custom message, exit codes match expectations. | 1–1.5h |
| **At.4** | MEDIUM | Wire At.3 into CI: `.github/workflows/ci.yml` runs `pytest tests/test_at_test_runtime.py` in the existing `ci` job. No new matrix entry. | 0.5h |
| **At.5** | LOW | SPEC.md §6.4: small note that `@test` is a stable feature (currently it reads as if it might not be), and a one-liner usage example. | 0.5h |

---

## Phase plan

**Phase 0 — Reproduce both failures.** Before fixing anything,
re-run the v5.13.0-prep audit's `tests/fixtures/at_test_smoke.mn`
through both compilers; confirm both still fail with the documented
error shapes (linker error in Python, `__mn_assert_fail` undefined
in native). If either has silently been fixed since the audit, the
scope shrinks accordingly.

**Phase 1 — Python bootstrap (At.1).** Locate the per-test
compilation path in `mapanare/cli.py` (subcommand `test`). The
fix is one of:

- (a) Synthesize a `main` that calls the `@test` function, around
  the lowered IR before clang invocation.
- (b) Compile the entire module (with all tests) into one binary
  with a synthetic `main` that dispatches on argv to a specific
  test by name, then re-invoke per-test by name to capture
  per-test output.

Recommendation: **(a)** for v5.13.1 (simpler, matches `go test`'s
per-test compilation model). (b) is more efficient but bigger
change; defer to a future hardening release.

**Phase 2 — Native runner (At.2).** Locate the test-IR generator
in `mapanare/self/main.mn` (the `test` subcommand handler). The
generator builds an IR module per test that calls
`@__mn_assert_fail` from the runtime, but never emits the
`declare void @__mn_assert_fail(...)` line in the generated
module's prelude. Two options:

- (a) Always emit the extern declaration in the generated test IR
- (b) Always link `runtime/native/assert.c` (or wherever
  `__mn_assert_fail` lives) into the test binary

Recommendation: **(a)** — the extern declaration is what every
other `__mn_*` builtin uses; the missing one was an oversight, not
a design choice. Look at how `__mn_str_println` is declared in the
same file for pattern.

**Phase 3 — Smoke test (At.3 + At.4).** New test file. Compile +
run the fixture through both compilers; assert the output matches
expected. CI integration last so a green local run gates the CI
addition.

**Phase 4 — Docs (At.5).** SPEC.md polish. Update CLAUDE.md if the
"Skills" table or any roadmap one-liner needs touching.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Phase 1's "synthesize main per test" approach breaks for tests that import other modules | MEDIUM | Reproduce a multi-file test fixture early in Phase 1. If the per-test main approach can't resolve cross-module imports, fall back to whole-module compilation with argv dispatch. |
| `__mn_assert_fail` extern signature wrong (memory issues at runtime) | LOW | Cross-check against the C-side definition in `runtime/native/`. The native test-IR generator has used the wrong signature before — guard with a smoke test that triggers an actual assertion failure. |
| CI smoke test flaky in WSL/Windows where clang is bundled | LOW | Use the same clang invocation path as the existing `ci` job so any toolchain mismatch is shared, not new. |
| Fix masks a deeper issue with how test-mode compilation differs from normal compilation | MEDIUM | Document in SESSION_REPORT exactly which IR-generation path differs; if there's a substantive divergence, file a follow-up to unify (post-v5.13.1). |

---

## Out of scope (deferred)

- Test discovery across a directory tree (`mnc test ./tests/`) —
  later release; current scope is single-file
- Parallel test execution — later
- Test output formatting (TAP, JSON, JUnit XML) — later
- Test fixtures, setup/teardown decorators — later
- Property-based testing infrastructure — out of v5.x scope
- Subtests (`t.Run`-style nested cases) — later

---

## Success criteria

- `python3 -m mapanare test tests/fixtures/at_test_smoke.mn` runs
  three tests, reports 1 pass + 2 fail (correctly identifying
  which is which), exits with non-zero overall
- `mnc-stage1 test tests/fixtures/at_test_smoke.mn` produces
  identical pass/fail/exit-code output
- `pytest tests/test_at_test_runtime.py` is green locally and in
  CI
- Failing test's assertion message ("this should fail") appears in
  the failure output
- No regression on `mnc fmt` (v5.13.0): `mnc fmt --check` still
  exits 0 on the corpus
- `make lint` clean
- SPEC.md §6.4 reflects that `@test` is shipping-tested
