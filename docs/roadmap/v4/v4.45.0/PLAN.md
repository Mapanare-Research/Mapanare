# Mapanare v4.45.0 — Tensor Reductions + Slicing + Views

> **Arc 3 release 4.** Reductions via method syntax, slicing via
> range/wildcard in index position. Slicing is new syntax — delta
> review mandatory.

**Status:** DONE (2026-04-12)
**Session log:** Single session. Reductions + slicing + IndexItem migration + tests.
**Decisions taken:** Decision 1 (atomic refcount — deferred to v5.x; copy-based slicing for v4.45.0), Decision 2 (read-only views — copies, not views), Decision 3 (no negative indices), Decision 4 (no stepped slices).
**Breaking:** No
**Prerequisite:** v4.44.0
**Delta review:** **YES** — slicing adds range and `:` wildcard to the grammar
**Full panel:** No (v4.46.0)
**Estimated work:** 2 sprints
**Theme:** Finish the tensor language surface. Linear regression in Mapanare.

---

## Scope

### Reductions

Method syntax on tensors:

```mapanare
let t: Tensor<Float>[3, 4] = ...
let total: Float = t.sum()
let avg: Float = t.mean()
let biggest: Float = t.max()
let smallest: Float = t.min()
let biggest_idx: Int = t.argmax()
let smallest_idx: Int = t.argmin()

let col_sums: Tensor<Float>[4] = t.sum(axis: 0)
let row_maxes: Tensor<Float>[3] = t.max(axis: 1)
```

- Without `axis` argument: reduce the whole tensor to a scalar.
- With `axis: N` argument: reduce along dimension N, return a tensor with that dimension removed.

These are **not new syntax** — method calls already exist. The runtime work is in extending `runtime/native/mapanare_gpu_builtins.c` with reduction primitives.

### Slicing

```mapanare
let a: Tensor<Float>[5, 5] = ...
let sub: Tensor<Float>[2, 5] = a[0..2, :]       // first 2 rows, all columns
let col: Tensor<Float>[5] = a[:, 2]             // all rows, column 2
let block: Tensor<Float>[3, 3] = a[1..4, 1..4]  // middle 3x3 block
```

- Range `N..M` in an index position means "dimensions N through M-1" along that axis.
- `:` (colon) means "all" — takes the full dimension.
- A slice returns a **view**: a new tensor header that shares the underlying buffer. No copy. The view has its own shape + stride data.

Slicing is **new syntax** for the `N..M` and `:` forms inside index brackets. Delta review mandatory.

---

## Part A — Reductions

### Phase A.1: Runtime reduction primitives

- [ ] `runtime/native/mapanare_gpu_builtins.c` — new functions:

  ```c
  MN_EXPORT double __mn_tensor_sum_f64(MnTensor *t);
  MN_EXPORT double __mn_tensor_mean_f64(MnTensor *t);
  MN_EXPORT double __mn_tensor_max_f64(MnTensor *t);
  MN_EXPORT double __mn_tensor_min_f64(MnTensor *t);
  MN_EXPORT int64_t __mn_tensor_argmax_f64(MnTensor *t);
  MN_EXPORT int64_t __mn_tensor_argmin_f64(MnTensor *t);

  MN_EXPORT MnTensor *__mn_tensor_sum_axis_f64(MnTensor *t, int64_t axis);
  MN_EXPORT MnTensor *__mn_tensor_max_axis_f64(MnTensor *t, int64_t axis);
  // etc.
  ```

- [ ] Same for `f32`, `i64`, `i32` element types.
- [ ] Axis reduction: iterate over all elements, accumulate into a result tensor whose shape is the input's shape minus the reduction axis.
- [ ] Empty tensor edge cases: `sum` returns 0, `mean` aborts (division by zero is a loud failure), `max`/`min` abort (undefined).

### Phase A.2: Method dispatch

- [ ] `mapanare/semantic.py` — when checking a method call on a tensor type, dispatch to the reduction method signatures. Each reduction method has:
  - No argument: returns scalar
  - `axis: Int` argument: returns tensor with one fewer dimension
- [ ] Semantic also verifies: `axis` must be in `0..rank`. Compile-time check if `axis` is a literal, runtime check otherwise.

### Phase A.3: Lowering

- [ ] Method call on tensor lowers to the specific runtime function for (element type × reduction × with/without axis).

### Phase A.4: Tests

- [ ] `tests/runtime/test_tensor_reductions.py`:
  - All 6 reductions (sum, mean, max, min, argmax, argmin) across all 4 element types
  - With and without `axis` argument
  - Match NumPy within tolerance
  - Edge cases: single-element tensor, empty tensor aborts on mean/max/min

---

## Part B — Slicing

### Phase B.1: Grammar

- [ ] `mapanare/mapanare.lark` — extend `index_list` to allow range and wildcard:

  ```
  index_list: index_item ("," index_item)*
  index_item: expr                      // scalar index
            | expr ".." expr            // range (half-open)
            | ":"                       // wildcard (full dimension)
  ```

- [ ] Disambiguate `expr ".." expr` from range expressions in other contexts. Range-as-value (`for i in 0..n`) already exists; range-in-index-position is a new use.

### Phase B.2: AST

- [ ] `mapanare/ast_nodes.py`:

  ```python
  @dataclass
  class IndexItem:
      kind: Literal["scalar", "range", "wildcard"]
      start: Optional[Expr]  # for range
      end: Optional[Expr]    # for range
      scalar: Optional[Expr]  # for scalar
      # wildcard has none of the above
  ```

- [ ] `IndexGet.indices: list[IndexItem]` — change from `list[Expr]` to `list[IndexItem]`. Existing call sites migrate (scalar items wrap).

### Phase B.3: Semantic

- [ ] `check_index_get` handles the three item kinds:
  - Scalar: reduces the dimension (rank−1 in that axis)
  - Range: keeps the dimension, shape is `end - start`
  - Wildcard: keeps the dimension, shape is unchanged
- [ ] If any item is a range/wildcard, the result is a tensor (view). Otherwise, the result is a scalar (as in v4.43.0).
- [ ] Compile-time range bounds check if `start`/`end` are literals.

### Phase B.4: View runtime

- [ ] `runtime/native/mapanare_gpu_builtins.c`:

  ```c
  typedef struct MnTensorView {
      MnTensor base;  // shares buffer with parent
      MnTensor *parent;  // for reference counting on drop
      int64_t *strides;  // for non-contiguous views
  } MnTensorView;

  MN_EXPORT MnTensor *__mn_tensor_slice(MnTensor *t, int64_t *starts, int64_t *ends, int64_t rank);
  ```

- [ ] The view shares the underlying buffer with the parent. Strides are computed from the slice bounds.
- [ ] Drop glue for a view: decrement parent refcount; if refcount drops to 0 and parent has no other live views, free the parent's buffer.
- [ ] This introduces reference counting for tensors. Pre-v4.45.0 tensors are uniquely owned; v4.45.0 adds a view model.
- [ ] **Decision:** for v4.45.0, simple approach — a view **always keeps its parent alive** for the view's lifetime. Views don't mutate the buffer; the parent's drop glue is deferred until all views are dropped. No refcounting needed if the ownership is tracked structurally (the view holds a pointer to its parent, and the drop glue of the view decrements an atomic counter on the parent).
- [ ] **Decision:** use an atomic counter. Small overhead, correct for multi-threaded code, avoids the ownership-graph complexity.

### Phase B.5: Lowering

- [ ] `mapanare/lower.py` — tensor slice lowers to `__mn_tensor_slice(parent, starts_array, ends_array, rank)`.
- [ ] Scalar indices in a slice (`a[1, 0..5]`) are treated as `start == 1, end == 2` internally.
- [ ] Drop glue for slice results: decrement parent refcount.

### Phase B.6: Self-hosted mirror

- [ ] Full mirror. Fixed-point diff stays at 0.

### Phase B.7: Delta review

- [ ] Rattler reviews the view / refcount model.
- [ ] Coral reviews the slicing syntax.

### Phase B.8: Tests

- [ ] `tests/golden/52_tensor_slicing.mn` — an example that uses ranges, wildcards, and mixed scalar/range indexing
- [ ] `tests/parser/test_tensor_slicing.py` — parse cases for `a[0..2, :]`, `a[:, 2]`, `a[1, 0..3, :]`
- [ ] `tests/semantic/test_tensor_slicing.py` — shape inference for views
- [ ] `tests/runtime/test_tensor_views.py`:
  - View shares buffer with parent (modifying parent element visible through view)
  - View lifetime keeps parent alive
  - Dropping all views before parent works
  - Dropping parent before all views triggers an abort (or: parent is kept alive until all views drop — pick one, document it)
  - Valgrind clean

---

## Part C — End-to-end demo

### Phase C.1: Linear regression golden

- [ ] `tests/golden/53_linear_regression.mn`:

  ```mapanare
  // Gradient descent for y = wx + b
  let X: Tensor<Float>[100, 1] = load_training_data()
  let y: Tensor<Float>[100] = load_labels()

  let w: Tensor<Float>[1] = Tensor<Float>[0.0]
  let b: Tensor<Float>[1] = Tensor<Float>[0.0]
  let lr: Float = 0.01

  for epoch in 0..1000 {
      let pred: Tensor<Float>[100] = (X.matmul(w)).squeeze() + b[0]
      let error: Tensor<Float>[100] = pred - y
      let grad_w: Float = (X.transpose().matmul(error.unsqueeze(axis: 1))).sum() / 100.0
      let grad_b: Float = error.sum() / 100.0
      w[0] = w[0] - lr * grad_w
      b[0] = b[0] - lr * grad_b
  }

  print("Final weights: w=", w[0], ", b=", b[0])
  ```

  Note: `matmul`, `transpose`, `squeeze`, `unsqueeze` are v4.45.0 extensions. Cover as methods on tensor:
  - `matmul(other)` — already exists at runtime from v4.28.0; expose as a method in v4.45.0
  - `transpose()` — returns a view with swapped strides (2-D only for v4.45.0)
  - `squeeze()` — removes size-1 dimensions
  - `unsqueeze(axis)` — adds a size-1 dimension at axis

- [ ] Reference NumPy implementation, match output within tolerance.
- [ ] This is the canonical demo the v4.46.0 panel will look at when asking "is the tensor arc complete?"

---

## Phase D — LOW sweep

2-3 items.

---

## Phase E — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.45.0
- [ ] `CHANGELOG.md [4.45.0]`
- [ ] `docs/cookbook.md` §Tensors — reductions + slicing + linear regression tutorial
- [ ] `docs/SPEC.md §3.10` — full documentation of the tensor surface
- [ ] SESSION_REPORT

---

## Exit criteria (18 items)

| # | Check | Evidence |
|---|---|---|
| 1 | All 6 reductions implemented for all 4 element types | 24 test cases |
| 2 | Reductions with `axis` argument return correctly-shaped tensors | shape tests |
| 3 | Reduction results match NumPy | tolerance tests |
| 4 | Empty-tensor reductions handle gracefully (sum=0; mean/max/min abort) | edge case tests |
| 5 | Grammar parses `0..N` and `:` in index position | parser tests |
| 6 | `IndexGet.indices` migrated to `list[IndexItem]` | grep + build |
| 7 | Slice semantic returns view type with correct shape | semantic tests |
| 8 | Slice lowering calls `__mn_tensor_slice` | grep emitted IR |
| 9 | View shares buffer with parent | runtime test |
| 10 | View keeps parent alive via atomic refcount | runtime test |
| 11 | Transpose / squeeze / unsqueeze methods work | runtime tests |
| 12 | Linear regression demo runs and converges | `tests/golden/53_linear_regression.mn` |
| 13 | Linear regression output matches NumPy reference | tolerance check |
| 14 | Valgrind clean on view-heavy code | valgrind run |
| 15 | Self-hosted mirror still byte-identical | `verify_fixed_point.sh` |
| 16 | Delta review PASS | `.reviews/deltas/v4.45.0-tensor-slicing.md` |
| 17 | Documentation complete for tensor surface | `check_docs_drift.py` clean |
| 18 | Standard closeout clean | CI |

---

## What v4.45.0 does NOT do

- **Tensor reshape beyond squeeze/unsqueeze** — v5.x
- **`.view(new_shape)`** explicit reshape — v5.x
- **Stride tricks / general `np.lib.stride_tricks`** — v5.x
- **Mutable views** — for v4.45.0 views are read-only. Mutating a view is an error. Mutable views are v5.x if demand.
- **Slicing with step (`0..10..2`)** — v5.x
- **Negative indices (`a[-1]`)** — v5.x
- **Matmul as operator (`@`)** — no plans

---

## Reference

- NumPy basic slicing — https://numpy.org/doc/stable/user/basics.indexing.html#slicing-and-striding
- NumPy reductions — https://numpy.org/doc/stable/reference/routines.statistics.html

---

## After v4.45.0

v4.46.0 is the **arc 3 panel release** — the third 5-minor cadence panel. Arc 3 officially closes on the panel verdict.
