---
name: ir-audit
description: Audit LLVM IR for known pathologies — detects ALLOCA_ALIAS, EMPTY_SWITCH, RET_TYPE_MISMATCH, MISSING_PERCENT, DUPLICATE_CASE, PHI_UNDEF_REF, and more. Saves baselines for delta tracking.
---

# IR Audit

Run diagnostics on LLVM IR files to detect known bug patterns.

## Instructions

### 1. Audit a file

```bash
python scripts/ir_doctor.py audit mapanare/self/main.ll
```

To audit only functions from a specific module:

```bash
python scripts/ir_doctor.py --only lower__ audit mapanare/self/main.ll
```

### 2. Detected pathologies

| Code | Severity | Description |
|------|----------|-------------|
| ALLOCA_ALIAS | error | List alloca shared between push and len (real vs mitigated) |
| EMPTY_SWITCH | error | Switch with 0 cases (broken match lowering) |
| RET_TYPE_MISMATCH | error | ret type != function declared return type |
| MISSING_PERCENT | error | SSA name missing % prefix |
| DUPLICATE_CASE | error | Switch has duplicate case values |
| PHI_UNDEF_REF | error | Phi references undefined value |
| LOOP_PUSH | warning | List push inside a loop (potential O(n^2)) |
| UNREACHABLE_BLOCKS | warning | Blocks not reachable from entry |

### 3. Other diagnostic commands

```bash
# Validate IR with llvm-as only (no pathology check)
python scripts/ir_doctor.py check file.ll

# Extract a single function's IR
python scripts/ir_doctor.py extract mapanare/self/main.ll lower__lower_match

# Per-function metrics table
python scripts/ir_doctor.py table mapanare/self/main.ll
python scripts/ir_doctor.py --top 15 table mapanare/self/main.ll

# JSON per-function hashes (for diffing across builds)
python scripts/ir_doctor.py fingerprint mapanare/self/main.ll

# Compare bootstrap vs stage1 for a golden test
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn

# Compare two IR files directly
python scripts/ir_doctor.py diff-ir a.ll b.ll

# Compare ALL golden tests
python scripts/ir_doctor.py diff-all

# Show struct byte layout
python scripts/ir_doctor.py structmap LowerState
python scripts/ir_doctor.py structmap LowerState --offset 176
python scripts/ir_doctor.py structmap  # list all structs

# Debug journal
python scripts/ir_doctor.py journal
python scripts/ir_doctor.py note "tried X, result was Y"
```

### 4. Baselines

Audit results are saved to `.ir_doctor/`. On subsequent runs, the tool shows delta: which issues were FIXED, NEW, or REGRESSED.
