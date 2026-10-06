# v5.48.1 — Te.3.D.4 / Te.3.D.5 — bootstrap mirror + self-host source migration

**Status:** PLANNING
**Type:** v5.48.0 carry-forward closeout. Lands the C runtime
mirror + self-host source migration that v5.48.0 explicitly
split. **No new language surface.** v5.48.0 already shipped the
Python parser/formatter; v5.48.1 brings the native side to
parity and migrates `mapanare/self/*.mn` to use the new
shorthand so the v5.19.0 brace-deprecation warning goes silent
on stage1 builds.
**Breaking:** No — same parse semantics on both sides; legacy
braces still parse with the v5.19.0 warning unchanged.
**Prerequisite:** v5.48.0 shipped (Python side green, stage1
rebuilt to 5.48.0). v5.48.1 doesn't depend on v5.49.0 (Windows
smoke) — they ship in calendar order but don't conflict
semantically.
**Estimated effort:** 1-2 sessions. Phase 4 is the higher-risk
piece (C-side preprocessor mirror that must match the Python
output byte-identically per the v5.14.1 cross-bootstrap test).
Phase 5 is mechanical formatting + stage1 rebuild + STRICT
3-stage fixed point gate.

---

## Why this exists

v5.48.0's SESSION_REPORT names two carry items explicitly:

- **Te.3.D.4 — bootstrap mirror**: the Python parser at v5.48.0
  accepts `if x: stmt`, `Pat => return x`, `fn name(): stmt`
  etc.; the C runtime preprocessor at
  `runtime/native/mapanare_core.c::__mn_indent_to_braces` does
  not. Stage1 / stage2 / native `mnc` continue to build because
  the self-host source is still in legacy brace form, so the
  preprocessor never has to handle the new shapes. But:
  - `mnc fmt` on a user `.mn` source migrates to the new
    shapes (Python side does this). When that user then runs
    `mnc-stage1 run` on the migrated file, the C preprocessor
    rejects it. The two compilers disagree on syntax surface,
    which is exactly the failure mode the v5.14.1
    cross-bootstrap test
    (`tests/bootstrap/test_indent_preprocessor.py`) was built
    to prevent.
  - The new shorthand cannot land in `mapanare/self/*.mn`
    until the C runtime accepts it (otherwise stage1 cannot
    reparse its own source). Te.3.D.5 is fully gated on
    Te.3.D.4.

- **Te.3.D.5 — internal source migration**: the audit at
  `docs/roadmap/v5/v5.48.0/PRE_PHASE_AUDIT.md` measured **2946
  single-line brace openers** across the 12 modules in
  `mapanare/self/` (excluding `mnc_all.mn`). At v5.48.0 they
  remain in legacy brace form and continue to fire the v5.19.0
  deprecation warning every stage1 build. The point of v5.48.0
  was to make these migratable; v5.48.1 actually migrates them.

After v5.48.1 there is no more first-party brace-form code in
the self-host. The deprecation warning fires only on user
sources that still need migration. v6.0 can flip the warning
to a hard error after v5.48.x soak.

---

## Goals

1. **Te.3.D.4.0** — Phase 0 audit. Re-confirm the v5.48.0
   PRE_PHASE_AUDIT counts at v5.48.1 HEAD (the goldens were
   migrated; the self-host wasn't, so the count should have
   dropped slightly). Identify any new single-line shapes the
   v5.48.0 Python preprocessor accepts that aren't yet in the
   v5.14.1 cross-bootstrap fixture set.
2. **Te.3.D.4.1** — C runtime helpers in
   `runtime/native/mapanare_core.c`: port
   `_split_inline_colon_body`, `_is_single_line_stmt_head`,
   `_rewrite_inline_colon_body`, `_normalize_fn_zero_arg_head`
   to C as `mn_ib_*` static functions. Mirror Python control
   flow byte-for-byte.
3. **Te.3.D.4.2** — Extend `mn_ib_has_colon_blocks` to also
   trigger the slow path for lines whose stripped content
   starts with one of the single-line stmt-keyword prefix hints
   AND contains `:` (mirror of the Python
   `_SINGLE_LINE_PREFIX_HINT` fast-path extension).
4. **Te.3.D.4.3** — Extend `__mn_indent_to_braces` main loop:
   single-line detection in both the continuation branch and
   the non-continuation branch; require `'{' not in content`
   guard; skip `::` namespace operator. Same
   `head + " { " + body + " }"` emission shape as Python; same
   recursive `_rewrite_inline_colon_body` for nested
   single-line bodies; same parent-comma-back-patch behavior;
   no indent_stack push for single-line forms.
5. **Te.3.D.4.4** — New `MN_EXPORT MnString
   __mn_rewrite_arm_stmt_shorthand(MnString source)` mirroring
   the Python `_rewrite_arm_stmt_shorthand`. Same scanner: mask
   strings/chars/`//` comments to spaces in a shadow buffer;
   walk for `=>` positions; for each, check if the body starts
   with a stmt keyword (`return`/`da`/`break`/`sal`/`continue`/
   `sigue`/`pass`); if so, walk until depth-0 `,` or `}` or
   end-of-line and emit `=> { body }`. Skip already-brace forms
   (`=>{`) and word-continuations (`return_value`).
6. **Te.3.D.4.5** — Wire `__mn_rewrite_arm_stmt_shorthand` into
   `mapanare/self/parser.mn::parse` between
   `__mn_indent_to_braces` and `tokenize`. Add `extern "C" fn`
   declaration. Update `mapanare/self/semantic.mn::is_builtin_function`,
   `lower.mn`, `emit_llvm.mn::declare_runtime_fn` if the
   builtin/runtime registration path needs the new symbol
   (search for the existing `__mn_indent_to_braces` registration
   and add `__mn_rewrite_arm_stmt_shorthand` symmetrically).
7. **Te.3.D.4.6** — Cross-bootstrap test extension. Add v5.48.1
   fixtures to `tests/bootstrap/test_indent_preprocessor.py`
   covering: (a) single-line stmt block with each accepted head
   (English + Spanish); (b) single-line continuation
   (`else: stmt`, `else if x: stmt`); (c) single-line arm
   shorthand for each of the 7 stmt keywords; (d) negative
   shapes (struct/enum/match single-line; `<T: Ord>` generic
   should NOT trigger; `X::Y` namespace should NOT trigger).
   Verify Python `_indent_to_braces`+`_rewrite_arm_stmt_shorthand`
   and C `__mn_indent_to_braces`+`__mn_rewrite_arm_stmt_shorthand`
   produce byte-identical output on every fixture.
8. **Te.3.D.5.0** — Pre-migration audit. Walk `mapanare/self/`
   modules; for each, count brace openers per shape; flag any
   shape the v5.48.0 formatter cannot migrate (the
   `one_line_arm_other` 64-case bucket). Decide per file: full
   `mnc fmt` migration; partial migration; defer to v5.48.x.
9. **Te.3.D.5.1** — Module-by-module migration. Run
   `python3 -m mapanare.cli fmt mapanare/self/<module>.mn` on
   each module (12 modules). After each cluster: rebuild stage1
   via `python3 scripts/build_stage1.py`; run
   `python3 scripts/test_native.py --stage1
   mapanare/self/mnc-stage1`; if any golden fails, revert that
   module's migration and split it to v5.48.x.
10. **Te.3.D.5.2** — Regenerate `mnc_all.mn` via the existing
    concat script after the per-module migrations land.
11. **Te.3.D.5.3** — STRICT 3-stage fixed point. Run
    `bash scripts/verify_fixed_point.sh --keep`. STRICT must hit
    at v5.48.1 HEAD's line count. (Line count will change
    relative to v5.48.0's 244,654 — colon shorthand reduces
    every migrated line by the trailing `}`. The new line count
    becomes the v5.48.1 baseline; v5.48.x and v6.x preserve from
    here.)
12. **Te.3.D.6** — Verification. New cross-bootstrap fixtures
    green; goldens 103/103; stage1 rebuilds; stage2 validates;
    STRICT 3-stage fixed point at the new v5.48.1 line count;
    `mnc-stage1 build` of every `.mn` in `mapanare/self/` shows
    **no v5.19.0 brace-deprecation warning** (the migration
    success criterion).
13. **Te.3.D.7** — Closeout. CHANGELOG, CLAUDE.md release notes,
    SPEC.md if any wording needs to drop "Python-side only"
    qualifiers, SESSION_REPORT.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.D.4.0** | HIGH (gate) | **Phase 0 audit.** Re-run `count_user_brace_block_openers` on `mapanare/self/`; confirm shape totals; sample any new edge case that needs cross-bootstrap fixture coverage. Output: `docs/roadmap/v5/v5.48.1/PRE_PHASE_AUDIT.md`. | 1h |
| **Te.3.D.4.1** | HIGH | **C helpers.** Port `_split_inline_colon_body`, `_is_single_line_stmt_head`, `_rewrite_inline_colon_body`, `_normalize_fn_zero_arg_head` to C as `mn_ib_*` statics in `runtime/native/mapanare_core.c`. Mirror Python control flow exactly; including the `::` skip and the `i + 1 < n` guards. | 3h |
| **Te.3.D.4.2** | HIGH | **Extended fast-path.** `mn_ib_has_colon_blocks` walks each line and ALSO triggers when the stripped content begins with one of the single-line prefix hints (`if`, `si`, `while`, `mien`, `for`, `cada`, `fn`, `pub`, `async`, `extern`, `else`, `sino`, `} else`, `} sino`) AND contains `:`. | 1h |
| **Te.3.D.4.3** | HIGH | **Main loop extension.** Single-line detection in both branches of `__mn_indent_to_braces`. Same `<head> { <body> }` emission as Python. Recursive nested rewrite. Comma-back-patch against parent. No stack push. The `'{' not in content` guard mirrors the Python protection. | 3h |
| **Te.3.D.4.4** | HIGH | **`__mn_rewrite_arm_stmt_shorthand`.** New `MN_EXPORT MnString` function mirroring Python; line-based; shadow-string masking; right-to-left replacement. | 3h |
| **Te.3.D.4.5** | HIGH | **Self-host wire-up.** Call new C runtime function from `mapanare/self/parser.mn::parse` after `__mn_indent_to_braces`. Mirror the Python `parse_recovering` order too. Update self-host's runtime-function registration tables symmetrically. | 2h |
| **Te.3.D.4.6** | HIGH (gate) | **Cross-bootstrap test.** Add fixtures to `tests/bootstrap/test_indent_preprocessor.py` covering single-line stmt, continuation, arm shorthand (all 7 keywords), and negative shapes. Test asserts Python and C produce byte-identical output on every fixture. | 2h |
| **Te.3.D.5.0** | HIGH (gate) | **Pre-migration audit.** Per-module shape count for `mapanare/self/`. Identify any shape that doesn't migrate cleanly (esp. `one_line_arm_other` 64-case multi-stmt bodies). Output: section in `PRE_PHASE_AUDIT.md`. | 1h |
| **Te.3.D.5.1** | HIGH | **Module-by-module migration.** Run `mnc fmt` on each `.mn` in `mapanare/self/` (12 modules). After each cluster (3-4 modules), rebuild stage1 + run goldens. Revert any module that breaks goldens; split to v5.48.x with diagnostic. | 4h |
| **Te.3.D.5.2** | HIGH | **`mnc_all.mn` regeneration.** Run the existing concat script. The single-file should reflect post-migration shape. | 0.5h |
| **Te.3.D.5.3** | HIGH (gate) | **STRICT 3-stage fixed point.** `bash scripts/verify_fixed_point.sh --keep`. STRICT must hit at the new v5.48.1 line count (NOT v5.47.0's 244,654 — migration shrinks the line count). The new value becomes the v5.48.x and v6.x baseline. | 1h |
| **Te.3.D.6** | HIGH (gate) | **Verification.** Goldens 103/103; native test runner GREEN; stage2 IR validates with llvm-as; `mnc-stage1 build mapanare/self/parser.mn` (and every other module) shows **zero brace-deprecation warning**. | 2h |
| **Te.3.D.7** | MEDIUM | **Closeout.** CHANGELOG entry; CLAUDE.md release notes (drop the "Python-side only" qualifiers from v5.48.0 entry, replace with "v5.48.1 closes the bootstrap mirror"); SESSION_REPORT. | 1h |

---

## Phase plan

- **Phase 0** — Audit (Te.3.D.4.0 + Te.3.D.5.0). Confirm
  v5.48.0's audit numbers still hold; identify any v5.48.0
  Python preprocessor edge case not yet in cross-bootstrap
  fixtures.
- **Phase 1** — C helpers (Te.3.D.4.1 + 4.2). Pure additions to
  `mapanare_core.c`; no behavioral change yet because they're
  not called.
- **Phase 2** — Main loop extension (Te.3.D.4.3). The
  `__mn_indent_to_braces` body now produces the same brace
  stream as Python for single-line shapes.
- **Phase 3** — `__mn_rewrite_arm_stmt_shorthand`
  (Te.3.D.4.4 + 4.5). New exported function + self-host call.
- **Phase 4** — Cross-bootstrap parity (Te.3.D.4.6). Test
  fixtures and byte-identity gate.
- **Phase 5** — Self-host migration (Te.3.D.5.0 + 5.1 + 5.2 +
  5.3). Module-by-module `mnc fmt`, rebuilds, STRICT.
- **Phase 6** — Final verification (Te.3.D.6).
- **Phase 7** — Closeout artifacts (Te.3.D.7).

---

## Risk

1. **C-side preprocessor parity drift.** The two preprocessors
   must produce byte-identical output on every fixture. Easy
   to introduce off-by-one in indent-handling or comma-back-
   patch logic. Mitigation: cross-bootstrap test (Te.3.D.4.6)
   as the oracle; do not move to Phase 5 until Phase 4 is
   green.
2. **Self-host migration breaks goldens.** Some `mapanare/self/`
   line shape may rely on a quirk the new shorthand changes.
   Mitigation: module-by-module migration with rebuild-after-
   each-cluster; revert + split if any cluster fails goldens.
3. **STRICT 3-stage fixed point divergence.** The new line
   count is the v5.48.1 baseline; if `mnc_all.mn` regeneration
   produces a different line count than the per-module sum,
   STRICT can fail spuriously. Mitigation: regenerate
   `mnc_all.mn` exactly once after all migrations, then run
   STRICT.
4. **`one_line_arm_other` (64 cases) cannot migrate.** Multi-
   stmt arm bodies have no shorthand in v5.48.0. Mitigation:
   leave those in brace form; they continue to warn but the
   warning count drops from ~6826 to ~70 in `mapanare/self/`.
   v6.0 grammar may revisit.
5. **Cross-bootstrap test fixtures need shape coverage**, not
   raw quantity. The test passes when every fixture matches
   byte-for-byte; missing a shape means a v5.48.2 follow-up.
   Mitigation: enumerate shapes from PRE_PHASE_AUDIT and
   v5.48.0 test cases; one fixture per shape.

---

## Success criteria

- C runtime accepts every single-line shape v5.48.0's Python
  parser accepts.
- Cross-bootstrap test
  (`tests/bootstrap/test_indent_preprocessor.py`) green for
  every existing fixture and every new v5.48.1 fixture.
- `mapanare/self/*.mn` migrated; stage1 build emits ZERO
  v5.19.0 brace-deprecation warnings on first-party self-host
  source.
- Goldens 103/103.
- Stage2 IR validates with llvm-as.
- STRICT 3-stage fixed point hits at the new v5.48.1 line
  count; v5.48.x onward preserves from here.
- `mnc_all.mn` reflects the post-migration shape.

---

## Carry-forward delta

**Closes now:**

- The Python/C preprocessor surface gap that v5.48.0 explicitly
  split.
- The first-party brace-deprecation warning flood on stage1
  builds (drops from ~6826 to ~70 in `mapanare/self/`).
- The 51-release strict-fixed-point streak rebases to a new
  (smaller) line count for v5.48.x onward.

**Leaves for v5.48.2 / v6.0:**

- The 64 `one_line_arm_other` multi-stmt arm bodies in
  `mapanare/self/` that have no shorthand in v5.48.0. v6.0
  grammar may add a multi-stmt single-line form, OR these
  stay in brace form until v6.0 hard removal.
- v6.0 hard removal of brace parsing remains the v6.0 PLAN
  input it has been since v5.19.0.
- stdlib (`stdlib/**/*.mn`) migration: stretch goal — the
  formatter handles it, but stdlib changes ride a separate
  cadence. Recommended as a v5.48.x bulk-fmt commit if there
  is appetite, otherwise defer.
