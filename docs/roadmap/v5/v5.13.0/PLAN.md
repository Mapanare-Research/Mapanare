# v5.13.0 — Mc.2 — `mnc fmt` (the formatter)

**Status:** PLANNING
**Breaking:** No. Formatter is opt-in; existing builds untouched.
**Prerequisite:** v5.12.0 shipped (Windows SDK split, Mc.6 closed).
**Estimated effort:** 8–14h, one or two sessions.

---

## Why this exists

The v5.13–v5.18 arc pivots Mapanare's surface syntax to be terser
than Python — the original "minimal code, same result" thesis. The
hardest sub-problem is migrating the 14k-line self-hosted compiler
(`mapanare/self/*.mn`) from `{}` blocks to the new terse syntax
without breaking goldens or the strict 3-stage fixed point.

The cheapest way to do that is to ship the formatter **first**, while
the language is still purely brace-based. Then in v5.14.0 we extend
fmt with a `--to-terse` mode and the migration is mechanical instead
of manual. Without fmt-first, v5.17.0 (the rewrite) becomes weeks of
hand-editing parser.mn (2,249 lines) and praying.

`mnc fmt` is also overdue on the Mc.* parity docket as a stand-alone
feature: every modern language has a canonical formatter, and
absence of one is one of the larger barriers to writing real
Mapanare code today.

---

## Goal

1. Ship `mnc fmt` as a working, idempotent, AST-preserving formatter
   for `.mn` source.
2. Cover the full corpus: every file in `tests/golden/`,
   `examples/`, and `mapanare/self/` round-trips through fmt cleanly.
3. CLI surface aligns with `gofmt` / `rustfmt` conventions:
   `mnc fmt <path>`, `mnc fmt --check`, `mnc fmt -i` (in-place).
4. Set up the formatter architecture so v5.14.0 can plug in a
   `--to-terse` rewriter without rewriting the formatter core.
5. No semantic changes. fmt(parse(x)).source ≡ semantically(x).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Mc.2.A** | HIGH | Formatter core in `mapanare/format.py`: parse → AST → re-emit canonical formatting. Reuse existing `mapanare/parser.py` and `ast_nodes.py`. | 3–4h |
| **Mc.2.B** | HIGH | CLI integration in `mapanare/cli.py` AND native `mnc` (`mapanare/self/main.mn`). Subcommand: `mnc fmt <path...>`, flags `--check` / `-i`. Glob support for directories. | 1–2h |
| **Mc.2.C** | MEDIUM | Formatting rules: 4-space indent, line width 100 (configurable later), one statement per line, no trailing whitespace, single trailing newline, consistent brace style for now. | 1–2h |
| **Mc.2.D** | HIGH | Idempotency tests: `format(format(x)) == format(x)` on the entire corpus. | 1h |
| **Mc.2.E** | HIGH | Golden corpus: every `tests/golden/*.mn` parses → formats → reparses → matches AST. Track diffs but do not block on cosmetic changes. | 1–2h |
| **Mc.2.F** | HIGH | Self-hosted compiler: `mapanare/self/*.mn` round-trips cleanly. Critical because v5.17.0 will rewrite these files using fmt. | 1–2h |
| **Mc.2.G** | LOW | Pre-commit hook example in `docs/guides/formatter.md`. | 0.5h |

---

## Phase plan

**Phase 0 — Audit current style.** Read all `.mn` files in `tests/golden/`,
`examples/`, `mapanare/self/`. Identify the de-facto rules: indentation,
brace placement, blank-line conventions. The formatter codifies the
existing dominant style; do not impose a new one.

**Phase 1 — Formatter core.** Write `mapanare/format.py`. Pure function:
`format(source: str) -> str`. Internally: parse → AST → emit. Emitter
visits AST nodes and produces canonical formatting.

**Phase 2 — CLI wiring.** Add `cmd_fmt` to `mapanare/cli.py`. Add
`mnc fmt` to native `mnc` (lives in `mapanare/self/main.mn`). Both
support `<path>`, `--check`, `-i`.

**Phase 3 — Idempotency + corpus tests.** New `tests/test_format.py`.
Cases: idempotency on every corpus file; AST-preservation; `--check`
exit code semantics (0 if no changes, 1 if changes needed).

**Phase 4 — Self-hosted round-trip.** Run `mnc fmt --check` on all
10 modules in `mapanare/self/`. Either pass cleanly or commit the
formatted versions and re-validate stage1/2/3 + goldens.

**Phase 5 — Docs + closeout.** `docs/guides/formatter.md` with usage,
pre-commit hook, editor integration notes. Update CLAUDE.md
"Skills" table. Write SESSION_REPORT.md.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Formatting changes break the strict 3-stage fixed point | MEDIUM | Run `verify_fixed_point.sh` after Phase 4; if it breaks, the formatter is producing non-canonical output for self/ — fix before merging. |
| Comments lost on AST round-trip | HIGH | Mapanare AST currently strips comments. Phase 1 must preserve them — either attach to nearest node or use a token-stream pass instead of pure AST. Decision in Phase 0. |
| Formatter becomes opinionated and rejects legal code | LOW | Start conservative: minimal whitespace normalization, no reordering, no rewriting expressions. Aggressive style choices wait for v5.19.0+. |
| Native `mnc fmt` lags Python `mapanare fmt` | LOW | Ship Python version first, native version uses same `mapanare/format.py` logic via FFI or by porting later. |

---

## Out of scope (deferred)

- `--to-terse` migration mode → **v5.14.0 (Te.1)**
- Configurable line width via `.mapanare-fmt` → v5.20.0+
- Sorting imports → v5.20.0+
- Wrapping long lines / breaking long expressions → v5.20.0+
- Comment-aware reformatting (e.g., wrapping doc comments) → v5.20.0+
- VSCode "format on save" extension → separate ecosystem repo

---

## Success criteria

- `mnc fmt --check tests/golden/` exits 0
- `mnc fmt --check mapanare/self/` exits 0 (after one-time
  self-format commit, if needed)
- `format(format(x)) == format(x)` for every corpus file
- Goldens 66/66 pass
- Strict 3-stage fixed point preserved
- `make lint` clean
