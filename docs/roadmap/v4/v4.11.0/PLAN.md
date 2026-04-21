# Mapanare v4.11.0 — Self-Hosted Global Constants + MIRType Enum

> Add global constant support to the self-hosted compiler. Then migrate MIRType.

**Status:** DONE (Phase 2 complete; Phase 1 deferred — needs AST LetDef variant)
**Breaking:** No
**Prerequisite:** v4.10.0

---

## The Problem

Module-level `let TK_INT: String = "int"` produces invalid stage2 IR:
`insertvalue operand must be aggregate type`. The self-hosted lowerer
doesn't handle global constant initialization for String types.

This blocks MIRType string→enum migration.

---

## Phase 1: Global constant lowering

- [ ] In `lower.mn`, add handling for module-level `let` with String initializer
- [ ] Generate a global constant in the MIR module
- [ ] In `emit_llvm.mn`, emit `@TK_INT = private constant {ptr, i64} ...` for globals
- [ ] Rebuild + golden + stage2

## Phase 2: MIRType kind constants

- [ ] Add `let TK_INT: String = "int"` etc. to mir.mn (19 constants)
- [ ] Replace all `t.kind == "int"` with `t.kind == TK_INT` across 4 .mn files
- [ ] Rebuild + golden + stage2
- [ ] `grep '\.kind == "' mapanare/self/emit_llvm.mn` → 0

## Phase 3: (Stretch) MIRType kind as enum

- [ ] If global constants work, add a `tipo TypeKind` enum to mir.mn
- [ ] Change `MIRType.kind` from `String` to `TypeKind`
- [ ] Migrate all construction and comparison sites
- [ ] Rebuild + golden + stage2

---

## Exit Criteria

| Check | Required |
|-------|----------|
| Module-level let constants work in stage2 | YES |
| MIRType kind comparisons use named constants | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
