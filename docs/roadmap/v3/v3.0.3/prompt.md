# v3.0.3 — Make It Run — Continuation Prompt

> Continue the v3.0.3 execution in WSL. Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.0.3/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Use Culebra for ALL debugging

```bash
~/.cargo/bin/culebra wrap -- gcc ...
~/.cargo/bin/culebra wrap -- valgrind ...
~/.cargo/bin/culebra journal add "description" --action fix --tags "runtime"
~/.cargo/bin/culebra journal show
```

---

## Goal

Every golden test program, compiled through mnc-stage1, must produce correct
output when executed. v3.0.2 proved the IR is valid. v3.0.3 proves the
programs actually work.

**Current state: 14/15 produce correct output. 12_while is broken (empty output).
Exit codes are non-zero for most tests.**

---

## Attack Order

### Phase 1: Fix 12_while (CRITICAL — only wrong output)

The while loop test produces no output. Debug:
1. `mapanare/self/mnc-stage1 tests/golden/12_while.mn > /tmp/while.ll`
2. Inspect the IR — check loop structure, variable stores, back-edge
3. Compare with Python bootstrap: `python3 -m mapanare emit-llvm tests/golden/12_while.mn`
4. Fix in `mapanare/self/lower.mn` (likely `lower_assign` or while lowering)

### Phase 2: Fix Exit Codes

Programs return non-zero exit codes because `main()` returns void.
Options:
- Rename user's main to `@mn_main`, add `int main() { mn_main(); return 0; }` in driver
- Or have the emitter generate `define i32 @main() { ... ret i32 0 }`

### Phase 3: Runtime Test Harness

Create `scripts/test_runtime.sh`:
- Compile each golden test through the full pipeline
- Run binary, capture stdout
- Compare against expected output
- Report PASS/FAIL

### Phase 4: Stage2 Golden Tests

Run the same runtime tests with stage2-compiled binaries.
Fixed point guarantees identical IR, but verify execution too.

### Phase 5: Hardening (may spill to v3.0.4)

- print vs println semantics
- String escape sequences
- Error output to stderr
- Larger test suite

---

## Key Files

| File | Role | Changes Expected |
|------|------|------------------|
| `mapanare/self/lower.mn` | Self-hosted lowerer | **FIX: while loop / variable reassignment** |
| `mapanare/self/emit_llvm.mn` | LLVM IR emitter | **FIX: main return type / exit code** |
| `mapanare/self/lower_state.mn` | State management | May need update_var fix |
| `runtime/native/mnc_driver.c` | C entry point | May need mn_main wrapper |
| `scripts/test_runtime.sh` | Runtime test harness | **NEW** |

---

## Rebuild + Test Cycle

```bash
# 1. Rebuild stage1
bash scripts/rebuild.sh quick

# 2. Compile + run a golden test
ulimit -s unlimited
mapanare/self/mnc-stage1 tests/golden/12_while.mn > /tmp/test.ll
llvm-as /tmp/test.ll -o /tmp/test.bc
llc /tmp/test.bc -o /tmp/test.o -filetype=obj -relocation-model=pic
gcc /tmp/test.o runtime/native/mapanare_core.c -I runtime/native \
    -o /tmp/test -lm -lpthread
/tmp/test

# 3. Verify fixed point still holds
bash scripts/verify_fixed_point.sh

# 4. Run runtime test suite
bash scripts/test_runtime.sh
```

---

## Culebra Journal (inherited from v3.0.2)

```
★ 15/15 golden tests pass through mnc-stage1 + llvm-as
★ Stage3 struct names fixed (MIRType field index swap)
★ THREE-STAGE FIXED POINT REACHED (stage2.ll == stage3.ll, 78,676 lines)
★ Root cause: WrapNone bug in lower_let
```
