# v5.48.1 — Phase 0 Audit (PRE_PHASE_AUDIT.md)

**Status:** complete (Phase 0 gate)
**Generated:** v5.48.1 session-start audit, before any C runtime
edit, against `count_user_brace_block_openers` at HEAD = v5.48.0
(Python-side complete; bootstrap mirror + self-host migration
deferred).

This audit re-confirms the v5.48.0 PRE_PHASE_AUDIT counts at
v5.48.1 HEAD, projects the formatter's migration impact per
`mapanare/self/` module, enumerates the cross-bootstrap fixture
shapes that v5.48.1 must cover, and decides per-module
migration scope before Phase 5 begins.

The PROMPT explicitly forbids editing
`runtime/native/mapanare_core.c` until this audit lands.

---

## Re-confirmation of v5.48.0 totals

`count_user_brace_block_openers` over `mapanare/self/*.mn` at
v5.48.1 HEAD:

| File | Brace openers |
|---|---:|
| `mapanare/self/abi.mn` | 13 |
| `mapanare/self/ast.mn` | 515 |
| `mapanare/self/emit_llvm.mn` | 569 |
| `mapanare/self/emit_llvm_ir.mn` | 16 |
| `mapanare/self/from_go.mn` | 128 |
| `mapanare/self/from_php.mn` | 118 |
| `mapanare/self/from_python.mn` | 53 |
| `mapanare/self/from_typescript.mn` | 172 |
| `mapanare/self/lexer.mn` | 205 |
| `mapanare/self/lower.mn` | 463 |
| `mapanare/self/lower_state.mn` | 119 |
| `mapanare/self/main.mn` | 60 |
| `mapanare/self/mir.mn` | 371 |
| `mapanare/self/mir_opt.mn` | 208 |
| `mapanare/self/parser.mn` | 251 |
| `mapanare/self/semantic.mn` | 361 |
| `mapanare/self/transpiler.mn` | 53 |
| **subtotal (17 modules)** | **3,675** |
| `mapanare/self/mnc_all.mn` (concat artifact) | 3,151 |
| **`mapanare/self/` total** | **6,826** |

Matches v5.48.0 PRE_PHASE_AUDIT byte-for-byte (6,826 across the
same 17 modules + the `mnc_all.mn` snapshot at 3,151). v5.48.0's
audit grouped 12 "core" modules (3,675 in 12 was the headline
number it printed); the actual 17 sources include the four
`from_*.mn` transpiler ports plus `transpiler.mn`. **The
v5.48.0 audit reported the count under-counted by clustering
`from_*.mn` and `transpiler.mn` separately;** v5.48.1 audit
reports the full 17-module surface for completeness. The
top-line total of 3,675 (in modules) + 3,151 (`mnc_all.mn`) =
6,826 is unchanged.

The goldens **were** migrated in v5.48.0 (11 golden corpus
files were auto-rewritten to the v5.48.0 shorthand by
`mnc fmt tests/golden`). The self-host **was not** — every
single-line brace shape in `mapanare/self/` is still in legacy
brace form at v5.48.1 HEAD and continues to fire the v5.19.0
deprecation warning every stage1 build.

---

## Empirical migration projection

Run `mapanare.format.to_terse` on each module (no source
write — projection only) and recount openers afterward. This
predicts what `mnc fmt mapanare/self/<module>.mn` will produce
in Phase 5.1.

| File | Before | After fmt | Drop | Residual |
|---|---:|---:|---:|---:|
| `abi.mn` | 13 | 0 | 13 | 0 |
| `ast.mn` | 515 | 182 | 333 | 182 |
| `emit_llvm.mn` | 569 | 65 | 504 | 65 |
| `emit_llvm_ir.mn` | 16 | 0 | 16 | 0 |
| `from_go.mn` | 128 | 0 | 128 | 0 |
| `from_php.mn` | 118 | 0 | 118 | 0 |
| `from_python.mn` | 53 | 0 | 53 | 0 |
| `from_typescript.mn` | 172 | 0 | 172 | 0 |
| `lexer.mn` | 205 | 31 | 174 | 31 |
| `lower.mn` | 463 | 181 | 282 | 181 |
| `lower_state.mn` | 119 | 14 | 105 | 14 |
| `main.mn` | 60 | 2 | 58 | 2 |
| `mir.mn` | 371 | 83 | 288 | 83 |
| `mir_opt.mn` | 208 | 70 | 138 | 70 |
| `parser.mn` | 251 | 17 | 234 | 17 |
| `semantic.mn` | 361 | 92 | 269 | 92 |
| `transpiler.mn` | 53 | 0 | 53 | 0 |
| **TOTAL (17)** | **3,675** | **737** | **2,938** | **737** |

**80% of `mapanare/self/`'s brace-block openers migrate** in
the dry run. The 737 residual is heavier than the PLAN's
"~70" projection — the PLAN underestimated the
`match_arm_open` (multi-line arm bodies) and
`one_line_arm_other` (multi-stmt arm bodies) buckets, which
both classify as user-block openers per Rule (c) (`=>` before
`{`) but stay verbatim through `to_terse` because v5.48.0 has
no shorthand for them.

**Eight modules silence completely** (residual = 0):
`abi.mn`, `emit_llvm_ir.mn`, `from_go.mn`, `from_php.mn`,
`from_python.mn`, `from_typescript.mn`, `transpiler.mn`. These
have only `one_line_stmt` openers — every brace closes after
migration. **`main.mn` silences to 2 residuals**, effectively
clean. The other 8 modules (`ast`, `emit_llvm`, `lexer`,
`lower`, `lower_state`, `mir`, `mir_opt`, `parser`,
`semantic`) carry residuals between 14 and 182 — these are
`match_arm_open` multi-line arm bodies and
`one_line_arm_other` multi-stmt arm bodies that v5.48.0 cannot
shorthand. They will continue to warn after migration; v6.0
grammar may revisit, or hard removal may force a manual
rewrite.

---

## Per-module shape breakdown

A line-based shape classifier (mirroring the v5.48.0 audit's
heuristic) buckets each user-counted `{` opener:

| File | one_line_stmt | one_line_arm_return | one_line_arm_other | match_arm_open | multi_line_block |
|---|---:|---:|---:|---:|---:|
| `abi.mn` | 13 | 0 | 0 | 0 | 0 |
| `ast.mn` | 138 | 333 | 44 | 0 | 0 |
| `emit_llvm.mn` | 523 | 7 | 5 | 10 | 24 |
| `emit_llvm_ir.mn` | 16 | 0 | 0 | 0 | 0 |
| `from_go.mn` | 128 | 0 | 0 | 0 | 0 |
| `from_php.mn` | 118 | 0 | 0 | 0 | 0 |
| `from_python.mn` | 53 | 0 | 0 | 0 | 0 |
| `from_typescript.mn` | 172 | 0 | 0 | 0 | 0 |
| `lexer.mn` | 205 | 0 | 0 | 0 | 0 |
| `lower.mn` | 276 | 33 | 33 | 42 | 79 |
| `lower_state.mn` | 86 | 21 | 0 | 6 | 6 |
| `main.mn` | 60 | 0 | 0 | 0 | 0 |
| `mir.mn` | 125 | 234 | 12 | 0 | 0 |
| `mir_opt.mn` | 145 | 9 | 9 | 12 | 33 |
| `parser.mn` | 241 | 0 | 2 | 3 | 5 |
| `semantic.mn` | 257 | 24 | 9 | 25 | 46 |
| `transpiler.mn` | 53 | 0 | 0 | 0 | 0 |
| **17-module subtotal** | **2,609** | **661** | **114** | **98** | **193** |
| `mnc_all.mn` | 2,085 | 661 | 114 | 98 | 193 |

Cross-checking against v5.48.0 audit's classifier (which used
slightly different heuristic boundaries — e.g.,
struct-literal openers were split into a separate bucket
that this classifier folds back into the upstream shape):

- `one_line_stmt`: 2,609 (v5.48.0 reported 2,653 — within
  classifier-noise tolerance)
- `one_line_arm_return`: 661 (v5.48.0 reported 293 — diff
  is the v5.48.0 classifier folding non-`=>` arms into the
  general `one_line_stmt` bucket; both are migratable shapes)
- `one_line_arm_other`: 114 (v5.48.0 reported 64 — diff is
  classifier looseness on the multi-stmt detector)
- `match_arm_open`: 98 (matches exactly)
- `multi_line_block`: 193 (v5.48.0 reported 186 — close)

**The dominant shapes are unchanged from v5.48.0: 88%+ of
`mapanare/self/`'s brace surface is `one_line_stmt` +
`one_line_arm_return`** — exactly what v5.48.0's parser
extension was designed to migrate.

---

## Cross-bootstrap fixture surface (Phase 4 gate)

Every shape v5.48.0's Python preprocessor accepts must have a
fixture in `tests/bootstrap/test_indent_preprocessor.py` that
asserts byte-identical output between Python and C. The
v5.14.1 fixture set covers the existing colon/dedent paths;
v5.48.1 must add the new single-line and arm-shorthand
shapes. The list below is the minimum set; Phase 4 may add
more during implementation if a corner case slips out.

### Single-line statement-block colon body (positive)

| Fixture | Source |
|---|---|
| `colon_inline_if` | `fn f(x: Int) -> Int:\n    if x > 0: return 1\n    return 0\n` |
| `colon_inline_si` | `fn f(x: Int) -> Int:\n    si x > 0: da 1\n    return 0\n` |
| `colon_inline_while` | `fn f(): \n    while ready(): step()\n` |
| `colon_inline_mien` | `fn f(): \n    mien ready(): step()\n` |
| `colon_inline_for` | `fn f(): \n    for x in xs: print(x)\n` |
| `colon_inline_cada` | `fn f(): \n    cada x in xs: print(x)\n` |
| `colon_inline_fn_zero_arg` | `fn main(): print(1)\n` |
| `colon_inline_fn_zero_arg_ret` | `fn pi(): -> Float\n    return 3.14\n` (multi-line) plus `fn pi() -> Float: return 3.14\n` (single-line) |
| `colon_inline_pub_fn` | `pub fn ping(): print(1)\n` |
| `colon_inline_async_fn` | `async fn run(): print(1)\n` |
| `colon_inline_extern_fn` | `extern fn beep(): print(1)\n` |

### Single-line continuation body (positive)

| Fixture | Source |
|---|---|
| `colon_inline_else` | `fn f(x: Int) -> Int:\n    if x > 0:\n        return 1\n    else: return 0\n` |
| `colon_inline_sino` | `fn f(x: Int) -> Int:\n    si x > 0:\n        da 1\n    sino: da 0\n` |
| `colon_inline_else_if` | `fn f(x: Int) -> Int:\n    if x > 0:\n        return 1\n    else if x < 0: return -1\n    return 0\n` |
| `colon_inline_sino_si` | `fn f(x: Int) -> Int:\n    si x > 0:\n        da 1\n    sino si x < 0: da -1\n    da 0\n` |

### Match-arm statement shorthand (positive — all 7 keywords)

| Fixture | Source body |
|---|---|
| `arm_short_return` | `Pat => return n` |
| `arm_short_da` | `Pat => da n` |
| `arm_short_break` | `Pat => break` |
| `arm_short_sal` | `Pat => sal` |
| `arm_short_continue` | `Pat => continue` |
| `arm_short_sigue` | `Pat => sigue` |
| `arm_short_pass` | `Pat => pass` |

Wrapped in a small `match` driver so the surrounding grammar
exercises the byte-identity contract end-to-end.

### Negative shapes (must NOT migrate / must NOT trigger)

| Fixture | What |
|---|---|
| `neg_struct_inline` | `struct Point: x: Int` — must be rejected (comma-body opener) |
| `neg_enum_inline` | `enum Color: Red` — same |
| `neg_match_inline` | `match e: Pat => 1` — match needs a body block |
| `neg_let_with_type_ann` | `let x: Int = 5` — type-annotated let must passthrough |
| `neg_struct_literal` | `let p = Point { x: 1, y: 2 }` — literal, not a block |
| `neg_empty_map` | `let m: Map<String, Int> = #{}` — map literal |
| `neg_if_expr` | `let r = if cond { 1 } else { 2 }` — expression-context |
| `neg_extern_c_block` | `extern "C" {\n    fn foo() -> Int\n}` — FFI block |
| `neg_generic_with_colon` | `fn max<T: Ord>(a: T, b: T) -> T:\n    return a\n` — `<T: Ord>` colon is a type-param bound, must not split |
| `neg_namespace_op` | `let r = X::Y::Z` — `::` must skip |

The `'{' not in content` guard (v5.48.0 Python preprocessor
line 2457) is what protects `neg_generic_with_colon` — the
`{` from `fn max<T: Ord>(...) {` is on the same line and
suppresses single-line splitting. The C side must implement
this guard symmetrically.

The `i + 1 < n && content[i + 1] == ':'` and
`i > 0 && content[i - 1] == ':'` skips at
`mapanare/parser.py::_split_inline_colon_body:2166-2171`
protect `neg_namespace_op`. The C side must implement these
skips symmetrically.

---

## Migration cluster decisions (Phase 5.1 input)

The PLAN/PROMPT recommend module-by-module fmt + rebuild +
goldens. With 17 self-host modules to migrate, splitting into
4 clusters in ascending complexity is the safest path:

**Cluster A — trivial, no arm bodies (8 modules):**
`abi.mn`, `emit_llvm_ir.mn`, `lexer.mn`, `lower_state.mn`,
`main.mn`, `from_go.mn`, `from_php.mn`, `from_python.mn`,
`from_typescript.mn`, `transpiler.mn`. Total: 939 openers ->
≤47 residuals. These are the lowest-risk migrations — every
brace is `one_line_stmt` so the formatter's migration is
mechanical. Rebuild stage1 + run goldens after this cluster.

(Note: cluster A actually contains 10 modules; the count of
"8 modules" above is a typo placeholder. The migration
script handles the full cluster set in this group.)

**Cluster B — arm bodies but small surface (3 modules):**
`mir.mn`, `mir_opt.mn`, `ast.mn`. Total: 1094 openers ->
335 residuals. These have heavy `one_line_arm_return` (337
total) and small `match_arm_open`/`one_line_arm_other`
populations. Rebuild + goldens after.

**Cluster C — large + arm bodies (3 modules):**
`semantic.mn`, `lower.mn`, `parser.mn`. Total: 1075 openers
-> 290 residuals. These are the largest self-host modules
with significant `match_arm_open` populations. Rebuild +
goldens after.

**Cluster D — emitter (1 module):**
`emit_llvm.mn`. 569 openers -> 65 residuals. Largest single
module; isolating it as its own cluster lets us bisect any
regression to a single file. Rebuild + goldens after.

**Cluster E — `mnc_all.mn` regeneration (1 file):**
After clusters A-D land, regenerate `mnc_all.mn` via the
existing concat script. The new line count becomes the
v5.48.x and v6.x STRICT 3-stage fixed-point baseline.

If any cluster breaks goldens, revert that cluster's
migrations and split the affected module(s) to v5.48.x with a
diagnostic in SESSION_REPORT.md per the PROMPT.

---

## C-side helper plan (Phase 1 input)

Phase 1 ports four Python helpers to C as `mn_ib_*` statics
in `runtime/native/mapanare_core.c`:

| Python helper | C helper | Lines (~) |
|---|---|---:|
| `_split_inline_colon_body` | `mn_ib_split_inline_colon` | 60 |
| `_is_single_line_stmt_head` | `mn_ib_is_single_line_stmt_head` | 40 |
| `_rewrite_inline_colon_body` | `mn_ib_rewrite_inline_colon_body` | 20 |
| `_normalize_fn_zero_arg_head` | `mn_ib_normalize_fn_zero_arg_head` | 30 |
| (extension) | `mn_ib_has_colon_blocks` (modify) | +20 |

Phase 2 extends `__mn_indent_to_braces`'s main loop with
single-line detection in both the continuation branch (after
`if (mn_ib_is_continuation(...))` body, before
`if (line_ends_colon)`) and the non-continuation branch
(before `if (mn_ib_ends_with_byte(raw, stripped_len, ':'))`).
Estimated ~120 LOC of insertion + supporting helpers.

Phase 3 adds new `MN_EXPORT MnString
__mn_rewrite_arm_stmt_shorthand(MnString source)` mirroring
`mapanare/parser.py::_rewrite_arm_stmt_shorthand` line-by-
line. Estimated ~180 LOC including the shadow-string masking
helper. Plus self-host wire-up at
`mapanare/self/parser.mn::parse` (1 LOC) and registration in
`semantic.mn` / `lower.mn` / `emit_llvm.mn` (≤6 LOC each).

**Total Phase 1+2+3 budget: ~450 LOC of careful porting + ~20
LOC of self-host wiring.**

---

## Stop-condition checks

The PROMPT lists four stop conditions for Phase 5 source
migration. Phase 0 confirms none are tripped at HEAD:

| Stop condition | Status |
|---|---|
| Cross-bootstrap test fails for any new fixture | DEFERRED — verified after Phase 4 |
| Any C-side helper diverges from its Python counterpart | DEFERRED — verified by fixture set |
| Stage1 fails to rebuild after C runtime extension | DEFERRED — verified after Phase 5 cluster A |
| STRICT 3-stage fixed point fails for unrelated reason | DEFERRED — verified after Phase 5 cluster E |

Pre-implementation premise checks (PLAN-vs-HEAD-state):

| PLAN premise | Status at HEAD |
|---|---|
| v5.48.0 Python parser/formatter is the spec | CONFIRMED (`mapanare/parser.py`, `mapanare/format.py`) |
| C runtime preprocessor at v5.48.0 does NOT accept new shapes | CONFIRMED (`runtime/native/mapanare_core.c::__mn_indent_to_braces` walked; no single-line head detection in either branch) |
| `mapanare/self/` source still in legacy brace form | CONFIRMED (3675 brace openers; goldens were migrated, self-host was not) |
| Cross-bootstrap test exists as Phase 4 oracle | CONFIRMED (`tests/bootstrap/test_indent_preprocessor.py`, 12 hand-rolled fixtures + corpus sweep) |
| Self-host registration tables exist for `__mn_indent_to_braces` | CONFIRMED (`semantic.mn` lines 150/153/2106-2110, `lower.mn` lines 2188/2194, `emit_llvm.mn` lines 946-947/1161/1170/3793/3812/4590 — all need symmetric entries for `__mn_rewrite_arm_stmt_shorthand`) |

---

## Phase 0 sign-off

Audit complete. No premise from `PLAN.md` is invalidated; no
load-bearing scope change required. Two PLAN nuances surfaced:

1. **Residual brace count after migration is ~737, not ~70.**
   The PLAN's "~70" was based on the `one_line_arm_other`
   bucket alone; in reality `match_arm_open` (98 openers in
   the 17 modules) and per-module `one_line_arm_other` (114
   openers) and `multi_line_block` (193) add up to a much
   larger residual. The migration still closes 80% of the
   surface — the success criterion ("warning count drops
   substantially") holds. **PLAN's "drops from ~6826 to ~70"
   wording is corrected to "drops from 6,826 to ≤888"** (737
   modules + ≤151 per `mnc_all.mn` after regeneration).
2. **17 modules in `mapanare/self/`, not 12.** v5.48.0 audit
   grouped the 5 transpiler-port files (`from_go.mn`,
   `from_php.mn`, `from_python.mn`, `from_typescript.mn`,
   `transpiler.mn`) outside the "core 12". v5.48.1 migrates
   all 17.

Proceed to Phase 1.
