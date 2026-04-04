# Mapanare v3.0.2 — Three-Stage Bootstrap

> The snake bites its own tail. For real this time.

**Status:** IN PROGRESS
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## Goal

One goal: **three-stage fixed point**.

```
Stage 0: Python compiles mnc_all.mn → stage1 binary (via C backend + gcc)
Stage 1: stage1 compiles mnc_all.mn → stage2 output
Stage 2: stage2 compiles mnc_all.mn → stage3 output
Verify:  stage2 output == stage3 output (fixed point)
```

Everything else is in service of this.

---

## Inherited State (from v3.0.1)

### What Works

| Component | Status |
|-----------|--------|
| mnc-stage1 binary | Self-compiles, produces 77K lines LLVM IR |
| Stage2 IR | Parses with llvm-as (5 structural issues auto-fixed) |
| Stage2 binary | Runs simple programs (needs 64MB stack) |
| C pipeline (lower.py + emit_c.py) | Functionally complete |
| 11/15 golden tests | Pass through stage1 + llvm-as |
| CI | Green (ruff + black + mypy + 832 tests + WASM) |

### What's Broken

| Problem | Root Cause | Impact |
|---------|-----------|--------|
| Stage2 can't parse its own source | Self-hosted parser doesn't handle generic type syntax (`Option<TypeExpr>`) | Blocks three-stage |
| COW state threading loses blocks | `add_block`/`set_block`/`emit_instr` through `Option<MIRFunction>` | Merge block instructions end up in entry block |
| 4/15 golden tests fail through stage1 | Struct field indices (2), enum sizing (1), Result types (1) | Self-hosted IR emitter quality |
| Stack overflow on large source | Large structs passed by value (680-byte LowerState) | Stage2 needs 64MB+ stack |

---

## Phase 1: Fix Self-Hosted Parser Generics

The self-hosted parser (`mapanare/self/parser.mn`) can't parse type annotations
with generics like `Option<TypeExpr>`, `List<MIRType>`, `Map<String, Int>`.

### 1.1 — Diagnose the Exact Failure

```bash
# Build stage1 and try to compile itself
python3 scripts/concat_self.py
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread
ulimit -s 65536
/tmp/mnc-stage1 mapanare/self/mnc_all.mn 2>&1 | head -20
```

The parser errors will show which specific syntax constructs fail.

### 1.2 — Fix Generic Type Parsing

The self-hosted `parse_type` function in `parser.mn` needs to handle:
- `Option<T>` → GenericType("Option", [T])
- `List<T>` → GenericType("List", [T])
- `Map<K, V>` → GenericType("Map", [K, V])
- Nested: `Option<List<Int>>` → GenericType("Option", [GenericType("List", [Int])])

Check the current implementation and fix it to handle the `<` `>` delimited
type arguments that appear in the self-hosted source.

### 1.3 — Verify Parser Handles All Self-Hosted Syntax

The self-hosted source (11,363 lines) uses these constructs:
- Generic types in annotations: `let x: Option<Foo> = ...`
- Generic types in function params: `fn f(x: List<Bar>) -> ...`
- Generic types in struct fields: `struct S { field: Option<T> }`
- Enum variant payloads with generic types
- `new StructName { field: value }` construct expressions
- `match` with `ConstructorPat`, `IdentPat`, `WildcardPat`
- `for _ in 0..N { ... }` range loops
- `list.push(x)` method calls
- String concatenation with `+`

After fixing generics, run stage1 on its own source and check for
remaining parser errors.

---

## Phase 2: Fix COW State Threading

The self-hosted lowerer's `add_block`, `set_block`, and `emit_instr` functions
thread state through `LowerState` which contains `Option<MIRFunction>`.

### The Bug

When `add_block` pushes a new block to `f.blocks`:
```mapanare
let mut blk_list: List<BasicBlock> = new_fn.blocks
blk_list.push(bb)
new_fn.blocks = blk_list
```

The COW list semantics should work: `blk_list` gets a copy-on-write reference,
`push` detaches and allocates a new buffer, then `new_fn.blocks = blk_list`
updates the function's blocks.

But when `set_block(s, merge_idx)` switches to the merge block and
`emit_instr(s, Phi(...))` appends to it, the instruction ends up in the
ENTRY block instead. This means blocks are created but instructions go
to the wrong block.

### Possible Fixes

**Option A: Flatten state** — Instead of `Option<MIRFunction>`, store the
function's blocks as a top-level field in `LowerState`. This avoids the
double-indirection through Option that may lose mutations.

**Option B: Use indices** — Store block instructions in a separate
`List<List<Instruction>>` indexed by block ID. `emit_instr` writes to
`instructions[current_block_idx]` instead of going through the function.

**Option C: Debug the COW** — Add tracing to the C runtime's `__mn_list_push`
to verify that the detach/copy works correctly when the list is nested
inside an Option inside a struct.

### Validation

After fixing, the stage2 IR should validate with `llvm-as` WITHOUT the
`fix_stage2_ir.py` post-processor.

---

## Phase 3: Fix Remaining Golden Tests

4 golden tests fail through stage1:

| Test | Error | Root Cause |
|------|-------|-----------|
| 06_struct.mn | invalid indices for insertvalue | Self-hosted emitter uses wrong GEP indices |
| 14_nested_struct.mn | invalid indices for insertvalue | Same as above |
| 07_enum_match.mn | Cannot allocate unsized type | Enum type not fully defined in IR |
| 10_result.mn | type mismatch { i1, ptr } vs i64 | Result unwrap type confusion |

Fix each in the self-hosted emitter (`emit_llvm.mn`).

---

## Phase 4: Three-Stage Bootstrap

### 4.1 — LLVM IR Path

```bash
# Stage 0: Python → stage1
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread

# Stage 1: stage1 → stage2
ulimit -s unlimited
/tmp/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
llvm-as /tmp/stage2.ll -o /tmp/stage2.bc
llc /tmp/stage2.bc -o /tmp/stage2.o -filetype=obj -relocation-model=pic
gcc /tmp/stage2.o runtime/native/mapanare_core.c -I runtime/native \
    -o /tmp/mnc-stage2 -lm -lpthread

# Stage 2: stage2 → stage3
/tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll

# Fixed point
diff /tmp/stage2.ll /tmp/stage3.ll  # Must be empty
```

### 4.2 — C Path (alternative)

If the LLVM IR path is too fragile, switch the self-hosted compiler to emit
C instead of LLVM IR. This requires:
1. Change `main.mn` to call a C emitter instead of `emit_mir_module`
2. The self-hosted C emitter (`emit_c.mn`, 770 lines) already exists but
   may not cover all MIR instructions

```bash
# Stage 1: stage1 → stage2.c
/tmp/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.c
gcc -O0 -I runtime/native /tmp/stage2.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage2 -lm -lpthread

# Stage 2: stage2 → stage3.c
/tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.c

# Fixed point
diff /tmp/stage2.c /tmp/stage3.c  # Must be empty
```

---

## Success Criteria

- [x] mnc-stage1 compiles its own source without parser errors
- [x] Stage2 IR validates with llvm-as (no post-processing needed) ← **DONE 2026-04-04**
- [x] 15/15 golden tests pass through stage1 ← **DONE 2026-04-04**
- [x] Stage2 binary produces correct IR ← **DONE 2026-04-04** (WrapNone bug in lower_let)
- [x] Three-stage fixed point reached (stage2 == stage3) ← **DONE 2026-04-04** (78,676 lines, 0 diff)
- [ ] `scripts/verify_fixed_point.sh` passes (automates the three-stage check)

---

## Tools

```bash
# Culebra (USE FOR EVERY BUILD/CRASH/DEBUG)
~/.cargo/bin/culebra wrap -- gcc ...
~/.cargo/bin/culebra wrap -- valgrind ...
~/.cargo/bin/culebra journal add "..." --action fix
~/.cargo/bin/culebra summary /tmp/stage1.c
~/.cargo/bin/culebra baseline diff /tmp/stage1.c

# Rebuild cycle
python3 scripts/concat_self.py
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread

# Stage2 IR fixup (temporary, remove when COW is fixed)
python3 scripts/fix_stage2_ir.py /tmp/stage2.ll /tmp/stage2_fixed.ll
llvm-as /tmp/stage2_fixed.ll -o /dev/null
```
