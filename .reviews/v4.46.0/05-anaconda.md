# Anaconda -- Toolchain Review of Mapanare v4.46.0

**Reviewer:** Anaconda
**Personality:** The Bureaucrat -- structured, formal, references GCC/POSIX standards and compiler engineering norms
**Previous Version Reviewed:** v4.41.0 (score 8.9/10, PASS -- Arc 2 cadence panel, LSP maturity)
**Panel Role:** Arc 3 cadence panel. Grades the tensor completeness arc (v4.42.0-v4.45.0). Four feature releases delivering tensor literals, multi-dimensional indexing, broadcasting, reductions, and slicing.
**Verdict:** **PASS**
**Score:** **9.2 / 10**
**Confidence:** 9/10
**Files Reviewed (verified byte-level against the repo):**

- `VERSION` -- reads `4.45.0`
- `CHANGELOG.md` -- lines 9-118 (v4.42.0 through v4.45.0 entries)
- `mapanare/mapanare.lark` -- 516 lines (full file); grammar rules including `tensor_literal`, `tensor_type`, `tensor_body`, `tensor_nested`, `tensor_atom`, `tensor_neg`, `index_expr`
- `mapanare/ast_nodes.py` -- full file; `TensorLiteral` (301-310), `IndexItem` (205-216), `IndexExpr` (219-228), `TensorType` (67-71)
- `mapanare/parser.py` -- lines 775-912; `index_expr`, `tensor_literal`, `tensor_body`, `tensor_nested`, `tensor_neg`
- `mapanare/semantic.py` -- lines 531-590 (IndexExpr/tensor indexing/slicing), lines 673-751 (tensor binary ops + broadcasting), lines 1309-1346 (`_check_tensor_literal`)
- `mapanare/types.py` -- lines 443-480 (`broadcast_shape`, `broadcast_incompatible_dim`)
- `mapanare/mir.py` -- lines 296-307 (`TensorInit` dataclass)
- `mapanare/lower.py` -- lines 2195-2227 (tensor reductions), lines 2412-2564 (`_lower_index`, `_lower_tensor_get`, `_lower_tensor_set`, `_lower_tensor_slice`, `_lower_tensor_binop`), lines 2755-2782 (`_lower_tensor_literal`)
- `mapanare/emit_llvm_text.py` -- lines 324-383 (function attributes for 40+ tensor runtime declarations), lines 509-533 (`_tensor_vars` tracking, dispatch registration), lines 1148-1183 (tensor cleanup in function epilogue), lines 1524-1563 (`_emit_drop_glue_tensors`), lines 3349-3395 (`_do_tensor_init`)
- `mapanare/optimizer.py` -- lines 381-393, 627-640 (`IndexItem` migration in constant folding and DCE)
- `mapanare/linter.py` -- lines 253-265, 349-362 (`IndexItem` migration in name collection)
- `mapanare/lsp/analysis.py` -- lines 679-691 (`IndexItem` migration in document analysis)
- `mapanare/self/ast.mn` -- lines 87-502; `TensorLit` variant in `Expr` enum, accessor functions
- `mapanare/self/parser.mn` -- lines 1910-1915, 2241-2264; `parse_tensor_lit`
- `mapanare/self/mir.mn` -- lines 36, 189, 514, 561, 661-669; `TensorInit` variant, accessor functions
- `mapanare/self/lower.mn` -- lines 1206-1207, 2839-2861; `lower_tensor`
- `mapanare/self/emit_llvm.mn` -- lines 301-305, 412-423, 525-530, 819, 880-890; `emit_tensor_init` (stub)
- `mapanare/self/semantic.mn` -- lines 34, 114, 444, 470-471, 657-673, 759-846; tensor type checking
- `mapanare/self/lower_state.mn` -- line 461; `TK_TENSOR` resolution
- `tests/parser/test_tensor_literal.py` -- 13 tests
- `tests/parser/test_tensor_indexing.py` -- 5 tests
- `tests/semantic/test_tensor_literal.py` -- 7 tests
- `tests/semantic/test_tensor_indexing.py` -- 8 tests
- `tests/semantic/test_tensor_broadcast.py` -- 17 tests
- `tests/semantic/test_tensor_shapes.py` -- 5 tests
- `tests/semantic/test_tensor_slicing.py` -- 7 tests
- `tests/llvm/test_tensor_literal.py` -- 12 tests
- `tests/llvm/test_tensor_indexing.py` -- 7 tests
- `tests/llvm/test_tensor_broadcast.py` -- 9 tests
- `tests/llvm/test_tensor_reductions.py` -- 10 tests
- `tests/tensor/test_tensor.py` -- 67 tests (Python runtime layer)
- `tests/golden/49_tensor_literal.mn` -- golden test
- `tests/golden/50_tensor_indexing.mn` -- golden test
- `tests/golden/51_tensor_broadcast.mn` -- golden test
- `tests/golden/52_tensor_slicing.mn` -- golden test
- `tests/golden/53_linear_regression.mn` -- golden test (demo)
- `docs/roadmap/v4/v4.46.0/PRE_PANEL_AUDIT.md` -- 18/19 claims PASS

---

## Executive Summary

Arc 3 (v4.42.0-v4.45.0) delivers a tensor language surface that flows cleanly through the full compiler pipeline: grammar extension in `mapanare.lark`, AST representation in `ast_nodes.py`, parse-time shape inference in `parser.py`, semantic type checking with NumPy-compatible broadcasting in `semantic.py` and `types.py`, MIR representation via `TensorInit` in `mir.py`, lowering to runtime calls in `lower.py`, and LLVM IR emission with proper drop glue in `emit_llvm_text.py`. The self-hosted compiler mirrors the Python bootstrap at each stage, though with reduced fidelity (1D tensor literals only, `emit_tensor_init` is a null-ptr stub).

I score this arc 9.2/10, up 0.3 from v4.41.0. The improvement reflects an arc with clean pipeline integration (every compiler phase was touched and wired correctly), a well-designed `IndexItem` AST node that handles three index kinds without grammar ambiguity, and a proper broadcasting implementation with rustc-quality diagnostics. The delta from 10.0 reflects one MEDIUM issue (the self-hosted `emit_tensor_init` emits a null pointer, meaning the self-hosted compiler cannot actually construct tensors), one MEDIUM issue (scalar-tensor subtraction/division operand order is semantically incorrect), and two LOW items. The MEDIUM issues are acceptable technical debt for an arc focused on the Python bootstrap path, but they are debt that must be acknowledged.

The 167 tensor-specific tests across 12 files, plus 5 golden test programs, provide comprehensive coverage of the happy path and several error paths. The pre-panel audit's 18/19 PASS rate with a well-documented FAIL (mean_i64 omission) is honest engineering.

---

## Section 1: Grammar Extension -- LALR Property Preserved

### 1.1 Tensor Literal Rule -- CORRECT

The `tensor_literal` rule at `mapanare.lark:356` is:

```
tensor_literal: KW_TENSOR LT type_expr GT LBRACKET tensor_body RBRACKET
```

This is unambiguous in an LALR(1) grammar because the sequence `KW_TENSOR LT` is uniquely identifiable. `KW_TENSOR` is declared as a contextual keyword with exact match `"Tensor"` (line 424), distinguishing it from `NAME`. The `LT` after `KW_TENSOR` cannot conflict with comparison because `KW_TENSOR` is not a valid left-hand side of a comparison expression (it is not in any `?expr` chain as an `atom_expr`). The `LBRACKET` after `GT` completes the type prefix and begins the data section.

**LALR verdict:** PASS. The grammar generates no shift/reduce or reduce/reduce conflicts. Lark would fail at grammar compilation time if it did, and the parser tests confirm successful parsing. The technique of introducing a keyword terminal (`KW_TENSOR`) as a prefix disambiguator is the standard approach (cf. GCC's `__attribute__` keyword, which serves the same function in C's LALR grammar).

### 1.2 Tensor Body Sub-Grammar -- WELL-DESIGNED

The tensor body rules (`tensor_body`, `tensor_nested`, `tensor_atom`, `tensor_neg`) at lines 357-361 are carefully factored:

```
tensor_body: tensor_elem (COMMA tensor_elem)* COMMA?
?tensor_elem: LBRACKET tensor_body RBRACKET -> tensor_nested
            | tensor_atom
?tensor_atom: int_lit | float_lit | ident | paren_expr
            | MINUS tensor_atom -> tensor_neg
```

The `tensor_atom` production excludes `list_lit` (which would create an LALR conflict with `tensor_nested`, since both start with `LBRACKET`). This is documented in the comment at line 354: "v4.42.0: tensor_atom excludes list_lit to avoid LALR ambiguity." The restriction is that compound expressions inside tensor literals must be parenthesized: `Tensor<Float>[(1 + 2), 4, 5]`. This is a reasonable trade-off between grammar simplicity and user convenience. Per ISO/IEC 9899:2018 (C23) section 6.7.9, even C requires compound initializers inside braces to be simple constant expressions without operator precedence parsing, so Mapanare's restriction is no worse than C's designated initializers.

### 1.3 Index Expression Rule -- MULTI-INDEX EXTENSION CLEAN

The `index_expr` rule at line 269 is:

```
postfix_expr LBRACKET expr (COMMA expr)* RBRACKET -> index_expr
```

This allows `a[0]`, `a[0, 1]`, `a[0..2, _]`, and `a[0, 1, 2]`. The comma-separated list of `expr` naturally supports scalars (integer literals, identifiers), ranges (`0..2` via `range_expr`), and wildcards (`_` as `KW_WILDCARD`, which is an `ident` in this context). The parser transformer at `parser.py:775-790` distinguishes these three cases by inspecting the parsed `Expr` nodes:

- `RangeExpr` -> `IndexItem(kind="range")`
- `Identifier(name="_")` -> `IndexItem(kind="wildcard")`
- Any other `Expr` -> `IndexItem(kind="scalar")`

This is an elegant design: the grammar does not need to know about tensor-specific index kinds; the parser transformer applies the domain semantics after parsing. Per the Dragon Book (Aho, Lam, Sethi, Ullman, section 4.3), this separation of syntactic parsing from semantic classification in the tree construction phase is correct practice for LALR parsers.

### 1.4 Tensor Type Rule -- CORRECT

The `tensor_type` rule at line 178 is:

```
tensor_type: KW_TENSOR LT type_expr GT LBRACKET expr (COMMA expr)* RBRACKET
```

This correctly uses `expr` (not `int_lit`) for shape dimensions, allowing both static shapes (`Tensor<Float>[3, 4]`) and dynamic shapes (`Tensor<Float>[n, m]`). The semantic checker resolves static vs. dynamic at type-check time (via `resolve_shape_from_type` in `types.py`).

---

## Section 2: AST Migration -- `IndexExpr.index` to `IndexExpr.indices`

### 2.1 Migration Scope -- COMPREHENSIVE

The v4.43.0 migration from `IndexExpr.index: Expr` (single index) to `IndexExpr.indices: list[IndexItem]` (multi-index with kind discrimination) touched 13 call sites across 6 modules:

| Module | Call sites | Pattern |
|--------|-----------|---------|
| `parser.py` | 1 | `index_expr` transformer builds `IndexItem` list |
| `semantic.py` | 3 | `_infer_expr` walks `IndexItem.kind` for rank checking and slice detection |
| `lower.py` | 4 | `_lower_index`, `_lower_tensor_slice`, and assignment lowering |
| `optimizer.py` | 2 | Constant folding and DCE name collection |
| `linter.py` | 2 | Name collection for unused variable detection |
| `lsp/analysis.py` | 1 | Document analysis expression visitor |

The CHANGELOG at line 33 claims "14 call sites" and line 78 repeats "all 14 visitor call sites migrated." I count 13 distinct `IndexItem` import-and-use sites across these 6 modules. The discrepancy of 1 is likely counting the `IndexExpr.indices` field definition itself or the `mir_opt.py` references to `inst.index` on `IndexGet`/`IndexSet` (which is a different field -- the MIR instruction's index operand, not the AST node's indices list). This is a minor accounting imprecision in the CHANGELOG, not a migration gap.

### 2.2 Migration Pattern -- CONSISTENT

Every migrated call site follows the same pattern:

```python
from mapanare.ast_nodes import IndexItem

for it in expr.indices:
    if isinstance(it, IndexItem):
        if it.kind == "scalar" and it.expr:
            # process scalar index
        elif it.kind == "range":
            # process range start/end
        elif it.kind == "wildcard":
            # process wildcard
    elif isinstance(it, Expr):
        # legacy fallback
```

The `isinstance(it, Expr)` fallback branch appears in `lower.py:2432` and `semantic.py:548`. This is defensive coding against the possibility of raw `Expr` objects appearing in the `indices` list (e.g., from a pre-v4.45.0 code path). The fallback is harmless (it processes the expression as a scalar index) and will be dead code once all producers always emit `IndexItem` wrappers. The `from mapanare.ast_nodes import IndexItem` inside function bodies (not at module level) is done consistently across all 6 modules, which avoids circular imports and keeps the `IndexItem` import lazy.

### 2.3 No Residual `IndexExpr.index` Usages -- VERIFIED

I searched for `.index` accesses on `IndexExpr` and found zero residual usages. The `inst.index` references in `mir_opt.py`, `emit_c.py`, `emit_wasm.py`, `emit_python_mir.py`, and `emit_llvm_text.py` are on `IndexGet` and `IndexSet` MIR instructions, which have their own `index: Value` field. These are unrelated to the `IndexExpr.index -> IndexExpr.indices` migration.

---

## Section 3: `IndexItem` AST Node Design -- RIGHT Abstraction

### 3.1 Three Kinds -- MINIMAL AND COMPLETE

The `IndexItem` dataclass at `ast_nodes.py:205-216` uses a string-discriminated kind field:

```python
@dataclass
class IndexItem(ASTNode):
    kind: str = "scalar"    # "scalar" | "range" | "wildcard"
    expr: Expr | None = None       # scalar value
    start: Expr | None = None      # range start
    end: Expr | None = None        # range end
```

The three kinds -- scalar, range, wildcard -- map precisely to the three index operations that NumPy and TensorFlow support:

| Kind | NumPy equivalent | Mapanare syntax | Example |
|------|-----------------|-----------------|---------|
| scalar | `a[0, 1]` | `a[0, 1]` | Element access |
| range | `a[0:2, :]` | `a[0..2, _]` | Slice with bounds |
| wildcard | `a[:, 0]` | `a[_, 0]` | Full dimension |

This covers the tensor indexing surface defined in SPEC section 3.10. It does NOT cover stepped slices (`a[0:10:2]` in NumPy), which the CLAUDE.md correctly documents as deferred to v5.x ("Tensor reshape, mutable views, stepped slices").

### 3.2 Alternative Designs Considered

A sum type (enum-like) approach would be cleaner in a language with discriminated unions:

```
enum IndexItem { Scalar(Expr), Range(Expr, Expr), Wildcard }
```

Python's `@dataclass` with string discrimination is the pragmatic equivalent. The alternative of using subclasses (`ScalarIndex(IndexItem)`, `RangeIndex(IndexItem)`, `WildcardIndex(IndexItem)`) would add three more classes to `ast_nodes.py` for minimal benefit. The chosen design is correct for a Python dataclass AST representation.

### 3.3 The `expr | None` Field Multiplicity

The `IndexItem` has three optional `Expr` fields (`expr`, `start`, `end`), of which only a subset is meaningful for each kind:

| Kind | `expr` | `start` | `end` |
|------|--------|---------|-------|
| scalar | used | None | None |
| range | None | used | used |
| wildcard | None | None | None |

This means a malformed `IndexItem(kind="scalar", start=some_expr)` would be silently accepted. This is a type safety concern, not a correctness bug -- the parser transformer at `parser.py:781-789` always constructs well-formed `IndexItem` values. A stricter design would use `assert` guards in `IndexItem.__post_init__`, but this is a LOW concern for a dataclass AST that is only constructed by the parser.

---

## Section 4: Parser Tensor Literal Handling (`parser.py:838-895`)

### 4.1 Shape Inference at Parse Time -- CORRECT PLACEMENT

Shape inference (counting elements at each nesting depth and detecting jagged arrays) is performed at parse time in `tensor_literal` (line 857-894) via the recursive `_walk` helper. This is the right place for three reasons:

1. **Jagged array detection is a parse error, not a type error.** A tensor literal `[[1, 2], [3]]` is structurally malformed -- no valid type can represent it. GCC similarly rejects `int a[2][3] = {{1,2,3},{4,5}}` at parse time, not during type checking.

2. **The shape is a compile-time constant.** The nesting structure of the literal determines the shape, and this is known at parse time. Deferring shape inference to the semantic checker would require the semantic checker to re-walk the nested list structure, duplicating the parser's work.

3. **The flat element list is needed for MIR.** The `TensorInit` MIR instruction expects a flat `elements: list[Value]` in row-major order. The parser's `_walk` function performs the flattening during shape inference, producing both `shape` and `flat` in a single pass. This is efficient.

### 4.2 Error Reporting -- ADEQUATE

The jagged array error at line 878 reports:

```
tensor literal shape mismatch at depth {depth}: expected {shape[depth]} elements, got {len(nodes)}
```

This includes the depth (dimension number) and the expected vs. actual counts. It uses `ParseError` with `line` and `column` from the tensor literal's span, which means the error points to the opening `Tensor<` token rather than the offending sub-array. More precise error reporting would require tracking per-element spans in the recursive walk, which is reasonable future work.

### 4.3 The `_walk` Recursive Design -- CORRECT

The `_walk(nodes, depth)` function at line 873 correctly:
1. Extends `shape` on first encounter of a new depth
2. Validates that subsequent sub-arrays at the same depth have the same length
3. Recurses for list-typed nodes (nested sub-arrays)
4. Appends to `flat` for Expr-typed nodes (leaf elements)
5. Ignores Token/non-Expr items (commas, brackets)

The recursion depth is bounded by the nesting depth of the literal, which is typically 1-4 for practical tensors. There is no explicit recursion limit, but Lark's parse tree depth already constrains this.

---

## Section 5: Semantic Broadcasting Rules (`semantic.py` + `types.py`)

### 5.1 `broadcast_shape()` -- NumPy-Compatible

The `broadcast_shape` function at `types.py:443-466` implements the NumPy broadcasting rules exactly as specified in the NumPy documentation ("General Broadcasting Rules"):

1. Left-pad the shorter shape with 1s to equalize rank
2. For each dimension, the sizes must be equal OR one of them must be 1
3. The output dimension is `max(a_i, b_i)`
4. Return `None` if incompatible

The test suite at `tests/semantic/test_tensor_broadcast.py:17-47` covers the canonical NumPy broadcasting examples: same shape, row-column (`(3,1)+(1,4)`), rank extension (`(3,4)+(4,)`), scalar-like (`(1,)+(5,)`), 3D-1D (`(2,3,4)+(4,)`), complex (`(5,1,4)+(1,3,1)`), and incompatible cases. These test cases are drawn directly from the NumPy broadcasting documentation examples.

**Conformance verdict:** PASS. The implementation matches numpy.broadcast_shapes behavior for all tested cases.

### 5.2 `broadcast_incompatible_dim()` -- Rustc-Quality Diagnostics

The companion function `broadcast_incompatible_dim` at `types.py:469-480` returns the 0-based dimension index where broadcasting fails. This is used at `semantic.py:712-728` to produce errors like:

```
shapes [3, 4] and [3, 5] are not broadcast-compatible for '+'; dimension 1 differs: 4 vs 5
```

This is modeled after rustc's approach of naming the specific dimension in mismatched type errors (e.g., `expected [f64; 3], found [f64; 5]`). The left-padding of both shapes before dimension comparison ensures that the dimension index corresponds to the broadcast-aligned dimension, not the original tensor's dimension, which is correct for user comprehension.

### 5.3 Semantic Tensor Binary Op Checking -- COMPREHENSIVE

The tensor binary op checking at `semantic.py:673-751` handles four cases:

1. **Tensor + Tensor (same shape):** No error, result type inherits tensor shape
2. **Tensor + Tensor (broadcastable):** No error, result type gets broadcast shape
3. **Tensor + Tensor (incompatible):** Error with dimension detail
4. **Tensor + Scalar / Scalar + Tensor:** No error, result type inherits tensor shape

All four arithmetic operators (`+`, `-`, `*`, `/`) are covered by the `_TENSOR_ARITH_OPS` set (checked at line 687). The matmul operator (`@`) is handled separately at `semantic.py:822-846` with appropriate shape validation.

### 5.4 Tensor Index Rank Checking -- CORRECT

The index rank checking at `semantic.py:552-558` correctly enforces that the number of indices matches the tensor's rank:

```python
if rank is not None and n_idx != rank:
    self._error(f"tensor index rank mismatch: got {n_idx} indices for rank-{rank} tensor", expr)
```

The `rank is not None` guard handles dynamically-shaped tensors (where `tensor_shape` is `None`). This mirrors NumPy's behavior: `a[0]` on a 2D array is valid (returns a row), but Mapanare's stricter tensor semantics require all dimensions to be indexed. This is a design choice documented in the SPEC and consistent with TensorFlow's static tensor indexing.

---

## Section 6: MIR `TensorInit` Instruction (`mir.py:296-307`)

### 6.1 Design -- CLEAN

```python
@dataclass(slots=True)
class TensorInit(Instruction):
    dest: Value = field(default_factory=Value)
    elem_type: MIRType = field(default_factory=mir_unknown)
    shape: list[int] = field(default_factory=list)
    elements: list[Value] = field(default_factory=list)
```

The `TensorInit` instruction captures exactly the information needed by the LLVM emitter:

- `dest`: The SSA value name for the allocated tensor
- `elem_type`: Element type (for choosing `store_f64` vs `store_i64`)
- `shape`: Compile-time shape (always known for tensor literals)
- `elements`: Flattened element values in row-major order

This instruction is at the right abstraction level: it represents "construct a tensor with this shape and these elements," leaving the allocation strategy (stack vs heap, arena vs malloc) to the emitter. The emitter at `emit_llvm_text.py:3349` translates this to:

1. Stack-allocate shape array: `[N x i64]`
2. `__mn_tensor_alloc(rank, shape_ptr, elem_size)` -> heap tensor
3. `__mn_tensor_store_{f64,i64}(tensor, index, value)` per element

### 6.2 `slots=True` -- CORRECT OPTIMIZATION

All MIR instruction dataclasses use `@dataclass(slots=True)`, which is a Python 3.10+ optimization that generates `__slots__` from field names. This reduces per-instance memory by ~40% and speeds attribute access by ~20%. For a compiler that may generate thousands of MIR instructions, this is the correct choice. GCC's internal GIMPLE tuples use a similar packed representation.

### 6.3 No `TensorSlice` or `TensorReduce` MIR Instructions -- DELIBERATE

Notably, there is no `TensorSlice` or `TensorReduce` MIR instruction. Slicing and reductions are lowered directly to `Call` instructions in `lower.py:2491-2527` and `lower.py:2218-2226`. This is a valid design: `TensorInit` exists because it requires structured emission (shape array allocation + multiple store calls), while slicing and reductions are single runtime calls that `Call` represents naturally.

If future optimization passes need to reason about tensor operations (e.g., fusing a slice followed by a reduction), dedicated MIR instructions would be needed. But for the current "lower to runtime calls" strategy, using `Call` is the simpler and correct approach.

---

## Section 7: Tensor Lowering (`lower.py`)

### 7.1 `_lower_tensor_literal` -- CORRECT

The tensor literal lowering at `lower.py:2755-2782` correctly:
1. Lowers each element expression to a MIR `Value`
2. Determines element MIR type from the AST `element_type`
3. Constructs a `MIRType` with `TypeKind.TENSOR`, element type argument, and shape tuple
4. Emits a `TensorInit` instruction

The element type resolution at lines 2766-2774 handles `Float/float`, `Int/int`, `Bool/bool` with a default to `Float`. The default is consistent with NumPy's default dtype (`float64`).

### 7.2 `_lower_tensor_binop` -- ISSUE: Non-Commutative Operator Order (MEDIUM)

The tensor binary op lowering at `lower.py:2536-2564` handles both tensor-tensor and tensor-scalar cases. For scalar-tensor operations (e.g., `5.0 - tensor`), line 2559-2563 swaps the operands:

```python
# scalar + tensor -> rewrite as tensor + scalar (commutative for +/*)
# For -/div, this is wrong conceptually but matches NumPy's broadcasting
# (scalar is promoted to a tensor). We swap and negate if needed.
dest = self._make_value(ty=rhs.ty, prefix="tsop")
self._emit(Call(dest=dest, fn_name=fn_name, args=[rhs, lhs]))
```

The comment acknowledges that `5.0 - tensor` is rewritten as `__mn_tensor_sub_scalar_f64(tensor, 5.0)`, which computes `tensor - 5.0`, not `5.0 - tensor`. This is **incorrect for subtraction and division**. The runtime function `__mn_tensor_sub_scalar_f64(tensor, scalar)` computes `tensor[i] - scalar`, not `scalar - tensor[i]`.

The comment says "matches NumPy's broadcasting (scalar is promoted to a tensor)" but NumPy does NOT swap operands for non-commutative ops. `5.0 - np.array([1,2,3])` returns `[4, 3, 2]` in NumPy, not `[-4, -3, -2]`.

**Impact:** Any Mapanare program that writes `scalar - tensor` or `scalar / tensor` will get the wrong result. The expression `5.0 - Tensor<Float>[1.0, 2.0, 3.0]` will produce `[-4.0, -3.0, -2.0]` instead of `[4.0, 3.0, 2.0]`.

**Recommendation:** Add a `__mn_tensor_rsub_scalar_f64` and `__mn_tensor_rdiv_scalar_f64` runtime function, or negate/reciprocate the result after swapping. The fix is straightforward but requires a new runtime function or a post-swap correction.

**Severity:** MEDIUM. Incorrect results for non-commutative scalar-tensor expressions. No test covers `scalar - tensor` or `scalar / tensor` (only `tensor - scalar` and `tensor / scalar` are tested), so the bug is undetected.

### 7.3 `_lower_tensor_slice` -- CORRECT

The slice lowering at `lower.py:2491-2528` correctly:
1. Iterates over `IndexItem` list
2. For `"range"` items: lowers `start` and `end` expressions
3. For `"wildcard"` items: emits `tensor_shape_dim(obj, d)` to get the dimension size
4. For `"scalar"` items in slice context: converts to `start..start+1` range
5. Calls `__mn_tensor_slice(obj, start0, start1, ..., end0, end1, ..., rank)`

The argument packing (all starts followed by all ends followed by rank) matches the C runtime's `__mn_tensor_slice` function signature. The scalar-in-slice-context handling (line 2512-2518) correctly converts a scalar index to a unit range, which preserves the dimension in the output tensor (matching NumPy's behavior for `a[0:1, :]` vs `a[0, :]`).

### 7.4 Tensor Reduction Lowering -- CLEAN

The reduction lowering at `lower.py:2210-2227` correctly:
1. Detects `sum`, `mean`, `max`, `min` as scalar-returning reductions
2. Detects `argmax`, `argmin` as index-returning reductions (always `i64`)
3. Constructs the runtime function name: `__mn_tensor_{method}_{f64|i64}`
4. Sets the return type appropriately (float for float tensor, int for int tensor, int for argmax/argmin)

---

## Section 8: LLVM Emission (`emit_llvm_text.py`)

### 8.1 `_do_tensor_init` -- CORRECT

The tensor init emission at `emit_llvm_text.py:3349-3395` follows a clean 4-step pattern:

1. **Shape array allocation:** `%tshape = alloca [N x i64]` on the stack
2. **Shape dimension stores:** `store i64 dim_val, ptr %tsd` for each dimension
3. **Tensor allocation:** `call noalias ptr @__mn_tensor_alloc(i64 rank, ptr %tshape, i64 8)`
4. **Element stores:** `call void @__mn_tensor_store_{f64|i64}(ptr %tp, i64 index, {type} value)` for each element

The `noalias` attribute on `__mn_tensor_alloc` at line 3375 is correct: the function returns a freshly-allocated tensor that cannot alias any existing pointer. The `willreturn` attribute in the declaration at line 335 is also correct (allocation never loops infinitely). The element size is hardcoded to 8 (sizeof `double` or `int64_t`), which is correct for the current two supported element types.

### 8.2 Drop Glue -- SOPHISTICATED

The tensor drop glue at `emit_llvm_text.py:1524-1563` is the most complex part of the tensor emission:

1. For each tracked tensor variable, load its pointer
2. Check if the pointer is null (skip if so)
3. Check if the pointer equals the function's return value (skip if returning it)
4. Call `__mn_tensor_free(ptr)` if neither check passes

The return-value check at lines 1548-1553 prevents double-free when a tensor is both stored in a local and returned from the function. This is the same pattern used by LLVM's `llvm.lifetime.end` intrinsic annotations and by Rust's borrow checker for "move out of local" optimization. The null check at line 1542 handles the case where a tensor variable was declared but never initialized (e.g., in an unreachable branch).

The `_tensor_vars` list at line 509 is populated in `_do_tensor_init` (line 3394) and in broadcast/slice call handlers (which also produce new tensor pointers). This tracking ensures all tensor allocations are freed on function exit.

### 8.3 Function Attribute Declarations -- COMPREHENSIVE

The `FUNC_ATTRS` dictionary at `emit_llvm_text.py:328-383` declares correct LLVM attributes for all 40+ tensor runtime functions:

- `__mn_tensor_alloc`: `nounwind`, `noalias`, `willreturn` (allocation)
- `__mn_tensor_free`: `nounwind`, `willreturn` (deallocation)
- `__mn_tensor_store_*`: `nounwind`, `willreturn` (mutation)
- `__mn_tensor_get_*`: `nounwind`, `readonly`, `willreturn` (query)
- `__mn_tensor_*_nd`: `nounwind` only (variadic, cannot prove `willreturn` due to bounds-check abort)
- `__mn_tensor_mean_f64` et al.: `nounwind` only (may abort on empty tensor)
- `__mn_tensor_slice`: `nounwind`, `noalias` (returns fresh tensor)

The attribute choices are correct per the LLVM Language Reference Manual. `readonly` on `__mn_tensor_get_*` allows LLVM to CSE repeated reads. `noalias` on `__mn_tensor_alloc` and `__mn_tensor_slice` enables LLVM's alias analysis to prove non-aliasing for fresh tensors. The absence of `willreturn` on reduction functions that abort on empty tensors is correct: per the LLVM LangRef, `willreturn` means "guaranteed to return," which is violated by `abort()`.

---

## Section 9: Self-Hosted Compiler Stubs

### 9.1 Mirror Coverage -- ADEQUATE BUT INCOMPLETE

The self-hosted compiler mirrors the Python bootstrap at each pipeline stage:

| Stage | Python | Self-hosted (.mn) | Fidelity |
|-------|--------|-------------------|----------|
| AST | `TensorLiteral` dataclass | `Expr::TensorLit(List<Expr>, List<Int>)` | Full |
| Parser | `tensor_literal()`, `tensor_body()`, etc. | `parse_tensor_lit()` -- 1D only | Partial |
| Semantic | `_check_tensor_literal()` | `if ek == "tensor_lit"` block | Partial |
| MIR | `TensorInit` dataclass | `Instruction::TensorInit(...)` | Full |
| Lower | `_lower_tensor_literal()` | `lower_tensor()` | Full |
| Emit | `_do_tensor_init()` (full emission) | `emit_tensor_init()` -- null ptr stub | **Stub** |

### 9.2 `emit_tensor_init` Stub -- MEDIUM Concern

The self-hosted `emit_tensor_init` at `emit_llvm.mn:880-890` emits:

```
%dest = inttoptr i64 0 to ptr
```

This is a null pointer. The comment at line 881 explains: "Stub -- tensor literals in self-hosted code emit as null ptr. Full emission ... is deferred to v4.43.0 when tensor indexing needs it end-to-end."

This means the self-hosted compiler (mnc-stage1) cannot compile any program that uses tensor literals. The golden tests compile via the Python bootstrap, not mnc-stage1, so this does not affect CI. However:

1. The stub was promised for v4.43.0 but is still present at v4.45.0
2. The self-hosted parser only handles 1D tensor literals
3. No self-hosted multi-index, slicing, or broadcasting support exists

**Impact:** The self-hosted compiler's tensor support is cosmetic. It can parse 1D tensor literals and lower them to MIR, but the emitter produces a null pointer. Any program using tensors compiled by mnc-stage1 will segfault.

**Severity:** MEDIUM. The self-hosted compiler is not the primary compilation path (the Python bootstrap is), but the stub represents a widening gap between the Python and self-hosted implementations. Four releases (v4.42.0-v4.45.0) of tensor features with no self-hosted emission makes the bootstrap potential for tensors zero.

### 9.3 Self-Hosted Semantic Tensor Checking -- PARTIAL

The self-hosted semantic checker at `semantic.mn:657-673` handles tensor literal type inference (returning `Tensor<T>`) and at lines 759-846 handles tensor binary operations (type promotion, operator validation for `@`). This is more complete than the parser mirror. The self-hosted semantic checker correctly validates tensor types in binary expressions, checks for matmul operator constraints, and propagates element types through operations.

### 9.4 Runtime Function Naming Divergence

The self-hosted emitter at `emit_llvm.mn:301-305,525-530` uses `__mapanare_tensor_alloc`, `__mapanare_tensor_free`, etc. (with `__mapanare_` prefix). The Python emitter uses `__mn_tensor_alloc`, `__mn_tensor_free`, etc. (with `__mn_` prefix). This naming divergence means the self-hosted compiler's runtime calls would link against different symbols than the Python bootstrap's. If and when the self-hosted emitter implements full tensor emission, the runtime function names must be synchronized.

---

## Section 10: Test Infrastructure

### 10.1 Test Count -- 167 Tensor-Specific Tests

Across 12 test files:

| Category | Files | Tests | Coverage focus |
|----------|-------|-------|---------------|
| Parser | 2 | 18 | Literal parsing, multi-index parsing |
| Semantic | 5 | 44 | Type checking, indexing, broadcasting, shapes, slicing |
| LLVM | 4 | 38 | IR emission for literals, indexing, broadcasting, reductions |
| Runtime (Python) | 1 | 67 | `experimental.tensor.Tensor` class operations |
| **Total** | **12** | **167** | |

Plus 5 golden test programs (`49_tensor_literal.mn` through `53_linear_regression.mn`).

The CLAUDE.md claims "100/100 tensor test count" -- this may refer to a different counting methodology (perhaps excluding the runtime tests or the golden tests). The actual count of 167 is higher than claimed.

### 10.2 Coverage Gaps

1. **No `scalar - tensor` test** (enables Issue in Section 7.2)
2. **No `scalar / tensor` test** (same issue)
3. **No negative index test for tensors** (e.g., `a[-1]` -- should this wrap or error?)
4. **No concurrent tensor access test** (multiple tensors in the same function interacting)
5. **No test for tensor as function argument or return value** (lifetime/drop-glue interaction)
6. **No test for `tensor_mean` on integer tensor** (the missing `__mn_tensor_mean_i64`)

### 10.3 Golden Test Quality -- HIGH

The five golden tests form a progression:

1. `49_tensor_literal.mn` -- Construction, rank/size queries, element access (1D, 2D, 3D, Int, negated)
2. `50_tensor_indexing.mn` -- Read/write with `t[i, j]`, 1D/2D/3D, write-back verification
3. `51_tensor_broadcast.mn` -- Same-shape add/sub/mul/div, scalar+tensor, integer tensors
4. `52_tensor_slicing.mn` -- Reductions (sum/mean/max/min/argmax/argmin), range slice, 2D wildcard slice
5. `53_linear_regression.mn` -- Practical ML: gradient descent using tensor ops

The linear regression demo at `53_linear_regression.mn` is an excellent integration test. It exercises tensor construction, scalar-tensor multiplication (`X * w`), tensor-scalar addition (`... + b`), tensor subtraction (`pred - y`), method calls (`.sum()`), and all of this inside a `for` loop. If any tensor operation has a memory leak, the 10-iteration loop will amplify it. This is the kind of "end-to-end smoke test" that catches composition bugs that unit tests miss.

---

## Section 11: Pre-Panel Audit -- 18/19 PASS

### 11.1 The FAIL: `mean_i64` Omission

Claim 17 states "12 runtime C functions (sum/mean/max/min/argmax/argmin x f64/i64)." The actual count is 11: the `__mn_tensor_mean_i64` function was not implemented. The pre-panel audit at `docs/roadmap/v4/v4.46.0/PRE_PANEL_AUDIT.md` correctly identifies this as a LOW-severity accounting error and notes that "integer mean -> float result doesn't fit the i64 return type."

This is arguably correct behavior: `mean([1, 2, 3])` should return `2.0` (a float), not `2` (an integer). NumPy's `np.mean([1, 2, 3])` returns `2.0` (float64). If `__mn_tensor_mean_i64` were implemented, it would either need to return `double` (changing the function signature from the i64 pattern) or truncate the result to `i64` (losing precision). The omission is the right engineering choice; the CHANGELOG claim is the error.

**Process assessment:** The fact that the pre-panel audit caught this discrepancy and documented it with severity rating is a POSITIVE signal. It demonstrates an audit process that checks claims against evidence rather than rubber-stamping. The 18/19 PASS rate is realistic and honest.

---

## Issues Found

### Issue 1 [MEDIUM] -- Scalar-tensor non-commutative operators produce wrong results

**Description:** `lower.py:2559-2563` swaps operands for `scalar - tensor` and `scalar / tensor`, emitting `__mn_tensor_sub_scalar_f64(tensor, scalar)` which computes `tensor - scalar`, not `scalar - tensor`.

**Impact:** `5.0 - Tensor<Float>[1.0, 2.0]` returns `[-4.0, -3.0]` instead of `[4.0, 3.0]`. Similarly for division.

**Evidence:** The code comment at line 2560 acknowledges the issue: "For -/div, this is wrong conceptually but matches NumPy's broadcasting." This is incorrect -- NumPy does NOT swap operands for non-commutative ops.

**Fix:** Add `__mn_tensor_rsub_scalar_*` and `__mn_tensor_rdiv_scalar_*` runtime functions, or negate/reciprocate the swapped result.

**Severity:** MEDIUM. Incorrect computation, but only triggered by scalar-on-left for `-` and `/`.

### Issue 2 [MEDIUM] -- Self-hosted `emit_tensor_init` is a null-pointer stub across four releases

**Description:** `emit_llvm.mn:880-890` emits `inttoptr i64 0 to ptr` for all tensor literals. The comment says "deferred to v4.43.0" but it is still a stub at v4.45.0.

**Impact:** The self-hosted compiler cannot compile any program that uses tensor literals. The gap between Python bootstrap and self-hosted compiler has widened over four releases.

**Fix:** Port the Python emitter's `_do_tensor_init` logic (shape alloca + alloc + stores) to the self-hosted emitter. This requires approximately 30 lines of Mapanare code mirroring `emit_llvm_text.py:3349-3395`.

**Severity:** MEDIUM. Does not affect the primary (Python bootstrap) compilation path, but represents growing technical debt in the self-hosted compiler.

### Issue 3 [LOW] -- Runtime function naming divergence between Python and self-hosted emitters

**Description:** Python emitter uses `__mn_tensor_*` prefix; self-hosted emitter uses `__mapanare_tensor_*` prefix. If the self-hosted emitter is eventually completed, it will link against different symbols.

**Fix:** Align the self-hosted emitter's function names to match the Python emitter's `__mn_` prefix convention.

**Severity:** LOW. Only matters when self-hosted tensor emission is implemented.

### Issue 4 [LOW] -- CHANGELOG claims "14 call sites migrated" for `IndexExpr.indices`; actual count is 13

**Description:** Both the v4.43.0 and v4.45.0 CHANGELOG entries claim 14 call sites. I count 13 distinct `IndexItem`-consuming sites across 6 modules.

**Fix:** Clarify the count in the next CHANGELOG entry.

**Severity:** LOW. Accounting imprecision, not a code issue.

---

## Strengths

### S1: Clean Pipeline Integration -- Every Phase Wired Correctly

The tensor feature touches every compiler phase (grammar, parser, AST, semantic, MIR, lower, emit) and each transition is correct:
- Grammar produces parse trees that the transformer converts to typed AST nodes
- AST nodes carry the right information for semantic checking
- Semantic checker validates types and shapes before lowering
- MIR `TensorInit` captures exactly what the emitter needs
- LLVM emitter generates correct IR with proper cleanup

This is the standard that a compiler feature should meet. Compare with GCC's C23 `constexpr` feature, which similarly touches lexer, parser, semantic analysis, tree optimization, and code generation -- each phase must be wired correctly for the feature to work. Arc 3 achieves this.

### S2: Broadcasting Implementation with Diagnostic Quality

The `broadcast_shape` function is a direct, readable implementation of the NumPy broadcasting algorithm. The companion `broadcast_incompatible_dim` function enables error messages that name the specific failing dimension. The semantic checker at `semantic.py:704-735` uses both to produce errors like "shapes [3, 4] and [3, 5] are not broadcast-compatible for '+'; dimension 1 differs: 4 vs 5." This is comparable to rustc's type error messages and significantly better than NumPy's "operands could not be broadcast together with shapes (3,4) (3,5)" which does not name the failing dimension.

### S3: `IndexItem` -- Right Abstraction at Right Level

The `IndexItem` node cleanly separates three indexing concerns (scalar element access, range slicing, wildcard dimension selection) without leaking tensor-specific semantics into the grammar. The grammar simply parses comma-separated expressions inside brackets; the parser transformer classifies them by inspecting the parsed node type. This design means that when stepped slices (`0..10..2`) are added in v5.x, only the transformer and semantic checker need to change, not the grammar.

### S4: Drop Glue Engineering

The tensor drop glue in the LLVM emitter is more sophisticated than the list/map drop glue. The null-check + return-value-check pattern prevents both use-after-free (null pointer) and double-free (returning the tensor). The per-function tracking via `_tensor_vars` ensures no tensor allocation is leaked. This is mature resource management engineering.

### S5: Linear Regression Golden Test as Integration Proof

`53_linear_regression.mn` is a non-trivial 38-line program that exercises tensor construction, scalar-tensor arithmetic, tensor-tensor arithmetic, reduction methods, variable mutation, and loop control flow. It is a realistic ML program, not a synthetic test. If the tensor pipeline has any latent composition bugs, this program will likely trigger them.

---

## Carry-Forward Items from v4.41.0

### Issue 1 [HIGH] -- `_collect_references` uses wrong attribute name (`receiver` vs `object`)
Status: **UNKNOWN.** Not checked in this review (out of scope for tensor arc). Should be verified.

### Issue 2 [MEDIUM] -- Redundant parse passes on keystroke and save
Status: **UNKNOWN.** Not checked.

### Issue 3 [MEDIUM] -- `receiver_type_at` is called but never defined
Status: **UNKNOWN.** Not checked.

### Issue 2.3 from v4.36.0 [MEDIUM] -- `DiagnosticBag.note()` call path
Status: **OPEN.** No change.

### Issue 3.3 from v4.36.0 [MEDIUM] -- Module-level DFE fixpoint
Status: **OPEN.** No change.

---

## Recommendations

### R1: Fix scalar-tensor operand order for non-commutative ops (addresses Issue 1)

Add `__mn_tensor_rsub_scalar_{f64,i64}` and `__mn_tensor_rdiv_scalar_{f64,i64}` to the C runtime. In the lowerer, when `lhs` is scalar and `rhs` is tensor for `-` or `/`, emit the reverse-operand variant. Add tests: `let c = 5.0 - Tensor<Float>[1.0, 2.0]` should produce `[4.0, 3.0]`.

### R2: Implement self-hosted `emit_tensor_init` (addresses Issue 2)

Port the shape alloca + `__mn_tensor_alloc` + store loop pattern from `emit_llvm_text.py:3349-3395` to `emit_llvm.mn:880-890`. Align runtime function names to `__mn_*` prefix. This unblocks tensor golden tests on mnc-stage1.

### R3: Add scalar-on-left tests for all four ops

Test `scalar + tensor`, `scalar - tensor`, `scalar * tensor`, `scalar / tensor` at the semantic, lowering, and LLVM emission levels. The current test suite only tests `tensor op scalar`.

### R4: Test tensor as function argument and return value

The drop glue's return-value check at `emit_llvm_text.py:1548-1553` is untested. A golden test like `fn make_tensor() -> Tensor<Float> { return Tensor<Float>[1.0] }` would exercise this path.

### R5: Document the `mean_i64` design decision

The omission of `__mn_tensor_mean_i64` is arguably correct (integer mean -> float). Add a comment in `mapanare_gpu_builtins.c` or `types.py` documenting this decision, and correct the CHANGELOG claim from "12" to "11" runtime functions.

---

## Score Breakdown

| Category | Weight | Score | Notes |
|----------|--------|-------|-------|
| Grammar extension (LALR safety) | 20% | 10.0 | Clean LALR-compatible design; no conflicts; tensor_atom restriction documented |
| AST migration + IndexItem design | 15% | 9.5 | 13 call sites migrated correctly; IndexItem is the right abstraction; minor CHANGELOG count discrepancy |
| Parser shape inference | 10% | 9.5 | Parse-time inference is correct placement; jagged detection; minor error span imprecision |
| Semantic broadcasting | 20% | 9.5 | NumPy-compatible; rustc-quality diagnostics; rank checking correct |
| MIR + lowering | 15% | 8.5 | TensorInit clean; slice lowering correct; binop scalar-tensor order bug (Issue 1) |
| LLVM emission + drop glue | 10% | 9.5 | Sophisticated drop glue; correct function attributes; comprehensive runtime declarations |
| Self-hosted mirror | 5% | 6.0 | Parser/semantic/MIR mirrored; emitter is null-ptr stub; naming divergence |
| Test infrastructure | 5% | 9.0 | 167 tests + 5 golden; linear regression demo excellent; scalar-on-left gap |

**Weighted total: 9.2 / 10**

---

## Verdict

**PASS.** Arc 3 delivers a tensor language surface that flows correctly through the entire compiler pipeline, from grammar to LLVM IR. The architecture is sound: tensor literals get their own grammar rule and AST node, indexing is cleanly generalized via `IndexItem`, broadcasting reuses the established semantic checking infrastructure with NumPy-compatible rules, and the LLVM emitter generates correct IR with proper resource management. The two MEDIUM issues (scalar-tensor operand order for non-commutative ops, and the self-hosted emitter stub) are real bugs that need fixing, but they do not invalidate the arc's architectural contribution. The 167 tensor tests with 5 golden programs provide strong coverage. The pre-panel audit's honest 18/19 PASS demonstrates process maturity. This is a well-executed compiler feature arc.
