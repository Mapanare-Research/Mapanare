# v5.18.0 — Mc.1 / Mc.3 / Mc.4 — LSP + init + check (tooling pack)

**Status:** PLANNING
**Breaking:** No. Three new `mnc` subcommands; nothing existing
changes.
**Prerequisite:** v5.17.0 shipped (self-hosted compiler in terse
syntax). Tooling reads + emits the canonical syntax from day one.
**Estimated effort:** 24–40h, three or four sessions. Mc.1 (LSP)
is ~70% of the work.

---

## Why this exists

After the terse syntax pivot lands (v5.13–v5.16), the language is
"good enough to read." But "good enough to **write**" requires
editor support — autocomplete, hover types, jump-to-definition,
real-time diagnostics — and project scaffolding so a new user can
go from zero to a running app without learning the file layout
manually.

This release closes the three highest-leverage gaps in the Mc.*
parity arc:

- **Mc.1 — LSP.** `mnc lsp` over stdio. VSCode + Neovim + Helix +
  Zed all speak LSP. Without this, writing Mapanare in a real
  editor is a wasteland.
- **Mc.3 — init.** `mnc init <name>` scaffolds a minimal project:
  `main.mn`, `mapanare.toml`, `.gitignore`, `README.md`. Cuts the
  "first project" bootstrap from 20 minutes to 10 seconds.
- **Mc.4 — check.** `mnc check <file>` runs parser + semantic
  checker, emits diagnostics, no codegen. Faster than `mnc build`,
  matches `cargo check` / `tsc --noEmit`.

Mc.5 (`mnc emit-wasm` parity with Python `mapanare emit-wasm`) is
listed as optional — include if there's spare capacity, otherwise
slip to a v5.17.x patch.

---

## Goal

1. `mnc lsp` runs an LSP server over stdio implementing the MVP
   feature set: textDocument/diagnostics, hover, definition,
   completion (basic).
2. A working VSCode extension reference implementation lives at
   `editors/vscode/` (or a separate ecosystem repo — decide in
   Phase 0). Documented end-to-end install path.
3. `mnc init <name>` scaffolds a runnable project. `mnc run` works
   in the new directory immediately.
4. `mnc check <file>` runs semantic analysis without emitting
   IR/binary. Exit code 0 on success, non-zero on errors.
5. Optional Mc.5: `mnc emit-wasm <file>` matches Python CLI
   behavior.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Mc.1.A** | HIGH | LSP scaffold: `mnc lsp` reads JSON-RPC over stdio, handles `initialize`, `initialized`, `shutdown`, `exit`. Lives in `mapanare/lsp.py` for now (port to native later). | 3–5h |
| **Mc.1.B** | HIGH | textDocument/didOpen, didChange, didClose: maintain in-memory file state. | 2h |
| **Mc.1.C** | HIGH | textDocument/publishDiagnostics: route parser + semantic errors through LSP, with proper Position/Range. | 3–4h |
| **Mc.1.D** | HIGH | textDocument/hover: return type info for the symbol under cursor. Reuse semantic checker's symbol table. | 3–4h |
| **Mc.1.E** | MEDIUM | textDocument/definition: jump-to-def. Same symbol table. | 2–3h |
| **Mc.1.F** | MEDIUM | textDocument/completion: keyword completions, in-scope identifier completions, member-access completions on known types. | 3–5h |
| **Mc.1.G** | MEDIUM | VSCode extension reference: `editors/vscode/` package with package.json, syntax highlighting (TextMate grammar), LSP client wiring. | 3–5h |
| **Mc.3.A** | MEDIUM | `mnc init <name>` subcommand. Scaffolds: `main.mn` (hello world in terse syntax), `mapanare.toml` (project name, version), `.gitignore`, `README.md`. | 1–2h |
| **Mc.3.B** | LOW | `mnc init --template <name>`: pick from a small set of templates (cli, agent, signal-pipeline, web-server stub). 1 template in v5.18.0; more later. | 1h |
| **Mc.4.A** | MEDIUM | `mnc check <file>` subcommand. Runs parser + semantic, emits diagnostics, exits 0/1. No codegen. | 1–2h |
| **Mc.4.B** | LOW | `mnc check --all`: walk current directory's `.mn` files. | 0.5h |
| **Mc.5** | OPTIONAL | `mnc emit-wasm <file>`: shell out to Python `mapanare emit-wasm` for v5.18.0; native port later. | 1–2h |

---

## Phase plan

**Phase 0 — Architecture decisions.** Write `MC_TOOLING_DESIGN.md`
covering:

- LSP host language: Python (in `mapanare/lsp.py`) for v5.18.0?
  Native `.mn` later? **Recommendation:** Python first. The LSP
  protocol is JSON-heavy; Python's `pylsp` patterns are
  well-trodden; native port can wait until LSP is stable.
- VSCode extension repo: in-tree at `editors/vscode/` or separate
  repo? **Recommendation:** in-tree for v5.18.0 to keep iteration
  tight; promote to separate repo once it stabilizes.
- Init template format: inline strings in `cmd_init` vs
  `templates/` directory? **Recommendation:** `templates/init/`
  directory of literal files, copied with name substitution.
- Diagnostic format: reuse existing `mapanare/diagnostics.py` Rust-
  style output for the CLI; map to LSP Diagnostic objects in the
  LSP layer.

**Phase 1 — Mc.4 first (smallest, lowest risk).** `mnc check` is
60 lines of code and validates the diagnostic-emission pipeline
that the LSP needs in Phase 3. Ship it first.

**Phase 2 — Mc.3.** Scaffold `templates/init/default/`. Implement
`cmd_init`. Test: `mnc init foo && cd foo && mnc run` works.

**Phase 3 — Mc.1.A through Mc.1.E.** LSP scaffold + open/change/close
+ diagnostics + hover + definition. This is the bulk of the
release.

**Phase 4 — Mc.1.F.** Completion. The most fiddly LSP feature
because in-scope identifier resolution at any cursor position
requires a deeper symbol table than diagnostics need.

**Phase 5 — Mc.1.G.** VSCode extension. End-to-end test: install
from VSIX, edit a `.mn` file, see diagnostics, hover, jump-to-def.

**Phase 6 — Mc.5 if capacity.** Otherwise defer.

**Phase 7 — Docs + closeout.**

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Symbol table from semantic.py doesn't expose positions LSP needs | MEDIUM | Phase 0 audit: confirm AST nodes carry source positions. If not, retrofit before Phase 3 — every node needs a `span: SourceSpan` field. |
| Incremental parsing required for snappy LSP — full re-parse on every keystroke is slow | MEDIUM | v5.18.0 ships full re-parse only. Document the latency. Incremental parsing is a separate (large) arc later. Acceptable on small files (<1000 LOC); document the boundary. |
| LSP works in tests but not in real editors due to JSON-RPC framing bugs | HIGH | Do **all** development against a real editor (VSCode) by mid-Phase 3. Don't trust unit tests alone. |
| VSCode extension publishing requires marketplace account + signing | LOW | Ship as VSIX in v5.18.0, publish to marketplace later. |
| Init template uses pre-terse syntax | LOW | Generated by hand in this release; review template at end of Phase 2 to confirm it's in canonical terse style. |
| Native `mnc lsp` lags Python implementation by a release | LOW | Ship Python version; mark Mc.1 as "Python-backed" in changelog. Native port goes on the follow-up docket. |

---

## Out of scope (deferred)

- Refactoring features (rename, extract function) → v6.0+
- Code actions (organize imports, quick fix) → v5.20.0+
- Semantic tokens / inlay hints → v5.20.0+
- Workspace-wide symbol search → v5.20.0+
- Native `mnc lsp` (in `.mn`) → defer until LSP stabilizes
- VSCode marketplace publishing → docket item
- Neovim / Helix / Zed configs → community contribs OK; not gated
- DAP (debugger) → far future
- Project-wide `mnc check` with caching → v5.20.0+

---

## Success criteria

- `mnc lsp` runs and `initialize` round-trips correctly
- VSCode extension shows diagnostics within 200ms on a 100-line
  file edit
- Hover shows accurate type info on identifiers in the corpus
- `mnc init demo && cd demo && mnc run` produces "Hello, world!"
- `mnc check tests/golden/some_file.mn` exits 0
- `mnc check <broken.mn>` exits 1 with a clear diagnostic
- Existing pytest suite passes
- Goldens 66/66 (existing + any from v5.15.0)
- Strict 3-stage fixed point preserved
- `make lint` clean
