# Plan: Heap-Allocated Large Struct Returns

## Problem

`LowerResult` (760 bytes) and `LowerState` (680 bytes) get corrupted when returned via sret and loaded back via `_load_struct_fields` / `_store_struct_fields`. The field-by-field decomposition produces valid IR, but BOTH llvmlite -O1 AND clang -O0 generate incorrect x86 for 34+ extract_value/insert_value chains on these huge structs.

**Proof**: `let x = 1; let xs = []` crashes with both compilers. The first `let` returns a LowerResult via sret. The caller loads it back (34 extract_values). The loaded state is corrupt. The second `let` then crashes when using the corrupt state.

## Solution

Same approach as the boxed enum refactor: for struct types > threshold, store them as `{i8* ptr}` with heap-allocated payload. The key targets:

1. **`LowerResult`** (760 bytes) — returned by every lowering function
2. **`LowerState`** (680 bytes) — contained in LowerResult, threaded through all calls
3. Any other struct > 56 bytes that flows through sret/byptr paths

The fix is NOT per-struct — it's a general mechanism: when `_is_large_struct(ty)` is true and the struct is used as a function return type, heap-allocate the return value instead of using sret with large by-value copy.

## Approach: Box sret returns

When a function returns a large struct via sret:

**Current flow (broken)**:
1. Caller allocates sret buffer on stack (760 bytes)
2. Callee fills buffer via `_store_struct_fields` (34 GEP+store ops)
3. Caller reads back via `_load_struct_fields` (34 GEP+load+insertvalue ops)
4. 760-byte SSA value gets corrupted during codegen

**New flow**:
1. Caller allocates sret buffer on stack (760 bytes) — same
2. Callee fills buffer via `_store_struct_fields` — same
3. Caller reads back via **memcpy to a fresh alloca**, NOT `_load_struct_fields`
4. Values are accessed via **GEP into the alloca**, never loaded as full SSA values

The key insight: we NEVER need to create a 760-byte SSA value. Every consumer of a LowerResult only needs individual FIELDS (Value.name, LowerState.tmp_counter, etc.). We can GEP directly into the alloca without loading the full struct.

## Implementation

### Step 1: Fix sret return loading

In `_emit_call` (around line 2935), when a large sret return is received:

```python
# Current (broken):
self._fn_allocas[inst.dest.name] = sret_alloca
values[inst.dest.name] = None  # force alloca path

# This is already correct! The alloca path stores None in values,
# which makes _get_value load from the alloca via _load_struct_fields.
# The bug is that _load_struct_fields creates a huge SSA value.
```

The fix: make `_get_value` for sret results NOT use `_load_struct_fields` — instead, keep `values[name] = None` and let FieldGet/Copy operations GEP directly into the alloca.

### Step 2: Fix `_emit_field_get` for large-alloca values

When a FieldGet accesses a field of a value whose `values[name]` is None (alloca path):
- Current: `_get_value` loads full struct via `_load_struct_fields`, then `extract_value`
- New: GEP directly into the alloca for the requested field — already implemented for large structs in `_emit_field_get`'s GEP path (line ~3188)

The GEP path already exists but may not fire for all cases. Need to verify it fires for LowerResult/LowerState field accesses.

### Step 3: Fix `_emit_struct_init` for large structs

When creating a large struct (like LowerResult):
- Current: builds full SSA value via `insert_value` chain, then `_store_value`
- New: already has GEP path for large structs (added in enum refactor Phase 2)
- Need to verify it works for LowerResult

### Step 4: Fix `_emit_copy` for large structs

Copy of LowerState/LowerResult:
- Current: already has memcpy fast path for large structs (line ~2145)
- Should already work — verify

### Step 5: Fix `_emit_return` for large sret

Return of LowerResult:
- Current: already has memcpy fast path for sret (line ~2966)
- Should already work — verify

## Key Insight

Most of the infrastructure is ALREADY in place from previous work:
- `_emit_field_get` has GEP path for large structs
- `_emit_copy` has memcpy path for large structs
- `_emit_return` has memcpy path for sret
- `_emit_struct_init` has GEP path for large structs (from enum refactor)

The ONE missing piece: `_get_value` still creates full SSA values via `_load_struct_fields` for cross-block references. The fix is to make it NEVER create large SSA values — always return from the alloca GEP path.

## Files to Modify

| File | Changes |
|------|---------|
| `mapanare/emit_llvm_mir.py` | `_get_value`: skip `_load_struct_fields` for large structs, keep alloca path |

## Test Strategy

1. `let x = 1; let xs = []` — the minimal reproducer
2. All 15 golden tests
3. All 7 self-hosted modules
4. 3697 pytest tests

## Success Criteria

- [ ] `let x = 1; let xs = []` compiles without crash
- [ ] 15/15 golden tests pass
- [ ] All 7 self-hosted modules compile
- [ ] 3697 pytest tests pass
