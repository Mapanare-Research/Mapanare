# v4.23.0 — MIRType Enum Migration — Continuation Prompt

> Replace all string type comparisons with enum variants. Delete TK_*().
> You are in WSL. Rebuild + golden + stage2 after every .mn change.

---

## Context

v4.11.0 added TK_INT()/TK_FLOAT()/etc. as string-returning functions.
This version replaces the String-based MIRType.kind with a real TypeKind
enum. ~111 sites across 4 files need updating. This is mechanical but
high-risk — every comparison site must be correct.

## Key files

- `mapanare/self/mir.mn` — TypeKind enum, MIRType struct, constructors
- `mapanare/self/emit_llvm_ir.mn` — resolve_mir_type (17 sites)
- `mapanare/self/emit_llvm.mn` — type resolution (58 sites)
- `mapanare/self/lower.mn` — type construction (24 sites)
- `mapanare/self/semantic.mn` — type checking (12 sites)

## Rules

- Define enum FIRST, change MIRType SECOND, update files ONE AT A TIME
- Rebuild + golden after each file
- If golden breaks, you changed a comparison wrong — find it
- The Python bootstrap does NOT change — only .mn files
