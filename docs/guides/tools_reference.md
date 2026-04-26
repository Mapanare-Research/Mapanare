# Tools Reference

> Exhaustive command reference for the Mapanare tooling suite. Moved
> here from `CLAUDE.md` to keep the top-level guidance slim.
> Spot-check and update this file when you add/change commands.

---

## Golden test harness

```bash
# Bootstrap-only (Windows)
python scripts/test_native.py

# Compare against mnc-stage1 (WSL)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Also run IR via lli (WSL)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run

# Regenerate reference files
python scripts/test_native.py --bless

# One test, verbose
python scripts/test_native.py --filter fib -v
```

Every run auto-updates `tests/golden/BENCHMARKS.md` with per-test
metrics (source lines, IR lines, IR size, function count, compile
time). Commit this file to track regressions over time.

---

## Rebuild cycle (WSL)

```bash
bash scripts/rebuild.sh           # concat + build + golden (default)
bash scripts/rebuild.sh quick     # concat + build only (fast iteration)
bash scripts/rebuild.sh full      # concat + build + golden + selftest + memory
bash scripts/rebuild.sh audit     # concat + build + audit main.ll
bash scripts/rebuild.sh worklist  # concat + build + show alloca alias work queue
```

---

## IR Doctor

Per-function diagnostics for the self-hosted compiler. Detects
ALLOCA_ALIAS, EMPTY_SWITCH, RET_TYPE_MISMATCH, MISSING_PERCENT,
DUPLICATE_CASE, PHI_UNDEF_REF, LOOP_PUSH, etc. Saves baselines to
`.ir_doctor/` — reruns show delta (fixed/new/regressed).

### Analysis

```bash
python scripts/ir_doctor.py audit mapanare/self/main.ll         # Audit + baseline + llvm-as
python scripts/ir_doctor.py --only lower__ audit main.ll        # Audit specific module
python scripts/ir_doctor.py worklist main.ll                    # Functions needing rewrite
python scripts/ir_doctor.py extract main.ll lower__lower_match  # Dump one function's IR
python scripts/ir_doctor.py check file.ll                       # llvm-as validation
python scripts/ir_doctor.py table main.ll                       # Per-function metrics table
python scripts/ir_doctor.py --top 15 table main.ll              # Top 15 largest functions
python scripts/ir_doctor.py fingerprint main.ll                 # JSON per-function hashes
python scripts/ir_doctor.py strings main.ll                     # Validate [N x i8] byte counts
```

### Rebuild + verify (WSL)

```bash
python scripts/ir_doctor.py golden     # Fresh compile+validate ALL golden
python scripts/ir_doctor.py selftest   # Self-compile mnc_all.mn
python scripts/ir_doctor.py memory     # Memory scaling test
python scripts/ir_doctor.py stage2     # Compile + validate stage2 IR
python scripts/ir_doctor.py xray       # Full stage2 build + runtime test
python scripts/ir_doctor.py snapshot   # Generate .stage1.ll files
```

### Compare + diff

```bash
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn   # Bootstrap vs stage1
python scripts/ir_doctor.py diff-ir a.ll b.ll                    # Compare two .ll files
python scripts/ir_doctor.py diff-all                             # All golden tests
python scripts/ir_doctor.py phi-check /tmp/stage2.ll             # Validate PHI transform
```

### Valgrind crash mapping

```bash
python scripts/ir_doctor.py valgrind tests/golden/11_closure.mn
python scripts/ir_doctor.py valgrind 11_closure.mn --struct EmitState
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mnc some_file.mn
python scripts/ir_doctor.py valgrind-map --timeout 60 ./my_binary --flag arg
```

### Struct layout

```bash
python scripts/ir_doctor.py structmap LowerState             # Show struct byte layout
python scripts/ir_doctor.py structmap LowerState --offset 176  # What field is at byte 176?
python scripts/ir_doctor.py structmap                        # List all structs with sizes
```

### Debug journal

```bash
python scripts/ir_doctor.py journal                  # View debug history
python scripts/ir_doctor.py note "tried X, got Y"    # Add note
```

---

## MIR Trace

Debug type inference issues in the Python lowerer.

```bash
python scripts/mir_trace.py tests/golden/10_result.mn divide           # One function
python scripts/mir_trace.py tests/golden/07_enum_match.mn              # All functions
python scripts/mir_trace.py tests/golden/10_result.mn divide -v        # Verbose
python scripts/mir_trace.py tests/golden/10_result.mn divide --json    # JSON output
python scripts/mir_trace.py tests/golden/10_result.mn divide --compare # MIR vs stage1 IR
```

---

## Self-hosted compiler build + fixed-point (WSL/Linux only)

```bash
python scripts/build_stage1.py                   # Build mnc-stage1 from Python bootstrap
bash scripts/verify_fixed_point.sh               # 3-stage self-compilation verification
bash scripts/verify_fixed_point.sh --keep        # Keep intermediate IR for debugging
```

---

## Culebra v2.4.0

Compiler diagnostics for LLVM IR AND C source (Rust, installed in WSL).
49+ YAML templates across ABI, IR, Binary, Bootstrap, C categories.
Nuclei-style pattern engine.

- Repo: `C:\Users\Juan\Documents\GitHub\Culebra` (also at
  github.com/Mapanare-Research/Culebra)
- crates.io: https://crates.io/crates/culebra

### Core scanning

```bash
culebra scan mapanare/self/main.ll                     # Run all templates
culebra scan main.ll --tags abi                        # ABI checks only
culebra scan main.ll --severity critical               # Critical findings only
culebra scan main.ll --id option-type-pun-zeroinit     # One template
culebra scan main.ll --autofix --dry-run               # Preview auto-fixes
culebra scan main.ll --autofix                         # Apply auto-fixes
culebra scan main.ll --header runtime/native/mapanare_runtime.c  # IR vs C structs
culebra scan main.ll --format json
culebra scan main.ll --format sarif                    # For GitHub Code Scanning
```

### AI-optimized debugging (v0.3.0+)

```bash
culebra triage main.ll                   # Group findings by root cause, dedupe
culebra triage main.ll --brief           # One-line summary
culebra compare stage1.ll stage2.ll --metric calls
culebra explain stage2.ll return-type-divergence
culebra bisect stage1.ll stage2.ll --top 30
culebra verify stage2.ll return-type-divergence       # PASS/FAIL for a fix
```

### C backend scanning (v2.0.0)

```bash
culebra scan stage2.c                    # Auto-detects .c
culebra scan stage2.c --tags c
culebra diff stage1.c stage2.c           # C fixed-point
```

C templates: `switch-no-break`, `missing-typedef`, `null-deref-pattern`,
`goto-dead-label`, `union-tag-mismatch`, `large-struct-by-value`,
`missing-return`, `buffer-overflow-pattern`.

### Debug feedback loop (v1.2.0+)

```bash
culebra wrap -- clang -c -O1 stage2.ll -o stage2.o    # Log command
culebra wrap -- valgrind /tmp/mnc-stage2 /tmp/tiny.mn
culebra learn                                          # Extract patterns from logs
culebra journal add "Fixed MIRFunction field indices" --action fix
culebra journal show                                   # Timeline
culebra journal show option                            # Search by keyword
```

### Semi-dynamic analysis (v1.1.0+)

```bash
culebra eval main.ll --function find_field_index --arg 0 --arg 0
culebra probe stage2.ll --function lower_fn --watch '%state'
culebra test-fn main.ll --function hardcoded_field_index --arg 0 --arg 0 --expect-ret 1
```

### One-shot summary

```bash
culebra summary stage2.ll                      # Scan + Types + Fields + Health + Score
culebra summary stage2.ll --struct LowerState  # Filter to one struct
```

### Inspection

```bash
culebra pretty stage2.ll                        # Module overview + function bars
culebra pretty stage2.ll --function lower_fn    # Syntax-highlighted IR
culebra dump stage2.ll --function lower_fn      # Variable dump
culebra dump stage2.ll --function lower_fn -v   # Also GEP chains
culebra inspect stage2.ll --function lower_fn   # Block-by-block walk
culebra stacktrace crash.log --ir stage2.ll     # Map valgrind/ASAN/gdb to IR
culebra missing-types stage2.ll                 # Find undefined named types
```

### Crash debugging

```bash
culebra crashmap stage2.ll --offset 0x20 --struct FnDefData
culebra trace stage2.ll --function lower_fn --var '%state'
culebra health stage2.ll --struct LowerState
culebra suggest stage2.ll --function lower_definition
```

### Baseline tracking (v0.4.0+)

```bash
culebra baseline save stage2.ll
culebra baseline diff stage2.ll
```

### CI gates

```bash
culebra lint-template stage2.ll return-type-divergence --expect  # FAIL if not fired
culebra lint-template stage2.ll option-type-pun-zeroinit --reject # FAIL if fired
```

### Type inference + field audit

```bash
culebra infer-types stage2.ll            # Infer missing type defs
culebra infer-types stage2.ll --ll       # As valid LLVM IR
culebra field-index-audit stage2.ll      # Detect index-0 bug
```

### Call graph + progress

```bash
culebra callchain stage2.ll --from lower --to current_block_terminated
culebra progress stage2.ll
culebra progress stage2.ll -b my-baseline.json
```

### Diagnostic map (symptom → templates)

```bash
culebra map crash
culebra map "type mismatch"
culebra map phi
```

### Other

```bash
culebra strings main.ll                  # Validate [N x i8] byte counts
culebra audit main.ll                    # IR pathology scan
culebra check main.ll                    # llvm-as wrapper
culebra diff stage1.ll stage2.ll         # Per-function structural diff
culebra extract main.ll my_function      # Dump one function's IR
culebra table main.ll --top 15           # Per-function metrics
culebra abi main.ll --header runtime/native/mapanare_runtime.c
culebra binary ./mnc-stage1 --ir main.ll
culebra phi-check /tmp/stage2.ll
culebra pipeline                         # Full pipeline from culebra.toml
culebra fixedpoint ./mnc-stage1 mapanare/self/mnc_all.mn
culebra templates list
culebra templates show option-type-pun-zeroinit
culebra workflow bootstrap-health-check --input stage1_output=stage1.ll
culebra watch --patterns '*.ll,*.mn' culebra scan main.ll
culebra test                             # Run [[tests]] from culebra.toml
culebra run ./mnc-stage1 test.mn --expect "hello"
culebra init                             # Starter culebra.toml
culebra drain .culebra-queue.yaml        # Mapanare dynamic-queue integration
```

---

## GitNexus

Code intelligence indexed separately — see `.claude/skills/gitnexus/`
SKILL.md files for usage.

| Task | Skill file |
|------|------------|
| Architecture questions | `gitnexus-exploring/SKILL.md` |
| Blast radius before edit | `gitnexus-impact-analysis/SKILL.md` |
| Bug tracing | `gitnexus-debugging/SKILL.md` |
| Rename / extract / split | `gitnexus-refactoring/SKILL.md` |
| Tools + schema reference | `gitnexus-guide/SKILL.md` |
| CLI (index, status, clean, wiki) | `gitnexus-cli/SKILL.md` |

Index refresh after commit:

```bash
npx gitnexus analyze                # fresh index (deletes embeddings)
npx gitnexus analyze --embeddings   # preserve embeddings
```

A PostToolUse hook re-runs analyze after `git commit`/`git merge`.
