# v5.15.0 — Terseness Design (Te.2)

**Status:** LOCKED — Phase 0 closed.
**Audience:** implementers (Phases 1–7) + future arc maintainers
(v5.16.0+).

This document fixes the syntactic and semantic decisions for the
three additive forms shipping in v5.15.0:

1. List + map comprehensions.
2. Implicit-return one-liner (`fn name(args) = expr`).
3. Terse lambda (`|x| body`).

All three are **sugar, not semantics**. Every form lowers to AST/MIR
constructs that already exist at v5.14.1. No new MIR ops, no new
runtime, no new type-system rules. The block-form implicit return
(`fn add(a, b) -> Int { a + b }` with no explicit `return`) is
**already shipped** and is not in scope; see SPEC §4.5 and the
v5.13.0-prep audit.

---

## 1. Lambda — terse syntax

### 1.1 Syntax

```
lambda_terse: BAR (NAME (COMMA NAME)*)? BAR expr
```

| Form | Meaning |
|---|---|
| `\|x\| x * 2` | one-arg lambda, body is single expression |
| `\|x, y\| x + y` | multi-arg |
| `\|\| 42` | zero-arg (empty pipe pair) |

The terse form **always** uses `\|...\|`. There is no bare-name
shorthand. Rationale: keeping the bars makes lambdas grep-able and
removes one ambiguity question. (`x => x * 2` is the legacy long
form; it stays parseable and is also lowered to the same `LambdaExpr`
AST node.)

Type annotations on params are **not** allowed in the terse form.
Use the long form `fn(x: Int) { return x * 2 }` if a binding type is
required.

### 1.2 Grammar placement

`lambda_terse` is added to `atom_expr`. The leading `BAR` is
unambiguous in expression position because `|` is never the start of
an expression elsewhere in the grammar (bitwise/logical OR is always
infix `||`; pattern-`|` is restricted to `match` arms via
`or_pattern`, which is reached through `pattern`, not `atom_expr`).

### 1.3 Lowering

```python
LambdaExpr(
    params=[Param(name=p) for p in names],
    body=expr,        # single expression, not a Block
)
```

Reuses the existing `_lower_lambda` path (lower.py:2928). Captures,
closure env-struct, ClosureCreate emission — all unchanged.

### 1.4 Equivalence test

`xs.map(|x| x * 2)` and `xs.map(fn(x) { return x * 2 })` produce
**identical IR modulo SSA naming**. Verified in
`tests/test_lambdas.py::test_terse_matches_long_form`.

---

## 2. Implicit-return one-liner

### 2.1 Syntax

```
fn_def: ... LPAREN param_list? RPAREN (ARROW type_expr)? (block | ASSIGN expr)
```

The `= expr` form is a sugar for a function whose body is exactly
`{ return expr }`. The function may still declare a return type.

| Form | Lowers to |
|---|---|
| `fn double(x) = x * 2` | `fn double(x) { return x * 2 }` |
| `fn id(x: Int): Int = x` | `fn id(x: Int): Int { return x }` |
| `fn pi() -> Float = 3.14159` | `fn pi() -> Float { return 3.14159 }` |

### 2.2 Restrictions

- **Body is a single expression.** No statements, no `let`, no
  control flow except via `if`/`match` (which are expressions).
- **Public/private prefix unchanged.** `pub fn f(x) = expr` works.
- **Async + extern not supported in this form.** The expression body
  has too narrow a surface to accommodate them; use the block form.

### 2.3 Block-form already works

`fn add(a, b) -> Int { a + b }` (no explicit `return`) compiles and
runs correctly **in both compilers** at v5.14.1. SPEC §4.5 documents
this. v5.15.0 does **not** modify the block-form path. Don't touch
it; don't add tests for it under this release.

### 2.4 fmt rule

`mnc fmt` does **not** auto-rewrite between `= expr` and `{ ... }`
forms. The choice is the author's. Whitespace inside the `=` form is
canonicalized: exactly one space on each side of `=`.

---

## 3. List + map comprehensions

### 3.1 Syntax

```
list_comp: LBRACKET expr comp_clause+ RBRACKET
map_comp:  MAP_OPEN expr COLON expr comp_clause+ RBRACE
comp_clause: KW_FOR pattern KW_IN expr (KW_IF expr)*
```

| Form | Meaning |
|---|---|
| `[x * 2 for x in xs]` | map every element |
| `[x for x in xs if x > 0]` | filter |
| `[x * y for x in xs for y in ys]` | nested (cartesian product) |
| `[x for x in xs if x > 0 if x < 100]` | multiple filters per clause |
| `#{ k: v * 2 for k in keys }` | map comprehension over keys |

### 3.2 LALR disambiguation

`list_lit` and `list_comp` share an opening `LBRACKET expr`. The
disambiguator is the next token after the first expression:

- `,` → `list_lit`
- `]` → `list_lit` (single-element list)
- `for` → `list_comp`

LALR(1) handles this with one token of lookahead. The grammar is
written such that `list_comp` is its own production reachable from
`atom_expr`, parallel to `list_lit`. Both forms produce distinct AST
nodes.

For `map_comp`, the ambiguity is between `map_lit` (`{ key: value,
... }`) and `map_comp` (`{ key: value for ... }`). Same
discriminator — token after the first `key: value` pair.

### 3.3 AST

```python
@dataclass
class CompClause(ASTNode):
    target: str                # bound variable name (single identifier)
    iter: Expr
    conditions: list[Expr]     # zero or more `if` filters

@dataclass
class Comprehension(Expr):
    kind: Literal["list", "map"]
    element: Expr              # for list
    key: Expr | None           # for map
    value: Expr | None         # for map
    clauses: list[CompClause]  # one or more, in source order
```

Pattern destructuring in comprehension targets (`for (k, v) in ...`)
is **deferred** — single-identifier targets only in v5.15.0.

### 3.4 Type inference

- Iterable expression must be `list<T>` or `map<K, V>` (or compatible
  range). Unknown / generic iterables flow through as `UNKNOWN`,
  same as existing for-loops.
- Bound variable `target` gets type `T` (or `K` for map keys, but
  v5.15.0 only supports the first form: `for k in m` iterates keys).
- Element expression type → list element type. For map comp, key
  expression → map key type, value expression → map value type.

### 3.5 Lowering

A comprehension lowers in `lower.py::_lower_expr` by **synthesizing
the equivalent AST** and recursing through the existing lowerers.
The synthesis allocates a fresh local for the result, emits the
nested for/if structure, and returns the local.

```
[expr for x in xs if cond]

  ⇒  let mut __comp = []
     for x in xs:
       if cond:
         __comp.push(expr)
     <yield __comp as the expression value>
```

For `map_comp`, the push is replaced with `__m.insert(key, value)`.

The synthesis happens at MIR-emit time rather than parse time so we
preserve span info on the original `Comprehension` node (matters for
type-error diagnostics) and so the bootstrap mirror has a single
parser-shape change rather than dozens of synthetic-node-construction
sites.

### 3.6 IR-equivalence requirement

`[x * 2 for x in xs]` must emit IR identical (modulo SSA naming) to
the manual loop:

```mn
let mut r = []
for x in xs {
    r.push(x * 2)
}
r
```

Verified in `tests/test_comprehensions.py::test_ir_matches_manual`.

### 3.7 Out of scope

- Pattern-destructuring targets: `[(k, v) for ... in items]` —
  deferred.
- `else` clauses in filters: `[x if c else d for x in xs]` —
  deferred.
- Set comprehensions: no native set type yet.
- Generator expressions: lazy semantics, defer to iterator-protocol
  arc.
- Walrus inside comprehensions: defer with walrus generally.

---

## 4. Bootstrap mirror

The native compiler (`mapanare/self/*.mn`) must parse and lower all
three new forms because new goldens use them and goldens are
required to pass through `mnc-stage1`.

| Module | Change |
|---|---|
| `mapanare/self/ast.mn` | add `Comprehension` and `CompClause` node types; bump dispatch tags |
| `mapanare/self/parser.mn` | recognize `\|...\| expr`, `... = expr` after fn signature, `[ expr for ... ]`, `#{ k:v for ... }` |
| `mapanare/self/lower.mn` | lower comprehensions by synthesis (mirror Python `lower.py`); other two forms reuse existing lambda / fn-body lowerers |

The bootstrap source itself is **not** rewritten to use any of these
features. v5.17.0 (Sh.*) does that. The fixed-point invariant is
preserved by construction: no behavioral change in the input source.

---

## 5. fmt rules — deferred

The PLAN's Te.2.I item asked for canonicalization of lambda /
comprehension / implicit-return whitespace inside the new forms.
That requires tokenization beyond what `format.py`'s current
line-based, AST-preserving rewriter does, so it ships **deferred to
v5.16.0** alongside Te.4 / Mc.\* polish.

What `format.py` currently does still applies — trailing whitespace
strip, leading-tab → spaces, blank-line collapsing, single trailing
newline. None of those regress the new forms.

The contract `fmt` does **not** rewrite between long and short forms
holds. User intent is preserved.

---

## 6. Risk register (post-design)

| Risk | Status |
|---|---|
| `\|x\|` ambiguous w/ bitwise OR | RESOLVED — `\|` is never an expression-start in the existing grammar; LALR(1) accepts the addition. |
| Comprehension type inference wrong on mixed types | OPEN — deferred to test-driven hardening; if `[1, 2.0]` syntax fails today, comprehension over the same expression also fails the same way. |
| Bootstrap lower change breaks fixed point | OPEN — mitigated by not rewriting any `mapanare/self/*.mn` source; the parser/lower additions only fire on new syntax. |
| IR-equivalence failure | OPEN — covered by Phase 6 IR-diff tests. |

---

## 7. Open questions (post-v5.15.0)

- Should pattern-target comprehensions land in v5.20.0 (Te.5 struct
  ergonomics) or earlier? Track in `docs/roadmap/v5/PARITY_GAPS.md`.
- Do we want a `where` clause as an alias for trailing `if`? Defer
  until a real grammar audit.
- Generator expressions vs lazy comprehensions: needs iterator
  protocol design — not in arc scope.
