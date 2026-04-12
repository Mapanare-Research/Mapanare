# Mapanare v4.42.0 — Tensor Literals + Runtime Primitive Wiring

> **Arc 3 release 1.** First of the tensor completeness arc. Adds
> tensor literal syntax and wires it to `runtime/native/mapanare_gpu_builtins.c`
> with a CPU fallback for when GPU is unavailable. This is the release
> where `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]` becomes a real source
> form, not documentation aspiration.

**Status:** DONE (2026-04-12)
**Session log:** Single session. Phases 1–11 completed sequentially.
**Decisions taken:** Decision 1 (shape mismatch → parse error), Decision 2 (empty `[]` → parse error, `[0]` allowed), Decision 3 (no 0-D tensors).
**Breaking:** No (additive syntax)
**Prerequisite:** v4.41.0 (arc 2 panel PASS)
**Delta review:** **YES** — new syntactic form, Rattler + Coral lenses
**Full panel:** No (v4.46.0)
**Estimated work:** 2 sprints
**Theme:** Tensors become a first-class language primitive, not a GPU-runtime-only thing.

---

## Why tensor literals first

SPEC §3.10 says tensors are "not yet implemented in any backend." v4.18.0 claimed they were first-class. v4.25.0 added shape checking. v4.28.0 fixed matmul. But the user still cannot write `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]` in source code and get a tensor value. The runtime primitives exist; the language surface does not.

v4.42.0 closes the source-side gap. Without tensor literals, the remaining arc-3 features (indexing, broadcasting, reductions, slicing) have no construction form and users have to build tensors via awkward stdlib helpers. Literals first makes everything else natural.

---

## Scope

### Syntax

```mapanare
let a: Tensor<Float>[2, 3] = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
let b: Tensor<Int>[3] = Tensor<Int>[10, 20, 30]
let c: Tensor<Float>[2, 2, 2] = Tensor<Float>[
    [[1.0, 2.0], [3.0, 4.0]],
    [[5.0, 6.0], [7.0, 8.0]],
]
```

The type annotation is the target shape. The literal body is a nested list of scalars. The semantic checker verifies shape consistency.

### AST

```python
@dataclass
class TensorLiteral(Expr):
    element_type: TypeExpr
    shape: list[int]  # inferred from nesting, validated against annotation
    elements: list[Expr]  # flat, row-major; length = product(shape)
    span: Span
```

### Semantic rules

1. The literal's element-type matches the type annotation's element type.
2. The literal's inferred shape (from nesting depth + element counts) matches the type annotation's shape.
3. Every element is a scalar of the element type.
4. Empty tensors (`Tensor<Float>[0]`) are allowed (zero-length).
5. Jagged arrays (`[[1, 2], [3]]`) are a compile error with a rustc-quality message.

### Lowering

- Allocate a tensor via `__mn_tensor_alloc(element_size, shape_data, rank)`.
- Emit stores for each element at `tensor[i]` for `i` in `0..len`.
- Return the allocated tensor pointer.

---

## Phase 0 — Pre-commit

- [ ] v4.41.0 panel PASS confirmed
- [ ] Fixed-point still 0 lines
- [ ] Delta reviewer chosen: **Rattler (primary)** for runtime crossing, **Coral (secondary)** for syntax design

## Phase 1 — Grammar

- [ ] `mapanare/mapanare.lark` — add tensor literal production:

  ```
  tensor_literal: "Tensor" "<" type_expr ">" "[" tensor_body "]"
  tensor_body: tensor_element ("," tensor_element)*
  tensor_element: atom | "[" tensor_body "]"
  ```

- [ ] Disambiguation: `Tensor<Float>[...]` must not conflict with existing postfix index `expr[...]`. The `Tensor<...>` prefix is load-bearing — without it, the parser can't tell tensor literals from list literals. Confirm no conflict.

## Phase 2 — AST + parser

- [ ] `mapanare/ast_nodes.py` — add `TensorLiteral` dataclass.
- [ ] `mapanare/parser.py` — `tensor_literal` transformer. Walks the nested body, flattens to row-major, infers shape from nesting depth and per-level lengths, returns `TensorLiteral`.
- [ ] Jagged detection: if sibling nested lists have different lengths, raise a `ParseError` with file:line and the mismatched lengths.

## Phase 3 — Semantic

- [ ] `mapanare/semantic.py` `check_tensor_literal(node: TensorLiteral, expected: Type) -> Type`:
  - Verify `expected` is a `Tensor<T>[shape]` or infer from the literal.
  - Verify shape consistency.
  - Verify every element has type `T` (scalars only in v4.42.0; nested tensor composition is v5.x).
  - Return `Tensor<T>[shape]`.

## Phase 4 — Lowering

- [ ] `mapanare/lower.py` `_lower_tensor_literal(node: TensorLiteral) -> MIRValue`:
  - Compute the shape array as a MIR constant.
  - Call `__mn_tensor_alloc(element_size, shape_ptr, rank)`.
  - For each element, emit a `tensor_set(tensor, i, element_value)`.
  - Return the tensor pointer.

- [ ] MIR may need a `TensorAlloc` instruction and a `TensorStore` instruction if not already present. Otherwise, these can lower to plain `Call` instructions targeting the runtime primitives.

## Phase 5 — Runtime

- [ ] `runtime/native/mapanare_gpu_builtins.c` — verify `__mn_tensor_alloc(size_t element_size, int64_t *shape, int64_t rank) -> MnTensor*` exists. If not, add it.
- [ ] CPU fallback: if CUDA/Vulkan not initialized at runtime, `__mn_tensor_alloc` allocates a plain heap buffer + metadata struct. Same shape, same interface; GPU features (matmul) fall through to CPU path.
- [ ] `__mn_tensor_store_element(tensor, index, value, element_size)` — write a scalar.
- [ ] Drop glue: `__mn_tensor_free` already exists for matmul cleanup; ensure it's called from the v4.3.0 drop glue framework for `TypeKind.TENSOR`.

## Phase 6 — LLVM emitter

- [ ] `mapanare/emit_llvm_text.py` — register `__mn_tensor_alloc` in `_RUNTIME_FN_ATTRS` if missing. Declare with `noalias` on the return, `nounwind`.
- [ ] Emit the calls from the lowered tensor literal MIR.

## Phase 7 — Self-hosted mirror

- [ ] `mapanare/self/ast.mn` — `TensorLiteral` AST node
- [ ] `mapanare/self/parser.mn` — tensor literal parsing + jagged detection
- [ ] `mapanare/self/semantic.mn` — shape + element-type check
- [ ] `mapanare/self/lower.mn` — same allocate + store lowering
- [ ] `mapanare/self/emit_llvm.mn` — runtime declarations mirrored (closing the v4.32.0 parity discipline for new symbols)
- [ ] **Byte-identity invariant:** after adding tensor literal lowering, fixed-point diff stays at 0 lines

## Phase 8 — Tests

- [ ] `tests/golden/49_tensor_literal.mn` — a program that constructs 1-D, 2-D, and 3-D tensors and prints a few elements
- [ ] `tests/parser/test_tensor_literal.py` — parse cases + jagged detection
- [ ] `tests/semantic/test_tensor_literal.py` — shape mismatch, element type mismatch
- [ ] `tests/llvm/test_tensor_literal.py` — end-to-end compile + run

## Phase 9 — Delta review

- [ ] Prep `.reviews/deltas/v4.42.0-tensor-literal.md` with the grammar diff, AST additions, semantic rules, lowering path.
- [ ] Rattler reviews the lowering + runtime crossing.
- [ ] Coral reviews the syntactic choice (`Tensor<T>[elements]` vs alternative forms).

## Phase 10 — LOW sweep

2 items from the running ledger.

## Phase 11 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.42.0
- [ ] `CHANGELOG.md [4.42.0]`
- [ ] `docs/SPEC.md §3.10` tensor section updated with literal syntax (don't update the "Status" line yet — that closes in v4.44.0 when broadcasting lands)
- [ ] `docs/cookbook.md` §Tensors — new subsection
- [ ] SESSION_REPORT

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Grammar accepts 1-D, 2-D, 3-D tensor literals | parser tests |
| 2 | Jagged arrays rejected with rustc-quality error | `test_jagged_array_is_parse_error` |
| 3 | Shape consistency with annotation enforced | `test_shape_mismatch_is_semantic_error` |
| 4 | Element type consistency enforced | `test_element_type_mismatch_is_error` |
| 5 | `__mn_tensor_alloc` wired into runtime | grep runtime source |
| 6 | CPU fallback works when GPU absent | `test_cpu_fallback_allocation` |
| 7 | 1-D tensor literal compiles and runs | `tests/llvm/test_tensor_literal.py::test_1d` |
| 8 | 2-D tensor literal compiles and runs | `test_2d` |
| 9 | 3-D tensor literal compiles and runs | `test_3d` |
| 10 | Empty tensor `Tensor<Float>[0]` works | `test_empty_tensor` |
| 11 | Drop glue frees tensor buffers (no valgrind leak) | `test_tensor_drop_glue_valgrind_clean` |
| 12 | Self-hosted mirror parses and lowers tensor literals | 45/45+ golden through mnc-stage1 |
| 13 | Fixed-point diff still 0 lines | `verify_fixed_point.sh` |
| 14 | Delta review returns PASS | `.reviews/deltas/v4.42.0-tensor-literal.md` |
| 15 | Standard closeout clean | CI logs |

---

## What v4.42.0 does NOT do

- **Tensor indexing** — v4.43.0
- **Tensor broadcasting** — v4.44.0
- **Tensor reductions, slicing, views** — v4.45.0
- **Tensor literal as nested tensors** (`Tensor<Tensor<Float>[3]>[2]`) — out of scope; scalars only in v4.42.0
- **Tensor comprehensions** (`Tensor<Float>[i * 2 for i in 0..10]`) — v5.x if ever
- **SPEC §3.10 Status line update** — moves to "Stable" in v4.44.0 when broadcasting lands

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Grammar conflict between tensor literal and list literal | low | medium | Phase 1 confirms via parser test; the `Tensor<T>` prefix disambiguates |
| `__mn_tensor_alloc` signature changes break v4.28.0 matmul | low | high | Don't change the signature; add new runtime functions if needed |
| CPU fallback allocation leaks on early-return | low | medium | Drop glue test in Phase 8; valgrind check |
| Jagged detection has edge cases | medium | low | Comprehensive parser tests |

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 3
- [`v4.28.0/SESSION_REPORT.md`](../v4.28.0/SESSION_REPORT.md) — matmul runtime work; the tensor runtime primitives this builds on
- NumPy array creation reference — https://numpy.org/doc/stable/reference/routines.array-creation.html (for semantic reference)

---

## After v4.42.0

v4.43.0 adds tensor indexing `t[i, j, k]` with runtime bounds checking.
