# v4.41.0 Measurements — Arc 2 Close

**Date:** 2026-04-12

## Test counts

| Suite | Count |
|-------|-------|
| Pytest (parser + semantic + LLVM + LSP) | 820 |
| Golden tests | 49 |
| LSP-specific tests | 49 (added across v4.37.0-v4.40.0) |

## Arc 2 delta (v4.36.0 → v4.41.0)

| Metric | v4.36.0 | v4.41.0 | Delta |
|--------|---------|---------|-------|
| Tests | 704 | 820 | +116 |
| LSP modules | 2 (server.py, analysis.py) | 6 (+workspace, completion, diagnostics, rename) | +4 |
| LSP features | 5 (within-file) | 9 (cross-module) | +4 |

## LSP features delivered

| Feature | Release | Handler |
|---------|---------|---------|
| Cross-module go-to-def | v4.37.0 | `textDocument/definition` |
| Workspace-aware hover | v4.37.0 | `textDocument/hover` |
| Cross-module find-refs | v4.38.0 | `textDocument/references` |
| Rename refactoring | v4.38.0 | `textDocument/rename` + `prepareRename` |
| Import completion | v4.39.0 | `textDocument/completion` |
| Type completion | v4.39.0 | `textDocument/completion` |
| Field/method completion | v4.39.0 | `textDocument/completion` |
| Diagnostic streaming | v4.40.0 | `textDocument/publishDiagnostics` |
| VS Code extension scaffold | v4.40.0 | `editor/vscode/` |
