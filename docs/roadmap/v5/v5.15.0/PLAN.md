# v5.15.0 — Te.2 — comprehensions, implicit return, terse lambdas

**Status:** PLANNING
**Breaking:** No. All three features are additive surface syntax.
Existing code keeps working unchanged.
**Prerequisite:** v5.14.0 shipped (colon-block syntax + fmt
`--to-terse` working).
**Estimated effort:** 16–25h, three sessions. Comprehensions are
the largest piece because they touch lower.py + emitter.

---

## Why this exists

Colon-block syntax (v5.14.0) saves a few characters per block but
doesn't deliver expression-level density. Python's terseness comes
from comprehensions, walrus, lambda one-liners, and implicit
"return last expression" semantics in expression contexts. v5.15.0
ships the three highest-leverage versions of those patterns:

1. **List/map comprehensions** — `[x*2 for x in xs if x > 0]`
   collapses 4 lines of imperative loop into 1.
2. **Implicit return one-liner** — `fn double(x) = x * 2` as sugar
   for `fn double(x): return x * 2`.
3. **Terse lambdas** — `|x| x*2` instead of
   `fn(x) { return x*2 }`.

> **Audit note (2026-04 v5.13.0 prep).** Block-form implicit
> return — "if a function has no explicit `return`, the last
> expression returns" — was originally part of this release's
> scope (Te.2.E). A pre-v5.13.0 audit verified it **already
> works** in both the Python bootstrap and `mnc-stage1`:
> `fn add(a, b) -> Int { a + b }` (no explicit `return`) compiles
> and runs correctly. SPEC §4.5 already documents the behavior.
> So the only implicit-return work left is the one-liner sugar
> form (`fn name() = expr`), which the parser currently rejects
> with `Unexpected '=' — expected '{'`.

Together with v5.14.0's colon syntax, this is what makes a 30-line
Python program land at ~25 lines of Mapanare instead of ~50.

---

## Goal

1. Ship list comprehensions (`[expr for x in iter if cond]`) and
   map comprehensions (`{k: v for ... }`). Lower to MIR loops,
   compile to LLVM IR with the same performance as a hand-written
   loop.
2. Ship the implicit-return one-liner form: `fn name(args) = expr`.
   (Block-form already works — see Audit note above.)
3. Ship a short lambda syntax. Recommendation: `|x| x * 2`
   (Rust-style closure syntax; doesn't conflict with bitwise OR
   because the leading `|` is unambiguous in expression context).
   Decide in Phase 0.
4. Bootstrap parser mirrors all three.
5. Goldens 66/66 + at least 6 new comprehension goldens covering
   the common patterns.
6. Strict 3-stage fixed point preserved.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.2.A** | HIGH | Phase 0: `TERSENESS_DESIGN.md`. Lock syntax for lambdas, decide implicit-return rules, list edge cases. | 1–2h |
| **Te.2.B** | HIGH | List comprehensions: grammar, AST node `Comprehension`, semantic checking, MIR lowering to a loop, emitter. | 5–8h |
| **Te.2.C** | HIGH | Map comprehensions: same path, different output type. | 2–3h |
| **Te.2.D** | MEDIUM | Implicit return one-liner form: `fn double(x) = x * 2`. Parser + lowering. | 1–2h |
| ~~**Te.2.E**~~ | ~~MEDIUM~~ | ~~Block-form implicit return.~~ **Already implemented** per v5.13.0-prep audit — SPEC §4.5 is real, not aspirational. Removed from scope. | — |
| **Te.2.F** | HIGH | Terse lambda: `|x| x * 2`. Lowers to existing closure machinery. | 2–3h |
| **Te.2.G** | HIGH | Bootstrap parser mirror in `mapanare/self/parser.mn` and AST in `mapanare/self/ast.mn`. | 4–6h |
| **Te.2.H** | HIGH | Tests: 6+ new goldens covering filter/map combos, nested comprehensions, type-inferred element types, lambda + comprehension composition. | 1–2h |
| **Te.2.I** | LOW | Update `mnc fmt` to canonicalize the new forms (no rewriting between long and short forms — preserve user intent). | 1h |

---

## Phase plan

**Phase 0 — Design lock.** Write `TERSENESS_DESIGN.md` covering:

- Lambda syntax: `|x| body` vs `\x -> body` vs `fn(x) body` (no
  braces). Recommendation: `|x| body`. Single-arg without `|`?
  (No — keep `|x|` always for grep-ability.)
- Implicit return: only `fn name() = expr` form, OR also
  block-form last-expression? **Recommendation:** both, with
  block form only when there's no explicit `return` anywhere in
  the function (so we don't surprise anyone reading mixed code).
- Comprehension generator clauses: `for x in iter if cond` is the
  first version; `for x in a for y in b` (nested) lands here too;
  `else` clauses (Python's `[x for x in xs if c else d]`) — defer.
- Type inference: comprehension element type inferred from the
  expression. If the iterable is `list[int]` and the expression
  is `x * 2.0`, result is `list[float]`.

**Phase 1 — Comprehensions, parser → AST.** New AST node
`Comprehension(expr, target, iter, conditions, kind="list"|"map")`.
Grammar:

```lark
list_comp: "[" expression "for" pattern "in" expression
           ("if" expression)* ("for" pattern "in" expression
           ("if" expression)*)* "]"
map_comp:  "{" expression ":" expression "for" ... "}"
```

**Phase 2 — Comprehensions, semantic + lowering.** Type-check
elements; lower to MIR. The MIR lowering pattern:

```
[expr for x in xs if cond]

  → let result = [];
    for x in xs:
      if cond:
        result.push(expr)
    result
```

**Phase 3 — Implicit return one-liner.** `fn double(x) = x * 2`
is sugar for `fn double(x): return x * 2`. Grammar change in
`fn_def` (allow `= expr` as an alternative to `block`); lowering
treats the expression as the body of an implicit `return` stmt.

Block-form implicit return is **not** in scope — it already works
per the v5.13.0-prep audit. See Audit note in "Why this exists."

**Phase 4 — Terse lambdas.** `|x| x * 2` lowers to existing closure
infrastructure. Already supported at MIR level; just parser +
AST sugar.

**Phase 5 — Bootstrap mirror.** Update `mapanare/self/ast.mn`,
`mapanare/self/parser.mn`, `mapanare/self/lower.mn`,
`mapanare/self/emit_llvm.mn` for the new constructs. Comprehension
lowering in lower.mn is the largest sub-piece.

**Phase 6 — Goldens.** Add `tests/golden/comprehension_*.mn`,
`tests/golden/lambda_terse.mn`, `tests/golden/implicit_return.mn`.

**Phase 7 — fmt + docs + closeout.**

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Lambda `\|x\|` ambiguous with bitwise OR | LOW | In LALR, `\|` at expression-start is unambiguous — bitwise OR is always infix. Verify in Phase 1 with parser tests. |
| Comprehension type inference wrong on mixed types | MEDIUM | Borrow logic from existing list literal type inference. New tests cover empty list, mixed numeric promotion, Option/Result element types. |
| Bootstrap lower.mn change breaks fixed point | HIGH | Validate after every Phase 5 sub-edit. If fixed point drifts, the Python lowering and the .mn lowering disagree on comprehension expansion — they must produce identical MIR. |
| Comprehension performance regression vs hand-written loop | LOW | Comprehensions lower to the same MIR ops as a manual loop. Benchmark in Phase 2 to confirm: `comprehension_perf.mn` vs `manual_loop.mn` produce equal IR (modulo SSA names). |

---

## Out of scope (deferred)

- Walrus operator (`:=`) — defer indefinitely; not on the critical
  path
- Set comprehensions — Mapanare has no native set type yet
- Generator expressions (lazy comprehensions) — defer; needs
  iterator protocol work
- Pattern matching in lambda args (`|Point(x, y)| ...`) — defer
- F-string-style interpolation upgrades — separate arc (We.* or
  similar)
- Single-line `if x: y` as an expression — defer; conflicts with
  Phase 0 rules from v5.14.0
- Decorator syntax — defer

---

## Success criteria

- `[x * 2 for x in [1, 2, 3]]` produces `[2, 4, 6]` and emits the
  same IR as the equivalent manual loop
- `{k: v * 2 for k, v in m}` produces a doubled-value map
- `fn double(x) = x * 2` and `fn double(x): return x * 2` produce
  identical IR
- `xs.map(|x| x * 2)` and `xs.map(fn(x) { return x * 2 })` produce
  identical IR
- 6+ new golden tests pass
- Goldens 66/66 (existing) + new = 72+/72+
- Strict 3-stage fixed point preserved
- `make lint` clean
