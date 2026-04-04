# Mapanare v3.0.3 — Make It Run

> The compiler compiles itself. Now the programs must run.

**Status:** IN PROGRESS
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## Goal

Every golden test program, compiled through mnc-stage1, must **produce correct output when executed**. v3.0.2 proved the fixed point (IR validates). v3.0.3 proves the compiled programs actually work.

---

## Inherited State (from v3.0.2)

### What Works

| Component | Status |
|-----------|--------|
| Three-stage fixed point | stage2.ll == stage3.ll (78,676 lines, 0 diff) |
| 15/15 golden tests | IR validates with llvm-as |
| Self-hosted compiler | 9,400+ lines, 10 modules, bilingual keywords |
| C pipeline | Python → C → gcc → stage1 binary |
| LLVM pipeline | stage1 → LLVM IR → llc → gcc → stage2 binary |

### Current Runtime Test Results

Compiled via: `mnc-stage1 test.mn → .ll → llvm-as → llc → gcc → binary`

| Test | Expected | Got | Status |
|------|----------|-----|--------|
| 01_hello | hello | hello | ✓ output, ✗ exit 192 |
| 02_arithmetic | 14 | 14 | ✓ output, ✗ exit 14 (value leaks) |
| 03_function | 30 | 30 | ✓ output, ✗ exit 30 |
| 04_if_else | big | big | ✓ output |
| 05_for_loop | 45 | 45 | ✓ output |
| 06_struct | 3 | 3 | ✓ output |
| 07_enum_match | green | green | ✓ output |
| 08_list | 4 | 4 | ✓ output |
| 09_string_methods | true\nHELLO WORLD | true\nHELLO WORLD | ✓ output |
| 10_result | 5 | 5 | ✓ output |
| 11_closure | 15 | 15 | ✓ output |
| 12_while | 5 | (empty) | ✗ NO OUTPUT |
| 13_fib | 55 | 55 | ✓ output, ✓ exit 0 |
| 14_nested_struct | 10 | 10 | ✓ output |
| 15_multifunction | 10\n15 | 10\n15 | ✓ output |

**14/15 produce correct output. 12_while is the only failure.**
Exit codes are non-zero for most tests (value leaking from main).

---

## Phase 1: Fix 12_while (the only wrong output)

`12_while.mn` uses `mien` (while loop) with mutable variable increment.
The compiled binary produces empty output. Likely causes:
- `update_var` doesn't persist the variable reassignment (`i = i + 1`)
- The while loop condition or body isn't compiled correctly
- The `mien` keyword might route to a different lowering path

### Diagnosis
1. Compile `12_while.mn` through stage1, inspect the IR
2. Check if `i = i + 1` generates Store to the alloca
3. Check if the loop back-edge jumps correctly
4. Compare with Python bootstrap's LLVM IR output

### Fix
Fix the while loop lowering or variable reassignment in the self-hosted lowerer/emitter.

---

## Phase 2: Fix Exit Codes

The `main()` function returns `void` in LLVM IR (`ret void`), but the C
entry point expects `int main()` to return 0. The undefined return register
leaks stale values as the process exit code.

### Approach A: Fix in mnc_driver.c
The driver already calls `compile_and_print()` and does `return 0`. For
golden test programs, the issue is that `@main` returns void but gcc
expects int. Add a C wrapper: `int main() { mn_main(); return 0; }`.

But the self-hosted emitter names the user's main function `@main`, which
conflicts with the C runtime's `main`. Fix: rename to `@mn_main` or
`@_mn_entry`, and have the driver call it.

### Approach B: Fix in the emitter
Have the emitter generate `define i32 @main()` with `ret i32 0` at the
end, wrapping the void body. This is what the Python C emitter does.

---

## Phase 3: Runtime Test Harness

Create `scripts/test_runtime.sh` that:
1. Compiles each golden test through stage1 → llvm-as → llc → gcc
2. Runs the binary and captures stdout
3. Compares against expected output (from Python `mapanare run`)
4. Reports PASS/FAIL with diff on failure
5. Exits non-zero if any test fails

This becomes the runtime correctness gate — complementing the IR validation
that `ir_doctor.py golden` already does.

---

## Phase 4: Run Stage2 Golden Tests

Once all 15 golden tests pass through stage1-compiled binaries, repeat
with stage2-compiled binaries. The fixed point guarantees the IR is
identical, so this should pass automatically. But running it confirms
the end-to-end pipeline works.

---

## Phase 5: Hardening (may spill to v3.0.4)

These are nice-to-haves that improve robustness but aren't blocking:

- **Print without newline**: `print()` vs `println()` — ensure `print`
  doesn't add a trailing newline (it currently uses `__mn_str_println`)
- **String escapes**: `\n`, `\t`, `\\` in string literals
- **Error messages**: self-hosted compiler should print parse/semantic
  errors to stderr, not mix with IR output
- **Memory leaks**: arena cleanup at program exit
- **Larger test suite**: port more tests from the Python bootstrap

---

## Success Criteria

- [ ] 15/15 golden tests produce correct output when executed
- [ ] All exit codes are 0 (clean shutdown)
- [ ] `scripts/test_runtime.sh` passes (automated runtime gate)
- [ ] Stage2-compiled binaries produce same results as stage1-compiled
- [ ] Three-stage fixed point still holds after all changes

---

## Tools

```bash
# Compile + run a single test
ulimit -s unlimited
mapanare/self/mnc-stage1 tests/golden/01_hello.mn > /tmp/test.ll
llvm-as /tmp/test.ll -o /tmp/test.bc
llc /tmp/test.bc -o /tmp/test.o -filetype=obj -relocation-model=pic
gcc /tmp/test.o runtime/native/mapanare_core.c -I runtime/native -o /tmp/test -lm -lpthread
/tmp/test

# Fixed point check (must still pass after changes)
bash scripts/verify_fixed_point.sh

# Golden IR validation
python3 scripts/ir_doctor.py golden

# Rebuild cycle
bash scripts/rebuild.sh quick
```
