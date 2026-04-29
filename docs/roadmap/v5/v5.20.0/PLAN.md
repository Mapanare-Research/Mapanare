# v5.20.0 — Te.5 — struct ergonomics

**Status:** PLANNING
**Breaking:** No. All four features are additive surface syntax;
existing struct/match code keeps working unchanged.
**Prerequisite:** v5.19.0 shipped (Te.3 closeout + Dk.* Docker
images). Te.5 is the post-arc capstone — adds the struct sugar
that auto-migration tools couldn't safely produce during the
v5.17.0 self-host rewrite.
**Estimated effort:** 16–24h, three sessions. Field shorthand and
struct update are small; destructuring in `let` and `if let` are
where the parser/semantic work concentrates.

---

## Why this exists

The v5.13–v5.19 terseness arc closed the *block-level* and
*expression-level* density gaps (colon syntax, comprehensions,
implicit return, lambdas, string interp). What's left visible
in `mapanare/self/` and any user code is **struct-shaped
boilerplate** — three patterns that re-emerge constantly:

1. **Constructor noise.** `new Point { x: x, y: y, z: z }` —
   the field names duplicate the local variable names. CLAUDE.md
   explicitly calls out the constructor-pattern (`let r: T =
   first_field; return r`) as a Mapanare idiom; field shorthand
   collapses the surrounding ceremony.
2. **Partial-update tax.** Updating one field of a struct
   currently reads as `Point { x: 5, y: old.y, z: old.z }` —
   every unchanged field has to be quoted. Rust's `..old` syntax
   removes the noise.
3. **Manual destructuring.** `let p = get_point(); let x = p.x;
   let y = p.y` is three lines for what should be one.
4. **Match-for-binding.** Today, unwrapping an Option or Result
   for a single binding requires a full `match` expression.
   `if let Some(x) = opt { ... }` is the idiomatic short form.

Te.5 lands these four together because they share the same
parser/semantic touchpoints (struct literal expressions, `let`
patterns, `if`/`while` condition forms) and reading them as
separate releases would be artificial.

**Why post-rewrite, not bundled into v5.17.0 Sh.*:** auto-
migration via `mnc fmt --to-terse` is not safe for any of these
features. Field shorthand requires checking that the source
expression is a bare identifier with the same name as the field
— that's a semantic check, not a syntactic one. Struct update
syntax requires inferring which fields are unchanged from
context. Destructuring requires recognizing the pattern of
sequential `let p.field` access. None of these can be
mechanically rewritten without risking semantic changes. So Te.5
ships as additive sugar; existing code stays as-is until a human
chooses to rewrite it.

---

## Goal

1. **Field shorthand**: `Point { x, y }` is sugar for
   `Point { x: x, y: y }`. Works in both `new T { ... }` and
   bare `T { ... }` (if both forms exist in the grammar).
2. **Struct update syntax**: `Point { x: 5, ..old }` builds a
   Point with `x = 5` and all other fields copied from `old`.
   The `..old` form must come last in the field list.
3. **Destructuring in `let`**: `let Point { x, y } = p` binds
   `x` and `y` to the corresponding fields. Supports nested
   destructuring (`let Outer { inner: Inner { a }, b } = o`)
   and rest patterns (`let Point { x, .. } = p`).
4. **`if let`** and **`let else`**:
   - `if let Some(x) = opt { ... }` runs the block iff `opt` is
     `Some(x)`, binds `x` in the block.
   - `if let Ok(v) = res { ... } else { ... }` extends naturally
     with a no-bind else branch.
   - `let else`: `let Some(x) = opt else { return None }` —
     diverging else is required to satisfy the binding.
5. Bootstrap mirrors all four.
6. Goldens cover the matrix.
7. Strict 3-stage fixed point preserved.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.5.A** | HIGH | Phase 0 design doc: lock the surface syntax for all four features. List ambiguities + decisions (e.g., does `Point { x }` conflict with block syntax? Does `let else` allow non-pattern bindings?). | 1–2h |
| **Te.5.B** | HIGH | Field shorthand: grammar + transformer. Detect `Point { x, y }` and rewrite at AST construction time to `Point { x: x, y: y }`. | 1–2h |
| **Te.5.C** | HIGH | Struct update syntax: `Point { x: 5, ..old }`. Grammar + AST node `StructUpdate(base: Expr, overrides: list[(name, expr)])`. Lowering: emit a copy from `old` plus per-override stores. | 2–3h |
| **Te.5.D** | HIGH | Destructuring in `let`: `let Point { x, y } = p`. Extend `let_stmt` grammar to accept patterns; lowering desugars to a series of field-extraction `let`s. | 3–4h |
| **Te.5.E** | HIGH | `if let` / `while let` / `let else`: `if let Some(x) = opt { ... }`. Grammar + AST + semantic checking + lowering to existing `match` machinery. | 4–6h |
| **Te.5.F** | HIGH | Bootstrap parser + lower mirrors for all four. Largest sub-piece because the patterns interact. | 4–6h |
| **Te.5.G** | HIGH | Goldens: `tests/golden/struct_*.mn` covering shorthand, update, destructuring, `if let`, `let else`. 8+ new tests. | 1–2h |
| **Te.5.H** | LOW | `mnc fmt`: canonicalize new forms (no auto-rewriting from old to new — preserve intent). | 1h |
| **Te.5.I** | LOW | SPEC.md updates for sections 3.7 (Struct Types), 4.6 (Match), 5.x (new Patterns subsection if needed). | 1h |

---

## Phase plan

**Phase 0 — Design lock.** Write
`docs/roadmap/v5/v5.20.0/STRUCT_ERGO_DESIGN.md`. Decisions to
lock:

- **Field shorthand inside `match` patterns:** `match p { Point
  { x, y } => ... }` — does this destructure both fields, or
  match-by-value? Recommendation: destructure (matches Rust).
- **Struct update form:** `Point { x: 5, ..old }` (Rust style,
  trailing) or `Point { ...old, x: 5 }` (JS style, override
  semantics)? Recommendation: trailing `..old` (matches Rust;
  one-pass left-to-right reading).
- **Multiple `..base` allowed?** No — single base only.
- **`let else` requirements:** the else branch must diverge
  (return, break, continue, panic, abort). Compiler enforces.
- **`if let` chains:** `if let X = a && let Y = b` — defer to a
  future release (Rust only stabilized this in 2024). Te.5
  ships single-pattern `if let` only.
- **Rest patterns in `let`:** `let Point { x, .. } = p` allowed
  in `let`. `..` matches any leftover fields without binding.
- **Default values via shorthand:** `Point { x = 0, y }` is
  **not** part of Te.5 — defer.

**Phase 1 — Field shorthand (Te.5.B).** Smallest, ship first.
Grammar:

```lark
struct_field_init: NAME (":" expression)?
```

Transformer: when `:` is absent, treat as `NAME: NAME` —
look up the local with the same name as the field.

Goldens:

```mn
let x = 1; let y = 2
let p = Point { x, y }
assert p.x == 1 && p.y == 2
```

**Phase 2 — Struct update syntax (Te.5.C).** Grammar:

```lark
struct_lit: NAME "{" struct_field_init ("," struct_field_init)*
            ("," ".." expression)? "}"
```

AST node `StructUpdate(struct_name, base_expr, overrides)`.
Lowering:

```text
Point { x: 5, ..old }

  → let _tmp = old;
    Point { x: 5, y: _tmp.y, z: _tmp.z }
```

Semantic: type-check that `base_expr` is the same struct type;
auto-fill any fields not in `overrides` from the base.

**Phase 3 — `let` destructuring (Te.5.D).** Grammar:

```lark
let_stmt: "let" KW_MUT? let_target (":" type_expr)? "=" expression

let_target: NAME                                      // existing
          | "Point" "{" field_pattern ("," ...)*       // struct
          | "(" let_target ("," let_target)+ ")"       // tuple
```

Where `field_pattern` is `NAME` (shorthand bind),
`NAME ":" let_target` (rename + nested), or `".."` (rest).

Lowering desugars to field-by-field assignments:

```mn
let Point { x, y } = p
  → let x = p.x; let y = p.y
```

Mutability: `let mut Point { x, y } = p` makes both `x` and
`y` mutable. Per-field mutability (`let Point { mut x, y }`)
is allowed if the design doc decides so.

**Phase 4 — `if let` / `while let` / `let else` (Te.5.E).**
Grammar:

```lark
if_let_expr: "if" "let" pattern "=" expression block ("else" block)?
while_let_stmt: "while" "let" pattern "=" expression block
let_else_stmt: "let" pattern "=" expression "else" block
```

Lowering: all three desugar to `match`:

```mn
if let Some(x) = opt { body } else { else_body }
  → match opt { Some(x) => body, None => else_body }

while let Some(x) = pop_one() { body }
  → loop { match pop_one() { Some(x) => body, None => break } }

let Some(x) = opt else { return None }
  → match opt { Some(x) => x, None => { return None } }
```

For `let else`, semantic checker verifies the else branch
diverges (control-flow analysis already exists for exhaustive
match — reuse).

**Phase 5 — Bootstrap mirror (Te.5.F).** All four features in
`mapanare/self/parser.mn`, `lower.mn`, `ast.mn` (new pattern
nodes if any). Validate per-feature with the corresponding
goldens before moving on.

**Phase 6 — Goldens (Te.5.G).** New tests:

- `struct_shorthand.mn`
- `struct_update.mn`
- `struct_update_partial.mn` (multiple overrides)
- `let_destructure.mn`
- `let_destructure_nested.mn`
- `let_destructure_rest.mn`
- `if_let.mn`
- `if_let_else.mn`
- `while_let.mn`
- `let_else.mn`

**Phase 7 — fmt + docs + closeout.** SPEC, README example
refresh (replace verbose constructor with shorthand), CHANGELOG,
SESSION_REPORT.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Field shorthand shadows local with same name as field but different type | LOW | Type checker already enforces `field: T = value: T'` errors when types mismatch. Shorthand is sugar; same error path. |
| Struct update with type-incompatible base silently picks wrong fields | MEDIUM | Phase 2's semantic check rejects `Point { x: 5, ..circle }` if `circle` is not a `Point`. Test explicitly. |
| Destructuring in mutable `let` produces shared mutable references | LOW | Field destructuring desugars to `let x = p.x` which is a copy for value types and a reference for ref types — same as direct field access. No new aliasing. Document. |
| `let else` diverging-check is incomplete (allows non-divergent else) | MEDIUM | Reuse existing exhaustiveness check from `match`; Phase 4 has explicit test cases for `let else { 42 }` (should error) and `let else { return X }` (should accept). |
| `if let` chained with `else if let` is misparsed | LOW | Standard ambiguity; use Rust's grammar precedent. Test the chain explicitly in goldens. |
| Bootstrap mirror introduces semantic drift | HIGH | Per-feature validation (Te.5.B → Te.5.F sub-modules → Te.5.G goldens). Strict 3-stage fixed point check after every phase. |
| `let else` interacts badly with implicit return (the function might be the diverging path) | MEDIUM | Specify in Phase 0: `let X = expr else { return None }` requires the else branch to *exit the current scope*, which `return` satisfies. The function's implicit return doesn't satisfy because it's not yet in the else branch. |
| Strict 3-stage fixed point breaks because lowering of new forms is non-deterministic | HIGH | Each new form has a single canonical lowering. Audit `lower.mn` for any randomness or hash-ordered iteration. |

---

## Out of scope (deferred)

- **`if let` chains** (`if let X = a && let Y = b`) — defer to
  v5.21.0+ if demand surfaces.
- **Default values in struct literals** (`Point { x = 0, y }`) —
  defer; needs broader struct-default story.
- **Tuple structs** (`struct Point(Int, Int)`) — defer; design
  question about positional access (`.0`, `.1`).
- **Field punning in match patterns** (`match p { Point { x, y }
  => ... }`) — depends on Phase 0 decision; if voted in, ships
  with Te.5; else defers.
- **Or-patterns at the top level of `let`** (`let (Some(x) |
  Ok(x)) = e`) — defer; Te.5 keeps `let` patterns refutable
  only via `let else`.
- **Move/borrow distinction in destructuring** — pre-borrow-
  checker; v6.0 territory.
- **Pattern guards in `if let`** (`if let Some(x) if x > 0 = e`)
  — defer.

---

## Success criteria

- `Point { x, y }` and `Point { x: x, y: y }` produce identical
  IR.
- `Point { x: 5, ..old }` and a hand-written copy-then-override
  produce identical IR.
- `let Point { x, y } = p` and `let x = p.x; let y = p.y`
  produce identical IR.
- `if let Some(x) = opt { f(x) }` and the equivalent `match`
  produce identical IR.
- `while let Some(x) = pop() { f(x) }` and the equivalent
  `loop { match }` produce identical IR.
- `let Some(x) = opt else { return None }` enforces divergence
  in the else branch (compile error if missing).
- 10+ new goldens land in `tests/golden/struct_*.mn` and
  `tests/golden/let_*.mn` and `tests/golden/if_let_*.mn`,
  all passing.
- Goldens 84+/84+ (66 existing + Te.2's 6 + Te.4's 8 + Te.5's
  10).
- Strict 3-stage fixed point preserved.
- Bootstrap mirror complete and self-compiles.
- `mnc fmt` does not auto-rewrite old forms to new — only
  canonicalizes new forms when present.
- README example switched to shorthand; SPEC §3.7, §4.6, §5
  updated.
- `make lint` clean.
- SESSION_REPORT documents Phase 0 decisions verbatim.
