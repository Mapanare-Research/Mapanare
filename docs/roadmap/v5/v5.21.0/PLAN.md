# v5.21.0 — Te.6 — small ergonomic wins

**Status:** PLANNING
**Breaking:** No. Pure additive surface syntax; existing code
parses identically.
**Prerequisite:** v5.20.0 shipped (Te.5 — struct ergonomics).
**Estimated effort:** 4–8h, single session. The release is
deliberately small; if it grows beyond ~8h, split.

---

## Why this exists

Through the v5.13–v5.20 terseness arc, a few small ergonomic
wins surfaced that didn't fit any cluster's theme cleanly but
are real readability improvements:

1. **Chained comparisons** — `0 < x < 10` reads better than
   `x > 0 && x < 10`. Small grammar change, big reader win in
   numeric code.

This release is the "small wins" sink for that kind of item.
It exists explicitly *because* small features are still worth
shipping — the cost of an extra release is low, the cost of
quietly dropping a real win because it "didn't seem big enough"
is permanent. New small wins can be added to Te.6 scope as they
emerge during the v5.13–v5.20 arc execution; if Te.6 fills up
beyond ~8h, the cluster splits into Te.6 + Te.7.

This also sets the precedent that ergonomic polish is its own
legitimate scope, not a sub-line of feature releases.

---

## Goal

1. **Chained comparisons** — Python-style `a < b < c` parses
   and means `a < b && b < c`, with `b` evaluated only once.
2. Bootstrap mirror.
3. Goldens cover the common shapes (3-element, 4-element,
   mixed operators, negatives, side-effecting middle term).
4. Strict 3-stage fixed point preserved.

(Add new items here as they emerge during v5.13–v5.20
execution.)

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.6.A** | HIGH | Phase 0 design: lock the operator set (just `<`/`<=`/`>`/`>=`/`==`/`!=` chain, or include `in` / `is`?). Lock middle-evaluation semantics (once, not once-per-comparison). | 0.5h |
| **Te.6.B** | HIGH | Grammar: `cmp_expr` rule extended to allow chained `cmp_op` runs. AST node `ChainedCompare(operands: list[Expr], ops: list[CmpOp])`. | 1h |
| **Te.6.C** | HIGH | Lowering: desugar `a < b < c` to `let _t = b; a < _t && _t < c` — temp introduced for any non-trivial middle term. For literal middles (numbers, identifiers), skip the temp. | 1–1.5h |
| **Te.6.D** | HIGH | Bootstrap mirror in `mapanare/self/parser.mn`, `lower.mn`, `ast.mn`. | 1.5–2h |
| **Te.6.E** | MEDIUM | Goldens: `chained_cmp_simple.mn` (`0 < x < 10`), `chained_cmp_4.mn` (`a < b < c < d`), `chained_cmp_mixed.mn` (`a <= b < c`), `chained_cmp_side_effect.mn` (`f() < g() < h()` — verify `g()` runs once). | 0.5–1h |
| **Te.6.F** | LOW | `mnc fmt`: canonicalize whitespace inside chains (single space around each operator). | 0.25h |
| **Te.6.G** | LOW | SPEC.md §2.2 (operators) note about chaining. | 0.25h |

---

## Phase plan

**Phase 0 — Operator set + semantics lock.** Decisions:

- Operators in the chain: `<`, `<=`, `>`, `>=`, `==`, `!=`.
  Pure comparison only — no `&&`, `||`, `in`, `is` mixed in.
- Direction mixing: `0 < x > -10` is **legal** (each pair is
  evaluated independently). Document that this is rarely useful
  but not an error.
- Middle term evaluation: **once**, even for side-effecting
  expressions. `f() < g() < h()` calls `g()` exactly once.
- Operator precedence: chained comparisons have the same
  precedence as a single comparison — they bind tighter than
  `&&` and looser than `+`.
- Boolean result: the chain is a single `Bool` value; you can
  use it in `if`, assign it, etc.

Document in `docs/roadmap/v5/v5.21.0/CHAINED_CMP_DESIGN.md`.

**Phase 1 — Grammar + AST (Te.6.B).** In `mapanare.lark`,
extend `cmp_expr`:

```lark
?cmp_expr: pipe_expr (cmp_op pipe_expr)*
cmp_op: LT | GT | LE | GE | EQ | NE
```

Transformer collects the run into a `ChainedCompare` AST node
when there are 2+ comparisons.

**Phase 2 — Lowering (Te.6.C).** In `lower.py`:

```text
ChainedCompare([a, b, c], [LT, LT])
  → let _t = lower(b)         // only if b is not a trivial expr
    let r = lower(a) < _t && _t < lower(c)
    r
```

Triviality check: identifier reference, literal, or already-bound
local — these don't get a temp. Anything else (function call,
arithmetic, field access of a complex receiver) gets a temp.

**Phase 3 — Bootstrap (Te.6.D).** Mirror in `mapanare/self/`.
Same triviality check.

**Phase 4 — Goldens (Te.6.E).**

```mn
// chained_cmp_simple.mn
fn main() {
    let x = 5
    assert 0 < x < 10
    assert !(0 < x < 3)
}

// chained_cmp_side_effect.mn
let mut count = 0
fn middle() -> Int { count += 1; 5 }

fn main() {
    assert 0 < middle() < 10
    assert count == 1   // middle() runs exactly once
}
```

**Phase 5 — fmt + docs (Te.6.F + Te.6.G).** Whitespace, SPEC
note. SESSION_REPORT documenting design decisions.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Side-effecting middle term evaluated twice (semantic regression) | MEDIUM | Phase 4 has an explicit count-check golden. CI fails if `middle()` runs twice. |
| Mixed-direction chains (`a < b > c`) confuse readers | LOW | Document in SPEC; `mnc fmt` does **not** rewrite mixed-direction chains as warning — preserve intent. Future linter rule could flag it. |
| Triviality check classifies a nontrivial expr as trivial | LOW | Conservative: when in doubt, introduce the temp. The temp is cheap; correctness matters more than IR length. |
| Bootstrap lowering disagrees with Python lowering on triviality | MEDIUM | Document the triviality rule precisely in CHAINED_CMP_DESIGN.md; both compilers reference the same rule. |
| Strict 3-stage fixed point breaks because temp naming differs | LOW | Use the existing fresh-temp naming scheme; do not invent new names. |

---

## Out of scope (deferred)

- Non-comparison chains (`a + b + c` is already left-assoc, no
  change needed)
- `in` / `is` membership chains (Python-style `a < b in xs`) —
  no real demand, defer
- Three-way comparison operator (`<=>`, spaceship) — separate
  arc, not in scope
- Pattern guards using chained cmp (`match x { n if 0 < n <
  10 => ... }`) — should *just work* once chained cmp parses;
  add as a smoke test, not new scope
- Range-membership shorthand (`x in 0..10`) — defer; needs
  iterator/range protocol decision
- New scope items added to Te.6 mid-arc — fold them in if
  scope still ≤ 8h, otherwise create v5.22.0 (Te.7)

---

## Success criteria

- `0 < x < 10` parses, type-checks, and lowers to a single
  Bool result
- 4-element chains work: `a < b < c < d`
- Mixed operators work: `a <= b < c`, `a == b == c`
- Side-effecting middle term evaluated exactly once
- Triviality check produces no temps for trivial middles, temps
  for non-trivial
- 4+ goldens land
- Goldens 88+/88+ (84 from Te.5 + 4 new)
- Strict 3-stage fixed point preserved
- Bootstrap mirror complete
- `mnc fmt --check` clean on goldens
- `make lint` clean
- SESSION_REPORT documents Phase 0 decisions
