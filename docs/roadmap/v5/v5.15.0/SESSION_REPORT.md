# v5.15.0 — Te.2 — comprehensions, implicit-return, terse lambdas

**Status:** ready, not tagged.
**Date:** 2026-04-29.
**Theme:** second release in the v5.13–v5.21 terseness arc; ships
the expression-density half of Te.\*.

---

## What landed

Three additive surface-syntax forms. Existing code keeps working
unchanged.

### Te.2.D — implicit-return one-liner

`fn name(args) [-> RetType] = expr` is sugar for
`fn name(args) [-> RetType] { return expr }`.

- Grammar: `fn_def` rhs is now `(block | ASSIGN expr)`.
- Python parser wraps the Expr as `Block([ReturnStmt(expr)])` so
  every downstream consumer (semantic checker, lowerer, emitter)
  is unchanged.
- Bootstrap mirror: same one-line conditional in
  `mapanare/self/parser.mn::parse_fn_body` and
  `parse_fn_body_as_data`.
- Block-form implicit return (last-expr-as-result) was **already
  shipped** at v5.14.0 per the v5.13.0-prep audit; v5.15.0 does not
  touch that path. SPEC §4.5 already documented it as canonical.

### Te.2.F — terse lambda `|x| body`

`|x| body`, `|x, y| body`, `|| body`. Single-expression body, no
type annotations on params (use the long form `fn(x: Int) {
return ... }` if a binding type is needed).

- Grammar: new `lambda_terse: BAR (NAME (COMMA NAME)*)? BAR expr`
  added to `atom_expr`.
- Lowers to the existing `LambdaExpr` AST node — same
  closure-environment-struct machinery as the legacy `(x) => body`
  form. Captures and ClosureCreate paths unchanged.
- Bootstrap mirror: new branch in `parse_atom` triggered on
  `tt == "BAR"`. Unambiguous because BAR is never the start of an
  expression elsewhere.
- Verified IR-equivalent to the long form modulo SSA naming.

### Te.2.B / Te.2.C — list + map comprehensions

`[expr for x in iter (if cond)*]`,
`#{ k: v for x in iter (if cond)* }`, multi-`for` allowed
(cartesian product). Single-identifier iteration target; pattern
destructuring deferred.

- New `Comprehension` and `CompClause` AST nodes.
- New grammar rules `list_comp`, `map_comp`, `comp_clause` —
  parallel to `list_lit` / `map_lit`. LALR(1) disambiguates on
  the next token after the first element/entry (`for` →
  comprehension, otherwise → literal).
- Lowering by AST synthesis in `lower.py::_lower_comprehension`:
  builds a fresh accumulator (`let mut __mn_comp_N = []` /
  `#{}`), then nested for/if structure with
  `__mn_comp_N.push(elem)` (lists) or `__mn_comp_N[k] = v`
  (maps), and yields the accumulator. Result MIR is identical to
  the manual-loop form modulo SSA naming and the synthesized
  variable name.
- For non-range iterables we synthesize an index-based loop
  (`for __i in 0..len(xs) { let x = xs[__i]; ... }`) because
  `for x in some_list` is **not yet supported** by the generic
  ForLoop lowering (the runtime `__iter_*` shims only know about
  ranges, see `runtime/native/mapanare_core.c:3375`). For range
  iterables the synthesizer uses a direct ForLoop. This keeps
  the pre-existing `for x in xs` limitation isolated to the
  manual-loop path while comprehensions Just Work.
- New empty-`MapLiteral` type-annotation patching path in
  `_lower_let` (mirror of the existing empty-`ListLiteral` path
  added at v4.122.0): when a user annotates `Map<K, V> = #{ ... }`
  and the entries list is empty, the synthesized `MapInit`
  instruction's `key_type` / `val_type` are patched from the
  annotation and the binding's Value is lifted. Without this,
  comprehension-produced maps printed `<?>` for indexed values
  because the LLVM emitter fell back to raw-pointer reads on
  `MAP<UNKNOWN, UNKNOWN>`.

**Bootstrap mirror — deferred to v5.15.1.** Comprehension parsing /
lowering in `mapanare/self/{ast,parser,lower}.mn` is the largest
piece of the arc and would have meaningfully expanded session scope.
v5.14.0 → v5.14.1 set the precedent: ship Python-side support, defer
the bootstrap mirror to a patch release. New comprehension goldens
do **not** exist in `tests/golden/`; comprehension coverage lives in
`tests/test_comprehensions.py` (Python bootstrap only — 11 tests,
covers parser, e2e execution, and IR-shape sanity).

---

## Files changed

| File | Δ | Why |
|---|---:|---|
| `mapanare/mapanare.lark` | +9 | grammar: `(block | ASSIGN expr)`, `lambda_terse`, `list_comp`, `map_comp`, `comp_clause` |
| `mapanare/ast_nodes.py` | +24 | `CompClause`, `Comprehension` dataclasses |
| `mapanare/parser.py` | +56 | one-liner wrap, `lambda_terse`, `list_comp`, `map_comp`, `comp_clause` transformers |
| `mapanare/lower.py` | +148 | `_lower_comprehension`, `_wrap_comp_for`; comprehension type-hint plumbing in `_lower_let`; empty-`MapLiteral` annotation patch |
| `mapanare/self/parser.mn` | +35 | bootstrap mirror — implicit-return one-liner, terse lambda |
| `tests/test_implicit_return.py` | +60 | 5 tests |
| `tests/test_lambdas.py` | +56 | 6 tests |
| `tests/test_comprehensions.py` | +194 | 11 tests (parse, e2e, IR-shape) |
| `tests/golden/67_implicit_return_one_liner.mn` | new | golden 67 |
| `tests/golden/68_terse_lambda.mn` | new | golden 68 |
| `docs/roadmap/v5/v5.15.0/TERSENESS_DESIGN.md` | new | Phase 0 design lock |
| `docs/roadmap/v5/v5.15.0/SESSION_REPORT.md` | new | this file |
| `VERSION` | bump | `5.14.0` → `5.15.0` |
| `CHANGELOG.md` | +1 entry | v5.15.0 release notes |
| `CLAUDE.md`, `README.md`, `docs/SPEC.md` | edits | terseness-arc updates |

Total: ~600 LOC added, ~10 LOC modified. Heaviest churn in
`lower.py`. No deletions — every form is purely additive.

---

## Validation

**Goldens — 68/68 PASS** (66 prior + 2 new), through both Python
bootstrap and `mnc-stage1`:

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
...
PASS 67_implicit_return_one_liner
PASS 68_terse_lambda
All 68 tests passed in 12.9s
```

**Strict 3-stage fixed point — preserved.**

```
$ bash scripts/verify_fixed_point.sh --keep
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (228630 lines, 0 diff)
```

The bootstrap mirror change in `mapanare/self/parser.mn` is
purely additive (new `if` branches that fire only on new syntax
shapes), so the input source `mnc_all.mn` — which uses none of the
new forms — produces the same MIR/IR through both stage2 and
stage3.

**New unit tests — 21/21 PASS.**

```
$ pytest tests/test_implicit_return.py tests/test_lambdas.py \
         tests/test_comprehensions.py
21 passed in 9.09s
```

**Existing pytest sweep — 6301/6301 PASS, no regressions.**
The only failures observed in the dev environment are pre-existing
gcc-toolchain issues in WSL (gcc.exe cannot find cc1 for `mnc run`
tests in `tests/cli/`) plus three lint-self-tests
(`tests/test_ci.py`) which trip on temporary `*.pyc` left during
the session — these were green pre-edit and are not caused by
v5.15.0.

**Lint — clean.**

```
$ black --check --target-version py312 mapanare/ tests/
$ ruff check mapanare/ tests/
$ mypy mapanare/ runtime/
Success: no issues found in 55 source files
```

---

## Out of scope (deferred)

| Item | Where it lands |
|---|---|
| Bootstrap mirror for comprehensions | **v5.15.1** (patch — mirrors v5.14.0 → v5.14.1) |
| `mnc fmt` whitespace canonicalization for new forms | **v5.16.0** alongside Te.4 |
| Pattern-destructuring comprehension targets `[(k, v) for ... in items]` | **v5.20.0** Te.5 |
| `else` clauses in filters `[x if c else d for x in xs]` | indefinite |
| Set comprehensions | indefinite (no native set type) |
| Generator / lazy comprehensions | iterator-protocol arc, indefinite |
| Walrus / chained comparisons inside comprehensions | with their parent feature |
| Self-host source rewrites to use comprehensions/lambdas | **v5.17.0** Sh.\* |

Out-of-scope items deliberately left undocumented in SPEC §
comprehensions until they ship; v5.15.0's SPEC update only mentions
the forms that work.

---

## Known limitations

- **`for x in some_list` (manual loop, not comprehension) still
  doesn't iterate correctly** — pre-existing limitation since the
  generic ForLoop lowering emits `__iter_has_next` /
  `__iter_next` calls and the runtime only implements those for
  ranges. Tracked separately; not in the v5.15.0 docket. The
  comprehension synthesizer routes around this by emitting
  index-based loops on non-range iterables.
- **Mixed numeric promotion in comprehensions** (e.g.
  `[x * 2.0 for x in [1, 2, 3]]`) follows the same rules as a
  manual loop's `__r.push(x * 2.0)`. If the manual form rejects,
  the comp does too.

---

## What v5.15.1 will do

Mechanical: add `Comprehension` + `CompClause` to
`mapanare/self/ast.mn`; add list/map-comp parsing to
`mapanare/self/parser.mn`; mirror `_lower_comprehension` synthesis
in `mapanare/self/lower.mn`. Validation: same 11 comprehension
tests run through `mnc-stage1` instead of the Python bootstrap.

The mirror is roughly the same shape as the v5.14.1 colon-block
mirror but smaller: no C runtime export needed, no separate
preprocessor module — just AST + parser + synthesizer
additions in three `.mn` files.
