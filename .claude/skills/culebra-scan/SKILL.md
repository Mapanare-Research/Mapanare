---
name: culebra-scan
description: Run Culebra v2.0.0 template-driven scan on LLVM IR (.ll) or generated C (.c) — 49 templates across ABI, IR, Binary, Bootstrap, and C categories. Auto-detects file type. Supports autofix, SARIF, and workflows.
---

# Culebra Scan

Run the Culebra template engine against compiler output. Auto-detects `.ll` (LLVM IR) or `.c` (generated C) files.

## Instructions

### 1. Quick summary (start here)

```bash
culebra summary /tmp/stage2.ll       # One command: scan + types + fields + health + score
culebra summary /tmp/stage2.c        # Same for C output (v3.0.0)
culebra triage /tmp/stage2.ll --brief  # One-line root cause summary
```

### 2. Full scan

```bash
# LLVM IR (41 templates)
culebra scan mapanare/self/main.ll

# Generated C (8 templates) — auto-detected from .c extension
culebra scan /tmp/stage2.c

# Filter by category
culebra scan main.ll --tags abi
culebra scan main.ll --tags ir
culebra scan stage2.c --tags c
culebra scan main.ll --severity critical,high
culebra scan main.ll --id option-type-pun-zeroinit
```

### 3. Debugging workflow

```bash
# Find what's wrong
culebra triage stage2.ll --brief             # Root causes in one line
culebra explain stage2.ll return-type-divergence  # Show matched IR in context
culebra suggest stage2.ll --function lower_fn     # Prioritized fix suggestions

# Understand the code
culebra pretty stage2.ll --function lower_fn      # Syntax-highlighted IR
culebra inspect stage2.ll --function lower_fn     # Block-by-block control flow
culebra dump stage2.ll --function lower_fn        # Variable state dump
culebra trace stage2.ll --function lower_fn --var '%state'  # Follow a variable

# Compare stages
culebra diff main.ll stage2.ll                    # Per-function structural diff
culebra compare main.ll stage2.ll --metric calls  # Which functions lost calls?
culebra bisect main.ll stage2.ll                  # Rank divergent functions by impact

# For C backend (v3.0.0)
culebra diff stage2.c stage3.c                    # Fixed-point check on C output
culebra compare stage1.c stage2.c --metric calls  # C metric comparison

# After fixing
culebra verify stage2.ll break-inside-nested-control  # Confirm fix: PASS/FAIL
culebra baseline save stage2.ll                       # Save snapshot
culebra baseline diff stage2.ll                       # Compare after rebuild

# Semi-dynamic
culebra eval main.ll --function hardcoded_field_index --arg '"VarInfo"' --arg '"value"'
culebra test-fn main.ll --function fn_name --arg 0 --expect-ret 1

# Session logging
culebra wrap -- clang -c -O1 stage2.ll -o stage2.o   # Log command output
culebra learn                                          # Analyze logs for patterns
culebra journal add "fixed field indices" --action fix
```

### 4. Auto-fix

```bash
culebra scan main.ll --autofix --dry-run    # Preview
culebra scan main.ll --autofix              # Apply
```

### 5. Type analysis

```bash
culebra missing-types stage2.ll              # Find undefined types
culebra missing-types stage2.ll -v           # Show which functions use them
culebra infer-types stage2.ll --ll           # Generate type defs from insertvalue chains
culebra field-index-audit stage2.ll          # Find structs stuck at index 0
culebra health stage2.ll --struct LowerState # PHI zeroinit, type-pun, null loads
culebra crashmap stage2.ll --offset 0x20 --struct FnDefData  # Map crash to field
```

### 6. Key templates

| Category | Template | Severity | What |
|---|---|---|---|
| **IR** | `break-inside-nested-control` | Critical | Break dropped in if-inside-for |
| **IR** | `match-phi-zeroinit-corruption` | Critical | PHI corrupts state struct |
| **IR** | `option-type-pun-zeroinit` | Critical | Option discriminant clobbered |
| **ABI** | `return-type-divergence` | Critical | fn return type differs between stages |
| **ABI** | `sret-zeroinitializer-return` | Critical | match_merge zeros sret return |
| **C** | `switch-no-break` | High | Switch fallthrough in generated C |
| **C** | `missing-typedef` | Critical | Struct used but not defined in C |
| **C** | `union-tag-mismatch` | Critical | Wrong union member for tag |
