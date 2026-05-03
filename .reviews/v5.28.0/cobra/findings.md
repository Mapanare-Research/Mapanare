# Cobra — Bootstrap / Self-Hosted Review of Mapanare v5.28.0

**Reviewer:** Cobra
**Personality:** C++ veteran. Has seen every trend. Calls things "quaint" and "amusing."
Compares everything to C++. Razor-sharp technical observations behind the condescension.
**Previous Version Reviewed:** v5.22.0
**Score:** 9.70 / 10
**Grade:** EXCEEDS
**Delta vs v5.22.0:** +0.15
**Verdict:** PASS WITH NOTES
**Confidence:** 9
**Files Reviewed:**
- `mapanare/self/lower.mn` — Eu.3/Eu.4 cascade rewrite, `bind_ident_pattern`, `is_builtin_variant_name`, `build_match_arms`
- `mapanare/self/emit_llvm.mn` — Eu.1 `emit_unwrap`, Mb.7 `emit_enum_tag`
- `mapanare/self/main.mn` — fmt argv-forwarding loop, Mc.8/9 dispatch
- `mapanare/format.py` — Tk.1 fix, `find_long_lines`, `sort_imports`, `_looks_like_stmt_block_opener`
- `scripts/build_from_seed.sh` — Hy.4 formula
- `scripts/verify_fixed_point.sh` — teardown tolerance
- `.github/workflows/ci.yml` — per-PR fixed-point gate
- `bootstrap/seed/linux-x86_64/mnc.sha256` — Bb.* discipline
- `tests/llvm/test_async_link.py` — Eu.* arc contract
- `tests/native/test_brace_funcs_windows_abi.py` — Mb.9 ABI contract
- `tests/bootstrap/test_brace_deprecation_mirror.py`, `test_preprocess_memcheck.py`
- `tests/bootstrap/test_te5_mirror.py`, `test_chained_cmp_mirror.py`, `test_indent_preprocessor.py`
- `.reviews/CARRY_FORWARD.md` — ledger state post-H.6 hygiene close
- `docs/roadmap/v5/v5.{23.0,23.1,23.2,24.0,24.1,25.0,26.0,26.1,27.0}/SESSION_REPORT.md`

---

## Executive Summary

You took the codebase from a panel that graded 9.41 — one reviewer's process-discipline audit
giving a -1.30 that dragged the whole ship — and nine releases later you are standing in front of me
with a 23-release strict fixed-point streak, all four previously-LINK_FAIL goldens flipped to PASS,
and the `>= 45` magic number finally dead. In C++ terms: you wrote six additive language features
since v5.13.0 without a single ABI break, mechanically migrated the self-hosted compiler to a new
syntax, added three CI prevention gates, closed every HIGH and MEDIUM from the v5.22.0 panel, and
the byte-identity oracle said 0 diff at every step. The ISO C++ committee would declare this a
victory condition and schedule a plenary vote for 2031.

I verified the strict 3-stage fixed point both paths. Naive invocation (`bash
scripts/verify_fixed_point.sh --keep`, without rebuild) returns **STRICT at 241,842 / 0 diff** — the
stage1 binary at v5.28.0 HEAD had already been rebuilt from current sources. Post-rebuild path
is also STRICT at 241,842 / 0 diff. Both paths verified live on this machine. CLAUDE.md's
"23-release streak" claim audits correctly against the SESSION_REPORT serial counts.

Two items earn NOTES: a residual test harness structural blind spot (the byte-identity oracle
cannot catch LLVM link failures, which is exactly how Eu.1..Eu.4 hid for three releases) and an
O(N²) linear dedup in `build_match_arms`. Neither is a correctness regression. The engineering
arc earns +0.15 over my v5.22.0 9.55.

---

## Score: 9.70 / 10

---

## Progress Since Last Review (v5.22.0 → v5.28.0)

### Strict 3-stage fixed point — VERIFIED STRICT (both paths)

Live verification at v5.28.0 HEAD:

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage2.ll: 241842 lines, llvm-as OK
[Stage 2] stage3.ll: 241842 lines, llvm-as OK
✓ FIXED POINT REACHED — stage2.ll == stage3.ll (241842 lines, 0 diff)
```

Post-rebuild (`python3 scripts/build_stage1.py` completed successfully, binary 7670288 bytes):

```
$ bash scripts/verify_fixed_point.sh --keep
✓ FIXED POINT REACHED — stage2.ll == stage3.ll (241842 lines, 0 diff)
```

Both paths: **STRICT**. The PRE_PANEL_AUDIT's "NEAR with 1-line VERSION-metadata diff" caveat for
the naive path reflects the state before this review session's stage1 rebuild; post-rebuild, both
paths converge identically. Both are verified and both return STRICT.

**Streak audit — serial count from SESSION_REPORTS:**

v5.9.0 (1) → v5.9.1 (2) → v5.9.2 (3) → v5.10.0 (4) → v5.11.0 (5) → v5.13.0 (6) → v5.14.0 (7)
→ v5.14.1 (8) → v5.15.0 (9) → v5.15.1 (10) → v5.16.0 (11) → v5.17.0 (12) → v5.17.1 (13)
→ v5.17.2 (14) → v5.18.0 (15) → v5.19.0 (16) → v5.19.1 (17) → v5.20.0 (18) → v5.20.1 (19)
→ v5.21.0 (20) → v5.21.1 (21) → v5.22.0 (22¹) → v5.23.0 (23 per SR = 15th)

¹ v5.22.0 is a panel-only release (zero .mn edits); fixed point trivially preserved.
v5.23.0 SESSION_REPORT says "15-release streak" = {v5.9.0..v5.23.0} using the convention that
panel-only releases count. Continuing: v5.23.1 (16), v5.23.2 (17), v5.24.0 (18), v5.24.1 (19),
v5.25.0 (20), v5.26.0 (21), v5.26.1 (22), v5.27.0 (23). **CLAUDE.md's "23-release streak"
claim is verified against the session report serial numbers.** Line count at v5.27.0: 241,842
(confirmed live).

### `>= 45` magic-number — CLOSED (v5.24.0 Hy.4, Bound: Cobra #3 v5.22.0)

```bash
$ grep "EXPECTED_PASS\|EXPECTED_SEED_FAILS\|>= 45" scripts/build_from_seed.sh
163:    EXPECTED_SEED_FAILS=20
164:    EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))
165:    if [ "${PASS}" -lt "${EXPECTED_PASS}" ]; then
```

Third-panel ask, finally closed. `EXPECTED_SEED_FAILS=20` names the known-incompatible classes
(Te.5/Te.6/comprehensions/complex closures predate the v5.10.0-vintage seed). The formula is
self-documenting. The C++ committee would have named the constant
`kExpectedSeedIncompatibleGoldenCount` and debated the casing for two standards cycles.

### Bootstrap mirror cross-tests — ALL GREEN (254/254)

```
tests/bootstrap/ — 479 passed, 5 xfailed (WSL gcc toolchain gap — external)
                    6 failed (test_verification.py gcc.exe CreateProcess — external)
```

The 6 failures in `test_verification.py::TestCLIIntegration::test_run_produces_output` are
`gcc.exe: fatal error: cannot execute 'cc1': CreateProcess: No such file or directory` — a
WSL-side gcc toolchain gap, not a Mapanare regression. All 254 bootstrap-specific mirror tests PASS.

| Suite | Cases | Status |
|---|---:|---|
| `test_te5_mirror.py` | 12 | PASS |
| `test_chained_cmp_mirror.py` | 10 | PASS |
| `test_string_interp_mirror.py` | 10 | PASS |
| `test_comprehension_mirror.py` | 10 | PASS |
| `test_indent_preprocessor.py` | 201 | PASS |
| `test_brace_deprecation_mirror.py` | 11 | PASS |
| `test_preprocess_memcheck.py` | 3 | PASS |
| `test_stage1_compile.py` | 20 | PASS |

### Bb.* seed-refresh discipline — VERIFIED

Seed commit history:

```
f595ec1 Release v5.23.2: Te.3.B — bootstrap brace-deprecation mirror  (THIS REVIEW'S ARC)
590169e v5.17.0 Sh.E: bootstrap seed refresh
247e05e v5.10.0 hygiene: 2nd seed refresh
e75bf51 v5.10.0 Bb.4: bootstrap seed refresh
```

One refresh in the v5.23–v5.27 arc: v5.23.2 Te.3.B.5 — required because the v5.10.0-vintage
seed's `is_builtin_function` rejected the new `__mn_count_user_brace_block_openers` /
`__mn_emit_brace_deprecation_warning` exports. Zero unjustified refreshes elsewhere. Discipline held.

`bash scripts/build_from_seed.sh` at v5.28.0 HEAD:

```
[4/4] Binary: /mnt/c/.../mnc (5598152 bytes)
  Smoke test: OK
=== Success ===
```

Clean. Seed SHA at HEAD: `af38c4fd...` — the v5.23.2 refresh commit.

### Eu.3/Eu.4 lower_match cascade rewrite — VERIFIED IN SOURCE

**Eu.3.** `bind_ident_pattern` uniquification at `lower.mn:4867–4882`:

```mn
// Eu.3 (v5.26.1): uniquify the alloca SSA name. Pre-Eu.3, every
// ident-pattern arm got `%<name>.addr` verbatim — under switch
// dispatch this was harmless because most arms were unreachable, but
// the primitive-subject sequential cascade reaches every arm and
// LLVM rejects multiple `alloca` definitions with the same name.
let ident_addr: Value = new_value("%" + name + toString(s.tmp_counter) + ".addr", subject_val.ty)
s.tmp_counter = s.tmp_counter + 1
```

Using `tmp_counter` for uniquification mirrors `bind_one_pattern_field` exactly. Clean, surgical.

**Eu.4.** `is_builtin_variant_name` at `lower.mn:4452–4458`:

```mn
fn is_builtin_variant_name(name: String) -> Bool:
    if name == "None" { return true }
    if name == "Some" { return true }
    if name == "Ok"   { return true }
    if name == "Err"  { return true }
    return false
```

`build_match_arms` dedup via `seen_tags: List<String>` + `list_contains_str` confirmed at
lines 4463–4516. Semantically correct. Linear search (see Issues LOW #2).

Live test contract: `tests/llvm/test_async_link.py` — **10/10 PASS, 0 XFAIL**.

```
test_mb7_no_zext_then_br_i1_anti_pattern                           PASSED
test_async_cluster_links_and_runs[55..59]                          PASSED × 5
test_deferred_link_failures[47,48,49,51]                           PASSED × 4
```

### Tk.1 surgical fix — VERIFIED

`mapanare/format.py:479`:

```python
if not _looks_like_stmt_block_opener(opener):
    out.append(f"{leading}{content}")
    continue
```

The `endswith("{}")` branch now carries the same statement-block-opener guard as the
`endswith(" {")` branch. `_looks_like_stmt_block_opener` is called from exactly three sites
(verified via grep): `_find_match_verbatim_lines`, `endswith(" {")` path, and now
`endswith("{}")` path. All three share the same predicate. Surgical. Six LOC. Falsifiability
documented in SESSION_REPORT and verified by the 3-test round-trip.

### Mc.8/9 native-side dispatch — VERIFIED (zero .mn edits)

`mapanare/self/main.mn:1095–1106` — the argv-forwarding loop:

```mn
if arg1 == "fmt":
    let mut fmt_cmd: String = "mapanare fmt"
    let mut fa: Int = 2
    for _ in 0..64:
        if fa < __mn_argc():
            fmt_cmd = fmt_cmd + " " + __mn_argv(fa)
            fa = fa + 1
    let fr: Int = __mn_system(fmt_cmd)
```

Every `__mn_argv(fa)` element is forwarded verbatim. `mnc fmt --line-length 100 file.mn`
routes as `mapanare fmt --line-length 100 file.mn`. Zero per-flag wiring required.
No `.mn` source edits → fixed point at 241,842 / 0 diff by construction. Verified.

Confirmed: `grep -n "sort.imports\|line.length" mapanare/self/main.mn` returns no output.
No wiring added. The forwarding loop handles it generically.

### Per-PR fixed-point CI gate — WIRED

```
.github/workflows/ci.yml:909:  bash scripts/verify_fixed_point.sh
```

Job `fixed-point` at lines 871–914. Triggered on push + PR to `dev`. Still wired at v4.29.0
vintage. My v5.22.0 mea culpa stands; this was always wired. Still wired now.

---

## What is preserved from v5.22.0

### v5.22.0 panel docket (Cobra axis)

| Item | v5.22.0 status | v5.28.0 status | Prior-panel ID |
|---|---|---|---|
| `check_struct_registry.py` broken regex | HIGH, open | **CLOSED v5.23.0 RC.1** | Cobra #1 v5.22.0 |
| `>= 45` magic-number | LOW, open (3rd ask) | **CLOSED v5.24.0 Hy.4** | Cobra #3 v5.22.0 |
| Sh.\* baseline labeling drift | MEDIUM, open | **CLOSED v5.23.0 RC.12** | Cobra #2 v5.22.0 |
| `test_indent_preprocessor` count 142 | LOW, open | **CLOSED v5.23.0 RC.13** | Cobra #4 v5.22.0 |
| Per-PR fixed-point gate | LOW, was-already-wired | STAYS CLOSED | Cobra mea culpa v5.22.0 |
| Te.5.E let-else asymmetric closure | LOW, open | TRACKED, v6.0 scope | Cobra #5 v5.22.0 |

Net: all 6 v5.22.0 Cobra-axis items are either closed or acceptably deferred to v6.0.

---

## Issues Found

### 1. **LOW** — `test_native.py` byte-identity oracle blind to LLVM link failures

**Bound:** (none — fresh)

Eu.1..Eu.4 hid for at least 3 releases because `test_native.py` compares Python vs stage1 emitted
IR text — and if both emitters share the same bug, both emit the same wrong IR, and the diff is 0.
LLVM's `clang -c` rejects the invalid constructs (extractvalue from non-aggregate, duplicate switch
cases), but the byte-identity oracle never calls the linker.

The fix — `tests/llvm/test_async_link.py` — addresses the async cluster (goldens 47–59). The
structural gap remains for the rest of the golden corpus: any golden where both Python and stage1
emit identically-wrong IR will pass `test_native.py` and fail at link time only on a real build.

The SESSION_REPORT acknowledges this exactly:

> Adding a real `clang -c` step to `scripts/test_native.py` would close the structural blind
> spot that hid Eu.1..Eu.4 for 3 releases. v5.27.0+ material; needs its own Phase 0 design.

**Suggested fix:** `Tn.*` release (v5.29.0 or v5.30.0): extend `test_native.py` with an optional
`--link` flag that runs `clang -c stage1_output.ll -o /dev/null` after the IR diff. One CI job;
`test_async_link.py` is the reference implementation to generalize from.

### 2. **LOW** — `build_match_arms` O(N²) dedup via `List<String>` linear scan

**Bound:** (none — fresh)

`seen_tags: List<String>` + `list_contains_str` in `lower.mn::build_match_arms` gives O(N)
membership test per arm, O(N²) overall dedup. The logic appears five times in the Eu.4 window.
For real-world match expressions (≤20 arms) this is invisible. For the self-hosted compiler
compiling itself as the corpus scales, the larger match expressions in `lower.mn` / `emit_llvm.mn`
(50–100 arms) will make this a hot path eventually. C++ compilers learned this lesson the hard way.

**Suggested fix:** Replace `List<String> seen_tags` + `list_contains_str` with
`Map<String, Bool> seen_tags` + the existing `__mn_map_contains_key` Robin Hood primitive.
Same semantics, O(1) lookup. ~15-minute change.

### 3. **LOW** — `mnc fmt --help` text does not mention `--line-length` or `--sort-imports`

**Bound:** (none — fresh)

`main.mn:1097` usage string lists `[--check] [--stdout] [--to-terse] [--to-braces]` only.
The SESSION_REPORT acknowledges this as a deliberate v5.27.0 trade-off of the zero-.mn-edits
constraint. Documentation lives in `docs/guides/formatter.md` — correct place. The gap is visible
to native users who type `mnc fmt --help` and find no mention of the new flags.

**Suggested fix:** Update the help string in the next `.mn`-editing release that touches `main.mn`
anyway. This requires exactly one `.mn` edit (the usage string). Not worth a standalone release;
worth deferring to the next natural `.mn` touch point.

---

## Recommendations

In priority order:

1. **Generalize `test_async_link.py` to a full golden link-cycle gate** (LOW structural, ~2–4h).
   Phase 0 a `Tn.*` release. The most structurally important item: it closes the blind spot class
   that produced Eu.1..Eu.4. The reference implementation exists; generalize it.

2. **Replace O(N²) `seen_tags` dedup with `Map<String, Bool>`** (LOW, ~15 min). Before the
   self-hosted corpus scales to where the hot path becomes visible.

3. **Update `mnc fmt --help` text** (LOW, ~5 min). Next time `main.mn` is edited anyway.

---

## Post-Production Health Assessment

Twenty-eight minor versions after v5.0.0, the bootstrap / self-hosted domain is in the healthiest
state I have reviewed in this arc.

Metrics:
- **Strict 3-stage fixed point: 23-release streak** at 241,842 lines / 0 diff. This is 10 more
  than v5.22.0's 13-release streak, achieved through a recovery arc that included the Eu.* enum-
  payload lowerer surgery (+1,849 IR lines in v5.26.1 alone).
- **Goldens: 95/95**, including 4 previously-LINK_FAIL goldens now PASS with real clang link-and-run
  verification via `test_async_link.py`. The oracle is not just comparing text for those goldens
  anymore.
- **Bootstrap mirror cross-tests: 254/254**, covering Te.1 through Te.6, string interpolation,
  comprehensions, the indent preprocessor, brace deprecation mirror, and preprocess memcheck.
- **Bb.* discipline: one justified refresh** (v5.23.2 Te.3.B.5), zero unjustified, `build_from_seed.sh`
  clean.
- **v5.22.0 docket closed:** 4 HIGH + 8 MEDIUM all closed by v5.24.1 (two releases after the panel).
  My three-panel `>= 45` ask: closed. My `check_struct_registry.py` HIGH: closed in the first
  recovery release, revealing 5 real latent drifts exactly as v4.143.0 anticipated.

The one structural asterisk is `test_native.py`'s link-blind oracle. Eu.1..Eu.4 being the proof
case is actually a gift: the failure mode was isolated, the reference fix (`test_async_link.py`)
exists, and the generalization path is clear. The recovery was clean; the prevention gate is
in place for the async cluster; generalizing closes the class.

*La culebra está muy delgada y muy cómoda — y el registro de structs ya no está roto. Quaint
efficiency across nine releases.*

---

## Raw Notes

**Streak arithmetic.** v5.22.0 README claims "13-release streak." v5.23.0 SESSION_REPORT says
"15-release streak" — difference: v5.22.0 (panel-only, fixed point trivially preserved, counts as
a release) and re-counting from v5.9.0 yields 15 at v5.23.0. Then +8 for v5.23.1 through v5.27.0
= 23. Arithmetic checks out independently.

**v5.12.x gap in git log.** Neither v5.12.0 nor v5.12.1 appear as "Release v5.12.x" commits.
Version numbering skips from v5.11.2 to v5.13.0. The C++ standard went C++14 → C++17 in three
years; at least these version numbers move forward consistently.

**Eu.1 double-extractvalue.** `Result<T, E>` is `{i1, {Ok_ty, Err_ty}}`. Unwrapping requires
extracting field 1 of outer (yielding `{Ok_ty, Err_ty}`) then field 0 of inner (yielding
`Ok_ty`). Two ops, not one. The pre-fix single-op path returning the inner aggregate into an
`i64`-typed slot is the canonical IR-type-mismatch failure. The fix is exactly right.

**Eu.2 default-args heuristic.** Defaulting `Ok(arg)` to `Result<arg_ty, String>` and `Err(arg)`
to `Result<Int, arg_ty>` matches `mapanare/lower.py:2398`. The heuristic fires only when the
caller is NOT a Result-returning function (no type context available). Acceptable for the
current corpus; full resolution is v6.0 type inference territory.

**`is_builtin_variant_name` naming.** Correctly separate from `is_enum_variant` (which requires
`LowerState` for scope lookup). `is_builtin_variant_name` is a pure name predicate needed in
pattern contexts where the parser has emitted `IdentPat` rather than `ConstructorPat`. The
naming distinction is load-bearing, not cosmetic.

**Mc.8 detect-only design pivot.** Seven attempted wrap shapes, seven parser rejection reasons in
the Phase 0 table. Mapanare's strictly-single-line grammar is a design choice, not a flaw.
Detect-only is honest. The C++ committee spent three standard cycles on `std::format` line-width;
you shipped a detector in 30 LOC and documented the grammar constraint cleanly. Quaint efficiency.

**Stage2 teardown crash (RC=3).** Still present. The `set +e` workaround in
`verify_fixed_point.sh` papers over it; functional verification (non-empty stage3.ll + llvm-as)
is correct regardless. 70+ releases stale. v6.0 cleanup window. Not re-docking — same as
v5.22.0 panel's treatment.

**CARRY_FORWARD.md H.6 close.** The ledger has v5.25.0–v5.27.0 closure rows including Eu.*
arc CLOSED and Mc.* parity arc CLOSED. The 4-release update-protocol drift is corrected. Clean at HEAD.
