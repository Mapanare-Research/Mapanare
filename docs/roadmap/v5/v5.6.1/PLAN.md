# Mapanare v5.6.1 — "Sh.6 Phase 2: Multi-Dim Indexing (a[i, j])"

> **Close golden 50 (`50_tensor_indexing`) by porting Python's
> `a[i, j]` / `a[i, j, k]` read-and-write tensor indexing to the
> self-hosted compiler.** First of the three `v5.6.x` Sh.6
> continuations that close the tensor feature arc started in v5.6.0.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.0 shipped (tensor literal parser + golden 49)
**Estimated work:** 1 session (~3–5 hours). Medium — parser surgery +
matched lower/semantic/emit wiring.
**Owner docket:** Sh.6 (opened v4.111.0; Phase 1 closed v5.6.0)

---

## Why this release exists

### The failing golden

Baseline after v5.6.0 (one session before v5.6.1 starts):

| Test | mnc-stage1 | bootstrap | v5.6.0 disposition |
|---|---|---|---|
| `49_tensor_literal` | PASS | OK | Closed Phase 1 |
| `50_tensor_indexing` | **FAIL (parse)** | OK | **Closes here** |
| `51_tensor_broadcast` | FAIL (emit — ptr/i64 mismatch) | OK | v5.6.2 |
| `52_tensor_slicing` | FAIL (parse — `_`, `..`) | OK | v5.6.3 |
| `53_linear_regression` | FAIL (emit — tensor binop + `.sum()`) | OK | v5.6.2/v5.6.3 |

Exact `mnc-stage1` error on golden 50:

```
parse error: expected RBRACKET but got COMMA
parse error: expected RPAREN but got DEC_INT
```

The offender is the subscript grammar at `mapanare/self/parser.mn:1672`:

```mn
if tt == "LBRACKET" {
    p = p + 1
    let idx_r: ExprResult = parse_expr(tokens, p, filename, 0)
    p = idx_r.pos
    p = expect(tokens, p, "RBRACKET")
    left = Expr::Index(left, idx_r.expr)
}
```

Single expression between `[` and `]`. No comma loop. Meanwhile
`Expr::TensorIndex(Expr, List<Expr>)` exists at `ast.mn:81` — declared
by a prior unrelated commit, never wired.

### Python reference

`mapanare/lower.py:2750-2786` — `_lower_tensor_get` / `_lower_tensor_set`:

```python
# Tensor: emit Call to __mn_tensor_get_*_nd (v4.43.0)
if obj_kind == TypeKind.TENSOR:
    return self._lower_tensor_get(obj, indices)
```

Both call into the variadic runtime:

```
__mn_tensor_get_f64_nd(tensor, rank, i0, i1, ...) -> f64
__mn_tensor_get_i64_nd(tensor, rank, i0, i1, ...) -> i64
__mn_tensor_set_f64_nd(tensor, rank, i0, i1, ..., val)
__mn_tensor_set_i64_nd(tensor, rank, i0, i1, ..., val)
```

C runtime has all four (`runtime/native/mapanare_gpu_builtins.c:378`
for `get_f64_nd`, and matching siblings).

### Sizing

Roughly:

| File | ~LOC |
|---|---:|
| `mapanare/self/parser.mn` — multi-index comma loop in `LBRACKET` branch | ~20 |
| `mapanare/self/semantic.mn` — `TensorIndex` type inference + 4 new builtins | ~35 |
| `mapanare/self/lower.mn` — `lower_tensor_index_get` + `lower_tensor_index_set` helpers + `TensorIndex` dispatch in `lower_expr` + IndexSet-when-target=TensorIndex branch | ~80 |
| `mapanare/self/emit_llvm.mn` — 4 `__mn_tensor_{get,set}_{f64,i64}_nd` declarations + runtime_fn_attrs rows + variadic call routing in `lower_call_by_name` if lowered that way | ~40 |
| Tests | ~60 |
| **Total** | **~235** |

Under v5.6.0's ~290-LOC budget. Comfortable.

---

## Scope

### What ships

#### 9.1a — Parser: comma-separated index list

`parser.mn` postfix loop at the `LBRACKET` branch. After the first
`parse_expr`, loop while the next token is `COMMA`; collect a
`List<Expr>`. On exit:

- If length == 1: keep `Expr::Index(left, idx)` for list/map/string
  single-subscript (no behavior change for non-tensor).
- If length >= 2: emit `Expr::TensorIndex(left, indices)`.

Rationale for the branch: `TensorIndex` only makes sense for Tensor
objects. Overloading `Expr::Index` would force lower/semantic to
inspect the operand's type *before* deciding which AST variant to
consume. Keeping two variants is cheaper. Python bootstrap has
`IndexItem`-list-of-size-N as a single form; `mn` AST doesn't need
that generality until v5.6.3's slicing arrives.

#### 9.1b — Semantic: `TensorIndex` type inference

`semantic.mn`:

- Add case to `infer_expr` for `TensorIndex(obj, indices)`: element
  type is the tensor's T; walk `obj` type, confirm TENSOR kind,
  return `<T>`.
- Register 4 runtime builtins (`tensor_get_f64_nd`, `tensor_get_i64_nd`,
  `tensor_set_f64_nd`, `tensor_set_i64_nd`) as internal — no
  user-facing name. Not required if lower.mn skips straight to
  `__mn_tensor_*_nd` without a semantic-layer builtin, which matches
  v5.6.0's pattern for `tensor_get_f64`. We'll confirm in
  implementation — may only need the dispatch in lower/emit.

#### 9.1c — Lower: `TensorIndex` → variadic call

`lower.mn::lower_expr` new case `TensorIndex(obj, indices)`:

```
let obj_r = lower_expr(st, obj)
let rank_val = const_int(len(indices))
let index_vals = map(indices, lower_expr)
let fn_name = if elem_kind == INT then "__mn_tensor_get_i64_nd" else "__mn_tensor_get_f64_nd"
let dest = make_value(elem_ty)
emit Call(dest, fn_name, [obj, rank_val] + index_vals)
return dest
```

Assignment target (`d[i, j] = val`): `lower_expr_assign` (the
`is_assign_target=true` path in `lower.mn:3212`) gets a
`TensorIndex` case parallel to the existing `Index` case:

```
let obj_r = lower_expr(st, ti_obj)
let idxs = map(ti_indices, lower_expr)
let rank = const_int(len(idxs))
let fn = if elem_kind == INT then "__mn_tensor_set_i64_nd" else "__mn_tensor_set_f64_nd"
emit Call(void_dest, fn, [obj, rank] + idxs + [val])
```

#### 9.1d — Emit: runtime declarations + variadic calling

`emit_llvm.mn::declare_all_runtime`:

```
s = declare_runtime_fn(s, "__mn_tensor_get_f64_nd", "double", "ptr, i64, ...")
s = declare_runtime_fn(s, "__mn_tensor_get_i64_nd", "i64", "ptr, i64, ...")
s = declare_runtime_fn(s, "__mn_tensor_set_f64_nd", "void", "ptr, i64, ...")
s = declare_runtime_fn(s, "__mn_tensor_set_i64_nd", "void", "ptr, i64, ...")
```

The `...` varargs suffix on the IR declaration is required — all four
are C variadic. If `declare_runtime_fn` doesn't currently support a
`...` param, add the support (likely ~10 LOC, mirror what Python
emits in `emit_llvm_text.py::_emit_decl` for `printf`).

`runtime_fn_attrs` gets four rows copied from v5.6.0's Phase 1
`tensor_get_*` lines.

Call-site emission: `lower_call_by_name` in `emit_llvm.mn` likely
routes by name already. Verify the variadic argument count matches
the MIR `Call` arg list.

### What does NOT ship

- **No tensor binops.** `a + b`, `a * 2.0` stays broken until v5.6.2.
- **No slicing, no wildcard, no reductions.** v5.6.3.
- **No broadcasting.** v5.6.2.
- **No shape checks at compile time.** Out-of-bounds is runtime only —
  same as Python bootstrap behavior.

---

## Exit criteria

1. `mnc-stage1` compiles `tests/golden/50_tensor_indexing.mn` clean
   (no parse errors, no semantic errors).
2. `llvm-as` accepts the emitted IR.
3. `lli` runs and produces byte-identical output to Python bootstrap
   (the Expected-output block in the test file — 1, 3, 4, 6, 10, 30,
   1, 8, 42, 99, 200).
4. Harness: `50_tensor_indexing` flips from FAIL to PASS (63/66 →
   **64/66**).
5. All v5.6.0-passing goldens still pass. No regressions in
   49_tensor_literal.
6. stage2.ll remains `llvm-as` clean; self-hosting preserved.
7. `make lint` clean; `check_struct_registry.py` clean.

---

## Design decisions

### D1 — New AST variant vs overload `Expr::Index`

`Expr::TensorIndex(Expr, List<Expr>)` already exists in `ast.mn`.
Use it. Don't collapse single-index + multi-index into one variant —
the type-oblivious parser can't tell at parse time whether `a[i]` is
a tensor index or a list subscript. Keeping the two variants means
single-subscript still routes through the existing
`Expr::Index` → `IndexGet` path, leaving list/map/string behavior
byte-identical.

### D2 — Parser emits `Expr::Index` for count==1, `Expr::TensorIndex` for count>=2

This is a syntactic decision, not a typed one. `a[5]` on a tensor
needs to still work — the existing v5.6.0 path already handles it
via `tensor_get_f64` / `_i64` (see `emit_llvm.mn:3277-3283`). Unifying
would force a semantic pass before codegen to pick the right runtime
fn, which we avoid.

### D3 — Variadic runtime call

`__mn_tensor_get_f64_nd` is C variadic because rank is dynamic.
Mapanare's LLVM emitter needs `...` support on the declaration. The
Python emitter already does this — mirror that. Alternative (fixed
N per rank: `_get_f64_1d`, `_get_f64_2d`, `_get_f64_3d`) rejected
because the C runtime is already variadic; no reason to regress the
ABI.

### D4 — No new MIR instruction

Direct `Call` lowering mirrors v5.6.0's pattern for `tensor_get_f64`.
A dedicated `TensorGet` MIR node would be slightly cleaner but
doesn't buy anything vs the `Call`-form and would add a new
`Instruction` registry slot (Reg.1 gate). v6.0 can unify tensor ops
into a typed MIR family.

### D5 — Design context: how other languages do this

Quick survey for the record — none of these change our decision, but
future maintainers should know where Mapanare sits:

- **NumPy / Python:** `a[i, j]` is sugar for `a.__getitem__((i, j))` —
  a tuple subscript. Any positive rank supported. Wildcard `:` +
  `...`. Implicit broadcasting.
- **Rust ndarray:** `a[[i, j]]` — array-of-scalars subscript.
  Requires `#[macro_use] extern crate ndarray` for `s![0..2, ..]`.
  Reductions: `a.sum()`, `a.mean()`. No implicit broadcasting;
  explicit `.broadcast((3, 2))` method.
- **Go gonum.mat:** `m.At(i, j)` / `m.Set(i, j, v)`. No operator
  overloading; `mat.Add(&c, &a, &b)` et al. Dense/Sparse matrix
  interfaces. No tuple subscript syntax.
- **Julia:** `A[i, j]` identical to Mapanare's surface. Dominant
  scientific language with the exact same syntax. Good precedent.
- **Swift:** `a[i, j]` via `subscript(_ i: Int, _ j: Int)` operator —
  matches Mapanare.

Mapanare's surface is closest to NumPy/Julia/Swift. The multi-arg
subscript is syntactic ergonomics; the semantic cost (two AST
variants) is the tax for keeping the parser type-oblivious.

---

## Risks

- **R1 — Varargs in self-hosted emitter.** If `declare_runtime_fn`
  doesn't support `...` yet, adding it is ~10 LOC but touches the
  declaration formatting path. Mitigation: check before coding;
  mirror Python `_emit_decl` at `emit_llvm_text.py`.
- **R2 — Single-subscript regression on tensors.** `a[5]` currently
  routes to `tensor_get_f64`. Adding `TensorIndex` for count>=2 must
  not break the count==1 path. Mitigation: keep the v5.6.0
  `tensor_get_f64` dispatch intact; only add the nd variant.
- **R3 — Assignment target path.** `d[0, 0] = 42.0` is the first time
  self-hosted sees a multi-index assignment. The existing `IndexSet`
  path is single-subscript-only. Mitigation: parallel
  `TensorIndexSet` MIR (if we introduce one) or just emit a direct
  `Call(__mn_tensor_set_f64_nd, ...)` from the assignment lowerer
  with no intermediate MIR node.
- **R4 — Self-compilation.** `mnc_all.mn` doesn't currently use
  multi-dim tensor indexing, so stage2.ll shouldn't change
  structurally. Verify with diff against v5.6.0 stage2.ll — only the
  4 new declarations should appear.
- **R5 — `TensorIndex` already in AST but not in `instr_kind` etc.**
  Any dead-code-scan helpers (accessors in `ast.mn`) may need audit
  for completeness.

---

## What NOT to do

- **Do not add broadcasting.** Even if it feels like a 5-line bonus.
  v5.6.2 scope.
- **Do not add range slicing `a[0..2, _]`.** Parser comma loop must
  stop at `RBRACKET` — no `DOTDOT`, no wildcard `_`. That's v5.6.3.
- **Do not port the full Python `IndexItem` machinery.** `TensorIndex`
  as `List<Expr>` is enough for this release. `IndexItem` earns its
  keep only when slices + scalars + wildcards mix in one subscript.
- **Do not touch `emit_llvm_text.py`.** Python already works. This
  is pure self-hosted porting.
- **Do not bump `TENSOR` size or add shape info to MIR.** Runtime
  owns the shape; the type system treats tensors as opaque.
- **Do not refactor `lower_index`.** Keep the existing
  `Expr::Index` → `IndexGet` branch untouched.
