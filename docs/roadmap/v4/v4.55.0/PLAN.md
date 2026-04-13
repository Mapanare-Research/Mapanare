# Mapanare v4.55.0 — `const` Path A — Real `ConstDef` AST Node

> **Arc 5 release 4.** Closes the v4.26.0 `const` CRITICAL **properly**
> — 29 releases after it was first filed. v4.27.0 chose Path B (revert)
> as the cheap closure. v4.55.0 is the Path A fix that was always
> "budgeted for a future release that actually needs named tensor
> dimensions." The tensor arc (v4.42.0–v4.45.0) delivered the need.

**Status:** DONE (2026-04-12)
**Session log:** Same session as v4.52.0-v4.54.0. Grammar, AST, parser, semantic, lower all implemented. Self-hosted scope issue found (const refs in fn bodies).
**Decisions taken:** Module-level only (default). Explicit type annotation required (default). Depth limit 10 (default). v4.27.0 negative guard deleted.
**Breaking:** No (additive: `const` becomes a real keyword, distinct from `let`)
**Prerequisite:** v4.54.0
**Delta review:** **YES** — new keyword. Coral primary, Anaconda secondary (type-system lens).
**Full panel:** No (v4.56.0)
**Estimated work:** 2 sprints
**Theme:** The lie finally becomes the truth. Real constant-folding, real immutability, real tensor-dimension substitution.

---

## Why Path A now, not then

The v4.26.0 panel offered two paths:
- **Path A**: Introduce `ConstDef` as a distinct AST node. Track immutability in the symbol table. Allow `const` identifiers in tensor shape positions. Real compile-time constant folding.
- **Path B**: Revert to a `let` alias. Strike the CHANGELOG entries.

v4.27.0 picked Path B because:
- Cheap (1 hour vs 3-4 hours)
- Panel agreed both were acceptable
- No tensor-dimension code existed to consume the feature

v4.55.0 picks Path A because:
- Arc 3 (v4.42.0–v4.45.0) shipped tensor literals, indexing, broadcasting, reductions. Named tensor dimensions are now a real ergonomic need:
  ```mapanare
  const N: Int = 100
  const BATCH: Int = 32
  let weights: Tensor<Float>[BATCH, N] = ...
  let biases: Tensor<Float>[N] = ...
  ```
  Without `const`, the user has to repeat `100` and `32` everywhere, or thread them through as function parameters.
- Arc 5 is the debt-drain arc. The v4.26.0 CRITICAL has been open for 29 releases. Closing it in arc 5 means the v4.56.0 panel grades it.
- The v4.27.0 Path B revert was always explicitly temporary.

---

## Scope

### Syntax

```mapanare
const N: Int = 100
const BATCH: Int = 32
const PI: Float = 3.141592653589793
const GREETING: String = "hello"

// Use as a tensor shape dimension:
let weights: Tensor<Float>[BATCH, N] = Tensor<Float>[...]

// Use in constant expressions:
const DOUBLED: Int = N * 2  // compile-time computed

// Use as a regular value:
let radius = PI * 2.0
```

### Semantics

1. `const NAME: TYPE = EXPR` — `EXPR` must evaluate to a constant at compile time.
2. `const` identifiers are module-level only for v4.55.0 (function-local `const` is v5.x backlog if demand).
3. Assigning to a `const` is a compile error: `const N: Int = 100; N = 200  // error: cannot assign to const`.
4. `const` identifiers can appear in tensor shape annotations: `Tensor<T>[N, M]` — the shape is resolved at the definition site, stored as a tuple of `Int`s on the tensor type.
5. Constant folding: `const DOUBLED: Int = N * 2` — the `*` operator is evaluated at compile time because both operands are constants.
6. The initializer `EXPR` can be:
   - Integer / float / string / bool literal
   - Named constant from another `const`
   - Constant expression: `N + 1`, `N * 2`, `PI * 2.0`, `"prefix" + "suffix"`
   - Not: function call (no compile-time function evaluation in v4.55.0); struct construction (maybe later)

### Differences from `let` at module level

- `const` requires a compile-time evaluable initializer; `let` does not.
- `const` is immutable and enforced; `let` at module level is also immutable by convention but not all checks are wired.
- `const` can be used in type annotations (tensor shapes); module-level `let` cannot.
- `const` has compile-time constant folding; `let` does not.

---

## Phase 0 — Design doc

- [ ] `docs/roadmap/v4/v4.55.0/DESIGN.md`:
  - AST node structure: `ConstDef(name, type_expr, value, span)` — **distinct** from `ModuleLetDef`
  - Symbol-table representation: `SymbolDef.kind = "const"`, `SymbolDef.const_value: Optional[ConstantValue]`
  - Constant-folding algorithm: recursive evaluation of allowed expressions against a table of already-computed constants
  - Tensor-shape substitution: `resolve_shape_from_type` walks a `TypeExpr` and substitutes any `NameRef` that resolves to a `ConstDef` with the const's integer value
  - Error diagnostics for non-constant initializers: rustc-quality with suggestion to use `let` instead
- [ ] Delta reviewer cross-check (Coral) before any code.

---

## Phase 1 — Grammar

- [ ] `mapanare/mapanare.lark`:
  ```
  const_def: "const" NAME ":" type_expr "=" expression
  KW_CONST: "const"
  ```
- [ ] `decorated_def` or `module_item` alternative list — add `const_def`.
- [ ] **Critical:** this time the `const` token is real and distinct from `let`. The v4.26.0 bug was that `const_def` was an alias for `module_let_def` in the Lark grammar.

## Phase 2 — AST

- [ ] `mapanare/ast_nodes.py`:
  ```python
  @dataclass
  class ConstDef(Definition):
      name: str
      type_expr: TypeExpr  # distinct field — full type, not collapsed to .name
      value: Expr  # the initializer
      span: Span
  ```
- [ ] **Critical:** the `type_expr` field is the full `TypeExpr` object. v4.26.0's parser collapsed this to a `.name` string, which is why tensor shapes silently dropped. v4.55.0 does not collapse.

## Phase 3 — Parser

- [ ] `mapanare/parser.py` `const_def` transformer:
  ```python
  def const_def(self, children):
      name = children[0]
      type_expr = children[1]  # full TypeExpr — not .name
      value = children[2]
      span = merge_spans(children)
      return ConstDef(name=name, type_expr=type_expr, value=value, span=span)
  ```
- [ ] Regression gate: a test that verifies the `type_expr` field is a `TypeExpr` object, not a string. This is the v4.26.0 bug we're specifically preventing.

## Phase 4 — Semantic + constant folding

### Phase 4.1: Symbol table extension

- [ ] `mapanare/semantic.py` — `SymbolDef` gets:
  - `is_const: bool`
  - `const_value: Optional[ConstantValue]` — the folded value
- [ ] `ConstantValue` is a tagged union: `IntValue(int)`, `FloatValue(float)`, `BoolValue(bool)`, `StringValue(str)`.

### Phase 4.2: Constant folder

- [ ] `mapanare/semantic.py` `fold_constant(expr: Expr, const_table: dict[str, ConstantValue]) -> ConstantValue | None`:
  - Literal: return directly
  - `NameRef(n)`: look up in `const_table`; if not found, return `None` (not a constant)
  - `BinaryOp(+, -, *, /, %, ...)`: recursively fold operands; if both are constants, evaluate; else `None`
  - `UnaryOp(-, !)`: recursively fold; evaluate if operand is constant
  - Anything else: `None`
- [ ] Type errors during fold (e.g., `Int + String`) are not reported here — they're reported by normal type checking. The fold just returns `None` and the semantic check fires the normal error.

### Phase 4.3: `check_const_def`

- [ ] `mapanare/semantic.py` `check_const_def(node: ConstDef) -> None`:
  1. Check the declared type expression is valid
  2. Check the value expression has compatible type
  3. Fold the value expression to a `ConstantValue`
  4. If fold fails: rustc-quality error "const initializer must be a constant expression"
  5. Register in the symbol table with `is_const=True, const_value=folded`

### Phase 4.4: Immutability enforcement

- [ ] `check_assignment(node: Assign) -> None` — if the target resolves to a `const` symbol, fire an error: "cannot assign to `const` X" with suggestion "use `let` for mutable bindings."

### Phase 4.5: Tensor shape substitution

- [ ] `mapanare/types.py` `resolve_shape_from_type(type_expr, const_table) -> list[int]`:
  - For each dimension expression in the type:
    - If `IntLiteral(n)`: `n`
    - If `NameRef(name)`: look up in const_table; must be `IntValue(n)` → `n`; otherwise error
    - If `BinaryOp`: fold; if `IntValue` result, use; else error
  - Return the resolved shape.
- [ ] Callers: tensor literal construction, struct field type resolution, function parameter type resolution.

---

## Phase 5 — Self-hosted mirror

- [ ] Grammar, AST, parser, semantic, constant folder, tensor shape substitution — all mirrored.
- [ ] Byte-identity invariant held — `verify_fixed_point.sh` still 0.
- [ ] **Important:** the self-hosted side's constant folder is where the real work is; the grammar/parser pieces are mechanical. Reserve ~1/2 sprint for the fold implementation.

---

## Phase 6 — Tests

- [ ] `tests/parser/test_const.py` — **the file that v4.26.0's CHANGELOG claimed existed but didn't.** Now it exists for real.
  - `test_const_int_parses`
  - `test_const_float_parses`
  - `test_const_string_parses`
  - `test_const_with_expression_initializer` — `const D: Int = N * 2`
  - `test_const_without_type_annotation_is_error` (for v4.55.0; inference is v5.x)
  - `test_const_without_initializer_is_error`
- [ ] `tests/semantic/test_const.py` — **also promised by v4.26.0 CHANGELOG.**
  - `test_const_int_literal_folds`
  - `test_const_float_literal_folds`
  - `test_const_refers_to_another_const`
  - `test_const_binary_op_folds`
  - `test_const_non_constant_initializer_is_error`
  - `test_const_references_undeclared_is_error`
  - `test_assignment_to_const_is_error`
  - `test_const_in_tensor_shape` — the main integration: `const N: Int = 4; let a: Tensor<Float>[N, N] = ...` resolves to `[4, 4]`
- [ ] `tests/golden/54_const_tensor_shape.mn` — the real use case:
  ```mapanare
  const N: Int = 3
  const BATCH: Int = 2

  fn main() {
      let a: Tensor<Float>[BATCH, N] = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
      let col_sums = a.sum(axis: 0)
      print("shape: ", col_sums.shape)  // expect [3]
      print("col 0: ", col_sums[0])
  }
  ```

## Phase 7 — Delta review

- [ ] `.reviews/deltas/v4.55.0-const-path-a.md` — prep file:
  - The story: v4.26.0 CRITICAL → v4.27.0 Path B → v4.55.0 Path A
  - The AST node distinction (vs the old alias)
  - The constant folder algorithm
  - The tensor shape substitution integration
  - The test files that v4.26.0 claimed existed, now real
- [ ] **Coral primary** (language design, new keyword, the original CRITICAL was hers to fix)
- [ ] **Anaconda secondary** (type system lens — is the constant folder sound? Does it have reasonable bounds on recursion?)

## Phase 8 — LOW sweep

2 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.55.0
- [ ] `CHANGELOG.md [4.55.0]` — `const` Path A, closes v4.26.0 CRITICAL properly
- [ ] `docs/SPEC.md §Bindings and Mutability` — `const` now has its own subsection, not "reserved for future use"
- [ ] `.reviews/CARRY_FORWARD.md` — original v4.26.0 `const` CRITICAL re-closed (was closed Path B in v4.27.0; now really closed Path A)
- [ ] SESSION_REPORT

---

## Exit criteria (16 items)

| # | Check | Evidence |
|---|---|---|
| 1 | DESIGN.md written and reviewed | file exists + Coral sign-off |
| 2 | Grammar accepts `const N: Int = 100` | `test_const_int_parses` |
| 3 | `ConstDef` is a distinct AST node | `isinstance(node, ConstDef)` |
| 4 | Parser preserves full `TypeExpr` (not collapsed to .name) | `test_const_type_expr_preserved` |
| 5 | Constant folder handles literals | `test_const_int_literal_folds` |
| 6 | Constant folder handles const references | `test_const_refers_to_another_const` |
| 7 | Constant folder handles binary ops | `test_const_binary_op_folds` |
| 8 | Non-constant initializer rejected | `test_const_non_constant_initializer_is_error` |
| 9 | Assignment to const rejected | `test_assignment_to_const_is_error` |
| 10 | `const` in tensor shape resolves correctly | `test_const_in_tensor_shape` |
| 11 | `54_const_tensor_shape.mn` golden runs and produces expected output | golden harness |
| 12 | Self-hosted mirror compiles + runs the golden | `test_native.py --stage1` |
| 13 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 14 | Delta review PASS | `.reviews/deltas/v4.55.0-const-path-a.md` |
| 15 | SPEC §Bindings and Mutability updated | diff |
| 16 | Standard closeout clean | CI |

---

## What v4.55.0 does NOT do

- **Function-local `const`** — v5.x backlog
- **Generic const parameters** (`fn foo<const N: Int>(...)`) — v5.x or later
- **`const fn`** — no; function compile-time evaluation is a separate design
- **`const` struct construction** (`const P: Point = Point { x: 1.0, y: 2.0 }`) — maybe v4.56.0+
- **Type inference for `const`** (`const N = 100`, inferring `Int`) — v4.56.0+ if appetite; v4.55.0 requires explicit annotation

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Constant folder has bounds/recursion issues | low | medium | Depth limit (10) + test with nested constants |
| Parser regression: `const` conflicts with other keywords | low | high | Phase 1 grammar test; `KW_CONST` is a new terminal |
| Tensor shape substitution breaks at tensor indexing/slicing sites | medium | medium | Phase 4.5 covers all call sites; integration tests catch misses |
| The v4.27.0 Path B revert left stale test guards that now fail | medium | low | `test_const_keyword_is_parse_error` needs to be deleted (not repurposed); add `test_const_keyword_parses` in its place |

---

## Reference

- [`.reviews/v4.26.0/README.md`](../../../../.reviews/v4.26.0/README.md) §Prioritized Action Items — the original CRITICAL
- [`v4.27.0/SESSION_REPORT.md`](../v4.27.0/SESSION_REPORT.md) §Decision 1 — the Path B choice and its explicit "future release" note

---

## After v4.55.0

v4.56.0 is the **arc 5 panel release**. The fifth 5-minor cadence panel. Arc 5 closes — four A-items drained, the real `const` ships, the compiler debt queue is materially smaller.
