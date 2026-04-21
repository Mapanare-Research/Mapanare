# v4.23.0 — MIRType Enum Migration — Continuation Prompt

> Replace all string type comparisons with enum variants. Delete TK_*().
> You are in WSL. Rebuild + golden + stage2 after every .mn change.
> Run lint before every commit. This is mechanical but high-risk — one
> wrong comparison crashes the compiler.

---

## Context

v4.11.0 added named constants (`TK_INT()`, `TK_FLOAT()`, etc.) that return
strings like `"int"`, `"float"`. This eliminated typos but the comparisons
are still string-based: `t.kind == TK_INT()` compares strings at runtime.

This version replaces the String with a real TypeKind enum. The MIR type
system becomes type-safe: a typo like `TkIntt` is a compile error, not a
silent bug. And the compiler uses `match` on TypeKind variants instead of
cascading `if` chains, enabling exhaustiveness checking.

## The Scale

~111 comparison sites across 5 files:

| File | Sites | What Changes |
|------|-------|-------------|
| `emit_llvm.mn` | ~58 | `resolve_type`, `is_byref_type`, push/emit helpers |
| `lower.mn` | ~24 | Type construction, type checking in lowering |
| `emit_llvm_ir.mn` | ~17 | `resolve_mir_type` (type→LLVM-type mapping) |
| `semantic.mn` | ~12 | Type checking, scope resolution |
| `mir.mn` | ~0 new | TypeKind enum definition, MIRType struct change, constructor updates |

## Strategy: File-at-a-Time Migration

Do NOT change all files at once. Change ONE file, rebuild, verify golden
tests. If tests break, the error is in that file. Fix before proceeding.

**Order:**
1. `mir.mn` — define TypeKind enum, change MIRType, update constructors
2. `emit_llvm_ir.mn` — smallest file, 17 sites
3. `semantic.mn` — 12 sites
4. `lower.mn` — 24 sites
5. `emit_llvm.mn` — largest file, 58 sites (do last, most risk)

After each file: `bash scripts/rebuild.sh` → golden tests must pass.

## Key Files

| File | Key Functions | What Changes |
|------|--------------|-------------|
| `mapanare/self/mir.mn` | `MIRType` struct, `mir_int()`, `mir_float()`, etc. | `kind: String` → `kind: TypeKind` |
| `mapanare/self/mir.mn` | `TK_INT()`, `TK_FLOAT()`, etc. | DELETE these functions |
| `mapanare/self/emit_llvm_ir.mn:66` | `resolve_mir_type(t)` | All `t.kind == "int"` → `match t.kind { TkInt => ... }` |
| `mapanare/self/emit_llvm.mn:246` | `resolve_type(st, ty)` | String comparisons → match on TypeKind |
| `mapanare/self/lower.mn` | Various type checks | `ty.kind == TK_INT()` → `ty.kind == TkInt` |
| `mapanare/self/semantic.mn` | Type checking | `ty.kind == "int"` → match-based |

## The TypeKind Enum

```mapanare
enum TypeKind {
    TkInt,
    TkFloat,
    TkBool,
    TkString,
    TkVoid,
    TkChar,
    TkStruct,
    TkEnum,
    TkList,
    TkMap,
    TkOption,
    TkResult,
    TkFn,
    TkAgent,
    TkSignal,
    TkStream,
    TkTensor,
    TkRange,
    TkPtr,
    TkUnknown
}
```

## Commands

```bash
# After every file change
bash scripts/rebuild.sh

# Quick test specific golden
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --filter 01_hello

# All golden
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Stage2
python3 scripts/ir_doctor.py stage2 --timeout 60

# Count remaining TK_*() calls (must reach 0)
grep -c 'TK_INT()\|TK_FLOAT()\|TK_BOOL()\|TK_STRING()' mapanare/self/*.mn

# Lint
black --check . && ruff check . && mypy mapanare/
```

## Rules

- Change ONE file at a time, rebuild + golden between each
- Start with mir.mn (the definition), not the consumers
- When changing comparisons, use the EXACT variant names from the enum
- If golden breaks after a file change, the error is in THAT file
- Do NOT fall back to string comparisons — commit to the enum
- The Python bootstrap does NOT change — only .mn files
- Record: how many TK_*() calls remain after each file migration

## Exit Criteria with Proof Commands

| Criterion | Proof Command |
|-----------|---------------|
| TypeKind enum exists | `grep 'enum TypeKind' mapanare/self/mir.mn` |
| MIRType uses TypeKind | `grep 'kind: TypeKind' mapanare/self/mir.mn` |
| Zero TK_*() calls | `grep -c 'TK_INT()\|TK_FLOAT()\|TK_BOOL()\|TK_STRING()\|TK_VOID()' mapanare/self/*.mn` → 0 |
| All golden pass | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → "All N tests passed" |
| Stage2 valid | `python3 scripts/ir_doctor.py stage2 --timeout 60` → "11/11" |
| Lint clean | `black --check . && ruff check . && mypy mapanare/` |
