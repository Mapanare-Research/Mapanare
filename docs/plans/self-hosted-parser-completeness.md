# Plan: Self-Hosted Parser Completeness

## Problem

The self-hosted parser (`mapanare/self/parser.mn`) is missing handlers for several expression types. These were always broken but hidden by the old inline enum layout — wrong AST nodes produced zeros instead of crashing. The boxed enum refactor (v1.0.12+) made these bugs visible as null pointer crashes.

**Blocked**: All 7 self-hosted modules fail to compile themselves. The `ast.mn` module (structs/enums only, no complex expressions) is the only one that compiles.

## Root Causes

**Two distinct issues blocking self-compilation:**

### Issue A: Parser — Missing expression handlers
`parse_atom` in `parser.mn` (line ~1421) handles token types and returns `Expr` nodes. Missing handlers fall through to line 1498: `return new_expr_result(Expr::NoneLit, pos + 1)` — silently producing a `None` literal instead of the correct AST node.

### Issue B: Codegen — LowerState/LowerResult struct corruption
The pattern `let x = 1; let xs = []` crashes — even though parsing is correct — because `LowerResult` (760 bytes) and `LowerState` (680 bytes) get corrupted when threaded through lowering functions via sret returns. The `_store_struct_fields` / `_load_struct_fields` field-by-field decomposition produces valid IR, but BOTH llvmlite -O1 AND clang -O0 generate incorrect x86 code for the 34+ extract_value/insert_value chain on these huge structs.

This is the SAME class of bug as the enum truncation — but for regular structs, not enums. The boxed enum refactor fixed enums (all 16 bytes now), but LowerState/LowerResult are still 680/760 bytes.

**Fix approach for Issue B**: Apply the same heap-allocation strategy — store `LowerResult` as `{i8* ptr}` with heap-allocated payload, just like enums. This would make ALL large return types fit in ≤16 bytes. Requires a new plan: `boxed-large-structs-refactor.md`.

## Missing Handlers (discovered so far)

### 1. `KW_NEW` — struct constructor ✅ FIXED
- Pattern: `new Struct { field: val, ... }`
- Was: fell through to `NoneLit`
- Fix: added `KW_NEW` handler in `parse_atom` (committed)

### 2. List literal `[]` after any `let` statement — BLOCKED by Issue B
- `let xs: List<T> = []` works in isolation (single statement)
- `let x = 1; let xs = []` crashes — NOT a parser bug
- Root cause: LowerState corruption during state threading (Issue B)
- Cannot fix with parser changes alone

### 3. Enum variant constructors — TO INVESTIGATE
- Pattern: `Enum::Variant(args)` — parsed as `NamespaceAccess` then `Call`
- The parser handles `NAME::NAME` as `NamespaceAccess` (line 1490-1492)
- Then postfix parsing handles `(args)` as a function call
- This might actually work — need to verify with test

### 4. Other potentially missing constructs — TO AUDIT
- `|>` pipe operator
- Lambda expressions `|params| body`
- Error propagation `expr?`
- `send` / signal expressions
- String interpolation `"${expr}"`

## Status

- **Issue A (parser)**: `KW_NEW` fixed. Other handlers may still be missing but can't be tested until Issue B is resolved.
- **Issue B (LowerState)**: Diagnosis complete. Root cause is identical to the enum truncation bug but for structs. Needs a new refactor (heap-allocate LowerResult like we did for enums).

## Next Steps

1. **Create `boxed-large-structs-refactor.md`** — plan to heap-allocate LowerResult/LowerState
2. Implement the struct boxing (same pattern as enum boxing)
3. Once Issue B is fixed, return to parser completeness testing
4. Fix remaining missing parser handlers as they're discovered

## Files to Modify

| File | Changes |
|------|---------|
| `mapanare/self/parser.mn` | Add missing expression handlers (Issue A) |
| `mapanare/emit_llvm_mir.py` | Heap-allocate large struct returns (Issue B — separate plan) |

## Success Criteria

- [x] All 15 golden tests pass
- [ ] `main.mn` compiles — BLOCKED by Issue B
- [ ] `lexer.mn` compiles — BLOCKED by Issue B
- [ ] `semantic.mn` compiles — BLOCKED by Issue B
- [ ] `parser.mn` compiles — BLOCKED by Issue B
- [ ] `lower.mn` compiles — BLOCKED by Issue B
- [ ] `emit_llvm.mn` compiles — BLOCKED by Issue B
- [ ] `mnc_all.mn` compiles (self-compilation)
- [x] 3697 pytest tests pass

## Priority

HIGH — but blocked by Issue B. The parser fix alone is insufficient. The LowerState corruption must be fixed first.
