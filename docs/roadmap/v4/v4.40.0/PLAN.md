# Mapanare v4.40.0 — LSP Diagnostic Streaming + VS Code Extension Polish

> **Arc 2 release 4.** Incremental re-check on save and on idle,
> with diagnostics pushed to the client without the user running a
> command. VS Code extension packaged and marketplace-ready.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.39.0
**Delta review:** No
**Full panel:** No (v4.41.0)
**Estimated work:** 1 sprint
**Theme:** Make diagnostics show up in the editor without the user running a command.

---

## Scope

### Diagnostic streaming

- LSP method: `textDocument/publishDiagnostics` (server → client push, not request/response)
- Triggered by: `didSave`, `didOpen`, and `didChange` after a 300ms idle debounce
- Payload: `Diagnostic[]` — one per error or warning from `SemanticChecker`
- Formatting: `Diagnostic.message` comes from `diagnostics.py`'s existing renderer; the LSP diagnostic format is structurally equivalent (file URI, range, severity, message, source, code)

### VS Code extension polish

- Package the new LSP capabilities (go-to-def, hover, find-references, rename, completion, streaming diagnostics)
- Bump extension version
- Update README, screenshots, marketplace listing
- Prepare for publish (but the actual publish is optional — solo founder can defer)

---

## Phase 1 — Diagnostic streaming infrastructure

### Phase 1.1: Diagnostic format conversion

- [ ] `mapanare/lsp/diagnostics.py` — new module (or extend existing LSP module).
- [ ] `semantic_error_to_lsp_diagnostic(err: SemanticError) -> LSPDiagnostic`:
  ```python
  def semantic_error_to_lsp_diagnostic(err: SemanticError) -> LSPDiagnostic:
      return LSPDiagnostic(
          range=LSPRange(
              start=LSPPosition(line=err.line - 1, character=err.column - 1),
              end=LSPPosition(line=err.end_line - 1, character=err.end_column - 1),
          ),
          severity=LSPDiagnosticSeverity.Error,
          source="mapanare",
          code=err.code if hasattr(err, "code") else None,
          message=err.message,
          # v4.40.0 adds relatedInformation for suggestions:
          related_information=[
              LSPDiagnosticRelatedInformation(
                  location=LSPLocation(uri=err.filename_to_uri(), range=err.span_to_range()),
                  message=err.suggestion,
              )
          ] if err.suggestion else None,
      )
  ```
- [ ] LSP line/column are 0-indexed; Mapanare's `SemanticError` is 1-indexed. Do the conversion once, at the boundary.

### Phase 1.2: Run the checker on save/change

- [ ] `Workspace.check_file(path: Path) -> list[SemanticError]` — runs the semantic checker on the file's cached AST, returns the error list.
- [ ] `Workspace.handle_did_save` (from v4.37.0) — after rebuilding the file, also run `check_file` and emit diagnostics to the LSP server.
- [ ] `Workspace.handle_did_change` — debounce pattern. The server tracks a per-file timer; on every `didChange`, reset the timer. When the timer fires (300ms idle), re-parse + re-check + emit diagnostics.

### Phase 1.3: Emission

- [ ] `mapanare/lsp/server.py` — add `publish_diagnostics(uri: str, diagnostics: list[LSPDiagnostic])` that sends a `textDocument/publishDiagnostics` notification to the client.
- [ ] Empty `diagnostics` list clears the previous diagnostics — send an empty list when a file is fixed so stale error markers disappear.

---

## Phase 2 — Incremental re-check mechanics

### Phase 2.1: Debounce timer

- [ ] Per-file timer dictionary `dict[Path, asyncio.TimerHandle]`.
- [ ] On `didChange`: cancel existing timer for the path, schedule a new one 300ms out.
- [ ] When the timer fires, run the re-check.
- [ ] On `didSave`: run the re-check immediately (no debounce).

### Phase 2.2: Text synchronization

- [ ] The LSP server already receives `didChange` with the new text buffer. Cache it in the `FileEntry.pending_text` field.
- [ ] The incremental re-check uses `pending_text` if present, else the on-disk file content.

### Phase 2.3: Partial failures

- [ ] If parsing fails, emit a parse-error diagnostic and clear semantic diagnostics (the semantic checker can't run on an unparseable tree).
- [ ] If parsing succeeds but semantic fails, emit both the parse error (none) and semantic errors.

---

## Phase 3 — Tests

- [ ] `tests/lsp/test_diagnostics_stream.py`:
  - `test_save_triggers_diagnostics` — integration test via mock LSP client
  - `test_change_triggers_diagnostics_after_debounce` — wait 400ms, verify diagnostics arrive
  - `test_change_before_debounce_cancels_previous` — rapid-fire changes only produce one diagnostic push
  - `test_fixed_file_clears_diagnostics` — edit the file to fix the error, next re-check emits an empty list
  - `test_parse_error_suppresses_semantic_errors` — unparseable file only produces parse-error diagnostic
  - `test_diagnostic_severity_for_errors_and_warnings` — errors map to `Error`, warnings to `Warning`
  - `test_diagnostic_range_covers_expression` — the range is the full span, not just the start position
  - `test_suggestion_appears_as_related_information`

---

## Phase 4 — VS Code extension polish

### Phase 4.1: Update the extension manifest

- [ ] Find the VS Code extension directory (likely `editor/vscode/` or `tools/vscode-mapanare/` or similar).
- [ ] `package.json` — bump version. Update `description`, `categories`, `keywords`, `capabilities`.
- [ ] `languages` entry: confirm `.mn` file association.
- [ ] `grammars` entry: confirm TextMate grammar reference.
- [ ] `configuration`: LSP settings (server path, log level, trace).

### Phase 4.2: Update the LSP client

- [ ] The VS Code extension's LSP client needs to know about the new capabilities. Likely already works (the LSP server declares its capabilities via `initialize` response).
- [ ] Verify in the extension's `client/src/extension.ts` (or equivalent) that the client registers for `textDocument/publishDiagnostics`, `textDocument/completion`, `textDocument/definition`, `textDocument/hover`, `textDocument/references`, `textDocument/rename`.

### Phase 4.3: Marketplace listing

- [ ] `README.md` in the extension directory — rewrite to showcase the new capabilities with screenshots.
- [ ] `CHANGELOG.md` in the extension directory — new entry describing the Arc 2 capabilities.
- [ ] Icon + screenshots — refresh if the existing ones are from v3.x.
- [ ] **Actual publish to VS Code marketplace is optional.** The artifact is ready; the lead decides when to push the button.

### Phase 4.4: Test the extension end-to-end

- [ ] Launch VS Code with the extension installed.
- [ ] Open a `.mn` file from the Mapanare self-hosted tree.
- [ ] Manually verify: go-to-def jumps correctly, hover shows types, find-references returns sites, rename works, completion offers relevant items, diagnostics appear on save.
- [ ] Write `tests/lsp/MANUAL_SMOKE_TEST.md` with a checklist the lead runs before each LSP-touching release.

---

## Phase 5 — LOW sweep

LSP-related items from the ledger. Candidates: stale LSP JSON schemas, client-side settings cleanup.

---

## Phase 6 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.40.0
- [ ] `CHANGELOG.md [4.40.0]` — LSP diagnostic streaming + VS Code polish
- [ ] `docs/reference.md` §Editor Integration — diagnostic streaming subsection + VS Code marketplace link
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `semantic_error_to_lsp_diagnostic` converts span + message + suggestion | unit test |
| 2 | Save triggers diagnostics | `test_save_triggers_diagnostics` |
| 3 | Change triggers diagnostics after 300ms debounce | `test_change_triggers_diagnostics_after_debounce` |
| 4 | Rapid changes don't spam the client | `test_change_before_debounce_cancels_previous` |
| 5 | Fixing a file clears stale diagnostics | `test_fixed_file_clears_diagnostics` |
| 6 | Parse errors suppress semantic errors | `test_parse_error_suppresses_semantic_errors` |
| 7 | Diagnostic range covers full expression span | `test_diagnostic_range_covers_expression` |
| 8 | Suggestions appear as `relatedInformation` | `test_suggestion_appears_as_related_information` |
| 9 | VS Code extension manifest updated | `package.json` diff |
| 10 | VS Code extension manual smoke test passes | `MANUAL_SMOKE_TEST.md` filled out |
| 11 | Extension marketplace listing ready | README + CHANGELOG in extension dir |
| 12 | Standard closeout clean | CI logs |

---

## What v4.40.0 explicitly does NOT do

- **Publish the VS Code extension to the marketplace.** That's a lead decision, not a release gate.
- **Quick-fix code actions** (e.g., "add missing import," "add missing match arm"). v5.x.
- **Inlay hints** (inline type annotations). v5.x.
- **Semantic tokens** (beyond TextMate grammar). v5.x.
- **Code lens** (run button above `fn main`, test-run buttons). v5.x.

---

## Reference

- LSP 3.17 §Language Features §Diagnostics
- [`v4.37.0/PLAN.md`](../v4.37.0/PLAN.md), [`v4.38.0/PLAN.md`](../v4.38.0/PLAN.md), [`v4.39.0/PLAN.md`](../v4.39.0/PLAN.md)

---

## After v4.40.0

v4.41.0 is the **arc 2 panel release** — 5-minor cadence panel runs against the LSP maturity arc.
