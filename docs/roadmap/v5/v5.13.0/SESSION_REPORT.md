# v5.13.0 — Session Report

**Status:** SHIPPED (this PR).
**Theme:** Mc.2 — `mnc fmt`, the canonical source formatter.
**Strict 3-stage fixed point:** preserved (1-line drift is
pre-existing from the v5.13.0 version-bump commit, unaffected by the
formatter).
**Goldens:** 66/66.
**Effort:** ~one session.

---

## What shipped

1. **`mapanare/format.py`** — new module. ~70 lines.
   - `format_source(source: str) -> str` — pure, idempotent,
     AST-preserving whitespace canonicalizer.
   - `check_formatted(source: str) -> bool` — thin convenience.
   - Six rules, in order: CRLF/CR → LF; strip trailing whitespace;
     leading tabs → 4 spaces; cap 2+ consecutive blank lines at 1;
     strip leading/trailing blank lines; ensure single trailing
     newline.

2. **`mapanare/cli.py`** — replaced the v5.12.x `_format_mapanare`
   stub (whose docstring lied about operator spacing) with a thin
   wrapper over `mapanare.format.format_source`. Upgraded `cmd_fmt`
   to accept multiple paths, directories (recursive), `--check`,
   and `--stdout`. Default (write in place) is preserved for
   backwards compatibility with `tests/cli/test_cli.py`. Reads files
   in **binary mode** so universal-newline translation cannot mask
   CRLF endings — without this, the CRLF → LF rule would silently
   no-op on platforms where Python's `read_text()` translates
   newlines.

3. **`mapanare/self/main.mn`** — added `fmt` to the native `mnc`
   dispatch. v5.13.0 implementation shells out to `mapanare fmt`
   (Python) per the PLAN's allowance; a future Mc.\* release can
   port `format.py` to `.mn` if the shell-out becomes a measurable
   hot path. Help text updated to mention `mnc fmt`.

4. **`tests/test_format.py`** — new file. ~250 lines.
   - 13 unit rule tests.
   - 6 corpus-parametrized tests across 114 `.mn` files
     (idempotency, AST preservation, parse-regression shape, no CR
     in output, no trailing whitespace, no triple-newline runs,
     single trailing newline).
   - 7 CLI integration tests covering `--check`, `--stdout`,
     directory recursion, and parse-error handling.

5. **`docs/guides/formatter.md`** — user-facing usage guide,
   pre-commit hook example, editor integration notes, contractual
   invariants for tooling.

6. **`docs/roadmap/v5/v5.13.0/STYLE_AUDIT.md`** — Phase 0
   deliverable. Documents what the corpus looks like today (114/114
   4-space indent, 0 trailing whitespace, 2 CRLF outliers) and why
   the conservative ruleset is defensible.

7. **One-time self-format**:
   - `mapanare/self/ast.mn` — CRLF → LF.
   - `mapanare/self/lexer.mn` — CRLF → LF.
   - `mapanare/self/mnc_all.mn` (regenerated artifact) — 10 stripped
     blank lines at module boundaries from `concat_self.py`'s
     output.

   Outside `self/`, no other corpus file needed reformatting — the
   audit confirmed the corpus was already canonical.

---

## How the design decisions landed

### Token-stream over AST-visit

The Phase 0 audit confirmed a token-stream / line-based formatter
was the right architecture for v5.13.0:

- Mapanare's AST drops `//`, `///`, and `/* */` comments. An
  AST-visit formatter would lose them on every round-trip.
- The corpus is already canonical on every measurable axis
  except line endings (114 / 114 4-space indent, 112 / 114 LF).
  There is no structural reformatting *to do*.
- A line-based pass is trivially AST-preserving: it never touches
  non-whitespace bytes, so the parser sees the same tokens.
- It sets up v5.14.0 cleanly. The `--to-terse` rewriter that
  v5.14.0 (Te.1) needs is separate logic that runs *before* the
  whitespace pass — both layers compose cleanly.

The trade-off — v5.13.0 cannot reformat braces, indents, or
expression layout — is acceptable per the PLAN's "conservative
formatting wins" guidance. The v5.20.0+ docket carries the
deferred decisions (configurable line width, import sorting, long-line
wrapping, comment-aware reformatting).

### Binary-mode I/O

Hit a real bug: Python's `Path.read_text()` applies universal-
newline translation by default, so CRLF reads as LF and the
formatter silently no-ops on the very files it's supposed to
canonicalize. Switched the CLI's read/write to `read_bytes()` /
`write_bytes()`. Caught while running `mnc fmt --check
mapanare/self/` — only `mnc_all.mn` reported drift, but
`ast.mn` / `lexer.mn` had CRLF on disk that should have been
flagged. With binary mode, all three are flagged correctly.

### Default writes in place

The PROMPT sketch suggested gofmt-style "print to stdout by
default, `-i` writes" semantics. The existing `cmd_fmt` and the
existing `tests/cli/test_cli.py::TestFmt::test_fmt_command_writes_file`
both assume "writes in place by default." Choosing the gofmt
convention would have been a quiet behavior break in a
"conservative" release that explicitly forbids one. Kept the
existing default; added `--check` and `--stdout` as opt-ins that
match the PLAN's spirit. Future release can flip the default if
desired with explicit migration.

---

## Verification

| Check | Result |
|---|---|
| `pytest tests/test_format.py` | 704 passed, 114 skipped (skips are by-design — non-parsing files only run the regression-shape test) |
| `pytest tests/cli/test_cli.py::TestFmt` | 7 / 7 passed |
| `mnc fmt --check tests/golden/` | exit 0 (clean) |
| `mnc fmt --check mapanare/self/` | exit 0 (clean, after one-time self-format) |
| `mnc fmt --check examples/` | reports 8 pre-existing parse failures; preserved |
| `bash scripts/rebuild.sh golden` | 270s → goldens improved 46/66 → 57/66 vs 2026-04-19 baseline (formatter is neutral; the deltas are unrelated fixes from interim commits) |
| `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | **66 / 66** |
| `bash scripts/verify_fixed_point.sh --keep` | 226,603 lines / 1-line `!"5.13.0"` vs `!"5.11.0"` drift; pre-existing from version-bump commit 538584b, unaffected by formatter |
| `make lint` (black + ruff + mypy on new code) | clean |

The 1-line fixed-point drift was confirmed pre-existing by reverting
to HEAD's pre-formatter state (`git checkout HEAD -- mapanare/self/{ast,lexer,mnc_all}.mn`),
rebuilding stage1, and re-running `verify_fixed_point.sh` — same
1-line drift. The formatter is therefore demonstrably neutral on the
fixed-point property.

---

## What it means for v5.14.0+

Every release in the terseness arc (v5.13–v5.21) layers one
rewrite pass on top of `format_source()`:

- **v5.14.0 Te.1.F** — `--to-terse` mode that rewrites `{}` blocks
  to `:` blocks via AST visit, then runs `format_source` last to
  normalize whitespace.
- **v5.15.0 Te.2** — list/map comprehensions, `|x| body` lambdas,
  one-liner implicit-return shorthand. AST rewrites; `format_source`
  cleans up.
- **v5.16.0 Te.4** — string-interp self-host parity. Lexer/parser
  port; `format_source` is the validation buffer.
- **v5.17.0 Sh.\*** — mechanical `mnc fmt --to-terse` on
  `mapanare/self/*.mn`. The release that this entire arc is built
  to enable. **Highest-risk release in the arc** because the
  rewriter has to be perfect on every line of self-hosted code.
  This is why v5.13.0 ships solid — Sh.\* leans on the corpus
  invariants `tests/test_format.py` enforces.
- **v5.18.0 Mc.1/3/4** — LSP server, `mnc init`, `mnc check`. The
  LSP can call `format_source` directly for "format on save"
  without spawning a subprocess.
- **v5.19.0 Te.3 + Dk.\*** — soft-deprecate `{}` (warning), ship
  Docker images.
- **v5.20.0 Te.5** — struct ergonomics (post-rewrite intentional;
  not auto-migratable).
- **v5.21.0 Te.6** — chained comparisons + small ergonomic wins.

If `format_source` had any AST-altering bug, every release in the
arc would inherit it. v5.13.0 is the single point of failure for
the entire 9-release migration, which is why it ships with nothing
more ambitious than whitespace normalization.

---

## Known limitations / deferred

Tracked here so future releases know where to layer:

- **No re-indentation.** The corpus is already 4-space; v5.13.0
  does not enforce it line-by-line. Will be added in a later
  release once a non-conforming file lands.
- **No brace-style normalization.** Same reasoning — the corpus is
  unanimous on same-line braces.
- **No trailing-comma policy.** The corpus has not converged.
- **No import sorting.** Deferred to v5.20.0+.
- **No long-line wrapping.** Deferred to v5.20.0+.
- **No comment-aware reformatting.** Doc comments, block comments,
  and line comments are preserved verbatim. Wrapping `///` doc
  comments is a v5.20.0+ feature.
- **Native `mnc fmt` shells out to `mapanare fmt`.** Acceptable
  per PLAN; porting to `.mn` is a future Mc.\* if needed.
- **`scripts/concat_self.py` is not formatter-aware.** Each time
  someone runs `python scripts/concat_self.py`, the regenerated
  `mnc_all.mn` will have the 10 extra blank lines at module
  boundaries that v5.13.0 stripped. The fix is one of:
  (a) format `mnc_all.mn` after every concat (`mapanare fmt -i
  mapanare/self/mnc_all.mn`), or (b) teach `concat_self.py` (and
  its bash sibling `concat_self.sh`) to call `format_source`. Not
  blocking — the file parses identically either way and the goldens
  pass — but a future release should pick one of the two fixes.

---

## Closeout checklist

- [x] `STYLE_AUDIT.md` written before implementation.
- [x] `mapanare/format.py` exists and is idempotent on full corpus.
- [x] AST-preservation invariant holds on full corpus (106 / 106
      parseable files).
- [x] `mnc fmt` works in both Python CLI and native `mnc` (shell-out).
- [x] `mnc fmt --check` exits 0 on `tests/golden/` and
      `mapanare/self/`.
- [x] Comments preserved (line / doc / block — all three forms,
      verified by line-based architecture).
- [x] Goldens 66/66 pass.
- [x] Strict 3-stage fixed point preserved (1-line drift is
      pre-existing from the version bump, not the formatter).
- [x] `make lint` clean on new code.
- [x] `docs/guides/formatter.md` exists.
- [x] `docs/roadmap/v5/v5.13.0/STYLE_AUDIT.md` exists.
- [x] `docs/roadmap/v5/v5.13.0/SESSION_REPORT.md` exists (this
      file).
