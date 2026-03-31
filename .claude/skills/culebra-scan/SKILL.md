---
name: culebra-scan
description: Run Culebra template-driven IR scan — 26 templates across ABI, IR, Binary, and Bootstrap categories. Detects unaligned strings, byte-count mismatches, struct layout divergence, empty switches, and more. Supports autofix, SARIF, and workflows.
---

# Culebra Scan

Run the Culebra template engine against the self-hosted compiler's IR output.

## Instructions

### 1. Full scan (all 26 templates)

Run inside WSL:

```bash
culebra scan mapanare/self/main.ll
```

### 2. Filtered scans

```bash
# By category
culebra scan mapanare/self/main.ll --tags abi
culebra scan mapanare/self/main.ll --tags ir
culebra scan mapanare/self/main.ll --tags bootstrap
culebra scan mapanare/self/main.ll --tags binary

# By severity
culebra scan mapanare/self/main.ll --severity critical
culebra scan mapanare/self/main.ll --severity critical,high

# Specific template
culebra scan mapanare/self/main.ll --id unaligned-string-constant
culebra scan mapanare/self/main.ll --id direct-push-no-writeback
culebra scan mapanare/self/main.ll --id empty-switch-body
```

### 3. Auto-fix

```bash
# Preview fixes
culebra scan mapanare/self/main.ll --autofix --dry-run

# Apply fixes
culebra scan mapanare/self/main.ll --autofix
```

### 4. Cross-reference against C runtime

```bash
culebra scan mapanare/self/main.ll --header runtime/native/mapanare_runtime.c
culebra abi mapanare/self/main.ll --header runtime/native/mapanare_runtime.c
```

### 5. Companion commands

```bash
# Validate IR
culebra check mapanare/self/main.ll

# Validate string byte counts
culebra strings mapanare/self/main.ll

# Detect IR pathologies
culebra audit mapanare/self/main.ll

# Per-function diff between stages
culebra diff stage1.ll stage2.ll

# Extract one function
culebra extract mapanare/self/main.ll function_name

# Per-function metrics
culebra table mapanare/self/main.ll --top 15
```

### 6. Workflows

```bash
culebra workflow bootstrap-health-check --input stage1_output=main.ll
culebra workflow pre-commit --input ir_file=main.ll
culebra workflow ci-full --input ir_file=main.ll --format sarif
```

### 7. Output formats

```bash
culebra scan mapanare/self/main.ll --format text      # Default, colored terminal
culebra scan mapanare/self/main.ll --format json      # Structured JSON
culebra scan mapanare/self/main.ll --format sarif     # GitHub Code Scanning
culebra scan mapanare/self/main.ll --format markdown  # CI reports
```

### 8. Interpret results

- Exit code **0** — no critical or high findings
- Exit code **1** — one or more critical/high findings detected

Key templates to watch for:
| ID | Severity | What it catches |
|---|---|---|
| `unaligned-string-constant` | Critical | String constants at odd addresses break pointer tagging |
| `empty-switch-body` | Critical | Switch with 0 cases — match arms not generated |
| `struct-layout-mismatch` | Critical | IR struct vs C header divergence |
| `byte-count-mismatch` | High | `[N x i8]` declared size vs actual content differs |
| `direct-push-no-writeback` | High | List push through GEP without temp writeback |
| `phi-predecessor-mismatch` | High | PHI references non-existent predecessor block |

### 9. Browse templates

```bash
culebra templates list
culebra templates list --tags abi
culebra templates show unaligned-string-constant
```
