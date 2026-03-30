---
name: stage2
description: Run stage2 validation — compile all self-hosted modules through mnc-stage1 and validate the output IR with llvm-as. Tests whether the compiler can compile itself.
---

# Stage 2 Validation

Test whether mnc-stage1 can compile its own source modules and produce valid LLVM IR.

## Instructions

### 1. Run stage2 validation

```bash
python scripts/ir_doctor.py stage2
```

For large files that need more time:

```bash
python scripts/ir_doctor.py stage2 --timeout 60
```

### 2. Interpret results

Each of the 10 self-hosted modules is compiled individually, plus `mnc_all.mn` (the full concatenated source):

- **OK** — valid llvm-as output
- **INVALID** — llvm-as error (type mismatch, undefined value, unsized type)
- **COMPILE_FAIL** — mnc-stage1 crashed
- **TIMEOUT** — exceeded timeout
- **FAIL** — mnc_all.mn produced 0 lines (OOM or silent failure)

### 3. Individual module errors vs mnc_all.mn errors

- **Individual module errors** (9/10 INVALID) are expected — cross-module `%struct.X` types aren't defined when compiling standalone. These don't block Phase 4.
- **mnc_all.mn errors** are the critical ones — this is the self-compilation path.

### 4. If mnc_all.mn has errors

```bash
# Get the full error
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>&1
llvm-as /tmp/stage2.ll -o /dev/null 2>&1

# Audit the stage2 IR
python scripts/ir_doctor.py audit /tmp/stage2.ll

# Check memory usage
/usr/bin/time -v ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /dev/null 2>&1
```

### 5. Target

**0 errors on mnc_all.mn** — this is the gate for Phase 4 (fixed-point verification).
