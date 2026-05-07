# v5.50.0 — Te.3.E — match-arm body grammar extensions; close v5.48.1 brace residuals

**Status:** PLANNING
**Type:** Grammar extension. Adds colon-form shorthand for the
match-arm body shapes the v5.48.0 Te.3.D shorthand doesn't reach
(`one_line_arm_other` multi-stmt single-line, `match_arm_open`
multi-line). Then migrates the ~737 residual brace openers across
`mapanare/self/*.mn` via `mnc fmt --to-terse` and regenerates
`mnc_all.mn`. Closes the v5.48.x soak's primary carry: brace
residuals that have no migration target.
**Breaking:** No (additive grammar). Existing brace-form arm bodies
keep parsing under the v5.19.0 deprecation warning. v6.0 hard
removal is the cut date for braces; v5.50.0 just gives the
formatter more shapes to migrate.
**Prerequisite:** v5.48.1 (Te.3.D bootstrap mirror + self-host
migration) shipped — the v5.48.0 single-line stmt-block colon
syntax and stmt-keyword arm shorthand are the foundation
v5.50.0 extends. v5.49.0 shipped (Wn.* Windows fix); v5.49.0
parser smartness ("only warn when fmt would actually migrate")
ensures that as v5.50.0 lands files with new shorthands, the
deprecation noise drops to zero by construction.
**Estimated effort:** 2–3 sessions. The work is structurally
parallel to v5.48.0 + v5.48.1 (Python parser + formatter +
C runtime mirror + self-host source migration + cross-bootstrap
tests + STRICT). Each phase is bounded; the integration risk is
LALR grammar disambiguation between expression-arms and
statement-arms.

---

## Why this exists

After v5.48.1, the v5.19.0 brace-deprecation warning fires for
~737 occurrences across 10 self-host modules:

| File | Residual braces | Shape |
|---|---:|---|
| `main.mn` | 2 | mostly `match_arm_open` |
| `ast.mn` | 182 | `one_line_arm_other` (constructor-style) |
| `mir.mn` | 83 | `one_line_arm_other` |
| `parser.mn` | 17 | `match_arm_open` |
| `lexer.mn` | 31 | mixed |
| `semantic.mn` | 92 | `match_arm_open` + `one_line_arm_other` |
| `lower_state.mn` | 14 | `one_line_arm_other` |
| `lower.mn` | 181 | both |
| `mir_opt.mn` | 70 | `match_arm_open` |
| `emit_llvm.mn` | 65 | `match_arm_open` |
| **Total** | **~737** | |

`mnc fmt --to-terse` is a fixed point on these files because the
v5.48.0 shorthand has no colon form for either residual shape.
The warning is honest about the deprecation but tells users to
run a tool that's a no-op — pure noise on every CI run.

v5.49.0 made the Python parser warning smarter (skip when
formatter is a fixed point) and silenced the self-host emission
entirely, which removed the noise from CI logs. But the
**actual residual** — 737 braces in shapes the grammar can't
yet migrate — remains. v6.0 hard-removal is the cut date; until
then, any user running `mnc fmt` on these files sees no progress.

v5.50.0 closes the loop: extend the grammar, extend the formatter,
migrate the residuals. After v5.50.0 the first-party brace
surface drops from 1,474 (v5.48.1) to ~0 in `mapanare/self/*.mn`,
and `mnc fmt --to-terse` becomes a true round-trip-to-fixed-point
on all self-host source.

The Te.3.E prefix continues the Te.3.D arc (single-line colon
blocks + stmt-keyword arm shorthand). Te.3.E is "everything else
the arm body accepts" + "multi-line arm bodies."

---

## Grammar extensions

### Te.3.E.1 — `one_line_arm_other` colon form

**Today (v5.48.0 shorthand):** `Pat => { stmt }` migrates only when
`stmt` starts with `return`, `da`, `break`, `sal`, `continue`,
`sigue`, or `pass`. Other single-statement bodies keep braces.

**v5.50.0:** extend the shorthand to accept ANY single statement
that's syntactically unambiguous in arm-body context. Concretely:

- **Assignment:** `Pat => { x = 1 }` → `Pat => x = 1`
- **Augmented assignment:** `Pat => { x += 1 }` → `Pat => x += 1`
- **Field assignment:** `Pat => { st.field = v }` → `Pat => st.field = v`
- **Index assignment:** `Pat => { arr[i] = v }` → `Pat => arr[i] = v`
- **Bare expression statement:** `Pat => { foo(x) }` → `Pat => foo(x)`
  (function call as statement; result discarded)
- **Yield / await wrappers** (where applicable; Phase 0 audit
  enumerates).

**Disambiguation:** the existing arm-body parser already
distinguishes expression-arms (`Pat => expr,`) from statement-arms
(`Pat => { stmts }`). The question is whether `Pat => foo(x),`
should be expression-arm-returning-call-result or statement-arm-
discarding-call-result.

**Rule:** in expression-position match (`let r = match x { ... }`),
all arms are expression-arms. In statement-position match, an arm
that ends with `return/da/break/sal/continue/sigue/pass` is a
statement-arm; otherwise it's an expression-arm whose value is
either consumed (assigned via the enclosing expression) or
discarded (statement-position).

This is a behavior-preserving rewrite: the brace form
`Pat => { foo(x) }` is currently a statement-arm; the colon form
`Pat => foo(x)` should lower identically. Phase 0 audit confirms
or surfaces a counterexample.

### Te.3.E.2 — `match_arm_open` multi-line colon form

**Today:** multi-statement arm bodies always use braces:
```
match x {
    Pat1 => {
        stmt1
        stmt2
        return result
    },
    Pat2 => stmt3
}
```

**v5.50.0:** introduce indentation-based multi-line arm bodies.
Two design candidates (Phase 0 audit decides):

**Candidate A — explicit `=>:` for multi-line** (mirrors `:` for
stmt-blocks):
```
match x:
    Pat1 =>:
        stmt1
        stmt2
        return result
    Pat2 => stmt3
```

**Candidate B — bare `=>` with indentation** (Python-like):
```
match x:
    Pat1 =>
        stmt1
        stmt2
        return result
    Pat2 => stmt3
```

Candidate A is grammatically explicit (the `:` token disambiguates
from expression-arm form). Candidate B is more terse but requires
indentation tracking to find the arm boundary. **Decision in
Phase 0 audit, locked before implementation.**

In both candidates, the comma separator between arms becomes
optional when arms are on separate lines (or banned when there's
indentation). Same approach Mapanare uses for stmt-blocks.

### Te.3.E.3 — formatter `to_terse` extensions

`mapanare/format.py::to_terse` extends to migrate both shapes:

- `_migrate_one_line_arm_body_other`: rewrites
  `Pat => { stmt }` → `Pat => stmt` for the new accepted statement
  shapes.
- `_migrate_match_arm_open`: rewrites multi-statement brace bodies
  to the chosen multi-line colon form. Preserves trailing-comma /
  indentation conventions per the chosen design.

Idempotence: `to_terse(to_terse(source)) == to_terse(source)`.
Round-trip: `to_braces(to_terse(source))` lowers to identical MIR.

### Te.3.E.4 — C runtime mirror

`runtime/native/mapanare_core.c::__mn_indent_to_braces` and
`__mn_rewrite_arm_stmt_shorthand` extend with the new shapes.
Byte-identical to the Python helpers per the Te.3.D.4 oracle
pattern (cross-bootstrap fixture suite at
`tests/test_indent_preprocessor.py` extended).

### Te.3.E.5 — self-host source migration

Run `mnc fmt --to-terse` over the 10 self-host modules in
`mapanare/self/*.mn`. Verify each module rebuilds via stage1,
goldens 103/103 at every cluster, STRICT 3-stage fixed point
preserved. 4-cluster migration matches the v5.48.1 Te.3.D.5
pattern.

After migration: regenerate `mnc_all.mn` via
`bash scripts/concat_self.sh`. Verify the bootstrap-from-seed
gate passes (the v5.49.0 update-bootstrap-seed workflow's new seed
must support the v5.50.0 grammar — Phase 0 plans the seed refresh
ordering).

---

## Goals

1. **Te.3.E.0** — **Phase 0 audit** (PRE_PHASE_AUDIT.md, mandatory).
   Empirically classify the 737 residual braces by shape. Decide
   Candidate A vs B for `match_arm_open`. Empirically project
   migration via `to_terse` extension prototype: how many braces
   close, how many remain (bounded out-of-scope shapes). Lock
   bundle/split decision: ≤ 50 LOC fix per phase = bundle;
   > 50 LOC = split to v5.50.x patches per phase.
2. **Te.3.E.1** — **`one_line_arm_other` shorthand.** Python
   parser + `_rewrite_arm_stmt_shorthand` extension. Add tests
   for every accepted shape under English + Spanish keyword
   variants.
3. **Te.3.E.2** — **`match_arm_open` multi-line colon form.**
   Python parser grammar + `_indent_to_braces` extension for the
   chosen candidate. Add positive + negative parse fixtures.
4. **Te.3.E.3** — **formatter migration.** Extend
   `mapanare/format.py::to_terse` with the two new rewrite rules.
   Pytest cases for idempotence + AST-equivalence + round-trip.
5. **Te.3.E.4** — **C runtime mirror.** Port the two new helpers
   to `runtime/native/mapanare_core.c`. Cross-bootstrap fixture
   suite extends with positive + negative shapes for both
   candidates.
6. **Te.3.E.5** — **self-host source migration.** Run
   `mnc fmt --to-terse` over `mapanare/self/*.mn` in 4 clusters
   per v5.48.1 precedent. Stage1 rebuild + goldens 103/103 +
   STRICT 3-stage at every cluster.
7. **Te.3.E.6** — **bootstrap seed refresh.** After self-host
   migration, the v0.6.0+ seed (or whichever was last refreshed
   via v5.49.0's `update-bootstrap-seed.yml`) must support the
   new grammar. If the current seed predates v5.50.0,
   re-trigger the seed-refresh workflow as part of v5.50.0
   release prep.
8. **Te.3.E.7** — **closeout artifacts.** Bump VERSION to 5.50.0;
   CHANGELOG `### Added`; CLAUDE.md release-notes;
   SPEC.md sync; SESSION_REPORT.md. PRE_PHASE_AUDIT.md already
   landed at Te.3.E.0.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.E.0** | HIGH (gate) | Phase 0 audit. Per-shape classification of 737 residuals. Candidate A vs B decision. `to_terse` prototype. Bundle/split sizing. Output: `PRE_PHASE_AUDIT.md`. | 4h |
| **Te.3.E.1** | HIGH | `one_line_arm_other` shorthand. Python parser + `_rewrite_arm_stmt_shorthand` extension. ~80 LOC + ~150 LOC tests. | 1 session |
| **Te.3.E.2** | HIGH | `match_arm_open` multi-line colon form. Python parser grammar + `_indent_to_braces` extension. ~150 LOC + ~200 LOC tests. | 1 session |
| **Te.3.E.3** | HIGH | Formatter `to_terse` extensions. ~80 LOC + ~120 LOC tests. | 0.5 session |
| **Te.3.E.4** | HIGH | C runtime mirror of E.1 + E.2. ~150 LOC C + cross-bootstrap fixture extension. | 1 session |
| **Te.3.E.5** | HIGH (gate) | Self-host source migration in 4 clusters. Stage1 rebuild + goldens + STRICT after each. ~10 modules. | 0.5 session |
| **Te.3.E.6** | MEDIUM | Bootstrap seed refresh (run v5.49.0's `update-bootstrap-seed.yml`). | 0.25 session |
| **Te.3.E.7** | HIGH (gate) | Closeout. VERSION + CHANGELOG + CLAUDE.md + SPEC.md + SESSION_REPORT.md. | 0.5 session |

---

## Phase plan

- **Phase 0** — Te.3.E.0 only. Classify residuals; Candidate A vs B;
  prototype `to_terse` extension; write `PRE_PHASE_AUDIT.md`.
- **Phase 1** — Te.3.E.1 + Te.3.E.2 (Python parser + grammar).
- **Phase 2** — Te.3.E.3 (Python formatter).
- **Phase 3** — Te.3.E.4 (C runtime mirror + cross-bootstrap test).
- **Phase 4** — Te.3.E.5 (self-host source migration in 4 clusters).
- **Phase 5** — Te.3.E.6 (seed refresh; conditional on whether the
  active seed supports v5.50.0 grammar).
- **Phase 6** — Te.3.E.7 (closeout).

Each phase has a STRICT preservation gate after the relevant
edits. Goldens 103/103 at every checkpoint per the v5.48.1
discipline.

---

## Out of scope

- **Block-only arm openers** (`trait`, `impl`, `agent` arms).
  Arm bodies are statement-or-expression contexts; struct/enum
  definitions inside arms are an edge case Phase 0 audit may
  surface as `0` in the residual count, in which case dropped.
- **Arm bodies with `match` inside.** Nested match in the same
  arm-body line was already handled at v5.48.0 Te.3.D for
  stmt-keyword arms; v5.50.0 inherits and extends. If Phase 0
  audit surfaces a regression here, that becomes a v5.50.x patch.
- **Hard removal of `{}`.** v6.0 thesis. v5.50.0 keeps the
  v5.19.0 deprecation warning unchanged for the residuals that
  remain after migration (which should be zero in
  `mapanare/self/*.mn` post-Te.3.E.5).
- **`stdlib/` and `examples/` migration.** Scoped to
  `mapanare/self/*.mn` for v5.50.0; broader sweep is v6.0 PLAN
  input or a separate v5.50.x patch.
- **Borrow checker.** v6.0 thesis.

---

## Risk

1. **LALR grammar ambiguity.** Multi-line arm bodies (Candidate B)
   collide with `Pat => expr` expression-arm form when `expr` is
   a multi-line construct (e.g., struct literal). Mitigation:
   Candidate A (`=>:`) sidesteps this by using a distinct token
   sequence. Phase 0 audit picks the candidate that minimizes
   parser changes; if both candidates are viable, prefer A
   for grammar simplicity.
2. **`one_line_arm_other` semantic drift.** Migrating
   `Pat => { foo(x) }` to `Pat => foo(x)` must lower to identical
   MIR. If the brace form was a statement-arm (call, discard) and
   the colon form is mis-parsed as expression-arm (call, return
   value), behavior changes. Mitigation: cross-bootstrap test
   fixtures explicitly assert byte-identical IR for both forms;
   STRICT 3-stage idempotence catches any drift end-to-end.
3. **C runtime mirror divergence.** The Python and C
   preprocessors must be byte-identical. Te.3.D.4.6 introduced
   the cross-bootstrap test (243/243 byte-identical). v5.50.0
   extends to ~270+ fixtures. Mitigation: run the cross-bootstrap
   suite as a Phase 3 gate before any self-host migration.
4. **STRICT preservation if migration shifts line counts.**
   v5.48.1 explicitly raised the STRICT baseline by +461 lines
   to reflect Te.3.D wiring. v5.50.0 will likely DECREASE the
   line count (colon forms are shorter than brace forms).
   Mitigation: STRICT gate accepts the new lower baseline as the
   v5.50.0 floor; document the delta in CHANGELOG `### Changed`.
5. **Bootstrap seed compat.** If the active seed (refreshed at
   v5.49.0 via `update-bootstrap-seed.yml`) predates the v5.50.0
   grammar, the post-Te.3.E.5 `mnc_all.mn` will segfault the
   seed exactly as v5.48.1's mnc_all.mn segfaults the v0.6.0
   seed today. Mitigation: Te.3.E.6 phase explicitly runs the
   seed-refresh workflow; the new seed is built from current
   sources (post-Te.3.E.5 migration) and supports the new
   grammar by construction.
6. **Out-of-scope shape resurfaces.** Phase 0 audit may surface
   shapes Phase 0 didn't anticipate (e.g., guards on
   `match_arm_open`, generics, etc.). Mitigation: PRE_PHASE_AUDIT
   enumerates ALL residual shapes; if a shape exceeds the LOC
   budget, split to v5.50.x patch.

---

## Success criteria

- ✅ `mnc fmt --to-terse` is a fixed point on every file in
  `mapanare/self/*.mn` (zero diff).
- ✅ Brace counts: `mapanare/self/*.mn` total brace openers ≤ 50
  (down from 1,474 at v5.48.1; remaining = shapes Phase 0
  explicitly deferred to v6.0 or v5.50.x).
- ✅ The v5.19.0 deprecation warning emits zero times when running
  `python scripts/build_stage1.py` against current self-host source.
- ✅ STRICT 3-stage fixed point preserved at the new v5.50.0
  baseline (line count expected to decrease; the streak is
  preserved at the new value, mirroring v5.48.1's +461-line
  baseline shift).
- ✅ Goldens 103/103.
- ✅ Cross-bootstrap fixture suite GREEN (~270+ cases, byte-identical
  Python vs C).
- ✅ `bash scripts/build_from_seed.sh --verify` GREEN end-to-end
  with the post-Te.3.E.6 refreshed seed.
- ✅ `make ci-gates` GREEN; `make lint` clean; `pytest tests/`
  GREEN on Linux + macOS + Windows.
- ✅ CHANGELOG `### Added` entries naming Te.3.E.1 + Te.3.E.2
  surface; `### Changed` entry naming the STRICT baseline shift;
  CLAUDE.md release notes; SPEC.md header re-sync to v5.50.0 cut.

---

## Carry-forward delta

**Closes:**
- ~737 residual `match_arm_open` + `one_line_arm_other` braces in
  `mapanare/self/*.mn` (carry from v5.48.1).
- v5.48.1 SESSION_REPORT note: "9 files retain residuals
  (`match_arm_open` multi-line arm bodies and `one_line_arm_other`
  multi-stmt arm bodies — neither has a v5.48.0 shorthand)" —
  v5.50.0 adds the shorthand both shapes need.
- The "first-party brace surface drops 78%: 6,826 → 1,474"
  metric becomes "drops 99%+: 6,826 → ≤ 50" at v5.50.0 close.

**Inherits to v5.50.x patches:**
- Whatever Phase 0 surfaces that exceeds the LOC budget per
  phase. Worst case: Te.3.E.2 multi-line grammar splits to a
  separate v5.50.1 if Candidate A vs B turns out to need
  more grammar surgery than projected.

**Inherits to v6.0:**
- Hard removal of `{}` (the v5.19.0 plan; soft deprecation
  unchanged at v5.50.0).
- Borrow checker (v6.0 thesis).
- Multi-level alias analysis.
- macOS notarization (carry from v5.33.0 Nu.2).
- Ai.1 `_specialize_fn` body-walk (carry from v5.40.0).
- `stdlib/` / `examples/` brace migration if not folded into a
  v5.50.x patch.

**Aggregate state entering v6.0 (post-v5.50.0):**
- Foundation arc CLOSED.
- Stdlib gap-close arc CLOSED.
- Manifesto arc CLOSED.
- Tensor closeout arc CLOSED.
- Package-system runway CLOSED.
- v5.43.0 lowerer-bug closeout CLOSED at v5.46.0.
- Pre-panel hygiene CLOSED at v5.47.0.
- v5 closeout panel CLOSED at v5.47.5.
- Te.3.D arc CLOSED at v5.48.1.
- Wn.\* arc CLOSED at v5.49.0.
- **Te.3.E arc CLOSED at v5.50.0** (this release).
- 0 HIGH carries; ≤ 2 MEDIUM carries (the structural items
  legitimately deferrable to v6.0); ≤ 4 LOW carries.

---

## Why this is "the real fix" not a workaround

v5.49.0 made the deprecation warning smarter (skip when formatter
is a fixed point). That silenced CI noise but **didn't migrate
anything** — the 737 braces still exist in `mapanare/self/*.mn`,
they're just not noisy anymore. v6.0's hard-removal cut would
have had to surface them via parser errors and force manual
rewrites of every site.

v5.50.0 closes the loop by extending the grammar to the shapes
that need migration, then running the migration. After v5.50.0:

- Brace count in `mapanare/self/*.mn`: 1,474 → ≤ 50
- v6.0 hard-removal cut affects ~50 sites (manageable manual
  cleanup) instead of 737 (would block v6.0 timeline)
- `mnc fmt --to-terse` is a true round-trip-to-fixed-point
- The deprecation warning's "Run `mnc fmt` to migrate" advice
  becomes truthful for every file the user might encounter

This is the v6.0 prerequisite that v5.48.1 documented but
deferred. v5.50.0 lands it before v6.0 PLAN drafts can assume
zero-residual self-host source.
