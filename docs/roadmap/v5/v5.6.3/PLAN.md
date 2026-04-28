# Mapanare v5.6.3 — "Sh.6 Phase 4: Tensor Slicing + Reductions"

> **Close goldens 52 + 53 by porting Python's range slicing
> (`a[1..3]`), wildcard `_`, 2D slice (`d[0..2, _]`), and reduction
> methods (`.sum()/.mean()/.max()/.min()/.argmax()/.argmin()`) to the
> self-hosted compiler.** Final Sh.6 release — completes the tensor
> feature arc before v5.7.0.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.2 shipped (tensor binops; 65/66 goldens)
**Estimated work:** 1–2 sessions (~4–6 hours). Largest of the
v5.6.x trio — parser gets two new `IndexItem` variants (range,
wildcard) and semantic gains method-call dispatch for tensor
reductions.
**Owner docket:** Sh.6 (opened v4.111.0; Phases 1–3 closed
v5.6.0/5.6.1/5.6.2)

---

## Why this release exists

### The failing goldens

Baseline after v5.6.2:

| Test | mnc-stage1 | bootstrap | Disposition |
|---|---|---|---|
| `52_tensor_slicing` | **FAIL (parse — `_` + `..`)** | OK | **Closes here** |
| `53_linear_regression` | **FAIL (`.sum()` method unresolved)** | OK | **Closes here** |

Exact errors today:

```
# Golden 52
parse error: expected RBRACKET but got COMMA
tests/golden/52_tensor_slicing.mn:0:0: error: Undefined variable '_'
```

```
# Golden 53 — after v5.6.2 ships binops
tests/golden/53_linear_regression.mn: error: unknown method 'sum' on Tensor<Float>
```

Two parser gaps and a method-dispatch gap:

1. **Range items in subscripts:** `a[1..3]`, `a[0..2, _]` — the
   comma-list parser from v5.6.1 must accept `..` (DOTDOT) and `_`
   (underscore wildcard) as subscript items, not full expressions.
2. **Wildcard `_`:** not a variable — a subscript-syntax token for
   "all indices in this dimension." Stub out at lexer/parser level.
3. **Method-call reductions:** `a.sum()` on `Tensor<T>` must
   resolve to `__mn_tensor_sum_{f64,i64}` — method-call dispatch
   in `semantic.mn` + `lower.mn`.

### Python references

- Slicing: `mapanare/lower.py:2788-2835` — `_lower_tensor_slice`
- Reductions: `mapanare/lower.py:2503-2522` inside
  `_lower_method_call`
- Parser: `mapanare/parser.py` — `IndexItem` with `kind` field in
  `{"scalar", "range", "wildcard"}`
- Grammar: `mapanare/mapanare.lark` — `index_item` production with
  range + wildcard alternates

### Runtime state

All reduction fns already exist:

```
__mn_tensor_sum_f64     __mn_tensor_sum_i64
__mn_tensor_mean_f64    (no mean_i64 — only f64)
__mn_tensor_max_f64     __mn_tensor_max_i64
__mn_tensor_min_f64     __mn_tensor_min_i64
__mn_tensor_argmax_f64  __mn_tensor_argmax_i64
__mn_tensor_argmin_f64  __mn_tensor_argmin_i64
```

`__mn_tensor_slice(tensor, starts..., ends..., rank)` also exists
(`runtime/native/mapanare_gpu_builtins.c:753`).

### Sizing

| File | ~LOC |
|---|---:|
| `mapanare/self/lexer.mn` — recognize `_` as `UNDERSCORE` when standalone (not identifier) | ~15 |
| `mapanare/self/parser.mn` — `IndexItem` AST + parse range `..` + wildcard `_` in subscript | ~90 |
| `mapanare/self/ast.mn` — `IndexItem` struct or enum variant + accessors | ~50 |
| `mapanare/self/semantic.mn` — tensor method-call dispatch (6 reductions) + slice result type | ~60 |
| `mapanare/self/lower.mn` — `lower_tensor_slice` + tensor method-call dispatch + Range-inside-subscript handling | ~120 |
| `mapanare/self/emit_llvm.mn` — 11 reduction runtime decls + `__mn_tensor_slice` decl | ~40 |
| Tests | ~80 |
| **Total** | **~455** |

Exceeds v5.6.1's budget — justified: this is the feature that finally
enables tensor slicing syntax (`..` inside `[...]`) and method calls
on tensors.

---

## Scope

### What ships

#### 9.3a — Lexer: `_` as `UNDERSCORE` token in subscript context

The simpler option: always lex `_` as a dedicated `UNDERSCORE`
token when it appears standalone (not prefixed with a letter). The
parser checks context — in subscripts, it's a wildcard; in a `let _
= ...`, it's a throwaway binding; in patterns, it's pattern-any.
Mapanare already treats `_` as a pattern wildcard — confirm
there's no regression.

Grep first:

```bash
grep -n '"_"\|UNDERSCORE\|is_underscore' mapanare/self/lexer.mn
grep -n '"_"\|UNDERSCORE' mapanare/self/parser.mn
```

If lexer currently returns `_` as `NAME`, edit to emit `UNDERSCORE`
for standalone `_`. Add token-type handling in parser where `NAME`
previously caught wildcard.

#### 9.3b — Parser: `IndexItem` AST + range + wildcard in subscript

New AST node:

```mn
// ast.mn
struct IndexItem {
    kind: String,   // "scalar" | "range" | "wildcard"
    expr: Expr,     // populated for "scalar"
    start: Expr,    // populated for "range" (may be NoneLit)
    end: Expr,      // populated for "range" (may be NoneLit)
}
```

Or represent as `enum` variants; choose whichever matches existing
patterns in `ast.mn`.

Parser: the v5.6.1 comma-loop LBRACKET branch becomes:

```mn
if tt == "LBRACKET" {
    p = p + 1
    let mut items: List<IndexItem> = []
    let first: IndexItem = parse_index_item(tokens, p, filename)
    p = first.pos
    items.push(first.item)
    while peek_type(tokens, p) == "COMMA" {
        p = p + 1
        let nxt: IndexItem = parse_index_item(tokens, p, filename)
        p = nxt.pos
        items.push(nxt.item)
    }
    p = expect(tokens, p, "RBRACKET")
    // All-scalar + single-item → single-subscript path
    if len(items) == 1 && items[0].kind == "scalar" {
        left = Expr::Index(left, items[0].expr)
    } else if all_scalar(items) {
        left = Expr::TensorIndex(left, scalar_exprs(items))
    } else {
        left = Expr::TensorSlice(left, items)
    }
}

fn parse_index_item(tokens, pos, filename) -> IndexItemResult {
    // Check for wildcard
    if peek_type(tokens, pos) == "UNDERSCORE" {
        return wildcard_item(pos + 1)
    }
    // Check for prefix range: ..end
    if peek_type(tokens, pos) == "DOTDOT" {
        let end_r = parse_expr(tokens, pos + 1, filename, 0)
        return range_item(NoneLit, end_r.expr, end_r.pos)
    }
    // Otherwise parse expression, then check for DOTDOT
    let first = parse_expr(tokens, pos, filename, 0)
    if peek_type(tokens, first.pos) == "DOTDOT" {
        let after_dd = first.pos + 1
        // ..end? or open-ended a..
        if peek_type(tokens, after_dd) == "COMMA" || peek_type(tokens, after_dd) == "RBRACKET" {
            return range_item(first.expr, NoneLit, after_dd)
        }
        let end_r = parse_expr(tokens, after_dd, filename, 0)
        return range_item(first.expr, end_r.expr, end_r.pos)
    }
    return scalar_item(first.expr, first.pos)
}
```

`Expr::TensorSlice(Expr, List<IndexItem>)` — new AST variant for
subscripts that mix ranges/wildcards with scalars.

#### 9.3c — Semantic: slice result type + tensor method dispatch

**Slice result type:** `a[1..3]` on `Tensor<T>` is `Tensor<T>`. Add
a `TensorSlice` case in `infer_expr`.

**Method dispatch on tensors:** Add in method-call inference:

```mn
if obj_ty is Tensor<T> && method in {"sum", "mean", "max", "min",
                                     "argmax", "argmin"} {
    let elem_kind = tensor_elem_kind(obj_ty)
    // Scalar reductions: sum/mean/max/min return element type
    if method == "sum" || method == "max" || method == "min" {
        return if elem_kind == "Int" { int_type() } else { float_type() }
    }
    if method == "mean" {
        return float_type()  // mean always returns Float (no i64 mean)
    }
    // Index reductions: argmax/argmin return Int
    return int_type()
}
```

Register these builtins in `register_builtins` so they're known at
name-resolution time. Also add `is_tensor_reduction_method(name)`
helper.

#### 9.3d — Lower: slice + reduction

**Slice:**

```mn
fn lower_tensor_slice(st: LowerState, obj: Expr, items: List<IndexItem>) -> LowerResult {
    let obj_r = lower_expr(st, obj)
    let mut s = obj_r.state
    let rank = len(items)
    let mut starts: List<Value> = []
    let mut ends: List<Value> = []

    for i in 0..rank {
        let it = items[i]
        if it.kind == "range" {
            let start_v = if is_none_lit(it.start) { const_int_val(s, 0) } else {
                let r = lower_expr(s, it.start); s = r.state; r.value
            }
            let end_v = if is_none_lit(it.end) { const_int_val(s, 0) } else {
                let r = lower_expr(s, it.end); s = r.state; r.value
            }
            starts.push(start_v)
            ends.push(end_v)
        } else if it.kind == "wildcard" {
            starts.push(const_int_val(s, 0))
            // end = tensor_shape_dim(obj, i)
            let dim_v = const_int_val(s, i)
            let shape_dest = make_value_typed(s, mir_int(), "sdim")
            s = emit_instr(s, Instruction::Call(shape_dest, "tensor_shape_dim", [obj_r.value, dim_v]))
            ends.push(shape_dest)
        } else {
            // scalar — treat as [k, k+1]
            let r = lower_expr(s, it.expr); s = r.state
            starts.push(r.value)
            let one = const_int_val(s, 1)
            let end_dest = make_value_typed(s, mir_int(), "send")
            s = emit_instr(s, Instruction::BinOp(end_dest, "+", r.value, one))
            ends.push(end_dest)
        }
    }

    let dest = make_value_typed(s, obj_r.value.ty, "tslice")
    let rank_val = const_int_val(s, rank)
    let args = [obj_r.value] + starts + ends + [rank_val]
    s = emit_instr(s, Instruction::Call(dest, "__mn_tensor_slice", args))
    return new_lower_result(dest, s)
}
```

**Reductions:** in method-call lowering, tensor reductions route to
the matching runtime fn:

```mn
if is_tensor_reduction_method(method) && is_tensor_value(obj_r.value) {
    let elem_kind = tensor_elem_kind_of(obj_r.value)
    let ty_suffix = if elem_kind == "Int" { "i64" } else { "f64" }
    let fn_name = "__mn_tensor_" + method + "_" + ty_suffix
    let ret_ty = reduction_return_type(method, elem_kind)
    let dest = make_value_typed(s, ret_ty, "tred")
    s = emit_instr(s, Instruction::Call(dest, fn_name, [obj_r.value]))
    return new_lower_result(dest, s)
}
```

#### 9.3e — Emit: runtime declarations

```
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
s = declare_runtime_fn(s, "__mn_tensor_slice", "ptr", "ptr, i64, ...")
s = declare_runtime_fn(s, "tensor_shape_dim", "i64", "ptr, i64")
```

11 reductions + slice + `tensor_shape_dim` (already declared? check
before duplicating). Matching `runtime_fn_attrs` rows.

### What does NOT ship

- **Stepped slicing `a[0..10:2]`.** Not in the Mapanare surface;
  Python doesn't do this either. v5.x feature track or v6.0.
- **Negative indices `a[-1]`.** Python handles; not in the test
  corpus for this release.
- **Multi-dim reductions `.sum(axis=0)`.** Corpus doesn't test it.
- **`a[...]` ellipsis.** Not in the grammar.
- **Mutable slices (view semantics).** Slices are copies in
  Mapanare's runtime; no view type.

---

## Exit criteria

1. `mnc-stage1` compiles both `52_tensor_slicing.mn` and
   `53_linear_regression.mn` clean.
2. `llvm-as` accepts emitted IR for both.
3. `lli` output byte-identical to Python bootstrap for both:

   - **52:** `15 3 5 1 4 0 60 30 1 2 20 30 2 6`
   - **53:** `w = <approaching 2.0> / b = <approaching 1.0> /
     converging` (use the exact bootstrap output since
     floating-point formatting must match)

4. Harness: **65/66 → 66/66 — first time ever**.
5. All v5.6.0–v5.6.2 tensor goldens still pass.
6. stage2.ll `llvm-as` clean; self-hosting preserved.
7. `make lint` clean; `check_struct_registry.py` clean.
8. `PARITY_GAPS.md` — Sh.6 moves to Historical (all four phases
   closed).
9. README goldens badge reads **66/66** (all four language
   variants).

---

## Design decisions

### D1 — Introduce `IndexItem` AST struct

v5.6.1 avoided `IndexItem` and used `List<Expr>`. v5.6.3 needs the
range + wildcard variants; `List<Expr>` can't represent those. Go
ahead and introduce `IndexItem` — it's the smallest surface that
matches Python's AST. The alternative (separate `TensorRange`,
`TensorWildcard` AST nodes at Expr level) bloats the expr-kind
count without helping lower.

### D2 — Range AST shared with existing `RangeExpr`?

Mapanare already has `Expr::RangeExpr` for `for x in 0..10`. Reusing
it for subscript ranges would work syntactically but conflate two
distinct roles: `RangeExpr` lowers to `__mn_range(start, end)` for
iterators; subscript ranges need `(start, end)` unpacked for
`__mn_tensor_slice`. Keep them separate: `IndexItem.kind == "range"`
with distinct `start` / `end` fields avoids the unwrap.

### D3 — Wildcard `_` as `UNDERSCORE` token, not identifier

Mapanare pattern-matching already treats `_` as wildcard. Lexing
standalone `_` as `UNDERSCORE` (not `NAME`) means parse sites decide
context: subscripts, patterns, or throwaway bindings. A single
lexer edit, zero semantic confusion. Python does the same
(`mapanare.lark`'s `_` rule).

### D4 — Slice return type — `Tensor<T>` (same as input)

`a[1..3]` is a 1D slice of a 1D tensor; `d[0..2, _]` is a 2D slice
of a 2D tensor. Rank preserved on wildcard/range dims; collapsed
on scalar dims. For now, return `Tensor<T>` with the same T and
leave rank-tracking to the runtime. The test corpus doesn't require
compile-time rank knowledge.

### D5 — Design context: how other languages do slicing + reductions

- **NumPy:** `a[1:3]`, `a[:, 1:3]`, `a[...]` ellipsis, boolean
  masks, fancy indexing. `.sum()`, `.mean()`, `.argmax()` — full
  stats library.
- **Rust ndarray:** `s![1..3, ..]` macro for slicing. Reductions as
  `.sum()`, `.mean()`, `.fold()`. Explicit `axis` arg for
  multi-dim reductions.
- **Julia:** `a[1:3, :]` — range + `:` wildcard. `sum(a, dims=2)`.
  Identical to Mapanare's chosen surface with `_` replacing `:`.
- **Go gonum:** slicing via method `.Slice(r1, r2, c1, c2)` —
  explicit, no syntax sugar. Reductions via separate packages.
- **R:** `a[1:3, ]` — trailing empty = all cols. The shortest
  wildcard syntax anywhere.
- **Swift:** range indexing `a[1..<3]`. Reductions via
  `.reduce(_:_:)`.

Mapanare picked `a[1..3, _]` — closest to Julia, with `_` for
wildcard to match pattern-match consistency. Syntax set in
v4.45.0; we finish the plumbing here.

### D6 — `.sum()` over tensor locals may leak until v5.6.x

Reductions return scalar (not tensor) — no allocation to free. Safe.
Slices return a fresh tensor — check drop-glue (same concern as
v5.6.2's binops). If v5.6.2 added `emit_track_tensor`, reuse it;
if v5.6.2 baseline-gated, update baseline.

---

## Risks

- **R1 — `UNDERSCORE` token lex change breaks existing uses.**
  Patterns (`match x { _ => ... }`) and throwaway bindings
  (`let _ = ...`) both consume `_`. Lexer switch must not break
  either. Mitigation: targeted pytest for each `_`-consuming site
  before committing lexer change.
- **R2 — Parser grammar ambiguity.** `a[b..]` — is `b` a variable
  (scalar) or a range start with no end? Decision: trailing
  `DOTDOT` with no expression is a range with open end (`..`), which
  means "to end of dim" at runtime. Match Python's behavior.
- **R3 — Method dispatch plumbing.** Self-hosted may not yet have a
  general "method call on tensor" path. Grep for how method calls on
  `List` / `String` are dispatched; mirror the pattern for `Tensor`.
  If the abstraction doesn't exist, add a minimal one.
- **R4 — Slice retains drop-glue semantics.** `let s = a[1..3]`
  allocates; scope-exit must free. See D6.
- **R5 — 53_linear_regression output is float-formatting dependent.**
  Python bootstrap's `str(Float)` formatter output must match
  self-hosted's. If 53 mismatches on `w = 1.9876543...` vs
  `w = 1.987654...`, check `__mn_str_from_float` parity. Likely
  already identical (same runtime fn) but verify.
- **R6 — stage2.ll line-count jump.** Adding `IndexItem` struct +
  parser + lower paths might shift self-compilation output. Verify
  fixed-point NEAR; if BROKEN, investigate dominance / PHI issues
  mirror v5.6.0's workaround pattern.

---

## What NOT to do

- **Do not add stepped slicing (`a[::2]`).** Not in the surface.
- **Do not add boolean masking (`a[a > 0]`).** Python doesn't do
  it either.
- **Do not introduce a tensor `View` type.** Slices are copies —
  runtime is already copying. Views are v6.0.
- **Do not skip the harness 66/66 verification.** This is the
  headline — the first time ever. Confirm visually.
- **Do not bump to 66/66 without all 3 parts shipping.** Slicing +
  reductions together or not at all. Partial would leave 52 or 53
  still failing.
- **Do not touch `emit_llvm_text.py`.** Python works.
- **Do not "improve" slice to support stride.** Out of scope.
- **Do not refactor `IndexItem` into something fancier than the
  Python AST.** Mirror exactly — audits across the two sides become
  trivial.
