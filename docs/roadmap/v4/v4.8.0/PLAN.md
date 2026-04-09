# Mapanare v4.8.0 — Solid Core (Fix Everything Before Features)

> No new features until the core is bulletproof.

**Status:** IN PROGRESS
**Breaking:** No
**Prerequisite:** v4.7.1

---

## Diagnosis (what we learned)

### Drop glue / skip_struct_ret
The escape analysis code in emit_llvm_text.py is CORRECT for user programs
(40/40 golden pass with drop glue enabled). The problem is the SELF-HOSTED
COMPILER: when drop glue is enabled, the self-hosted semantic checker
(`semantic.mn`) reads invalid memory in `ast__expr_ident_name`, which corrupts
state and causes crashes in subsequent lowering.

**Root cause:** `semantic.mn` has memory safety bugs — its AST accessor
functions read freed data. This was hidden by `skip_struct_ret` (which leaks
all strings in struct-returning functions instead of freeing them).

### What's blocking drop glue removal
1. Fix `semantic.mn` AST accessor memory safety
2. OR: don't call `check()` in the self-hosted compile() pipeline (current state)
3. Then: remove `skip_struct_ret` and get proper string cleanup

### Culebra findings
- `field-index-always-zero` — confirmed: unregistered structs get index 0
- `undefined-named-type` — confirmed: struct types not defined in IR
- 8 Culebra templates have YAML parse errors (template bugs, not code bugs)
- Scanning main.ll times out (866K lines) — need to scan individual golden outputs

---

## Remaining work (deferred items from v4.2.0-v4.7.1)

### Phase 1: hardcoded_field_index (self-hosted, needs rebuild)
- Replace with auto-derived mapping from struct definitions
- Delete the ~160 line function
- Fixes Culebra `field-index-always-zero` finding

### Phase 2: MIRType string → enum (self-hosted, needs rebuild)
- Add TypeKind enum to mir.mn
- Replace all `== "int"` etc.

### Phase 3: Self-hosted workaround fixes (needs rebuild)
- PHI zeroinitializer, substr off-by-one, ABI mismatch

### Phase 4: Self-hosted optimization passes (needs rebuild)
- Constant folding, propagation, dead block elimination

### Phase 5: Fix semantic.mn memory safety
- Valgrind trace: ast__expr_ident_name invalid reads
- Once fixed, re-enable check() in compile() and remove skip_struct_ret

### Phase 6: String pooling (needs constant-tag or non-freeable marker)
- str(true)/str(false) should not allocate
- Small int pool for -128..127

### Phase 7: Fix Culebra templates
- Fix 8 broken templates in Culebra repo

---

## Exit Criteria

| Check | Required |
|-------|----------|
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| hardcoded_field_index deleted | YES |
| MIRType uses enum | YES |
| All workarounds removed | YES |
| Self-hosted constant folding | YES |
| semantic.mn memory-safe | YES |
| skip_struct_ret removed | YES |
| str(true) = constant | YES |
| Culebra: 0 critical on golden IR | YES |
