# v5.17.0 Phase 0 — `--to-terse` dry-run survey

**Date:** 2026-04-29
**Status:** Phase 0 complete. Three v5.14.0-era latent bugs fixed
(commits not yet authored). 17/17 modules dry-run cleanly through
`mnc fmt --to-terse` + parse-check. Goldens 80/80. Strict 3-stage
fixed point: 0-line diff (231,957 lines), preserved.
**Working tree:** v5.16.0 HEAD, branch `dev`.

---

## Scope correction up front

The PLAN names 10 modules in `mapanare/self/`. The directory now has
**18 modules** (8 added since the PLAN was drafted): `abi.mn`,
`mir_opt.mn`, `transpiler.mn`, `from_go.mn`, `from_php.mn`,
`from_python.mn`, `from_typescript.mn`, plus `mnc_all.mn` (the
regenerated concatenation, not edited directly). Phase 1 must cover
all 17 hand-edited modules.

Total source lines (excluding `mnc_all.mn`): **28,698**, not 14,000.

---

## Per-module dry-run table — final state (after Sh.A.1 fixes)

`python3 -m mapanare fmt --to-terse --stdout` on each module, output
captured in `/tmp/sh-dry-run-fix8/`. **All 17 modules** produce output
that parses cleanly via `mapanare.parser.parse`.

| Module | Before | After | Δ | % shrink | Parse-check |
|---|---:|---:|---:|---:|:---|
| abi.mn | 94 | 89 | -5 | 5.3% | OK |
| ast.mn | 952 | 760 | -192 | 20.2% | OK |
| lexer.mn | 601 | 533 | -68 | 11.3% | OK |
| emit_llvm_ir.mn | 275 | 224 | -51 | 18.5% | OK |
| mir.mn | 921 | 774 | -147 | 16.0% | OK |
| lower_state.mn | 595 | 509 | -86 | 14.5% | OK |
| parser.mn | 2749 | 2390 | -359 | 13.1% | OK |
| semantic.mn | 2292 | 2002 | -290 | 12.7% | OK |
| lower.mn | 5157 | 4554 | -603 | 11.7% | OK |
| emit_llvm.mn | 6428* | 5782 | -646 | 10.0% | OK |
| main.mn | 1334 | 1137 | -197 | 14.8% | OK |
| mir_opt.mn | 1880 | 1619 | -261 | 13.9% | OK |
| transpiler.mn | 596 | 500 | -96 | 16.1% | OK |
| from_go.mn | 1524 | 1271 | -253 | 16.6% | OK |
| from_php.mn | 1161 | 972 | -189 | 16.3% | OK |
| from_python.mn | 578 | 490 | -88 | 15.2% | OK |
| from_typescript.mn | 1561 | 1311 | -250 | 16.0% | OK |
| **TOTAL** | **28,698** | **24,917** | **-3,781** | **13.2%** | |

`*` `emit_llvm.mn` grew by 4 lines vs the v5.16.0 HEAD due to Sh.A.1's
`}}` re-indent (each `}}` → 2 lines).

The 13.2% mechanical shrink falls short of the PLAN's 30% target.
Phase 2 (comprehension upgrades) and Phase 3 (implicit return) need
to close ~17 more percentage points, or the SESSION_REPORT will need
to revise the target downward.

---

## v5.14.0-era latent bugs fixed in Sh.A.1

Phase 0 dry-run on the v5.16.0 HEAD formatter surfaced three
distinct latent bugs that would have blocked all 11 of 17 modules
with multi-line match arms or expression-context blocks. Per the
PROMPT (`If goldens break: revert that module's changes, file a
v5.14.0 follow-up bug, defer.`), strict reading would have deferred
those modules. We instead applied the small targeted fixes as
v5.17.0 Sh.A.1 because deferring 11 of 17 modules would have lost
nearly all the release's payoff.

### Bug A — `to_terse` corrupts multi-line match arms

`mapanare/format.py::to_terse` rewrote match-arm openers
`Pat => { ... }` to `Pat =>:` (invalid syntax) and orphaned the
trailing `},` closer. Affected every module using multi-line match
arms: `parser.mn`, `semantic.mn`, `lower.mn`, `lower_state.mn`,
`emit_llvm.mn`, `main.mn`, `mir_opt.mn`, `transpiler.mn`, all four
`from_*.mn`.

**Fix.** `to_terse` now detects `match X { ... }` blocks containing
any `Pat => {` multi-line arm body via a pre-pass
(`_find_match_verbatim_lines`) and preserves the entire match in
brace form. Single-line arms (`Pat => expr` or `Pat => { ... }` on
one line) and empty arms (`Pat => {}`) still convert.

### Bug B — `to_terse` corrupts expression-context blocks

`let x = if cond { ... } else { ... }` is an *expression*; the
braces are part of the if-expr grammar. `to_terse` rewrote the
opener to colon form, producing `let x = if cond:` (invalid).
Affected `lower.mn`.

**Fix.** New helper `_looks_like_stmt_block_opener` distinguishes
statement-level openers (`fn`, `if`, `while`, ...) from
expression-context ones. The pre-pass marks
non-statement-block openers as verbatim and finds the matching
brace via `_find_brace_close` (string- and comment-aware
brace counter). Continuations like `} else {` after a verbatim
block are also kept verbatim by propagation through the main loop.

### Bug C — `_indent_to_braces` mishandles multi-level dedent

`_indent_to_braces` (the colon → brace preprocessor) only popped
**one** level on `else:` continuations, even when the dedent
spanned multiple levels. This was a pre-existing bug latent in the
v5.14.0 implementation; it never surfaced for hand-written colon
sources because authors avoided multi-level dedent, but `to_terse`
of brace sources with nested if/else routinely produces it.

Reproducer:

```
fn f(a: Bool, b: Bool) -> Int:
    if a:
        if b:
            return 1
        else:
            return 2
    else:               ← multi-level dedent: -2 levels from prior body
        return 3
```

Pre-fix the brace output had unmatched braces.

**Fix.** Both Python (`mapanare/parser.py::_indent_to_braces`) and
C (`runtime/native/mapanare_core.c::__mn_indent_to_braces`)
continuation handlers now pop nested colon-blocks until the stack
matches the continuation's level, emitting `}` for each inner
block before the outer `} else {`. Mirrored byte-identical via the
existing bootstrap test
(`tests/bootstrap/test_indent_preprocessor.py`).

---

## Source quality cleanup folded into Sh.A.1

`mapanare/self/emit_llvm.mn` had four sites with non-canonical
`}}` (two close braces on one line, inside an `} else { if X { ... }
else { ... }}` pattern where the inner if/else body wasn't indented
further than its parent else). Brace form parses fine because braces
are explicit, but the indent layout doesn't translate to colon
syntax cleanly even with the rewriter's verbatim handling. Fix is a
mechanical re-indent of the 4 sites to canonical 4-space-per-level.
Stage1 build green, goldens 80/80, fixed point 0-diff after the
fix.

---

## Validation status (after Sh.A.1)

| Check | Result |
|---|---|
| All 17 self/ modules `--to-terse` parse-check | ✅ 17/17 |
| `tests/test_format.py` | ✅ 1166 passed, 128 skipped |
| `tests/test_colon_blocks.py` (4 new regression tests added) | ✅ |
| `tests/parser/` | ✅ 416 passed |
| `tests/bootstrap/test_indent_preprocessor.py` (1 new fixture) | ✅ 170 passed |
| Goldens via `mnc-stage1` | ✅ 80/80 |
| Strict 3-stage fixed point | ✅ 0-diff (231,957 lines) |
| `make build-rt` (libmapanare_rt.a regen) | ✅ 5.16.0 baked |
| Full `tests/` sweep (excluding `tests/cli`) | ✅ 7205 passed, 244 skipped, 16 xfailed, 8 failed |
| `black --check` (after `black mapanare/format.py tests/test_colon_blocks.py`) | ✅ |

The 8 full-suite failures are all **pre-existing on v5.16.0 HEAD**
(verified via `git stash`):

- 6 × `tests/bootstrap/test_verification.py::TestCLIIntegration::
  test_run_produces_output[*]` and `test_run_fibonacci_correct` —
  Windows MinGW `gcc.exe` cannot find `cc1` from WSL. Environment
  issue, not a regression.
- 1 × `tests/test_ci.py::TestToolsRunLocally::
  test_struct_registry_gate_passes` — `lower_state.mn::LowerState`
  has 18 fields in source, registry at
  `emit_llvm.mn::build_internal_struct_list` has 17 (missing
  `comp_type_hint`, added in v5.15.1 Cb.5). Should be fixed
  separately; doesn't block Sh.A.1.
- 1 × `tests/test_ci.py::TestToolsRunLocally::test_black_check_passes`
  was caused by my edits and is now fixed by running `black` on the
  two modified Python files.

---

## Commits planned for Sh.A.1

To respect the PROMPT's "never mix categories in a single commit"
rule (so bisect points at exactly one cause if regressions later
surface), the work is split into three commits:

1. **Sh.A.1.A** — `mapanare/format.py` rewriter fix +
   `tests/test_colon_blocks.py` regressions (4 new tests).
2. **Sh.A.1.B** — `mapanare/parser.py::_indent_to_braces` Python
   fix + `runtime/native/mapanare_core.c::__mn_indent_to_braces`
   C mirror + `tests/bootstrap/test_indent_preprocessor.py` new
   fixture.
3. **Sh.A.1.C** — `mapanare/self/emit_llvm.mn` 4-site re-indent
   (no semantic change, IR byte-identical, fixed point preserved).

(`mnc-stage1` and `runtime/native/libmapanare_rt.a` are build
artifacts, not committed.)

---

## Next steps

1. Author the three Sh.A.1 commits.
2. Begin **Phase 1** — per-module `--to-terse` rewrite, dependency
   ordered. Each module is its own commit; each commit is gated on
   stage1 build + goldens + fixed point.
3. Watch the fixed point especially for `parser.mn`, `lower.mn`,
   and `emit_llvm.mn` — these are the largest modules and the
   most likely to surface latent rewriter quirks.
