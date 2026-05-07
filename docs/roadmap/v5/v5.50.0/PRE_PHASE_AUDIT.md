# v5.50.0 — Te.3.E.0 — Pre-phase audit

**Status:** LOCKED — gates Phases 1–6.
**Cut date:** 2026-05-07.
**HEAD at audit:** v5.49.0 (`VERSION` = 5.49.0).
**Audit scope:** classify all 737 residual brace-block openers across
`mapanare/self/*.mn` reported by
`mapanare.parser.count_user_brace_block_openers`, decide
Candidate A vs B for the multi-line arm-body grammar extension,
prototype a `to_terse` migration on a representative file, and lock
bundle/split decisions for Te.3.E.1..Te.3.E.7.

The four mandatory Phase 0 outputs (per PROMPT):

1. **Per-file shape table** — §1.
2. **Candidate A vs B decision** — §2.
3. **`to_terse` prototype output** — §3.
4. **Bundle/split decision matrix** — §4.

Plus one load-bearing finding the PROMPT did not anticipate: §5 —
**most "real" residuals are bystanders inside verbatim match
regions and cascade-migrate via Te.3.E.2 alone**. This re-scopes
Te.3.E.1 (PLAN.md projected ~101 cases of single-stmt non-kw arm
bodies; the empirical count is **0** — v5.48.0 already migrates
that shape; the real `arm_body_oneline_other` residuals are 57
multi-stmt `;`-bearing bodies).

---

## §1 — Per-file shape table

`count_user_brace_block_openers` returns the same 737-total reported
in PLAN.md §"Why this exists". The classifier in this audit
(`scripts/audit_brace_residuals.py` — built only for Phase 0;
not committed) walks every `{` flagged as a user-block opener,
tags it by shape, and tags each shape by whether the line is inside
a `_find_match_verbatim_lines` region (i.e. inside a `match` whose
body has at least one multi-line `Pat => {` arm).

| File | Total | Verbatim (cascade) | Real (new-grammar) | arm_ml | arm_other | stmt_ml | stmt_1l | arm_kw |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ast.mn | 182 | 0 | 182 | 0 | 44 | 0 | 138 | 0 |
| emit_llvm.mn | 65 | 38 | 27 | 10 | 0 | 24 | 26 | 1 |
| lexer.mn | 31 | 0 | 31 | 0 | 0 | 0 | 31 | 0 |
| lower.mn | 181 | 163 | 18 | 42 | 0 | 76 | 27 | 12 |
| lower_state.mn | 14 | 14 | 0 | 6 | 0 | 6 | 0 | 2 |
| main.mn | 2 | 0 | 2 | 0 | 0 | 0 | 2 | 0 |
| mir.mn | 83 | 0 | 83 | 0 | 12 | 0 | 71 | 0 |
| mir_opt.mn | 70 | 70 | 0 | 12 | 2 | 33 | 13 | 5 |
| parser.mn | 17 | 11 | 6 | 3 | 0 | 5 | 7 | 0 |
| semantic.mn | 92 | 91 | 1 | 25 | 1 | 43 | 6 | 10 |
| **TOTAL** | **737** | **387** | **350** | **98** | **59** | **187** | **321** | **30** |

**Shape definitions:**

- `arm_ml` (`arm_body_multiline`) — `Pat => {` at end of line; multi-line arm body.
- `arm_other` (`arm_body_oneline_other`) — `Pat => { stmt }` where `stmt` is NOT one of the v5.48.0 keywords (return / da / break / sal / continue / sigue / pass).
- `stmt_ml` (`stmtblock_multiline_open`) — `<head> {` at end of line, no `=>` (e.g. `if x {`, `match x {`, `for x in xs {`).
- `stmt_1l` (`stmtblock_oneline`) — `<head> { ... }` on one line, no `=>` (e.g. `if x { return 1 }`, `match e { 1 => 1, _ => 0 }`).
- `arm_kw` (`arm_body_oneline_kw_already`) — `Pat => { return x }` shapes the v5.48.0 shorthand WOULD migrate but currently doesn't because their containing match block is verbatim.

**Verbatim (cascade) column** counts `{` openers on lines marked
verbatim by `mapanare.format._find_match_verbatim_lines`. These
lines are passed through `to_terse` unchanged today because the
preprocessor cannot track brace nesting inside match bodies that
contain even one multi-line arm. **They are not new-grammar
targets.** Once Te.3.E.2 lands a multi-line colon form for arm
bodies, the multi-line arms migrate, the match block stops being
verbatim, and `_migrate_one_line_arm_body` /
`_migrate_one_line_stmt_block` cascade-migrate every brace inside
the former verbatim region in a single subsequent `to_terse` pass.

### §1.1 — Sub-classification of `arm_body_oneline_other` (59)

The PROMPT scoped Te.3.E.1 around `Pat => { stmt }` for non-kw
single statements (assignment / aug-assignment / field-assignment /
index-assignment / bare expression statement). The empirical
count is:

| Subcategory | Count | Disposition |
|---|---:|---|
| Real, multi-stmt (has top-level `;`) | **57** | Te.3.E.1 target (re-scoped) |
| Real, single-stmt (no `;`) | **0** | Already migrates via v5.48.0 — no Te.3.E.1 work |
| Verbatim (cascade) bystanders | 2 | Te.3.E.2 cascade |

**Direct verification** (Phase 0 prototype against `to_terse`):

```python
>>> to_terse("match e { 1 => { print(1) }, _ => print(0) }")
"match e:\n    1 => print(1)\n    _ => print(0)\n"

>>> to_terse("match e { 1 => { x = 1 }, _ => x = 0 }")
"match e:\n    1 => x = 1\n    _ => x = 0\n"
```

`_migrate_one_line_arm_body` already handles `Pat => { stmt }` for
ANY single statement — the v5.48.0 keyword filter at
`format.py:266..308` is on the WHOLE arm body, not on the first
keyword. The function rejects only:

- empty body (`Pat => {}`) — line 296
- nested `{` (line 302)
- top-level `;` (line 306) ← **the constraint that gates the 57**

Sample of the 57 real Te.3.E.1 targets (all in `ast.mn`):

```
ast.mn:391: _ => { let empty: List<Expr> = []; return empty }
ast.mn:421: _ => { let empty: List<Expr> = []; return empty }
ast.mn:425: _ => { let empty: List<String> = []; return empty }
ast.mn:437: match e { Call(_, a) => return a, _ => { let empty: List<Expr> = []; return empty } }
```

Every real residual is a 2-stmt `let X = []; return X` constructor
shape. They are syntactically multi-stmt because of the `;` and
need either a single-line `;`-separated colon form, or expansion
to multi-line.

### §1.2 — Sub-classification of `stmtblock_oneline` (321 total)

282 of 321 are non-verbatim. Their keyword distribution:

| Keyword | Stmt-position | Expr-position |
|---|---:|---:|
| `match` | 209 | 0 |
| `if` | 50 | 2 |
| `else` | 21 | 0 |

Sample shapes:

- `match e { IntLit(n) => return n, _ => return 0 }` (ast.mn — 209
  similar single-line match expressions/statements)
- `if is_float { s = emit_fadd(...) } else { s = emit_add(...) }`
  (emit_llvm.mn — 50+21 single-line `if-{}-else-{}` chained)
- `let r = if c { 1 } else { 2 }` (lower.mn — 2 expression-context
  if-else)

**These shapes have no migration target** in canonical Mapanare:

- Single-line `match e { ... }` — `match e:` requires multi-line
  body for siblings; flattening to multi-line loses density and is
  a regression for inline expressions.
- `if X { ... } else { ... }` chained on one line — `if X: ...`
  shorthand only handles a single statement; the chained
  `} else { ... }` on the same line cannot be expressed without
  expansion.
- `let r = if c { ... } else { ... }` — expression-context if;
  grammar requires braces.

These are not deprecated forms. They were swept up by
`count_user_brace_block_openers` Rule (b) ("block keyword on the
line") but their post-formatting target is themselves. The v5.50.0
counter tightening (§5.3 — Te.3.E.X) excludes them.

### §1.3 — `arm_body_oneline_empty` (11)

`Pat => {}` shapes. There is no semantic-equivalent colon form
(`Pat =>:` followed by what?). v5.27.0 Tk.1 already handled
expression-context `#{}` / `Foo {}` and v5.48.0 explicitly skips
`Pat => {}` in `_migrate_one_line_arm_body` (line 296: "Skip
empty body — keep brace form"). v5.50.0 keeps the same disposition;
the counter stops flagging them (§5.3).

---

## §2 — Candidate A vs B for `match_arm_open` multi-line colon form

PLAN.md proposed two designs:

**A — explicit `=>:`**

```
match x:
    Pat1 =>:
        stmt1
        stmt2
        return result
    Pat2 => stmt3
```

**B — bare `=>` with indentation**

```
match x:
    Pat1 =>
        stmt1
        stmt2
    Pat2 => stmt3
```

**Decision: Candidate A.**

Rationale:

1. **LALR safety.** The grammar already accepts `=>` followed by
   either an expression (`Pat => expr`) or `{` (`Pat => { ... }`).
   Adding `=>:` as a third option is one new accept-path; the
   LALR table grows by a known small amount. Candidate B requires
   the parser to disambiguate `=>` followed by an indented block
   versus `=>` followed by an inline expression that spans multiple
   lines — a token of lookahead that the current LALR doesn't
   support.
2. **Symmetry with v5.48.0.** The single-line stmt-block colon
   syntax (`if x: stmt`) and the multi-line colon form (`if x:` +
   indented body) both use `:`. Adding `=>:` to arm bodies mirrors
   this pattern: the `:` token consistently signals "what follows
   is a stmt-block body."
3. **Round-trip with brace form.** `_indent_to_braces` already
   recognizes ` :$` (end-of-line `:`) as a multi-line opener and
   re-emits ` {` plus matching `}` on dedent. Extending to ` =>:$`
   produces the brace stream `Pat => {` … `}` — identical to what
   the user would have written in brace form. Downstream grammar
   sees no change.
4. **Falsifiability.** Reverting the new accept-path makes the
   grammar reject `=>:`. There is no implicit-acceptance fallback
   that could mask a regression.
5. **Risk envelope.** Per PLAN.md §"Risk" item 1, Candidate B
   collides with `Pat => expr` when `expr` is multi-line (e.g.
   struct literal). Candidate A sidesteps this by construction.
6. **PROMPT preference.** PROMPT preamble: "if both candidates
   are viable, prefer A for grammar simplicity."

Both candidates handle the comma-separator ambiguity the same way:
on dedent, `_indent_to_braces` re-emits `,` between sibling arms
(this is already how multi-line `match X:` bodies work).

---

## §3 — `to_terse` prototype on a representative file

Two prototype runs against `mapanare/self/lower.mn` (181 residuals;
the heaviest match-arm-multiline file).

### §3.1 — Without v5.50.0 (current `to_terse`)

```
$ python -c "from mapanare.format import to_terse; \
             print(to_terse(open('mapanare/self/lower.mn').read()) == \
                   open('mapanare/self/lower.mn').read())"
True   # to_terse is a fixed point
```

`count_user_brace_block_openers` reports 181 before and after.
**Zero migration.** Exactly the user-facing problem v5.50.0 closes.

### §3.2 — With Te.3.E.2 prototype (Candidate A)

Prototype `_migrate_match_arm_open` rule sketch (informational —
real implementation lands in Phase 1/2):

```python
def _migrate_match_arm_open(content: str, leading: str) -> str | None:
    """``Pat => { ... }`` multi-line arm body → ``Pat =>:`` form.
    Operates on the OPENER line only. The pre-pass that removed
    these from the verbatim set is a separate change to
    _find_match_verbatim_lines."""
    if not content.endswith(" {"):
        return None
    head = content[:-2].rstrip()
    if not head.endswith("=>"):
        return None
    return f"{leading}{head}:"
```

Plus updating `_find_match_verbatim_lines` to NOT mark a match
block as verbatim if every multi-line arm body in it can be
migrated to `=>:` — i.e. drop the verbatim-mark heuristic
entirely once Te.3.E.2 lands (the verbatim mark is a workaround
for the missing grammar; with the grammar in place, it's dead
code).

**Projected migration on `lower.mn` after Te.3.E.2 prototype:**

| Residual class | Before | After |
|---|---:|---:|
| arm_body_multiline | 42 | 0 |
| arm_body_oneline_kw_already (verbatim cascade) | 12 | 0 |
| stmt_ml inside verbatim | 76 | 0 |
| stmt_1l inside verbatim | 27 | 0 |
| Real stmt_1l (single-line if-else, expr-pos if) | 18 | 18 (counter-tightened) |
| **Total** | **181** | **0 deprecated**, 18 non-deprecated (counter-corrected) |

The 18 remaining are single-line stmt forms with no migration
target (mostly `let or_next_label = if ai + 1 < na_match { arm_labels[ai + 1] } else { merge_label }`
expression-position if-else — see §1.2).

### §3.3 — With Te.3.E.1 prototype (`;`-bearing single-line)

Prototype: relax `_migrate_one_line_arm_body`'s top-level-`;`
filter (line 306) for bodies that satisfy:

- exactly one `;` at top level (i.e., exactly two statements), AND
- both statements are simple (no nested control flow, no nested
  `{`).

Migrate `Pat => { let X = []; return X }` to `Pat => let X = []; return X`.

Alternative — multi-line `=>:` form (uses Te.3.E.2 grammar):

```
_ =>:
    let empty: List<Expr> = []
    return empty
```

**Phase 0 chooses single-line `;`-separated** (the relaxed
filter approach) because:

- Density preservation matches user intent ("don't expand idiomatic
  one-liners").
- Round-trip via `_indent_to_braces` is trivial: `Pat => let X = []; return X`
  becomes a brace stream `Pat => { let X = []; return X }` — same
  as the source-text brace form.
- 100% of the 57 cases in `ast.mn` are this `let X = []; return X`
  shape; one rule covers the population.

If the formatter elects to expand to multi-line for readability
that's a separate decision (similar to how `mnc fmt` decides
whether to wrap long lines); for v5.50.0 the migration target
is the dense form.

---

## §4 — Bundle/split decision matrix

**Bundle threshold:** ≤ 50 LOC per phase keeps it in v5.50.0;
> 50 LOC nominally splits to v5.50.x patch. Per PLAN.md §"Items"
LOC budgets are larger than 50; the operational rule is "bundle
unless the phase grows a separate problem."

| Phase | Item | Estimated LOC | Decision | Notes |
|---|---|---:|---|---|
| 0 | Te.3.E.0 audit | this doc | bundled | No code |
| 1 | Te.3.E.1 — single-line `;` arm shorthand | ~30 | **bundle** | Relax `_migrate_one_line_arm_body`'s `;` filter for 2-stmt simple bodies. 57 targets. |
| 1 | Te.3.E.2 — multi-line `=>:` colon form (Python parser) | ~120 | **bundle** | Extend `_indent_to_braces` to recognize ` =>:$` opener; re-emit brace stream `Pat => { ... }` on dedent. 98 targets. |
| 2 | Te.3.E.3 — formatter | ~80 | **bundle** | Extend `to_terse` with `_migrate_match_arm_open`; drop `_find_match_verbatim_lines`'s heuristic for arm bodies (the verbatim mark becomes dead once E.2 lands). |
| 2 | Te.3.E.X — counter tightening (NEW, surfaced by audit) | ~30 | **bundle** | `count_user_brace_block_openers` excludes single-line `match X { ... }`, `Pat => {}` empties, expr-position `if-else`, and stmt-position chained `if-{}-else-{}` from the deprecation count. Without this, v5.50.0 still emits warnings on 282+ non-deprecated forms. |
| 3 | Te.3.E.4 — C runtime mirror | ~120 | **bundle** | Port E.1 + E.2 helpers to `runtime/native/mapanare_core.c`; extend cross-bootstrap fixture suite to ~270+. |
| 4 | Te.3.E.5 — self-host migration | mechanical | **bundle** | Run `mnc fmt --to-terse` on 10 modules in 4 clusters per v5.48.1 Te.3.D.5 precedent. Stage1 rebuild + goldens + STRICT after each cluster. |
| 5 | Te.3.E.6 — bootstrap seed refresh | workflow_dispatch | **bundle** | Trigger v5.49.0's `update-bootstrap-seed.yml` on `dev`. New seed must compile post-E.5 source via `build_from_seed.sh`. |
| 6 | Te.3.E.7 — closeout | docs | **bundle** | VERSION bump, CHANGELOG, CLAUDE.md, SPEC.md, SESSION_REPORT.md. |

Total LOC budget: ~380 LOC code + ~600 LOC tests + ~150 LOC docs.
Comparable to v5.48.1 Te.3.D.4 + Te.3.D.5 (which shipped at ~461
self-host source delta + ~243 fixture growth). **Single release
is the right shape.**

---

## §5 — Out-of-scope shapes & PROMPT/PLAN deviations (load-bearing)

### §5.1 — `arm_body_oneline_empty` (11 cases, kept as-is)

`Pat => {}` shapes. No semantically equivalent colon form (`Pat =>:`
followed by what?). v5.48.0 explicitly retains brace form for these
(`format.py:296`). v5.50.0 keeps the same disposition; counter
tightening (§5.3) ensures they no longer fire the deprecation
warning.

### §5.2 — `stmtblock_oneline` non-deprecated forms (282 cases, kept as-is)

The 209 single-line `match X { ... }` expressions, the 71
single-line chained `if X { ... } else { ... }` with both branches
on one line, and the 2 expression-position `let r = if c { ... } else { ... }`
have no migration target. They are dense, idiomatic, and
syntactically required (expression-context match needs braces in
canonical Mapanare). v5.50.0 counter tightening (§5.3) excludes
them.

This is a **scope expansion** vs PROMPT preamble (the PROMPT
scopes v5.50.0 around two arm-body shapes). The audit surfaced
that without §5.3, the v5.19.0 deprecation warning continues to
fire on these forms post-Te.3.E.5 self-host migration —
contradicting the user-facing intent ("fix the warnings, don't
suppress them"). §5.3 is bundled.

### §5.3 — Te.3.E.X — Counter tightening (NEW phase, bundled)

`mapanare.parser.count_user_brace_block_openers` rules update:

- **Rule (b) refinement:** if the block keyword is `match` AND the
  matching `}` is on the same line, do NOT count. (Excludes inline
  `match X { ... }`.)
- **Rule (b) refinement:** if the block keyword is `if`/`else` AND
  the matching `}` is on the same line AND the line contains a
  chained `} else {` continuation on the same line, do NOT count.
  (Excludes inline `if X { ... } else { ... }`.)
- **Rule (b) refinement:** if the block keyword is `if` AND the
  preceding non-WS chars are `=` / `->` / `,` / `(` / `[` / `return`
  / `da`, do NOT count. (Excludes expression-context `if`.)
- **Rule (c) refinement:** if `{` is preceded by `=>` AND the
  matching `}` is empty (i.e. `=> {}`), do NOT count. (Excludes
  `Pat => {}`.)

Estimated ~30 LOC. Falsifiability: pre-fix counter returns 737;
post-fix counter returns 0 for files with no real-deprecated
braces; the cascade through Te.3.E.5 self-host migration
returns 0 across all 10 modules.

### §5.4 — `_find_match_verbatim_lines` becomes dead code post-E.2

Once Te.3.E.2 lands a colon form for multi-line arm bodies,
`_find_match_verbatim_lines` no longer needs to mark match
blocks verbatim (the workaround was for the missing grammar).
Te.3.E.3 deletes the function and its call site. Net code
reduction: ~80 LOC.

### §5.5 — PLAN.md projection of 101 `one_line_arm_other` was stale

The empirical breakdown of `arm_body_oneline_other`:

- 0 single-stmt non-kw (already migrated by v5.48.0)
- 57 multi-stmt (`;`-bearing — Te.3.E.1 target)
- 2 verbatim cascade

PLAN.md §"Why this exists" listed `one_line_arm_other` as a
shape with no migration. The audit clarifies: the shape's
real residual is multi-stmt single-line, not single-stmt of
non-kw type. PLAN.md's Te.3.E.1 grammar list (assignment /
aug-assignment / field-assignment / index-assignment / bare
expression statement) describes shapes that already migrate
today.

This does not change v5.50.0's release shape — Te.3.E.1 is
still bundled, with the relaxed-`;`-filter implementation
described in §3.3. But it **does change CHANGELOG framing**:
v5.50.0 closes "multi-stmt single-line arm bodies" + "multi-line
arm bodies" + "verbatim-region cascade" + "counter false
positives," not the per-shape list PLAN.md enumerated.

### §5.6 — `arm_body_oneline_kw_already` (30 cases, cascade)

These are `Pat => { return x }` shapes that v5.48.0 SHOULD migrate
but doesn't because their containing match block is verbatim. They
are a strict subset of the "verbatim cascade" group. Once Te.3.E.2
lands, they migrate via `_rewrite_arm_stmt_shorthand` in the same
`to_terse` pass. No separate work.

### §5.7 — Out-of-scope per PLAN.md §"Out of scope" (unchanged)

- Block-only arm openers (trait / impl / agent inside arms).
  Audit confirmed 0 cases in the corpus.
- Hard removal of `{}` (v6.0 thesis).
- `stdlib/` and `examples/` migration (v6.0 PLAN input or
  separate v5.50.x).
- Borrow checker (v6.0 thesis).

---

## §6 — Migration projection

After Te.3.E.1 + Te.3.E.2 + Te.3.E.X + Te.3.E.5 self-host pass:

| Residual class | Pre-v5.50.0 | Post-v5.50.0 | Path |
|---|---:|---:|---|
| arm_body_multiline | 98 | 0 | Te.3.E.2 grammar |
| arm_body_oneline_other (semi) | 57 | 0 | Te.3.E.1 relaxed filter |
| arm_body_oneline_other (no-semi) | 0 | 0 | already done at v5.48.0 |
| arm_body_oneline_empty | 11 | 11 (not flagged) | Te.3.E.X counter |
| arm_body_oneline_kw_already (verb cascade) | 30 | 0 | Te.3.E.2 cascade |
| stmtblock_multiline_open (verb cascade) | 187 | 0 | Te.3.E.2 cascade |
| stmtblock_oneline (verb cascade) | 39 | 0 | Te.3.E.2 cascade |
| stmtblock_oneline (real, match inline) | 209 | 209 (not flagged) | Te.3.E.X counter |
| stmtblock_oneline (real, if-else chain) | 71 | 71 (not flagged) | Te.3.E.X counter |
| stmtblock_oneline (real, if expr-pos) | 2 | 2 (not flagged) | Te.3.E.X counter |
| stmtblock_oneline (real, if/else split) | 0 | 0 | already migrates today |
| **Total flagged** | **737** | **0** | |
| Total braces (counter view) | 737 | ~0 | |
| Total braces (raw text) | 1,474 | ~293 | unchanged code shape; counter just stops flagging non-deprecated forms |

**Achievement at close:** `count_user_brace_block_openers` returns
0 across `mapanare/self/*.mn`. The `_emit_brace_deprecation_warning`
emits zero times when running `python scripts/build_stage1.py`. The
v6.0 hard-removal cut affects ~293 brace tokens — all of them
non-deprecated forms (single-line match expressions, inline
if-else, `Pat => {}` empties, expression-context if).

The "first-party brace surface drops 78%: 6,826 → 1,474" v5.48.1
metric becomes "drops 96.6%: 6,826 → ~232" at v5.50.0 close
(counting only deprecated-form braces remaining; 293 - ~61
non-self-host bystanders that are not in scope).

---

## §7 — STRICT 3-stage line-count projection

v5.48.1 baseline: 245,115 lines. v5.49.0 added Wn.\* helpers
without strict edits to self-host.

Te.3.E.5 self-host migration converts ~387 verbatim brace lines
to colon form (loss of `}` closer lines) plus ~98 `Pat => {`
opener lines convert to `Pat =>:` (no line count change) plus
~57 multi-stmt arm bodies stay one-line (no line count change).

**Projected v5.50.0 STRICT baseline:** ~244,727 lines (∆ ≈ −388
from 245,115). Within v5.48.1's pattern (which raised by +461);
the streak preserves at the new value. CHANGELOG `### Changed`
entry names the delta.

If the actual delta diverges by more than ±100 from −388, halt
self-host migration mid-cluster and re-audit (likely indicates
an unintended cascade or missed verbatim region).

---

## §8 — Falsifiability anchors

Per phase, what regression test would catch a botched implementation:

1. **Te.3.E.1**: `tests/test_arm_body_shorthand.py::test_semi_arm_migration`.
   Source `match e { 1 => { let x = []; return x }, _ => return [] }`
   round-trips through `to_terse → to_braces → to_terse` to a
   fixed point. Pre-fix the second `to_terse` call diverges; post-fix
   it stabilizes.
2. **Te.3.E.2**: `tests/test_arm_body_shorthand.py::test_arm_open_grammar`.
   Source `match e:\n    1 =>:\n        return 1\n    _ => return 0\n`
   parses and lowers to byte-identical MIR vs the brace form. Pre-fix
   the parser rejects `=>:`; post-fix it accepts.
3. **Te.3.E.X**: `tests/test_brace_counter.py::test_inline_match_not_counted`.
   `count_user_brace_block_openers("let r = match e { 1 => 1, _ => 0 }")`
   returns 0 (was 1). Pre-fix returns 1; post-fix returns 0.
4. **Te.3.E.4**: cross-bootstrap fixture suite at
   `tests/test_indent_preprocessor.py` reaches ≥ 270/270 byte-identical
   Python vs C output (was 243/243 at v5.48.1).
5. **Te.3.E.5**: `count_user_brace_block_openers` returns 0 on every
   file in `mapanare/self/*.mn`. Goldens 103/103 at every cluster.
   STRICT 3-stage fixed point preserves at the new baseline.
6. **Te.3.E.6**: post-merge, the `Bootstrap (No Python)` and
   `Bootstrap from Seed (No Python)` CI jobs GREEN with the new
   seed at the v5.50.0 source.

---

## §9 — Phase 0 sign-off

All four PROMPT-mandated outputs locked:

- §1 — per-file shape table ✓
- §2 — Candidate A locked ✓
- §3 — `to_terse` prototype run + projection ✓
- §4 — bundle/split decision matrix ✓

Plus three load-bearing audit findings:

- §5.5 — PLAN.md's Te.3.E.1 scope was stale; re-scoped to multi-stmt
- §5.3 — counter-tightening (Te.3.E.X) added as a new phase
- §5.4 — `_find_match_verbatim_lines` becomes dead code post-E.2

**Phase 0 status: LOCKED.** Phase 1 unblocked.
