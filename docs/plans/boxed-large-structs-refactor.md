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

**The problem is fundamental**: ANY `builder.load` or `builder.store` of >~200 byte structs gets truncated. The memcpy+load approach (tried and failed) doesn't help because the LOAD itself creates a huge SSA value that gets truncated downstream.

**The fix**: Apply the same heap-allocation approach as enums to ALL large structs. Represent `LowerResult`, `LowerState`, `MIRFunction`, `MIRModule`, etc. as `{i8* ptr}` with heap-allocated payload. This makes every SSA value ≤16 bytes.

This is the same approach we used for enums — change `_register_struct` to produce `{i8* ptr}` for large structs, and update `_emit_struct_init`, `_emit_field_get`, `_emit_field_set`, `_emit_copy` to work through heap pointers.

## Files to Modify

| File | Changes |
|------|---------|
| `mapanare/emit_llvm_mir.py` | `_get_value`: skip `_load_struct_fields` for large structs, keep alloca path |

## Test Strategy

1. `let x = 1; let xs = []` — the minimal reproducer
2. All 15 golden tests
3. All 7 self-hosted modules
4. 3697 pytest tests

## Progress (2026-03-20)

Prototype implemented and tested. Results:
- `_register_struct` → `{i8*}` for 42 large structs: ✅ works
- `_emit_struct_init` → malloc + GEP stores: ✅ works
- `_emit_field_get` → extract ptr, bitcast, GEP, load: ✅ works
- `_emit_field_set` → extract ptr, bitcast, GEP, store: ✅ works
- Binary shrinks from 1.5MB to 453KB
- `main.mn` compiled successfully! (first time ever with boxed approach)
- **BUT**: `_emit_copy` needs deep copy (malloc+memcpy) to prevent aliasing.
  Shallow copy of `{i8*}` causes `let mut new_st = st; new_st.field = val` to
  modify BOTH `st` and `new_st` (they share the same heap pointer).
  Deep copy prototype had edge cases with `i8*` vs `{i8*}` type mismatches.

### Known Issues to Fix
1. **Deep copy in `_emit_copy`**: when source value is `i8*` (not `{i8*}`), `extract_value` fails. Need pointer-type check before extraction.
2. **3 golden test regressions** (07_enum_match, 08_list, 10_result): all crash in `lower_list` — same aliasing issue from shallow copy.
3. Prototype changes were NOT committed (lost in git stash). Need to re-apply.

### Analysis (2026-03-21)

The root cause is NOT struct size but **by-value parameter passing of 680-byte LowerState**.

At byptr threshold 56 (LowerState by pointer): `let+list` works but `match` crashes (aliasing).
At byptr threshold 1024 (LowerState by value): `match` works but `let+list` crashes (stale registers).
These are CONTRADICTORY requirements — no single threshold fixes both.

The `println` call between statements "fixes" things by forcing full state materialization (function call barrier). Field access barriers don't help — only real function calls work.

### Next Steps
The remaining blocker requires one of:
1. **Boxed LowerState** — represent as `{i8*}` to eliminate large by-value passing entirely
2. **Deep copy at function entry** — memcpy byptr parameters AND set values to None (force alloca path)
3. **Compiler barrier intrinsic** — emit `asm volatile("")` or similar to force materialization

## Success Criteria

- [ ] `let x = 1; let xs = []` compiles without crash
- [ ] 15/15 golden tests pass
- [ ] All 7 self-hosted modules compile
- [ ] 3697 pytest tests pass
