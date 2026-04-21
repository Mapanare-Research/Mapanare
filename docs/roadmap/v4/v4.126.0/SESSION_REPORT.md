# v4.126.0 Session Report — Golden Test Push: 27 → 39 native (+12)

> First buffer release of the v4.130.0 closeout arc. Golden test
> triage + fix pass for the self-hosted compiler.

## Headline

**`mnc-stage1` golden pass count: 27 → 39 of 65 (+12).** PLAN target was 40+ (≥ 14 improvement); release lands 1 test short of the target. Two surgical fixes (one parser bug, one harness over-strictness) closed 12 tests; the remaining 26 are documented per-test with reproducers and dispositions.

## What shipped

### Code change 1 — parser fix (`mapanare/self/parser.mn:366`)

`is_definition_start` was missing `KW_CONST` and `KW_TRAIT`. The parser's top-level driver loop dispatches each top-level token via this predicate; a false return routes the token to the statement parser instead of the definition parser. So module-level `const N: Int = 100` was silently consumed as a statement, never registered in any module-level scope, and the semantic check errored with `Undefined variable 'N'` whenever a function body referenced the const.

The bug had been latent since v4.55.0 (when const was introduced). Three previous workarounds — v4.78.0's `const_def` early branch in `register_def`, v4.78.0's `parse_const_def → LetDef` alias, and the duplicate `KW_CONST` dispatch at parse_definition.mn:476/524 — all addressed downstream paths that were unreachable because the upstream `is_definition_start` filter rejected the token.

**Discovery process**: confirmed via debug instrumentation. Initial hypotheses (semantic.mn long-if-chain unreachability, register_module_let dead code) were wrong. Adding `__mn_str_eprint("[DBG] parse_const_def fired with name='" + name + "'\n")` to `parse_const_def` showed the function never fired for module-level const. Adding a similar print at the top of `parse_definition` showed `parse_definition` was only called once — for the `fn main()` keyword. The `const N: Int = 100` line was not reaching `parse_definition` at all. That narrowed the bug to the upstream dispatch in `parse(source, filename)` at parser.mn:422, which uses `is_definition_start(tt)` as the gate.

**Fix**: 4 lines added to `is_definition_start` (KW_CONST + KW_TRAIT entries) plus 6 lines of comment context. The previously-added downstream workarounds were left in place — they're now belt-and-suspenders rather than load-bearing.

**Closes**: `54_const_basic`, `58_const_scope` (2 golden tests).

### Code change 2 — harness relax (`scripts/test_native.py:577`)

Documented option (b) from `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`. The harness compared `stage1.defines == bootstrap.defines` (strict equality). Python bootstrap runs `inline_small_functions` MIR pass; `mnc-stage1` does not (the self-hosted equivalent was disabled at v4.111.0 because it produced malformed MIR — the four zero-ROI passes documented in v4.109.0 forensics). So `mnc-stage1` consistently emits a *superset* of functions for the same source, and the strict equality fired even though the IR was semantically equivalent (LLVM's own inliner converges them at `-O2`).

**Fix**: changed strict equality to strictly-fewer (`if sfp["defines"] < fp["defines"]`). The `missing = set(fp["functions"]) - set(sfp["functions"])` check at line 583 is unchanged — it remains the actual correctness gate that catches truly-dropped functions.

**Closes**: `03_function`, `15_multifunction`, `23_multi_return`, `26_generics`, `27_impl`, `28_traits`, `41_module_let`, `42_module_let_string`, `43_module_let_math`, `45_ffi_bind` (10 golden tests).

### What did NOT ship

Three other paths were investigated and abandoned at the per-test 30-minute time limit per PLAN's threshold rule:

- **Sh.2 emit_mir_call NULL deref** (11 tests). Two minimal reproducers were narrowed (see CHANGELOG and GOLDEN_TRIAGE for details). Hypothesis: `find_function` returns a copied FnEntry with stale String pointer for `fe.ret_type`. Same family as v4.101.0's Python-emitter `_move_resource` bugs. The fix would be to mirror `_move_resource` into self-hosted `emit_llvm.mn` at six analogous call sites — multi-day work, scoped for v4.127.0+ per PLAN.

- **lower_expr crashes** (3 tests). `33_break_continue` reproducer narrowed to "Int let then 2+-element list literal triggers `lower__lower_expr+0x2501`". Same bug family as Sh.2 — likely List<Value> reallocation in `lower_list`'s push loop with stale pointers. The comment at lower.mn:2856-2858 explicitly warns about this scenario.

- **Async / tensor / closure-typed missing features** (11 tests). Adding `block_on` etc. as builtins in self-hosted `semantic.mn` would let the semantic check pass, but the self-hosted lowerer has zero coroutine support — `block_on` would lower to an unresolved Call. Per PLAN's "Default: skip and document. Stubs create false confidence."

## Verification

| Check | Result |
| --- | --- |
| `python3 scripts/build_stage1.py` | clean build, 3,488,912 bytes stripped |
| `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | **39 pass / 26 fail** of 65 in 8.1s |
| Δ from v4.125.0 HEAD baseline | **+12 passes, 0 regressions** |
| `make test` (excluding bootstrap) | 5,058 passed / 38 failed / 103 skipped / 7 xfailed |
| Failure set vs v4.124.0 baseline | byte-identical (An.1 carry-forward) |
| `ruff check` on touched files | clean |
| Pre-existing `make lint` baseline | unchanged (302 findings, An.2) |
| `libmapanare_rt.a` | byte-identical to v4.125.0 (no C runtime changes) |

## Exit criteria scorecard

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Pass count improved by ≥ 14 (27 → 40+) | ❌ MISSED BY 1 (27 → 39, +12) | `scripts/test_native.py` output |
| 2 | All 65 failures categorized (E/L/M/R/T/H/B) | ✅ | `GOLDEN_TRIAGE.md` |
| 3 | Remaining failures documented with root cause + complexity | ✅ | `GOLDEN_TRIAGE.md` |
| 4 | No regressions in previously-passing golden tests | ✅ | 27 baseline tests still pass; +12 new passes are pure additions |
| 5 | `make test` green | ⚠ pre-existing An.1 carry-forward | Failure set byte-identical to v4.124.0 baseline; no new failures |
| 6 | `make lint` clean | ⚠ pre-existing An.2 carry-forward | Touched files clean; baseline 302 findings unchanged |
| 7 | Standard closeout clean | ✅ | CHANGELOG + SESSION_REPORT + VERSION bump |

**Criterion 1 missed by 1 test.** The shortfall is documented honestly. The Sh.2 fix that would close 11 more tests is identified and scoped for v4.127.0; with that fix landed, the count would jump from 39 to 50 (77%).

## Diff stat

```
mapanare/self/parser.mn   |  10 +++++++++-
scripts/test_native.py    |  17 ++++++++++++++---
docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md    | new
docs/roadmap/v4/v4.126.0/SESSION_REPORT.md   | new
CHANGELOG.md              | <release entry added>
```

3 files changed for code (parser.mn + test_native.py); 2 docs added; CHANGELOG appended. ~22 net new code lines.

## Open items carried to v4.127.0

| Item | Source | Disposition |
| --- | --- | --- |
| Sh.2 — `__mn_str_starts_with` from `emit_mir_call+0x236a4` | v4.111.0 docket | v4.127.0 PLAN target — mirror v4.101.0 `_move_resource` into self-hosted emit_llvm.mn |
| L — lower_expr crashes (offsets 0xb26 + 0x2501) | v4.126.0 narrowed | Same family as Sh.2 |
| Sh.4 — self-hosted async/coroutine support | v4.111.0 docket | v4.128.0+ |
| Sh.6 — self-hosted tensor support | v4.111.0 docket | v4.128.0+ |
| Sh.7 — self-hosted closure-typed parameters | v4.111.0 docket | v4.128.0+ |
| `51_match_guards_and_or` — bootstrap also fails | v4.104.0 carry | Out of scope (orthogonal to self-hosted) |

---

**v4.126.0 lands.** Buffer release 1 of 4 (v4.126.0 → v4.130.0). The two fixes shipped are small, surgical, and immediately reviewable. The diagnostic narrowing on Sh.2 + L gives v4.127.0 a concrete starting point. The honest 39 / 65 (not 40+) is recorded in the criteria scorecard rather than hidden.
