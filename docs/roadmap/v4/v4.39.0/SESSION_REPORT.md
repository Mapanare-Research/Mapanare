# v4.39.0 Session Report — LSP Completion

**Date:** 2026-04-12
**Scope:** Context-aware completion in four contexts
**Breaking:** No
**Arc:** 2 (Editor Tooling) — release 3

---

## What shipped

### Completion module (`mapanare/lsp/completion.py`)

New module with four completion functions:

1. **`complete_import(prefix, workspace)`** — offers workspace modules + stdlib after `import`
2. **`complete_type(workspace)`** — offers 14 builtin types + user structs/enums/traits in type position
3. **`complete_field_method(receiver_type, workspace)`** — offers struct fields and builtin methods for Option, Result, List, String after `.`
4. **`complete_identifiers(workspace, current_module)`** — fallback with scope ranking: current module > public imports > builtins

### Context detection

`_detect_completion_context(source, line, col)` inspects the text before cursor:
- After `import ` → import context
- After `.` → field/method context
- After `:` or `->` → type context
- Otherwise → identifier fallback

### Visibility rules

Internal symbols from other modules are excluded from fallback completion. Only `pub` symbols cross module boundaries.

### Scope ranking

`sortText` field orders completions: `0_` (current module) < `2_` (imports) < `3_` (builtins).

---

## Test evidence

- 13 new tests (`tests/lsp/test_completion.py`)
- 810 total tests pass
- Covers: import (3), type (2), field/method (4), fallback (4)

---

## Files changed

| File | Lines | What |
|------|-------|------|
| `mapanare/lsp/completion.py` | +220 | NEW — 4 completion contexts + builtin method tables |
| `mapanare/lsp/server.py` | +50 | Context detection, workspace-aware completion wiring |
| `tests/lsp/test_completion.py` | +145 | NEW — 13 tests |
