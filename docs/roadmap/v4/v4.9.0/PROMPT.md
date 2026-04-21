# v4.9.0 — semantic.mn Memory Safety — Continuation Prompt

> Fix AST accessor memory safety so the self-hosted semantic checker works.
> You are in WSL. Run valgrind after every fix.

---

## Context

v4.8.0 fixed the emit_llvm.mn workarounds. Now fix the semantic checker.
The checker reads freed memory in ast__expr_ident_name during
check_call_resolved. This was confirmed by valgrind on an O0 build.

## Key Commands

```bash
# Build O0 for valgrind (better stack traces)
clang -O0 -g -c mapanare/self/main.ll -o /tmp/main_O0.o
gcc /tmp/main_O0.o /tmp/core.o /tmp/io.o /tmp/rt.o /tmp/gpu.o \
    /tmp/gpub.o /tmp/mnc_main.o -o /tmp/mnc-O0 -no-pie -rdynamic -lm -lpthread

# Valgrind with full detail
valgrind --num-callers=20 /tmp/mnc-O0 tests/golden/06_struct.mn 2>&1 | grep -A5 "Invalid"

# Normal rebuild + test cycle
python3 scripts/build_stage1.py
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
python3 scripts/ir_doctor.py stage2 --timeout 30
```

## Rules

- Run valgrind after EVERY ast.mn or semantic.mn change
- Fix one accessor at a time, rebuild between each
- The semantic checker must produce REAL errors for bad code, not crash
