# Mapanare v3.3.0 — Fixed Point

> The compiler compiles itself. The output works. No Python.

**Status:** PLANNED
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (internal compiler change — language unchanged)

---

## The Problem

The compiler can compile itself (stage1 → stage2 IR validates with
llvm-as). But when stage2 IR is compiled to a binary and that binary
runs, it produces **wrong output**. Arithmetic becomes `@__op_+` calls,
variables go undefined, struct fields misalign.

Root cause: **enum tag mismatch**. The Python bootstrap assigns enum
variant tags (0, 1, 2, ...) in a different order than the self-hosted
compiler. When the Python-compiled binary (stage1) compiles the source
to produce stage2, the stage2 binary's `match` statements dispatch to
the wrong arms because its tag numbers don't match what stage1 embedded.

Example: `Instruction::BinOp` might be tag 3 in Python but tag 7 in
the self-hosted compiler. Stage2 sees a BinOp instruction with tag 3,
matches it as `Call` (which IS tag 3 in the self-hosted numbering),
and emits `@__op_+` instead of `add i64`.

**Python is not the reference.** Comparing stage1 vs stage2 output is
the wrong goal — they will always differ because they use different
emitters. The goal is **stage2 == stage3**: the self-hosted compiler
compiled by ITSELF produces the same output when it compiles itself
again.

---

## The Insight

Stop depending on enum tag numbers. The Instruction enum has 30
variants — if even one tag disagrees between compiler generations,
everything breaks. Enum tags are an **unstable ABI**.

The fix: **string-tagged dispatch**. Replace `match instr { BinOp(...)
=> ... }` with `if instr_kind(instr) == "binop" { ... }`. String
comparison works regardless of how enums are laid out in memory. The
string `"binop"` is `"binop"` no matter which compiler produced the
binary.

This is the same pattern already used for `BinOpKind` (via
`binop_kind_to_str`) and type dispatch (via `ty.kind`). Extend it to
the three critical enums: `Instruction`, `Expr`, `Stmt`.

---

## Inherited State (from v3.2.0)

| Component | Status |
|-----------|--------|
| Seed binary | 25/25 golden tests (no Python) |
| Self-compilation | Stage2 IR validates (llvm-as) |
| Stage2 binary | Broken (enum tag mismatch) |
| `__op_*` fallback | Handles arithmetic, not enough |
| PHI type recovery | Fixed for struct/bool types |
| C runtime | argv, argc, file_read, eprint, exit |

---

## Attack Order

### Phase 1: Tag Functions for All Critical Enums

Add `_kind` string accessor functions to the three enums that cross
the compilation boundary.

**mir.mn — Instruction:**
```mapanare
fn instr_kind(i: Instruction) -> String {
    match i {
        Const(_, _, _) => { return "const" },
        Copy(_, _) => { return "copy" },
        BinOp(_, _, _, _) => { return "binop" },
        Call(_, _, _) => { return "call" },
        ...
    }
}
```

**ast.mn — Expr and Stmt:**
```mapanare
fn expr_kind(e: Expr) -> String {
    match e {
        IntLit(_) => { return "int_lit" },
        Binary(_, _, _) => { return "binary" },
        ...
    }
}
```

These functions are compiled once and embedded. Even if the enum tags
shift between compilations, the string output is stable.

**Key insight:** These tag functions must be defined in the SAME module
as the enum (ast.mn for Expr/Stmt, mir.mn for Instruction). This way
the `match` inside the tag function uses the SAME tag numbering as
the enum definition. The tag function acts as a **stable bridge**
between the unstable enum layout and string-based dispatch.

### Phase 2: String-Based Dispatch in Emitter

Replace the `match instr { ... }` dispatch in `emit_llvm.mn` with
if/else chains on `instr_kind(instr)`:

```mapanare
fn emit_mir_instr(st: EmitState, instr: Instruction) -> EmitState {
    let kind: String = instr_kind(instr)
    if kind == "const" {
        let dest: Value = instr_dest(instr)
        ...
    }
    if kind == "binop" {
        let dest: Value = instr_dest(instr)
        let op: BinOpKind = instr_binop_kind(instr)
        ...
    }
    ...
}
```

Need accessor functions to extract fields from each variant:
- `instr_dest(i)` → Value (most variants have this)
- `instr_binop_kind(i)` → BinOpKind
- `instr_binop_lhs(i)` / `instr_binop_rhs(i)` → Value
- `instr_call_fn_name(i)` → String
- `instr_call_args(i)` → List<Value>
- etc.

Each accessor uses `match` internally (same-module, stable tags).

### Phase 3: String-Based Dispatch in Lowerer

Same pattern in `lower.mn` for Expr/Stmt dispatch:

```mapanare
fn lower_expr(st: LowerState, e: Expr) -> LowerResult {
    let kind: String = expr_kind(e)
    if kind == "int_lit" { ... }
    if kind == "binary" { ... }
    if kind == "call" { ... }
    ...
}
```

### Phase 4: String-Based Dispatch in Parser/Semantic

The parser creates AST nodes (fine — it's in the same compilation).
The semantic checker dispatches on Expr/Stmt variants. Convert those
match statements to string-based dispatch.

### Phase 5: Verify Fixed Point

```bash
# Stage 1: Python bootstrap (one last time)
python3 scripts/build_stage1.py

# Stage 2: stage1 compiles itself
./mnc-stage1 mnc_all.mn > stage2.ll
clang -c -O2 stage2.ll -o stage2.o
gcc stage2.o mnc_main.c mapanare_core.c -o mnc-stage2

# Stage 3: stage2 compiles itself
./mnc-stage2 mnc_all.mn > stage3.ll

# Fixed point: stage2 == stage3
diff stage2.ll stage3.ll  # must be identical

# Stage 2 works:
./mnc-stage2 tests/golden/02_arithmetic.mn | llvm-as  # must pass

# All golden:
for f in tests/golden/*.mn; do
    ./mnc-stage2 "$f" | llvm-as || echo "FAIL: $f"
done
```

Once stage2 == stage3, update the seed to stage2 and delete the
Python dependency from build_from_seed.sh. The build becomes:

```
seed → compile source → stage1 binary → compile source → stage2 (final)
```

Both stages use the same tag functions, so enum layout doesn't matter.

### Phase 6: True Build-From-Source

Update `build_from_seed.sh` to do the two-stage bootstrap:
1. Seed compiles source → stage1
2. Stage1 compiles source → stage2 (final)

Stage2 is the released binary. Verify with `--verify` flag.

---

## Why This Works

The enum layout mismatch happens because two DIFFERENT compilers
(Python vs self-hosted) assign different tag numbers. But a tag
function compiled in the SAME compilation as the enum always agrees
with itself:

```
Compilation A produces binary-A:
  - Instruction::BinOp has tag 7
  - instr_kind() for tag 7 returns "binop"
  - emit_mir_instr() checks if kind == "binop" → matches

Compilation B produces binary-B:
  - Instruction::BinOp has tag 3
  - instr_kind() for tag 3 returns "binop"
  - emit_mir_instr() checks if kind == "binop" → matches
```

The tag numbers differ, but the string bridge is stable. Any compiler
that correctly compiles the tag function will produce a working binary,
regardless of how it numbers enum variants internally.

---

## Scope

**What changes:**
- mir.mn: add `instr_kind()` + field accessors (~200 lines)
- ast.mn: add `expr_kind()`, `stmt_kind()` + field accessors (~150 lines)
- emit_llvm.mn: replace `match instr` with if/else on kind (~400 lines)
- lower.mn: replace `match expr` with if/else on kind (~300 lines)
- semantic.mn: replace `match expr` with if/else on kind (~200 lines)
- parser.mn: no change (creates AST, doesn't dispatch on it)

**What doesn't change:**
- Grammar, syntax, semantics — zero user-facing changes
- C runtime — unchanged
- Golden tests — unchanged (same programs, same output)
- MIR data structures — Instruction/Expr/Stmt enums stay

**Total estimate:** ~1,200 lines of mechanical refactoring.

---

## Success Criteria

- [ ] Tag functions for Instruction, Expr, Stmt (same-module, match-based)
- [ ] Emitter dispatches on `instr_kind()` strings, not enum match
- [ ] Lowerer dispatches on `expr_kind()` strings, not enum match
- [ ] Semantic checker dispatches on `expr_kind()` strings
- [ ] 25/25 golden tests pass on stage1 (Python-built)
- [ ] 25/25 golden tests pass on stage2 (self-compiled)
- [ ] Stage2 == Stage3 (fixed point)
- [ ] `build_from_seed.sh` does two-stage bootstrap, no Python
- [ ] Seed updated to self-compiled binary

---

## Tools

```bash
# Development (needs Python)
python3 scripts/build_stage1.py
python3 scripts/ir_doctor.py golden

# Verification (no Python)
bash scripts/build_from_seed.sh --verify

# Fixed-point check
bash scripts/verify_fixed_point.sh
```
