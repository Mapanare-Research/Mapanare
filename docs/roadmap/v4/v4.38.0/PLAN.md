# Mapanare v4.38.0 — LSP Navigation (Find-References + Rename)

> **Arc 2 release 2.** Extends the v4.37.0 workspace index with
> reverse references (every call + read site of a symbol) and
> text-based rename refactoring with semantic validation.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.37.0 (workspace index must exist and be correct)
**Delta review:** No
**Full panel:** No (v4.41.0)
**Estimated work:** 1.5 sprints
**Theme:** Let a developer safely rename a symbol across the whole workspace.

---

## Scope

### Find-references

- LSP method: `textDocument/references`
- Input: `ReferenceParams` (position + `context.includeDeclaration`)
- Output: `Location[]` — one per reference site
- Cross-module: yes. The workspace index has to track reverse references (every file that mentions a top-level symbol).

### Rename refactoring

- LSP method: `textDocument/rename`
- Input: `RenameParams` (position + new name)
- Output: `WorkspaceEdit` — a multi-file edit applied atomically by the client
- Semantic validation: rejects renames to names already in scope at any use site.
- Scope: local variables, parameters, functions, structs, enums, fields, methods, modules.

---

## Phase 1 — Reverse reference index

### Phase 1.1: Index structure

- [ ] `mapanare/lsp/workspace.py` — extend `WorkspaceIndex`:

  ```python
  @dataclass
  class ReferenceSite:
      path: Path
      span: Span
      kind: Literal["call", "read", "type_use", "import"]
      context_name: str  # enclosing function/impl for display

  class WorkspaceIndex:
      # Existing:
      files: dict[Path, FileEntry]
      symbols_by_name: dict[tuple[str, str], SymbolDef]
      # NEW:
      refs_by_symbol: dict[tuple[str, str], list[ReferenceSite]]
  ```

- [ ] `Workspace.collect_references(file_ast, path) -> list[tuple[SymbolKey, ReferenceSite]]` — walks the AST, emits a reference site for every identifier/call/type-use that resolves to a `SymbolDef`.
- [ ] `Workspace.rebuild_file` now also removes old reference sites for this path before adding new ones (O(total refs per file) — fine for realistic workspace sizes).

### Phase 1.2: Reference collection walker

- [ ] `mapanare/lsp/refs.py` — a visitor that walks an AST and collects every reference. Reuses `resolve_symbol` from v4.37.0 to map each identifier to its `SymbolDef`.
- [ ] Handles: function calls, field access (as read on the struct type), method calls (as call on the impl'd method), type references, enum variant usage, import paths.

### Phase 1.3: Tests

- [ ] `tests/lsp/test_find_references.py`:
  - `test_find_references_local_variable` — finds every read site in the same function
  - `test_find_references_top_level_function_same_file`
  - `test_find_references_top_level_function_cross_module`
  - `test_find_references_struct_field` — every `.field` access site
  - `test_find_references_method` — every `.method()` call site
  - `test_find_references_enum_variant` — every construction + pattern match
  - `test_find_references_include_declaration_flag` — honors the `context.includeDeclaration` LSP flag
  - `test_find_references_no_false_positives_on_shadowed_local` — a local `let x` shadowing a top-level `x` gets its own reference set

---

## Phase 2 — LSP references handler

- [ ] `textDocument/references` handler:

  ```python
  def on_references(params: ReferenceParams) -> list[Location]:
      node = node_at_cursor(...)
      if node is None:
          return []
      symbol = resolve_symbol(node, file_entry.ast, workspace)
      if symbol is None:
          return []
      key = (symbol.module, symbol.name)
      sites = workspace.refs_by_symbol.get(key, [])
      locations = [Location(path_to_uri(s.path), span_to_range(s.span)) for s in sites]
      if params.context.includeDeclaration:
          locations.insert(0, Location(path_to_uri(symbol.path), span_to_range(symbol.span)))
      return locations
  ```

- [ ] Handle local variables: they don't go through the workspace index (local to a file). Fall back to walking the enclosing function's scope.

---

## Phase 3 — Rename refactoring

### Phase 3.1: Rename validation

- [ ] `mapanare/lsp/rename.py` — `validate_rename(symbol, new_name, workspace) -> Optional[str]`. Returns an error message if the rename is invalid, `None` if OK.
- [ ] Validation rules:
  1. `new_name` is a valid identifier (same rules as the lexer — reject keywords, reject invalid characters).
  2. `new_name` does not conflict with an existing name in any scope that uses the symbol.
  3. For top-level symbols: `new_name` is not already a top-level name in the symbol's module.
  4. For local variables: `new_name` is not shadowed by an outer scope nor shadows an inner scope.
  5. For struct fields: `new_name` is not already a field of the same struct.
  6. For method names: `new_name` is not already a method of the same impl.

### Phase 3.2: Rename execution

- [ ] `mapanare/lsp/rename.py` — `apply_rename(symbol, new_name, workspace) -> WorkspaceEdit`:
  1. Collect every reference site of the symbol via `workspace.refs_by_symbol`.
  2. Add the definition site too.
  3. For each site, build a `TextEdit` with the span of the old name and the replacement text of the new name.
  4. Group `TextEdit`s by file URI into a `WorkspaceEdit.changes` map.
  5. Return the `WorkspaceEdit`.

### Phase 3.3: LSP handler

- [ ] `textDocument/rename` handler:

  ```python
  def on_rename(params: RenameParams) -> Optional[WorkspaceEdit]:
      node = node_at_cursor(...)
      symbol = resolve_symbol(node, ...)
      if symbol is None:
          raise LspError("no symbol under cursor to rename")
      error = validate_rename(symbol, params.newName, workspace)
      if error is not None:
          raise LspError(error)
      return apply_rename(symbol, params.newName, workspace)
  ```

- [ ] `textDocument/prepareRename` handler — lets the client check feasibility before showing the rename UI. Returns the span of the symbol if renameable, or `null`/error if not.

### Phase 3.4: Tests

- [ ] `tests/lsp/test_rename.py`:
  - `test_rename_local_variable_in_function_body`
  - `test_rename_top_level_function_single_file`
  - `test_rename_top_level_function_across_modules`
  - `test_rename_struct_field_updates_all_accesses`
  - `test_rename_method_updates_all_calls`
  - `test_rename_enum_variant_updates_construction_and_match`
  - `test_rename_rejects_keyword` — cannot rename to `if`, `match`, etc.
  - `test_rename_rejects_name_already_in_scope_at_top_level`
  - `test_rename_rejects_name_shadowed_by_local`
  - `test_rename_rejects_invalid_identifier` — cannot rename to `123` or `my-name`
  - `test_prepare_rename_returns_span_for_valid_symbol`
  - `test_prepare_rename_returns_error_for_keyword`

---

## Phase 4 — LOW sweep

2-3 items from the ledger that fit the LSP lens: VS Code extension polish, stale JSON schemas, LSP protocol version bump if needed.

---

## Phase 5 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.38.0
- [ ] `CHANGELOG.md [4.38.0]` — LSP navigation
- [ ] `docs/reference.md` §Editor Integration — find-references + rename subsections
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Reverse reference index populated by `rebuild_file` | workspace fixtures exercise it |
| 2 | Find-references on local variable works | `test_find_references_local_variable` |
| 3 | Find-references cross-module works | `test_find_references_top_level_function_cross_module` |
| 4 | Find-references on struct field works | corresponding test |
| 5 | Find-references includes declaration when flag set | `test_find_references_include_declaration_flag` |
| 6 | No false positives on shadowed locals | `test_find_references_no_false_positives_on_shadowed_local` |
| 7 | Rename validates invalid identifiers | `test_rename_rejects_invalid_identifier` |
| 8 | Rename rejects keyword targets | `test_rename_rejects_keyword` |
| 9 | Rename rejects name conflicts at top level | corresponding test |
| 10 | Rename rejects shadowing conflicts for locals | corresponding test |
| 11 | Rename applies across files atomically | integration test with a 3-file workspace |
| 12 | `prepareRename` handler works | `test_prepare_rename_*` |
| 13 | Standard closeout clean | CI logs |

---

## What v4.38.0 explicitly does NOT do

- **Semantic rename that updates comments or docstrings** — v5.x. v4.38.0 only touches actual symbol occurrences.
- **Rename that changes the symbol's type or visibility** — out of scope.
- **Rename with automatic import updates** — imports using the renamed name update, but imports using a path that references the renamed symbol don't get automatic re-export updates. v5.x.
- **Undo support beyond the client's native undo** — the client handles it.
- **Cross-workspace rename** (multi-root workspaces) — v5.x.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Rename validation misses a scope conflict | medium | high | Comprehensive test cases; any missed conflict surfaces as broken code after rename — easy to repro, easy to fix |
| Reverse reference index grows too large for huge workspaces | low | medium | Measured; if problematic, lazy-populate on first query |
| `textDocument/prepareRename` is client-specific — VS Code doesn't use it uniformly | low | low | Test against VS Code headless; fall back to raw `rename` handler |

---

## Reference

- LSP 3.17 spec §Language Features §References + §Rename
- [`v4.37.0/PLAN.md`](../v4.37.0/PLAN.md) — the workspace index this release extends

---

## After v4.38.0

v4.39.0 adds completion (imports, type names, field access) on top of the same index.
