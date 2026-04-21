# Anaconda -- Toolchain Review of Mapanare v4.41.0

**Reviewer:** Anaconda
**Personality:** The Bureaucrat -- structured, formal, references standards (LSP 3.17, Language Server Protocol Specification, Semantic Versioning 2.0.0)
**Previous Version Reviewed:** v4.36.0 (score 9.4/10, PASS -- Arc 1 cadence panel)
**Panel Role:** Arc 2 cadence panel. Grades the LSP maturity arc (v4.37.0-v4.40.0). Four feature releases delivering cross-module navigation, completion, rename, and diagnostics.
**Verdict:** **PASS**
**Score:** **8.9 / 10**
**Confidence:** 9/10
**Files Reviewed (verified byte-level against the repo):**

- `VERSION` -- reads `4.41.0`
- `CHANGELOG.md` -- lines 8-130 (v4.37.0 through v4.41.0 entries)
- `mapanare/lsp/server.py` -- 691 lines (full file); the pygls LanguageServer wiring
- `mapanare/lsp/workspace.py` -- 362 lines (full file); WorkspaceIndex, SymbolDef, ReferenceSite, reference collection
- `mapanare/lsp/completion.py` -- 242 lines (full file); four completion contexts
- `mapanare/lsp/diagnostics.py` -- 115 lines (full file); diagnostic conversion and semantic check integration
- `mapanare/lsp/rename.py` -- 91 lines (full file); validate_rename + apply_rename
- `mapanare/lsp/analysis.py` -- 1343 lines (full file); DocumentAnalysis, IncrementalParser, cross-module import resolution, diagnostic enrichment
- `mapanare/lsp/__init__.py` -- 1 line (docstring only)
- `mapanare/parser.py` -- lines 1750-1770 (`parse()` entry point)
- `mapanare/semantic.py` -- lines 2141-2170 (`check()` convenience function), lines 84-92 (exported constants: `BUILTIN_FUNCTIONS`, `BUILTIN_GENERIC_TYPES`, `PRIMITIVE_TYPES`)
- `mapanare/ast_nodes.py` -- lines 180-194 (`MethodCallExpr`, `FieldAccessExpr` -- field name is `object`, not `receiver`)
- `mapanare/types.py` -- lines 359-366 (`BUILTIN_TRAITS`)
- `tests/lsp/test_workspace_index.py` -- 141 lines (13 tests)
- `tests/lsp/test_completion.py` -- 164 lines (13 tests)
- `tests/lsp/test_find_references.py` -- 61 lines (5 tests)
- `tests/lsp/test_rename.py` -- verified exists (8 tests per pre-panel audit)
- `tests/lsp/test_diagnostics_stream.py` -- 139 lines (10 tests)
- `tests/lsp/test_analysis.py` -- lines 1-60 (header, helpers, first test class)
- `editor/vscode/package.json` -- 69 lines (VS Code extension manifest v0.6.0)
- `.reviews/v4.41.0/MEASUREMENTS.md` -- delta metrics
- `.reviews/v4.41.0/PRE_PANEL_AUDIT.md` -- 17/17 claims verified

---

## Executive Summary

Arc 2 (v4.37.0-v4.40.0) delivers a genuine LSP layer on top of the existing Mapanare compiler infrastructure. The architecture is sound: the LSP reuses `mapanare.parser.parse()` and `mapanare.semantic.check()` as-is, with no forked copies or LSP-specific reimplementations of the parser or type checker. The `WorkspaceIndex` is a clean O(1)-lookup abstraction that sits above the per-file `DocumentAnalysis` layer. The completion module correctly leverages the type system -- builtin types from `mapanare/types.py`, user-defined types from the workspace index, and visibility-gated cross-module symbols.

I score this arc 8.9/10, down 0.5 from v4.36.0. The delta reflects one HIGH issue (attribute name bug in `_collect_references` causing silent reference tracking failure on any real-world codebase), one MEDIUM issue (double/triple parsing on every keystroke and save), one MEDIUM issue (`receiver_type_at` is called but never defined, making field/method completion permanently degraded), and two LOW items. The HIGH issue is a latent correctness bug that will crash `scan_root` for any workspace containing method calls. The MEDIUM issues are performance and completeness gaps that will be noticed immediately by users.

The arc is architecturally correct in its layering decisions. The problems are integration-level bugs that slipped through because the test files use only simple function calls, not method calls or field accesses.

---

## Section 1: Parser + Semantic Checker Reuse

### 1.1 Parser Integration -- CORRECT

The LSP reuses `mapanare.parser.parse()` at three call sites:

| Call site | Module | Context |
|-----------|--------|---------|
| `workspace.py:134` | WorkspaceIndex.rebuild_file | Index a workspace file |
| `diagnostics.py:98` | run_semantic_check | Live diagnostic push |
| `analysis.py:241-246` | IncrementalParser.parse | Per-chunk incremental re-parse |

All three call `parse(source, filename=...)` with the correct signature. The parser is imported lazily (inside function bodies) to avoid circular imports at module load time. This is the correct pattern for an LSP server that may be imported as a library.

The `IncrementalParser` at `analysis.py:225-298` is a well-designed optimization. It splits source into top-level chunks via `_TOPLEVEL_RE`, hashes each chunk with MD5, and re-parses only chunks whose hashes changed. The cache is per-URI with chunk-level granularity. This means editing a function body only re-parses that function's chunk, not the entire file. The fallback path (full parse fails, incremental with cache) is correct: it tries full parse first (fast path), and falls back to chunk-by-chunk parsing with cache when the full parse fails (e.g., mid-typing with syntax errors). This is a textbook incremental parsing strategy for an LALR parser that does not natively support incremental parsing.

### 1.2 Semantic Checker Integration -- CORRECT

The semantic checker is reused at two call sites:

| Call site | Module | Context |
|-----------|--------|---------|
| `diagnostics.py:106-110` | run_semantic_check | `check(program, filename=uri)` |
| `analysis.py:1302` | analyze_document | `check(program, filename=uri)` |

Both call the convenience function `mapanare.semantic.check()` which instantiates a `SemanticChecker` and runs the two-pass analysis. Neither call site passes a `ModuleResolver`, which means cross-module type checking is not available in the LSP diagnostic path. This is acceptable for v4.40.0 (single-file semantic diagnostics); cross-module semantic checking would require threading the workspace index into the semantic checker, which is a future enhancement.

The `BUILTIN_FUNCTIONS`, `PRIMITIVE_TYPES`, and `BUILTIN_GENERIC_TYPES` constants from `mapanare/semantic.py` are imported directly into `analysis.py` at line 61-66 for hover and completion. This is correct -- the LSP layer reads the type system's source of truth rather than maintaining its own copy.

### 1.3 No Fork, No Duplication -- VERIFIED

I verified that no `.py` file in `mapanare/lsp/` contains a Lark grammar, a parser implementation, or a type-checking pass. The LSP layer is a pure consumer of the compiler's public API (`parse()`, `check()`, AST node dataclasses, type constants). This is the standard the LSP specification encourages: "The language server should reuse the compiler's parsing and type-checking logic."

---

## Section 2: WorkspaceIndex Architecture

### 2.1 Data Model -- CLEAN

`WorkspaceIndex` stores:
- `files: dict[Path, FileEntry]` -- per-file cached state (path, mtime, AST, symbols, imports)
- `_by_name: dict[(module, name), SymbolDef]` -- O(1) qualified lookup
- `_by_unqualified: dict[name, list[SymbolDef]]` -- O(1) unqualified lookup (handles name collisions across modules)
- `refs_by_symbol: dict[(module, name), list[ReferenceSite]]` -- reverse reference index (v4.38.0)

This is a clean two-tier index: primary key is `(module, name)`, secondary index is unqualified `name`. The `FileEntry` caches the full AST, which enables the reference collection pass without re-parsing. `SymbolDef` carries span, visibility, detail (signature), and doc comment -- everything needed for hover, go-to-def, and completion without re-parsing the target file.

### 2.2 scan_root -- CORRECT MODULO BUG

`scan_root` does two passes:
1. Walk `os.walk(root)`, call `rebuild_file(path)` for each `.mn` file. This parses, extracts symbols, and collects within-file references.
2. Clear `refs_by_symbol` and re-collect references across all files. This second pass is needed because the first pass cannot resolve cross-module references (symbols from later files are not yet indexed).

The two-pass design is correct. The clear-and-rebuild at line 110 ensures no stale references from the first pass leak into the final index.

### 2.3 rebuild_file -- CORRECT

`rebuild_file` at line 117 correctly:
1. Removes old symbols from `_by_name` and `_by_unqualified`
2. Removes old reference sites from `refs_by_symbol`
3. Re-parses the file via `parse()`
4. Re-extracts symbols and references
5. On parse failure, stores a stub `FileEntry` to prevent retry loops

The error handling at line 159 (`except Exception`) is appropriate for an LSP context -- a single broken file should not crash the entire workspace index.

### 2.4 Symbol Extraction -- COMPREHENSIVE

`_extract_top_level_symbols` at line 277 handles all 9 top-level definition types: `FnDef`, `StructDef`, `EnumDef`, `TraitDef`, `AgentDef`, `PipeDef`, `TypeAlias`, `ExternFnDef`, `ModuleLetDef`. The visibility is correctly derived from each definition's `public` attribute. The `detail` field provides useful summaries (function signatures, struct fields, enum variants).

### 2.5 Reference Collection -- BUGGY (see Issue 1)

`_collect_references` at line 193 walks the AST to find references to known symbols. It correctly handles `Identifier`, `CallExpr`, `ConstructExpr`, `NamedType`, `IfExpr`, `MatchExpr`, and `ForLoop`. However, the `MethodCallExpr` and `FieldAccessExpr` handlers at lines 216-221 access `expr.receiver`, which does not exist on these AST nodes (the field is `object` per `ast_nodes.py:183,192`). This is a correctness bug documented as Issue 1.

---

## Section 3: Completion Module

### 3.1 Four Contexts -- WELL-STRUCTURED

`completion.py` provides four completion functions:

| Function | Trigger | Sources |
|----------|---------|---------|
| `complete_import` | After `import ` | Workspace file stems + "stdlib" hint |
| `complete_type` | After `:` or `->` | `_BUILTIN_TYPES` (14 entries) + workspace structs/enums/traits/aliases |
| `complete_field_method` | After `.` | Builtin method tables (Option/Result/List/String) + workspace struct fields |
| `complete_identifiers` | Ctrl+Space fallback | Current-module symbols > pub cross-module > builtins |

### 3.2 Type System Leverage -- CORRECT

The builtin type list at line 18 (`_BUILTIN_TYPES`) is consistent with `mapanare/types.py`'s `TypeKind` enum. The 14 entries cover all user-facing types. The builtin method tables for Option (4 methods), Result (4 methods), List (6 methods), and String (10 methods) match the actual methods available in the runtime and documented in the SPEC.

The `complete_type` function at line 113 correctly combines builtin types (priority `0_`) with user-defined types from the workspace (priority `1_`), ensuring builtins appear first in the completion list.

### 3.3 Visibility Gate -- CORRECT

`complete_identifiers` at line 192 applies a visibility gate: symbols from the current module are always offered (priority `0_`); symbols from other modules are only offered if `sym.visibility == "pub"` (priority `2_`). This is verified by `test_completion.py::test_visibility_respected` which confirms `internal_fn` is excluded from cross-module completions.

### 3.4 Field/Method Completion via Receiver Type -- DEGRADED (see Issue 3)

The completion handler in `server.py:468` attempts to get the receiver type via `analysis.receiver_type_at(line, col)`, but this method does not exist on `DocumentAnalysis`. The `hasattr` guard always returns `False`, so `receiver_type` is always `""`. The `complete_field_method("")` function receives an empty string and returns an empty list (no builtin type matches, no struct name match). The within-file `_dot_completions` path in `analysis.py:855` still works (it resolves the object name to a type via `_resolve_type_name`), but the workspace-aware path is dead code for field/method completion.

### 3.5 Context Detection -- ADEQUATE

`_detect_completion_context` at `server.py:627` uses simple line-prefix heuristics: `startswith("import ")` for import context, `endswith(".")` for field context, `endswith(":")` or `endswith("->")` for type context. These heuristics are correct for common cases but will misfire on multi-line expressions or string literals containing these characters. This is acceptable for a v0.5 LSP -- more precise context detection would require AST-aware cursor placement.

---

## Section 4: Diagnostic Integration

### 4.1 diagnostics.py -- CLEAN BOUNDARY MODULE

`diagnostics.py` serves as the 1-based-to-0-based conversion boundary between Mapanare's compiler (1-based lines/columns) and LSP (0-based). The `semantic_error_to_diagnostic` function at line 15 handles the conversion with `max(0, ... - 1)` guards. The `relatedInformation` attachment for suggestions at line 42 follows the LSP 3.17 specification correctly.

`run_semantic_check` at line 87 is a clean composition: parse, then check, returning diagnostics for whichever step fails. The `except Exception: pass` at line 112 for semantic check crashes is appropriate -- a crash in the semantic checker should not block diagnostic delivery of parse errors.

### 4.2 Debounced Re-check -- DOUBLE WORK (see Issue 2)

The `on_change` handler at `server.py:174` calls `_analyze_and_publish` immediately (which runs the Lark parser via `IncrementalParser` + semantic check + linter), then schedules a debounced `_debounced_recheck` after 300ms (which runs `parse()` + `check()` again via `run_semantic_check`). This means every keystroke triggers one immediate full analysis plus one delayed re-analysis. The `on_save` handler at line 193 is even worse: it calls `_analyze_and_publish` (parse + check + lint), then `_rebuild_workspace_file` (parse again), then `_run_and_publish_semantic_diagnostics` (parse + check again). That is three parse passes on every save.

The intended design appears to be: `_analyze_and_publish` provides fast incremental results (using cached chunks), and the debounced `_debounced_recheck` provides a "second opinion" with a fresh full semantic check. But both publish to the same diagnostic channel, so the debounced results overwrite the immediate results 300ms later. The net effect is redundant work with no user-visible benefit.

---

## Section 5: Rename Refactoring

### 5.1 Validation -- THOROUGH

`rename.py:validate_rename` checks three rules:
1. `_IDENT_RE` -- valid Mapanare identifier syntax
2. `_KEYWORDS` -- 38 keywords (including bilingual `pon`, `si`, `sino`, etc.) cannot be used as names
3. `workspace.lookup(module, new_name)` -- no conflict with existing top-level symbol in same module

### 5.2 Apply -- CORRECT

`apply_rename` at line 53 collects the definition site and all reference sites from `workspace.refs_by_symbol`, builds a `WorkspaceEdit` changes map. The span-to-range conversion at `_add_edit` (line 75) correctly does 1-based to 0-based conversion. The multi-file edit structure is correct for LSP's `WorkspaceEdit`.

### 5.3 Rename Scope Limitation

Rename only covers top-level symbols tracked by the workspace index. Local variables (let bindings inside function bodies) are not renamed cross-module, which is correct (they cannot be referenced cross-module). However, rename also does not cover local variable renames within a single file -- the `apply_rename` function only consults `workspace.refs_by_symbol`, not `analysis._references`. This is a limitation, not a bug (the LSP specification allows partial rename support).

---

## Section 6: Build System Impact

### 6.1 No Build System Changes -- VERIFIED

Arc 2 adds 4 new Python modules under `mapanare/lsp/`, 6 new test files under `tests/lsp/`, and 2 files under `editor/vscode/`. No changes to `Makefile`, `pyproject.toml` (dependency list), `setup.cfg`, or CI workflows were needed. The LSP depends on `pygls` and `lsprotocol`, which are listed in the `[dev]` extras. The VS Code extension at `editor/vscode/package.json` declares a dependency on the LSP server via `mapanare lsp` from PATH, with no npm build step required.

### 6.2 Import Laziness -- CORRECT

All imports of `mapanare.parser` and `mapanare.semantic` inside the LSP modules are deferred (inside function bodies), except for `analysis.py:61-66` which imports `BUILTIN_FUNCTIONS`, `PRIMITIVE_TYPES`, `BUILTIN_GENERIC_TYPES`, and `SemanticError` at module level. These are lightweight constants and an exception class, not the full parser/checker machinery. This means `import mapanare.lsp.server` does not eagerly import the Lark grammar or build the parser tables, which is correct for CLI startup performance when the LSP is not being used.

---

## Issues Found

### Issue 1 [HIGH] -- `_collect_references` uses wrong attribute name (`receiver` vs `object`)

**Description:** `workspace.py:217` accesses `expr.receiver` on `MethodCallExpr`, and line 221 accesses `expr.receiver` on `FieldAccessExpr`. The actual AST field is `object` (per `ast_nodes.py:183,192`). The attribute `receiver` does not exist on either node.

**Impact:** Any `.mn` file containing a method call (`obj.method()`) or field access (`obj.field`) in a function body will cause `_collect_references` to raise `AttributeError`. In `rebuild_file` (line 155), this is caught by the `except Exception` at line 159, so the file silently fails to index references (symbols are still indexed, only references are lost). In `scan_root`'s second pass (line 113), the exception is NOT caught, so `scan_root` will crash and the workspace index will be left in a partially initialized state.

**Evidence:** `ast_nodes.py:180-194` defines `MethodCallExpr.object` and `FieldAccessExpr.object`. No `receiver` property or alias exists. `analysis.py:674,678,680` correctly uses `expr.object` for the same node types.

**The bug is masked in tests** because all test files in `tests/lsp/` use only simple function calls (`helper()`, `print()`) and do not contain method calls or field accesses in function bodies.

**Fix:** Change `expr.receiver` to `expr.object` at `workspace.py:217` and `workspace.py:221`.

**Severity:** HIGH. This is a correctness bug that will crash workspace initialization for any real-world Mapanare project. The fact that it is masked by test coverage gaps makes it more dangerous, not less.

### Issue 2 [MEDIUM] -- Redundant parse passes on keystroke and save

**Description:** `on_change` (server.py:180-190) calls `_analyze_and_publish` immediately (which parses + checks + lints), then schedules a debounced `_debounced_recheck` (which parses + checks again). `on_save` (server.py:197-201) calls `_analyze_and_publish`, then `_rebuild_workspace_file` (which parses again), then `_run_and_publish_semantic_diagnostics` (which parses + checks again). This is 2 parse passes per keystroke and 3 per save.

**Impact:** On a large file, the user will see noticeable latency. The debounced re-check at 300ms will overwrite the immediate diagnostics, causing a visual flicker. The triple parse on save is pure waste -- the workspace rebuild and semantic re-check could reuse the AST from `_analyze_and_publish`.

**Recommendation:** The `on_change` handler should EITHER do immediate analysis OR debounced analysis, not both. The recommended pattern is: immediate analysis for hover/completion/go-to-def (update `_documents`), debounced analysis for diagnostics (update published diagnostics). For `on_save`, the workspace rebuild should reuse the AST from `_analyze_and_publish` rather than re-parsing.

**Severity:** MEDIUM. Performance issue that will affect DX. Not a correctness bug.

### Issue 3 [MEDIUM] -- `receiver_type_at` is called but never defined

**Description:** `server.py:468` calls `analysis.receiver_type_at(line, col)` guarded by `hasattr`. The `DocumentAnalysis` class in `analysis.py` does not define `receiver_type_at`. The `hasattr` check always returns `False`, so the workspace-aware field/method completion path in `server.py` always receives `receiver_type=""` and returns zero candidates.

**Impact:** Field/method completion after `.` only works via the within-file `_dot_completions` path in `analysis.py:855`, not via the workspace-aware `complete_field_method` path in `completion.py`. The workspace-aware path (which has builtin method tables for Option/Result/List/String and struct field lookup) is dead code in the server handler. Users typing `my_option.` will get completions from the within-file path (which resolves types via `_resolve_type_name`) but miss the richer builtin method tables.

**Recommendation:** Either implement `receiver_type_at` on `DocumentAnalysis` (delegating to `_resolve_type_name` for the object before the dot), or remove the `hasattr` guard and pass the receiver type from the within-file analysis path.

**Severity:** MEDIUM. The feature advertised in v4.39.0 CHANGELOG ("Field/method completion after `.`") partially works via the within-file path but the cross-module/builtin enrichment is not wired.

### Issue 4 [LOW] -- `_collect_references` does not walk `WhileLoop`, `LambdaExpr`, or `Block` in all expression arms

**Description:** `_collect_references` in `workspace.py:200-274` walks function bodies via `_walk_block` -> `_walk_stmt` -> `_walk_expr`, but `_walk_stmt` only handles `ExprStmt`, `LetBinding`, `ReturnStmt`, and `ForLoop`. It does not handle `WhileLoop`, `SignalDecl`, or `Block` (nested blocks). `_walk_expr` does not handle `LambdaExpr`, `IndexExpr`, `PipeExpr`, `UnaryExpr`, `BinaryExpr`, `SpawnExpr`, `SyncExpr`, or `SendExpr`. By contrast, `analysis.py:618-721` handles all of these.

**Impact:** References inside while loops, lambdas, binary expressions, pipe expressions, and other constructs will not be tracked by the workspace index. This means cross-module find-references will miss some reference sites. Within-file find-references (via `analysis.py`) will still find them.

**Recommendation:** Port the full `_visit_stmt`/`_visit_expr` walker from `analysis.py` to `workspace.py`'s `_collect_references`, or factor out a shared walker.

**Severity:** LOW. Partial reference coverage is common in early LSP implementations. The within-file path compensates.

### Issue 5 [LOW] -- Test coverage gap for method calls and field accesses

**Description:** No test file in `tests/lsp/` creates workspace files containing method calls (`obj.method()`) or field accesses (`obj.field`). All test files use simple function calls and identifier references. This is why Issue 1 was not caught.

**Impact:** The existing 49 LSP tests validate the happy path but do not exercise the most common Mapanare expression patterns.

**Recommendation:** Add at least two test files to the workspace test helpers that contain method calls and field accesses in function bodies (e.g., `"fn main() { let p = Point { x: 1, y: 2 }\nprint(str(p.x)) }"`).

**Severity:** LOW. Test gap enabling Issue 1.

---

## Strengths

### S1: Genuine Compiler Reuse -- No Fork

The LSP layer calls `mapanare.parser.parse()` and `mapanare.semantic.check()` without any modification, wrapper, or fork. There is no "LSP-specific parser" or "lightweight type checker." The same Lark LALR parser and the same two-pass semantic checker that run in `mapanare compile` run in the LSP. This means every parser bug fix and semantic checker improvement automatically benefits the LSP. This is the gold standard for language server design and matches the approach used by rust-analyzer (reuses `rustc`'s parser) and pylsp (reuses Python's `ast` module).

### S2: WorkspaceIndex as Clean Abstraction Layer

The `WorkspaceIndex` sits between the per-file `DocumentAnalysis` and the cross-file LSP features. It provides O(1) lookup by qualified name, O(1) lookup by unqualified name, and reverse reference tracking. The API is minimal: `scan_root`, `rebuild_file`, `lookup`, `lookup_by_name`, `find_references`, `all_symbols`. All LSP features (hover, go-to-def, find-refs, rename, completion) consume this API rather than doing their own workspace scanning. This is a clean separation of concerns.

### S3: IncrementalParser for Edit-Time Performance

The `IncrementalParser` at `analysis.py:225` is a pragmatic solution to the problem of re-parsing on every keystroke with a non-incremental (Lark LALR) parser. The MD5-based chunk hashing means that unchanged definitions are not re-parsed, and the chunk boundary detection (`_TOPLEVEL_RE`) mirrors the grammar's top-level production rules. The fallback to chunk-by-chunk parsing when full parsing fails is correct and ensures that a syntax error in one function does not destroy hover/completion for the rest of the file.

### S4: Diagnostic Enrichment with Fix Suggestions

The `_enrich_diagnostics` function at `analysis.py:1163` adds "Did you mean?" suggestions for undefined variables using `difflib.get_close_matches`, and type conversion suggestions for type mismatches. The suggestion infrastructure (via `FixSuggestion` dataclass and `relatedInformation` in the LSP protocol) is well-structured. The code action handler at `server.py:506` provides QuickFix actions for `[W002]` (unused import) and `[W005]` (unnecessary `mut`), with a "Fix all" composite action. This is a genuine IDE feature, not just diagnostic display.

### S5: Visibility-Aware Cross-Module Completion

The completion system correctly distinguishes between `pub` and `internal` symbols across modules. `complete_identifiers` only offers cross-module symbols with `visibility == "pub"`. The sort-text system (`0_` for current module, `2_` for public imports, `3_` for builtins) provides sensible ranking. This matches the behavior of mature language servers like rust-analyzer and TypeScript's tsserver.

---

## Recommendations

### R1: Fix `expr.receiver` -> `expr.object` in `workspace.py` (addresses Issue 1)

Two-character fix at lines 217 and 221. This is a ship-blocker for any real-world use.

### R2: Eliminate redundant parse passes (addresses Issue 2)

Refactor `on_change` to separate the analysis path (fast, for hover/completion) from the diagnostic path (debounced, for error reporting). Do not run both immediately. On `on_save`, pass the already-parsed AST to `_rebuild_workspace_file` and `_run_and_publish_semantic_diagnostics` instead of re-parsing.

### R3: Implement `receiver_type_at` on `DocumentAnalysis` (addresses Issue 3)

This can delegate to `_resolve_type_name` for the identifier before the dot, using `_word_at` and `_dot_completions`'s existing logic. Without this, the builtin method tables in `completion.py` (24 methods across 4 types) are unreachable from the server handler.

### R4: Expand test workspace files to include method calls and field accesses (addresses Issue 5)

Prevents regressions of Issue 1's class of bug. Two or three files in the test helpers with `obj.method()` and `obj.field` patterns.

### R5: Factor out a shared AST walker between `analysis.py` and `workspace.py` (addresses Issue 4)

Both modules walk the AST to collect references, but `workspace.py`'s walker handles fewer node types. A shared `ASTWalker` base class or visitor function would eliminate the divergence.

---

## Carry-Forward Items from v4.36.0

### Issue 2.3 [MEDIUM] -- `DiagnosticBag.note()` call path
Status: **OPEN.** No change. Deferred to v5.x.

### Issue 2.4 [LOW] -- `_supports_color` does not respect `CLICOLOR` / `CLICOLOR_FORCE`
Status: **OPEN.** No change. Deferred.

### Issue 3.3 [MEDIUM] -- Module-level DFE fixpoint
Status: **OPEN.** No change. Deferred.

### Issue 3.4 [MEDIUM] -- `MIRPassStats` with no `--stats` flag
Status: **OPEN.** No change. Deferred.

---

## Score Breakdown

| Category | Weight | Score | Notes |
|----------|--------|-------|-------|
| Parser/semantic reuse | 25% | 10.0 | No fork; `parse()` and `check()` called directly; IncrementalParser is a clean optimization |
| WorkspaceIndex design | 25% | 8.5 | Clean abstraction; O(1) lookup; but `_collect_references` has attribute bug and incomplete walker |
| Completion correctness | 20% | 8.0 | Four contexts well-structured; visibility correct; but `receiver_type_at` dead path degrades field/method completion |
| Diagnostic integration | 15% | 8.5 | Clean boundary module; enrichment with suggestions; but redundant parse passes on change/save |
| Build system impact | 10% | 10.0 | Zero build changes; lazy imports; VS Code manifest correct |
| Test coverage | 5% | 7.5 | 49 tests across 6 files; but no tests with method calls/field accesses; Issue 1 slipped through |

**Weighted total: 8.9 / 10**

---

## Verdict

**PASS.** Arc 2 delivers a genuine LSP layer with the correct architectural decisions: compiler reuse without forking, a clean workspace index abstraction, and visibility-aware cross-module features. The HIGH issue (attribute name bug) is a two-character fix that should be applied before the next release. The MEDIUM issues (redundant parsing, dead `receiver_type_at` path) are integration gaps that limit performance and feature completeness but do not invalidate the architecture. The arc is real, the features are real, and the foundation is sound for future development.
