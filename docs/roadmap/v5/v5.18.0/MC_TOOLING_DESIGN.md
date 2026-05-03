# v5.18.0 — Mc.* Tooling Pack — Design + Audit

**Status:** Phase 0 lock — written 2026-04-30.
**Author:** v5.18.0 cycle.
**Supersedes:** N/A (first design doc for the Mc.* arc).

---

## Summary

The Phase 0 audit found that **most of v5.18.0's surface is already
implemented in the Python codebase.** The release was originally
scoped against a greenfield assumption ("create `mapanare/lsp.py`")
that doesn't match reality. This design doc replaces that assumption
with an audit-driven scope: **verify the as-shipped tooling, fix
divergences from PLAN, fill the missing pieces (init templates,
VSCode extension, native dispatch stubs), and ship docs.**

---

## As-shipped state (audit findings)

### Mc.1 — LSP

`mapanare/lsp/` is a 3,020-line Python package using `pygls` +
`lsprotocol`. Layout:

| File | LOC | Role |
|---|---:|---|
| `server.py` | 712 | LSP entry point, JSON-RPC over stdio, debounced diagnostics |
| `analysis.py` | 1,351 | Document analysis: parse + semantic + symbol index |
| `completion.py` | 280 | textDocument/completion (keywords, identifiers, member access) |
| `diagnostics.py` | 114 | Semantic-check runner that emits LSP-shaped diagnostics |
| `rename.py` | 131 | textDocument/rename (out of scope per PLAN — leave alone) |
| `workspace.py` | 431 | Workspace-wide symbol index for cross-module go-to-def |

Identifies as `mapanare-lsp v0.5.0`. Capabilities exceed PLAN's MVP:

- `initialize` / `initialized` / `shutdown` / `exit` ✅
- `textDocument/didOpen` / `didChange` / `didClose` ✅
- `textDocument/publishDiagnostics` (debounced 300ms) ✅
- `textDocument/hover` ✅
- `textDocument/definition` ✅
- `textDocument/completion` ✅
- `textDocument/references` ✅ (find-refs)
- `textDocument/rename` ✅ (out of PLAN scope, but already shipped)
- Workspace-wide symbol index (cross-module go-to-def) ✅

CLI wiring at `mapanare/cli.py:1357` (`cmd_lsp`). Tests at
`tests/lsp/{test_analysis, test_completion, test_diagnostics_stream,
test_find_references, test_rename, test_workspace_index}.py`.

**Decision:** v5.18.0 keeps the existing implementation. No rewrite.
Native `.mn` LSP port stays deferred per PLAN risk register.

### Mc.4 — `mnc check`

`cmd_check` exists at `mapanare/cli.py:236`. Pipeline:

```
parse_recovering(source)
  → for each ParseError, emit Diagnostic(severity=ERROR, ...)
  → check(ast, ...)
  → for each SemanticError, emit Diagnostic via err.to_diagnostic()
  → if any: format_diagnostic + format_summary, exit 1
  → else: print "check: <file> OK"
```

Honors `--werror` (`semanticerror.warning` → `Severity.ERROR`).
Smoke test: `mapanare check tests/golden/01_hello.mn` exits 0
with "check: tests/golden/01_hello.mn OK".

**Gaps:** no `--all` directory walk; no `tests/test_check.py`.

### Mc.3 — `mnc init`

`cmd_init` at `mapanare/cli.py:439` calls
`stdlib.pkg.init_project(project_dir, name)`. Implementation
at `stdlib/pkg.py:965`:

- Creates `mapanare.toml` via `save_manifest`.
- Writes `main.mn` with **inline string literal**:
  ```python
  f.write('fn main() {\n    print("Hello, Mapanare!")\n}\n')
  ```
- No `.gitignore`. No `README.md`. **Brace syntax**, not terse.

**Gaps (MUST fix in v5.18.0):**

1. Brace `fn main() { ... }` is non-canonical post-v5.13–v5.17.
   The first file a new user reads should be in the syntax we're
   pushing, i.e. `fn main(): ...` with implicit-return where
   appropriate.
2. Missing `.gitignore` (PLAN §Items Mc.3.A).
3. Missing `README.md` (PLAN §Items Mc.3.A).
4. Inline-string template is brittle. Move to template directory.

### Native `mnc` dispatch (`mapanare/self/main.mn`)

Currently dispatches: `emit-llvm`, `fmt`, `run`, `build`, `compile`,
`test`, `cache`, `version`. **No `check`, `init`, `lsp`.**

**Decision:** v5.18.0 adds **dispatch stubs** that print a clean
"use `mapanare check`/`mapanare init`/`mapanare lsp` (Python CLI)"
hint and exit 0. Native ports of these subcommands are tracked
on the follow-up docket. This is the cheapest path that closes
the user-visible gap — `mnc check foo.mn` should not silently
crash or print "unknown command."

### `templates/init/`

Does not exist. Greenfield in v5.18.0.

### `editors/vscode/`

Does not exist in the Mapanare repo. **Discovered mid-session:**
the canonical extension lives in a sibling repo,
[Mapanare-Research/mapanare-vscode](https://github.com/Mapanare-Research/mapanare-vscode),
shipping at v0.4.0 with publisher `mapanare-research`. Already
wires `mapanare lsp` and exposes 7 commands (run, check,
compile, fmt, lint, lintFix, restartLsp). v5.18.0 updates that
repo to v0.5.0 rather than building anything in-tree.

---

## v5.18.0 closeout scope

| Item | Action | Effort |
|---|---|---:|
| **Mc.4.A.test** | `tests/test_check.py` — clean file (exit 0), broken file (exit 1, has diagnostic), `--werror` promotion, multi-error file | 0.5h |
| **Mc.4.B** | `mnc check --all`: walk current dir for `*.mn`, run check on each | 0.5h |
| **Mc.3.refactor** | `templates/init/default/{main.mn, mapanare.toml, .gitignore, README.md}` with `{{NAME}}` substitution; rewrite `init_project` to copy from template dir | 1.5h |
| **Mc.3.terse** | Template `main.mn` uses `fn main():` (terse) not `fn main() {` (brace) | (folded above) |
| **Mc.1.verify** | Run existing LSP through PLAN success criteria; smoke-test against VSCode dev extension; document any divergences as patch follow-ups | 2h |
| **Native dispatch** | Add `check`/`init`/`lsp` stubs in `mapanare/self/main.mn` that print "use `mapanare …`" and exit 0 | 0.5h |
| **VSCode extension** | Bump sibling repo `mapanare-vscode` to v0.5.0; add `mapanare.init` + `mapanare.checkAll` commands; refresh README to v5.18.0 capabilities. (Existing 0.4.0 already wires LSP + 7 commands + 40+ snippets.) | 1h |
| **Docs** | `MC_TOOLING_DESIGN.md` (this), `SESSION_REPORT.md`, `docs/guides/lsp.md`, `docs/guides/init.md`, `editors/vscode/README.md` | 1.5h |
| **Updates** | README.md tooling section, CHANGELOG.md, CLAUDE.md release note | 0.5h |

Total: ~10–12h, single session.

---

## Decisions locked

1. **LSP host language:** Python (`pygls`-backed), as already shipped.
   Native `.mn` LSP deferred — no scope or schedule in v5.18.0.
2. **VSCode extension home:** sibling repo
   [Mapanare-Research/mapanare-vscode](https://github.com/Mapanare-Research/mapanare-vscode).
   No in-tree extension. The "promote to separate repo" plan in
   PLAN.md was already done before v5.18.0 — the audit caught it.
   Marketplace publish stays a separate docket item.
3. **Init template format:** `templates/init/default/` directory of
   literal files with `{{NAME}}` placeholder substitution. Rejected:
   inline strings (current) — too brittle. Rejected: jinja2 — adds
   a dep for one substitution.
4. **Init template syntax:** terse colon-block (`fn main():`).
   Canonical post-v5.17.0; the first file a new user reads should
   match what they'll write.
5. **Native dispatch:** stubs only in v5.18.0. Print
   "subcommand `X` not yet supported in `mnc`; run `mapanare X`"
   to stderr and exit 0. Real native ports tracked on the follow-up
   docket.
6. **Diagnostic format:** existing `mapanare/diagnostics.py`
   (Rust-style) for the CLI; existing `mapanare/lsp/diagnostics.py`
   adapter for LSP. No changes.
7. **AST positions:** every node already inherits `span: Span(line,
   column, end_line, end_column)`. No retrofit needed.
8. **Symbol table:** existing `Scope` + `Symbol.node.span` already
   used by `mapanare/lsp/analysis.py`. No retrofit.
9. **LSP capability set for v5.18.0 ship:** match what's already
   shipped in `mapanare/lsp/server.py` v0.5.0. Don't add new
   capabilities in this release; verify the existing ones meet
   PLAN's success criteria.
10. **Rename:** out of PLAN scope but already implemented at
    `mapanare/lsp/rename.py`. Leave untouched. Don't gate the
    release on it; don't advertise it as new in CHANGELOG.

---

## Risk register (revised)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Existing LSP fails to launch in real VSCode (JSON-RPC framing, pygls version drift) | LOW–MED | Phase 3 success criterion: launch from `editors/vscode/` extension dev mode and verify diagnostics + hover work. If broken, this becomes the v5.18.0 critical path. |
| Existing LSP test suite has been bit-rotting since v4.40.0 | MED | Run `pytest tests/lsp/ -v` early in Phase 3. Triage failures. |
| Init template substitution breaks on names with regex-special chars | LOW | Use `str.replace` (literal), not `re.sub`. Document allowed name regex. |
| `pygls` not in `pyproject.toml` install deps | LOW | Audit `pyproject.toml` early. Add to `[project.optional-dependencies] lsp` if missing. |
| VSCode extension TypeScript build fails on user machines without Node | LOW | Document Node ≥18 prereq in `editors/vscode/README.md`. Ship the compiled `out/` and a `.vsix` artifact. |
| Strict 3-stage fixed point breaks because we touched `main.mn` | LOW | Native dispatch additions are pure-additive new branches in the dispatch table. Verify with `bash scripts/verify_fixed_point.sh --keep` after the change. |

---

## Out of scope (deferred to v5.20.0+)

- Refactoring features (rename, extract function) → v6.0+.
  *Rename is already implemented at `mapanare/lsp/rename.py` — left
  untouched and unadvertised in v5.18.0; will surface in v5.20.0.*
- Code actions (organize imports, quick fix) → v5.20.0+.
- Semantic tokens / inlay hints → v5.20.0+.
- Workspace-wide symbol search (workspace/symbol) → v5.20.0+.
- Native `mnc lsp` (in `.mn`) → no schedule.
- VSCode marketplace publishing → docket item.
- Neovim / Helix / Zed configs → community contribs OK.
- DAP (debugger) → far future.
- Project-wide `mnc check` with caching → v5.20.0+.
- Incremental parsing → tracked separately, no v5.x slot.

---

## Success criteria

Lifted from PLAN.md, mapped to current state:

- [x] `mnc lsp` runs and `initialize` round-trips correctly
  *(verified at audit time: `from mapanare.lsp.server import server`
  imports clean as `mapanare-lsp v0.5.0`)*
- [ ] VSCode extension shows diagnostics within 200ms on a 100-line
  file edit *(Phase 5)*
- [ ] Hover shows accurate type info on identifiers *(Phase 3 verify)*
- [ ] `mnc init demo && cd demo && mnc run` produces "Hello, world!"
  *(Phase 1 — currently brace syntax + missing files)*
- [x] `mapanare check tests/golden/some_file.mn` exits 0
  *(verified: `check: tests/golden/01_hello.mn OK`)*
- [ ] `mapanare check <broken.mn>` exits 1 with a clear diagnostic
  *(Phase 2 test)*
- [ ] Existing pytest suite passes
- [ ] Goldens 66/66 (or current baseline)
- [ ] Strict 3-stage fixed point preserved
- [ ] `make lint` clean
