# v5.41.0 — Phase 0 audit (existing tensor surface)

Audit run at v5.40.0 HEAD. Confirms what's actually present
versus what the PLAN's framing assumes, and surfaces the
delta between PLAN scope and real scope before any compiler
edits land.

## What already exists

### Builtin Tensor type (`TypeKind.TENSOR`)

- AST: `IndexItem(kind, expr, start, end)` — no `step` field.
- AST: `RangeExpr(start, end, inclusive)` — no `step` field.
- Grammar (`mapanare/mapanare.lark`): `RANGE` (`..`) +
  `RANGE_INCL` (`..=`) operators. **No `:step` syntax in the
  grammar.** PLAN/PROMPT claim "Grammar already supports
  `[start..end:step]`" — this is wrong at HEAD.
- Lower: `_lower_tensor_get` (`__mn_tensor_get_*_nd`),
  `_lower_tensor_set` (`__mn_tensor_set_*_nd`),
  `_lower_tensor_slice` (`__mn_tensor_slice`). The slice path
  handles `range` and `wildcard` index items only — no `step`
  is plumbed because the AST has no step field.
- Emitter: `_TENSOR_BROADCAST_FNS`, `_TENSOR_SCALAR_FNS`,
  `_TENSOR_RSCALAR_FNS`, `_TENSOR_REDUCE_F64`,
  `_TENSOR_REDUCE_I64` — broadcast / scalar / reduction
  dispatch tables. No reshape, no view, no step.
- C runtime (`runtime/native/mapanare_gpu_builtins.c`):
  `__mn_tensor_alloc`, `__mn_tensor_free`,
  `__mn_tensor_store_*`, `__mn_tensor_get_*`,
  `__mn_tensor_get_*_nd`, `__mn_tensor_set_*_nd`,
  `__mn_tensor_rank`, `__mn_tensor_size`,
  `__mn_tensor_shape_dim`, `__mn_tensor_print_f64`,
  `__mn_tensor_argmax/argmin`, broadcast/scalar arithmetic,
  reductions, `__mn_tensor_slice` (line 753 — **a copying
  slice**, not a view; allocates new buffer + memcpy per
  element).
- C struct (`runtime/native/mapanare_runtime.h:336`):
  `mapanare_tensor_t { data, ndim, shape, size, elem_size }`.
  **No refcount. No strides. No offset.** Contiguous
  row-major only.

### Stdlib `GpuTensor` (separate type from builtin Tensor)

- `stdlib/gpu/tensor.mn` ships `pub fn reshape(t: GpuTensor,
  shape: List<Int>) -> Result<GpuTensor, TensorError>` at
  line 544. Implementation: validates total element count;
  allocates new `GpuTensor` struct sharing `t.data` pointer
  with new shape metadata. **This works today** for the
  stdlib `GpuTensor` type — but `GpuTensor` is a stdlib
  struct, not the language-builtin `Tensor`.
- `stdlib/gpu/tensor.mn` does NOT ship `view()` or stepped
  slicing.

## What's actually missing (corrected scope)

### Ts.1 — reshape

- **Builtin `Tensor` has no reshape method** at any layer
  (parser → lower → emit → runtime).
- The stdlib `GpuTensor.reshape` is a different type's
  method and is not what the LLVM-backend parity gap
  refers to.
- C runtime has no `__mn_tensor_reshape` export.
- Add: MIR op `TensorReshape`, lower for `t.reshape(shape)`
  on builtin `Tensor`, emitter branch, `__mn_tensor_reshape`
  C export sharing the data buffer.

### Ts.2 — mutable views

- No view operation on builtin `Tensor` exists. The existing
  `__mn_tensor_slice` copies data — it is **not** a view.
- `mapanare_tensor_t` has no refcount, no strides, no
  offset — adding views requires substantial struct surgery
  with ABI implications for every existing function that
  takes/returns `mapanare_tensor_t *`.
- Add: MIR op `TensorView`, lower for `t.view(...)`,
  emitter branch, `__mn_tensor_view` C export, refcount
  field on `mapanare_tensor_t` (+ "is_view" flag for the
  drop-glue audit).

### Ts.3 — stepped slices

- **Grammar does not accept `[start..end:step]` at HEAD.**
  PLAN/PROMPT framing is wrong on this point.
- Adding stepped slices requires: grammar change
  (`RANGE_STEP` token or extending `range_op` rule); parser
  to construct `RangeExpr` (or `IndexItem`) with a `step`
  field; AST node update (add `step` field); lower path to
  emit step-aware slice MIR op; runtime helper that
  composes strides per-axis.
- Add: AST `RangeExpr.step` (or `IndexItem.step`); grammar
  rule + parser; MIR op `TensorStepSlice`; lower + emitter;
  `__mn_tensor_step_slice` C export.

### Ts.5 — C runtime helpers

- ~150 LOC PLAN budget is realistic only if the
  `mapanare_tensor_t` struct gains a refcount field
  (~30 LOC) and every existing function that frees a
  tensor gates on refcount (`__mn_tensor_free` becomes
  refcount-aware; sweep ~5 sites). Plus the four new
  helpers themselves.

## Compiler-edit budget — corrected

| Layer | PLAN said | Actual scope |
|---|---|---|
| Grammar | "already supports" | Add `:step` rule, lexer token (~15 LOC) |
| AST | (implicit) | Add `step` field to `RangeExpr` or `IndexItem` (~10 LOC) |
| Parser | (implicit) | Construct step-bearing nodes (~20 LOC) |
| MIR (Python) | New ops | Append `TensorReshape`, `TensorView`, `TensorStepSlice` (~80 LOC) |
| MIR (self-host) | Mirror | Same three ops + lower mirrors (~150 LOC) |
| Lower (Python) | ~150+250+150 | Reshape ~80, view ~120, step ~80 (~280 LOC) |
| Lower (self-host) | mirror | (~280 LOC) |
| Emitter (Python) | Inline above | Three new emit branches (~120 LOC) |
| Emitter (self-host) | Mirror | (~120 LOC) |
| C runtime | ~100 LOC | Refcount on struct + 4 new exports + drop-glue audit (~200 LOC) |
| Goldens + tests | Ts.4 | 3 goldens + 3 pytest files + property test (~400 LOC tests) |
| Docs | Ts.6 | SPEC + CLAUDE + tensor.md cookbook (~150 LOC) |

**Realistic LOC total: ~1,900 across compiler + runtime +
tests + docs.** PLAN's "~600 LOC compiler + ~150 LOC C +
~3 goldens" is a substantial under-count, principally
because (a) the grammar needs to change (PLAN missed
this), (b) the `mapanare_tensor_t` struct needs a
refcount (PLAN floats this as "probably" but the field
addition cascades through every existing free site),
(c) the self-host MIR enum needs the same new ops
appended (PLAN flags but doesn't budget).

**Realistic effort: 3–5 working days, not 1–2 sessions.**

## ABI compatibility risk

- Adding fields to `mapanare_tensor_t` is an ABI change.
  Stage1 binaries built against the v5.40.0 runtime cannot
  link against the v5.41.0 runtime if the struct grows.
  Mitigation: append new fields at the end of the struct
  AND rebuild stage1 from source as part of the
  `bash scripts/verify_fixed_point.sh` rebuild step. The
  binary-compat regression test the PROMPT requests is
  **not safe** for struct-layout changes — it can only
  validate MIR-enum-ordinal stability. Document this
  explicitly in the SESSION_REPORT.

## Recommendation

The PLAN under-budgets v5.41.0. Three options:

1. **Ship as one v5.41.0 release** at the corrected
   ~1,900 LOC budget (3–5 days). Accepts the larger
   diff for full closeout in a single tag.

2. **Split across v5.41.0 + v5.41.1**: Ts.1 (reshape) +
   Ts.5 (refcount + reshape C helper) ship at v5.41.0
   (~700 LOC); Ts.2 (views) + Ts.3 (stepped slices) +
   remaining tests/docs ship at v5.41.1 (~1,200 LOC).
   Smaller per-release diff, two strict-streak gates.

3. **Re-scope v5.41.0 to "drop the parity-gap claim"**:
   strike the `Not yet on LLVM: tensor reshape, mutable
   views, stepped slices` line from CLAUDE.md without
   shipping the features; promote the gap to a v5.42+
   docket. Honest framing if the appetite for ~1,900 LOC
   compiler-edit + struct-layout-change isn't there in
   the current arc.

Surfacing to lead before authoring code.
