# v4.8.0 — Self-Hosted Workarounds — Continuation Prompt

> Fix the 3 classes of workarounds in emit_llvm.mn.
> You are in WSL. Run rebuild + golden + stage2 after every .mn change.

---

## Context

emit_llvm.mn has 8 workaround sites across 3 root causes: substr bug (4),
PHI zeroinitializer (2), ABI mismatch (2). Each needs root cause investigation
before the workaround can be removed.

## Execution

For each workaround:
1. Read the workaround code and comment
2. Write a minimal test case that reproduces the bug
3. Find the root cause (C runtime, emitter, or lowerer)
4. Fix the root cause
5. Remove the workaround
6. `python3 scripts/build_stage1.py` → `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → `python3 scripts/ir_doctor.py stage2`
7. Commit

## Rules

- Fix ONE workaround at a time, rebuild+verify between each
- If a fix breaks golden or stage2, revert before trying the next
- Document root cause in commit message
