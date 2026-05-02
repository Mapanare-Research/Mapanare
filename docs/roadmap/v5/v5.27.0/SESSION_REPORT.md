# v5.27.0 — Session Report — Mc.8 + Mc.9 + Tk.1 — formatter polish

**Date:** 2026-05-02
**Status:** ready, not tagged
**Predecessor:** v5.26.1 (Eu.1..Eu.4 — Eu.\* arc closeout)
**Arc:** **Mc.\* parity arc CLOSED** (12-release closure of v5.13.0
deferrals); **Tk.\*** sub-arc opened and closed in this release.

## Summary

Three formatter / rewriter polish items shipping together because
they all live in `mapanare/format.py` and ship without compiler
edits. Closes:

- **Mc.8** (`--line-length N`) — 12-release carry from v5.13.0.
- **Mc.9** (`--sort-imports`) — 12-release carry from v5.13.0.
- **Tk.1** (`to_terse` empty `#{}` rewriter bug) — 3-release carry
  from v5.24.1 Wd.2.

**Strict 3-stage fixed point preserved by construction at 241,842
lines / 0 diff** (23-release strict streak — same line count as
v5.26.1 because **zero `mapanare/self/*.mn` source edits in
v5.27.0**; the help-text dispatch in `main.mn` already forwards
every argv element verbatim, so no native-side wiring was needed
for the new flags). Goldens **95/95**.

## Phase 0 — design pivot on Mc.8

The PROMPT/PLAN proposed an `wrap_lines(src, width)` rewriter that
would split long lines at clean break points (commas in arg lists,
`|>`, `&&`, `||`, method-call dots). Phase 0 surfaced a
fundamental incompatibility with v5.13.0 Mc.2's **AST-preservation
invariant**:

| Wrap shape attempted | Parser response |
|---|---|
| `foo(a, b,\n    c)` (split arg list at comma) | `Unexpected newline — expected ')'` |
| `x.a()\n    .b()` (split method chain at dot) | `Unexpected dot ('.')` |
| `a\n    && b` (split at `&&`) | `Unexpected and ('&&')` |
| `x\n    \|> f` (split at `\|>`) | `Unexpected gt ('>')` |
| Multi-line list `[\n    1,\n    2\n]` | `Unexpected newline — expected ']'` |
| Multi-line struct/map literal | Same |
| Multi-line param decl `fn x(\n    a: Int\n)` | `Unexpected newline — expected ')', identifier, kw self` |

Mapanare's grammar is **strictly single-line for all expressions**:
newlines are not implicit continuations inside `(`/`[`/`{`/`#{`.
Auto-wrapping would necessarily produce source that fails to parse,
violating the AST-preservation invariant the v5.13.0 Mc.2 release
locks in for every `mnc fmt` flag.

**Decision (after consulting the user):** Mc.8 ships **detect-only**.
The grammar work to add newline-tolerance inside grouping
delimiters is a separate scope (would require parser + bootstrap
mirror work, breaking the "zero compiler edits" v5.27.0 constraint).
A future release that does the grammar lift can revisit
auto-wrapping; v5.27.0 closes the Mc.\* arc honestly by shipping
the detector now.

## Tk.1 — empty `#{}` map literal preservation

**Bug.** `mapanare/format.py::to_terse`'s `endswith("{}")` branch
unconditionally stripped the `{}` and emitted a colon-block opener
plus an indented `pass`. For statement-context openers (`fn empty()
{}`) this is the intended rewrite. For expression-context empty
literals (`let m: Map<String, Int> = #{}`, `let p = Point {}`), the
result was grammatically invalid:

```
let m: Map<String, Int> = #:    ← invalid
    pass
```

The `endswith(" {")` branch (block-opener with body) routes
expression-context openers through a verbatim pre-pass (via
`_find_match_verbatim_lines`); the `endswith("{}")` branch had no
equivalent guard. v5.24.1 Wd.2 surfaced the bug during the SPEC
corpus migration, sidestepped at the time by leaving SPEC §17.1
(`let empty: Map<String, Int> = #{}`) unrewritten and tracking the
fix as a scope-creep guard for v5.27.0+.

**Fix** (`mapanare/format.py:466-474`, ~6 LOC). Add the same
statement-block-opener filter the `endswith(" {")` branch relies on:

```python
if not _looks_like_stmt_block_opener(opener):
    out.append(f"{leading}{content}")
    continue
```

This routes any `... {}`-suffixed line whose left context is not a
statement-block keyword (`fn`, `if`, `while`, `for`, `loop`,
`struct`, `enum`, `match`, `trait`, `agent`, `impl`, etc.) through
verbatim — covering empty map literals, empty struct literals, and
any other expression-context shape.

**Tests** (4 new):
- `tests/test_colon_blocks.py::TestToTerseRules::test_to_terse_preserves_empty_map_literal`
- `tests/test_colon_blocks.py::TestToTerseRules::test_to_terse_empty_map_literal_idempotent`
- `tests/test_colon_blocks.py::TestToTerseRules::test_to_terse_preserves_empty_struct_literal`
- `tests/test_format.py::TestMarkdownRewriter::test_empty_map_literal_preserved_in_fence`

**Falsifiability round-trip** (verified during the session): all 3
unit tests fail on pre-fix `format.py` with the exact pre-fix bug
shape (`let p = Point {}` → `let p = Point:\n    pass\n`); all
3 pass after the 6-LOC fix.

**SPEC.md note.** The PROMPT instructed retiring a "SPEC §17.1
`<!-- preserve-brace -->` marker", but no such marker exists at
§17.1 — the v5.24.1 "manual revert" was simply leaving the line
`let empty: Map<String, Int> = #{}` untouched (no marker
inserted). The single existing `<!-- preserve-brace -->` marker
(SPEC.md line 1060) preserves the §4 brace-style legacy demo
(`fn factorial(n: Int) -> Int { ... }`) and **stays** — that's
intentional preservation of the legacy brace-form syntax for
illustration purposes, unrelated to Tk.1. The end-to-end
proof of fix is that `to_terse_markdown(SPEC.md)` is now
idempotent, the §17.1 empty-map line round-trips verbatim, and
zero spurious `= #:` substrings appear in the output (verified
via a one-shot Python invocation during the session).

## Mc.8 — `--line-length N` (detect-only)

**Surface.** New CLI flag on `mapanare fmt` / `mnc fmt`:

```text
--line-length N    # default 0 = disabled; report lines > N chars on stderr
```

In the default (write) mode, overlong lines are reported as
warnings on stderr but never block. In `--check` mode, the
presence of any overlong line causes a non-zero exit so CI gates
can enforce the ceiling.

**Implementation** (`mapanare/format.py::find_long_lines`, ~30
LOC): pure read-only detector returning `[(line_no, length), ...]`
for every line strictly exceeding `max_length`. `max_length <= 0`
disables the check. Trailing newline does not count. Source is
**never modified**.

**Conservative ruleset (locked):**
- Strict inequality: a line of exactly `max_length` chars is NOT
  flagged. Lines must exceed the limit to fire.
- Tabs count as one character (raw-source counting; the formatter
  normalizes leading tabs to 4 spaces in an earlier pass anyway).
- String literal contents counted as part of the line length —
  the detector does not peek inside strings.
- Line numbers are 1-based.

**Tests** (19 new in `tests/test_format_wrap.py`):
- 14 unit tests covering boundary conditions, off-by-one, line
  numbering, idempotence-via-purity, tab handling, trailing-newline
  exclusion.
- 5 CLI integration tests covering `--line-length 0` silence,
  stderr reporting, `--check` failure on long lines, `--check`
  pass on short lines, and the load-bearing
  source-not-modified assertion.

**Idempotence + AST-preservation:** trivially satisfied by
construction — the detector never modifies source.

## Mc.9 — `--sort-imports`

**Surface.** New CLI flag on `mapanare fmt` / `mnc fmt`:

```text
--sort-imports    # sort contiguous top-level import blocks alphabetically
```

Additive on top of the primary transformer (`format_source` /
`to_terse` / `to_braces` / auto-migration default).

**Implementation** (`mapanare/format.py::sort_imports`, ~50 LOC).
Walks the source line by line; identifies contiguous runs of
top-level `import ...` lines (column-0 only; indented imports are
not reordered); sorts each run alphabetically by full line text;
preserves all non-import lines (blank lines, comments, other
top-level declarations) verbatim.

**Conservative ruleset (locked):**
- Block boundaries are **any** non-import line — including blank
  lines and comments. The user's existing groupings (e.g.
  stdlib / third-party / local separated by blanks) function as
  the de-facto group structure; each group sorts independently.
- Comments inside an import block (`// keep this first`) split the
  surrounding block into sub-blocks. Neither side reorders across
  the comment — keeps adjacency comments attached to their target.
- Indented `import` lines (column > 0) are NOT considered. Only
  top-level imports are sorted.
- Stable sort by full line text (case-sensitive ASCII order).

**AST-preservation.** Mapanare's import resolution does not depend
on source order for the shapes the corpus uses (`import path::sub`,
`import path::sub { items }`). The sort preserves the
`ImportDecl` multiset; `parse(src)` and
`parse(sort_imports(src))` produce ASTs that differ only in
declaration order. Locked by `tests/test_format_imports.py::
TestSortImportsAstPreserving` and the load-bearing corpus check
`test_sort_imports_preserves_self_main_ast`, which sorts the
8-import block in `mapanare/self/main.mn` and asserts the
multiset of `ImportDecl` nodes is preserved.

**Tests** (24 new in `tests/test_format_imports.py`):
- 13 unit tests covering empty source, no-imports, single-import,
  simple block sort, idempotence, already-sorted no-op, blank-line
  group separation, imports-then-code, comment-splits-subblocks,
  indented-import-skip, selector tail (`{ items }`), trailing
  newline preservation, no-trailing-newline pass-through.
- 2 AST-multiset preservation tests (simple + with selectors).
- 3 CLI integration tests (write-in-place, idempotence-via-CLI,
  `--check` flags unsorted).
- 5 parametrized idempotence fixtures.
- 1 corpus check (`mapanare/self/main.mn`).

## Native dispatch

**Zero `mapanare/self/*.mn` source edits.** The existing `fmt`
dispatch arm in `mapanare/self/main.mn:1095-1108` forwards every
argv element verbatim through a generic loop, so `mnc fmt
--line-length 100 file.mn` and `mnc fmt --sort-imports file.mn`
work end-to-end through the native binary without any wiring
changes. The strict 3-stage fixed point is preserved at v5.26.1's
241,842 lines / 0 diff by construction.

The `mnc fmt --help` text was deliberately not updated to mention
the new flags — the goal #5 constraint (zero `.mn` edits) takes
priority. Documentation lives in `docs/guides/formatter.md` (which
was extended in this release).

## Cadence-gate hard fire — acknowledged

v5.27.0 is the v5.24.0 Hy.3 cadence-gate hard-fire target (5+
minor versions since the v5.22.0 panel — last panel was 5
releases ago: v5.22.0 → v5.23.0 → v5.24.0 → v5.24.1 → v5.25.0 →
v5.26.0 → v5.26.1 → v5.27.0 = 7 minors). The
`scripts/check_cadence.py` gate **fires hard** at v5.27.0 HEAD;
this is **expected and informational**.

**Resolution.** The **v5.28.0 RE-PANEL** closes the cadence gap
**1 minor late on purpose**. Bundling formatter polish (Mc.8 +
Mc.9 + Tk.1) with a panel cycle was rejected during PLAN drafting
— formatter work is the wrong scope to mix with a panel review,
which needs a clean pre-panel docs-hygiene sweep
(parallel to v5.21.1 Mc.7's `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`
pattern). v5.28.0 PROMPT will be drafted to address the cadence
gate explicitly and ship the panel cleanly.

## Carry-forward delta

**Closes:**
- **Mc.8** (12-release carry: v5.13.0 → v5.27.0). Detect-only
  scope; auto-wrap deferred to a future release with grammar
  lifting.
- **Mc.9** (12-release carry: v5.13.0 → v5.27.0). Full scope
  shipped.
- **Tk.1** (3-release carry: v5.24.1 → v5.27.0).

**Mc.\* parity arc CLOSED.** Every Mc.\* item from the v5.13.0
parity gap docket is now resolved (Mc.1 LSP / Mc.2 fmt / Mc.3
init / Mc.4 check / Mc.5 emit-wasm rescoped to v6.0 / Mc.6 + Mc.7
docs hygiene / Mc.8 line-length detect-only / Mc.9 sort-imports).

**Out of arc but related:**
- Bigger `to_terse` audit (auto-migration of complex shapes,
  comment realignment, etc.) explicitly out of scope.
- Auto-wrap rewriter rescoped to v5.30.0+ pending grammar work.
- Bootstrap formatter port stays out of scope until v6.0
  borrow-checker work (per v5.13.0 Mc.2 design).

**Inherits to v5.28.0 RE-PANEL:**
- 0 HIGH / 0 MEDIUM / ~3 LOW open in carry-forward docket
  (rolled forward from v5.27.0 PLAN line 154).
- Cadence-gate fire flagged in this report; v5.28.0 PROMPT to
  address it explicitly.

## Source delta

| File | Delta | Notes |
|---|---:|---|
| `mapanare/format.py` | +95 LOC | Tk.1 fix (~6 LOC) + `find_long_lines` (~30 LOC) + `sort_imports` (~50 LOC) + `__all__` extension + helper |
| `mapanare/cli.py` | +30 LOC | `--line-length` + `--sort-imports` argparse wiring + per-file detector wiring |
| `mapanare/self/*.mn` | **0 LOC** | Zero edits — argv forwarding loop already generic |
| `tests/test_colon_blocks.py` | +25 LOC | 3 Tk.1 unit tests |
| `tests/test_format.py` | +18 LOC | 1 Tk.1 markdown test |
| `tests/test_format_wrap.py` | +200 LOC (new file) | 19 Mc.8 tests |
| `tests/test_format_imports.py` | +280 LOC (new file) | 24 Mc.9 tests |
| `docs/guides/formatter.md` | +90 LOC | `--sort-imports` + `--line-length` sections |

**Total Python delta:** ~125 LOC of compiler-side code (~6 / ~30
/ ~50 / ~30 split across the four items). Above the per-fix
30-LOC ceiling at the aggregate level but consistent with the
v5.26.1 Eu.\* pattern of bundling distinct items in one release
when each is small.

## Closeout checklist

- [x] Tk.1 fix landed; falsifiability round-trip documented;
      SPEC §17.1 cleared (no marker existed; the empty map line
      now round-trips through `to_terse_markdown` cleanly).
- [x] Mc.8 detect-only `find_long_lines()` shipped with 19 tests.
- [x] Mc.9 `sort_imports()` shipped with 24 tests including
      AST-multiset preservation on `mapanare/self/main.mn`.
- [x] CLI flags `--line-length`, `--sort-imports` wired in
      `cmd_fmt`.
- [x] `docs/guides/formatter.md` updated with both new sections.
- [x] **Zero** `mapanare/self/*.mn` source edits (goal #5).
- [x] Goldens 95/95 preserved.
- [x] Strict 3-stage fixed point preserved at 241,842 lines / 0
      diff (23-release streak).
- [x] VERSION bumped to 5.27.0.
- [x] CLAUDE.md release-notes entry added; Mc.\* parity arc CLOSED.
- [x] CHANGELOG.md entry added.
- [x] `make lint` clean.
- [x] Cadence-gate fire acknowledged; v5.28.0 RE-PANEL scheduled
      to close the cadence gap one minor late.

## What changed since v5.26.1

| Surface | Change |
|---|---|
| `mapanare fmt --line-length N` | New flag — detect-only long-line reporter on stderr; `--check` makes it a hard fail. |
| `mapanare fmt --sort-imports` | New flag — alphabetical sort within contiguous import blocks. |
| `mapanare fmt --to-terse` | Bug fix — empty `#{}` map literals (and empty struct literals) now survive the rewrite verbatim. |
| `mnc fmt` | All three above flags reach native via existing argv-forwarding (no native-side edits). |
| Goldens | 95/95 preserved (zero compiler edits). |
| Strict fixed point | Preserved at 241,842 lines / 0 diff (zero `.mn` edits). |
