# v5.15.1 — Cb.* — bootstrap comprehension mirror (patch)

**Status:** ready, not tagged.
**Date:** 2026-04-29.
**Theme:** closes the v5.15.0 deferred item — `mnc-stage1` learns to
parse and lower list/map comprehensions exactly the way the Python
bootstrap does. Same shape as v5.14.0 → v5.14.1, but smaller (no C
runtime export, no separate preprocessor module).

---

## What landed

`mnc-stage1` now accepts every comprehension surface the Python
bootstrap accepts at v5.15.0 — list, map, multi-`for`, multi-`if`,
range and non-range iterables — and produces stdout-identical
results to the Python compiler on every test in
`tests/test_comprehensions.py`.

### Cb.1 — AST nodes (`mapanare/self/ast.mn`)

New `CompClause` struct (`target: String, iter: Expr,
conditions: List<Expr>`) and new
`Comprehension(String, Option<Expr>, Option<Expr>, Option<Expr>,
List<CompClause>)` variant on `Expr` — kind, element (list comp),
key + value (map comp), clauses. `expr_kind` extended with
`comprehension`; accessor functions follow the existing pattern
(`expr_comp_kind`, `expr_comp_element`, `expr_comp_key`,
`expr_comp_value`, `expr_comp_clauses`); `new_comp_clause`
constructor.

### Cb.2/Cb.3 — Parser surface (`mapanare/self/parser.mn`)

Single-token lookahead in `parse_list_lit` / `parse_map_lit`. After
the first element (lists) or `key: value` pair (maps), peek the
next token: `KW_FOR` → dispatch to comprehension; otherwise fall
through to existing literal logic. New `parse_comp_clause`
(consumes `for NAME in expr (if expr)*`), `parse_list_comp_tail`
(consumes `comp_clause+ RBRACKET`), `parse_map_comp_tail` (consumes
`comp_clause+ RBRACE`). Both build a single `Expr::Comprehension`
node carrying the kind tag and the parsed first-expression(s).

### Cb.4 — Lowering (`mapanare/self/lower.mn`)

`lower_comprehension` mirrors
`mapanare/lower.py::_lower_comprehension` byte-for-byte:

1. Allocate fresh accumulator name `__mn_comp_N` from
   `tmp_counter`.
2. Build init expression — `Expr::ListLit([])` for list comp,
   `Expr::MapLit([])` for map comp — and the per-iteration write
   expression: `Expr::MethodCall(Ident, "push", [element])` for
   list, `Expr::Assign(Index(Ident, key), "=", value)` for map
   (mirrors Python's `_AssignExpr`/`IndexExpr` synthesis;
   `IndexSet` MIR op handles both list and map writes).
3. Synthesize and lower a `Stmt::Let("__mn_comp_N", true, hint,
   init)` — the type hint comes from `state.comp_type_hint`
   (set up by `lower_let` before recursing; cleared on entry to
   `lower_comprehension` so nested comprehensions don't inherit).
4. Build the loop body innermost-out, applying filters then
   for-clauses both in reverse source order.
5. Lower each statement in the resulting outer Block.
6. Return the accumulator's loaded value via
   `lower_identifier(state, "__mn_comp_N")`.

`wrap_comp_for` mirrors Python's `_wrap_comp_for`. Range
iterables (`expr_kind == "range"`) emit a direct `Stmt::For`.
Non-range iterables emit the index-based pattern: `let __src = iter;
for __i in 0..len(__src) { let target = __src[__i]; ... }`. This
routes around the pre-existing `for x in some_list` lowering gap
(the runtime `__iter_*` shims only know ranges).

### Cb.5 — Type-hint plumbing

New `comp_type_hint: Option<TypeExpr>` field on `LowerState`
(`mapanare/self/lower_state.mn`). `lower_let` sets it before
lowering a comprehension RHS:

```mn
if expr_kind(value) == "comprehension" {
    match type_ann {
        Some(_) => { st.comp_type_hint = type_ann },
        _ => { st.comp_type_hint = none }
    }
} else {
    st.comp_type_hint = none
}
```

`lower_comprehension` reads + clears it on entry. The synthesized
inner Let's `type_annotation` flows into the existing
`lower_let_list_hint` path for list comp (typed alloca via
`lower_list_typed_into`). For map comp, the helper
`patch_last_mapinit_types` post-hoc rewrites the most recent
`MapInit` instruction's `key_type` / `val_type` from the
annotation's `Map<K, V>` args (mirror of Python `_lower_let`
v5.15.0 Te.2.C empty-`MapLit` patch). Without the patch,
indexing the comprehension's result would see `UNKNOWN` value
type and the LLVM emitter would print `<?>`.

### Pre-existing emitter gap fixed in scope

Phase 3 surfaced one pre-existing bootstrap gap that blocked
`test_map_comp_doubles`: `emit_builtin_len` had no `TK_MAP()`
branch, so `len(map)` fell through to the list path and emitted

```
%t.lp = alloca {ptr, i64, i64, i64, i64}
store {ptr, i64, i64, i64, i64} %map_val, ptr %t.lp  ; type mismatch
```

— rejected by `llvm-as`. Fixed by extracting field 0 of the
`{ptr, i64}` map value (the runtime `MnMap*`) and passing it
directly to `__mn_map_len`. This is the *first* call site for
`__mn_map_len` from the bootstrap emitter; the runtime symbol was
already declared.

### Tests

- **New** `tests/golden/{69_list_comp,70_list_comp_filter,71_map_comp}.mn`
  — three goldens promoted from v5.15.0's `test_comprehensions.py`.
  Goldens **68/68 → 71/71** through `mnc-stage1`.
- **New** `tests/bootstrap/test_comprehension_mirror.py` — 10
  cross-bootstrap cases mirroring every test in
  `tests/test_comprehensions.py`. 4 parser-only (asserts
  `mnc-stage1 emit-llvm` succeeds), 5 e2e (compile → llc → clang →
  run, asserts stdout matches Python), 1 IR-shape sanity. **10/10
  PASS.**

### Out of scope (preserved deferrals from v5.15.0)

- Pattern-destructuring comprehension targets — v5.20.0 Te.5.
- `else` clauses in filters — indefinite.
- Set comprehensions (no native set type) — indefinite.
- Generator / lazy comprehensions — iterator-protocol arc, indefinite.
- Walrus / chained comparisons inside comprehensions — with their
  parent feature.
- Self-host source rewrites to use comprehensions — v5.17.0 Sh.\*.
  v5.15.1 only adds parsing/lowering capability; `mapanare/self/*.mn`
  source remains comprehension-free.

---

## Files changed

| File | Δ | Why |
|---|---:|---|
| `mapanare/self/ast.mn` | +35 | `CompClause` struct, `Comprehension` variant, `expr_kind` case, accessors, constructor |
| `mapanare/self/parser.mn` | +75 | `parse_comp_clause`, `parse_list_comp_tail`, `parse_map_comp_tail`, lookahead in `parse_list_lit` / `parse_map_lit` |
| `mapanare/self/lower.mn` | +175 | `lower_comprehension`, `wrap_comp_for`, `patch_last_mapinit_types`; comp_type_hint setup in `lower_let`; `comprehension` dispatch in `lower_expr` |
| `mapanare/self/lower_state.mn` | +5 | `comp_type_hint: Option<TypeExpr>` field on `LowerState` + init |
| `mapanare/self/emit_llvm.mn` | +12 | `len(map)` dispatch via `extractvalue` + `__mn_map_len` |
| `tests/bootstrap/test_comprehension_mirror.py` | +200 | 10 cross-bootstrap cases (4 parse + 5 e2e + 1 IR-shape) |
| `tests/golden/69_list_comp.mn` | new | golden 69 |
| `tests/golden/70_list_comp_filter.mn` | new | golden 70 |
| `tests/golden/71_map_comp.mn` | new | golden 71 |
| `docs/roadmap/v5/v5.15.1/AUDIT.md` | new | Phase 0 audit + prerequisite check |
| `docs/roadmap/v5/v5.15.1/SESSION_REPORT.md` | new | this file |
| `VERSION` | bump | `5.15.0` → `5.15.1` |
| `CHANGELOG.md` | +1 entry | v5.15.1 release notes |
| `CLAUDE.md` | edits | release-notes update |

Total: ~500 LOC added (mostly mirroring the Python lowerer
line-for-line). No deletions.

---

## Validation

**Goldens — 71/71 PASS** through `mnc-stage1`:

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
...
PASS 69_list_comp 12L->287L 21bb 325stk 7ms (1 fns) stg1:1fns 220ms
PASS 70_list_comp_filter 11L->303L 24bb 334stk 7ms (1 fns) stg1:1fns 200ms
PASS 71_map_comp 12L->156L 11bb 148stk 7ms (1 fns) stg1:1fns 178ms
All 71 tests passed in 14.0s
```

**Strict 3-stage fixed point — preserved** (the v5.9.0 milestone):

```
$ bash scripts/verify_fixed_point.sh
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (228630 lines, 0 diff)
```

The new `mapanare/self/{ast,parser,lower,lower_state,emit_llvm}.mn`
code is purely additive (new branches/fields/dispatch keys); the
bootstrap input source `mnc_all.mn` uses no comprehensions, so
neither stage2 nor stage3 IR is affected. `len(map)` doesn't
appear in `mnc_all.mn` either, so the `emit_builtin_len` map
branch doesn't fire during the bootstrap loop.

**Cross-bootstrap parity — 10/10 PASS:**

```
$ python3 -m pytest tests/test_comprehensions.py \
                    tests/bootstrap/test_comprehension_mirror.py
============================== 20 passed in 11.21s ==============================
```

The 4 parser-only cases assert `mnc-stage1 emit-llvm` succeeds.
The 5 e2e cases compile → llc → clang → run and assert stdout
matches Python's expected output exactly. The 1 IR-shape sanity
case asserts the comprehension lowers to `__mn_list_push` inside
`for_header`/`for_body` blocks — same shape as a hand-written
loop.

**Lint — clean:**

```
$ make lint
ruff check . && black --check . && mypy mapanare/ runtime/
All checks passed!
389 files would be left unchanged.
Success: no issues found in 55 source files
```

---

## What v5.15.1 unblocks

- **v5.16.0 (Te.4 — self-host string-interp parity)** — the
  bootstrap now accepts every Python-bootstrap-acceptable surface
  form, so v5.16.0's parity work has a stable reference compiler
  to verify against.
- **v5.17.0 (Sh.\* — mechanical `mnc fmt --to-terse` rewrite of
  `mapanare/self/`)** — closes the parity-gap docket entry that
  "comprehensions work in `mapanare` but not in `mnc`".
  Comprehension introduction in `self/` is still a separate hand
  pass; v5.17.0 is brace-style → colon-style only.

## Footprint per the original PLAN

| Item | Estimate | Actual |
|---|---:|---:|
| Cb.1 (AST) | 30m–1h | ~30 min, +35 LOC |
| Cb.2/Cb.3 (parser) | 1.5–2.5h | ~1h, +75 LOC |
| Cb.4 (lower_comprehension) | 2–3h | ~1.5h, +130 LOC |
| Cb.5 (type-hint plumbing) | 30m–1h | ~30 min, +25 LOC |
| Cb.6 (cross-bootstrap test) | 1h | ~30 min, +200 LOC |
| Cb.7 (3 goldens) | 30m | ~10 min |
| Pre-existing gap fix (`len(map)`) | unscoped | ~15 min, +12 LOC |
| Phase 0 + Phase 6 | — | ~1h |

Total session: ~5h, well within the PLAN's 5–8h estimate.
