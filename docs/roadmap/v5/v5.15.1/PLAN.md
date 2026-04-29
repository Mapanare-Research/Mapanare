# v5.15.1 — bootstrap comprehension mirror (patch)

**Status:** PLANNING
**Breaking:** No. Pure additive: `mnc-stage1` learns to parse and
lower list/map comprehensions, exactly matching what the Python
bootstrap already does as of v5.15.0. Code that uses no
comprehensions continues to compile unchanged.
**Prerequisite:** v5.15.0 shipped (Python parser/lowerer for list
+ map comprehensions, `Comprehension` / `CompClause` AST nodes,
`tests/test_comprehensions.py` 11 cases green through Python).
**Estimated effort:** 5–8h, one or two sessions. Smaller than
v5.14.1 — no C runtime export, no separate preprocessor module,
no semantic.mn changes (synthesis lowers to existing constructs).

---

## Why this exists

v5.15.0 shipped list and map comprehensions in the Python bootstrap.
By explicit decision (PLAN.md and SESSION_REPORT "Out of scope"),
the **bootstrap mirror was deferred**: `mnc-stage1` rejects
comprehension syntax with a parse error today. Users who write
comprehensions must compile through the Python bootstrap; if they
need native speed via `mnc run` / `mnc build`, they must rewrite
the comprehension as a manual loop.

That gap is acceptable in v5.15.0 because:

1. The Python bootstrap is the canonical reference compiler in dev
   workflows. v5.15.0 delivers comprehensions to `mapanare`
   (`mapanare run`, `mapanare emit-llvm`) on day one.
2. Comprehension syntax in `mapanare/self/*.mn` itself only matters
   at v5.17.0 (Sh.\* — mechanical rewrite of self/ via
   `mnc fmt --to-terse`), and the rewriter does not introduce
   comprehensions; that's a hand-written cleanup pass for later.
3. Touching `mapanare/self/{ast,parser,lower}.mn` is the only way
   to break the strict 3-stage fixed point; v5.15.0 deliberately
   avoided that risk.

The gap stops being acceptable when **v5.16.0 (Te.4 — self-host
string-interp parity) wants to be the validation buffer for
v5.17.0**. For v5.16.0 to do its job, the bootstrap must already
accept every Python-bootstrap-acceptable surface form, so that
v5.16.0's parity work has a stable reference compiler to verify
against. Ship v5.15.1 between v5.15.0 and v5.16.0; "soon after
v5.15.0" is the most honest place because the lowering design is
fresh.

---

## Goal

1. `mnc-stage1` parses and lowers list comprehensions (`[expr for
   x in iter (if cond)*]`) and map comprehensions (`#{ k: v for
   ... }`), with multi-`for` cartesian-product clauses, exactly
   matching v5.15.0's Python behavior.
2. The bootstrap implementation **mirrors** the Python lowering
   strategy — AST synthesis to fresh accumulator + nested for/if +
   push (lists) or `m[k] = v` (maps), with index-based loops on
   non-range iterables. Same algorithm, same identifier-naming
   convention (`__mn_comp_N`), same range-vs-non-range detection.
3. `tests/test_comprehensions.py` (the 11 cases v5.15.0 added,
   currently Python-only) re-runs through `mnc-stage1` and passes.
4. **Strict 3-stage fixed point preserved.** The new `.mn` lowering
   code, when compiled into stage1 and used to build stage2, must
   produce IR byte-identical to stage3 — same as every release
   since v5.9.0.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cb.1** | HIGH | Add `Comprehension(String, Option<Expr>, Option<Expr>, Option<Expr>, List<CompClause>)` to `Expr` enum and `CompClause` struct to `mapanare/self/ast.mn`. Mirror Python `ast_nodes.py` shape. Add `expr_kind` and any accessors needed by lower. | 30m–1h |
| **Cb.2** | HIGH | Add `parse_list_comp` and `parse_map_comp` to `mapanare/self/parser.mn`. The disambiguator from `list_lit` / `map_lit` is the next token after the first element/entry: `KW_FOR` → comp, `COMMA`/`RBRACKET`/`RBRACE` → literal. Single token of lookahead. | 1–2h |
| **Cb.3** | HIGH | Wire the new branches into `parse_list_lit` and `parse_map_lit` (lookahead + dispatch). Both call sites already exist; add the lookahead at entry. | 30m |
| **Cb.4** | HIGH | Implement `lower_comprehension` in `mapanare/self/lower.mn`. Mirror `mapanare/lower.py::_lower_comprehension` line-by-line. Includes the helper for `_wrap_comp_for` (range vs non-range index-based synthesis). | 2–3h |
| **Cb.5** | HIGH | Wire the type-hint plumbing in `lower_let` so user `List<T>` / `Map<K, V>` annotations on `let r: List<T> = [...]` reach the synthesizer's internal accumulator and patch its `key_type` / `val_type`. Mirror Python `_lower_let` at v5.15.0. | 30m–1h |
| **Cb.6** | HIGH | New `tests/bootstrap/test_comprehension_mirror.py` — re-runs `tests/test_comprehensions.py` 11 cases through `mnc-stage1` and asserts byte-identical stdout. Safety net. | 1h |
| **Cb.7** | MEDIUM | New comprehension goldens — promote 3 of the 11 cases (list-doubles, list-filter, map-doubles) to `tests/golden/{69_list_comp,70_list_comp_filter,71_map_comp}.mn`. These were Python-only at v5.15.0; now they run through `mnc-stage1`. | 30m |
| **Cb.8** | LOW | Bb.\* seed refresh if any new C-runtime export is required. **None expected** — comprehension lowering uses only existing IR ops (`__mn_list_push`, `IndexSet` on map, `__mn_list_new`, `__mn_map_new`, range iter). | — |

---

## Phase plan

**Phase 0 — Pre-implementation audit.** Run the existing v5.15.0
`tests/test_comprehensions.py` directly against `mnc-stage1` (via
a wrapper that pipes the source through the native compiler). Document
the exact failure shape. Expectation: every case fails with a parse
error at the comprehension's `for` keyword, since the stage1 parser
currently treats `[expr for...]` as `list_lit` and rejects the
unexpected `for`. Write the baseline to
`docs/roadmap/v5/v5.15.1/AUDIT.md` — the acceptance criterion is
that all 11 pass through `mnc-stage1` after Cb.6.

**Phase 1 — AST nodes (Cb.1).** Smallest and lowest-risk first.
Add the enum variant and the accessor stubs. Validate by rebuilding
`mnc-stage1` and confirming goldens 68/68 still pass — adding an
unused enum variant should not affect anything.

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep
```

**Phase 2 — Parsing (Cb.2 + Cb.3).** Add `parse_list_comp` and
`parse_map_comp`. Wire the lookahead in `parse_list_lit` /
`parse_map_lit` so they dispatch to the comp parser when the
discriminator is `KW_FOR`. After this phase: stage1 should
construct correct `Comprehension` AST nodes for comprehension
syntax, but the lowerer doesn't know what to do with them — expect
a runtime crash or wrong output until Phase 3 lands.

Validation between Cb.3 and Cb.4 — confirm the parser produces
the right AST without trying to lower. A small test program with
`mnc-stage1 parse <file>` (if a parse-only mode exists) is enough,
or a temporary `print` injected into `parse_list_comp`.

**Phase 3 — Lowering (Cb.4 + Cb.5).** The hard part. Read
`mapanare/lower.py::_lower_comprehension` and `_wrap_comp_for`
end to end before writing one line of `.mn`. Port byte-for-byte:

- `__mn_comp_N` accumulator naming (use a counter on the lowerer
  state, same as `_tmp_counter`).
- Range-detection branch: if `clause.iter` is `Range(_, _, _)`,
  emit a direct `For` loop. Otherwise, synthesize the index-based
  pattern with a hoisted source binding, `0..len(__src)` range,
  and a per-iteration `let target = __src[__i]` re-bind.
- Filter handling: each `if cond` wraps the body in
  `If(cond, body, None)` innermost-out.
- Map insertion: `__r[k] = v` via `Assign(Index(__r, k), "=", v)`,
  not a method call (Mapanare maps don't expose `.insert`; map
  writes go through `IndexSet` MIR op).
- Type-hint plumbing: when `lower_let` sees a `Comprehension` RHS
  with a `List<T>` / `Map<K, V>` annotation, set `_comp_type_hint`
  on the lowerer; the comprehension lowerer reads it back and
  threads it onto the synthesized inner `LetBinding`. Clear the
  hint before recursing into the element/key/value expressions.

After Phase 3:

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep
```

**This is where fixed point is most likely to break.** The new
synthesizer code is non-trivial; any non-determinism (map iteration
order, hash collisions in symbol tables) surfaces here. If it
breaks, see PROMPT Phase 3 diagnostics.

**Phase 4 — Cross-bootstrap validation (Cb.6).** Add
`tests/bootstrap/test_comprehension_mirror.py` mirroring
`tests/test_comprehensions.py::_compile_and_run` but routing through
`mnc-stage1` instead of `mapanare emit-llvm`. Each of the 11 cases
must produce the same stdout under both compilers. If divergence
surfaces, fix the bootstrap port to match Python — do not modify
the Python lowerer here.

**Phase 5 — Goldens (Cb.7).** Promote three representative cases
from `tests/test_comprehensions.py` to
`tests/golden/{69_list_comp,70_list_comp_filter,71_map_comp}.mn`.
Run the full golden suite — 71/71 pass through stage1.

**Phase 6 — Closeout.** SESSION_REPORT, CHANGELOG entry, CLAUDE.md
release-notes entry, drop the v5.15.0 "deferred to v5.15.1" note
from SPEC §16.5 / §17.5.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Strict 3-stage fixed point breaks during Phase 3 | MEDIUM | Phase 3 validation is explicit. If it breaks, isolate by reverting Cb.4 and re-running — Cb.1 + Cb.2 + Cb.3 alone (no lowerer) cannot break fixed point because `mapanare/self/*.mn` source uses no comprehensions, so the new code paths in stage1 don't fire when stage1 compiles itself. |
| Bootstrap `.mn` lacks an idiom the synthesizer needs | LOW | Phase 0 audit lists every method called by `_lower_comprehension` / `_wrap_comp_for`. The list is small: `_fresh_tmp`-equivalent, `_lookup_var`-equivalent, `_lower_let`/`_lower_stmt`/`_lower_expr` — all pre-existing in `lower.mn`. |
| Bootstrap synthesizer diverges from Python on an edge case | MEDIUM | Cb.6 cross-bootstrap test catches this. The 11 v5.15.0 cases plus the 3 promoted-to-goldens give 14 oracle programs. |
| Map-write idiom (`m[k] = v`) doesn't lower correctly in stage1 | LOW | The Python-side fix in v5.15.0 was *also* `Assign(Index, "=", v)`; if it works in Python (verified by `test_map_comp_doubles`), the same AST shape works in stage1. If divergence appears, root-cause is in `lower_assign`, not in the comprehension synthesizer. |
| LALR-equivalent disambiguation in hand-written parser | MEDIUM | Single-token lookahead at `parse_list_lit` / `parse_map_lit` entry. After the first element parse, peek the next token: `KW_FOR` → comp, otherwise → literal. The bootstrap parser is recursive descent so this is straightforward. |
| Empty-`MapLiteral` annotation patching path missing in stage1 | MEDIUM | This was a v5.15.0 fix (mirror of v4.122.0 empty-`ListLiteral` patch). Confirm the analogous patch exists in stage1's `lower_let`; if not, port it as part of Cb.5. Without it, comprehension-produced maps print `<?>` for indexed values. |

---

## Out of scope (deferred)

- **Pattern-destructuring comprehension targets** `[(k, v) for ...
  in items]` — same as v5.15.0; deferred to v5.20.0 Te.5.
- **Else-clauses in filters** `[x if c else d for x in xs]` —
  Python-style, indefinite.
- **Set comprehensions** — no native set type.
- **Generator / lazy comprehensions** — iterator-protocol arc,
  indefinite.
- **Self-host source rewrites to use comprehensions** —
  v5.17.0 Sh.\*. v5.15.1 only adds parsing/lowering capability;
  `mapanare/self/*.mn` source remains comprehension-free.

---

## Success criteria

- `mnc-stage1` compiles every comprehension program the Python
  bootstrap accepts. Cross-bootstrap test (Cb.6) green on all 11
  v5.15.0 cases.
- Three new goldens (`69_list_comp`, `70_list_comp_filter`,
  `71_map_comp`) compile through `mnc-stage1`. Full corpus
  68/68 → 71/71.
- **Strict 3-stage fixed point preserved.**
- `make lint` clean.

---

## What it unblocks

- **v5.16.0 (Te.4)** can land self-host string-interp parity work
  with confidence that the bootstrap already accepts every surface
  form the Python bootstrap does.
- **v5.17.0 (Sh.\*)** can mechanically rewrite `mapanare/self/`
  via `mnc fmt --to-terse` knowing both compilers handle the
  output. Comprehension introduction in self/ is still a separate
  hand pass — v5.17.0 is brace-style → colon-style only — but
  v5.15.1 closes the parity-gap docket entry that "comprehensions
  work in mapanare but not in mnc".
