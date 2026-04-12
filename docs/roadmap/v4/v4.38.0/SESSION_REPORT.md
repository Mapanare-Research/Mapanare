# v4.38.0 Session Report — LSP Navigation

**Date:** 2026-04-12
**Scope:** Find-references + rename refactoring
**Breaking:** No
**Arc:** 2 (Editor Tooling) — release 2

---

## What shipped

### Reverse reference index

Extended `WorkspaceIndex` with `refs_by_symbol: dict[tuple[str, str], list[ReferenceSite]]`. The `_collect_references` AST walker visits function bodies and collects every identifier/call/type-use that resolves to a known symbol. A second pass after `scan_root` ensures cross-module references are captured regardless of file processing order.

### Find-references (`textDocument/references`)

The handler now:
1. Tries within-file references first (existing v0.5.0)
2. Falls back to workspace index `find_references()` for cross-module results
3. Honors `context.includeDeclaration` flag

### Rename (`textDocument/rename` + `textDocument/prepareRename`)

New `mapanare/lsp/rename.py` module with:
- `validate_rename(symbol, new_name, workspace)` — rejects keywords, invalid identifiers, name conflicts in same module
- `apply_rename(symbol, new_name, workspace)` — builds multi-file edit map from definition + all reference sites
- `prepareRename` handler checks feasibility and returns symbol span

### Rename capabilities registered

Server now advertises `rename_provider=RenameOptions(prepare_provider=True)`.

---

## Test evidence

- 13 new tests: `test_find_references.py` (5) + `test_rename.py` (8)
- 797 total tests pass (parser + semantic + LLVM + LSP)
- Cross-module rename verified: definition in file A, call sites in files B and C

---

## Design decisions

1. **Local stays local** — rename only crosses module boundaries for top-level symbols
2. **Reject shadowing** — rename to a name in scope is rejected even if outer scope is unused
3. **Second-pass reference collection** — `scan_root` does a second pass after all symbols indexed

---

## Files changed

| File | Lines | What |
|------|-------|------|
| `mapanare/lsp/rename.py` | +95 | NEW — validate + apply rename |
| `mapanare/lsp/workspace.py` | +80 | ReferenceSite, _collect_references, find_references, second-pass scan |
| `mapanare/lsp/server.py` | +70 | rename + prepareRename handlers, cross-module references |
| `tests/lsp/test_find_references.py` | +55 | NEW — 5 tests |
| `tests/lsp/test_rename.py` | +95 | NEW — 8 tests |
