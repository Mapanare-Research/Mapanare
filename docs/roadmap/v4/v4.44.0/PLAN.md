# Mapanare v4.44.0 — Tensor Broadcasting for Binary Ops

> **Arc 3 release 3.** Existing `+`, `-`, `*`, `/` extended to
> tensor operands with NumPy broadcasting rules. No new syntax:
> pure semantic + runtime work.

**Status:** DONE (2026-04-12)
**Session log:** Single session. broadcast_shape + semantic + runtime + lowering + tests.
**Decisions taken:** Decision 1 (NumPy exactly), Decision 2 (no mixed types), Decision 3 (rustc-quality with dimension detail).
**Breaking:** No
**Prerequisite:** v4.43.0
**Delta review:** No (no new syntax — semantic tightening only)
**Full panel:** No (v4.46.0)
**Estimated work:** 1.5 sprints
**Theme:** Tensor arithmetic with shape-compatible broadcasting and compile-time shape errors.

**Closes:** Coral v4.31.0 LOW item 19 — SPEC §3.10 tensor status line.

---

## Scope

### Broadcasting rules (NumPy-style)

Two tensors are broadcast-compatible if, aligning from the trailing dimensions:
- Each dimension pair is either equal, or one of them is 1 (broadcasts to the other).
- Rank mismatch is allowed: the shorter tensor's shape is left-padded with 1s.

Examples:

```mapanare
let a: Tensor<Float>[3, 4] = ...
let b: Tensor<Float>[3, 4] = ...
let c = a + b  // shape [3, 4]

let d: Tensor<Float>[3, 1] = ...
let e: Tensor<Float>[1, 4] = ...
let f = d + e  // shape [3, 4] via broadcasting

let g: Tensor<Float>[4] = ...
let h = a + g  // shape [3, 4] via rank extension (g is promoted to [1, 4])

let i: Tensor<Float>[3, 5] = ...
let j = a + i  // SEMANTIC ERROR: shapes [3, 4] and [3, 5] not broadcast-compatible
```

Shape errors fire at **compile time** if both shapes are known statically. If one operand has a dynamic shape (runtime-determined), the check falls through to runtime.

### Semantic changes

- [ ] `mapanare/semantic.py` `check_binary_op(node: BinaryOp) -> Type`:
  - If both operands are tensors: compute the broadcast shape. If shapes are not compatible, fire a compile error.
  - If one operand is a tensor and the other is a scalar: the scalar broadcasts to the tensor's shape (scalar + tensor, tensor + scalar).
  - If one operand is a tensor and the other is a non-tensor non-scalar: error.
- [ ] Helper: `broadcast_shape(a: list[int], b: list[int]) -> Optional[list[int]]` — NumPy rule. Returns `None` on incompatible.
- [ ] Helper: `emit_shape_mismatch_error(op, a_shape, b_shape)` — rustc-quality message showing both shapes and the incompatible dimension.

### Runtime

New functions:
- `__mn_tensor_add_broadcast_f64(MnTensor *a, MnTensor *b) -> MnTensor*`
- Same for `sub`, `mul`, `div` and `f32`, `i64`, `i32` element types
- Same for scalar variants: `__mn_tensor_add_scalar_f64(MnTensor *a, double s)`

Implementation:
- Compute the result shape.
- Allocate the result tensor.
- For each output element, compute the corresponding source indices in both operands using broadcasting rules.
- Call the scalar op.
- Return the result tensor.

### Lowering

- Binary op on tensors: lower to the runtime call for the specific op + element type combination.
- Result tensor ownership: the callee returns a fresh tensor; drop glue frees it at the end of its lifetime.

---

## Phase 1 — Semantic broadcasting logic

### Phase 1.1: Broadcast shape computation

- [ ] `mapanare/types.py` — new helper `broadcast_shape(a_shape: list[int], b_shape: list[int]) -> Optional[list[int]]`:

  ```python
  def broadcast_shape(a: list[int], b: list[int]) -> Optional[list[int]]:
      # Left-pad the shorter shape with 1s
      max_rank = max(len(a), len(b))
      a_padded = [1] * (max_rank - len(a)) + a
      b_padded = [1] * (max_rank - len(b)) + b

      result = []
      for ai, bi in zip(a_padded, b_padded):
          if ai == bi:
              result.append(ai)
          elif ai == 1:
              result.append(bi)
          elif bi == 1:
              result.append(ai)
          else:
              return None  # incompatible
      return result
  ```

### Phase 1.2: Shape error diagnostics

- [ ] `mapanare/semantic.py` — when broadcast fails:

  ```
  error: shapes [3, 4] and [3, 5] are not broadcast-compatible
    --> src/foo.mn:12:13
     |
  12 |     let c = a + i
     |             ^^^^^
     |
     = note: for broadcasting, each corresponding dimension must be equal or 1
     = note: dimension 1 differs: 4 vs 5
  ```

### Phase 1.3: Binary op integration

- [ ] `check_binary_op` extended to detect tensor operands and run the shape check.
- [ ] Return type is a tensor with the computed broadcast shape.

## Phase 2 — Runtime broadcasting

### Phase 2.1: Tensor + tensor

- [ ] `runtime/native/mapanare_gpu_builtins.c` — new function per element type:

  ```c
  MN_EXPORT MnTensor *__mn_tensor_add_broadcast_f64(MnTensor *a, MnTensor *b) {
      // Compute result shape
      int64_t result_rank = max(a->rank, b->rank);
      int64_t result_shape[MAX_RANK];
      for (int64_t d = 0; d < result_rank; d++) {
          int64_t ai = (d < result_rank - a->rank) ? 1 : a->shape[d - (result_rank - a->rank)];
          int64_t bi = (d < result_rank - b->rank) ? 1 : b->shape[d - (result_rank - b->rank)];
          result_shape[d] = (ai > bi) ? ai : bi;
      }

      // Allocate result
      MnTensor *result = __mn_tensor_alloc(sizeof(double), result_shape, result_rank);

      // Element-wise with broadcast index mapping
      int64_t total = 1;
      for (int64_t d = 0; d < result_rank; d++) total *= result_shape[d];

      for (int64_t i = 0; i < total; i++) {
          int64_t a_idx = broadcast_index(i, result_shape, result_rank, a);
          int64_t b_idx = broadcast_index(i, result_shape, result_rank, b);
          ((double*)result->data)[i] = ((double*)a->data)[a_idx] + ((double*)b->data)[b_idx];
      }

      return result;
  }
  ```

- [ ] Same shape for `sub`, `mul`, `div` and for element types `f32`, `i64`, `i32`.
- [ ] Helper: `broadcast_index(flat_out, out_shape, rank, source)` — compute the source's flat index for a given output flat index, accounting for broadcast.

### Phase 2.2: Tensor + scalar

- [ ] `__mn_tensor_add_scalar_f64(MnTensor *a, double s) -> MnTensor*` — iterate all elements, add scalar, return new tensor.
- [ ] Same for all ops × all element types.

### Phase 2.3: Runtime fn attrs

- [ ] `_RUNTIME_FN_ATTRS` — all new functions declared with `noalias` on return, `nounwind`. No `willreturn` (these have unbounded element count, could be cut short by abort on allocation failure).

## Phase 3 — Lowering

- [ ] `mapanare/lower.py` `_lower_binary_op(node)`:
  - Existing scalar cases unchanged.
  - New tensor case: dispatch on element type and operator to the right runtime function.
  - For tensor-scalar mixed case, same dispatch with `scalar` suffix.

## Phase 4 — Self-hosted mirror

- [ ] Mirror semantic broadcast computation in `mapanare/self/semantic.mn`.
- [ ] Mirror runtime declarations in `mapanare/self/emit_llvm.mn` `_RUNTIME_FN_ATTRS` equivalent.
- [ ] Mirror lowering in `mapanare/self/lower.mn`.
- [ ] Fixed-point diff stays at 0.

## Phase 5 — Tests

- [ ] `tests/golden/51_tensor_broadcast.mn`:
  - Same-shape addition
  - Row + column broadcast `[3, 1] + [1, 4]`
  - Rank extension `[3, 4] + [4]`
  - Scalar + tensor
  - Tensor + scalar
- [ ] `tests/semantic/test_tensor_broadcast.py`:
  - Compatible shapes type-check
  - Incompatible shapes fail with rustc-quality message
  - Shape mismatch message names the offending dimension
- [ ] `tests/runtime/test_tensor_broadcast.py`:
  - Numeric results match NumPy for 10 test cases
  - Scalar promotion correctness
  - Broadcast on 3-D and 4-D tensors

## Phase 6 — SPEC update (the Coral closure)

- [ ] `docs/SPEC.md §3.10` — update the **Status** line:
  - **Before:** "Experimental. Not yet implemented in any backend."
  - **After:** "Stable on LLVM backend. GPU-accelerated when CUDA/Vulkan available. CPU fallback otherwise. Compile-time shape checking for broadcast operations; runtime bounds checking for indexing."
- [ ] This closes Coral's v4.31.0 LOW item 19. Ledger row updated.

## Phase 7 — LOW sweep

2-3 items.

## Phase 8 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.44.0
- [ ] `CHANGELOG.md [4.44.0]`
- [ ] Cookbook: tensor arithmetic section
- [ ] SESSION_REPORT

---

## Exit criteria (14 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `broadcast_shape` helper correct for all NumPy rules | unit test with 20 cases including edge cases |
| 2 | Shape mismatch fires at compile time with rustc-quality message | `test_shape_mismatch_diagnostic` |
| 3 | Same-shape tensor addition works | `test_same_shape_add` |
| 4 | Row + column broadcast works | `test_row_column_broadcast` |
| 5 | Rank extension works | `test_rank_extension_broadcast` |
| 6 | Tensor + scalar works | `test_tensor_plus_scalar` |
| 7 | All four ops (+, -, *, /) implemented | tests cover each |
| 8 | All 4 element types (f64, f32, i64, i32) work | tests cover each |
| 9 | Results match NumPy within 1e-6 tolerance | `test_numpy_parity` |
| 10 | Drop glue frees intermediate tensors | valgrind-clean |
| 11 | Self-hosted mirror still byte-identical | `verify_fixed_point.sh` clean |
| 12 | SPEC §3.10 Status line updated | diff |
| 13 | Coral LOW item 19 marked CLOSED | `CARRY_FORWARD.md` |
| 14 | Standard closeout clean | CI |

---

## What v4.44.0 does NOT do

- **In-place tensor ops** (`a += b`) — v5.x
- **Tensor operator overloading for user-defined types** — no
- **Broadcasting for comparison ops** (`a == b`) — v4.45.0 or later
- **Broadcasting rules beyond NumPy's** — no
- **Automatic mixed-precision** (`f32 + f64 → f64`) — v5.x; for v4.44.0 element types must match

---

## Reference

- NumPy broadcasting docs — https://numpy.org/doc/stable/user/basics.broadcasting.html

---

## After v4.44.0

v4.45.0 adds reductions (`sum`, `mean`, `max`, `min`, `argmax`, `argmin`) and slicing/views (`t[0..2, :]`). Slicing is new syntax → delta review.
