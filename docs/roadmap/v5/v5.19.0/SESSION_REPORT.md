# v5.19.0 — Te.3 — brace-block soft deprecation + closeout of the terseness arc

**Status:** SHIPPED.
**Scope:** Te.3.A / Te.3.B / Te.3.C / Te.3.D / Te.3.E.
**Scope split:** Dk.\* (Docker images) moved mid-execution to
v5.19.1. See `DOCKER_DESIGN.md` for the locked design that landed
intact at v5.19.1.
**Breaking:** Soft-breaking — `{}` still parses; emits a parse-time
deprecation warning. Hard removal scheduled for v6.0.
**Backfilled:** This SESSION_REPORT was written retroactively at
v5.23.0 (RC.11) — the original release shipped at fba8521 + db32bd4
without an SR file. Source material: `PLAN.md`, `PROMPT.md`,
`DOCKER_DESIGN.md`, and the v5.19.0 commits (db32bd4, fba8521,
6adfee7).

---

## Why this exists

The headline closeout of the v5.13–v5.20 terseness arc. By v5.18.0
the self-hosted compiler, all examples, all docs, and the SPEC were
already in terse colon-block syntax. The only `{}`-style code left
in the wild was downstream user code and the golden corpus. Te.3
formally deprecates braces, ships an auto-migration path via
`mnc fmt`, and migrates the golden corpus to colon-form.

The original v5.19.0 PLAN bundled Te.3 with Dk.\* (Docker images);
the scope split happened at commit 6adfee7 once mid-execution
surfaced two unrelated formatter gaps (Te.3.E) that needed scope
to close. Dk.\* shipped clean at v5.19.1.

---

## What landed

### Te.3.A — parse-time deprecation warning

New `count_user_brace_block_openers()` in `mapanare/parser.py` runs
on the original source **before** `_indent_to_braces` (the
preprocessor that converts colon-form to brace-form internally).
This ordering is load-bearing — running detection after the
preprocessor would false-positive on every block, including
converted-from-colon ones.

Detection scans for lines ending in `{` while tracking string
state, comment lines, and `#{` map-literal openers. Wired into
both `parse()` and `parse_recovering()`.

Warning shape (one stderr line per file, stable wording for CI
grep):

```
warning: <path>: uses deprecated {}-block syntax (N occurrence(s)).
Run `mnc fmt <path>` to migrate. Hard removal in v6.0.
```

### Te.3.B — `mnc fmt` auto-migration default

`cmd_fmt` now picks per-file: if a file contains user-written
brace blocks, route through `to_terse` instead of `format_source`.
New `--keep-braces` flag opts back into v5.13.0 whitespace-only
behavior. The redundant deprecation warning is suppressed during
fmt's own parse-validation step (`MAPANARE_NO_BRACE_WARNING`
toggled around the parse call) so users running
`mnc fmt myfile.mn` don't see the migration hint while migrating.

### Te.3.C — env-var opt-out

`MAPANARE_NO_BRACE_WARNING=1` suppresses the deprecation warning
unconditionally. Targeted at downstream CI that wants to defer
migration without the noise floor.

### Te.3.D — golden corpus migration (commit db32bd4)

Mechanical rewrite via `mnc fmt tests/golden/` (the new
auto-migrate default from Te.3.B). All 80 golden files migrated;
0 residual user-written brace blocks. Total source shrink ~199
lines from dropped closing `}`s.

Load-bearing for the deprecation contract: shipping a release
that warns about brace syntax while the test corpus is still
brace-form would be incoherent. The corpus also doubles as a
sample gallery — downstream users browsing `tests/golden/` now
see the canonical terse style.

The migration is mechanical: `--to-terse` is colon-equivalent at
the AST level, so MIR / IR shape is conserved by construction.
Native goldens 80/80 pass through `mnc-stage1` against the
migrated corpus.

`BENCHMARKS-linux.md`, `BENCHMARKS.md`, and `HISTORY.jsonl` are
auto-regenerated artifacts from
`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
running against the migrated corpus — they record per-test
source-line shrink (e.g. `04_if_else: 11L → 6L`,
`06_struct: 12L → 7L`, `29_generic_impl: 24L → 16L`) and roll
forward the timing baseline.

`tests/test_format.py::test_check_clean_corpus_exits_zero` now
uses the bare `mnc fmt --check` (not `--keep-braces`) since the
corpus is canonical colon-form.

### Te.3.E — formatter polish (added mid-execution)

Surfaced during the golden-corpus migration: 13 files / 23 brace
openers refused to convert to colon. Three patterns:

1. Spanish keyword aliases: `si`, `mien`, `cada`, `tipo`, `modo`,
   `way`.
2. Generic-prefixed openers: `impl<T>`.
3. Corresponding comma-body openers: `tipo `, `modo `, `way `.

Without these patches, downstream user code with mixed-language
surface or generic impls would be stuck after running
`mnc fmt --to-terse`. `_STMT_BLOCK_KEYWORDS`, `_COMMA_BODY_OPENERS`,
and `_looks_like_stmt_block_opener` were extended; the latter now
matches `kw + "<"` in addition to space and paren.

---

## Tests

- `tests/test_brace_deprecation.py` — 23 cases covering detection
  edge-cases (string contents, line comments, map literals,
  escaped quotes), warning emission shape, env var suppression,
  fmt auto-migration, `--keep-braces` opt-out, and mutual-
  exclusion validation.
- `tests/test_format.py` — 4 pre-existing TestCli cases gained
  `--keep-braces` (they tested v5.13.0's whitespace-only default,
  which is now opt-in). 788/788 format tests pass.
- 117/117 LSP tests pass.
- 252/252 parser/cli tests pass.

Broad pytest sweep across 16 dirs: 2964 passed (1 pre-existing
unrelated failure).

---

## Verification

- Native goldens **80/80** through `mnc-stage1` against the
  migrated corpus.
- Strict 3-stage fixed point preserved by construction (Te.3 is
  surface syntax + formatter; no compiler logic edits in
  `mapanare/self/*.mn`).
- `make lint` clean.
- `bash scripts/build_from_seed.sh` clean.

---

## Scope split rationale

The original v5.19.0 PLAN bundled Te.3 with Dk.\*. Mid-execution
(commit 6adfee7) the split was made because:

1. Te.3.E — the formatter polish that surfaced during corpus
   migration — added scope that wasn't in the original PLAN.
2. Te.3 was already a clean closeout of the v5.13–v5.20 terseness
   arc; bundling Docker work would dilute that thesis.
3. Dk.\* is meaningful work on its own (builder image + runtime
   image + `mnc init --docker` + GHCR publish workflow + smoke
   tests) and the locked design in `DOCKER_DESIGN.md` was clean
   enough to ship as a standalone v5.19.1 release.

The v5.19.1 SR records the Dk.\* execution and design amendments
applied during that release.

---

## Carry-forward into the v5.20+ arc

Te.3's soft deprecation lives until v6.0 (hard removal). The
v5.19.0 release explicitly does NOT touch:

- Bootstrap mirror of the colon-block preprocessor (already
  shipped at v5.14.1 B.5/B.6).
- Single-line `if x: y` shape — explicitly rescoped to v6.0 at
  v5.21.1 H.4 (Decision-1 Path B).
- Te.3 hollow-surface (single-line `{...}` not detected as
  user-brace; `mnc-stage1` has no brace deprecation logic at
  all). Surfaced by the v5.22.0 panel; closes at v5.23.2.

---

## Files touched

- `mapanare/parser.py` — `count_user_brace_block_openers`,
  warning emission, env-var gate.
- `mapanare/format.py` — `to_terse` driver, `_STMT_BLOCK_KEYWORDS`,
  `_COMMA_BODY_OPENERS`, `_looks_like_stmt_block_opener`.
- `mapanare/cli.py` — `cmd_fmt` auto-migration default,
  `--keep-braces` flag.
- `tests/test_brace_deprecation.py` — new (23 cases).
- `tests/test_format.py` — `--keep-braces` propagation in 4
  existing TestCli cases.
- `tests/golden/*.mn` — 80 files migrated to colon syntax
  (commit db32bd4).
- `tests/golden/BENCHMARKS-linux.md`,
  `tests/golden/BENCHMARKS.md`, `tests/golden/HISTORY.jsonl` —
  regenerated.

---

## Commits

- `6adfee7` — design: scope split (Te.3 here, Dk.\* moved to v5.19.1)
- `fba8521` — Te.3.A/B/C/E: brace deprecation + fmt auto-migration + formatter polish
- `db32bd4` — Te.3.D: migrate `tests/golden/` to colon syntax
