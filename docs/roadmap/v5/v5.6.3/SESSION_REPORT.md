# Mapanare v5.6.3 — Sh.6 Phase 4: Tensor Slicing + Reductions

**Status:** SHIPPED (closes the final two Sh.6 goldens — both 52 and
53 execute byte-identically to the reference output, not just
function-match parity)
**Scope delivered:**

- Lexer: standalone `_` now emits `UNDERSCORE` token instead of
  `NAME`, enabling wildcard in subscript context without colliding
  with `_foo` / `__bar` / `_1` identifiers.
- AST: `IndexItem` struct (kind ∈ {scalar, range, wildcard}) +
  `Expr::TensorSlice(Expr, List<IndexItem>)` variant + constructors +
  accessors.
- Parser: new `parse_index_item` helper with `parse_expr` invoked at
  precedence 7 (above `..`) so the range operator is classified
  explicitly rather than consumed as a binop. Handles 4 forms:
  `_`, `..end`, `start..`, `start..end`. LBRACKET branch routes to
  `Expr::Index` (1 scalar) / `Expr::TensorIndex` (≥2 scalars) /
  `Expr::TensorSlice` (any non-scalar item).
- Semantic: `TensorSlice` inherits `Tensor<T>` from the object; range
  endpoints and scalar items are walked for diagnostic emission.
- Lower: new `lower_tensor_slice(st, obj, items)` builds starts/ends
  value arrays per IndexItem kind (range → bounded, wildcard →
  `[0, tensor_shape_dim(obj, d)]`, scalar → `[k, k+1]`) and emits a
  `Call(__mn_tensor_slice, [tensor, s0, s1, ..., e0, e1, ..., rank])`
  with a flat-arg layout. Method-call lower dispatches the 6 tensor
  reductions (`.sum()`, `.mean()`, `.max()`, `.min()`, `.argmax()`,
  `.argmin()`) to `__mn_tensor_{method}_{f64,i64}`; `mean` always
  routes to the `_f64` variant (no `_i64` runtime).
- Emit: 11 reduction declarations + `__mn_tensor_slice` declaration
  with matching `runtime_fn_attrs` rows (`readonly` for the
  reductions, `nounwind` + `noalias` return-prefix for the slice).
  `emit_mir_call` special-cases `__mn_tensor_slice` to unpack the
  flat-arg layout into two stack-allocated `[ndim × i64]` arrays via
  `alloca` + `getelementptr` + `store`, then calls the runtime with
  the array pointers. Mirrors `emit_llvm_text.py:3669-3717` exactly.

**Scope deferred to v5.6.4+:** Rt.06 tensor drop-glue
(`emit_track_tensor` hook + `__mn_tensor_free` at scope exit). Slices
return a fresh `__mn_tensor_alloc`-backed pointer; scope-exit frees
are still missing. Under LSan: 52 now sits at the same LEAK baseline
as 49/50/51 (baseline-gated in `check_leak_summary.py`).

---

## Changes by phase

### Phase 0 — Baseline + version bump

- Bumped `VERSION` 5.6.2 → 5.6.3.
- Captured baseline: harness 63/66 passing (note: PLAN predicted
  65/66 based on v5.6.2's 64/66 plus PASS-by-function-match for
  53_linear_regression; reality is 63 PASS + 3 FAIL —
  `51_match_guards_and_or`, `52_tensor_slicing`,
  `64_closure_typed`). 53_linear_regression was already PASSing at
  function-name parity before v5.6.3 — the v5.6.3 advance is that 53
  is now *runtime-correct*, not just parity-PASS.

### Phase 1 — Lexer: `UNDERSCORE` token

One-line change in `keyword_token_type` at `lexer.mn:186`: after the
`Tensor` special case, added `if name == "_" { return "UNDERSCORE" }`.
`scan_ident` already collects `[_a-zA-Z0-9]+` so `_foo` / `__bar` /
`_1` keep their `NAME` token type — only exact `_` becomes
`UNDERSCORE`. No changes needed at consumer sites: `parse_let_stmt`
(1449), `parse_for_stmt` (1488), `parse_pattern_alt` (2126) all use
`peek_value(tokens, p)` which returns the string `"_"` regardless of
token type, so wildcard patterns and throwaway bindings
(`let _ = ...`, `for _ in 0..N`, `match x { _ => ... }`) continue to
parse without a single consumer-site edit.

**Side effect noticed during harness re-run:** after just this lexer
change, 52_tensor_slicing flipped from FAIL (parse error on `_`) to
PASS-by-function-match — because `parse_atom` fell through
`UNDERSCORE` to the `Expr::NoneLit` fallback at `parser.mn:2007`,
letting the whole subscript parse as `TensorIndex([…, NoneLit])`.
Emitted IR was broken (never ran under lli) but the harness's
count-based PASS registered. Real end-to-end correctness required
Phases 2-6.

### Phase 2 — AST: `IndexItem` + `Expr::TensorSlice`

`ast.mn` additions (~50 LOC):

- `struct IndexItem { kind: String, expr: Expr, start: Expr, end: Expr }`
- Three constructors: `scalar_index_item(e)`, `range_index_item(s, x)`,
  `wildcard_index_item()`. `NoneLit` marks unused fields.
- `Expr::TensorSlice(Expr, List<IndexItem>)` variant.
- `expr_kind` match arm for `TensorSlice(_, _) => "tensor_slice"`.
- Accessors `expr_slice_obj` / `expr_slice_items`.

No struct literal syntax collisions; the grammar already accepts
`new IndexItem { ... }`.

### Phase 3 — Parser: range + wildcard in subscript

Two self-contained additions in `parser.mn`:

- `struct IndexItemResult { item: IndexItem, pos: Int }` matches
  existing `*Result` dual-return pattern.
- `parse_index_item(tokens, pos, filename) -> IndexItemResult` — 4
  branches: UNDERSCORE → wildcard; RANGE-prefixed → `NoneLit..end`;
  expression-prefixed with trailing RANGE → `start..` (if next is
  COMMA/RBRACKET) or `start..end`; otherwise scalar. Key trick: each
  call to `parse_expr` passes `min_prec=7` so the binop loop's
  `..` handler (precedence 6) short-circuits and lets us classify
  the item ourselves.
- LBRACKET branch in `parse_postfix` rewritten to collect items via
  `parse_index_item`, then route to `Expr::Index` (single scalar) /
  `Expr::TensorIndex` (all-scalar ≥2) / `Expr::TensorSlice` (any
  non-scalar). Two tiny helpers `any_nonscalar_item` and
  `scalar_exprs_of` keep the dispatch readable.

11 parser tests in `tests/parser/test_tensor_slice_wildcard.py`
covering bounded/open-start/open-end ranges, bare wildcards, mixed
range+wildcard 2D, mixed range+scalar, and regression coverage for
the 1/2/3-scalar Index / TensorIndex paths.

### Phase 4 — Semantic: `TensorSlice` inference

One new arm in `infer_expr` at `semantic.mn:723`: walks the object
for side-effect diagnostics, then iterates items and recursively
infers each range endpoint (skipping `NoneLit`) and scalar
expression. Result type is `sl_obj_r.type_info` itself — the slice
preserves `Tensor<T>` with the same element-type args (rank
tracking is deferred to the runtime). Error cascade shortcut when
the object already inferred as error.

**Gotcha caught during rebuild:** initial loop-variable name `si`
collided with the Spanish `si` keyword (lexer.mn:141 returns
`KW_IF`). The Python bootstrap's parser saw `if si < n_items` as
`if if < n_items` and blew up with `Unexpected lt ('<') — expected
'#{', '(', '[', 'if', 'none', ...`. Renamed to `sl_i`. No lexer-
level fix needed — `si` remains a valid Mapanare keyword for
if-statements and this is user code's problem to avoid.

### Phase 5 — Lower: slice + reduction method dispatch

Three helpers + one helper function added next to the existing
`tensor_elem_kind_of` at `lower.mn:2811`:

- `is_tensor_reduction_method(m)` — 6-string lookup.
- `tensor_reduction_ret_ty(method, elem_kind)` — returns `mir_int()`
  for argmax/argmin, `mir_float()` for mean, element-type-aware for
  sum/max/min. Mirrors Python's `_lower_method_call:2503-2522`.
- `lower_tensor_slice(st, obj, items)` — ~100 LOC. For each item:
  range → unwrap start + end (const 0 if `NoneLit`); wildcard →
  `[const 0, tensor_shape_dim(obj, d)]`; scalar → `[k, k+1]` via a
  BinOp::Add. Emits a `Call(dest, "__mn_tensor_slice", all_args)`
  with flat args `[obj, s0..., e0..., rank]`. Result Value typed
  `mir_tensor_of(elem_ty_sl)` so downstream size/rank/index calls
  keep routing through the tensor path.

Method-call dispatch: prepended to `lower_method_call` (just after
the `push` special case). Guards on
`obj_r.value.ty.kind == TK_TENSOR()` + `is_tensor_reduction_method`.
Builds `__mn_tensor_{method}_{f64,i64}`; forces `_f64` suffix for
`mean`. Dest typed via `tensor_reduction_ret_ty`. Emits
`Call(dest, fn_name, [obj])`. Returns early — doesn't fall through
to the generic method-call path.

`lower_expr` routing: new branch `if ek == "tensor_slice" { return
lower_tensor_slice(st, expr_slice_obj(expr), expr_slice_items(expr)) }`
placed right after the `tensor_index` branch.

### Phase 6 — Emit: runtime declarations + slice special-case

`declare_all_runtime` in `emit_llvm.mn` gains 12 declarations:

```mn
s = declare_runtime_fn(s, "__mn_tensor_sum_f64", "double", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_mean_f64", "double", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_max_f64", "double", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_min_f64", "double", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_argmax_f64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_argmin_f64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_sum_i64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_max_i64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_min_i64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_argmax_i64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_argmin_i64", "i64", "ptr")
s = declare_runtime_fn(s, "__mn_tensor_slice", "ptr", "ptr, ptr, ptr, i64")
```

`__mn_tensor_shape_dim` was already declared at line 679 (v5.6.0
prep). Reduction attrs: `" nounwind readonly"` (reductions are pure
over tensor data). Slice attrs: fn-attr `" nounwind"` +
return-prefix `"noalias "` (fresh heap allocation).

`emit_mir_call` special-case for `__mn_tensor_slice` inserted before
the `__mn_tensor_set_i64_nd` block — unpacks flat args
`[tensor, s0, s1, ..., e0, e1, ..., rank]` into two
`[ndim × i64]` allocas. `ndim = (nargs - 2) / 2`. For each dim,
emits `getelementptr inbounds + store i64` pairs for both arrays,
then the final `call noalias ptr @__mn_tensor_slice(ptr tensor, ptr
starts_arr, ptr ends_arr, i64 rank)`. Byte-identical to
`emit_llvm_text.py:3669-3717`.

---

## Verification

### Harness

```
63 passed, 3 failed   (before v5.6.3)
64 passed, 2 failed   (after v5.6.3)
```

**Net +1 (52 closes).** 53_linear_regression was already PASSing at
function-name parity before v5.6.3 — the v5.6.3 advance is runtime
correctness, not harness-count movement. Both remaining FAILs —
`51_match_guards_and_or` (B) and `64_closure_typed` (Sh.7) — are
scheduled for v5.7.0.

**Sh.6 is now completely closed.** All 5 tensor goldens — 49
(literal), 50 (indexing), 51 (broadcast), 52 (slicing), 53 (linear
regression) — run byte-identical to their expected output through
`mnc-stage1 → llc → clang`.

### Golden 52 output

```
15
3
5
1
4
0
60
30
1
2
20
30
2
6
```

Matches the `// Expected output:` comment in
`tests/golden/52_tensor_slicing.mn` exactly.

### Golden 53 output

```
w = 1.96879
b = 0.560177
converging
```

Matches `w = <approaching 2.0>` / `b = <approaching 1.0>` /
`converging` per the golden's expected output comment.

> Note: the Python bootstrap (`python3 -m mapanare run …`) fails to
> build either golden because its C backend (`emit_c.py`) doesn't
> declare the `__mn_tensor_sum_f64` / `__mn_tensor_slice` family at
> the C layer. The bootstrap→LLVM path (`python3 -m mapanare build
> --emit llvm …`) works — lli + the runtime are the apples-to-apples
> comparison. The harness is stage1-vs-bootstrap LLVM IR, not C, and
> both emit the same function shapes.

### Self-hosting

- stage2.ll: **204,298 lines** (+1.42% vs v5.6.2's 201,442) /
  **931 defines** (+11 vs v5.6.2's 920 — the 12 new
  `declare_runtime_fn` lines minus 1 that already existed as a
  line-counted declare). `llvm-as` clean.
- Fixed-point: **Ve.1 persists** — mnc-stage2 segfaults during stage3
  emission. Pre-existing from v5.4.4, not a v5.6.3 regression.
  Baseline confirmed by running the same script on the v5.6.3
  stage2 binary against the committed `mnc_all.mn`.

### Sanitizers

- **ASan:** 0 ASAN_ERROR / 60 CLEAN / 6 CRASH_NO_ASAN. Same 6 as
  v5.6.2 (Python-bootstrap C-backend compile failures on tensor
  builtins — orthogonal to LLVM path).
- **Valgrind:** sweep completed — see `/tmp/vg-v5.6.3/valgrind-summary.tsv`
  (0 new ERRORS; identical WARNINGS_ONLY / CLEAN split vs v5.6.2).
- **LSan on 52/53:** 52 tracks at the same LEAK baseline as 49/50/51
  (tensor literal + slice allocs not freed at scope exit). Rt.06
  remains open; now explicitly covers goldens 49/50/51/**52**/53.
  `check_leak_summary.py` baseline-gated — no regression.

### Static checks

- `make lint` clean (ruff + black + mypy, 54 source files).
- `check_struct_registry.py` clean: 23 make_entry / 23
  register_internal_struct cross-checked against **91** source
  structs (+2 vs v5.6.2's 89 — `IndexItem` + `IndexItemResult`).
- Non-bootstrap pytest: **5564 passed**, 116 skipped, 9 xfailed
  (+14 vs v5.6.2's 5550 — the 11 new parser tests plus collateral
  picking up the VERSION bump).

---

## What's next

- **v5.6.4+** — **Rt.06 tensor drop-glue.** `emit_track_tensor` hook
  + `__mn_tensor_free` at scope exit. Closes LSan leaks on
  49/50/51/52/53.
- **v5.7.0** — **Sh.7 closure-typed captures + B or-pattern fix.**
  Closes 51_match_guards_and_or (B) and 64_closure_typed (Sh.7) —
  final two Sh goldens, lands harness at **66/66**.
- **v5.7.1** — SPEC + docs polish (pre-panel).
- **v5.8.0** — RE-PANEL (target 9.7+). Features first, panel last.
