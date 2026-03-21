# Plan: Self-Hosted Parser Completeness

## Problem

The self-hosted parser (`mapanare/self/parser.mn`) is missing handlers for several expression types. These were always broken but hidden by the old inline enum layout — wrong AST nodes produced zeros instead of crashing. The boxed enum refactor (v1.0.12+) made these bugs visible as null pointer crashes.

**Blocked**: All 7 self-hosted modules fail to compile themselves. The `ast.mn` module (structs/enums only, no complex expressions) is the only one that compiles.

## Root Cause

`parse_atom` in `parser.mn` (line ~1421) handles token types and returns `Expr` nodes. Missing handlers fall through to line 1498: `return new_expr_result(Expr::NoneLit, pos + 1)` — silently producing a `None` literal instead of the correct AST node.

## Missing Handlers (discovered so far)

### 1. `KW_NEW` — struct constructor ✅ FIXED
- Pattern: `new Struct { field: val, ... }`
- Was: fell through to `NoneLit`
- Fix: added `KW_NEW` handler in `parse_atom` (committed)

### 2. List literal `[]` in certain contexts — TO INVESTIGATE
- `let xs: List<T> = []` works in isolation
- Crashes when many functions precede it in the same file
- May be a different issue (MIR lowering or cross-module type resolution)
- Need to create minimal reproducer and trace

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

## Diagnosis Steps

For each module that crashes:

1. Binary search for the crash line: `head -N module.mn > test.mn; echo 'fn main(){}' >> test.mn`
2. Check crash backtrace: `gdb -batch -ex run -ex 'bt 5' --args ./mnc-stage1 test.mn`
3. Identify the expression type that produces wrong AST
4. Add handler to `parse_atom` or the relevant parse function
5. Rebuild mnc-stage1 and re-test

## Files to Modify

| File | Changes |
|------|---------|
| `mapanare/self/parser.mn` | Add missing expression handlers in `parse_atom` and other parse functions |

## Test Strategy

After each parser fix:
1. `python scripts/build_stage1.py` — rebuild mnc-stage1
2. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — 15/15 golden tests
3. Test each module: `./mnc-stage1 mapanare/self/{ast,main,lexer,...}.mn`
4. `python -m pytest tests/ -x -q` — 3697 tests

## Success Criteria

- [ ] All 15 golden tests pass (currently ✅)
- [ ] `main.mn` compiles
- [ ] `lexer.mn` compiles
- [ ] `semantic.mn` compiles
- [ ] `parser.mn` compiles
- [ ] `lower.mn` compiles
- [ ] `emit_llvm.mn` compiles
- [ ] `mnc_all.mn` compiles (self-compilation)
- [ ] 3697 pytest tests pass (currently ✅)

## Priority

HIGH — this is the remaining blocker for self-compilation (v1.0.6 milestone). The boxed enum refactor eliminated the llvmlite codegen bug. The parser is the last piece.
