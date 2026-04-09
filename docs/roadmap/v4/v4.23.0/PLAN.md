# Mapanare v4.23.0 — MIRType Enum Migration

> Replace string-based type comparisons with a real TypeKind enum. Zero TK_*() calls.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.22.0

---

## The Problem

MIRType.kind is a String throughout the self-hosted compiler. Type checks
like `t.kind == "int"` are slow (string comparison) and fragile (typos
compile but produce wrong behavior). v4.11.0 added named constants
(`TK_INT()`, `TK_FLOAT()`, etc.) that return strings — a partial fix.

This version replaces the String with a real TypeKind enum and converts
all ~111 comparison sites across 4 files.

---

## Phase 1: Define TypeKind enum in mir.mn

- [ ] Add `enum TypeKind` with all 18+ variants (TkInt, TkFloat, TkBool, ...)
- [ ] Add accessor functions for each variant
- [ ] Do NOT change MIRType yet — just define the enum

## Phase 2: Change MIRType.kind to TypeKind

- [ ] Change `kind: String` to `kind: TypeKind` in MIRType struct
- [ ] Update all MIRType constructors (mir_int, mir_float, mir_bool, etc.)
- [ ] Update all comparison sites: `t.kind == "int"` → `t.kind == TkInt`
- [ ] Update all TK_*() call sites to use the enum variant directly
- [ ] Delete the TK_*() string-returning functions
- [ ] Rebuild + golden + stage2

## Phase 3: Update emit_llvm_ir.mn

- [ ] `resolve_mir_type` must match on TypeKind enum instead of strings
- [ ] All 17 type→LLVM-type mappings updated

## Phase 4: Update emit_llvm.mn

- [ ] All ~58 type comparison sites updated
- [ ] `resolve_type` and helpers use TypeKind

## Phase 5: Update lower.mn and lower_state.mn

- [ ] All ~24 type comparison sites updated
- [ ] Type construction uses TypeKind enum

## Phase 6: Update semantic.mn

- [ ] All ~12 type comparison sites updated

---

## Exit Criteria

| Check | Required |
|-------|----------|
| TypeKind enum defined in mir.mn | YES |
| MIRType.kind uses TypeKind (not String) | YES |
| All TK_*() functions deleted | YES |
| No `t.kind == "string_literal"` comparisons remain | YES |
| 45/45 golden | YES |
| 11/11 stage2 | YES |
