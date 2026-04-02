---
name: golden
description: Run the 15/15 golden test suite — compiles all golden test programs through mnc-stage1 and validates with llvm-as. Shows delta from last run (FIXED/REGRESSED/CHANGED).
---

# Golden Tests

Compile all golden test programs through the self-hosted compiler and validate the output IR.

## Instructions

### 1. Run the golden suite

```bash
python scripts/ir_doctor.py golden
```

### 2. Interpret results

- **OK** — llvm-as validates, no ir_doctor pathologies
- **WARN(N)** — llvm-as validates but ir_doctor found N issues (check audit)
- **INVALID** — llvm-as rejects the IR (type mismatch, undefined value, etc.)
- **COMPILE_FAIL** — mnc-stage1 crashed (SIGSEGV, timeout, etc.)
- **EMPTY** — mnc-stage1 produced no functions (header only)

### 3. If tests regressed

Run targeted diagnostics:

```bash
# Audit the specific failing test's IR
python scripts/ir_doctor.py audit /tmp/failing_test.ll

# Extract a specific function
python scripts/ir_doctor.py extract mapanare/self/main.ll lower__lower_match

# Compare bootstrap vs stage1 output
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn
```

### 4. If all 15 pass

Report the score and any delta from the previous run. The baseline is saved in `.ir_doctor/golden.json`.

### 5. Always verify tests too

After any code change that affects the golden suite:

```bash
python -m pytest tests/self_hosted/ tests/bootstrap/ -q --tb=short
```

The golden suite tests the **compiled binary**. The pytest suite tests the **Python compiler**. Both must pass.
