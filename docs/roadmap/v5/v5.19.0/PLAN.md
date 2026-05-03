# v5.19.0 — Te.3 — deprecate `{}` + finish the terseness arc

**Status:** SHIPPED (Te.3.A/B/C/D + golden corpus migration).
**Scope split (executed 2026-04-30):** Original PLAN bundled Te.3
+ Dk.* (Docker images). Mid-execution split: v5.19.0 ships Te.3
as a clean closeout of the v5.13–v5.20 terseness arc; **Dk.* moves
to v5.19.1** so v5.19.0 isn't gated on multi-hour Docker image
work. The v5.19.1 PLAN inherits the locked design decisions from
`DOCKER_DESIGN.md` in this folder.
**Breaking:** Soft-breaking. `{}` syntax still parses but emits a
deprecation warning. Hard removal scheduled for v6.0.
**Prerequisite:** v5.18.0 shipped (LSP + init + check). Self-hosted
compiler in terse syntax (v5.17.0). `mnc fmt --to-terse` available
(v5.14.0).
**Actual effort:** ~4h. Te.3 was the small piece; the work that
made it ship-quality was the formatter polish (Spanish keyword
aliases, `impl<T>` generics) needed to migrate the golden corpus.

---

## Why this exists

This release is the closeout of the terse-syntax arc.

**Te.3** — formally deprecate brace syntax. The self-hosted
compiler is already terse (v5.17.0), all examples and docs are
terse (v5.17.0/v5.18.0), and the golden corpus is now terse too
(this release). The only `{}`-style code left in the wild is
downstream user code. Deprecation warning + automatic fmt
migration gives users a clean path forward.

**Dk.*** (moved to v5.19.1) — Docker images. The PLAN originally
bundled Docker with Te.3 because both targeted "polish for
newcomers." Mid-execution we found that the Te.3 deprecation
release needs the golden corpus migrated and surfaced two
formatter gaps (Spanish keyword aliases + `impl<T>` generics)
that block downstream user migration. Closing those was the right
v5.19.0 scope. The Docker arc is meaningful work in its own right
(builder image, runtime image, `mnc init --docker`, GHCR publish
workflow, smoke tests) and ships as v5.19.1 with its own design
locked in `DOCKER_DESIGN.md`.

---

## Goal (v5.19.0 — shipped)

1. Brace-style blocks emit a deprecation warning at parse time.
   Default: warning to stderr per file with `{}` syntax. Suppress
   with `MAPANARE_NO_BRACE_WARNING=1`. **Done.**
2. `mnc fmt` with no flags auto-migrates `{}` to colon syntax for
   `.mn` files containing user-written brace blocks.
   `--keep-braces` opts back into v5.13.0 whitespace-only behavior.
   **Done.**
3. Formatter recognizes Spanish keyword aliases (`si`, `mien`,
   `cada`, `tipo`, `modo`, `way`) and generic-prefixed openers
   (`impl<T>`) so `mnc fmt --to-terse` can migrate downstream code
   that uses these. **Done.**
4. `tests/golden/*.mn` corpus (80 files) migrated from brace to
   colon style via the auto-migrate default. **Done.**

## Goal (v5.19.1 — Docker, separate release)

5. Pre-built Docker images published to GHCR on release tag:
   - `ghcr.io/mapanare-research/mapanare-builder:5.19.1` + `:latest`
   - `ghcr.io/mapanare-research/mapanare-runtime:5.19.1` + `:latest`
6. `mnc init --docker` scaffolds a multi-stage `Dockerfile` and
   `.dockerignore` in a new project.
7. Docs at `docs/guides/docker.md` covering: builder image usage,
   multi-stage app pattern, image sizes, FROM scratch caveats.
8. CI workflow `publish-docker.yml` that builds + pushes images on
   release tag.

See `docs/roadmap/v5/v5.19.1/PLAN.md` for the Docker arc detail.

---

## Items (v5.19.0 — shipped)

| ID | Severity | Description | Effort | Status |
|---|---|---|---|---|
| **Te.3.A** | MEDIUM | Parser emits brace-deprecation warning at parse time. Once per file, not once per block. Detected before `_indent_to_braces` so colon-form is silent. | 1h | DONE |
| **Te.3.B** | MEDIUM | `mnc fmt` (no flag) auto-converts `{}` → `:` per file when user braces present. `--keep-braces` opts out. Redundant warning suppressed during fmt's own parse-validation. | 1h | DONE |
| **Te.3.C** | LOW | `MAPANARE_NO_BRACE_WARNING=1` env var suppresses the warning. | 0.5h | DONE |
| **Te.3.D** | MEDIUM | Migrate `tests/golden/*.mn` (80 files) to colon syntax. Documents and examples were already terse from v5.17.0/v5.18.0. | 1h | DONE |
| **Te.3.E** (added mid-execution) | MEDIUM | Formatter polish: extend `_STMT_BLOCK_KEYWORDS` with Spanish aliases (`si`, `mien`, `cada`, `tipo`, `modo`, `way`); recognize `impl<T>` generic prefix. Without these, the corpus migration would have left 23 residual brace blocks in 13 files, and downstream user code with mixed-language surface would be stuck after `mnc fmt`. | 1.5h | DONE |
| Dk.* (moved to v5.19.1) | — | Builder + runtime images, `mnc init --docker`, GHCR publish workflow, smoke test. See `docs/roadmap/v5/v5.19.1/PLAN.md`. | 14–18h | DEFERRED |

---

## Phase plan (executed 2026-04-30)

**Phase 0 — Te.3 detection architecture + Docker design lock.**
Wrote `DOCKER_DESIGN.md`. Two key locks:

- **Te.3 detection** runs on the original source **before**
  `_indent_to_braces`, since the preprocessor converts every
  colon-block into brace form before the Lark parser sees it.
  A transformer hook would false-positive on every block.
  Detection scans for lines ending in `{` while tracking string
  state, comments, and `#{` map-literal openers.
- **Docker** locked to GHCR (`ghcr.io/mapanare-research/...`),
  amd64-only, `debian:bookworm-slim` base, two independent images.
  Implementation moved to v5.19.1 — see `DOCKER_DESIGN.md` and
  `docs/roadmap/v5/v5.19.1/PLAN.md`.

**Phase 1 — Te.3.A/B/C.** Parser hook + cmd_fmt auto-migration +
env var suppression. New tests in `tests/test_brace_deprecation.py`
(23/23). Existing `tests/test_format.py` updated for the new
default (4 tests gained `--keep-braces`).

**Phase 1.5 — Te.3.D + Te.3.E.** Migrating the golden corpus
revealed three residual patterns the formatter couldn't handle:
Spanish keyword aliases (`si`/`sino` if-else chains, `tipo` struct
definitions), and `impl<T>` generic-prefix openers. Patched
`_STMT_BLOCK_KEYWORDS`, `_COMMA_BODY_OPENERS`, and
`_looks_like_stmt_block_opener` in `mapanare/format.py`. Re-ran
`mnc fmt tests/golden/`: 80/80 files migrated, 0 residual user
braces. **Native goldens 80/80** through `mnc-stage1` against the
migrated corpus.

**Phase 2–7** — moved to v5.19.1.

---

## Risk register (Te.3 portion — all resolved)

| Risk | Likelihood | Resolution |
|---|---|---|
| Te.3 brace warning floods CI logs for projects mid-migration | MEDIUM | `MAPANARE_NO_BRACE_WARNING=1` env var. To be documented in CHANGELOG migration notes at v5.19.0 closeout. |
| Auto-fmt `{}`→`:` on save surprises users running `mnc fmt --check` | MEDIUM | `mnc fmt --check` exits 1 if `{}` blocks present. Documented as the migration prompt. `--keep-braces` is the opt-out for users mid-migration. |
| Detection logic false-positives on multi-line struct literals | LOW | False positives produce one stderr warning line; bounded. Vanishingly rare in canonical style. |
| Formatter can't migrate user code with Spanish keywords | MEDIUM | Surfaced during Phase 1.5 corpus migration. Resolved by Te.3.E formatter polish (added Spanish aliases + `impl<T>` generic prefix). |

Docker risk register lives in `docs/roadmap/v5/v5.19.1/PLAN.md`.

---

## Out of scope (deferred)

- Hard removal of `{}` syntax → **v6.0** (alongside borrow checker)
- Docker arc (Dk.1–Dk.6) → **v5.19.1** (separate release, design
  locked here, implementation tracked in
  `docs/roadmap/v5/v5.19.1/PLAN.md`)

---

## Success criteria (v5.19.0 — met)

- `{}`-style code parses with one deprecation warning per file ✓
- `mnc fmt` auto-converts `{}`→`:` ✓
- `mnc fmt --check` flags `{}` files as needing migration ✓
- `MAPANARE_NO_BRACE_WARNING=1` suppresses warning ✓
- `tests/golden/*.mn` migrated to colon syntax (80/80) ✓
- Native goldens 80/80 through `mnc-stage1` against migrated corpus ✓
- 23 new tests in `tests/test_brace_deprecation.py`, all passing ✓
- Formatter handles Spanish keyword aliases + `impl<T>` generics ✓
