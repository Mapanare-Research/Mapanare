# Plan: Heap-Allocated Enum Payloads

## Problem

Enums were `{i64 tag, [N x i8] payload}` — up to 272 bytes for `Instruction`. llvmlite's -O1 codegen truncates large SSA values, crashing lexer.mn, parser.mn, lower.mn.

## Solution

Changed ALL enums to `{i64 tag, i8* payload_ptr}` (16 bytes). Payload is heap-allocated via malloc (arena when re-enabled). 16 bytes is well below the 56-byte threshold — all large-struct workarounds are now dead code for enums.

## Phases

### Phase 1: `_register_enum` → `{i64, i8*}` ✅ DONE
- [x] Changed `payload_ty` from `ir.ArrayType(ir.IntType(8), N)` to `LLVM_PTR`
- [x] Store per-variant payload sizes in `_enum_types` tuple (4th element: `dict[str, int]`)
- [x] Enum type is now `ir.LiteralStructType([LLVM_INT, LLVM_PTR])` for all enums
- [x] Updated all 5 tuple-unpack sites to 4-tuples
- [x] Verified: 0 old `{i64, [N x i8]}`, 13000+ `{i64, i8*}` in generated IR

### Phase 2: `_emit_enum_init` → heap allocate payload ✅ DONE
- [x] Compute variant's payload struct type: `ir.LiteralStructType(field_types)`
- [x] If variant has payload: `malloc(payload_size)` → bitcast to `variant_struct*` → GEP+store each field
- [x] If no payload: build `{tag, null}`
- [x] Build final value: `insertvalue {tag, payload_ptr}`
- [x] Removed the "large enum memcpy" path
- [x] Replaced manual byte-offset calculation with structured GEP
- [x] Verified: 195 malloc payload allocations in IR

### Phase 3: `_emit_enum_payload` → load through pointer ✅ DONE
- [x] `extract_value(enum_val, 1)` → get `i8*` payload pointer
- [x] Build variant struct type from `variant_payloads`
- [x] Bitcast `i8*` to `variant_struct*`
- [x] GEP to `payload_idx` field, load
- [x] Removed `use_alloca_path` branch
- [x] Removed manual byte-offset extraction
- [x] Kept boxed-field dereference (pointer-to-pointer for recursive fields)
- [x] Kept Result/Option fallback (extract_value for unregistered enums)

### Phase 4: `_emit_enum_tag` → simplify ✅ DONE
- [x] Removed "large enum fast path" (GEP into alloca)
- [x] Standard path: `extract_value(enum_val, 0)` — always safe at 16 bytes
- [x] Kept pointer-type fallback for cross-module cases

### Phase 4.5: Self-hosted parser fix (discovered during testing) ✅ DONE
- [x] Added `KW_NEW` handler to `parse_atom` in `parser.mn`
- [x] `return new Struct { field: val, ... }` now parses correctly
- [x] Discovery: old code NEVER parsed `new` keyword — `new Struct{...}` was silently converted to `NoneLit` (produced wrong output without crashing)

### Phase 5: Golden tests ✅ DONE
- [x] 15/15 golden tests pass
- [x] IR shows `{i64, i8*}` not `{i64, [N x i8]}`
- [x] Binary 22% smaller (1.5MB → 1.17MB)
- [x] IR 5% shorter (155K → 148K lines)

### Phase 6: Dead code cleanup — DEFERRED
- [ ] Remove `_has_large_array_field` helper (no more array fields in enums)
- [ ] Remove `_value_src_alloca` tracking (kept for now, harmless)
- [ ] Remove `src_mir_val` param from `_store_value` (kept for now, harmless)
- [ ] Clean up `_emit_list_push` large-element fast path (16-byte enums use standard path)
- [ ] Clean up `_emit_index_get` large-element memcpy path (same reason)

> Deferred because the old workaround code is harmless (never triggers for 16-byte enums) and removing it risks breaking non-enum large struct paths that still need it.

### Phase 7: Full test suite ✅ DONE
- [x] 3697/3697 pytest tests pass
- [x] ruff, mypy clean

### Phase 8: Self-compilation — BLOCKED by parser bugs
- [x] `python scripts/build_stage1.py` — rebuilds mnc-stage1 successfully
- [x] `ast.mn` compiles ✅
- [ ] `main.mn` — CRASH (pre-existing parser bug, see below)
- [ ] `lexer.mn` — CRASH (same root cause)
- [ ] Remaining 5 modules — CRASH (same root cause)

## Key Discovery: Pre-existing Parser Bugs

The remaining module crashes are **NOT caused by the boxed enum refactor**. They are pre-existing bugs in the self-hosted parser (`parser.mn`) that were **always there but hidden** by the old inline enum layout:

1. **`KW_NEW` never handled** → `new Struct { ... }` parsed as `NoneLit` → FIXED
2. **Other missing constructs** → The self-hosted parser produces wrong AST nodes for many patterns. With the old `{i64, [264 x i8]}` layout, reading the payload of a wrongly-tagged enum returned zeros (the zero-initialized inline payload). With the new `{i64, i8*}` layout, reading the payload of a wrongly-tagged enum dereferences null → immediate crash.

**Proof**: The old mnc-stage1 produced WRONG IR for `test_4fn.mn` — `[]` list literals compiled as `Option::None`, struct constructors compiled as `NoneLit`. The output was silently incorrect. The new code crashes immediately on the same input, making the bug visible.

## Next Steps (for future work)

1. **Fix self-hosted parser** (`parser.mn`) — add missing expression handlers:
   - `[]` list literals (might need `parse_list_lit` to handle `LBRACKET`)
   - Enum variant constructors (`Enum::Variant(args)`)
   - Other patterns that produce wrong AST nodes
2. **Phase 6 cleanup** — remove dead large-enum workaround code
3. **Re-enable arena allocator** — switch from malloc to arena for payload allocation
4. **Phase 8** — once parser is fixed, all 7 modules should compile

## Files Modified

| File | Changes |
|------|---------|
| `mapanare/emit_llvm_mir.py` | `_register_enum` (boxed type), `_emit_enum_init` (heap alloc), `_emit_enum_tag` (simplified), `_emit_enum_payload` (pointer extraction) |
| `mapanare/self/parser.mn` | Added `KW_NEW` handler in `parse_atom` |

## Key Invariants (verified)

- [x] `{i64, i8*}` is 16 bytes — below `_LARGE_STRUCT_THRESHOLD` (56)
- [x] Option/Result types (`{i1, T}`) are NOT changed — separate code paths
- [x] Payload lifetime: malloc'd, never freed (batch compiler)
- [x] Shallow copy of `{i64, i8*}` is correct — no mutable aliasing
- [x] Boxed recursive fields remain doubly-indirected

## Success Criteria

- [x] 15/15 golden tests pass
- [ ] 7/7 self-hosted modules compile — BLOCKED by parser bugs (not enum layout)
- [x] 3697/3697 pytest tests pass
- [ ] `mnc-stage1 mapanare/self/mnc_all.mn` — BLOCKED by parser bugs
