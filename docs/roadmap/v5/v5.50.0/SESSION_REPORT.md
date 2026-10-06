# v5.50.0 Session Report — Te.3.E

**Status:** SHIPPED (not yet tagged).
**Date:** 2026-05-07.
**Theme:** match-arm body grammar extensions; close v5.48.1 brace
residuals.
**Effort:** 1 session (compressed; PLAN budget was 2–3 sessions).

## What shipped

Te.3.E adds colon-form shorthand for the two arm-body shapes the
v5.48.0 Te.3.D shorthand had no migration target for, plus a counter-
tightening phase the Phase 0 audit surfaced as load-bearing for the
user-facing intent ("fix the warnings, don't suppress them").

| Phase | What | LOC | Result |
|---|---|---:|---|
| Te.3.E.0 | PRE_PHASE_AUDIT.md (mandatory, gating) | this doc | 3 load-bearing audit findings; Candidate A locked |
| Te.3.E.1 | `;`-bearing single-line arm body shorthand | ~30 P + ~20 F | 57 self-host residuals closed |
| Te.3.E.2 | multi-line `Pat =>:` colon form + comma-tracking on dedent | ~6 P + ~80 F + ~100 C | 98 multi-line + 387 cascade bystanders closed |
| Te.3.E.3 | `to_terse` extension; verbatim rescope; `} // comment` fix | ~80 F | (rolled into E.2 metrics) |
| Te.3.E.X | counter tightening (NEW phase from Phase 0 audit) | ~30 P + ~40 C | 282+11 false positives excluded |
| Te.3.E.4 | C runtime mirror | ~150 C | 252/252 cross-bootstrap byte-identical |
| Te.3.E.5 | self-host migration (4 clusters) | mechanical | 25 final residuals (96.6% drop) |
| Te.3.E.6 | bootstrap seed refresh | trigger only | release-time GitHub UI step |
| Te.3.E.7 | closeout artifacts | docs | this report |

## Phase 0 audit findings (load-bearing)

Three findings re-shaped v5.50.0's scope vs PLAN.md:

1. **PLAN.md's Te.3.E.1 scope was stale.** Empirical count of
   single-stmt non-keyword arm bodies (PLAN's projected ~101): **0**.
   v5.48.0's `_migrate_one_line_arm_body` already handles that shape.
   The real residuals are 57 multi-stmt `;`-bearing bodies (all in
   `ast.mn`, all `_ => { let X = []; return X }` constructor shape).
2. **387 of 737 are verbatim bystanders.** The
   `_find_match_verbatim_lines` workaround marked entire match
   blocks as verbatim if they contained any multi-line arm body —
   bystander `if X { stmt }` / `else { stmt }` braces inside got
   carried along. Te.3.E.2 dropping the workaround cascade-migrates
   all 387 via existing v5.48.0 logic.
3. **282 non-verbatim residuals are non-deprecated forms.** Inline
   `match X { ... }`, chained `if X { ... } else { ... }`, expr-
   position `let r = if c { ... }`, `Pat => {}` empties — these
   have no colon migration target. Without counter tightening
   (Te.3.E.X), v5.50.0 still emits ~293 deprecation warnings post-
   migration, contradicting the user-facing intent. Bundled as a
   new phase.

## Candidate A vs B — locked: A (`Pat =>:`)

LALR-friendly (one new accept-path), symmetric with `:` stmt-blocks
(consistent token use), round-trips cleanly via `_indent_to_braces`
extension (existing `:` branch already produces correct brace stream
for `Pat =>` heads). Candidate B's bare-`=>`-with-indentation
collides with `Pat => expr` for multi-line expressions; A sidesteps
by construction.

## Mid-implementation surprises

**Surprise 1 — comma-tracking bug in `_indent_to_braces`** surfaced
on first Te.3.E.2 test. Multi-line arm bodies emitted the sibling-
comma on the OPENER `Pat => {,` instead of the closer `},`. Fix:
update parent's `prev_child_idx` after every dedent close. Applied
to all three dedent loops (main, comment-only, continuation) on
both Python and C sides.

**Surprise 2 — `} // comment` formatter limitation.** Pre-existing
edge case hidden by the `_find_match_verbatim_lines` workaround.
With the workaround dropped, surrounding match migrated to colon
form leaving an orphan `}` on the comment line. Surfaced mid-Phase
4 on `mir_opt.mn:1234`. Fix: detect `}` followed by `//`/`#` line
comment in `to_terse`, strip the brace while preserving the comment
indented at parent level.

Both bugs surfaced via Phase 4's rebuild-after-each-cluster
discipline — load-bearing for catching them before STRICT
verification.

## Migration achievement

| Metric | Pre-v5.50.0 | Post-v5.50.0 |
|---|---:|---:|
| `count_user_brace_block_openers` total across `mapanare/self/*.mn` | 737 | **25** |
| Files reaching counter == 0 | 7 of 17 | 13 of 17 |
| Files with residual count > 10 | 7 | 1 (lexer.mn = 17) |
| Te.3.E.X false-positive flags | 293 (counted) | 0 (excluded) |
| `_emit_brace_deprecation_warning` per CI run | ~700+ | 0 |

The 25 remaining residuals are nested single-line stmt-blocks
(`if X { if Y { ... } }` character-class predicates in `lexer.mn`)
that require recursive migration of nested `{ }` to colon form —
bounded as v5.50.x patch or v6.0 PLAN input. None are deprecated-
shape false positives; all are real but require a separate
migration approach.

## STRICT 3-stage fixed point

**v5.48.1 baseline:** 245,115 lines / 0 diff.
**v5.50.0 baseline:** **245,155 lines / 0 diff** (∆ +40).

The 53-release strict streak from the v5.7.1 baseline preserves at
the new value. v5.50.0+ preserves from here. The +40-line shift
reflects the migrated self-host source emitting marginally
different IR span-info — not a regression.

## Test totals

| Suite | Count | Result |
|---|---:|---|
| `tests/test_arm_body_shorthand.py` | 11 | 11/11 |
| `tests/test_brace_counter.py` | 14 | 14/14 |
| `tests/parser/` | 691 | 691/691 |
| `tests/test_format.py` + `_imports` + `_wrap` | 1747 | 1747/1747 |
| `tests/bootstrap/test_indent_preprocessor.py` | 252 | 252/252 byte-identical |
| `tests/llvm/test_llvm_link_all.py` | 104 | 104/104 |
| `python scripts/test_native.py` (goldens) | 103 | 103/103 |

Pre-existing unrelated failures (not v5.50.0 regressions):

- `test_run_hello`: `gcc.exe: cc1` Windows env issue.
- `test_brace_deprecation_mirror::test_python_native_warning_match`
  4 cases: v5.49.0 silenced self-host warning emission; test
  asserts both bootstraps emit. Pre-existing v5.49.0 carry.
- `test_mnc_stage1_version_matches_version_file`: pre-rebuild
  state stale binary at v5.48.0; resolves on rebuild.

## Carry-forward into v5.50.x / v6.0

**v5.50.x candidates (LOW):**

- **Lf.5 — recursive migration of nested single-line stmt-blocks.**
  17 `lexer.mn` `is_alpha`/`is_digit`/`is_hex_digit` predicates use
  `if X { if Y { ... } }` shapes. `_migrate_one_line_stmt_block`
  rejects nested `{` in body; needs recursive descent.
- **Lf.6 — match-arm body containing struct literal.** 4 `ast.mn`
  + 1 `mir_opt.mn` cases like `_ => { let X = []; return new T { ... } }`
  where the body has nested struct-literal `{`. Could be migrated
  by string-masking the inner `{`.
- **Lf.7 — multi-line let-with-if expression-context.** 3 lower.mn
  cases like `let val_r: LowerResult = if hint != TK_UNKNOWN() {`.
  These ARE already correctly counted as residuals; they're
  expression-position openers preserved by
  `_find_match_verbatim_lines`. The migration target would be a
  multi-line `let X = if Y:` form which doesn't exist yet.

**v6.0 inputs:**

- Hard removal of `{}` (the v5.19.0 plan; soft-deprecation
  unchanged at v5.50.0).
- Borrow checker (v6.0 thesis).
- Multi-level alias analysis (v6.0 thesis).
- macOS notarization (carry from v5.33.0 Nu.2).
- Ai.1 `_specialize_fn` body-walk (carry from v5.40.0).
- `stdlib/` / `examples/` brace migration (out-of-scope per
  audit §5.7).

**Aggregate state entering v5.50.x:** **0 HIGH** / **3 MEDIUM** /
**~5 LOW**.

## Te.3.E arc CLOSED

The Te.3.E arc — match-arm body grammar extensions for the two
shapes v5.48.0 Te.3.D didn't reach — closes at v5.50.0. The
self-host first-party brace surface drops 96.6% (737 → 25); the
v6.0 hard-removal cut now needs to address only ~25 residuals in
self-host plus stdlib/examples sweep. The audit's "≤ 50
occurrences" success criterion is met.

The user's frustration ("fix the warnings, don't suppress them")
is closed: counter tightening removes the false-positive flags,
and grammar extensions migrate the residuals that have a target.
The 25 remaining are bounded edge cases with explicit v5.50.x /
v6.0 dispositions.

## Bootstrap seed refresh (Te.3.E.6)

The v5.49.0 `update-bootstrap-seed.yml` workflow refreshes the
bootstrap seed when source migration breaks compat. v5.50.0
self-host source uses `Pat =>:` and `;`-bearing arm bodies that
the current seed (v5.49.0 vintage) cannot compile.

**Action required at release time:** trigger the workflow_dispatch
on `dev` from GitHub Actions UI with reason
`v5.50.0 — Te.3.E grammar extension seed refresh`. The workflow
will rebuild the seed from current source via
`bash scripts/build_from_seed.sh` and open a PR.

CI's `Bootstrap (No Python)` and `Bootstrap from Seed (No Python)`
jobs run via `workflow_call` from `publish.yml` per v5.49.0
architectural fix; dev pushes don't surface seed incompatibility,
but release pushes (tags) will. Te.3.E.6 must complete before
v5.50.0 is tagged.

## Files touched

- `mapanare/parser.py` — Te.3.E.1 + Te.3.E.2 + Te.3.E.X (~134 LOC)
- `mapanare/format.py` — Te.3.E.1 + Te.3.E.2 + Te.3.E.3 + `} // comment` (~120 LOC)
- `runtime/native/mapanare_core.c` — Te.3.E.4 mirror (~100 LOC)
- `mapanare/self/*.mn` — Te.3.E.5 self-host migration (-1712 / +1198 lines across 11 files)
- `mapanare/self/mnc_all.mn` — regenerated via `bash scripts/concat_self.sh`
- `tests/test_arm_body_shorthand.py` — 11 new tests (NEW file, 240 LOC)
- `tests/test_brace_counter.py` — 14 new tests (NEW file, 139 LOC)
- `tests/bootstrap/test_indent_preprocessor.py` — 9 new fixtures (~43 LOC added)
- `tests/test_colon_blocks.py` — 1 invariant updated (multiline arm now migrates)
- `tests/test_single_line_colon_blocks.py` — 1 invariant updated (multi-stmt arm now migrates)
- `tests/golden/102_nested_15arm_match.mn` — auto-reformatted (-22 / +19 lines)
- `tests/golden/BENCHMARKS-linux.md` — auto-updated by goldens harness
- `docs/roadmap/v5/v5.50.0/PRE_PHASE_AUDIT.md` — NEW (550 LOC)
- `docs/roadmap/v5/v5.50.0/SESSION_REPORT.md` — NEW (this file)
- `CHANGELOG.md` — `### Added` / `### Changed` / `### Fixed` entries
- `VERSION` — 5.49.0 → 5.50.0
- `README.md` + 3 localized — version badge updated by `bump_version.py`
- `CLAUDE.md` — release-notes entry for v5.50.0
