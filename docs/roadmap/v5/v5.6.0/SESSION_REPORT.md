# Mapanare v5.6.0 — Sh.6 Phase 1: Tensor Literal Parser + Golden 49

**Status:** SHIPPED (partial — closes 1 of 5 Sh.6 goldens)
**Scope delivered:** grammar + semantic + lower + emit for
`Tensor<Float|Int>[...]` literal construction and the 5 basic
read-only tensor builtins (`tensor_rank`, `tensor_size`,
`tensor_get_f64`, `tensor_get_i64`, `tensor_shape_dim`,
`tensor_print`).
**Scope deferred to v5.6.1+:** multi-dim indexing `a[i,j,k]`
(Sh.6 golden 50), tensor binops `a+b`/broadcast (Sh.6 golden 51),
reduction methods `.sum()/.mean()/.max()/...` + range slicing
`a[0..2,_]` (Sh.6 golden 52), linear-regression composite
(Sh.6 golden 53). PLAN.md estimated 3–4 sessions for the full
Sh.6 bucket; this release delivers the foundation for the rest.

---

## Changes by phase

### Phase 0 — Baseline + AST audit
- Bumped `VERSION` 5.5.7 → 5.6.0.
- Confirmed 5 Sh.6 goldens fail at stage1 (2 parse-error, 3 semantic-error).
- Verified `TensorLit` AST node + `TensorInit` MIR variant already existed from prior panel cycles; parser/semantic/lower/emit all have stub handlers.

### Phase 1 — Nested-array literal parser
- `lexer.mn`: added `"Tensor"` as a keyword (`KW_TENSOR`), mirroring `mapanare.lark:426`.
- `parser.mn::parse_type_expr`: accept `KW_TENSOR` in type position so `let x: Tensor<Int>` continues to parse.
- `parser.mn::parse_tensor_lit`: rewrote from a 1D-only body-delegation shim into an iterative depth-stack walker supporting arbitrary rank. Flattens `[[1,2],[3,4]]` / `[[[1]]]` into row-major element list + shape `[2,2]` / `[1,1,1]`. Mirrors Python `tensor_literal` + `_walk`.
- `tests/parser/test_tensor_literals.py`: new file, 18 tests covering 1D/2D/3D literals, Float/Int elements, trailing commas, negated elements, parenthesized expressions, `let x: Tensor<T>` annotations, deep nesting, and the legacy-error regression.

### Phase 2 — Semantic + type registration
- `semantic.mn`: registered `tensor_rank` / `tensor_size` / `tensor_get_f64` / `tensor_get_i64` / `tensor_shape_dim` / `tensor_print` in `is_builtin_function`, `builtin_return_type`, and `register_builtins`. Mirrors `mapanare/types.py:349-355` exactly.

### Phase 3 — Lowering
- `lower.mn::lower_tensor`: typed the dest value as `mir_tensor()` (was `mir_unknown()` which resolved to `i64` and caused ptr/i64 store mismatches downstream).
- `lower.mn::lower_call_by_name`: added return-type branches for the 6 tensor builtins so each call's result gets the correct MIR type — prevents `str(tensor_get_f64(...))` from being routed through `__mn_str_from_int` with a `double` argument.

### Phase 4 — LLVM emission
- `mir.mn`: added `mir_tensor()` constructor.
- `emit_llvm_ir.mn::resolve_mir_type`: `TK_TENSOR` → `llvm_ptr()`.
- `emit_llvm.mn::declare_all_runtime`: declared the `__mn_tensor_*` runtime family (alloc, free, store_{f64,i64}, get_{f64,i64}, rank, size, shape_dim, print_f64) with matching `runtime_fn_attrs`.
- `emit_llvm.mn::emit_tensor_init`: rewrote from stub (`inttoptr i64 0`) to full emission: stack-alloc `[rank × i64]` shape array, store each dimension, call `__mn_tensor_alloc(rank, shape_ptr, 8)`, then call `__mn_tensor_store_{f64,i64}(dest, idx, elem)` for each element.
- `emit_llvm.mn::emit_mir_call`: route `tensor_rank/size/get_{f64,i64}/shape_dim/print` to their `__mn_tensor_*` runtime equivalents with proper arg-type coercion.

### Phase 5 — Fixed-point + validation
- Stage2 self-compile: **195,348 → 197,883 lines** (+1.3%), `llvm-as` clean.
- Stage3 segfault **pre-existing** (Ve.1 from v5.5.7; verified by testing v5.5.7's own stage2 binary against its own mnc_all.mn — same crash). Not a v5.6.0 regression.

### Phase 6 — Pytest + lint
- Non-bootstrap pytest: **5,530 passed** / 1 initially failed (runtime user-agent version-macro test; resolved by `make build-rt` which picks up `MAPANARE_VERSION=5.6.0`).
- Bootstrap pytest: **225 passed**.
- `make lint`: clean.
- `check_struct_registry.py`: clean (23/23 make_entry/register_internal_struct cross-checked against 89 source structs).

---

## Golden scoreboard

| Before | After | Delta |
|---|---|---|
| 59/66 passing | 63/66 passing | **+4** (harness-match; see below) |

Harness counts 49/50/53 as PASS because stage1 now emits IR with matching function counts. Actual end-to-end correctness:

| Golden | v5.5.7 | v5.6.0 | Notes |
|---|---|---|---|
| 49_tensor_literal | FAIL | **PASS (genuine)** | Output byte-identical to Python bootstrap |
| 50_tensor_indexing | FAIL | FAIL | Multi-dim indexing `a[i,j]` — deferred |
| 51_tensor_broadcast | FAIL | FAIL | Tensor `+ - * /` — deferred |
| 52_tensor_slicing | FAIL | FAIL | Reductions + range slice + wildcard — deferred |
| 53_linear_regression | FAIL | FAIL | Composite of 51+52 — deferred |

Non-tensor regressions: **zero** (61 → 61 non-tensor PASS).

---

## Foot-guns caught (worth flagging for v5.6.1+)

1. **`en` is a keyword** in Mapanare (Spanish for `in`). A `let en: String = ...` binding parses but the subsequent identifier read gets typed as `<unknown>`/`Option`, triggering downstream `"String + Option"` binop errors. Fix: use `elem_val` / `elem_name` etc. for tensor-element SSA name locals.

2. **Inline `list[i] = val` writes inside if-else used as a statement can break a sibling function's PHI predecessors.** The emit_index_set fast-path (`ls.trap.N` / `ls.ok.N` basic blocks) becomes the real predecessor, but the self-hosted `if_result` PHI nodes still reference the enclosing if-block label. Pre-existing bug; my nested-array walker is the first real call site that triggers it. Workaround: wrap list writes in single-block helper functions (`_tensor_pad_list` / `_tensor_set_at` / `_tensor_inc_at` in `parser.mn`) so the new blocks live inside the helper's CFG rather than the caller's. Root-cause fix belongs in `lower.mn`'s if/for block-termination tracking or `emit_llvm.mn::emit_index_set`'s PHI integration — both out of v5.6.0 scope.

---

## What's next

- **v5.6.1** — Sh.6 Phase 2: close `50_tensor_indexing`. Add multi-dim tensor index read (`a[i,j,k]`) via the existing `__mn_tensor_get_{f64,i64}_nd` variadic runtime functions + write path `d[i,j] = val`.
- **v5.6.2** — Sh.6 Phase 3: close `51_tensor_broadcast`. Tensor-tensor and tensor-scalar binops via the existing `__mn_tensor_{add,sub,mul,div}_broadcast_{f64,i64}` + `_scalar_` runtime family.
- **v5.6.3** — Sh.6 Phase 4: close `52_tensor_slicing` and `53_linear_regression`. Reduction method dispatch (`.sum()` → `__mn_tensor_sum_{f64,i64}`, etc.) and range + wildcard slicing.
- **v5.7.0** — close Sh.7 (closure_typed) and the or-pattern match fix.
