# v5.20.1 Pre-Implementation Audit (Phase 0)

**Date:** 2026-05-01.
**Stage1 baseline:** v5.18.0 source @ commit 2de1242 (`mapanare/self/mnc-stage1`, 6,864,056 bytes, mtime 2026-04-30).
**Goldens baseline:** 80 passed, 11 failed (`tests/golden/81…91`) — matches `v5.20.0/SESSION_REPORT.md` § "Goldens delta".
**Fixed-point baseline:** stage2.ll == stage3.ll @ **232,281 lines / 0-line diff** (the v5.18.0 milestone).

---

## 1. Failure shape per golden through `mnc-stage1`

Each new v5.20.0 golden fails at the first token the v5.18.0 grammar can't accept.

| # | File | First-error stage | Token / shape |
|---|---|---|---|
| 81 | `81_struct_shorthand.mn` | parser | `expected COLON but got COMMA` — shorthand `Point { x, y }` hits `parse_struct_fields_to_list` after consuming NAME (`x`); the next token `,` is rejected because the parser unconditionally `expect`s `COLON`. |
| 82 | `82_struct_update.mn` | parser | `expected COLON but got NAME` — `..p1` is lexed as `RANGE NAME`; after the override `x: 99 COMMA`, the parser sees `RANGE` then `NAME` (`p1`), expects another field name + `COLON`. |
| 83 | `83_struct_update_partial.mn` | parser | Same RANGE/NAME confusion as 82. |
| 84 | `84_let_destructure.mn` | parser | `expected ASSIGN but got LBRACE` — `parse_let_stmt` consumes `let Point` as the binding name and then expects `=`. |
| 85 | `85_let_destructure_nested.mn` | parser | Same as 84. |
| 86 | `86_let_destructure_rest.mn` | parser | Same as 84. |
| 87 | `87_let_destructure_mut.mn` | parser | Same as 84 (KW_MUT is consumed first, then `Point` becomes the binding name). |
| 88 | `88_if_let.mn` | parser | `expected LBRACE but got NAME` — `parse_if_expr` reads `let` as the start of the condition expression; `let` lacks an expr-position lexer hook so it tokenises as `KW_LET`, parsed as an identifier; next token `Some` is unexpected. |
| 89 | `89_if_let_else.mn` | parser | Same as 88. |
| 90 | `90_while_let.mn` | parser | Same as 88 (parse_while_stmt). |
| 91 | `91_let_else.mn` | parser | `expected ASSIGN but got LPAREN` — `parse_let_stmt` consumes `let Some` as the binding name and then expects `=`; sees `(`. |

All failures are in the parser; semantic and lower paths are not exercised today for the four new forms.

---

## 2. Bootstrap parser idiom inventory

| Concern | Finding |
|---|---|
| Single-token lookahead | The bootstrap parser uses `peek_type(tokens, p)` / `peek_value(tokens, p)` with a position-based offset. Used pervasively (`parser.mn:1248`, etc.). All Te.5.F dispatch decisions can be expressed as `if peek_type(...)`. |
| `parse_let_stmt` shape | `parser.mn:1265-1286` — reads `KW_LET KW_MUT? NAME COLON? type_expr? ASSIGN expr`. The Te.5.F.D / Te.5.F.E dispatch points sit immediately after the optional `KW_MUT`. Specifically: after `let mut is_mut: Bool` is set, before `let name: String = peek_value(tokens, p)`, we will switch on `peek_type(tokens, p)` for `NAME LBRACE` (destructure) and on subsequent context for the let-else form. |
| `parse_if_expr` / `parse_while_stmt` shape | `parser.mn:1868` and `parser.mn:1319`. Both immediately call `parse_expr` for the condition. Te.5.F.E dispatch: at the top of each, peek for `KW_LET` and dispatch to a new `parse_if_let_expr` / `parse_while_let_stmt`. |
| `parse_struct_fields_to_list` | `parser.mn:1715-1729`. Tracks values **positionally only** — discards field names. Te.5.F.B trivially adds value-omitted shorthand by changing the unconditional `expect(COLON)` to a conditional. **However**, the positional-only path is what creates the pre-existing bootstrap miscompile of out-of-order initializers (see § 6 below) — Te.5.F.C requires switching to a name-aware parse. |
| `parse_pattern` | `parser.mn:1947-1999`. Already covers Wildcard, IdentPat, LiteralPat, ConstructorPat (`Some(x)`, `Ok(v)`), OrPat. Te.5.F.E reuses this verbatim for if-let / while-let / let-else patterns. No `StructPattern` parsing required for v5.20.1 — let-destructuring uses a custom `parse_let_destructure_pat` helper because the full pattern grammar is overkill there. |

---

## 3. `_struct_fields` / equivalent in bootstrap

`mapanare/self/lower_state.mn:11-48` defines `LowerState.struct_fields: List<StructFieldInfo>`. Lookup helpers at `lower_state.mn:192-219`:

- `find_struct_fields(name) -> Option<List<String>>`
- `is_struct_name(name) -> Bool`
- `get_struct_field_names(name) -> List<String>`

The Python field is named `_struct_fields` and stores a `dict[str, list[str]]`. The bootstrap stores a list of `StructFieldInfo` records and scans linearly. Both shapes are equivalent for our purposes; the bootstrap helpers already give us the full ordered field-name list keyed by struct name.

---

## 4. Per-fn counter reset block

`mapanare/self/lower.mn:460-473` is the per-fn entry block that resets `tmp_counter`, `block_counter`, `vars`, and `fn_blocks`. `_struct_update_counter` will be added to `LowerState` and reset alongside `tmp_counter` in this block (matching Python `lower.py:984-987`).

---

## 5. Pattern node infrastructure

Existing in `ast.mn:139-144`:

```
enum Pattern:
    Wildcard
    IdentPat(String)
    LiteralPat(Expr)
    ConstructorPat(String, List<Pattern>)
    OrPat(List<Pattern>)
```

Mirror of Python. Sufficient for Te.5.F.E (if-let / while-let / let-else use ConstructorPat / Wildcard).

For Te.5.F.D, the destructure pattern is a **per-feature struct** (`StructPattern`, `FieldPattern`) added separately, **not** a Pattern variant — same as Python's `StructPattern` / `FieldPattern` dataclasses living outside the `Pattern` union. This keeps the existing `parse_pattern` machinery untouched.

---

## 6. Pre-existing bootstrap defect surfaced (out-of-order field init)

While auditing path 1 (`Call(Ident("__new_X"), [vals])`), reproduced this failing test:

```mn
struct Point: x: Int; y: Int
fn main():
    let p: Point = new Point { y: 99, x: 1 }
    print(str(p.x))   // expected 1
    print(str(p.y))   // expected 99
```

| Compiler | stdout |
|---|---|
| `python3 -m mapanare emit-llvm` (Python bootstrap) | `1` then `99` — correct |
| `mnc-stage1` (bootstrap) | `99` then `1` — **incorrect (silent miscompile)** |

`parse_struct_fields_to_list` and downstream `lower_call_by_name`'s `__new_` branch zip values with `field_names` **positionally**, so out-of-order source field initialization writes the wrong slots.

**Impact on v5.20.1:** Golden 83 (`new Box { z: 30, x: 10, ..b1 }`) initializes fields out of declaration order. The new `Te.5.F.C` lowering MUST reorder by struct definition before emitting the positional `__new_` Call. Goldens 81/82 happen to use declaration order, so they would not trigger this bug independently.

**Scope decision:** the Te.5.F.C lowerer reorders by struct-definition order from the field-name registry. This fixes the new feature path correctly and (as a free side-effect) any future `new T { ... }` literal that adopts named-field reordering through the new code path. The pre-existing bug for the legacy `Call(__new_X, ...)` path created by `parse_struct_construct` for non-`..base` literals is **left untouched** — it has been latent since v3.x and fixing it requires changing the parser to route every struct literal through the named path, which would risk breaking the strict 3-stage fixed point. Out of scope for v5.20.1; tracked as a follow-up note in `SESSION_REPORT.md`.

---

## 7. Acceptance criteria

After Te.5.F.G:

- [ ] All 11 v5.20.0 goldens (`tests/golden/81…91`) pass through `mnc-stage1`.
- [ ] Existing 80 goldens still pass.
- [ ] `bash scripts/verify_fixed_point.sh --keep` reports stage2.ll == stage3.ll (0-line diff). Line count may grow vs. 232,281 by the size of the new bootstrap `.mn` code.
- [ ] `tests/bootstrap/test_te5_mirror.py` green — byte-identical stdout from Python bootstrap and `mnc-stage1` for all 11 goldens.
- [ ] `bash scripts/build_from_seed.sh` succeeds.
- [ ] `make lint` clean.
