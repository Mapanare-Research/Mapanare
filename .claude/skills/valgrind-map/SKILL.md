---
name: valgrind-map
description: Run valgrind on the self-hosted compiler and automatically map crash offsets to Mapanare struct fields. Diagnoses uninitialised values, invalid reads, and use-after-free.
---

# Valgrind Field Mapper

Run valgrind on a crashing binary and automatically identify which struct field is corrupted.

## Instructions

### 1. Run on a crashing test

```bash
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/11_closure.mn
```

### 2. Map against a specific struct

When you know which struct is involved:

```bash
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mapanare/self/mnc-stage1 some_file.mn
```

### 3. With longer timeout

For large files:

```bash
python scripts/ir_doctor.py valgrind-map --timeout 60 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn
```

### 4. Interpret output

The tool reports:
- **Issue type** — Uninitialised value, Invalid read/write, Conditional jump
- **Function** — where the crash occurred
- **Byte offset** — into the stack allocation or heap block
- **Field mapping** — which Mapanare struct field is at that offset

Example output:
```
Valgrind Analysis
=================
Issue: Uninitialised value
Function: lower__lower_lambda
Offset: 176 bytes into stack allocation

Field Mapping (LowerState, 240 bytes):
  Offset 176 → enum_variants (List<EnumVariantNames>)
  Field type: {ptr, i64, i64, i64} (32 bytes)
```

### 5. Clean runs

If valgrind reports 0 issues, the binary is memory-clean for that input. This is useful for confirming fixes.

### 6. WSL/Linux only

Valgrind requires Linux. Run this in WSL, not Windows PowerShell.
