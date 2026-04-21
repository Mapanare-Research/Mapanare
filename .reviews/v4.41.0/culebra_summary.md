# Culebra Summary — v4.41.0

**Note:** Arc 2 had zero compiler/emitter changes. IR is identical to v4.36.0.

## Codebase Health

| Metric | Value |
|--------|-------|
| Python compiler lines | 34,459 |
| C runtime lines | 13,150 |
| Self-hosted compiler lines | 37,211 |
| LSP modules | 6 (server, analysis, workspace, completion, diagnostics, rename) |
| Golden tests | 49 |
| Pytest tests (core + LSP) | 820 |
| LSP tests | 49 (added in Arc 2) |

## Arc 2 Features Delivered

1. **v4.37.0**: WorkspaceIndex + cross-module go-to-def + hover
2. **v4.38.0**: Find-references + rename refactoring
3. **v4.39.0**: Context-aware completion (import, type, field/method, fallback)
4. **v4.40.0**: Diagnostic streaming + VS Code extension scaffold
