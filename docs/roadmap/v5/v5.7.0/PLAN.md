# Mapanare v5.7.0 — "Sh.6: Self-Hosted Tensor"

> **Port `Tensor` / `Float` types and nested-array literal parsing
> from Python bootstrap to `mapanare/self/`.** Closes Sh.6 (5 failing
> native goldens). The tensor surface (literals, indexing,
> broadcasting, reductions, slicing) is stable since v4.45.0 on the
> Python side; the self-hosted compiler frontend is missing it.

**Status:** PLANNED
**Breaking:** No (tensor surface unchanged; self-hosted compiler
gains support for already-spec'd syntax)
**Prerequisite:** v5.6.0 shipped (Sh.4 async closed)
**Estimated work:** 3–4 sessions (~7–10 hours). Largest of the v5.6–
v5.8 feature-parity arc because it touches lexer + parser.
**Owner docket:** Sh.6 (opened v4.111.0; "v5.x feature track" since
PARITY_GAPS.md:141)

---

## Why this release exists

### The failing goldens

Per `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md`:

| Test | Error |
|---|---|
| `49_tensor_literal` | `Undefined function 'tensor_rank'`, `Undefined variable 'Tensor'` |
| `50_tensor_indexing` | `parse error: expected RPAREN but got RBRACKET` (nested-array `[[1,2],[3,4]]`) |
| `51_tensor_broadcast` | `Undefined variable 'Tensor'`, `Undefined variable 'Float'` |
| `52_tensor_slicing` | `Undefined variable 'Float'`, `Undefined variable 'Tensor'` |
| `53_linear_regression` | `Undefined variable 'Tensor'` |

Three distinct gaps in the self-hosted compiler:

1. **Grammar:** `parser.mn` doesn't recognize nested-array literal
   syntax `[[1,2],[3,4]]` as a tensor literal.
2. **Semantic:** `semantic.mn` doesn't register `Tensor` or `Float`
   as types, and doesn't register tensor builtins (`tensor_rank`,
   `tensor_shape`, `tensor_reshape`, etc.).
3. **Lowering:** `lower.mn` doesn't lower `TensorLit` AST nodes to
   MIR `TensorInit` instructions.

The Python bootstrap handles all three since v4.45.0. The C runtime
has `__mn_tensor_*` functions complete.

### Sizing

Tensor is the largest feature gap of the v5.6–v5.8 arc. The Python
lowerer has ~500 LOC of tensor-specific handling; `emit_llvm_text.py`
has ~400 LOC of tensor emission. Porting faithfully is a
multi-session task.

---

## Scope

### What ships

#### 7.0a — Nested-array literal in grammar (lexer + parser)

`mapanare/self/lexer.mn` — verify `LBRACKET`/`RBRACKET` tokens
already exist (they do, for lists). No lexer changes expected.

`mapanare/self/parser.mn` — tensor literals are disambiguated from
list literals by content:
- `[1, 2, 3]` — 1D tensor or list (context-dependent)
- `[[1,2],[3,4]]` — 2D tensor literal
- `[[[1]]]` — 3D tensor literal

Python bootstrap disambiguates via type annotation (`let t: Tensor<F>
= [...]`) or via semantic-check post-pass. Mirror whichever Python
does. If Python type-annotates to disambiguate, the parser produces
a generic `ListLit` node and semantic converts based on declared
type. If Python has a parser-level `TensorLit` node, port it.

```bash
# Reference check
grep -n "TensorLit\|nested_list\|parse_tensor" mapanare/parser.py
grep -n "TensorLit" mapanare/self/ast.mn
```

Expected: self-hosted `ast.mn` already has `TensorLit` node (since
the Python-side feature pre-dates the v4.45.0 self-hosted arc start).
If so, just port the parser rule.

#### 7.0b — Register `Tensor` / `Float` types

`mapanare/self/semantic.mn::register_builtins` — add:

```mapanare
s = register_builtin_type(s, "Tensor", TypeKind::TENSOR)
s = register_builtin_type(s, "Float", TypeKind::FLOAT)

// Tensor builtins
s = register_builtin_fn(s, "tensor_rank",    fn_type(tensor_t, int_t))
s = register_builtin_fn(s, "tensor_shape",   fn_type(tensor_t, list_int_t))
s = register_builtin_fn(s, "tensor_reshape", ...)
s = register_builtin_fn(s, "tensor_slice",   ...)
// ... mirror semantic.py
```

#### 7.0c — Lower tensor expressions

`mapanare/self/lower.mn` — new handlers:

- `lower_tensor_lit(s, data)` → MIR `TensorInit` instruction
- `lower_tensor_index(s, data)` → MIR tensor-index call
- `lower_tensor_method(s, data)` → dispatch `reshape`, `slice`, etc.

Use Python `lower.py::_lower_tensor_*` as the spec.

#### 7.0d — Emit tensor intrinsics

`mapanare/self/emit_llvm.mn::declare_all_runtime` — declare the
`__mn_tensor_*` family:

```mapanare
s = declare_runtime_fn(s, "__mn_tensor_create", ptr_t, "i64, ptr, i64, ptr")
s = declare_runtime_fn(s, "__mn_tensor_rank", int_t, "ptr")
s = declare_runtime_fn(s, "__mn_tensor_shape", ptr_t, "ptr")
s = declare_runtime_fn(s, "__mn_tensor_reshape", ptr_t, "ptr, ptr, i64")
s = declare_runtime_fn(s, "__mn_tensor_index", ptr_t, "ptr, ptr, i64")
// ... and more
```

`emit_instr` dispatch — add `tensor_init` handler emitting
`__mn_tensor_create` call with shape + flat-data pointer.

**Expected LOC:**

| File | ~LOC |
|---|---:|
| `parser.mn` — tensor literal rule | ~80 |
| `semantic.mn` — type + builtin registration | ~80 |
| `lower.mn` — tensor handlers | ~250 |
| `emit_llvm.mn` — runtime declarations + emission | ~180 |
| **Total** | **~590** |

### What does NOT ship

- **Tensor reshape** (if still "not yet on LLVM" per CLAUDE.md). If
  Python doesn't support it, self-hosted doesn't either.
- **Mutable views / stepped slices.** Python-side deferred per
  CLAUDE.md; stays deferred.
- **GPU tensor dispatch.** `stdlib/gpu/tensor.mn` uses
  `@gpu`/`@cuda`/`@vulkan` decorators already ported — no new work.
- **New tensor syntax.** Everything spec'd already.

---

## Exit criteria

1. 5 Sh.6 goldens compile via `mnc-stage1` without error.
2. Compiled IR passes `llvm-as`.
3. Compiled + lli-executed output matches Python bootstrap for all 5.
4. 15+ parser tests for nested-array literal syntax.
5. Strict 3-stage fixed-point holds.
6. Non-bootstrap pytest 0 failures.
7. `make lint` clean.
8. `PARITY_GAPS.md` moves Sh.6 to Historical.

---

## Design decisions

### D1 — Mirror Python's disambiguation

Whatever Python uses to distinguish `[1,2,3]` as list vs tensor,
self-hosted copies. Type annotation is most likely
(`let x: Tensor<Int> = [1,2,3]`). Parser produces `ListLit`; semantic
rewrites to `TensorLit` based on declared type.

### D2 — Float vs Int tensor elements

Python `Tensor<Float>` and `Tensor<Int>` have different runtime
storage (f64 vs i64 arrays). Self-hosted emitter must produce the
correct `__mn_tensor_create` arguments (element-size + elem-type tag).
Cross-reference `mapanare_tensor.c` for the expected constants.

### D3 — No new MIR instruction unless Python has one

If Python lowers `t.reshape(shape)` to `Call("tensor_reshape", [t,
shape])`, self-hosted does the same. Only add new MIR kinds if the
Python side has them.

### D4 — Tests

Reuse the 5 Sh.6 goldens. Add a dedicated parser test file
`tests/parser/test_tensor_literals.py` with 15+ cases: 1D, 2D, 3D,
mixed numeric types, empty dim, malformed (parse error recovery).

---

## Risks

- **R1 — Parser precedence collision with list literal.** Making
  `[[1,2],[3,4]]` parse as nested-list-of-lists is straightforward;
  the question is whether semantic can always disambiguate. If not,
  add a `TensorLit` AST node with parser fallback.
- **R2 — Float ABI.** `Tensor<Float>` boxed vs unboxed storage
  depends on element size. Mirror Python exactly.
- **R3 — Fixed-point breaks** as new emission enters stage2.ll.
  Mitigation: verify after every helper.
- **R4 — Runtime signature drift.** `__mn_tensor_*` is stable since
  v4.45.0; low risk. Double-check in `runtime/native/mapanare_tensor.c`.

---

## What NOT to do

- Do not add tensor reshape/view/slice features if Python bootstrap
  doesn't already have them.
- Do not touch `runtime/native/mapanare_tensor.c`. It's complete.
- Do not invent MIR instructions without checking Python.
- Do not skip the 15-test parser test file — tensor grammar
  regressions are easy to introduce and hard to debug later.
