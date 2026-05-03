# v5.20.0 — Struct Ergonomics Design Lock

**Status:** LOCKED — Phase 0
**Date:** 2026-04-30
**Scope:** Te.5.B / Te.5.C / Te.5.D / Te.5.E
**Operating principle:** Sugar over the existing pattern engine. Every
Te.5 form desugars to constructs Mapanare already has — struct
literals, field access, `match`, `let`, `while`. No new MIR ops, no
new IR shapes, no new runtime functions.

---

## Phase 0 surprise — partial pre-existing infrastructure

`mapanare/parser.py:1022` `field_init` already supports value-omitted
shorthand at the *transformer* level — falls back to
`Identifier(name=name)` when no `:` is present. Only the grammar
rule `field_init: NAME COLON expr` is mandatory-colon. **Te.5.B is
a 1-rule grammar relaxation, not a transformer rewrite.**

The bootstrap `mapanare/self/parser.mn` does not have the same
fall-through; bootstrap mirror in Phase 5 will bring the two into
parity.

No pre-existing infrastructure for: `StructPattern`, `FieldPattern`,
`RestPattern`, `StructUpdate`, `IfLetExpr`, `WhileLetStmt`,
`LetElseStmt`. All net-new.

---

## Locked decisions

### D1 — Struct update direction

`Point { x: 5, ..old }` (Rust style — trailing). Locked.

Rationale: one-pass left-to-right reading; explicit overrides come
first, fallback comes last; matches the `..rest` direction in
existing pattern semantics.

Rejected: `Point { ..old, x: 5 }` (JS style). The override-after-
spread reading is ambiguous when the override key matches a base
key — Rust avoids this entirely by putting the base last.

### D2 — Multiple `..base` per literal

Disallowed. Single base only. Compiler errors on
`Point { ..a, ..b }`.

Rationale: ambiguous merge semantics; no clear use case that
isn't expressible as `Point { ..a, ..b_overrides }` (manual).

### D3 — Field punning in match patterns

Allowed. `match p { Point { x, y } => f(x, y) }` destructures
both fields. Matches Rust.

Rationale: keeps the `let Point { x, y } = p` and `match p {
Point { x, y } => ... }` surfaces consistent.

**However:** v5.20.0 ships `StructPattern` for `let` only.
Match-side struct patterns ship in v5.20.0 too (cheap once the
pattern node exists), but receive lower test coverage; full
match-pattern parity polish moves to v5.21.0+ if gaps surface.

### D4 — Per-field mutability in destructuring

Allowed. `let Point { mut x, y } = p` makes only `x` mutable.
Top-level `let mut Point { x, y }` makes all bound names mutable.

Rationale: matches user prompt explicit decision; aligns with
Rust pattern grammar; no semantic complexity beyond the
desugaring (each field becomes its own `let` / `let mut`).

### D5 — `let else` divergence requirement

Required. The else branch must diverge. Compile-time enforced.

Divergent forms accepted:

- `return <expr>?`
- `break`
- `continue`
- `panic(<expr>?)` — calls runtime abort
- A tail expression that is itself a divergent call (semantic
  checker traces obvious cases; gives up on dynamic-dispatch
  divergence and accepts).
- A nested `if`/`match` where every arm diverges.
- A nested block whose tail statement diverges.

Compile error if the else branch can fall through. Error
points at the closing `}` of the else block with the diagnostic
shape used for non-exhaustive `match` arms.

### D6 — Implicit return interaction with `let else`

The else branch must *itself* diverge. The surrounding function's
implicit return does **not** satisfy the requirement.

Rationale: implicit return at function tail means the function
returns `()` or the tail value if the else branch falls through;
that's "returning normally," not "diverging." Forcing an explicit
`return` (or other divergent form) inside the else block keeps
the contract local and readable.

Concretely: this **fails** to compile —

```mn
fn foo() {
    let Some(x) = opt else { 42 }     // not divergent
    print(str(x))
}
```

Even though `foo` returns `()`, the else block must say `return`
(or `panic`, etc.) explicitly.

### D7 — `if let` chains

Not in v5.20.0. `if let X = a && let Y = b { ... }` deferred to
v5.21.0+ if demand surfaces. v5.20.0 ships single-pattern
`if let` only.

Rationale: Rust only stabilized chained `if let` in 2024;
adoption signals are still nascent; defer until we see real
calling code that needs it.

### D8 — `while let` semantics

Desugar to:

```mn
while true {
    match <scrutinee> {
        <pattern> => <body>,
        _ => break,
    }
}
```

Mapanare has no `loop` keyword — `while true` is canonical.

The scrutinee is re-evaluated each iteration (matches Rust).

### D9 — Rest pattern `..` in destructuring

Supported in `let` patterns. Binds nothing. Must come last in
the field list. At most one `..` per pattern.

Examples:

```mn
let Point { x, .. } = p              // OK — x bound, y/z ignored
let Point { x, .., y } = p           // ERROR — `..` must be last
let Point { x, .., .. } = p          // ERROR — at most one `..`
```

In v5.20.0, `..` in `let` patterns is the only supported rest
context. Tuple rest patterns (`let (x, .., z) = t`) are not in
scope (Mapanare's tuples are surface-only via `paren_expr`/
`tuple_expr` and don't yet have a destructuring story).

### D10 — Default-value shorthand

Excluded from Te.5. `Point { x = 0, y }` — defer.

Rationale: needs a broader struct-default story (do struct
definitions get default values? what about generic field
defaults?). v5.20.0 stays scoped to "rearrange existing data,"
not "introduce new data shapes."

---

## Surface syntax summary

```mn
// D1, D2 — struct update
let p1 = new Point { x: 1, y: 2, z: 3 }
let p2 = new Point { x: 99, ..p1 }              // x=99, y=2, z=3

// Te.5.B — field shorthand (in struct literals)
let x = 1; let y = 2; let z = 3
let p = new Point { x, y, z }                   // = new Point { x: x, ... }
let p4 = new Point { x: 99, y, z }              // mixed OK

// Te.5.D — let destructuring
let Point { x, y, z } = p                       // binds x, y, z
let Point { x, .. } = p                         // binds x only
let Point { x, mut y } = p                      // y mutable, x not (D4)
let Outer { inner: Inner { a }, b } = o         // nested
let mut Point { x, y } = p                      // both mutable

// Te.5.E — if let / while let / let else
if let Some(x) = opt { use(x) }
if let Some(x) = opt { use(x) } else { fallback() }
while let Some(x) = pop() { use(x) }
let Some(x) = opt else { return None }          // x bound for rest of scope
```

---

## AST nodes (Phase 1–4 will add these)

```python
# mapanare/ast_nodes.py

@dataclass
class StructUpdate(Expr):
    """new Name { field: expr, ..base }"""
    name: str = ""
    overrides: list[FieldInit] = field(default_factory=list)
    base: Expr = field(default_factory=Expr)

@dataclass
class StructPattern(Pattern):
    """Point { x, y, .. } in let or match."""
    name: str = ""
    fields: list[FieldPattern] = field(default_factory=list)
    has_rest: bool = False

@dataclass
class FieldPattern(ASTNode):
    """Field in a StructPattern: `x` (shorthand) or `x: nested`."""
    name: str = ""
    mutable: bool = False              # D4 — per-field mut
    sub_pattern: Pattern | None = None  # None ⇒ shorthand binds NAME

@dataclass
class IfLetExpr(Expr):
    """if let <pattern> = <scrutinee> { ... } [else { ... }]"""
    pattern: Pattern = field(default_factory=lambda: Pattern())
    scrutinee: Expr = field(default_factory=Expr)
    then_block: Block = field(default_factory=lambda: Block())
    else_block: Block | IfExpr | "IfLetExpr" | None = None

@dataclass
class WhileLetStmt(Stmt):
    """while let <pattern> = <scrutinee> { ... }"""
    pattern: Pattern = field(default_factory=lambda: Pattern())
    scrutinee: Expr = field(default_factory=Expr)
    body: Block = field(default_factory=lambda: Block())

@dataclass
class LetElseStmt(Stmt):
    """let <pattern> = <scrutinee> else { ... }"""
    pattern: Pattern = field(default_factory=lambda: Pattern())
    type_annotation: TypeExpr | None = None
    scrutinee: Expr = field(default_factory=Expr)
    else_block: Block = field(default_factory=lambda: Block())
```

`LetBinding` is **not** modified to carry a pattern. Destructuring
`let X { y, z } = e` is parsed as a separate `LetDestructure` node
that lowers to `let _tmp = e; let y = _tmp.y; let z = _tmp.z`.

```python
@dataclass
class LetDestructure(Stmt):
    """let <StructPattern> [: T] = <expr>"""
    pattern: Pattern = field(default_factory=lambda: Pattern())
    mutable: bool = False              # outer `let mut`
    type_annotation: TypeExpr | None = None
    value: Expr = field(default_factory=Expr)
```

Rationale for the split: `LetBinding` (single name) is the hot
path for the existing 14k-line bootstrap; widening it to carry a
pattern would force every consumer to re-check. A separate node
keeps the change additive.

---

## Lowering plan (per feature)

### Te.5.B — Field shorthand

**No lowering change.** Already works at the transformer level
(see Phase 0 surprise). Grammar edit only:

```lark
field_init: NAME (COLON expr)?
```

### Te.5.C — Struct update

`StructUpdate` lowers to: emit base into a fresh tmp, then emit a
regular `ConstructExpr` filling overrides explicitly and falling
back to `<tmp>.<field>` for any field not in `overrides`. Type
checker (semantic) verifies the base expression has the same
struct type as `name` and resolves the field list.

```mn
new Point { x: 5, ..old }
  ⇒ {
        let __mn_base_N: Point = old
        new Point { x: 5, y: __mn_base_N.y, z: __mn_base_N.z }
    }
```

The `__mn_base_N` temp is generated even when `old` is a bare
identifier — keeps semantic uniformity and side-effect ordering.

### Te.5.D — `let` destructuring

`LetDestructure` lowers in `_lower_let_destructure` (new function):

```mn
let Point { x, mut y } = p

  ⇒  let __mn_dst_N: Point = p
     let x = __mn_dst_N.x
     let mut y = __mn_dst_N.y
```

Single tmp; field accesses are emitted in declaration order;
nested patterns recurse — `let Outer { inner: Inner { a }, b } = o`
becomes:

```mn
let __mn_dst_N: Outer = o
let __mn_inner_M: Inner = __mn_dst_N.inner
let a = __mn_inner_M.a
let b = __mn_dst_N.b
```

Rest patterns (`..`) emit no `let` — fields not named are simply
not bound.

### Te.5.E — `if let` / `while let` / `let else`

All three desugar in the lowerer to existing `match` shapes.
Lowering is direct (no AST rewrite at parse time) so error
messages can refer to source-level `if let` / `while let` /
`let else` keywords.

```mn
if let Some(x) = opt { body } [else { else_block }]

  ⇒  match opt {
         Some(x) => <body>,
         _ => <else_block | ()>,
     }

while let Some(x) = pop() { body }

  ⇒  while true {
         match pop() {
             Some(x) => <body>,
             _ => break,
         }
     }

let Some(x) = expr else { else_block }

  ⇒  let __mn_le_N = expr
     match __mn_le_N {
         Some(x) => (),                  // bindings extracted below
         _ => { <else_block> },          // must diverge — D5
     }
     let x = __mn_le_N.<unwrap_field>     // synthesized per pattern
```

The `let else` lowering is the trickiest because the bindings
introduced by the pattern must persist in the *outer* scope, not
inside the match arm. Two strategies:

1. **Inline-and-extract** (above): match runs purely for the
   "fall-through-or-not" check; bindings are re-extracted via
   field access on the temp after the match.
2. **Synthesized-tuple-return**: match arm builds a tuple of all
   bound values; outer `let` destructures the tuple.

Strategy 1 is simpler and emits less IR. **Locked: strategy 1.**
For nested patterns, the extraction goes recursively (e.g.,
`let Some(Point { x, y }) = e else { ... }` extracts `_tmp.0.x`
and `_tmp.0.y` after the match — but Mapanare doesn't yet have
positional struct access, so v5.20.0 supports `let else` only
with patterns at depth ≤ 2 where each level has a name to
field-access through). This depth limit is a v5.20.0 simplification;
deeper `let else` patterns deferred to v5.21.0+.

For Mapanare's actual pattern set (Some/Ok/Err + struct), the
extraction step works because:

- `Some(x)` → `__mn_le_N.value` (Option is `{tag, value}` shape)
- `Ok(v)` → `__mn_le_N.ok_value` (Result is tagged shape)
- `Err(e)` → `__mn_le_N.err_value`
- `Point { x, y }` → `__mn_le_N.x`, `__mn_le_N.y`

Implementation detail: `_lower_let_else` will reuse the existing
"unwrap" helpers from `_lower_match` for Some/Ok/Err and the
field-access path for `StructPattern`.

---

## Format canonicalization (Te.5.H)

`mapanare/format.py` post-Te.5 rules:

1. Whitespace inside `{ }` of struct literal: one space inside
   each side.
2. `..base` placement: always last in the field list.
3. `if let` / `while let` / `let else`: standard keyword spacing.
4. **No auto-rewrite** from long form to short form. `Point { x:
   x, y: y }` does NOT become `Point { x, y }` under
   `mnc fmt --to-terse` because the safety check ("is the value
   a bare identifier with the same name as the field?") is a
   semantic question — `mnc fmt` is whitespace-only +
   AST-preserving and cannot answer it without growing into a
   semantic-aware rewriter, which is out of scope per CLAUDE.md
   v5.13.0 ("Conservative by design").

---

## Bootstrap mirror plan (Te.5.F)

Per-feature commit ordering (smallest to largest):

1. **Te.5.B mirror** — `mapanare/self/parser.mn`: relax
   `parse_field_init` to allow value-omitted shorthand.
   `~10 LOC`. No `ast.mn` change (FieldInit shape unchanged —
   shorthand fills `value` with an `Ident` at parse time).
2. **Te.5.C mirror** — `ast.mn`: new `StructUpdate` variant on
   `Expr`. `parser.mn::parse_construct_expr`: accept trailing
   `, ..base`. `lower.mn`: new `lower_struct_update` follows
   Python's `_lower_struct_update`. `~120 LOC`.
3. **Te.5.D mirror** — `ast.mn`: new `Pat::Struct(name,
   fields, has_rest)`, `FieldPattern` struct, `Stmt::LetDest(...)`.
   `parser.mn`: `parse_let_stmt` looks ahead for `KW_LET (KW_MUT)?
   NAME LBRACE` to dispatch to `parse_let_destructure`. `lower.mn`:
   `lower_let_destructure` mirrors Python. `semantic.mn`: type-
   check struct-pattern field names. `~250 LOC`.
4. **Te.5.E mirror** — `ast.mn`: new `Expr::IfLet`,
   `Stmt::WhileLet`, `Stmt::LetElse`. `parser.mn`: extend
   `parse_if_expr` to detect `KW_IF KW_LET`, extend
   `parse_while_stmt` for `KW_WHILE KW_LET`, extend
   `parse_let_stmt` for `KW_LET <pattern> ASSIGN <expr> KW_ELSE`.
   `lower.mn`: three new lowering functions. `semantic.mn`:
   divergence check for let-else else block. `~400 LOC`.

After each per-feature commit:

- `python scripts/build_stage1.py`
- `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
- `bash scripts/verify_fixed_point.sh --keep`

If strict 3-stage fixed point breaks at any commit, the bootstrap
lowering is non-deterministic — fix in `lower.mn`, do not paper
over.

---

## Goldens (Te.5.G)

Minimum 10 new goldens:

| File | Feature | Asserts |
|---|---|---|
| `81_struct_shorthand.mn` | Te.5.B | shorthand IR == long-form IR |
| `82_struct_update.mn` | Te.5.C | `..old` overrides + carries-over |
| `83_struct_update_partial.mn` | Te.5.C | multi-field override |
| `84_let_destructure.mn` | Te.5.D | basic `let X { y, z } = e` |
| `85_let_destructure_nested.mn` | Te.5.D | `let X { y: Y { a }, b }` |
| `86_let_destructure_rest.mn` | Te.5.D | `let X { y, .. }` |
| `87_let_destructure_mut.mn` | Te.5.D | `let X { mut y, z }` |
| `88_if_let.mn` | Te.5.E | `if let Some(x) = ...` |
| `89_if_let_else.mn` | Te.5.E | with else branch |
| `90_while_let.mn` | Te.5.E | drain via `while let` |
| `91_let_else.mn` | Te.5.E | `let Some(x) = ... else { return }` |

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Field shorthand shadows local with same name as field but different type | LOW | Type checker already enforces field-type/value-type compat. Same error path. |
| Struct update with type-incompatible base silently picks wrong fields | MEDIUM | Phase 2 semantic check rejects mismatched base type. Test explicitly. |
| Destructuring in mutable `let` produces shared mutable references | LOW | Field destructure desugars to `let x = p.x` — same aliasing as direct field access. No new aliasing. |
| `let else` divergence-check is incomplete | MEDIUM | Reuse existing exhaustive-match check infrastructure. Negative test for non-divergent else. |
| `if let` chained with `else if let` is misparsed | LOW | Standard ambiguity; test the chain explicitly. |
| Bootstrap mirror introduces semantic drift | HIGH | Per-feature validation + strict fixed-point check after every phase. |
| `let else` interacts badly with implicit return | MEDIUM | D5/D6 explicit: function-tail implicit return does NOT satisfy divergence. Test it. |
| Strict 3-stage fixed point breaks because lowering is non-deterministic | HIGH | Each form has a single canonical lowering. Audit `lower.mn` for hash-ordered iteration. |
| `KW_NEW` mandatory in struct literal interacts with destructuring patterns | MEDIUM | Destructuring patterns do NOT use `new` (it's pattern-position, not expression-position). Grammar disambiguates by context — pattern grammar runs in `let_stmt` / `match_arm`, expression grammar in expression position. |

---

## Success criteria (verbatim from PROMPT.md)

- `Point { x, y }` and `Point { x: x, y: y }` produce identical IR.
- `Point { x: 5, ..old }` and a hand-written copy-then-override
  produce identical IR.
- `let Point { x, y } = p` and `let x = p.x; let y = p.y`
  produce identical IR.
- `if let Some(x) = opt { f(x) }` and the equivalent `match`
  produce identical IR.
- `while let Some(x) = pop() { f(x) }` and the equivalent
  `while true { match }` produce identical IR.
- `let Some(x) = opt else { return None }` enforces divergence
  in the else branch (compile error if missing).
- 10+ new goldens land in `tests/golden/struct_*.mn` and
  `tests/golden/let_*.mn` and `tests/golden/if_let_*.mn`,
  all passing.
- Goldens 84+/84+ (66 existing + Te.2's 6 + Te.4's 8 + Te.5's 10).
- Strict 3-stage fixed point preserved.
- Bootstrap mirror complete and self-compiles.
- `mnc fmt` does not auto-rewrite old forms to new — only
  canonicalizes new forms when present.
- README example switched to shorthand; SPEC §3.7, §4.6, §5
  updated.
- `make lint` clean.
- SESSION_REPORT documents Phase 0 decisions verbatim.

---

## Out of scope (deferred to v5.21.0+)

- `if let` chains (`if let X = a && let Y = b`)
- Default values in struct literals (`Point { x = 0, y }`)
- Tuple structs (`struct Point(Int, Int)`) and positional access
- Field punning in match patterns at parity with `let`
- Or-patterns at the top level of `let` (`let (Some(x) | Ok(x)) = e`)
- Move/borrow distinction in destructuring — v6.0
- Pattern guards in `if let` (`if let Some(x) if x > 0 = e`)
- Tuple destructuring (`let (x, y) = t`) — Mapanare tuples
  are surface-only via `paren_expr`/`tuple_expr` and lack a
  destructuring story.
- Deeper `let else` patterns (depth > 2) — strategy 1 extraction
  needs positional access for tagged variants nested deeper.

---

## Phase order

| Phase | Item | Effort | Validates |
|---|---|---|---|
| 0 | This document | shipped | — |
| 1 | Te.5.B field shorthand (Python) | 0.5h | grammar + 1 golden |
| 2 | Te.5.C struct update (Python) | 2h | grammar + lowering + 2 goldens |
| 3 | Te.5.D let destructuring (Python) | 3h | grammar + lowering + 3 goldens |
| 4 | Te.5.E if-let / while-let / let-else (Python) | 4h | grammar + 3 lowerings + divergence + 4 goldens |
| 5 | Te.5.F bootstrap mirror | shipped in v5.20.1 | 4 sub-features, fixed-point check each |
| 6 | Te.5.G golden consolidation | 1h | 10+ pass through stage1 |
| 7 | Te.5.H + Te.5.I — fmt + SPEC + closeout | 2h | docs + SESSION_REPORT |

Total: 16-21h. Within PLAN.md's 16-24h budget.

---

## Notes for implementers

1. **Watch `_lower_let` and `_lower_match` for hash-ordered
   iteration** — the strict 3-stage fixed point at v5.18.0
   (231,723 lines / 0-line diff post-v5.17.2) is achieved by
   careful insertion-order handling. Adding new `LetDestructure`
   / `IfLetExpr` lowering must preserve insertion order in any
   set/dict iteration.
2. **Span tracking** — every new AST node must carry a `Span`
   for v5.18.0 LSP compatibility. Use `_span_from_children` in
   parser.py.
3. **Bootstrap parser adds tokens** — verify `KW_LET` /
   `KW_NEW` / `KW_ELSE` are already lexed; new keywords needed
   only if a feature introduces one (none in Te.5).
4. **Goldens land at numbers 81-91** to follow the existing
   v5.16.0 (72-80 string-interp) sequence. v5.17/5.18/5.19
   added no goldens.
5. **`mnc fmt --check` clean** is part of CI — make sure new
   goldens pass formatting.
