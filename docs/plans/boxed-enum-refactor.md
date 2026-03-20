# Plan: Heap-Allocated Enum Payloads

## Problem

Enums are `{i64 tag, [N x i8] payload}` — up to 272 bytes for `Instruction`. llvmlite's -O1 codegen truncates large SSA values, crashing lexer.mn, parser.mn, lower.mn.

## Solution

Change ALL enums to `{i64 tag, i8* payload_ptr}` (16 bytes). Payload is heap-allocated via malloc (arena when re-enabled). 16 bytes is well below the 56-byte threshold — all large-struct workarounds become dead code for enums.

## Phases

### Phase 1: `_register_enum` → `{i64, i8*}`
- [ ] Change `payload_ty` from `ir.ArrayType(ir.IntType(8), N)` to `LLVM_PTR`
- [ ] Store per-variant payload sizes in `_enum_types` tuple (add 4th element: `dict[str, int]`)
- [ ] Enum type becomes `ir.LiteralStructType([LLVM_INT, LLVM_PTR])` for all enums

### Phase 2: `_emit_enum_init` → heap allocate payload
- [ ] Compute variant's payload struct type: `ir.LiteralStructType(field_types)`
- [ ] If variant has payload: `malloc(payload_size)` → bitcast to `variant_struct*` → GEP+store each field
- [ ] If no payload: build `{tag, null}`
- [ ] Build final value: `insertvalue {tag, payload_ptr}`
- [ ] Remove the "large enum memcpy" path (lines ~3926-3955)
- [ ] Remove manual byte-offset calculation — use structured GEP instead

### Phase 3: `_emit_enum_payload` → load through pointer
- [ ] `extract_value(enum_val, 1)` → get `i8*` payload pointer
- [ ] Build variant struct type from `variant_payloads`
- [ ] Bitcast `i8*` to `variant_struct*`
- [ ] GEP to `payload_idx` field, load
- [ ] Remove `use_alloca_path` branch
- [ ] Remove manual byte-offset extraction
- [ ] Keep boxed-field dereference (pointer-to-pointer for recursive fields)

### Phase 4: `_emit_enum_tag` → simplify
- [ ] Remove "large enum fast path" (GEP into alloca)
- [ ] Just use `extract_value(enum_val, 0)` — always safe at 16 bytes
- [ ] Keep the pointer-type fallback for cross-module cases

### Phase 5: Golden tests
- [ ] Run `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
- [ ] All 15 must pass
- [ ] Check 07_enum_match IR shows `{i64, i8*}` not `{i64, [N x i8]}`

### Phase 6: Dead code cleanup
- [ ] Remove `_has_large_array_field` helper (no more array fields in enums)
- [ ] Remove `_value_src_alloca` tracking (no longer needed)
- [ ] Remove `src_mir_val` param from `_store_value` (no longer needed)
- [ ] Clean up `_emit_list_push` large-element fast path (16-byte enums use standard path)
- [ ] Clean up `_emit_index_get` large-element memcpy path (same reason)

### Phase 7: Full test suite
- [ ] `python -m pytest tests/ -x -q` — all 3697 must pass

### Phase 8: Self-compilation
- [ ] `python scripts/build_stage1.py` — rebuild mnc-stage1
- [ ] Test ALL 7 modules: `./mnc-stage1 mapanare/self/{ast,main,lexer,emit_llvm,semantic,parser,lower}.mn`
- [ ] All 7 must compile without crash
- [ ] Test `./mnc-stage1 mapanare/self/mnc_all.mn` — self-compilation

## Key Invariants

- `{i64, i8*}` is 16 bytes — below `_LARGE_STRUCT_THRESHOLD` (56)
- Option/Result types (`{i1, T}`) are NOT changed — they have their own constructors
- Payload lifetime: malloc'd, never freed (batch compiler), arena when re-enabled
- Shallow copy of `{i64, i8*}` is correct — no mutable aliasing of enum values
- Boxed recursive fields remain doubly-indirected (payload_ptr → struct with ptr fields)

## Files to Modify

| File | Changes |
|------|---------|
| `mapanare/emit_llvm_mir.py` | `_register_enum`, `_emit_enum_init`, `_emit_enum_tag`, `_emit_enum_payload`, cleanup |
| `scripts/build_stage1.py` | Already has 64MB stack flag; no other changes needed |

## Risks

1. **Cross-module enums** — type resolution must find the new `{i64, i8*}` type. Low risk: suffix matching is type-agnostic.
2. **Zero-payload variants** — null pointer. Already handled by existing None/empty checks.
3. **Memory leaks** — acceptable for batch compiler. Arena will fix when re-enabled.
4. **Option/Result confusion** — must NOT change Option/Result types (separate code paths).

## Success Criteria

- [ ] 15/15 golden tests pass
- [ ] 7/7 self-hosted modules compile
- [ ] 3697/3697 pytest tests pass
- [ ] `mnc-stage1 mapanare/self/mnc_all.mn` runs without crash
