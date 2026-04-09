# Enum Payload Corruption Fix Plan

## Problem Statement

The self-hosted compiler (mnc-stage1) produces invalid LLVM IR for 9/15 golden tests.
All 9 failures share the same root cause: **enum payload field corruption**.

When the `Instruction` enum stores a variant with 3+ fields containing nested structs
(e.g., `StructInit(Value, MIRType, List<FieldPair>)` — 176 bytes), the inner struct
fields beyond the first ~16 bytes are corrupted when read back.

**Evidence:**
- `Value.name` (first 16 bytes of payload) survives correctly
- `Value.ty.kind`, `MIRType.kind`, `MIRType.name`, `List` contents are all zeroed/garbage
- `Call(Value, String, List<Value>)` (128 bytes) works perfectly
- `ListInit(Value, MIRType, List<Value>)` (176 bytes) — List<Value> works but MIRType is corrupted
- `StructInit(Value, MIRType, List<FieldPair>)` (176 bytes) — List<FieldPair> is empty

## Hypothesis

The text emitter's `_do_enum_init` allocates the payload with `malloc(size)` and stores
fields via GEP. The `_tsz()` function computes the payload size correctly (verified: 176
bytes matches llvmlite's `_approx_type_size`). But the **GEP field indices** may produce
wrong byte offsets for nested struct fields when the payload struct has alignment padding.

In LLVM IR, `getelementptr inbounds {A, B, C}, ptr %p, i32 0, i32 1` accesses field 1
at its **ABI-aligned offset**, not at `sizeof(A)` bytes. If the emitter computes the
payload struct type incorrectly (e.g., using different field types than what the GEP uses),
the stores write to wrong memory locations.

## Investigation Plan

### Step 1: Reproduce minimally
Create a minimal .mn program that triggers the bug and produces wrong output.
Verify the IR is valid but produces wrong values at runtime.

### Step 2: Compare IR for working vs broken variants
Extract the enum init code for `Call` (works, 128B payload) and `StructInit` (broken, 176B)
from the compiled main.ll. Compare the GEP patterns, malloc sizes, and store sequences.

### Step 3: Identify the specific corruption
Add debug printf to the C runtime or compiled code to print the payload pointer and
field values after store, then again after load in the match arm. Find exactly which
field goes to zero.

### Step 4: Fix the root cause
Based on findings, fix either:
- `_do_enum_init` (store path) — wrong GEP type or index
- `_do_enum_payload` (load path) — wrong bitcast type or GEP index
- `_tsz()` — wrong size computation causing malloc to allocate too few bytes
- `_reg_enum` — wrong payload type registration

### Step 5: Verify
- All 15 stage2 IR files pass llvm-as
- All 15 golden tests produce correct output when compiled
- 3698 pytest still pass
- 15/15 golden harness still pass

## Tests Affected

| Test | Instruction | Payload Size | Issue |
|------|------------|-------------|-------|
| 06_struct | StructInit | 176B | fields list empty |
| 14_nested_struct | StructInit | 176B | fields list empty |
| 05_for_loop | (loop vars) | varies | phi/variable corruption |
| 12_while | (loop vars) | varies | duplicate SSA name |
| 07_enum_match | Switch/EnumTag | varies | variant not recognized |
| 08_list | ListInit | 176B | type mismatch |
| 09_string_methods | Call (method) | varies | method dispatch broken |
| 10_result | WrapOk/Err | varies | return type mismatch |
| 11_closure | ClosureCreate | varies | params empty, ret void |

## Findings

### Root Cause Identified

The root cause is NOT enum payload corruption. It's a **self-hosted compiler control flow bug**:

**The self-hosted compiler cannot return complex types from inside `if`/`match` blocks.**

When a function has `if condition { return complex_value }`, the `return` inside the `if`
body does NOT actually return. The control flow falls through to the code after the `if` block.
This affects:
- `strip_percent`: can't strip `%` from strings (worked around by not adding `%`)
- `emit_struct_init_from_values`: can't be called from inside a conditional
- `try_emit_struct_construct`: can't dispatch struct construction from within a check
- `emit_field_set`: silently returns unchanged state when struct entry not found

This is caused by the MIR lowering in `lower.mn` not properly terminating blocks when
`Return` instructions appear inside `if` blocks. The `lower_if` creates separate blocks
for then/else/merge, and a `Return` in the then block gets captured as the then-block's
last instruction, but the merge block still gets emitted and executed.

### What Was Fixed (6/15 → partial)

1. String globals at module level (emit_llvm.mn)
2. println/print unknown type handling (emit_llvm.mn)
3. Named struct type in extractvalue (emit_llvm.mn)
4. Block ordering for if/for/match terminators (lower.mn)
5. Return expression parsing (parser.mn — explicit `Some()` wrap)
6. Void phi elimination for if-branches (lower.mn)
7. Lambda name without `%` prefix (lower.mn)
8. Double `%%` in list push (emit_llvm.mn)
9. Struct construction via `__new_` Call pattern (parser.mn + emitter)

### What's Still Blocked (9/15)

All remaining failures trace back to the **if-block-return bug**:
- Struct construction: `__new_` handler can't dispatch from conditional
- Loop variables: loop body mutations don't propagate
- Enum match: variant tag checks can't dispatch
- String methods: method resolution involves conditionals
- Closures: lambda param detection involves conditionals
- Result types: unwrap/match involves conditionals

### Fix Path

The fix must be in the Python bootstrap's lowerer (`mapanare/lower.py`) or the text emitter
(`mapanare/emit_llvm_text.py`). The self-hosted `lower.mn` generates the broken IR, so the
fix needs to either:

1. Fix the block termination logic in `lower.mn`'s `lower_if` to properly propagate
   `Return` instructions through nested blocks
2. Or add a post-processing pass that detects unterminated blocks after `Return` and
   adds proper `br` terminators

## Current Status

- 6/15 stage2 valid IR: 01_hello, 02_arithmetic, 03_function, 04_if_else, 13_fib, 15_multifunction
- 9/15 blocked by self-hosted compiler control flow bug (returns inside if blocks)
