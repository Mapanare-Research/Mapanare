# Mapanare v4.37.0 — LSP Foundation (Workspace Index + Go-to-Definition + Hover)

> **First release of Arc 2.** Editor-tooling work. No new language
> syntax, no new compiler capability — pure glue on top of the
> existing parser + semantic checker. v4.37.0 builds the workspace-
> wide symbol index that the rest of the arc depends on.

**Status:** DONE (2026-04-12)
**Breaking:** No (LSP is a supplementary protocol; existing CLI unchanged)
**Prerequisite:** v4.36.0 (arc 1 panel PASS)
**Delta review:** No (no grammar / MIR / emitter changes)
**Full panel:** No (cadence fires at v4.41.0)
**Estimated work:** 2 sprints (index design is the hard part)
**Theme:** Make go-to-definition work across modules. Make hover show inferred types. First real editor-tooling upgrade in 14 releases.

---

## Why LSP now

The v4.26.0 Boa review flagged the LSP as "present but basic." The recovery arc deliberately did not touch it — feature work was frozen. Arc 1 re-enabled feature work and shipped four language surface features. Arc 2 catches up the developer experience so the new surface is actually usable in an editor.

Specifically, the v4.26.0 observation was that the existing LSP only handled within-file go-to-definition. Cross-module navigation — clicking a function call and jumping to the function definition in another file — did not work. That's the single biggest day-to-day LSP gap and v4.37.0 closes it.

The rest of Arc 2 adds find-references (v4.38.0), rename refactoring (v4.38.0), completion (v4.39.0), and diagnostic streaming (v4.40.0). Each release delivers one coherent slice. v4.37.0 is the foundation: the workspace index that every other release reuses.

---

## Scope

### Workspace index

- **Data structure:** `WorkspaceIndex` class mapping `(module_name, symbol_name) → SymbolDef`. `SymbolDef` carries: the `Path` to the source file, the `Span` of the definition, the inferred type, the kind (`fn`, `struct`, `enum`, `trait`, `let`, `type`), and visibility.
- **Build:** walk the workspace root on LSP initialization. Parse every `.mn` file. For each file, run the semantic pass to populate types. Collect every top-level symbol into the index. Total build time scales with workspace size — for the Mapanare self-hosted compiler's 15,000 lines across 11 modules, expect ~300ms.
- **Update:** on every `textDocument/didSave`, re-parse the saved file, re-run the semantic pass, replace the file's symbols in the index. O(1) lookup, O(file size) update. Incremental, not full rebuild.
- **Persistence:** none. The index is in-memory, rebuilt on every LSP server start. Persistence is a v5.x optimization.

### Go-to-definition

- LSP method: `textDocument/definition`
- Input: a `TextDocumentPositionParams` (file URI + line/column)
- Output: a `Location` (file URI + range) or `null` if no symbol under cursor
- Algorithm:
  1. Parse the file if not already cached.
  2. Find the AST node under the cursor.
  3. If it's an identifier reference, resolve via the semantic checker's scope resolution (same logic that emits "undefined symbol" errors at compile time).
  4. If the resolved symbol has a `Path` in its `SymbolDef`, return a `Location` pointing at that file + range.
  5. If the symbol is a local variable, return a `Location` at the binding site in the same file.
- **Cross-module:** the v4.37.0 improvement. Resolve via `WorkspaceIndex` for top-level symbols whose module is not the current file's module.

### Hover

- LSP method: `textDocument/hover`
- Input: a `TextDocumentPositionParams`
- Output: a `Hover` with `contents` (Markdown) and `range`
- Algorithm:
  1. Find the AST node under the cursor.
  2. Run type inference on the enclosing function up to the cursor position.
  3. For an identifier, return its declared or inferred type.
  4. For a function call, return the function's full signature.
  5. For a struct field access, return the field's type.
  6. Format via `diagnostics.py`'s renderer for consistency with CLI error messages.

---

## Phase 1 — Workspace index

### Phase 1.1: Data structures

- [ ] `mapanare/lsp/workspace.py` — new module (or extend existing LSP module). Define:

  ```python
  @dataclass
  class SymbolDef:
      module: str
      name: str
      kind: Literal["fn", "struct", "enum", "trait", "let", "type", "impl"]
      path: Path
      span: Span  # location of the definition header
      body_span: Optional[Span]  # full body if applicable
      type_expr: Optional[Type]  # resolved type; None if not yet typed
      visibility: Literal["pub", "internal"]
      doc_comment: Optional[str]  # for hover display

  @dataclass
  class FileEntry:
      path: Path
      last_mtime: float
      ast: Optional[Program]  # cached AST
      symbols: list[SymbolDef]  # top-level symbols in this file
      imports: list[ImportDecl]  # for cross-ref

  class WorkspaceIndex:
      files: dict[Path, FileEntry]
      symbols_by_name: dict[tuple[str, str], SymbolDef]  # (module, name) → SymbolDef
      # ... methods below
  ```

- [ ] `Workspace.scan_root(root_path: Path) -> None` — walk the tree, find every `.mn` file, call `rebuild_file(path)` for each.
- [ ] `Workspace.rebuild_file(path: Path) -> None` — parse the file, run semantic pass, populate `FileEntry.symbols`, update `symbols_by_name` (remove old entries for this file first, then add new).
- [ ] `Workspace.lookup(module: str, name: str) -> Optional[SymbolDef]` — O(1) query.
- [ ] `Workspace.symbols_in_file(path: Path) -> list[SymbolDef]` — for outline views (LSP `textDocument/documentSymbol`).

### Phase 1.2: Semantic integration

- [ ] `mapanare/semantic.py` — the semantic checker already produces `SymbolDef`-shaped data during scope resolution. Expose it via a new public method `collect_top_level_symbols(program: Program) -> list[SymbolDef]` that returns the collected symbols after the semantic pass.
- [ ] Handle partial failures: if a file has a semantic error, still return whatever symbols were successfully resolved. The LSP must function on broken code — that's when users need hover/go-to-def the most.

### Phase 1.3: Watchers and update protocol

- [ ] `Workspace.handle_did_save(uri: str, text: str) -> None` — called from the LSP server on `textDocument/didSave`. Invalidates the file cache, re-runs parse + semantic, updates the index.
- [ ] `Workspace.handle_did_open(uri: str, text: str) -> None` — same path.
- [ ] `Workspace.handle_did_change(uri: str, new_text: str) -> None` — debounced. Don't re-index on every keystroke; wait 300ms for idle. v4.40.0 will add streaming diagnostics that use this same mechanism.
- [ ] For v4.37.0 the simple approach: only rebuild on save. `didChange` just updates a pending-text buffer used by hover/definition queries.

### Phase 1.4: Tests

- [ ] `tests/lsp/fixtures/workspace_a/` — small test workspace with 3 modules: `main.mn`, `helpers.mn`, `types.mn`. Cross-module imports and references.
- [ ] `tests/lsp/test_workspace_index.py`:
  - `test_scan_root_finds_all_files` — expect 3 files indexed
  - `test_scan_root_collects_top_level_symbols` — expect `main`, `helpers::helper_fn`, `types::Point`, etc.
  - `test_lookup_by_module_and_name` — O(1) query returns `SymbolDef` with correct fields
  - `test_rebuild_file_replaces_old_symbols` — edit `helpers.mn` adding a new function, rebuild, verify new symbol present and old still there
  - `test_rebuild_file_removes_deleted_symbols` — edit `helpers.mn` deleting a function, rebuild, verify symbol is gone
  - `test_handles_file_with_semantic_errors` — a file with a type error still contributes its parse-level symbols

---

## Phase 2 — Go-to-definition

### Phase 2.1: Cursor-to-AST-node resolution

- [ ] `mapanare/lsp/node_at_cursor.py` — new module. Given an AST and a (line, column) cursor position, walk the AST and return the smallest node whose span contains the cursor.
- [ ] Handle: identifier references, function calls, field access, method calls, type references, import paths, pattern bindings.
- [ ] Edge cases: cursor on whitespace (return None); cursor on a keyword (return None — keywords are not symbols); cursor between two tokens (return the left token's AST).

### Phase 2.2: Symbol resolution

- [ ] `mapanare/lsp/definition.py` — new module. `resolve_symbol(ast_node, file_ast, workspace) -> Optional[SymbolDef]`.
- [ ] Algorithm:
  1. If the node is an `Ident` — look it up in the local scope first (walk `Block` ancestors, check `LetDef` / parameter bindings).
  2. If not local, look in the file's top-level symbols.
  3. If not in this file, look in the workspace index by fully-qualified name.
  4. For a `FunctionCall`, resolve the `callee` expression.
  5. For a `FieldAccess`, resolve the receiver's type, then look up the field on that type.
  6. For a `MethodCall`, resolve the receiver's type, find the `impl` block, find the method.
  7. For a `TypeExpr`, resolve the type name.
  8. For an `ImportDecl`, resolve the imported module path.

### Phase 2.3: LSP handler

- [ ] `mapanare/lsp/server.py` (or wherever the LSP dispatch lives) — add `textDocument/definition` handler:
  ```python
  def on_definition(params: TextDocumentPositionParams) -> Optional[Location]:
      file_entry = workspace.files[uri_to_path(params.textDocument.uri)]
      node = node_at_cursor(file_entry.ast, params.position.line, params.position.character)
      if node is None:
          return None
      symbol = resolve_symbol(node, file_entry.ast, workspace)
      if symbol is None:
          return None
      return Location(
          uri=path_to_uri(symbol.path),
          range=span_to_range(symbol.span),
      )
  ```
- [ ] Register the handler via the existing LSP dispatch table.

### Phase 2.4: Tests

- [ ] `tests/lsp/test_goto_definition.py`:
  - `test_goto_local_variable` — cursor on a `let x`, return the binding site
  - `test_goto_function_in_same_file` — cursor on a call, return the fn definition
  - `test_goto_function_in_other_file` — cross-module case, the v4.37.0 improvement
  - `test_goto_struct_field_definition`
  - `test_goto_method_via_impl_block`
  - `test_goto_type_reference`
  - `test_goto_import_target`
  - `test_goto_keyword_returns_none` — cursor on `let` keyword, no symbol
  - `test_goto_whitespace_returns_none`
  - `test_goto_unresolved_symbol_returns_none` — cursor on a typo, gracefully returns None

---

## Phase 3 — Hover

### Phase 3.1: Hover handler

- [ ] `mapanare/lsp/hover.py` — new module. `compute_hover(ast_node, file_ast, workspace) -> Optional[Hover]`.
- [ ] For each node kind, compute the hover content:
  - **Identifier binding (`let x: T = ...`)**: return `x: T` (declared) or `x: <inferred>` if inferred
  - **Function**: return the signature `fn name(a: A, b: B) -> R` + doc comment if present
  - **Function call (cursor on callee)**: same as function hover
  - **Struct field access**: return `field: T`
  - **Type reference**: return the type's definition header
  - **Enum variant**: return `EnumName::Variant(A, B)` with payload types
- [ ] Format output via `diagnostics.py`'s existing formatter — same code path that produces CLI error messages.

### Phase 3.2: Type inference integration

- [ ] The hover needs inferred types. That means re-running the semantic checker on the file in a mode that captures types at every AST node.
- [ ] `mapanare/semantic.py` — add `SemanticChecker.check_with_type_annotations(program) -> dict[SpanKey, Type]` that returns a mapping from span to type. Called once per `handle_did_save`, cached in the `FileEntry`.
- [ ] Hover queries read from the cached type map. No per-query inference.

### Phase 3.3: LSP handler

- [ ] `textDocument/hover` handler:
  ```python
  def on_hover(params: TextDocumentPositionParams) -> Optional[Hover]:
      file_entry = workspace.files[uri_to_path(params.textDocument.uri)]
      node = node_at_cursor(file_entry.ast, params.position.line, params.position.character)
      if node is None:
          return None
      return compute_hover(node, file_entry, workspace)
  ```

### Phase 3.4: Tests

- [ ] `tests/lsp/test_hover.py`:
  - `test_hover_on_declared_let_shows_declared_type`
  - `test_hover_on_inferred_let_shows_inferred_type`
  - `test_hover_on_function_call_shows_signature`
  - `test_hover_on_struct_field_shows_type`
  - `test_hover_on_method_shows_impl_signature`
  - `test_hover_on_enum_variant_shows_payload_types`
  - `test_hover_on_import_shows_module_path`
  - `test_hover_on_whitespace_returns_none`
  - `test_hover_on_broken_expression_returns_partial_info` — graceful degradation

---

## Phase 4 — LOW sweep

v4.37.0 takes 2-3 LOW items from the running carry-forward queue (items surfaced by the v4.36.0 panel or still open from earlier).

Candidates (audit at release time):
- [ ] Self-hosted `loop` grammar construct (closes `A10` from v4.36.0) — if appetite. Would require delta review.
- [ ] VS Code extension icon + README refresh (cosmetic, low-risk)
- [ ] Any LSP-related debt the v4.36.0 panel surfaced

---

## Phase 5 — Closeout

- [ ] Standard closeout: black, ruff, mypy, pytest, golden, stage2, fixed-point, CI gates
- [ ] **New CI requirement:** `tests/lsp/` runs as part of the main pytest suite. Add to `.github/workflows/ci.yml` if not already covered.
- [ ] `VERSION` bumped to 4.37.0
- [ ] `CHANGELOG.md [4.37.0]` entry — LSP foundation; lists the new LSP capabilities
- [ ] `docs/roadmap/v4/v4.37.0/SESSION_REPORT.md` written
- [ ] `docs/reference.md` §Editor Integration — new section describing go-to-def + hover, how to configure in VS Code

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare/lsp/workspace.py` module exists with `WorkspaceIndex` class | file exists + class defined |
| 2 | Workspace scan builds index from a multi-file fixture | `test_scan_root_finds_all_files` passes |
| 3 | Incremental update on save replaces old symbols | `test_rebuild_file_replaces_old_symbols` passes |
| 4 | Go-to-definition resolves local variables | `test_goto_local_variable` passes |
| 5 | Go-to-definition resolves same-file functions | `test_goto_function_in_same_file` passes |
| 6 | **Go-to-definition resolves cross-module functions** (the v4.37.0 improvement) | `test_goto_function_in_other_file` passes |
| 7 | Go-to-definition for struct fields and enum variants | corresponding tests pass |
| 8 | Hover shows declared type for let bindings | `test_hover_on_declared_let_shows_declared_type` passes |
| 9 | Hover shows inferred type when not declared | `test_hover_on_inferred_let_shows_inferred_type` passes |
| 10 | Hover shows function signatures | `test_hover_on_function_call_shows_signature` passes |
| 11 | Hover gracefully handles broken code | `test_hover_on_broken_expression_returns_partial_info` passes |
| 12 | LSP server dispatches `textDocument/definition` and `textDocument/hover` | integration test via mock LSP client |
| 13 | `tests/lsp/` added to CI | `.github/workflows/ci.yml` diff |
| 14 | Standard closeout (lint, golden, stage2, fixed-point, CI gates) all clean | CI logs |
| 15 | SESSION_REPORT written | file exists |

---

## What v4.37.0 explicitly does NOT do

- **Find-references** — v4.38.0
- **Rename refactoring** — v4.38.0
- **Completion** — v4.39.0
- **Incremental re-check on typing** — v4.40.0
- **Code actions / quick fixes** — v5.x backlog
- **Semantic highlighting beyond TextMate grammar** — v5.x backlog
- **Persistent workspace index** — v5.x optimization; v4.37.0 rebuilds on every LSP server start

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Workspace index rebuild on save is too slow for large projects | medium | medium | Target ≤500ms for a 20k-line workspace; profile; if too slow, add per-file semantic caching |
| Cursor-to-AST resolution misses edge cases | medium | low | Comprehensive test fixtures; graceful "return None" on unknown node kinds |
| Semantic checker's symbol collection doesn't match what LSP needs | low | medium | Phase 1.2 integrates early; test against real workspaces |
| LSP protocol version mismatch with VS Code extension | low | low | Pin versions; integration test with VS Code headless mode |

---

## Reference

- LSP 3.17 spec — https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
- `textDocument/definition` — §Language Features
- `textDocument/hover` — same
- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 2

---

## After v4.37.0

v4.38.0 extends the workspace index with reverse references (find-references) and text-based rename refactoring with semantic validation. Same index, new queries on top.
