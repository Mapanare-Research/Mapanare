# v5.13.1 — `@test` runtime fix (patch)

**Status:** SHIPPED (impl complete; awaiting `/bump-version` + tag).
**Theme:** patch — fix two latent bugs that made `@test` (a SPEC §6.4
"shipping" feature) unusable on either compiler, plus the smoke test
that should have prevented them.

---

## Summary

Pre-v5.13.1, the simplest possible `@test` fixture failed in both
runners:

```
$ python3 -m mapanare test fixture.mn
  FAIL test_passes — clang compile error: undefined reference to `main`

$ ./mnc-stage1 test fixture.mn
  FAIL fixture.mn — clang failed: use of undefined value '@__mn_assert_fail'
```

Both compilers parsed and discovered `@test` correctly; both broke
during the **runtime path**. v5.13.1 closes both bugs, plumbs the
optional `assert COND, "msg"` user-message through to runtime
output (the message was being parsed and silently dropped on both
sides), and adds `tests/test_at_test_runtime.py` so regressions
trip CI.

## Items shipped

### At.1 — Python bootstrap (`mapanare test`)

- `mapanare/test_runner.py::run_test_file` rewritten as per-test
  compile+run. The lowered IR for a `@test`-only file has no
  `main`, so clang/ld blew up at link time with "undefined
  reference to `main`". Each test now gets its own binary built
  by appending a synthesized `define i32 @main() { call void
  @<test>(); ret i32 0 }` fragment, driven by the new
  `_emit_test_main` / `_run_one_test` helpers.
- `mapanare/emit_llvm_text.py::_do_assert` extended to call
  `__mn_str_println` on the user-supplied message Value when one
  exists. Pre-v5.13.1 this only printed `"assertion failed at
  file:line"`, dropping the message that `lower._lower_assert`
  had carefully captured into the MIR Assert node.
- `mapanare/emit_llvm_text.py::_compute_pure_fns` taught about
  `Assert` instructions. Latent for years: assert lowers to
  `printf` + `@exit(1)` — observable side effects — but the pure-
  function classifier only looked at `Call` instructions. So a
  function whose body was just `assert ...` was tagged
  `memory(none) willreturn`, which let -O2's IPO happily delete
  the call from `main`. Latent because no `@test` runner ever
  called an assert-bearing fn until At.1 wired it up.

### At.2 — Native runner (`mnc-stage1 test`)

- `runtime/native/mapanare_core.{c,h}` — new `__mn_assert_fail`
  C function. Modeled on `__mn_panic`: prints `assertion
  failed[: <message>]` to stderr and `exit(1)`s. Pre-v5.13.1 the
  symbol was emitted by every lowered `assert` in self-host code
  but was never defined in C — the only reason `mnc-stage1` itself
  links is that nothing in the compiler's own source uses
  `assert`.
- `mapanare/self/emit_llvm.mn::declare_all_runtime` — added
  `declare void @__mn_assert_fail({ptr, i64})`. Without it the
  emitted IR died at clang IR-parse with "use of undefined value
  '@__mn_assert_fail'" before reaching the link step. Mirrored
  into `mnc_all.mn` via `scripts/concat_self.py`.
- `mapanare/self/lower.mn::lower_assert` — pass the
  `Option<String>` user message through to the
  `__mn_assert_fail` call instead of the hardcoded `"assertion
  failed"` literal. The `match Some(m) / _` form keeps the empty-
  message default when no message was given.
- `mapanare/self/main.mn::run_test` — rewritten as per-test
  compile+run with three new helpers:
  - `_trim_line`: manual whitespace strip (lower.mn doesn't yet
    translate `.trim()` to `__mn_str_trim`; mirrors the existing
    `ws_trim` in emit_llvm.mn).
  - `discover_test_names`: source-text scan for `@test` followed
    by `fn NAME` (or `pub fn NAME`). Originally written using
    `source.split("\n")`, which returns a List of correct length
    but with empty entries when the source string is a function
    parameter — suspect string-ownership bug latent because no
    other call site in the compiler splits a parameter String.
    Routed around with a manual character-by-character `substr`
    scan (filed for v5.14.x triage; not blocking v5.13.1).
  - `build_test_main_ir` / `run_one_test`: per-test mn_main
    synthesis. The C wrapper (`mn_user_main.c`) calls `mn_main`,
    so we synthesize a fresh `mn_main` per test that calls one
    `@test` function and returns 0. Per-test isolation = an
    `__mn_assert_fail` exit(1) reports as that one test's
    failure instead of taking down the whole file.

### At.3 — smoke test

- `tests/fixtures/at_test_smoke.mn` — 3-test fixture:
  passing assert, passing string equality, failing assert with a
  custom message.
- `tests/test_at_test_runtime.py` — three pytest functions:
  fixture sanity, Python runner end-to-end, native runner end-
  to-end. Both runner tests assert that PASS, FAIL, all three
  test names, and the failing test's custom message all appear
  in output, and that the runner exits non-zero overall.
  Native test skips on Windows (the runner shells out to gcc
  via /tmp paths — POSIX-only for this release; Windows path
  staged for v5.18.0's Mc.4 `mnc check`).

### At.4 — CI wiring

- No new workflow changes needed: `.github/workflows/ci.yml::ci`
  already runs `pytest tests/`, which auto-discovers
  `test_at_test_runtime.py`. Verified locally; CI will pick up
  the new test on push.

### At.5 — docs

- `docs/SPEC.md` §6.4 — extended `@test` decorator entry with
  invocation syntax (Python + native), per-test isolation
  semantics, message form, and the v5.13.1 stability marker
  pointing at the smoke test.

## Reproductions (Phase 0)

Both audit failures reproduced verbatim against v5.13.0 HEAD on
2026-04-29:

| Compiler | Failure shape |
|---|---|
| Python `mapanare test` | All 3 tests `FAIL` with `clang compile error: ld: undefined reference to 'main'`. Exit 0 (suite reported failures but exit 1 path held). |
| Native `mnc-stage1 test` | Single `FAIL <file>` line. clang error: `use of undefined value '@__mn_assert_fail'` at IR-parse. |

After fix:

| Compiler | Output |
|---|---|
| Python | `2 passed, 1 failed (3 total)` with `assertion failed at at_test_smoke:13: this should fail`. Exit 1. |
| Native | `result: 2 passed, 1 failed (3 total)` with `assertion failed: this should fail`. Exit 1. |

## Validation

- `tests/test_at_test_runtime.py` — 3/3 pass locally
  (`test_fixture_present`, `test_python_bootstrap_at_test_runtime`,
  `test_native_at_test_runtime`)
- Goldens: **66/66 preserved** (`scripts/test_native.py
  --stage1 mapanare/self/mnc-stage1`)
- Strict 3-stage fixed point: **preserved** — stage2.ll ==
  stage3.ll, 228,244 lines, 0 diff (was 226,603 lines at
  v5.13.0; +1,641 lines from the new lower_assert match arm,
  emit_llvm.mn declare, main.mn helpers, and the rebuilt
  emit_llvm_text Assert-pure-classifier stanza)
- `mnc fmt --check tests/golden/ mapanare/self/` — exit 0 (after
  one auto-format pass on the regenerated `mnc_all.mn`)
- `make lint` — clean (ruff + black + mypy)

## Out of scope (deferred)

The plan's "do not" list held:

- Test discovery across directory trees (`mnc test ./tests/`) — later
- Parallel test execution — later
- TAP / JSON / JUnit output — later
- Test fixtures + setup/teardown — later
- Subtests — later
- Test runner unification (Python + native sharing one driver) —
  separate future hardening release; do not rebundle into a patch

Drive-by findings filed for later releases:

- **String.split() returns empty strings when invoked on a
  function-parameter String** — reproduced inside
  `mnc-stage1`'s own runtime context but works fine in user
  programs. Worked around in `discover_test_names` via a manual
  `substr` scan. Suspect string-ownership / lifetime bug;
  candidate for v5.14.x or v5.15.x triage. No user-facing
  impact found beyond this one call site.
- **`else if` chained syntax rejected by the self-host parser**
  in some contexts (line:col of the `if` keyword raised
  "Unexpected 'if' — expected ';', '}', newline"). Worked around
  in `discover_test_names` with the consumed-flag pattern. The
  Python bootstrap accepts the same construct.
- **`.trim()` does not dispatch to `__mn_str_trim`** in the
  self-host lower.mn (Call(name="trim") emitted instead). Already
  documented inline at `emit_llvm.mn::ws_trim`; new
  `main.mn::_trim_line` helper duplicates the shape.

## Files touched

- `runtime/native/mapanare_core.c` — `+13 -0` (new function)
- `runtime/native/mapanare_core.h` — `+4 -0` (new declaration)
- `mapanare/emit_llvm_text.py` — `+25 -3` (Assert message
  surfacing + pure-fn classifier fix)
- `mapanare/test_runner.py` — `+106 -86` (per-test compile+run
  rewrite; net + because of new helpers)
- `mapanare/self/emit_llvm.mn` — `+7 -0` (extern declare)
- `mapanare/self/lower.mn` — `+8 -1` (message plumbing through
  to `__mn_assert_fail`)
- `mapanare/self/main.mn` — `+165 -38` (discover/build/run
  helpers + per-test run_test rewrite)
- `mapanare/self/mnc_all.mn` — auto-regenerated by
  `scripts/concat_self.py`
- `tests/fixtures/at_test_smoke.mn` — `+13 -0` (new fixture)
- `tests/test_at_test_runtime.py` — `+85 -0` (new smoke test)
- `docs/SPEC.md` — `+9 -1` (decorator entry expansion)

## Ready-to-ship checklist

- [x] Phase 0 reproductions documented (both failure shapes)
- [x] `mapanare test` runs the fixture, reports 1 PASS + 2 PASS +
      1 FAIL, surfaces custom message, exits 1
- [x] `mnc-stage1 test` same
- [x] `tests/test_at_test_runtime.py` green locally
- [x] CI green expected on push (pytest auto-discovers)
- [x] SPEC.md §6.4 polished
- [x] Goldens 66/66 (no regression)
- [x] Strict 3-stage fixed point preserved
- [x] `make lint` clean
- [ ] `/bump-version` to bump VERSION → 5.13.1, update README +
      CHANGELOG (separate step, awaiting user)
- [ ] Tag (separate step, lead's call per persistent guidance)
