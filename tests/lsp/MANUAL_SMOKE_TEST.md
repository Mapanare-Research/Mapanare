# LSP Manual Smoke Test Checklist

Run this before any LSP-touching release. Open a `.mn` file from the
self-hosted compiler tree in VS Code with the Mapanare extension.

## Checklist

- [ ] **Diagnostics on open** — errors/warnings appear in Problems panel
- [ ] **Diagnostics on save** — fixing an error and saving clears the marker
- [ ] **Diagnostics on change** — typing a syntax error shows after ~300ms
- [ ] **Go-to-definition (same file)** — Ctrl+Click on a function call jumps to its definition
- [ ] **Go-to-definition (cross-module)** — Ctrl+Click on a function from another file opens it
- [ ] **Hover** — hovering over a function shows its signature
- [ ] **Hover (cross-module)** — hovering over a cross-module symbol shows signature + source module
- [ ] **Find references** — Shift+F12 on a function shows all call sites
- [ ] **Rename** — F2 on a function name renames across all files
- [ ] **Rename reject** — F2 rename to a keyword shows an error
- [ ] **Completion (dot)** — typing `.` after a value shows fields/methods
- [ ] **Completion (type)** — typing `:` after a parameter shows type names
- [ ] **Completion (import)** — typing after `import ` shows module names
- [ ] **Completion (fallback)** — Ctrl+Space in a function body shows identifiers

## Environment

- VS Code version: ___
- Extension version: ___
- Mapanare version: ___
- OS: ___
- Date: ___
- Tester: ___
