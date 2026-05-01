# v5.20.0 — Te.5 — struct ergonomics

**Date:** 2026-04-30.
**Cycle:** Phase 0 → Phase 4 in one session; Phase 5 (bootstrap
mirror) deferred to v5.20.1 mirror v5.14.0 → v5.14.1 + v5.15.0
→ v5.15.1 precedent.
**Status:** **READY** (Python side, pending closeout — see
"Deferred to v5.20.1" below).

---

## Headline

v5.20.0 lands the post-Sh.* terseness capstone — four struct
ergonomics features that auto-migration tools couldn't safely
produce during the v5.17.0 self-host rewrite. All four are
additive surface syntax with **zero new MIR ops, zero new
runtime functions, and zero new IR shapes** — every form
desugars to constructs Mapanare already had.

Concretely:

- **Te.5.B — field shorthand.** `Point { x, y }` ≡ `Point { x: x,
  y: y }`. AST-byte-identical, IR-byte-identical to the long
  form.
- **Te.5.C — struct update.** `Point { x: 5, ..base }` lowers to
  `let __mn_base_N = base; new Point { x: 5, y: __mn_base_N.y,
  z: __mn_base_N.z }`. IR-byte-identical to the manual long
  form.
- **Te.5.D — let destructuring.** `let Point { x, y } = p` binds
  `x` and `y` in the surrounding scope. Nested patterns
  (`let Outer { inner: Inner { a }, b } = o`), rest patterns
  (`let Point { x, .. } = p`), and per-field mutability
  (`let Point { mut x, y } = p`) all work. When the RHS is a
  bare Identifier (the common case), the lowerer skips the
  synthesized base tmp and runs field accesses directly on the
  source name — IR is byte-identical to `let x = p.x; let y =
  p.y`.
- **Te.5.E — if-let / while-let / let-else.** Three refutable-
  binding forms that desugar at lower time to existing
  match/while/let. Pattern bindings inside `let-else` leak into
  the surrounding scope (the essential feature). Else block
  divergence (D5/D6) is enforced at lower time with a clear
  error.

The v5.13–v5.20 terseness arc is now closed on the Python side.

## Phase 0 surprises

Phase 0 was the design lock (`STRUCT_ERGO_DESIGN.md`, 10 locked
decisions). Two surprises from the audit:

1. **Field shorthand was already half-shipped.** `mapanare/parser.py:1022`
   `field_init` transformer already had a value-omitted fall-through
   to `Identifier(name=name)`. Only the grammar rule
   `field_init: NAME COLON expr` was mandatory-colon. Te.5.B
   collapsed to a 1-character grammar relaxation.
2. **No infrastructure for the other three features.** No
   `StructPattern`, `FieldPattern`, `RestPattern`, `StructUpdate`,
   `IfLetExpr`, `WhileLetStmt`, or `LetElseStmt`. All net-new.

## Locked decisions (verbatim from `STRUCT_ERGO_DESIGN.md`)

| ID | Decision | Status |
|---|---|---|
| D1 | Struct update direction: trailing `..base` (Rust style) | Locked |
| D2 | Multiple `..base` per literal: disallowed | Locked |
| D3 | Field punning in match patterns: allowed (D-only in v5.20.0) | Locked |
| D4 | Per-field mutability in destructuring: allowed | Locked |
| D5 | `let else` divergence requirement: required, compile-enforced | Locked |
| D6 | Implicit return in `let else` else: does NOT satisfy divergence | Locked |
| D7 | `if let` chains: deferred to v5.21.0+ | Locked |
| D8 | `while let` semantics: `while true { match { _ => break } }` | Locked |
| D9 | Rest pattern `..` in destructuring: supported | Locked |
| D10 | Default-value shorthand (`Point { x = 0, y }`): excluded | Locked |

## Files touched

### Added

- `docs/roadmap/v5/v5.20.0/STRUCT_ERGO_DESIGN.md` (Phase 0 lock,
  ~ 10 locked decisions, AST-node sketch, lowering plan,
  bootstrap-mirror ordering, 11 planned goldens).
- `docs/roadmap/v5/v5.20.0/SESSION_REPORT.md` (this).
- `tests/golden/81_struct_shorthand.mn` (Te.5.B).
- `tests/golden/82_struct_update.mn` (Te.5.C).
- `tests/golden/83_struct_update_partial.mn` (Te.5.C, multi-override).
- `tests/golden/84_let_destructure.mn` (Te.5.D, basic).
- `tests/golden/85_let_destructure_nested.mn` (Te.5.D, nested).
- `tests/golden/86_let_destructure_rest.mn` (Te.5.D, rest).
- `tests/golden/87_let_destructure_mut.mn` (Te.5.D, per-field mut).
- `tests/golden/88_if_let.mn` (Te.5.E).
- `tests/golden/89_if_let_else.mn` (Te.5.E with else).
- `tests/golden/90_while_let.mn` (Te.5.E).
- `tests/golden/91_let_else.mn` (Te.5.E).

### Modified

- `mapanare/mapanare.lark` — three new statement productions
  (`let_dest_stmt`, `let_else_stmt`, `while_let_stmt`), one new
  expression production (`if_let_expr`), `field_init` shorthand,
  `construct_expr` extended with `..base`. ~25 line delta.
- `mapanare/ast_nodes.py` — 6 new dataclasses: `StructUpdate`,
  `StructPattern`, `FieldPattern`, `LetDestructure`, `LetElseStmt`,
  `WhileLetStmt`, `IfLetExpr`. ~50 line delta.
- `mapanare/parser.py` — 6 new transformer methods + import edits.
  ~70 line delta.
- `mapanare/semantic.py` — `_check_let_destructure`,
  `_check_let_else`, `_check_while_let`, `_check_if_let` plus the
  pattern-bindings helper. ~60 line delta.
- `mapanare/lower.py` — `_lower_struct_update`,
  `_lower_let_destructure`, `_emit_destructure_pattern`,
  `_lower_if_let`, `_lower_while_let`, `_lower_let_else`, plus
  module-level divergence helpers (`_block_diverges`,
  `_stmt_diverges`, `_expr_or_block_diverges`). ~280 line delta.
  New `self._struct_update_counter` (separate from `_tmp_counter`)
  keeps Te.5.C and Te.5.D synthesized base tmps from perturbing
  the global `%tN` sequence — preserves byte-identical IR vs the
  manual long forms.

## Goldens delta

11 new (`81_…91_`). Existing 80 unchanged. **Python bootstrap:
91/91 PASS.** Native stage1: 80/80 PASS for the existing corpus,
**11/11 FAIL for the new goldens** because `mnc-stage1` was
built from v5.18.0 source which doesn't know any of the Te.5
forms. The bootstrap mirror that closes this is on the v5.20.1
docket (Phase 5 — see "Deferred" below).

## Validation

- `python3 -m pytest tests/parser/ tests/semantic/` — **557
  passed** in 17s. No regressions.
- All 11 new goldens compile through `mapanare emit-llvm` and
  the resulting IR validates via `clang -c`.
- Te.5.B IR byte-identical to long form (success criterion #1).
- Te.5.C IR byte-identical to long form (success criterion #2).
- Te.5.D IR byte-identical to `let x = p.x; let y = p.y` when
  RHS is a bare ident (success criterion #3).
- Te.5.E if-let / while-let IR byte-identical to manual
  `match` / `while true { match }` long forms (success
  criteria #4, #5).
- Te.5.E let-else: structurally identical to manual
  `let x = match scrutinee { Some(x) => x, _ => { return } }`,
  with a 1-step PHI counter offset (negligible — same
  instructions, same semantics).
- Te.5.E let-else divergence: non-divergent else block errors
  at lower time with a clear message (success criterion #6).

## Deferred to v5.20.1

- **Te.5.F — bootstrap mirror.** Mirror all four features in
  `mapanare/self/{ast,parser,lower,semantic}.mn`. Per design
  doc estimated 4–6h on its own (Te.5.B ~10 LOC, Te.5.C ~120,
  Te.5.D ~250, Te.5.E ~400). Splitting bootstrap mirror into
  v5.20.1 follows the v5.14.0 → v5.14.1 colon-block pattern
  and the v5.15.0 → v5.15.1 comprehension pattern — both
  released the Python feature first, then patched in the
  bootstrap mirror as a follow-up so each release stays
  manageable.
- **Strict 3-stage fixed point.** Will be re-validated as part
  of v5.20.1's mirror work. v5.20.0 doesn't change
  `mapanare/self/*.mn` so existing fixed-point status is
  unchanged from v5.18.0 (the 232,281-line / 0-line-diff
  milestone).
- **`mnc fmt --check` clean across new goldens.** Format rules
  for the new forms (Te.5.H) — defer with the bootstrap mirror.
  v5.20.0 does NOT auto-rewrite long forms to short forms
  (would be unsafe — see design doc rationale).

## Out of scope (deferred to v5.21.0+)

Per `STRUCT_ERGO_DESIGN.md`:

- `if let` chains (`if let X = a && let Y = b`).
- Default values in struct literals (`Point { x = 0, y }`).
- Tuple structs and positional access (`.0`, `.1`).
- Or-patterns at the top of `let`.
- Tuple destructuring (`let (x, y) = t`).
- Multi-binding `let else` patterns (`let Pair(a, b) = pair else
  { ... }`).
- Pattern guards in `if let`.
- Move/borrow distinction in destructuring (v6.0 territory).

## Risks discharged

| Risk (from design doc) | Outcome |
|---|---|
| Field shorthand shadows local with same name as field but different type | Type checker catches via existing field-type/value-type compat path. Confirmed in test. |
| Struct update with type-incompatible base silently picks wrong fields | `_lower_struct_update` validates override field names against `_struct_fields`; falls through to FieldAccessExpr lowering for unmentioned fields, which catches type mismatches. |
| Destructuring in mutable `let` produces shared mutable references | Field destructure desugars to `let x = p.x` — same aliasing as direct field access. No new aliasing. |
| `let else` divergence-check is incomplete | New `_block_diverges` recursive walker handles ReturnStmt/BreakStmt/ContinueStmt/panic-call/nested-if-match. Negative test confirms compile error on falling-through else. |
| `if let` chained with `else if let` is misparsed | LALR(1) handles via standard `IfExpr` else-block grammar; ASTs roundtrip correctly. |
| Bootstrap mirror introduces semantic drift | Deferred to v5.20.1 — mirrors will land per-feature with strict fixed-point validation between commits. |
| `let else` interacts badly with implicit return | D6 explicit: function-tail implicit return does NOT satisfy divergence. Test confirms compile error. |
| Strict 3-stage fixed point breaks because lowering is non-deterministic | All Te.5 lowering uses ordered iteration (struct field order from `_struct_fields`, list iteration). v5.20.1 mirror will validate. |
| `KW_NEW` mandatory in struct literal interacts with destructuring patterns | Pattern grammar is in `let_stmt` context; expression grammar in expression context. Disjoint. |

## Recommendations

1. **Tag v5.20.0 once you've reviewed.** Eight commits land cleanly
   (af61c91 base + 8586cd6 hygiene + 894920c Te.5.A/B + 06af1a8
   Te.5.C/D + 4ea40e1 Te.5.E + this report).
2. **v5.20.1 — Te.5.F bootstrap mirror.** Track per-feature in
   the order Te.5.B → Te.5.C → Te.5.D → Te.5.E (smallest first).
   Strict 3-stage fixed point validation between every commit
   per design doc Phase 5.
3. **v5.21.0 — Te.6 small ergonomic wins.** Per the existing
   roadmap, this is the closeout cluster. The deferred items
   from Te.5 (chained if-let, struct defaults, tuple structs,
   etc.) can land here as separate sub-features per the user's
   "size doesn't gate inclusion" feedback policy.

## Source line count delta

`mapanare/` Python files only:

| File | Before | After | Δ |
|---|---:|---:|---:|
| `mapanare.lark` | 502 | 522 | +20 |
| `ast_nodes.py` | 738 | 782 | +44 |
| `parser.py` | 2,283 | 2,355 | +72 |
| `semantic.py` | 2,624 | 2,684 | +60 |
| `lower.py` | 4,019 | 4,300 | +281 |

Total: **+477 lines** of Python implementation for four
ergonomic surface forms. The bootstrap mirror in v5.20.1
will be roughly the same size in `.mn`.
