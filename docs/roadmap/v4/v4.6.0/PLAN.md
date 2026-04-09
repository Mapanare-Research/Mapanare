# Mapanare v4.6.0 — Self-Hosted Quality (Clean Compiler)

> No workarounds. No manual tables. No string-typed enums.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.5.0 (type system must be sound before cleaning up the compiler)

---

## The Core Problems

The self-hosted compiler has accumulated workarounds and fragile patterns:

1. `hardcoded_field_index` — ~160 lines of manual struct→field index mapping
2. `MIRType.kind` uses string comparisons (`t.kind == "int"`) instead of enum
3. Active workarounds for PHI zeroinitializer, substr off-by-one, ABI mismatch
4. 2 legacy typed pointers (`i64*`, `void ()*`)

These make the compiler fragile and hard to maintain. Adding a struct field
requires updating a table. A typo in a kind string silently breaks type checking.

---

## Phase 1: Replace Hardcoded Field Index Table

### 1A. Understand the current system

- [ ] Read `emit_llvm.mn` `hardcoded_field_index()` (~line 1095)
- [ ] Document: which structs are in the table, how many fields each
- [ ] Identify: where is this function called? (should be GEP emission)

### 1B. Auto-derive from struct definitions

- [ ] During lowering or emission, when struct types are registered, build the
      field→index mapping automatically from `StructInfo.fields`
- [ ] Store in a `Map<String, Map<String, Int>>` (struct_name → field_name → index)
- [ ] Replace all calls to `hardcoded_field_index` with map lookup
- [ ] Delete the `hardcoded_field_index` function

### 1C. Test

- [ ] `/golden` — all pass (field indices must match before and after)
- [ ] Add a golden test that exercises field access on a 5+ field struct
- [ ] `/rebuild` + verify fixed point

**Files:** `mapanare/self/emit_llvm.mn`, `mapanare/self/lower.mn`

---

## Phase 2: MIRType Kind Enum

### 2A. Define kind enum

- [ ] In `mir.mn`, add a `TypeKind` enum (or tipo) with variants:
      `Int, Float, Bool, String, Void, Struct, Enum, List, Map, Option, Result,
      Signal, Stream, Agent, Fn, Any, Tensor`
- [ ] Add `kind` field to `MIRType` as `TypeKind` instead of `String`

### 2B. Migrate consumers

- [ ] Replace all `t.kind == "int"` with `t.kind == TypeKind::Int` (or match)
- [ ] This affects: `lower.mn`, `lower_state.mn`, `emit_llvm.mn`, `emit_llvm_ir.mn`
- [ ] Search for every string literal that could be a kind tag

### 2C. Rebuild and verify

- [ ] `bash scripts/rebuild.sh`
- [ ] `/golden` — all pass
- [ ] `/stage2` — passes
- [ ] Search for remaining `== "int"`, `== "string"`, etc. — target: 0

**Files:** `mapanare/self/mir.mn`, `mapanare/self/lower.mn`,
`mapanare/self/lower_state.mn`, `mapanare/self/emit_llvm.mn`,
`mapanare/self/emit_llvm_ir.mn`

---

## Phase 3: Fix Self-Hosting Workarounds

### 3A. PHI zeroinitializer bug

- [ ] Read `emit_llvm.mn:3205` — uses string variable to "avoid if-expression
      (PHI zeroinitializer bug in stage2)"
- [ ] Investigate root cause: what generates the zeroinitializer PHI?
- [ ] Fix the lowerer or emitter to produce correct PHI nodes
- [ ] Replace the workaround with a normal if-expression
- [ ] Verify with `/stage2` — stage2 IR should not have zeroinitializer PHIs

### 3B. substr off-by-one

- [ ] Read `emit_llvm.mn:2588` — uses `.contains() + .replace()` because
      "substr has off-by-one issues in the compiled binary"
- [ ] Write a minimal test case: `"hello".substr(1, 3)` in .mn, compile with
      mnc-stage1, run, check output
- [ ] Find the off-by-one in the C runtime's `__mn_str_substr` or in the
      self-hosted emitter's substr lowering
- [ ] Fix it and replace the workaround

### 3C. ABI mismatch with C runtime

- [ ] Read `emit_llvm.mn:2513` — inlines range construction to "avoid ABI
      mismatch with C runtime"
- [ ] The issue: self-hosted compiler expects `{i64, i64}` but C runtime returns
      `void*` (or similar)
- [ ] Fix: either change the C runtime's range function to return `{i64, i64}`
      or change the emitter to call the correct signature
- [ ] Replace the inlined workaround with a proper function call

### 3D. Rebuild and verify

- [ ] `bash scripts/rebuild.sh full`
- [ ] `/golden` — all pass
- [ ] `/stage2` — passes
- [ ] Verify fixed point maintained

**Files:** `mapanare/self/emit_llvm.mn`, `runtime/native/mapanare_core.c`

---

## Phase 4: Typed Pointers Cleanup

### 4A. Replace `i64*` in tensor alloc

- [ ] In `emit_llvm.mn:371`, replace `"i64*"` with `"ptr"` in the
      `__mapanare_tensor_alloc` declaration
- [ ] Verify: tensor golden test passes (if exists), or tensor builtins still work

### 4B. Replace `void ()*` in function constants

- [ ] In `emit_llvm.mn:789`, replace `"void ()* @"` with just `"ptr @"` —
      under opaque pointer mode, function references are already `ptr`
- [ ] Remove the bitcast entirely

### 4C. Verify LLVM compatibility

- [ ] `llvm-as` the output IR — must pass with no typed pointer warnings
- [ ] `/golden` — all pass

**Files:** `mapanare/self/emit_llvm.mn`

---

## Phase 5: Verification

- [ ] `.\dev.ps1 validate` — full validation
- [ ] `/golden` — 40/40
- [ ] `/rebuild` + `/stage2`
- [ ] Search for `hardcoded_field_index` — must not exist
- [ ] Search for `== "int"`, `== "string"`, `== "float"` in self-hosted — target: 0
- [ ] Search for `i64*`, `void ()*` in self-hosted — target: 0
- [ ] Search for "avoid", "workaround", "bug in stage2" comments — target: 0
- [ ] Verify fixed point: stage3 == stage4

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `hardcoded_field_index` deleted, auto-derived mapping in place | YES |
| MIRType uses enum kind (not string comparisons) | YES |
| PHI zeroinitializer workaround removed (root cause fixed) | YES |
| substr off-by-one workaround removed (root cause fixed) | YES |
| ABI mismatch workaround removed (root cause fixed) | YES |
| `i64*` and `void ()*` replaced with `ptr` | YES |
| All 40 golden tests pass | YES |
| Self-hosted rebuild + fixed point maintained | YES |
| Zero "workaround"/"avoid"/"bug in stage2" comments remaining | YES |
