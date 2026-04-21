# Cobra -- C++/ABI Review of Mapanare v4.41.0 (Arc 2 Panel)

**Reviewer:** Cobra
**Personality:** The Grumpy C++ Veteran -- condescending, encyclopedic, razor sharp
**Previous Version Reviewed:** v4.36.0 (score: 9.80, PASS)
**Verdict:** PASS
**Confidence:** 10/10
**Score:** 9.80/10 (unchanged from v4.36.0)
**Files Reviewed:**
- `mapanare/lsp/workspace.py` (362 lines -- symbol extraction + reference collection)
- `mapanare/lsp/completion.py` (241 lines -- new in v4.39.0)
- `mapanare/lsp/rename.py` (90 lines -- new in v4.38.0)
- `mapanare/lsp/diagnostics.py` (114 lines -- new in v4.40.0)
- `mapanare/lsp/server.py` (diff: +243/-7)
- `mapanare/ast_nodes.py` (struct/enum field definitions, lines 618-650)
- `.reviews/CARRY_FORWARD.md` (173 lines)
- `.reviews/v4.41.0/PRE_PANEL_AUDIT.md`, `MEASUREMENTS.md`
- `git diff --name-only` for `emit_llvm_text.py`, `lower.py`, `semantic.py`, `types.py`, `parser.py`, `mapanare.lark`, `runtime/native/`, `mapanare/self/`

---

## Executive Summary

Arc 2 (v4.37.0-v4.40.0) is an LSP-only arc. Zero compiler changes, zero ABI changes, zero grammar changes, zero runtime changes. I confirmed this by diffing every file in my domain -- `emit_llvm_text.py`, `lower.py`, `semantic.py`, `types.py`, `ast_nodes.py`, `parser.py`, `mapanare.lark`, `mir.py`, `mir_builder.py`, the entire `runtime/native/` directory, and the entire `mapanare/self/` directory -- against v4.36.0. Every diff came back empty. This is the cleanest non-regression certificate I have ever written.

The workspace index (`mapanare/lsp/workspace.py`) is the only new code that touches AST nodes from my domain. I verified it imports AST types read-only and does not modify any AST node, emit any IR, or interact with the type system in any way that could produce ABI drift. The import list grew from 8 to 24 AST node types between v4.36.0 and v4.41.0 (for the reference-collection walker at v4.38.0), but these are all pure read-only pattern matches against existing dataclass instances.

My two tracked carry-forwards (P3 and A10) are still in the ledger. Neither was addressed in this arc, which is correct -- an LSP arc should not be fixing lowerer semantics or grammar gaps.

---

## Non-Regression Verification

### Compiler / ABI files: ZERO changes

```
git diff --name-only v4.36.0..HEAD -- mapanare/emit_llvm_text.py mapanare/lower.py \
  mapanare/semantic.py mapanare/types.py mapanare/ast_nodes.py mapanare/parser.py \
  mapanare/mapanare.lark runtime/native/ mapanare/self/ mapanare/mir.py mapanare/mir_builder.py
(empty output)
```

No file in my domain was touched. ABI is byte-identical to v4.36.0. This is the correct outcome for an LSP-only arc.

### Import-side ABI drift: NONE

The LSP workspace module imports 24 AST node types:

```python
from mapanare.ast_nodes import (
    AgentDef, Block, CallExpr, ConstructExpr, EnumDef, Expr, ExprStmt,
    ExternFnDef, FieldAccessExpr, FnDef, ForLoop, Identifier, IfExpr,
    ImportDef, LetBinding, MatchArm, MatchExpr, MethodCallExpr,
    ModuleLetDef, NamedType, PipeDef, Program, ReturnStmt, Span,
    Stmt, StructDef, TraitDef, TypeAlias,
)
```

All of these are used exclusively in `isinstance()` checks inside `_extract_top_level_symbols` and `_collect_references`. No AST node is constructed, mutated, or passed to any emitter. No import from `mapanare.types`, `mapanare.mir`, `mapanare.lower`, or `mapanare.emit_llvm_text`. The LSP module is a pure consumer of the AST layer with no write path. This cannot produce ABI drift.

---

## Carry-Forward Status

### P3: Self-hosted guard fall-through divergence

**Status:** OPEN, cycle 2. CARRY_FORWARD.md line 117 tracks this as `MEDIUM`, targeting v4.37.0. It was not addressed in v4.37.0-v4.40.0 (LSP arc, no compiler changes). The tracking version should be updated to v4.42.0+ since v4.37.0 has shipped without the fix. **The underlying bug is unchanged** -- `lower.mn:3418-3425` still jumps to the next arm's label instead of rebuilding a decision tree. Latent for current usage, wrong for overlapping variant guards.

### A10: Bounded-for sentinels

**Status:** OPEN, cycle 11 (by my count). CARRY_FORWARD.md line 113 still says "442 sites across 8 self-hosted modules." The actual count was 552 at v4.36.0 per my last review, and since zero self-hosted files changed in Arc 2, it remains 552. The stale count from my v4.36.0 Issue #3 was not updated. Tracking version is v4.37.0+, which has now shipped without the grammar change. Should be updated to v4.42.0+ or later.

### Other items from my v4.36.0 review

| # | Item | v4.36.0 | v4.41.0 | Note |
|---|------|---------|---------|------|
| 1 | Guard fall-through (P3) | LOW | OPEN (cycle 2) | Not addressed, expected in LSP arc |
| 2 | Dead arena code (11th cycle) | LOW | **12th cycle** | `_emit_arena_destroy` / `_fn_is_arena_eligible` still dead. File untouched. |
| 3 | A10 count stale in CARRY_FORWARD | LOW | UNCHANGED | Still says 442, actual is 552 |
| 4 | Or-pattern binding validation (self-hosted) | LOW | UNCHANGED | `semantic.mn:1060-1067` still binds first alternative only |
| 5 | Golden tests 49-51 missing `.ref.ll` | LOW | UNCHANGED | `--bless` not run |
| 6 | `_BYREF_BYTES = 64` asymmetry | LOW (3rd cycle) | **4th cycle** | Untouched |

All six items carry forward unchanged, which is exactly what should happen when zero compiler files are modified. I am not penalizing the score for items that were correctly out-of-scope for an LSP arc.

---

## Workspace Index: Struct/Enum Field Metadata Assessment

The workspace index extracts struct and enum symbols with field-level metadata in `_extract_top_level_symbols` (lines 277-339). Here is what it captures:

**StructDef** (line 292):
```python
fields = ", ".join(f.name for f in defn.fields) if defn.fields else ""
detail=f"struct {defn.name} {{ {fields} }}"
```

This captures field *names* but drops field *types*. `StructField` has both `name: str` and `type_annotation: TypeExpr`, but only `.name` is extracted into the `detail` string. For LSP hover and completion, this means a user sees `struct Point { x, y }` but not `struct Point { x: Float, y: Float }`. This is adequate for symbol identification but insufficient for type-aware completion or hover.

**EnumDef** (line 299):
```python
variants = ", ".join(v.name for v in defn.variants) if defn.variants else ""
detail=f"enum {defn.name} {{ {variants} }}"
```

Same pattern: variant names are captured, but variant payload types (`EnumVariant.fields: list[TypeExpr]`) are dropped. A user sees `enum Option { Some, None }` instead of `enum Option { Some(T), None }`.

This is not a bug -- it is a design choice for the `detail` string's brevity. The full `StructField` and `EnumVariant` data is still available in `entry.ast` (the cached AST). The completion module at `completion.py` can (and likely does) access the full AST for field-level type information when building completion items. The `detail` field on `SymbolDef` is a summary for quick display, not the authoritative source. See Issue #1.

---

## Issues Found

### CRITICAL: None

### HIGH: None

### MEDIUM: None

### LOW

1. **[LOW] Struct/enum `detail` strings omit field types** -- `mapanare/lsp/workspace.py:292, 299`.

   The `detail` field for struct and enum symbols lists field/variant names but not their types. For the LSP hover and workspace-symbol responses, this produces summaries like `struct Point { x, y }` rather than `struct Point { x: Float, y: Float }`. The information is available on the AST node (`StructField.type_annotation`, `EnumVariant.fields`) and could be included with a one-line change per case:

   ```python
   # Struct: include type annotations
   fields = ", ".join(
       f"{f.name}: {_type_expr_display(f.type_annotation)}" if f.type_annotation else f.name
       for f in defn.fields
   ) if defn.fields else ""

   # Enum: include payload types
   variants = ", ".join(
       f"{v.name}({', '.join(_type_expr_display(t) for t in v.fields)})" if v.fields else v.name
       for v in defn.variants
   ) if defn.variants else ""
   ```

   The `_type_expr_display` helper is already imported from `mapanare.lsp.analysis` at line 353 (`_fn_sig` uses it). Not blocking; the full AST is cached and available for richer queries. But the `detail` string is what appears in workspace-symbol and hover responses, so enriching it would improve the user experience for no cost.

2. **[LOW] CARRY_FORWARD.md tracking versions for P3 and A10 are stale** -- `.reviews/CARRY_FORWARD.md:113, 117`.

   P3 targets v4.37.0, which has shipped without the fix. A10 targets "v4.37.0+ if grammar adds `loop { }`", which also shipped without movement. Both should be updated to v4.42.0+ or whatever the next compiler-focused arc targets. This is a bookkeeping issue, not a correctness issue, but the carry-forward ledger's value depends on its tracking versions being current.

3. **[LOW] Dead arena code, 12th cycle** -- `mapanare/emit_llvm_text.py:1491-1530`.

   Carrying forward from v4.36.0 Issue #2. File untouched in Arc 2. **12th cycle.** I am mentioning it for ledger continuity. At this point the dead code is a permanent fixture unless someone specifically targets it.

---

## Recommendations

### Priority 1: Update CARRY_FORWARD.md tracking versions (Issue #2)

P3 and A10 both target v4.37.0, which has shipped. Update to the next compiler arc's first version. One-line edits.

### Priority 2: Enrich struct/enum detail strings (Issue #1)

Two small changes in `workspace.py:292` and `workspace.py:299` to include type annotations in the `detail` field. The helper function is already imported. Five minutes of work for a measurably better hover/workspace-symbol experience.

### Priority 3: Run `--bless` for golden tests 49-51

Carrying from v4.36.0. Still 30 seconds. Still not done.

---

## Arc 2 Assessment

This is the easiest review I have written. Zero files in my domain were modified. The LSP code imports AST types read-only and cannot produce ABI drift. The carry-forward ledger has not moved on my items, which is correct for an LSP-only arc but means the tracking versions are now stale. The workspace index correctly extracts struct/enum symbols but could include field type metadata in the detail strings for richer hover/completion display.

**Score: 9.80/10, PASS.** Unchanged from v4.36.0. I cannot award points for work that did not happen in my domain, and I cannot deduct points for items that were correctly out of scope. The codebase stands exactly where it was at v4.36.0 from the C++/ABI perspective. The 0.20 withheld remains allocated to: -0.08 for the dead arena code (12th cycle, approaching geological timescales), -0.06 for the two self-hosted mirror divergences (P3 guard fall-through, or-pattern binding validation), -0.03 for the missing golden reference files (49-51), -0.02 for the stale A10 count, -0.01 for the BYREF_BYTES asymmetry (4th cycle).

This is PASS with maximum confidence. An LSP-only arc cannot regress ABI. It didn't.
