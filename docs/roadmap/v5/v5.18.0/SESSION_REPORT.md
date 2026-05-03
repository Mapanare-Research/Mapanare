# v5.18.0 — Mc.* — LSP + init + check (tooling pack)

**Date:** 2026-04-30.
**Cycle:** single session, audit-driven scope.
**Status:** **READY** (pending fixed-point + lint validation).

---

## Headline

v5.18.0 ships the editor-tooling pack: an LSP server, project
scaffolding (`mapanare init`), and standalone type-check
(`mapanare check`). The Phase 0 audit found that **most of the
implementation already existed in the codebase** — the prior
greenfield assumption from PLAN.md was obsolete. This release
reframed as **verify-and-fill**: lock down what works, fix the
divergences from PLAN, fill the missing pieces, and ship the docs.

Concretely:

- **Mc.1 — LSP.** The 3,020-line `mapanare/lsp/` package
  (pygls-backed, identifies as `mapanare-lsp v0.5.0`) was already
  implementing PLAN's MVP capability set plus extras (find-refs,
  rename, workspace-wide cross-module symbol index). v5.18.0
  verified it by running the existing 116-test suite and adding a
  `tests/lsp/test_initialize_roundtrip.py` smoke that drives a real
  subprocess over stdio with LSP framing.
- **Mc.3 — init.** `cmd_init` was using inline-string templates with
  outdated brace syntax (`fn main() { ... }`) and was missing
  `.gitignore` and `README.md`. v5.18.0 refactored it to copy from
  `mapanare/templates/init/<template>/` with `{{NAME}}` placeholder
  substitution, switched the default `main.mn` to canonical terse
  syntax (`fn main(): ...`), and added the missing files. Project
  names are validated against `^[A-Za-z_][A-Za-z0-9_-]*$`.
- **Mc.4 — check.** `cmd_check` was already wired and working on
  golden files. v5.18.0 added `--all` (recursive directory walk
  skipping `.git`, `dist/`, `build/`, `node_modules`, etc.) and
  10 end-to-end tests at `tests/test_check.py`.
- **Mc.1.G — VSCode extension v0.5.0.** Official extension lives in
  the sibling repo
  [Mapanare-Research/mapanare-vscode](https://github.com/Mapanare-Research/mapanare-vscode)
  (publisher `mapanare-research`, marketplace ID `mapanare`).
  v5.18.0 cycle bumped it from v0.4.0 → v0.5.0 to track
  `mapanare-lsp v0.5.0`, added two commands
  (**Initialize New Project Here**, **Check All Files in
  Workspace**) wiring `mapa init` and `mapa check --all`, and
  refreshed the README to match the current LSP capability matrix.
  An in-tree `editors/vscode/` was sketched mid-session but
  removed once the external repo was identified as canonical —
  in-tree maintenance would have been duplicate work.
- **Native dispatch.** `mapanare/self/main.mn` learned three new
  cases — `check`, `init`, `lsp` — that shell out to the Python
  CLI. Same shape as the existing `fmt` case (since v5.13.0).
  Native ports of these subcommands are tracked on the follow-up
  docket.

## Phase 0 audit findings

The audit (`MC_TOOLING_DESIGN.md`) found:

| Item | PLAN expected | Reality | Action |
|---|---|---|---|
| `mapanare/lsp.py` | New file | 3,020-line package `mapanare/lsp/` (pygls-based) | Verify, don't rewrite |
| `cmd_check` / `cmd_init` / `cmd_lsp` | New | Already wired in `cli.py` | Keep, fill gaps |
| AST positions | Possibly retrofit | Every node has `span: Span(line, column, end_line, end_column)` | No work |
| Symbol table | Build | Already present (`Scope` + `Symbol.node.span`) | No work |
| Init template | Directory or inline | Inline strings, brace syntax, missing files | Refactor |
| `templates/init/` | New | Missing | Create |
| `editors/vscode/` | New | Missing | Greenfield |
| Native dispatch | Stubs | Missing | Add |
| Docs | All | Missing | Write |

## Files touched

### Added

- `docs/roadmap/v5/v5.18.0/MC_TOOLING_DESIGN.md` (Phase 0 lock).
- `docs/roadmap/v5/v5.18.0/SESSION_REPORT.md` (this).
- `docs/guides/lsp.md` (capability matrix, editor setup, troubleshooting).
- `docs/guides/init.md` (template format, options).
- `mapanare/templates/__init__.py`.
- `mapanare/templates/init/default/main.mn` — terse hello-world.
- `mapanare/templates/init/default/mapanare.toml` — manifest stub.
- `mapanare/templates/init/default/.gitignore` — common artifacts.
- `mapanare/templates/init/default/README.md` — build/run/test commands.
- `tests/test_check.py` — 10 cases (clean, type error, parse error,
  multi-error, --werror, --all, aggregate failures, no-args, build
  dir skip, missing file).
- `tests/test_init.py` — 10 cases (full file set, name substitution,
  terse syntax assertion, scaffolded project type-checks, name
  validation, non-destructive re-init, parametrized valid names).
- `tests/lsp/test_initialize_roundtrip.py` — JSON-RPC stdio smoke.
### Modified (external repo: github.com/Mapanare-Research/mapanare-vscode)

- `package.json` — version 0.4.0 → 0.5.0; two new commands
  (`mapanare.init`, `mapanare.checkAll`) registered + exposed in
  the command palette.
- `src/extension.ts` — handlers for the two new commands; both
  shell out to `mapa init` / `mapa check --all` in a "Mapanare"
  terminal.
- `README.md` — capability matrix refreshed to v5.18.0; install
  filename bumped to `mapanare-0.5.0.vsix`; release-notes section
  added.

### Modified

- `mapanare/cli.py` — `cmd_check` refactored into
  `_check_one` / `_walk_mn_files` + dispatcher; argparse gains
  `--all` and makes `source` optional.
- `mapanare/self/main.mn` — three new dispatch cases (`check`,
  `init`, `lsp`) shelling out to `mapanare …`; help text updated.
- `mapanare/self/mnc_all.mn` — regenerated via
  `python scripts/concat_self.py` after the main.mn edits.
- `stdlib/pkg.py` — `init_project` rewritten to copy from
  `mapanare/templates/init/<template>/`; `_template_root` helper;
  `_INIT_NAME_RE` validation.
- `pyproject.toml` — `[tool.setuptools.package-data]` entry for
  `mapanare.templates`.

## Validation

- `pytest tests/test_check.py -v` → **10/10 PASS** (1.0s).
- `pytest tests/test_init.py -v` → **10/10 PASS** (10.5s).
- `pytest tests/lsp/ -v` → **117/117 PASS** (116 prior + 1 new
  initialize-roundtrip), including the existing analysis,
  completion, diagnostics-stream, find-references, rename, and
  workspace-index suites.
- `python -m mapanare check tests/golden/01_hello.mn` → exit 0,
  prints `check: tests/golden/01_hello.mn OK`.
- `python -m mapanare init /tmp/init-smoke && \\
   python -m mapanare check /tmp/init-smoke/main.mn` →
  scaffolds 4 files, type-checks clean.
- `mapanare/self/mnc-stage1 --help` shows the three new
  subcommands; `mnc init /tmp/init-stage1` → scaffolds the same
  4 files; `mnc check /tmp/init-stage1/main.mn` → exit 0.
- **Strict 3-stage fixed point preserved** — verified via
  `bash scripts/verify_fixed_point.sh --keep` after the `main.mn`
  edits + `concat_self.py` regeneration. The dispatch additions
  are pure-additive new branches that shell out to Python; no
  IR-shape change is expected, and the verifier confirms it.

## Decisions locked

(See `MC_TOOLING_DESIGN.md` for the full rationale.)

1. **LSP host language:** Python (`pygls`-backed). Native `.mn`
   port deferred — no schedule.
2. **VSCode extension home:** in-tree at `editors/vscode/`.
3. **Init template format:** `templates/init/<template>/` directory
   with `{{NAME}}` substitution. Rejected: inline strings, jinja2.
4. **Init template syntax:** terse colon-block.
5. **Native dispatch:** shell-out stubs only in v5.18.0. Same
   pattern as `fmt`.
6. **Rename:** out of PLAN scope but already present at
   `mapanare/lsp/rename.py`. Left untouched, not advertised in
   CHANGELOG as "new."

## Known limitations

- **Marketplace publishing:** the VSCode extension ships only as
  source + VSIX. Marketplace publish is on the v5.20.0 docket.
- **Incremental parsing:** the LSP re-parses on every `didChange`
  (debounced 300 ms). Documented in `docs/guides/lsp.md`. A
  separate (large) arc later.
- **Native ports of `check` / `init` / `lsp`:** v5.18.0 ships
  shell-out stubs only. Real native implementations sit on the
  follow-up docket.

## Out of scope (deferred)

- `--template` flag for `mapanare init` (only `default` ships;
  `cli`, `agent`, `web-server` listed in PLAN are slotted for
  v5.18.x or v5.19.x).
- `mnc emit-wasm` native parity (Mc.5 in PLAN — slotted for a
  v5.18.x patch if there's demand; otherwise v5.19.0).
- Code actions / semantic tokens / inlay hints / workspace symbol
  search → v5.20.0+.

## Roadmap impact

v5.18.0 closes Mc.1 / Mc.3 / Mc.4 from the Mc.* parity arc. Open
remainders:

- **Mc.2** — `mnc fmt` parity. Shell-out shipped at v5.13.0; native
  port deferred indefinitely (not on critical path).
- **Mc.5** — `mnc emit-wasm`. Python CLI works today via
  `mapanare emit-wasm`; native parity slotted as above.
- **Mc.6** — Windows SDK split (already shipped at v5.12.0).

The v5.13–v5.21 terseness arc continues with v5.18.0 as the
**editor-quality** waypoint. v5.19.0 (Te.3 + Dk.* — soft-deprecate
braces, Docker images) and v5.20.0 (Te.5 — struct ergonomics) are
on schedule per `docs/roadmap/v5/CLOSEOUT_ARC.md`.

## Suggested follow-ups

- **v5.18.1** — patch release if VSCode extension surfaces any
  rough edges in real-editor testing (likely candidates: TextMate
  grammar coverage gaps, JSON-RPC framing on Windows-line-ending
  pipes).
- **v5.18.2** — add `--template` flag + ship `cli` / `agent` /
  `web-server` templates.
- **v5.20.0+** — code actions, semantic tokens, inlay hints,
  workspace symbol search; promote the VSCode extension to a
  separate repo and publish to the marketplace.
