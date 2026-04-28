# Panel v5.2.0 -- Anaconda (CI / Testing)

**Score: 8.9 / 10**
**Grade: MEETS**
**Prior (v4.154.0): 9.4 / 10 EXCEEDS**
**Delta vs v4.154.0: -0.5**

---

## 0. Executive summary

At v4.154.0 I scored 9.4 EXCEEDS and carried forward seven LOW items:
An.9 (E1 IR-shape tests), An.10 (test-count script), coverage gate,
Windows CI, ruff expansion, randomized-order flaky, and bootstrap 13
failures. The v5.0.1-v5.2.0 arc (12 releases) closed An.9 and An.10 at
v5.0.6, added 136 net new tests (5,309 to 5,445), delivered a substantial
51-test registry suite for the first user-facing feature since v5.0.0,
and added 31 precision tests across 4 new test files for the In.1, Ea.1,
Perf.1, and Cb.6 work.

**However, the arc also produced two genuine quality regressions that I
cannot overlook:**

1. **Lint process failure.** The v5.2.0 package registry code was
   committed without running `black` or `ruff`. Four files have
   formatting violations. Nine ruff errors (5 unused imports, 1 line
   too long, 1 import sort, 2 others). Two of the eight CI gates
   (`test_black_check_passes`, `test_ruff_check_passes`) are red at
   HEAD. This is the first time since v4.133.0 (An.1 closeout) that
   lint gates have been red on the dev branch. For a project that
   established "all 8 CI gates green" as a baseline at v4.117.0 and
   maintained it for 37 consecutive releases, shipping code that fails
   the lint gates is a process failure.

2. **Fixed-point regression.** The v5.1.2 In.1 inliner re-enable broke
   the self-compilation fixed-point. stage2.ll fails `llvm-as` with
   `undefined value '%_inl0_6_t4'`. Prior state: NEAR FIXED POINT at
   v4.154.0 (4 diff, version metadata). Current state: BROKEN. This is
   the most significant quality regression since the v4.134.0 strict
   fixed-point was first achieved. The In.1 rename fix passed all 54
   golden tests and its 4 dedicated rename tests, but the
   self-compilation path exposes more complex inlining patterns that the
   rename logic does not handle. This is exactly the failure mode I would
   have flagged at v5.1.2 had I reviewed it: **unit tests are necessary
   but not sufficient for optimizer passes** (the v5.1.2 SESSION_REPORT
   itself states this as "Key learning #1" for Li.1 -- the same lesson
   was not applied to In.1).

I am grading **8.9 MEETS**, a -0.5 delta from v4.154.0. The regression
from EXCEEDS to MEETS is driven by: (a) 2 red lint gates at HEAD --
the first red gates in 37 releases, (b) fixed-point regression from
NEAR to BROKEN, and (c) an LLVM-version-sensitive test (An.9) that
is now failing on LLVM 18. The positive work (51 registry tests, An.9/
An.10 closures, 31 optimizer precision tests, 54/66 golden stability)
prevents the score from falling further. The arc maintained test
discipline on every release except the final one (v5.2.0), which was
the only release that introduced new source code (the registry client)
and is the one that broke the lint baseline.

---

## 1. Carry-forward closure assessment

### 1.1 An.9 CLOSED (v5.0.6) -- E1 unified-return IR-shape tests

`tests/llvm/test_unified_return_shape.py` (132 lines, 3 tests) added
at v5.0.6. I reviewed the full file. The three tests are:

| Test | What it gates | Status |
|------|---------------|--------|
| `test_area_has_single_switch_pre_opt` | E1 invariant: `@area` has exactly 1 switch | PASS |
| `test_make_shape_uses_sret` | Rt.1/Cb.15 sret pointer gate | PASS |
| `test_post_opt_single_switch_in_hot_loop` | Post-`opt -O2`: `@main` has 1 switch | **FAIL** |

The third test fails on LLVM 18.1.3: `opt -O2` produces 0 switches
in the hot loop (expected 1). LLVM 18's SimplifyCFG is more aggressive
than LLVM 17 -- it folds the dispatch switch into predicated selects,
eliminating the switch entirely. This is a better optimization than
the E1 two-to-one fold; the test's assertion is LLVM-version-sensitive.

**Assessment:** The first two tests are the structurally important gates
-- they verify the pre-optimization IR shape that enables E1. The third
test is a nice-to-have that breaks on newer LLVM versions. This is an
inherent risk of asserting post-optimization IR shapes, which I should
have anticipated when I proposed An.9. The test should be updated to
accept 0 or 1 switches (both represent successful optimization), or
the assertion should be relaxed to `switch_count <= 1`. As written, it
is a deterministic failure on LLVM 18 and will fail in CI (which uses
LLVM 18).

**Docket: An.9r (LOW).** Update the LLVM 18 switch-count assertion in
`test_post_opt_single_switch_in_hot_loop` to accept 0 (LLVM 18 select
conversion) or 1 (LLVM 17 switch fold). The pre-opt tests are correct.

### 1.2 An.10 CLOSED (v5.0.6) -- deterministic test-count script

`scripts/count_tests.py` (82 lines) + `make count-tests` target. I
reviewed the full script. It uses a clean regex (`^\s*def\s+test_\w+\s*\(`)
to count `def test_*` declarations, avoiding parametrize/fixture
expansion ambiguity. Supports `--by-dir` breakdown and `--path` scoping.
Current count: **4,284 `def test_*` declarations**, expanding to ~5,445
pytest-collected (parametrization ratio: 1.27x).

This is exactly what I asked for. The script is deterministic, its
output is reproducible, and the delta from v4.154.0 (which I estimated
at ~4,200 based on rough regression from 5,309 collected) is consistent.
Good closure.

### 1.3 Remaining carry-forwards (unchanged)

| Item | Status |
|------|--------|
| Coverage gate -> enforcing | Still informational (`\|\| true` at ci.yml:165). Now 49 releases deferred. |
| Windows CI lane | Still absent. Windows native binary shipped (v5.0.1) but no Windows CI runner. |
| Ruff ruleset expansion | No new rules added (still E, F, W, I). |
| Randomized-order flaky | Not attempted. |
| Bootstrap 13 failures | Not re-verified this arc. Expected stable. |

---

## 2. Test count progression

### 2.1 Per-release arc reconstruction

| Release | What | Test count | Delta | Source |
|---------|------|---:|---:|---|
| v4.154.0 | perf panel | 5,309 | -- | BASELINE |
| v5.0.4 | Cb.15 sret | ~5,309 | 0 | No test files added |
| v5.0.5 | Gr.2+Cb.9a | ~5,321 | +12 | 12 parser tests |
| v5.0.6 | 8-item closeout | ~5,330 | +9 | Cb.6-test (2), An.9 (3), An.10 counter |
| v5.1.0 | Perf.1 inline list | ~5,340 | +10 | test_list_inline (10) |
| v5.1.1 | Ge.1r zero-init | ~5,340 | 0 | No new tests |
| v5.1.2 | In.1+Ea.1+Bn.2/4 | ~5,354 | +14 | In.1 (4), Ea.1 (7), Li.1 (3) |
| v5.1.3 | Own.1 P1 | ~5,354 | 0 | No new tests |
| v5.1.4 | Perf.2 lazy coro | ~5,354 | 0 | No new tests |
| v5.2.0 | Registry MVP | **5,445** | +91 | 51 registry + VERSION rebuild |
| **Total** | | **5,445** | **+136** | |

The v5.2.0 registry release accounts for 91 of the 136-test delta.
The 51 registry tests expand to more pytest-collected items due to
parametrization and fixture-generated variants. The remaining 40 tests
are from the non-registry work (Perf.1, In.1, Ea.1, An.9, Cb.6-test,
Gr.2 parser tests).

### 2.2 An.10 verification

`scripts/count_tests.py` reports 4,284 `def test_*` declarations.
The MEASUREMENTS.md reports the same number. The 5,445 pytest-collected
count aligns with parametrized expansion. This is now a reproducible,
deterministic baseline. The per-release bookkeeping drift I flagged at
v4.144.0 and v4.154.0 is resolved by construction: future releases can
run `make count-tests` for an authoritative number.

---

## 3. New test suites -- detailed review

### 3.1 Registry tests (51 tests, v5.2.0)

Three files in `tests/registry/`:

| File | Tests | Lines | What |
|------|------:|------:|------|
| `test_mapanare_toml_parsing.py` | 17 | 191 | Manifest parse, serialize, round-trip, error paths |
| `test_lockfile.py` | 14 | 140 | LockFile round-trip, disk I/O, determinism, error paths |
| `test_publish_install_roundtrip.py` | 20 | 212 | Semver resolution, tarball creation, integrity, install-all |

**Coverage audit (manifest):**

| Path | Positive | Negative |
|------|----------|----------|
| Minimal manifest | `test_minimal_manifest` | -- |
| Full manifest | `test_full_manifest` | -- |
| Inline table dep | `test_inline_table_dependency` | -- |
| Missing name | -- | `test_missing_name_raises` |
| Missing version | -- | `test_missing_version_raises` |
| Empty deps | `test_empty_dependencies` | -- |
| Dev deps | `test_dev_dependencies` | -- |
| Comments | `test_line_comments_ignored` | -- |
| Round-trip minimal | `test_round_trip_minimal` | -- |
| Round-trip w/ repo | `test_round_trip_with_repository` | -- |
| Round-trip w/ deps | `test_round_trip_with_dependencies` | -- |
| Round-trip w/ git | `test_round_trip_with_git_dependency` | -- |
| Dependency.from_dict string | `test_string_value` | -- |
| Dependency.from_dict dict | `test_dict_value` | -- |
| Dependency.from_dict default | `test_dict_default_version` | -- |
| Dependency.from_dict invalid | -- | `test_invalid_type_raises` |

4 error-path tests out of 17 (23.5% negative ratio) is appropriate
for a parsing module.

**Coverage audit (lockfile):**

7 serialization/parse tests + 2 find tests + 1 error test + 1
determinism test + 1 JSON structure test + 3 disk I/O tests (load
missing, save+load, overwrite). Good coverage for the lockfile
surface. The `test_deterministic_output` test is important: lockfiles
must be deterministic for reproducible builds.

**Coverage audit (semver/install):**

5 `_version_tuple` tests (basic, two parts, prerelease, build,
zero). 11 `_satisfies_constraint` tests covering *, exact, ^, ~,
>=, <, and compound constraints. 4 `_resolve_best_local` tests.
2 tarball tests (creation, mn_modules exclusion). 2 integrity tests.
1 install-all test with mock. 2 URL assertion tests.

The semver coverage is thorough. Caret-zero-major (`^0.x`) correctly
tests the minor-version ceiling rule. Compound constraint tests
exercise the comma-separated AND logic. The tarball exclusion test
verifies `mn_modules/` is omitted (supply-chain correctness).

**What concerns me:**

1. **No network-level tests.** The `install_package` and `publish`
   functions call `urllib.request.urlopen` and `urllib.request.Request`
   against `mapanare.dev`. The test suite uses `@patch` mocks for the
   install-all path but does not test the actual HTTP request/response
   cycle, even with a local stub server. This is acceptable for MVP
   (network tests are flaky by nature), but the mock coverage should
   expand as the registry matures.

2. **The test files have lint violations.** This is the process failure
   discussed in S0.

**Verdict: good first-pass coverage for a registry MVP.** The
positive/negative ratio is balanced, round-trip tests ensure
serialization fidelity, and the semver constraint logic is thoroughly
exercised. The mock isolation for `install_all` is correct.

### 3.2 List inline tests (10 tests, v5.1.0)

`tests/llvm/test_list_inline.py` (171 lines, 10 tests). Five classes:

| Class | Tests | What |
|-------|------:|------|
| `TestListInlineGet` | 4 | GEP presence, bounds check, float path, push+get roundtrip |
| `TestListInlineSet` | 2 | GEP store, bounds check |
| `TestListSlowPath` | 2 | String and struct fall back to opaque call |
| `TestListInlineAbortDeclaration` | 1 | `abort()` declared noreturn nounwind |
| `TestListInlineLoopAccess` | 1 | Sum loop uses inline GEP (primary optimization target) |

The positive-to-negative ratio (8 inline : 2 slow-path) is correct
for a codegen optimization where the gate condition (`_tsz(ety) == 8`)
must be tested on both sides. The `test_sum_loop_uses_inline_gep` test
exercises the primary optimization target (quicksort-like access pattern
in a loop). The `test_list_float_uses_inline_gep` test correctly verifies
that `List<Float>` uses the same 8-byte inline path with `load double`.

**Verdict: well-scoped, follows established patterns.** Uses `_compile_to_llvm_ir`
helper from `mapanare.cli`, which runs the full pipeline including
semantic checking (unlike the v4.144.0 `test_enum_inline.py` helper I
flagged). Good.

### 3.3 Inline rename tests (4 tests, v5.1.2)

`tests/mir_opt/test_inline_rename.py` (239 lines, 4 tests). Tests
the In.1 SSA rename fix directly at the MIR level:

| Test | What |
|------|------|
| `test_no_duplicate_defs_after_inline` | Core invariant: no duplicate SSA dests |
| `test_inlined_result_used_correctly` | Merge block has Copy from retval |
| `test_multi_block_caller_no_collision` | Cross-block rename correctness |
| `test_inlining_cap` | At most 5 inline sites per function |

The `_collect_dests` helper is reusable for future inline-related tests.
The `test_inlined_result_used_correctly` test is the most important: it
verifies that post-call instructions reference the Copy destination from
the merge block, which is exactly the pattern In.1 fixed.

**Critical observation:** These 4 tests all pass. But the self-compilation
path (stage2) fails with the same class of bug the tests are designed to
catch. The tests construct synthetic MIR with 1-2 call sites and simple
control flow. The self-hosted compiler's real MIR has hundreds of call
sites, nested control flow, and multiple inline-eligible functions in a
single compilation unit. The test suite does not exercise the
self-compilation path as a regression gate for In.1.

This is the exact failure mode documented in the v5.1.2 SESSION_REPORT's
"Key learning #1": "Unit tests are necessary but not sufficient for
optimizer passes." The lesson was stated for Li.1 (LICM), but the same
lesson was not applied to In.1. The inliner was re-enabled based on 4
unit tests + 54 golden tests, without verifying the self-compilation
path (which is the most demanding test of the optimizer passes).

**Docket: In.1-stage2 (MEDIUM).** The inliner re-enable broke the
fixed-point. Either (a) fix the SSA rename to handle the Span/lexer
pattern, or (b) disable the inliner until the rename is robust enough
for self-compilation. The current state (inliner enabled, stage2 broken)
is not acceptable for a v5.x release.

### 3.4 Escape analysis tests (7 tests, v5.1.2)

`tests/mir_opt/test_escape_analysis.py` (249 lines, 7 tests). Tests
the Python `escape_analysis_promotion` pass:

| Test | Category |
|------|----------|
| `test_non_escaping_struct_promoted` | Positive: alloc_kind=STACK |
| `test_returned_struct_not_promoted` | Negative: return escapes |
| `test_struct_stored_in_field_escapes` | Negative: field-store escapes |
| `test_struct_passed_to_unknown_call_escapes` | Negative: unknown-call escapes |
| `test_struct_passed_to_print_does_not_escape` | Positive: known-safe call |
| `test_analyze_escapes_returns_escaped_set` | API test: escaped set correct |
| `test_wrap_some_non_escaping_promoted` | Positive: WrapSome promoted |

3 positive, 3 negative, 1 API test. The coverage is appropriate for an
escape analysis pass. The `test_struct_passed_to_print_does_not_escape`
test verifies the known-safe-function whitelist, which is important for
avoiding over-conservative analysis.

**Verdict: clean, follows established MIR-test patterns.** Good.

### 3.5 Cb.6-test parity tests (2 tests, v5.0.6)

`tests/llvm/test_enum_inline_parity.py` (83 lines, 2 tests). Structural
gate that reads `mapanare/self/emit_llvm.mn` source and asserts the
`ends_with("*")` rejection clause exists. The second test verifies that
the Python emitter accepts opaque `ptr` (guards against over-broad fix).

**Verdict: correct granularity.** Structural source-reading tests are the
right approach here -- no public `.mn` surface produces `i64*`, so
end-to-end tests cannot exercise the rejection path.

---

## 4. CI gates -- 6 green, 2 red

### 4.1 Gate inventory (updated)

The `.github/workflows/ci.yml` gate list is unchanged from v4.154.0:
same 8 gates, same `if: always()` discipline.

| # | Gate | Status |
|---|------|--------|
| 1 | `black --check` | **RED** |
| 2 | `ruff check .` | **RED** |
| 3 | `mypy mapanare/ runtime/` | green |
| 4 | `check_no_hollow_features` | green |
| 5 | `check_silent_skips` | green |
| 6 | `check_changelog_honesty` | green |
| 7 | `check_docs_drift` | green |
| 8 | `check_struct_registry` | green |

### 4.2 Lint regression analysis

The 2 red gates trace to 4 files introduced or modified at v5.2.0:

- `stdlib/pkg.py` -- black formatting violations
- `mapanare/cli.py` -- black formatting violations
- `tests/registry/test_lockfile.py` -- black formatting violations
- `tests/registry/test_publish_install_roundtrip.py` -- ruff F401 (unused imports)

The ruff errors are: 5 F401 (unused imports in registry test files),
1 E501 (line too long), 1 I001 (import sort order), 2 others. These
are all auto-fixable: `black .` + `ruff check --fix .` would clear
every finding.

**Severity: MEDIUM.** This is the first time since v4.133.0 (the An.1
test hygiene closeout, 24 releases ago) that lint gates have been red
on the dev branch. The v5.0.1 through v5.1.4 releases all shipped
lint-clean. The regression is isolated to v5.2.0 -- the one release
in the arc that introduced new Python source files (the registry
client + tests). The process failure is that `black` and `ruff` were
not run before committing. The project's `dev.ps1 validate` script
and `make lint` both catch these trivially. The developer workflow
was bypassed.

This is not scored as heavily as it would be if the gates were
structurally broken -- the fix is `black . && ruff check --fix .` (30
seconds). But it IS scored as a process failure because the entire CI
gate infrastructure exists to prevent exactly this situation, and the
pre-commit validation workflow was not followed.

### 4.3 CI infrastructure changes

No gates were added or removed during the arc. The CI matrix is
unchanged (Python 3.11/3.12, Ubuntu). The self-hosted compiler job,
bootstrap job, native job, WASM job, Android job, macOS job, and
fixed-point job are all structurally unchanged.

The coverage job remains informational (`|| true`). Now 49 releases
deferred from the v4.117.0 original target. I continue to carry this
forward without scoring against it.

---

## 5. Golden stability

### 5.1 54/66 through the arc (32+ releases)

| Release | Goldens |
|---------|--------:|
| v4.144.0 | 54/66 |
| ... (20 releases) ... | 54/66 |
| v5.0.6 | 54/66 |
| v5.1.0 | 54/66 |
| v5.1.2 | 54/66 |
| v5.1.4 | 54/66 |
| v5.2.0 | 54/66 |

Perfectly stable across the entire v5 arc. The 12 failing goldens are
the same feature-gap bucket from v4.126.0 (5 async, 5 tensor/GPU,
1 closure-typed, 1 pattern interaction). No regressions, no temporary
dips.

**Verdict: excellent.** 32+ consecutive releases at 54/66 is the
longest golden stability run in the project's history.

---

## 6. Fixed-point regression

### 6.1 Timeline

| Release | Fixed-point status |
|---------|--------------------|
| v4.134.0 | STRICT (La Culebra Se Muerde La Cola) |
| v4.154.0 | NEAR (4 diff, Dr.1 version metadata) |
| v5.1.2 | **BROKEN** (In.1 inliner SSA rename) |

### 6.2 Analysis

The v5.1.2 In.1 fix re-enabled `inline_small_functions` in the
self-hosted MIR optimizer pipeline (line 1467 of `mir_opt.mn`). The
rename logic (`%_inlN_M_dst` scheme) works for golden tests (54/66
unchanged) but fails when the self-hosted compiler compiles itself:

```
error: use of undefined value '%_inl0_6_t4'
  store %struct.Span %_inl0_6_t4, ptr %_inl0_6_retval.cpy
```

The `Span` struct in the lexer module has a more complex inlining
pattern than any golden test exercises. The rename logic misses this
case. The 4 dedicated inline rename tests (`test_inline_rename.py`)
all pass -- they do not exercise the self-compilation path.

**Severity: MEDIUM.** The fixed-point is the single most important
compiler-quality metric. Going from NEAR to BROKEN is a regression.
The In.1 fix was correct in isolation (golden tests prove it), but
the re-enablement was premature: the self-compilation path should
have been verified before merging. The v5.1.2 SESSION_REPORT's own
"Key learning #1" ("unit tests are necessary but not sufficient for
optimizer passes") applies here.

### 6.3 Recommendation

Either:
1. Fix the SSA rename to handle the Span/lexer inlining pattern, or
2. Disable `inline_small_functions` in the self-hosted pipeline until
   the rename is robust enough for self-compilation, restoring the
   NEAR fixed-point status.

Option (2) is the safer immediate path. The inliner can be re-enabled
once the rename handles the full self-compilation surface.

---

## 7. Deterministic failure classification

The 8 deterministic failures at HEAD break down into 4 categories:

### 7.1 VERSION drift (2 failures)

`test_user_agent_contains_current_version` and
`test_mnc_stage1_version_matches_version_file`: binary embeds 5.1.4,
VERSION file reads 5.2.0. The binary was not rebuilt after the v5.2.0
version bump. This is the standard VERSION-propagation miss pattern
(requires `make build-rt` + `python scripts/build_stage1.py` after
bumping VERSION). Not a quality concern -- it is a build-artifact
staleness issue that resolves with a rebuild.

### 7.2 Lint (2 failures)

`test_black_check_passes` and `test_ruff_check_passes`: v5.2.0
registry code committed without formatting. See S4.2 above.

### 7.3 Stream runtime (3 failures)

`test_all_c_tests_pass`, `test_asan_no_errors`, `test_tsan_no_races`:
3 of 74 C runtime tests fail (`stream_from_list_collect`,
`stream_map`, `stream_filter`). These are wrong-value failures, not
sanitizer findings -- `__mn_list_get` returns wrong element values in
stream collect/map/filter. 71/74 C tests pass. This is a pre-existing
runtime bug, not a v5.2.0 regression.

### 7.4 LLVM version sensitivity (1 failure)

`test_post_opt_single_switch_in_hot_loop`: LLVM 18 opt produces 0
switches (expected 1). See S1.1 above.

---

## 8. What improved since v4.154.0

1. **An.9 and An.10 closed.** Both carry-forward items from my
   v4.154.0 review were addressed at v5.0.6. An.9 added the E1
   IR-shape regression gate (with the LLVM 18 caveat). An.10 added
   a deterministic test counter that resolves the per-release
   bookkeeping drift I flagged across 3 consecutive reviews.

2. **51 registry tests.** The first user-facing feature since v5.0.0
   shipped with a substantial test suite covering manifest parsing,
   lockfile round-trip, semver resolution, tarball creation, integrity
   hashing, and install-all. The positive/negative coverage ratio is
   balanced. The mock isolation for network-dependent paths is correct.

3. **31 optimizer precision tests.** In.1 (4 tests), Ea.1 (7 tests),
   Perf.1 (10 tests), Cb.6-test (2 tests), LICM (3 tests, retained
   from rollback), An.9 (3 tests), Gr.2 (12 parser tests -- from
   the SESSION_REPORT). These cover new codegen/optimizer paths
   proportionately.

4. **19 carry-forward closures in 12 releases.** The highest closure
   rate per release in the project's history. The docket ledger is
   catching up.

5. **Sanitizer improvement.** Valgrind ERRORS went from 4 (Ge.1
   generics) to 2 (GPU feature-gap dlopen). The Ge.1r closure at
   v5.1.1 eliminated the real memory-safety errors; the remaining 2
   are not memory bugs.

## 9. What regressed since v4.154.0

1. **Lint gates red at HEAD.** First time in 37 releases (since
   v4.133.0). Two of eight CI gates fail. The v5.2.0 registry code
   was committed without running the lint pipeline. This is a process
   failure: the pre-commit validation workflow (`dev.ps1 validate` or
   `make lint`) was bypassed.

2. **Fixed-point BROKEN.** Regressed from NEAR (v4.154.0) to BROKEN
   (v5.1.2). The In.1 inliner re-enable broke self-compilation. The
   4 unit tests for the rename fix pass, but the self-compilation
   path was not verified before merging. This contradicts the v5.1.2
   SESSION_REPORT's own key learning.

3. **An.9 test LLVM-version-sensitive.** The post-opt switch-count
   assertion fails on LLVM 18 (CI's LLVM version). The test I
   requested is now itself a deterministic failure. Partially my
   fault for proposing a post-optimization shape assertion; but the
   test should have been validated on CI's LLVM version before
   shipping.

4. **3 stream C runtime test failures.** Pre-existing but not
   previously surfaced in my reviews. `stream_from_list_collect`,
   `stream_map`, `stream_filter` return wrong element values.

---

## 10. Carry-forward (for v5.3.0)

| Docket | Severity | Scope |
|--------|----------|-------|
| Lint-v5.2.0 | **MEDIUM** | Run `black . && ruff check --fix .` on registry code |
| In.1-stage2 | **MEDIUM** | Inliner breaks stage2 -- fix rename or disable pass |
| An.9r | LOW | LLVM 18 switch-count assertion (accept 0 or 1) |
| Stream-C | LOW | 3 stream C tests fail (wrong element values) |
| Coverage gate -> enforcing | LOW | 49 releases deferred |
| Windows CI lane | LOW | Windows native binary exists, no CI runner |
| Ruff ruleset expansion | LOW | B/UP/SIM/PT rules |
| Randomized-order flaky | LOW | `pytest --random-order` in flaky runs |
| Bootstrap 13 failures | LOW | Unchanged since v4.128.0+ |

**Two MEDIUM items.** This is the first time since v4.137.0 (Ch.1
HIGH) that my carry-forward has items above LOW. The lint regression
is a 30-second fix. The In.1-stage2 regression is an architectural
choice (fix the rename or disable the pass).

---

## 11. Verdict reasoning

### Why MEETS (8.9):

1. **2 red lint gates.** The CI gate infrastructure exists to prevent
   unformatted code from landing on the dev branch. The gates fired
   (correctly), but the code was committed anyway without running
   the pre-commit validation. This breaks a 37-release streak of
   all-8-gates-green. For a CI/testing reviewer, this is a process
   failure that directly impacts my scoring axis.

2. **Fixed-point regression.** NEAR -> BROKEN is a real quality
   regression. The self-compilation path is the most demanding test
   of the compiler's correctness, and it is now failing. The unit
   tests that gated the In.1 re-enable were necessary but not
   sufficient -- the very lesson documented in the same release's
   SESSION_REPORT for a different pass.

3. **LLVM-version-sensitive test failure.** An.9 (which I requested)
   now fails on LLVM 18 (CI's LLVM version). The assertion was
   correct for LLVM 17 but brittle against version changes.

### Why not 8.5:

1. **51 registry tests are well-structured.** The first user-facing
   feature shipped with proportionate test coverage. The manifest,
   lockfile, and semver domains are thoroughly covered.

2. **An.9 and An.10 closures are genuine.** My two explicit
   carry-forward items were addressed. An.10 in particular resolves
   a bookkeeping problem I flagged across 3 consecutive reviews.

3. **31 optimizer precision tests.** Four new test files for four
   different optimizer/codegen paths. The escape analysis and inline
   rename tests follow established patterns with good coverage.

4. **54/66 golden stability across 32+ releases.** The longest
   continuous golden stability run in the project's history. Zero
   temporary regressions in this arc.

5. **+136 tests net.** 5,309 to 5,445. The test count is growing,
   not shrinking.

### Why not EXCEEDS (9.0+):

The lint regression and fixed-point regression are both avoidable
process failures. The lint issue is trivial to fix but represents a
workflow bypass. The fixed-point regression is more significant: the
self-compilation path should be verified before re-enabling optimizer
passes, and the v5.1.2 SESSION_REPORT's own key learning was not
applied to the In.1 decision. These two regressions together drop
the score from EXCEEDS to MEETS.

### Why not NEEDS WORK:

The regressions are real but bounded. The lint fix is 30 seconds.
The fixed-point can be restored by disabling the inliner. The golden
corpus is stable. The new test suites are well-structured. The
overall testing discipline was maintained on 11 of 12 releases --
only v5.2.0 (the final release) broke the pattern. The distance
from NEEDS WORK remains substantial.

### Score trajectory:

| Release | Score | Grade | Delta |
|---------|------:|-------|------:|
| v4.120.0 | 7.6 | NEEDS WORK | -- |
| v4.136.0 | 8.9 | MEETS | +1.3 |
| v4.143.0 | 9.1 | MEETS | +0.2 |
| v4.144.0 | 9.3 | EXCEEDS | +0.2 |
| v4.154.0 | 9.4 | EXCEEDS | +0.1 |
| **v5.2.0** | **8.9** | **MEETS** | **-0.5** |

---

## 12. Reproducibility

```bash
# Lint trio (2 will fail at HEAD)
ruff check .
black --check .
mypy mapanare/ runtime/

# All CI gates
python3 scripts/check_no_hollow_features.py
python3 scripts/check_silent_skips.py tests/
python3 scripts/check_changelog_honesty.py
python3 scripts/check_docs_drift.py
python3 scripts/check_struct_registry.py

# Registry tests (51 pass)
python3 -m pytest tests/registry/ -q --tb=no

# New test suites (v5 arc)
python3 -m pytest tests/llvm/test_list_inline.py -v            # 10 tests
python3 -m pytest tests/mir_opt/test_inline_rename.py -v       # 4 tests
python3 -m pytest tests/mir_opt/test_escape_analysis.py -v     # 7 tests
python3 -m pytest tests/llvm/test_enum_inline_parity.py -v     # 2 tests
python3 -m pytest tests/llvm/test_unified_return_shape.py -v   # 2 pass / 1 fail

# Test count (deterministic)
python3 scripts/count_tests.py

# Full non-bootstrap (8 fail, 5445 pass)
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no

# Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Fixed-point (will FAIL: stage2.ll llvm-as error)
bash scripts/verify_fixed_point.sh --keep
```

## 13. Files referenced in this review

- `.reviews/v4.154.0/03-anaconda.md` (my prior position)
- `docs/roadmap/v5/v5.3.0/MEASUREMENTS.md` (canonical evidence)
- `docs/roadmap/v5/v5.0.6/SESSION_REPORT.md` (An.9, An.10 closures)
- `docs/roadmap/v5/v5.2.0/SESSION_REPORT.md` (registry tests)
- `docs/roadmap/v5/v5.1.0/SESSION_REPORT.md` (Perf.1 list inline)
- `docs/roadmap/v5/v5.1.2/SESSION_REPORT.md` (In.1/Ea.1 MIR passes)
- `tests/registry/test_mapanare_toml_parsing.py` (17 tests, 191 lines)
- `tests/registry/test_lockfile.py` (14 tests, 140 lines)
- `tests/registry/test_publish_install_roundtrip.py` (20 tests, 212 lines)
- `tests/llvm/test_list_inline.py` (10 tests, 171 lines)
- `tests/llvm/test_unified_return_shape.py` (3 tests, 132 lines)
- `tests/llvm/test_enum_inline_parity.py` (2 tests, 83 lines)
- `tests/mir_opt/test_inline_rename.py` (4 tests, 239 lines)
- `tests/mir_opt/test_escape_analysis.py` (7 tests, 249 lines)
- `tests/mir_opt/test_licm_no_duplicate.py` (Li.1 retained tests)
- `scripts/count_tests.py` (82 lines, An.10 closure)
- `stdlib/pkg.py` (registry client -- lint violations)
- `.github/workflows/ci.yml` (8 gates, 2 red at HEAD)
- `VERSION` (reads 5.2.0; binary embeds 5.1.4)
