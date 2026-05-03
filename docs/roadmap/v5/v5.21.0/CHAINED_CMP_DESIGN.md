# v5.21.0 Te.6 — Chained Comparisons Design Lock

**Status:** LOCKED — Phase 0 decisions; Phases 1–5 implement against this.
**Reference:** Python's chained comparison semantics
([docs](https://docs.python.org/3/reference/expressions.html#comparisons)).

---

## Why this exists

`0 < x < 10` reads better than `0 < x && x < 10`. Small grammar
change, big reader win in numeric / range / bounds-check code.
Python's behavior is the gold standard; mirror exactly.

---

## D1 — Operator set

The chain accepts exactly these operators:

| Op | Meaning |
|----|---------|
| `<`  | less than |
| `<=` | less or equal |
| `>`  | greater than |
| `>=` | greater or equal |
| `==` | equal |
| `!=` | not equal |

**Excluded:** `&&`, `||` (logical), `in`, `is`, `<=>` (spaceship,
not in language). No mixing with non-comparison operators inside
the chain. Mixing happens via parentheses or normal `&&`/`||`.

**Precedence merge.** Pre-v5.21.0, `eq_expr` (==, !=) sat at
strictly lower precedence than `cmp_expr` (<, >, <=, >=). v5.21.0
merges both into a single `cmp_expr` precedence level — same as
Python. **Audit confirmed** (grep across `mapanare/self/`,
`tests/`, `stdlib/`): no existing code relies on the relative
precedence of `==` vs `<` at the same level — every mix uses
explicit parens or `&&`/`||`. Safe change.

---

## D2 — Direction mixing

`0 < x > -10` is **legal** (each adjacent pair evaluated
independently as `&&`-joined comparisons). Equivalent to
`0 < x && x > -10`. Documented as legal but rare; not flagged.
A future linter rule may flag mixed-direction chains; not in
v5.21.0 scope.

---

## D3 — Middle-term evaluation: ONCE

**The single most important semantic rule.** `f() < g() < h()`
calls `g()` exactly once. Any implementation that calls `g()`
twice is wrong, even if pure functions happen to produce the
same boolean answer. Side-effecting middle terms exist; tests
exercise them (Phase 4 golden `chained_cmp_side_effect.mn`).

For an N-element chain `a₀ op₁ a₁ op₂ a₂ … opₖ aₖ`:

- `a₀` evaluated once (it's a leaf, never reused).
- `aₖ` evaluated once (leaf).
- Each interior `aᵢ` (1 ≤ i ≤ k−1) evaluated once.

The desugaring binds each non-trivial interior term to a fresh
local before constructing the `&&` chain.

---

## D4 — Triviality predicate

To avoid IR bloat, an interior term that is itself a
side-effect-free, single-evaluation read **skips the temp**.

**Trivial:**
- `Identifier` (name reference)
- `IntLiteral`, `FloatLiteral`, `BoolLiteral`, `StringLiteral`,
  `CharLiteral`, `NoneLiteral`

**Non-trivial (gets a temp):**
- `CallExpr`, `MethodCallExpr` — side effects possible
- `BinaryExpr`, `UnaryExpr` — re-evaluation cost, side effects
  possible (e.g., `++`)
- `FieldAccessExpr`, `IndexExpr` — possible side effects on
  receiver evaluation; defensive
- `ConstructExpr`, `StructUpdate`, `ListLiteral`, `MapLiteral`,
  `TensorLiteral`, `LambdaExpr`, `RangeExpr`, `IfExpr`,
  `MatchExpr`, `IfLetExpr`, `BlockExpr` — anything that allocates
  or has control flow
- `InterpString` — runs `__mn_str_concat` chain
- `SomeExpr`, `OkExpr`, `ErrExpr`, `WrapNone`-shape expressions
- `AssignExpr`, `SpawnExpr`, `SyncExpr`, `AwaitExpr`, `SendExpr`,
  `ErrorPropExpr`, `SignalExpr`, `PipeExpr`

**Conservative rule.** When in doubt, emit the temp. Temps are
cheap; correctness matters more than IR length. The emitted temp
binds via the existing `let` machinery and uses
`fresh-tmp`-style naming so strict 3-stage fixed point is not
disturbed.

**Bootstrap parity.** The native `mnc-stage1` mirrors this list
verbatim. Any divergence in the list is a bootstrap bug.

---

## D5 — Precedence + result type

- Precedence: same as a single comparison — binds tighter than
  `&&`, looser than `+`. The chain's outer `&&`s are inserted at
  *desugar* time, not at *parse* time, so the outer `&&` binds
  exactly as a hand-written `&&` would.
- Result type: a single `Bool`. Usable in any Bool position
  (`if`, `while`, `assert`, RHS of `let`, etc.).

---

## D6 — Empty / single-comparison chains: NO BEHAVIOR CHANGE

A bare `pipe_expr` (no comparison) is just `pipe_expr` — the
existing transformer pass-through. A 2-element comparison
`a < b` produces the **existing** `BinaryExpr(a, <, b)` AST
shape — byte-identical IR before and after this release. Only
3+ element chains produce the new `ChainedCompare` AST node.

This is a hard requirement for strict 3-stage fixed point.

---

## Desugaring algorithm (reference implementation)

```python
def lower_chained_compare(node: ChainedCompare, ctx) -> Value:
    # Step 1: lower each operand. Interior non-trivial operands
    # get bound to a fresh temp so they evaluate exactly once.
    operand_vals: list[Value] = []
    for i, expr in enumerate(node.operands):
        v = lower_expr(expr, ctx)
        is_interior = 0 < i < len(node.operands) - 1
        if is_interior and not is_trivial(expr):
            tmp_name = ctx.fresh_chain_tmp()  # e.g., __mn_chain_0
            ctx.bind_local(tmp_name, v)
            v = ctx.lookup(tmp_name)
        operand_vals.append(v)

    # Step 2: build pairwise comparisons.
    pairs: list[Value] = []
    for i, op in enumerate(node.ops):
        pairs.append(emit_binop(op, operand_vals[i], operand_vals[i+1]))

    # Step 3: fold pairs left-to-right with &&.
    return functools.reduce(emit_and, pairs)
```

For pure-trivial chains (e.g., `0 < x < 10` where `x` is an
Identifier), no temp is allocated; IR is identical to a
hand-rolled `0 < x && x < 10`.

---

## Phase 0 lock — six decisions

| # | Decision |
|---|----------|
| D1 | Chain ops = {<, <=, >, >=, ==, !=}; eq/cmp precedence merged into single level |
| D2 | Mixed-direction chains legal (`a < b > c`) |
| D3 | Each operand evaluated exactly once |
| D4 | Triviality = Identifier ∪ Literals; everything else gets a temp |
| D5 | Same precedence as single cmp; result is `Bool` |
| D6 | 1-cmp shapes preserve existing AST + IR byte-identity |

These six decisions are locked. Phase 1+ implements against
them; any deviation is a bug to be fixed, not a re-decision.
