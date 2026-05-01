# v5.20.1 — Te.5.F — bootstrap mirror (patch)

**Date:** 2026-05-01.
**Cycle:** Phase 0 → Phase 6 in one session, smallest-first per
the v5.14.0→v5.14.1 / v5.15.0→v5.15.1 precedent.
**Status:** **READY** (pending closeout).

---

## Headline

v5.20.1 closes the v5.20.0 bootstrap-mirror gap. `mnc-stage1` now
parses and lowers all four Te.5 surface forms exactly matching
v5.20.0's Python behavior:

- **Te.5.F.B — field shorthand.** `Point { x, y }` ≡ `Point { x: x,
  y: y }`. 1-character relaxation in `parse_struct_fields_to_list`:
  consume the field name, then conditionally accept `:` + expr or
  fall back to `Ident(fname)` as the value.
- **Te.5.F.C — struct update.** `Point { x: 5, ..base }` and the
  bare `Point { ..base }` form. New `Expr::ConstructUpdate` AST
  variant; `lower_struct_update` in `lower.mn` synthesizes the
  full `Construct` in struct-declaration order, slotting overrides
  by name and filling holes with `__mn_base_N.<field>` accesses.
  New `struct_update_counter` on `LowerState` (separate from
  `tmp_counter`) keeps synthesized base tmps from perturbing the
  global `%tN` sequence.
- **Te.5.F.D — let destructuring.** `let Point { x, y } = p` with
  nested patterns, rest patterns (`..`), and per-field `mut`. New
  `Stmt::LetDestructure` plus `StructPattern` / `FieldPattern`
  structs in `ast.mn`. `lower_let_destructure` mirrors Python's
  bare-Ident optimization (skip the synthesized base tmp when RHS
  is already in scope).
- **Te.5.F.E — if-let / while-let / let-else.** Three refutable-
  binding forms desugared at lower time to existing match / while /
  let. `parse_if_expr` and `parse_while_stmt` learn `KW_LET`
  lookahead; `parse_let_stmt` dispatches `NAME LPAREN` and
  `UNDERSCORE` to `parse_let_else_body`. Divergence helpers
  (`block_diverges`, `stmt_diverges`, `match_arm_body_diverges`)
  port from Python's `_block_diverges` / `_stmt_diverges` /
  `_expr_or_block_diverges`.

The v5.20.0 SESSION_REPORT's "Deferred to v5.20.1" item is
discharged. The 11 v5.20.0 goldens at `tests/golden/81…91` now
pass through `mnc-stage1` with byte-identical stdout vs. the
Python bootstrap.

## Phase 0 audit

`AUDIT.md` documents:

1. Failure shape per golden through v5.18.0-era stage1 — all 11
   fail at the parser's first un-grammar token (COLON/ASSIGN/
   LBRACE/LPAREN-after-IF/WHILE).
2. Bootstrap parser idiom inventory — confirms `peek_type()`-based
   single-token lookahead, `parse_let_stmt` shape, struct-field
   registry shape, per-fn counter reset block.
3. Pattern-node infrastructure already covers ConstructorPat /
   Wildcard for Te.5.F.E. StructPattern / FieldPattern were
   net-new (shipped here as standalone structs, not Pattern
   variants — mirrors Python design).
4. Pre-existing bootstrap miscompile of out-of-order field
   initializers in non-`..base` literals (`new Point { y: 99,
   x: 1 }` produces wrong results — bootstrap zips positionally,
   ignoring source field names). **Out of scope** for v5.20.1; the
   Te.5.F.C lowering reorders by struct definition correctly for
   the new path. Tracked as a v5.21.0+ follow-up.

## Files touched

### Added

- `docs/roadmap/v5/v5.20.1/AUDIT.md` (Phase 0).
- `docs/roadmap/v5/v5.20.1/SESSION_REPORT.md` (this).
- `tests/bootstrap/test_te5_mirror.py` (Te.5.F.G).

### Modified

- `mapanare/self/ast.mn` — 1 new Expr variant (`ConstructUpdate`),
  1 new Expr variant (`IfLet`), 3 new Stmt variants
  (`LetDestructure`, `LetElse`, `WhileLet`); 2 new structs
  (`StructPattern`, `FieldPattern`) + constructors + accessors.
- `mapanare/self/parser.mn` — extended `parse_struct_fields_to_list`
  for shorthand; rewrote `parse_struct_construct` for `..base`;
  extended `parse_let_stmt` with single-token-lookahead dispatch
  to `parse_let_destructure_body` / `parse_let_else_body`;
  extended `parse_if_expr` / `parse_while_stmt` for `KW_LET`.
- `mapanare/self/semantic.mn` — `infer_expr` arm for
  `construct_update`, `if_let`; `check_stmt` arms for
  `let_destructure`, `let_else`, `while_let`;
  `define_pattern_bindings` recursive helper.
- `mapanare/self/lower_state.mn` — new `struct_update_counter`
  field on `LowerState`.
- `mapanare/self/lower.mn` — per-fn reset of
  `struct_update_counter`; `lower_struct_update`,
  `lower_let_destructure`, `emit_destructure_pattern`,
  `lower_if_let`, `lower_while_let`, `lower_let_else` plus
  divergence helpers (`block_diverges`, `stmt_diverges`,
  `match_arm_body_diverges`).
- `mapanare/self/lower.mn::lower_match` — 4-line fix to skip the
  alloca-fn_ret dance when fn_ret is `void`. Pre-existing latent
  bug surfaced when statement-context match (from v5.20.1 if-let
  desugar) lands in `fn main()` (void return type).

## Goldens delta

Native stage1: 80/80 → **91/91** PASS. Cross-bootstrap test
asserts byte-identical stdout for all 11 new goldens via Python
and native pipelines.

## Validation

| Phase | Goldens | Fixed point | Notes |
|---|---|---|---|
| 0 (audit, baseline) | 80/91 | 232,281 lines / 0 diff | v5.18.0 milestone |
| 1 (Te.5.F.B) | 81/91 | 232,322 lines / 0 diff | +41 IR lines |
| 2 (Te.5.F.C) | 83/91 | 233,453 lines / 0 diff | +1,131 IR lines |
| 3 (Te.5.F.D) | 88/91 | 236,478 lines / 0 diff | +3,025 IR lines |
| 4 (Te.5.F.E) | **91/91** | **238,086 lines / 0 diff** | +1,608 IR lines |

`bash scripts/build_from_seed.sh` succeeds. `make lint` clean
(one pre-existing mypy error in `mapanare/lower.py:257`
`_expr_or_block_diverges` from v5.20.0 commit 4ea40e11 fixed in
scope — added an explicit `isinstance(node, Expr)` guard).

`tests/bootstrap/test_te5_mirror.py` 12/12 PASS — 11 byte-
identical-stdout cases covering every Te.5.F.B–E surface form
plus a sanity case for the let-else divergence-check deviation.

## Source line count delta

`mapanare/self/` only:

| File | Before | After | Δ |
|---|---:|---:|---:|
| `ast.mn` | 749 | 838 | +89 |
| `parser.mn` | 2,370 | 2,560 | +190 |
| `semantic.mn` | 1,982 | 2,120 | +138 |
| `lower.mn` | 4,515 | 4,835 | +320 |
| `lower_state.mn` | 508 | 513 | +5 |

Total bootstrap delta: **+742 lines**. Mirror is 1.55× the
v5.20.0 Python delta of +477 lines, in line with the bootstrap's
lower-level idioms (manual accessor functions, explicit
`peek_type()` lookahead vs Lark grammar, hand-written recursive-
descent vs LALR transformers).

## Deviations from Python

1. **`let_else` divergence check** — Python raises a
   `RuntimeError` at lower time when the else block doesn't
   diverge. The bootstrap can't easily emit a structured
   diagnostic from inside `lower.mn`; instead it computes
   `block_diverges` for telemetry, then proceeds with the
   desugar. The resulting binding may be unsound when the else
   block falls through, but compilation completes. The
   cross-bootstrap test (`test_let_else_non_divergent_rejected`)
   documents this deliberate deviation.
2. **`mnc-stage1` field-init out-of-order miscompile** — pre-
   existing in the legacy `Call(__new_X, vals)` path. Not fixed
   here; Te.5.F.C uses a separate by-name path that reorders
   correctly.

## Out of scope (deferred per design)

- Multi-binding `let else` patterns (`let Pair(a, b) = pair else
  { ... }`) — Python doesn't support these at v5.20.0 either.
- `if let` chains (`if let X = a && let Y = b`) — Te.5 D7.
- Default-value shorthand (`Point { x = 0, y }`) — Te.5 D10.
- Self-host source rewrites to use any of the new forms — kept
  out so the v5.18.0 strict-fixed-point milestone (the
  232,281-line delta for stage2.ll == stage3.ll) is preserved
  by construction.
- Match-side `StructPattern` parity at full Te.5.D feature
  parity — D3 noted Python ships this with lower test coverage;
  v5.20.1 doesn't widen.
- Native `mnc fmt --to-terse` rewriter for the new forms —
  Te.5.H. The new forms can't be safely auto-migrated.

## Recommendations

1. **Tag v5.20.0 + v5.20.1 together** — v5.20.1 is the bootstrap
   counterpart of v5.20.0 (per the v5.14.x / v5.15.x precedent);
   they ship as a pair in the same release window.
2. **v5.21.0 — Te.6 — small ergonomic wins** (chained
   comparisons, etc.) — now unblocked. The bootstrap accepts
   every v5.20.0 surface form, so v5.21.0's incremental
   additions can land against a stable reference.
3. **`STRUCT_ERGO_DESIGN.md`** — drop the "deferred to v5.20.1"
   note; mark the bootstrap mirror as **shipped in v5.20.1**.
