# v4.41.0 Pre-Panel Audit — Arc 2

**Date:** 2026-04-12
**Scope:** Fact-check v4.37.0-v4.40.0 SESSION_REPORT claims

## Results

| Version | Claims | Passed | Failed |
|---------|--------|--------|--------|
| v4.37.0 | 4 | 4 | 0 |
| v4.38.0 | 5 | 5 | 0 |
| v4.39.0 | 4 | 4 | 0 |
| v4.40.0 | 4 | 4 | 0 |
| **Total** | **17** | **17** | **0** |

## v4.37.0 — WorkspaceIndex

| Claim | Evidence | Verdict |
|-------|----------|---------|
| `mapanare/lsp/workspace.py` exists | File present (223 lines) | PASS |
| WorkspaceIndex has scan_root, rebuild_file, lookup | All methods verified | PASS |
| `tests/lsp/test_workspace_index.py` (13 tests) | pytest collects 13 | PASS |
| Cross-module go-to-def wired in server.py | workspace fallback at line ~245 | PASS |

## v4.38.0 — Find-references + Rename

| Claim | Evidence | Verdict |
|-------|----------|---------|
| `mapanare/lsp/rename.py` exists | File present (95 lines) | PASS |
| ReferenceSite in workspace.py | Dataclass at line ~52 | PASS |
| refs_by_symbol populated via _collect_references | Function exists + second-pass in scan_root | PASS |
| `tests/lsp/test_find_references.py` (5 tests) | pytest collects 5 | PASS |
| `tests/lsp/test_rename.py` (8 tests) | pytest collects 8 | PASS |

## v4.39.0 — Completion

| Claim | Evidence | Verdict |
|-------|----------|---------|
| `mapanare/lsp/completion.py` exists | File present (220 lines) | PASS |
| 4 completion contexts (import, type, field, fallback) | All 4 functions present | PASS |
| Visibility-respected test passes | test_visibility_respected in test_completion.py | PASS |
| `tests/lsp/test_completion.py` (13 tests) | pytest collects 13 | PASS |

## v4.40.0 — Diagnostics + VS Code

| Claim | Evidence | Verdict |
|-------|----------|---------|
| `mapanare/lsp/diagnostics.py` exists | File present (115 lines) | PASS |
| relatedInformation for suggestions | test_suggestion_appears_as_related_information passes | PASS |
| `editor/vscode/package.json` exists | File present | PASS |
| `tests/lsp/test_diagnostics_stream.py` (10 tests) | pytest collects 10 | PASS |

## Conclusion

All 17 claims verified. Arc 2 SESSION_REPORTs are honest.
