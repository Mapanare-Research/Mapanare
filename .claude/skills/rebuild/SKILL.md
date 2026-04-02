---
name: rebuild
description: Full rebuild cycle — concatenate self-hosted modules, build mnc-stage1 via Python text emitter + clang, run golden tests. The one command that answers "does the compiler work right now?"
---

# Rebuild Self-Hosted Compiler

Concatenate, compile, and test the self-hosted compiler in one shot.

## Instructions

### 1. Choose the rebuild mode

The user may specify a mode. Default is the standard rebuild.

| Mode | Command | What it does |
|------|---------|--------------|
| default | `bash scripts/rebuild.sh` | concat + build + golden |
| quick | `bash scripts/rebuild.sh quick` | concat + build only (fast iteration) |
| full | `bash scripts/rebuild.sh full` | concat + build + golden + selftest + memory |
| audit | `bash scripts/rebuild.sh audit` | concat + build + audit main.ll |

### 2. Run the rebuild

```bash
bash scripts/rebuild.sh
```

This runs on **WSL/Linux only** (needs clang, llvm-as).

### 3. Check results

The output shows:
- Build status (success/fail)
- Golden test results (15/15 target)
- Delta from last run (FIXED/REGRESSED)
- Baseline saved to `.ir_doctor/`

### 4. If build fails

Common failures:
- **Semantic error in .mn files** — check for `Undefined function` or `Cannot assign to immutable`. Fix the .mn source.
- **clang error** — check `mapanare/self/main.ll` for invalid LLVM IR. Run `llvm-as main.ll` to find the line.
- **Timeout** — the O(n^2) string concat bug may have returned. Check `emit_mir_module` uses `join("\n", st.lines)`.

### 5. If golden tests regress

```bash
# Quick diagnosis
python scripts/ir_doctor.py golden

# Compare with previous baseline
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn
```

### 6. After successful rebuild

Always verify the pytest suite:

```bash
python -m pytest tests/self_hosted/ tests/bootstrap/ -q --tb=short
```
