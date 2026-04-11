# Mapanare v4.39.0 — LSP Completion (Imports + Types + Field Access)

> **Arc 2 release 3.** Context-aware completion using the workspace
> index from v4.37.0. Three completion contexts: after `import`,
> in type position, and after `.` on a value.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.38.0
**Delta review:** No
**Full panel:** No (v4.41.0)
**Estimated work:** 1 sprint
**Theme:** Completion that knows the language's structure.

---

## Scope

### Context 1: After `import `

```mapanare
import std|
            ^-- cursor here, completion offers: stdlib::, local modules, ...
```

- Triggered by typing `import ` (with trailing space).
- Offers: `stdlib::` (expands to installed stdlib module list), local modules in the workspace, installed package names.
- Sub-paths: `import stdlib::m|` offers `math`, `math::abs`, `map`, etc.

### Context 2: In type position

```mapanare
fn foo(x: |)
          ^-- cursor here, completion offers: Int, Float, String, Bool, user types, generic params in scope, ...
```

- Triggered by typing `:` in a type annotation position.
- Offers: builtin types (`Int`, `Float`, `String`, `Bool`, `List`, `Map`, `Option`, `Result`, `Signal`, `Stream`, `Agent`, `Tensor`), user-defined types in scope, generic type parameters bound in the enclosing function/impl/trait.

### Context 3: After `.` on a value

```mapanare
let p: Point = ...
p.|
  ^-- cursor here, completion offers: x, y (struct fields), plus any methods in impl blocks
```

- Triggered by typing `.` after an expression.
- Offers: fields of the expression's type (for structs), methods in `impl` blocks for the type, `::<method>` paths.
- Requires type inference on the receiver expression.

---

## Phase 1 — Completion framework

### Phase 1.1: Trigger character detection

- [ ] `mapanare/lsp/completion.py` — the LSP `textDocument/completion` handler is called on:
  - Trigger characters: `.`, `:`, `:` (for `::`), space-after-`import`
  - Manual invocation (Ctrl+Space)
- [ ] Detect which context applies by inspecting the AST at the cursor position:
  - Inside an `ImportDecl` path → import context
  - Cursor immediately after `:` in a type annotation position → type context
  - Cursor immediately after `.` on an expression → field/method context
  - Otherwise → fallback (identifier completion based on local scope + top-level symbols)

### Phase 1.2: Completion item format

- [ ] Each completion item has:
  - `label`: the name to insert
  - `kind`: `Module`, `Class`, `Function`, `Field`, `Method`, `Variable`, `Constant`
  - `detail`: short type signature or description
  - `documentation`: hover-quality explanation from the `SymbolDef.doc_comment`
  - `insertText`: what to actually type (may include placeholders for function calls)
  - `sortText`: for ranking — local-scope symbols rank above module-level, module-level above stdlib

---

## Phase 2 — Import context

- [ ] `mapanare/lsp/completion.py` `complete_import(prefix: str) -> list[CompletionItem]`:
  1. If prefix is empty: return `stdlib` + every top-level local module + every installed package.
  2. If prefix has one segment (e.g., `stdlib`): return the sub-modules of that namespace.
  3. If prefix has multiple segments (e.g., `stdlib::math`): return the public symbols of that module.
- [ ] stdlib module enumeration: walk `stdlib/` directory at workspace-index-build time, cache the module tree.
- [ ] Local module enumeration: any `.mn` file under the workspace root is a module.

---

## Phase 3 — Type context

- [ ] `mapanare/lsp/completion.py` `complete_type(scope: Scope, workspace: WorkspaceIndex) -> list[CompletionItem]`:
  1. Builtin types: fixed list.
  2. User-defined types in the current scope: from `scope.types`.
  3. Generic type parameters bound in the enclosing function/impl/trait: from `scope.generic_params`.
  4. Imported types from other modules: from the workspace index.
- [ ] Format: `Int`, `Float`, `String`, `Bool`, `List<T>`, `Map<K, V>`, etc. The completion fills in type parameters as placeholders where relevant.

---

## Phase 4 — Field/method context

### Phase 4.1: Receiver type inference

- [ ] `mapanare/lsp/completion.py` — reuse the v4.37.0 type-annotation cache (`SemanticChecker.check_with_type_annotations`) to look up the receiver expression's inferred type.
- [ ] If the receiver is a struct type, enumerate the struct's fields.
- [ ] If the receiver has an `impl` block (or multiple via traits), enumerate the methods.
- [ ] If the receiver type is `Option<T>` / `Result<T, E>` / `List<T>` / `Map<K, V>`, enumerate the builtin methods (`is_some`, `unwrap`, `map`, `and_then`, `len`, `push`, etc.).

### Phase 4.2: Method signature formatting

- [ ] For each method completion, format the insertion text to include the argument placeholders:
  ```
  foo($1, $2)$0
  ```
  Where `$N` are LSP snippet placeholders. The editor jumps to each in turn as the user tabs through.

---

## Phase 5 — Fallback identifier completion

- [ ] When no specific context matches (manual Ctrl+Space in the middle of a block), offer every identifier currently in scope:
  - Local variables from enclosing scopes
  - Parameters from the enclosing function
  - Top-level symbols in the current module
  - Imported symbols from `use` declarations
- [ ] Rank: inner scope > outer scope > module top-level > imports > stdlib.

---

## Phase 6 — Tests

- [ ] `tests/lsp/test_completion.py`:
  - `test_import_completion_offers_stdlib`
  - `test_import_completion_offers_local_modules`
  - `test_import_sub_path_completion` — `stdlib::m` offers `math`, `map`
  - `test_type_completion_offers_builtins`
  - `test_type_completion_offers_user_types`
  - `test_type_completion_offers_generic_params` — inside a `fn foo<T>(x: |)`, `T` is offered
  - `test_field_completion_on_struct`
  - `test_method_completion_on_option`
  - `test_method_completion_on_user_impl`
  - `test_fallback_completion_offers_locals`
  - `test_fallback_completion_ranks_inner_scope_first`
  - `test_completion_respects_visibility` — doesn't offer `internal` symbols from other modules

---

## Phase 7 — LOW sweep

2-3 items as usual. LSP-relevant candidates: VS Code snippet refresh, schema file lint.

---

## Phase 8 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.39.0
- [ ] `CHANGELOG.md [4.39.0]` — LSP completion
- [ ] `docs/reference.md` §Editor Integration — completion subsection
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Trigger detection identifies import / type / field contexts | unit tests cover each |
| 2 | Import completion offers stdlib modules | `test_import_completion_offers_stdlib` |
| 3 | Import completion offers local modules | `test_import_completion_offers_local_modules` |
| 4 | Import sub-path completion works | `test_import_sub_path_completion` |
| 5 | Type completion offers builtins | `test_type_completion_offers_builtins` |
| 6 | Type completion offers user types in scope | `test_type_completion_offers_user_types` |
| 7 | Type completion offers generic parameters | `test_type_completion_offers_generic_params` |
| 8 | Field completion on struct types | `test_field_completion_on_struct` |
| 9 | Method completion on Option / Result / user impls | corresponding tests |
| 10 | Fallback completion ranks by scope depth | `test_fallback_completion_ranks_inner_scope_first` |
| 11 | Visibility respected | `test_completion_respects_visibility` |
| 12 | Standard closeout clean | CI logs |

---

## What v4.39.0 explicitly does NOT do

- **Auto-import** — when completing a type that's not imported, v4.39.0 does not auto-add the import. That's a v5.x feature that requires thinking about whether the user wanted a local type or a module type.
- **Snippet-based completions for common patterns** (e.g., `match<Tab>` expanding to a full match expression) — nice but not in scope.
- **Learning from usage patterns** — v5.x if ever.
- **Completion in comments** — no.

---

## Reference

- LSP 3.17 §Language Features §Completion
- [`v4.37.0/PLAN.md`](../v4.37.0/PLAN.md) — workspace index

---

## After v4.39.0

v4.40.0 adds diagnostic streaming (incremental re-check on save/idle) and publishes a new VS Code extension build.
