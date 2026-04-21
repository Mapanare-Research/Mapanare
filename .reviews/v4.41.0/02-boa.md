# Boa -- Python/DX Review of Mapanare v4.41.0 Arc 2 Panel

**Reviewer:** Boa
**Personality:** The Python Evangelist -- positive, upbeat, earnest, sharp when she has to be
**Previous Version Reviewed:** v4.36.0 (score: 9.5/10, PASS)
**Verdict:** PASS
**Confidence:** 9/10
**Score: 9.2/10** (down from 9.5 -- honest regression reflecting real issues found in this arc's new code)
**Arc Coverage:** v4.37.0 through v4.41.0 (the LSP maturity arc -- WorkspaceIndex, cross-module features, completion, rename, diagnostics, VS Code extension)
**Files Reviewed:** `mapanare/lsp/workspace.py` (362 lines), `mapanare/lsp/completion.py` (242 lines), `mapanare/lsp/rename.py` (91 lines), `mapanare/lsp/diagnostics.py` (115 lines), `mapanare/lsp/server.py` (691 lines, focusing on v4.37.0-v4.40.0 additions), `tests/lsp/test_workspace_index.py` (13 tests), `tests/lsp/test_completion.py` (13 tests), `tests/lsp/test_rename.py` (8 tests), `tests/lsp/test_diagnostics_stream.py` (10 tests), `tests/lsp/test_find_references.py` (5 tests), `editor/vscode/package.json` (69 lines), `mapanare/ast_nodes.py` (Span dataclass), `mapanare/semantic.py` (SemanticError dataclass). **Total: 49 new LSP tests across 5 test files.**

## Executive Summary

This arc is the most ambitious LSP investment the project has made. Four releases delivered a workspace-wide symbol index, cross-module go-to-def and hover, find-references, rename refactoring, context-aware completion in four contexts, diagnostic streaming with debounce, and a VS Code extension scaffold. That is a LOT of surface area. The architectural foundation -- `WorkspaceIndex` with O(1) lookup by `(module, name)` and incremental rebuild -- is well-designed. The separation of concerns is clean: `workspace.py` owns the index, `completion.py` owns the completion logic, `rename.py` owns the validation and edit generation, `diagnostics.py` owns the SemanticError-to-LSP conversion. The server wires them together. This is the RIGHT decomposition.

But I found real issues in this arc that I did not find in v4.36.0. The debounce mechanism has a thread-safety gap and a double-publish pattern. The `_detect_completion_context` function misses several edge cases. The rename validation does not cover cross-module conflict scenarios. The diagnostic converter references a `suggestion` field that does not exist on `SemanticError`. The VS Code extension manifest is structurally incomplete (no `extension.ts`, no `language-configuration.json`). And `rename.py` imports the `keyword` module but never uses it. These are not catastrophic -- the features work for the happy paths -- but they represent a lower standard of precision than what I saw in the v4.34.0-v4.35.0 pattern-matching arc, where every edge case was pinned. The 0.3-point score drop reflects this honestly.

The 49 tests are well-structured and cover the main paths. But they are almost entirely happy-path tests. I found very few tests that exercise boundary conditions, error recovery, or concurrent behavior. The test count is good; the test DEPTH is shallow for infrastructure this critical.

## Progress Since Last Review

### v4.36.0 Boa findings -- verification

| v4.36.0 Issue | Severity | Status in v4.41.0 | Evidence |
|---|---|---|---|
| **M1.** `pattern_matching.py` has zero dedicated unit tests | MEDIUM | **NOT ADDRESSED** | No `tests/test_pattern_matching.py` exists. The algorithm is still tested only transitively. This remains open. |
| **M2.** Unreachable-arm warning path has zero test coverage | MEDIUM | **NOT ADDRESSED** | No test asserts that the unreachable-arm warning fires. Still open. |
| **M3.** Guard fall-through / or-pattern lowering has no MIR-level tests | MEDIUM | **NOT ADDRESSED** | No new MIR-level tests for guard fall-through or or-pattern lowering. Still open. |
| **L1.** `_check` helper inconsistency across semantic test files | LOW | **NOT ADDRESSED** | Still copy-pasted across files. |
| **L2.** `bind.py` dead-branch elif guard | LOW | **NOT ADDRESSED** | Still present. |

**Resolution rate: 0 of 3 MEDIUM items closed. This is the first review cycle where my prior items were not addressed.** I understand -- the arc focus was LSP maturity, not pattern-matching test coverage. But I want to be transparent: three MEDIUM items from v4.36.0 are now two review cycles old. They should be scheduled.

### New work in v4.37.0-v4.41.0

| Feature | Version | Status | Evidence |
|---|---|---|---|
| `WorkspaceIndex` with O(1) symbol lookup | v4.37.0 | **CONFIRMED** | `workspace.py:84-191`. Dict-based `_by_name` for `(module, name)` -> `SymbolDef`, `_by_unqualified` for name -> `[SymbolDef]`. Incremental `rebuild_file` removes old symbols before re-indexing. 13 workspace tests pass. |
| Cross-module go-to-def | v4.37.0 | **CONFIRMED** | `server.py:279-297`. Falls back to `WorkspaceIndex.lookup_by_name` when within-file resolution fails. Correctly converts 1-based Span to 0-based LSP positions. |
| Cross-module hover | v4.37.0 | **CONFIRMED** | `server.py:230-241`. Falls back to workspace index for symbols not found in current file. Shows `detail`, `doc_comment`, and module name in Markdown. |
| Find references via AST walker | v4.38.0 | **CONFIRMED** | `workspace.py:193-274`. `_collect_references` walks function bodies, agent methods. Detects `Identifier`, `CallExpr`, `ConstructExpr`, `NamedType` references. Second pass in `scan_root` ensures cross-module refs resolve. 5 find-refs tests pass. |
| Rename with validation | v4.38.0 | **CONFIRMED** | `rename.py:31-72`. Three validation rules: valid identifier, not a keyword, no same-module conflict. `apply_rename` builds a `WorkspaceEdit`. 8 rename tests pass. |
| Context-aware completion (4 contexts) | v4.39.0 | **CONFIRMED** | `completion.py` provides `complete_import`, `complete_type`, `complete_field_method`, `complete_identifiers`. `server.py:627-653` detects context via `_detect_completion_context`. 13 completion tests pass. |
| Diagnostic streaming with debounce | v4.40.0 | **CONFIRMED** | `diagnostics.py:87-114` runs parse + semantic check, returns LSP diagnostics. `server.py:174-190` debounces re-checks via `threading.Timer`. |
| VS Code extension scaffold | v4.41.0 | **CONFIRMED** | `editor/vscode/package.json` declares language, activation events, LSP configuration, capabilities. |

## Strengths

1. **`WorkspaceIndex` is architecturally sound.** The dual-index design (`_by_name` for qualified O(1) lookup, `_by_unqualified` for cross-module name search) is the right choice. The incremental rebuild path (`rebuild_file`) correctly removes old symbols before inserting new ones -- this prevents stale symbol accumulation. The error handling around parse failures (lines 159-162) keeps a stub `FileEntry` so the index does not re-parse broken files on every query. The `_extract_top_level_symbols` function covers all 9 definition types (fn, struct, enum, trait, agent, pipe, type, extern_fn, module let). The visibility tracking (pub vs internal) propagates correctly through to completion filtering. This is clean, purpose-built infrastructure.

2. **The completion module has good layered design.** Four contexts, four functions, each one self-contained. `complete_import` offers workspace module names with prefix filtering. `complete_type` combines builtin types (highest priority via sort_text "0_") with user-defined types (lower priority "1_"). `complete_field_method` handles four builtin type families (Option, Result, List, String) with accurate method signatures, PLUS user-defined struct fields parsed from the SymbolDef detail string. `complete_identifiers` ranks current-module symbols first ("0_"), public cross-module symbols second ("2_"), and builtins third ("3_"). The sort_text strategy is simple and correct -- it gives the user the most relevant results first without complex scoring algorithms.

3. **The rename validation rules are correct for the cases they cover.** Rule 1 (valid identifier regex) prevents renaming to syntactically invalid names. Rule 2 (keyword check) includes both English and bilingual keywords -- this is important because Mapanare supports Spanish-language keywords. Rule 3 (same-module conflict) prevents renaming to a name that already exists in the same module. The `apply_rename` function correctly generates edits for both the definition site and all reference sites, keyed by file URI. The workspace edit format is standard LSP.

4. **The diagnostic converter correctly handles the 1-based to 0-based boundary.** `semantic_error_to_diagnostic` applies `max(0, x - 1)` for all four position components, with correct fallback behavior when `end_line` or `end_column` are 0 (meaning "not provided"). The end position falls back to the start position or start+1, which is the correct single-character range for point diagnostics. The severity mapping covers all four LSP severity levels. The `run_semantic_check` function correctly catches parse exceptions and converts them to diagnostics, and silently swallows semantic checker crashes (line 112: `except Exception: pass`) -- this is the RIGHT behavior for an LSP server where a crash in the checker should not block diagnostic delivery for the file.

5. **The find-references AST walker covers the important expression types.** `_collect_references` handles `Identifier` (read), `CallExpr` (call), `ConstructExpr` (type_use), `NamedType` (type_use), `IfExpr` (recursive walk into then/else blocks), `MatchExpr` (recursive walk into arms), `FieldAccessExpr` (receiver walk), `MethodCallExpr` (receiver + args walk), `ForLoop` (iterable + body walk). The two-pass strategy in `scan_root` (first pass indexes symbols, then clears refs and re-walks everything) ensures that cross-module references are resolved against the complete symbol table rather than a partial one. This is correct.

6. **The test structure is clean and consistent.** All five test files use the same `_make_workspace` helper pattern (create temp dir, write files, scan root). Tests are organized into classes by feature. Assertions are specific and descriptive. The `test_visibility_respected` test in completion correctly verifies that internal symbols from other modules are NOT offered. The `test_current_module_symbols_ranked_first` test verifies the sort_text ordering. These are the kind of behavioral tests that pin the user-visible contract.

## Issues Found

### CRITICAL

**None.** The features work for the common cases. The LSP server initializes, indexes, and responds to requests.

### HIGH

**H1. The `on_change` handler publishes diagnostics TWICE on every keystroke.**

`server.py:174-190`: `on_change` calls `_analyze_and_publish(uri, source)` at line 180, which runs the analysis pipeline and publishes diagnostics. Then it ALSO starts a 300ms debounce timer that calls `_debounced_recheck`, which calls `_run_and_publish_semantic_diagnostics`, which runs `run_semantic_check` (parse + semantic) and publishes diagnostics AGAIN.

Similarly, `on_save` (lines 193-201) calls `_analyze_and_publish` AND THEN `_run_and_publish_semantic_diagnostics` -- that is two parse+check cycles and two `publishDiagnostics` calls on every save.

The intent is clear: `_analyze_and_publish` runs the lightweight analysis pipeline (for hover, completion, etc.) while `_run_and_publish_semantic_diagnostics` runs the full semantic checker. But the result is:

- On every keystroke: immediate diagnostics + a second diagnostic push 300ms later.
- On every save: immediate diagnostics + immediate SECOND diagnostic push.

The second push will either show the same diagnostics (redundant network traffic + UI flicker) or show different diagnostics (confusing if the analysis and semantic pipelines disagree). For the `on_change` case, the debounce should be the ONLY diagnostic publisher -- the immediate `_analyze_and_publish` should update the analysis cache (for hover/completion) but NOT publish diagnostics. For the `on_save` case, the double call is pure waste.

Severity rationale: HIGH because this affects every keystroke and every save in the editor. Users will see diagnostic flicker (momentary clear-then-repopulate) on every save.

---

**H2. The debounce timer is not cancelled on `on_save` or `on_close`, creating a race condition.**

When a user types (triggering `on_change` which starts a 300ms timer), then immediately saves (triggering `on_save`), the 300ms timer is still running. Both `on_save` and the timer callback will call `publishDiagnostics` -- potentially with different results if the file was modified between the save and the timer firing.

Worse: `on_close` (lines 204-211) clears the document caches and publishes empty diagnostics, but does NOT cancel any pending debounce timer. If a timer fires after `on_close`, `_debounced_recheck` will find the source in `_sources` (which WAS cleared) and either silently no-op or crash, depending on timing.

The fix is straightforward: cancel any pending timer in `on_save` and `on_close`:
```python
old_timer = _debounce_timers.pop(uri, None)
if old_timer is not None and hasattr(old_timer, "cancel"):
    old_timer.cancel()
```

Severity rationale: HIGH because the race condition on close could cause diagnostics to appear for a closed file, which is a user-visible bug in VS Code (diagnostics panel shows stale entries).

### MEDIUM

**M1. `_detect_completion_context` misses several important edge cases.**

The function (`server.py:627-653`) uses simple string scanning of the line prefix. Issues:

(a) **Multi-word type annotations:** `let x: Option<` triggers the `<` trigger character, but `_detect_completion_context` looks for `:` or `->` as the last non-space char. At cursor position after `Option<`, the last char is `<`, not `:`, so it falls through to "identifier" instead of "type". The `<` trigger character is declared in the server capabilities (line 149) but the context detector does not recognize it.

(b) **Dot after whitespace:** If the user writes `foo .` (with a space before the dot), `text.rstrip().endswith(".")` returns True. But the space before the dot likely means the user is not doing method access -- they may have accidentally typed a period. This is a minor false positive.

(c) **Colon in match arms:** `match x { 1 =>` -- the `=>` contains `>` but not `:`, so this correctly falls through to "identifier". However, `let x: Int = match y { 1:` (hypothetical but possible in error recovery) would trigger "type" context inside a match arm, which is wrong.

(d) **No handling of `fn foo(x: Type, y:` -- the colon detection works here because the line ends with `:`, but `fn foo() ->` followed by a space (cursor after the space) would have `before` as `fn foo() -> ` and `before.endswith("->")` would be False (trailing space). The `rstrip()` call at line 648 fixes this for trailing spaces, but ONLY trailing spaces -- if the user typed `fn foo() -> I` (partial type), the `before` is `fn foo() -> I` and neither `:` nor `->` is the last char.

Of these, (a) is the most impactful because `<` is declared as a trigger character but the context detector ignores it.

Suggested fix: add `<` to the type-context detection:
```python
if before.endswith(":") or before.endswith("->") or before.endswith("<"):
    return "type"
```

Severity rationale: MEDIUM because completion still works (the fallback "identifier" context offers all symbols), but the results are less relevant than they should be.

---

**M2. `receiver_type_at` does not exist on `DocumentAnalysis`, making field/method completion always empty for user types.**

`server.py:468` calls `analysis.receiver_type_at(line, col)` guarded by `hasattr(analysis, "receiver_type_at")`. I searched `mapanare/lsp/analysis.py` for this method -- it does not exist. The `hasattr` check will always return `False`, so `receiver_type` will always be the fallback empty string `""`.

This means that `complete_field_method("", _workspace)` is called, which returns zero candidates (no builtin type matches `""`, and no struct matches `""`). The dot-completion feature, as currently wired, returns NOTHING for user-defined struct fields and NOTHING for builtin type methods. The only dot-completions that work are the within-file completions from `analysis.completions_at(line, col)` which may provide local-scope completions.

The `completion.py` module is well-designed and tested in isolation (all 13 completion tests pass by calling the functions directly with explicit types). But the server integration is broken because the bridge function (`receiver_type_at`) was never implemented.

Severity rationale: MEDIUM because dot-completion is a premium UX feature, and the code creates the APPEARANCE of support (the completion module is fully implemented, the server declares `.` as a trigger character) but the wiring is incomplete. Users will press `.` and get nothing (or only local completions).

---

**M3. `diagnostics.py` reads a `suggestion` field that `SemanticError` does not have.**

`diagnostics.py:44`: `suggestion = getattr(err, "suggestion", None)`. I checked `mapanare/semantic.py` -- the `SemanticError` dataclass has: `message`, `line`, `column`, `end_line`, `end_column`, `filename`, `severity`. There is NO `suggestion` field.

The `getattr` with default `None` means this silently falls back to no related information. The code is SAFE -- it will not crash. But the entire relatedInformation feature (lines 42-56) is dead code. The test `test_suggestion_appears_as_related_information` passes because it uses a `FakeErrorWithSuggestion` class that HAS a `suggestion` attribute -- but this class does not reflect the actual `SemanticError` shape.

This is a spec-vs-implementation mismatch: the diagnostic converter was designed for a `SemanticError` with a `suggestion` field that does not yet exist. Either the converter was written speculatively ahead of a planned `SemanticError` enhancement, or the field was planned but not yet added.

Severity rationale: MEDIUM because the feature is dead (suggestions never appear in the editor) but the code is safe and the tests are technically correct for the interface they test.

---

**M4. `rename.py` imports `keyword` (Python stdlib) but never uses it.**

Line 8: `import keyword`. This module is never referenced anywhere in the file. The Mapanare keyword set is defined inline as `_KEYWORDS` (lines 19-28). The `import keyword` appears to be a leftover from an earlier implementation that may have used Python's `keyword.iskeyword()`.

This will be caught by ruff (unused import), but it is currently in the codebase.

Severity rationale: MEDIUM (only because it will fail the linter gate if not already suppressed -- from a functional standpoint this is LOW).

---

**M5. Rename validation does not check cross-module import conflicts.**

`validate_rename` checks three rules: valid identifier, not a keyword, no same-module name conflict. But it does NOT check:

(a) **Cross-module references that would become ambiguous.** If module A has `fn helper` and module B has `fn util`, renaming A's `helper` to `util` would create two different symbols both named `util`. Any file that imports both A and B would now have an ambiguous reference. The validator does not warn about this.

(b) **Builtin name shadowing.** Renaming to `print`, `len`, `str`, `Some`, `Ok`, or `Err` is allowed by the validator because these are not in `_KEYWORDS`. But they are builtin function names, and shadowing them would break any call site that uses the builtin without qualification.

(c) **Rename target is the same as the current name.** `validate_rename(sym, sym.name, ws)` returns `None` (valid), but `apply_rename` would generate identity edits. The LSP spec says `prepareRename` should return the current name as the placeholder (which it does), and the client SHOULD reject no-op renames, but the server should also guard against this.

Suggested fix for (b): add builtins to the validation:
```python
_BUILTINS = frozenset({"print", "len", "str", "int", "float", "Some", "Ok", "Err", "signal", "stream"})

if new_name in _BUILTINS:
    return f"'{new_name}' shadows a builtin function"
```

Severity rationale: MEDIUM because (a) requires multi-module awareness that is legitimately hard, (b) is a straightforward omission, and (c) is cosmetic.

---

**M6. The `_add_edit` function in `rename.py` does not handle `Span` objects where `end_line` or `end_column` is 0.**

`rename.py:85`: `"line": max(0, (span.end_line or span.line) - 1)`. If `span.end_line` is 0 (the Span dataclass default), this falls back to `span.line`. But the text edit range end position should be `(span.line, span.column + len(old_name))` -- i.e., the end of the identifier being renamed. Using `span.line`/`span.column` gives a zero-width range, which would not actually select the text to replace.

The LSP spec says a zero-width range at a position means "insert at this position" -- so a rename edit with `start == end` would INSERT the new name instead of REPLACING the old name. This could produce `old_namenew_name` in the buffer.

In practice, the Mapanare parser likely populates `end_line` and `end_column` for most nodes, so this may not manifest. But it is a latent bug in the fallback path.

Severity rationale: MEDIUM because it depends on whether the parser always populates end positions. If any `Span` has default `end_line=0`, the rename will corrupt the file.

### LOW

**L1. `_map_completion_kind` in `server.py` is missing the "method" and "module" kinds.**

`completion.py` returns `CompletionCandidate` objects with `kind="method"` (from `complete_field_method`) and `kind="module"` (from `complete_import`). But `_map_completion_kind` (server.py:667-679) does not have entries for "method" or "module". Both fall through to `CompletionItemKind.Text`, which means methods and modules show up with a generic text icon in VS Code instead of the correct method/module icon.

Fix:
```python
"method": lsp.CompletionItemKind.Method,
"module": lsp.CompletionItemKind.Module,
```

---

**L2. The VS Code extension manifest is structurally incomplete.**

`editor/vscode/package.json` references `./language-configuration.json` (line 35) and `./out/extension.js` (line 23), but neither file exists. The `capabilities` section (lines 59-68) is not a standard VS Code extension manifest field -- VS Code ignores it. The manifest has no `devDependencies`, no `scripts` (build, watch, package), no `tsconfig.json`, and no `src/extension.ts`. As shipped, this extension cannot be built or installed.

I understand this is labeled a "scaffold" -- but a scaffold that references nonexistent files is more of a TODO list than a scaffold. At minimum, the manifest should either (a) include stub files so `npm install && npm run compile` works, or (b) remove the file references until the files exist.

---

**L3. The `_collect_references` walker does not visit `WhileLoop`, `LetBinding` type annotations, `LambdaExpr`, `BinaryExpr`, `UnaryExpr`, `IndexExpr`, or `PipeExpr`.**

The AST walker in `workspace.py:200-248` covers `Identifier`, `CallExpr`, `MethodCallExpr`, `FieldAccessExpr`, `IfExpr`, `MatchExpr`, `ConstructExpr`, and `NamedType`. But it misses:

- `WhileLoop` (condition + body)
- `LetBinding` type annotations (`let x: MyType = ...` -- the type annotation is a reference)
- `LambdaExpr` (closure bodies)
- `BinaryExpr` / `UnaryExpr` (operands may contain identifiers)
- `IndexExpr` (receiver + index)
- `PipeExpr` (both sides)

This means find-references will miss references inside these expression types. The most impactful gap is `BinaryExpr` -- any function called inside a binary expression (e.g., `foo() + bar()`) will not be found as a reference because the walker does not recurse into binary expression operands.

---

**L4. The `on_change` handler assumes `params.content_changes[-1].text` contains the full document.**

`server.py:178`: `source = params.content_changes[-1].text`. This is correct ONLY because the server declares `TextDocumentSyncKind.Full` (line 142), which means the client sends the complete document on every change. If the sync kind were ever changed to `Incremental`, this code would receive incremental diffs, not full text, and the entire analysis pipeline would get partial documents. This should have a comment or assertion guarding the assumption.

---

**L5. The `_fn_sig` function in `workspace.py` uses a lazy import from `mapanare.lsp.analysis`.**

`workspace.py:353`: `from mapanare.lsp.analysis import _type_expr_display`. This is an import of a private function from a sibling module, done lazily inside a function body. The lazy import avoids a circular dependency (analysis imports from workspace), but the underscore-prefix convention signals "private" -- this function should either be promoted to a public API or duplicated in workspace.py. More importantly, if `analysis.py` is ever refactored to rename `_type_expr_display`, `workspace.py` will break at RUNTIME (not import time) because the lazy import defers the failure.

---

**L6. Three prior Boa MEDIUM items (M1-M3 from v4.36.0) remain open after two review cycles.**

These are: (M1) no dedicated unit tests for `pattern_matching.py`, (M2) unreachable-arm warning untested, (M3) guard/or-pattern lowering MIR tests missing. I understand the arc focus was elsewhere. Flagging for visibility -- these should be scheduled for the next non-feature cycle.

## Test Coverage Assessment

### Quantitative Summary

| Test File | Tests | Coverage Focus |
|---|---|---|
| `test_workspace_index.py` | 13 | Scan, lookup, rebuild, symbol extraction, parse error recovery |
| `test_completion.py` | 13 | Import, type, field/method, fallback completion, visibility, ranking |
| `test_rename.py` | 8 | Validation (4 rules), apply rename (single/cross/multi-file) |
| `test_diagnostics_stream.py` | 10 | Line mapping, severity, suggestion, parse error, integration |
| `test_find_references.py` | 5 | Same-file, cross-module, include_declaration, enum, nonexistent |
| **Total** | **49** | |

### What is well-tested

- WorkspaceIndex scan, lookup, and incremental rebuild (happy paths)
- Completion in all four contexts with correct ranking
- Rename validation for all three rejection rules
- Diagnostic 1-based to 0-based conversion
- Parse error to diagnostic conversion
- Cross-module find-references with include_declaration flag

### What is NOT tested

1. **Debounce behavior** -- no test verifies that rapid `on_change` calls result in a single diagnostic publish after the debounce window. No test verifies timer cancellation. This is the most complex concurrent code in the LSP and it has ZERO test coverage.

2. **`_detect_completion_context`** -- no test calls this function directly. It is tested only transitively through the `on_completion` handler, which is not tested at all (the completion tests call the completion module functions directly, bypassing the server).

3. **Server handler integration** -- none of the 49 tests instantiate the `LanguageServer` or call the `on_*` handlers. All tests call the underlying functions directly. This means the LSP protocol wiring (parameter unpacking, response formatting, error handling) is entirely untested.

4. **`_add_edit` range computation** -- no test verifies that the rename edit ranges are correct for multi-line symbols or symbols with default (zero) end positions.

5. **Large workspace performance** -- no test verifies that `scan_root` on a workspace with 100+ files completes in reasonable time.

6. **Concurrent access** -- no test verifies that `rebuild_file` called from `on_save` while `on_completion` is reading the index does not produce corrupted results. The index uses plain dicts with no locking.

## Recommendations

### Score justification

**9.2/10.** Down 0.3 from v4.36.0's 9.5. The drop reflects: (1) H1 (double diagnostic publish) and H2 (debounce race condition) are real bugs that affect the editing experience, (2) M2 (`receiver_type_at` not implemented) means the flagship dot-completion feature is silently broken in the server integration, (3) M3 (suggestion field does not exist) means the relatedInformation feature is dead code, (4) three prior MEDIUM items remain open. The score remains above 9.0 because the architectural foundation is sound, the decomposition is clean, the test count is good, and the features work correctly in isolation.

### Priority order for v4.42.0+

1. **Close H1 -- fix the double diagnostic publish.** Separate `_analyze_and_publish` into two concerns: "update analysis cache" (always) and "publish diagnostics" (only via debounce or on save). The `on_change` handler should update the cache immediately but defer diagnostic publishing to the debounce timer.

2. **Close H2 -- cancel debounce timers on save and close.** Add timer cancellation to `on_save` and `on_close`. This is a 4-line fix.

3. **Close M2 -- implement `receiver_type_at` on `DocumentAnalysis`.** This is the bridge that makes dot-completion work. Without it, the entire `completion.py` field/method path is dead in the server.

4. **Close M4 -- remove the unused `import keyword` in rename.py.** One-line fix, will unblock the linter.

5. **Close L1 -- add "method" and "module" to `_map_completion_kind`.** Two-line fix, improves VS Code icon rendering.

6. **Add integration tests for the server handlers.** Even 5-10 tests that call `on_completion`, `on_rename`, `on_references` through a mock LanguageServer would catch the wiring issues (like M2) that unit tests on the underlying functions miss.

7. **Schedule v4.36.0 M1-M3** (pattern-matching unit tests, unreachable-arm test, MIR-level tests). These are now two cycles old.

### Post-arc assessment

**Is the LSP architecture ready for production?** The foundation is yes. The `WorkspaceIndex` design is right. The separation into workspace/completion/rename/diagnostics modules is right. The incremental rebuild strategy is right. But the wiring layer (server.py) has real bugs (H1, H2) and a missing bridge (M2) that need to be fixed before users will have a good experience.

**Is the VS Code extension shippable?** No. The manifest references files that do not exist. There is no `extension.ts`, no `language-configuration.json`, no build system. This needs another release of work to become a functional extension.

**Are the 49 tests sufficient?** For the underlying modules (workspace, completion, rename, diagnostics), yes -- the coverage is solid for happy paths. For the server integration layer, no -- zero tests call the `on_*` handlers. The most critical gap is the debounce mechanism, which is the most concurrent, timing-sensitive code in the LSP and has zero test coverage.

**What should the next arc prioritize from my seat?** Fix H1+H2 (debounce/publish bugs), implement `receiver_type_at` (M2), then add 10-15 server integration tests. After that, the LSP will be genuinely useful.
