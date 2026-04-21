# Mapanare v4.43.0 — Tensor Indexing + Bounds Checking

> **Arc 3 release 2.** Multi-dimensional indexing: `t[i, j]` for 2-D,
> `t[i, j, k]` for 3-D, comma-separated for general n-D. Bounds
> checked at runtime with the abort-on-OOB discipline from v4.32.0.

**Status:** DONE (2026-04-12)
**Session log:** Single session. Grammar migration + semantic + lowering + runtime + tests.
**Decisions taken:** Decision 1 (variadic), Decision 2 (no coercion), Decision 3 (under-rank = error).
**Breaking:** No (grammar extension only; existing single-index still works for lists)
**Prerequisite:** v4.42.0 (tensor literals)
**Delta review:** **YES** — new index syntax, Rattler lens (bounds-check ABI)
**Full panel:** No (v4.46.0)
**Estimated work:** 1.5 sprints
**Theme:** Read and write individual tensor elements by coordinate.

---

## Scope

### Syntax

```mapanare
let a: Tensor<Float>[3, 3] = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
let x: Float = a[1, 2]  // 6.0
a[2, 0] = 99.0          // assignment
```

Generalizes to any rank: `t[i]` for 1-D, `t[i, j]` for 2-D, `t[i, j, k]` for 3-D, etc.

### Grammar extension

Today's grammar has `index_expr: expr "[" expr "]"` — single-index only. v4.43.0 extends to:

```
index_expr: expr "[" index_list "]"
index_list: expr ("," expr)*
```

For list types (v4.32.0+), a single-index is required; a multi-index is a semantic error.
For tensor types, any number of indices ≤ rank is allowed. Under-indexing `t[i]` on a 2-D tensor returns a 1-D view of row `i` (this is the v4.45.0 slicing integration — for v4.43.0, under-indexing is a semantic error).

### Semantic rules

1. Number of indices must equal the tensor's rank.
2. Each index is `Int`.
3. The result type is the tensor's element type.
4. Bounds checking is runtime, not compile time (the indices may be variables whose values aren't known until runtime).

### Lowering

- `t[i, j]` lowers to `__mn_tensor_get_nd(t, [i, j], 2)` — pass the index array + rank.
- Runtime: compute flat offset `i * shape[1] + j`, bounds-check against `shape[0] * shape[1]`, read from the buffer.
- OOB: `abort("tensor index out of bounds: idx=[%ld, %ld] shape=[%ld, %ld]")` — same discipline as `__mn_list_get`.

---

## Phase 1 — Grammar

- [ ] `mapanare/mapanare.lark` — `index_list` production:
  ```
  index_expr: primary "[" index_list "]"
  index_list: expr ("," expr)*
  ```
- [ ] Confirm no conflict with list literals `[1, 2, 3]` at call-argument positions.

## Phase 2 — AST + parser

- [ ] `mapanare/ast_nodes.py` — change `IndexGet` from `index: Expr` to `indices: list[Expr]`. Every call site updates.

  Backwards compatibility: v4.42.0 codebase has `IndexGet(receiver, index)` single-index. Migrate all call sites to `IndexGet(receiver, [index])` in v4.43.0. This is a mechanical refactor — one commit, validate, move on.

- [ ] Same for `IndexSet`.
- [ ] `mapanare/parser.py` — `index_expr` transformer builds `IndexGet(receiver, list_of_indices)`.

## Phase 3 — Semantic

- [ ] `mapanare/semantic.py` `check_index_get(node: IndexGet) -> Type`:
  - Resolve receiver type.
  - **If list**: `len(indices) == 1`, single index is `Int`, return element type. (Old behavior preserved.)
  - **If map**: `len(indices) == 1`, index type matches map key type, return value type. (Old behavior preserved.)
  - **If tensor**: `len(indices) == rank(tensor)`, every index is `Int`, return tensor element type. (New.)
  - **Else**: rustc-quality error.
- [ ] `check_index_set` — same rules, but the RHS value type must match the element type.

## Phase 4 — Lowering

- [ ] `mapanare/lower.py` `_lower_index_get(node)`:
  - For list/map: unchanged.
  - For tensor: emit a call to `__mn_tensor_get_nd` with the index array.
- [ ] For efficiency at rank ≤ 4, we can emit specialized calls (`__mn_tensor_get_1d`, `__mn_tensor_get_2d`, `__mn_tensor_get_3d`) to avoid the variadic overhead. Cost: 3 extra runtime functions. Benefit: hot path elides an allocation + pointer dereference.
- [ ] **Decision:** ship the variadic form in v4.43.0 for simplicity. If profiling shows the overhead matters, add the specialized forms in a v4.43.1 point release or v4.44.0. The anti-rush rule says simpler-first.

## Phase 5 — Runtime

- [ ] `runtime/native/mapanare_gpu_builtins.c`:

  ```c
  MN_EXPORT double __mn_tensor_get_f64_nd(MnTensor *t, int64_t *idx, int64_t rank) {
      if (rank != t->rank) {
          fprintf(stderr, "mapanare: tensor index rank %ld doesn't match tensor rank %ld\n", rank, t->rank);
          abort();
      }
      // Compute flat offset with bounds check per dimension
      int64_t flat = 0;
      int64_t stride = 1;
      for (int64_t d = rank - 1; d >= 0; d--) {
          int64_t i = idx[d];
          if (i < 0 || i >= t->shape[d]) {
              fprintf(stderr, "mapanare: tensor index [%s] out of bounds for shape [%s]\n",
                      format_idx(idx, rank), format_shape(t->shape, rank));
              abort();
          }
          flat += i * stride;
          stride *= t->shape[d];
      }
      return ((double*)t->data)[flat];
  }
  ```

- [ ] Same shape for `__mn_tensor_get_f32_nd`, `__mn_tensor_get_i64_nd`, `__mn_tensor_get_i32_nd`.
- [ ] Same shape for `__mn_tensor_set_*_nd`.
- [ ] `_RUNTIME_FN_ATTRS` — declare all eight functions with `nounwind` (bounds-check aborts call `abort()`, which is `noreturn`, not unwinding).

## Phase 6 — Self-hosted mirror

- [ ] Grammar, AST, parser, semantic, lowering — all mirrored.
- [ ] Self-hosted `_RUNTIME_FN_ATTRS` entries for the new runtime functions (closes the asymmetry discipline).
- [ ] Fixed-point diff stays at 0.

## Phase 7 — Tests

- [ ] `tests/golden/50_tensor_indexing.mn` — a program that uses 2-D and 3-D indexing with both read and write
- [ ] `tests/parser/test_tensor_indexing.py` — parse cases
- [ ] `tests/semantic/test_tensor_indexing.py`:
  - Under-rank indexing on tensor is an error
  - Over-rank indexing on tensor is an error
  - Single-index on list still works
  - Multi-index on list is an error
  - Index type mismatch (`String` as index) is an error
- [ ] `tests/runtime/test_tensor_bounds.py`:
  - OOB read aborts with the expected stderr message
  - OOB write aborts
  - In-bounds read/write works for all integer and float element types

## Phase 8 — Delta review

- [ ] Rattler reviews the `__mn_tensor_get_nd` ABI. Key question: is the variadic-via-pointer approach reasonable or should we insist on fixed-rank specialization from day one?
- [ ] Coral reviews the syntactic choice (multi-index via comma).

## Phase 9 — LOW sweep

2-3 items.

## Phase 10 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.43.0
- [ ] CHANGELOG, SESSION_REPORT, docs updates

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Grammar parses `t[i, j, k]` | parser test |
| 2 | `IndexGet.indices` is a list; all call sites migrated | grep + build clean |
| 3 | Semantic enforces rank match for tensor indexing | `test_under_rank_is_error` |
| 4 | Semantic preserves list single-index behavior | `test_list_single_index_still_works` |
| 5 | Tensor read lowers to `__mn_tensor_get_*_nd` | grep emitted IR |
| 6 | Tensor write lowers to `__mn_tensor_set_*_nd` | same |
| 7 | OOB read aborts | `test_oob_read_aborts` |
| 8 | OOB write aborts | `test_oob_write_aborts` |
| 9 | In-bounds read/write correct for all element types | round-trip tests |
| 10 | Self-hosted mirror parses, lowers, runs | golden harness |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | Delta review PASS | `.reviews/deltas/v4.43.0-tensor-indexing.md` |
| 13 | Standard closeout clean | CI |

---

## What v4.43.0 does NOT do

- **Under-rank indexing returns view** — v4.45.0 (slicing). v4.43.0 treats under-rank as an error.
- **Fancy indexing** (index by list, index by boolean mask) — v5.x
- **Specialized fixed-rank runtime functions** — deferred pending profiling
- **Tensor indexing inside tensor literals** — no

---

## Reference

- NumPy array indexing — https://numpy.org/doc/stable/user/basics.indexing.html

---

## After v4.43.0

v4.44.0 adds broadcasting for binary ops. No new syntax — semantic + runtime work only.
