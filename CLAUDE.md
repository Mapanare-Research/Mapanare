# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mapanare is an AI-native compiled programming language (v2.1.0) with first-class agents, signals, streams, and tensors. It compiles to LLVM IR (native backend via llvmlite) and WebAssembly (WAT/WASM). A legacy Python transpiler backend exists for reference and bootstrapping only. The self-hosted compiler is 9,400+ lines of `.mn` across 10 modules in `mapanare/self/`. The language is frozen at v1.0 — syntax and semantics changes require RFC + deprecation cycle.

## Current Version & Roadmap

- **v1.0.0** — Language freeze, self-hosted fixed-point, formal memory model, stability guarantees
- **v1.1.0** — AI native: LLM drivers, embeddings, RAG as stdlib
- **v1.2.0** — Data & storage: SQL drivers, Dato v1.0, YAML/TOML
- **v1.3.0** — Web platform & security: crawler, vulnerability scanner, web framework
- **v2.0.0** — GPU compute (CUDA/Vulkan via dlopen), WebAssembly backend, mobile targets, Python backend deprecated
- **v2.1.0** (current) — Self-hosted compiler approaching fixed-point, stage2 validation, valgrind-based crash diagnostics

See `docs/roadmap/ROADMAP.md` for the full roadmap and `docs/roadmap/v2.0.0/PLAN.md` for the current execution plan.

## Pre-Push Validation (MANDATORY)

**Before ANY commit or push**, run the full validation suite. This mirrors CI exactly and writes results to `error.log`:

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT emission (runs once)
.\dev.ps1 validate         # Same as above (default mode), runs once and exits
.\dev.ps1 validate -Watch  # Validate then watch for changes
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only (black + ruff + mypy)
.\dev.ps1 fmt              # Auto-format (black + ruff --fix)
.\dev.ps1 e2e              # End-to-end tests only
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for all `examples/wasm/*.mn` files — this is what catches WASM CI failures locally. Running just `pytest` is NOT sufficient; the WASM cross-compilation step in CI compiles those examples and will fail independently of pytest.

**Quick partial checks** (use these during development, but always run full validate before pushing):

```bash
# WASM emission only (fast, catches the most common CI-only failures)
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
python -m mapanare emit-wasm examples/wasm/wasi_app.mn -o /dev/null

# Lint only (no tests)
black --check . && ruff check . && mypy mapanare/ runtime/

# Single test file
pytest tests/semantic/test_types.py -v

# Single test directory
pytest tests/parser/ -v
pytest tests/llvm/ -v
pytest tests/wasm/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v
make lint             # ruff check . && black --check . && mypy mapanare/ runtime/
make fmt              # black . && ruff check --fix .
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches and egg-info

# Run specific tests
pytest tests/parser/ -v              # Parser tests only
pytest tests/semantic/test_types.py  # Single test file
pytest tests/llvm/ -v                # LLVM emitter tests
pytest tests/bootstrap/ -v           # Self-hosted compiler tests

# Golden test harness (native compiler validation)
python scripts/test_native.py                                    # Bootstrap-only (Windows)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # Compare with native (WSL)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run  # Also run IR via lli
python scripts/test_native.py --bless                            # Regenerate reference files
python scripts/test_native.py --filter fib -v                    # One test, verbose

# Rebuild cycle (WSL) — one command for the full edit-compile-test loop
bash scripts/rebuild.sh              # concat + build + golden (default)
bash scripts/rebuild.sh quick        # concat + build only (fast iteration)
bash scripts/rebuild.sh full         # concat + build + golden + selftest + memory
bash scripts/rebuild.sh audit        # concat + build + audit main.ll
bash scripts/rebuild.sh worklist     # concat + build + show alloca alias work queue

# IR Doctor — per-function diagnostics for the self-hosted compiler
# Detects: ALLOCA_ALIAS (real vs mitigated), EMPTY_SWITCH, RET_TYPE_MISMATCH,
#          MISSING_PERCENT, DUPLICATE_CASE, PHI_UNDEF_REF, LOOP_PUSH, etc.
# Saves baselines to .ir_doctor/ — reruns show delta (fixed/new/regressed)
python scripts/ir_doctor.py audit mapanare/self/main.ll              # Audit + baseline + llvm-as
python scripts/ir_doctor.py --only lower__ audit mapanare/self/main.ll  # Audit specific module
python scripts/ir_doctor.py worklist mapanare/self/main.ll           # Functions needing recursive rewrite
python scripts/ir_doctor.py extract mapanare/self/main.ll lower__lower_match  # Dump one function's IR
python scripts/ir_doctor.py check file.ll                            # Just llvm-as validation
python scripts/ir_doctor.py golden                                   # Fresh compile+validate ALL golden (WSL, no cache)
python scripts/ir_doctor.py selftest                                 # Self-compile mnc_all.mn (WSL)
python scripts/ir_doctor.py memory                                   # Memory scaling test (WSL)
python scripts/ir_doctor.py table mapanare/self/main.ll              # Per-function metrics table
python scripts/ir_doctor.py --top 15 table mapanare/self/main.ll     # Top 15 largest functions
python scripts/ir_doctor.py fingerprint mapanare/self/main.ll        # JSON per-function hashes
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn       # Bootstrap vs stage1 (WSL)
python scripts/ir_doctor.py diff-ir a.ll b.ll                        # Compare two .ll files
python scripts/ir_doctor.py valgrind tests/golden/11_closure.mn       # Auto-run valgrind + map crash to fields (WSL)
python scripts/ir_doctor.py valgrind 11_closure.mn --struct EmitState  # Map against a different struct
python scripts/ir_doctor.py structmap LowerState                     # Show struct byte layout + field names
python scripts/ir_doctor.py structmap LowerState --offset 176        # What field is at byte 176?
python scripts/ir_doctor.py structmap                                # List all structs with sizes
python scripts/ir_doctor.py journal                                  # View debug history (runs + notes)
python scripts/ir_doctor.py note "tried X, result was Y"             # Add note to debug journal
python scripts/ir_doctor.py diff-all                                 # All golden tests (WSL)
python scripts/ir_doctor.py snapshot                                 # Generate .stage1.ll files (WSL)
python scripts/ir_doctor.py stage2                                   # Compile self-hosted modules through mnc-stage1, validate stage2 IR
python scripts/ir_doctor.py stage2 --timeout 60                      # With longer timeout
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn  # Run valgrind and map crash offsets to struct fields
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mnc some_file.mn  # Map against specific struct
python scripts/ir_doctor.py valgrind-map --timeout 60 ./my_binary --flag arg     # With timeout
python scripts/ir_doctor.py strings mapanare/self/main.ll                        # Validate string constant byte counts
python scripts/ir_doctor.py strings mapanare/self/main.ll -v                     # Also show duplicate strings
python scripts/ir_doctor.py xray                                                 # Full stage2 build + runtime test
python scripts/ir_doctor.py xray --timeout 60                                    # With longer timeout
python scripts/ir_doctor.py phi-check /tmp/stage2.ll                             # Validate PHI fix preserves structure

# MIR Trace — debug type inference issues in the Python lowerer
python scripts/mir_trace.py tests/golden/10_result.mn divide         # Trace types for one function
python scripts/mir_trace.py tests/golden/07_enum_match.mn            # Trace all functions in file
python scripts/mir_trace.py tests/golden/10_result.mn divide -v      # Verbose (all instructions)
python scripts/mir_trace.py tests/golden/10_result.mn divide --json  # JSON output
python scripts/mir_trace.py tests/golden/10_result.mn divide --compare  # Compare MIR vs stage1 IR

# Self-hosted compiler build + fixed-point (WSL/Linux only)
python scripts/build_stage1.py                   # Build mnc-stage1 from Python bootstrap
bash scripts/verify_fixed_point.sh               # 3-stage self-compilation verification
bash scripts/verify_fixed_point.sh --keep        # Keep intermediate IR for debugging

# Culebra v2.0.0 — compiler diagnostics for LLVM IR AND C source (Rust, installed in WSL)
# 29+ YAML templates across ABI, IR, Binary, Bootstrap categories. Nuclei-style pattern engine.
# Repo: C:\Users\Juan\Documents\GitHub\Culebra (also at github.com/Mapanare-Research/Culebra)
# crates.io: https://crates.io/crates/culebra

# --- Core scanning ---
culebra scan mapanare/self/main.ll                          # Run all templates against IR
culebra scan mapanare/self/main.ll --tags abi               # ABI checks only
culebra scan mapanare/self/main.ll --severity critical      # Critical findings only
culebra scan mapanare/self/main.ll --id option-type-pun-zeroinit  # One specific template
culebra scan mapanare/self/main.ll --autofix --dry-run      # Preview auto-fixes
culebra scan mapanare/self/main.ll --autofix                # Apply auto-fixes
culebra scan mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Cross-ref IR vs C structs
culebra scan mapanare/self/main.ll --format json            # JSON output
culebra scan mapanare/self/main.ll --format sarif           # SARIF for GitHub Code Scanning

# --- AI-optimized debugging (v0.3.0) ---
culebra triage mapanare/self/main.ll                        # Group findings by root cause, deduplicate
culebra triage mapanare/self/main.ll --format json          # Structured JSON for AI consumption
culebra compare stage1.ll stage2.ll --metric calls          # Per-function metric comparison (flags drops)
culebra compare stage1.ll stage2.ll --metric pushes --threshold 0.5  # Custom metric + threshold
culebra explain stage2.ll return-type-divergence            # Show matched IR in context + remediation
culebra explain stage2.ll option-type-pun-zeroinit --function parser  # Scoped to one function
culebra bisect stage1.ll stage2.ll                          # Find divergent functions ranked by impact
culebra bisect stage1.ll stage2.ll --top 30                 # Show more results
culebra verify stage2.ll return-type-divergence             # PASS/FAIL — verify a fix worked
culebra verify stage2.ll break-inside-nested-control --function tokenize  # Scoped verify

# --- C backend scanning (v2.0.0) — scan generated C for Mapanare v3.0.0 ---
culebra scan stage2.c                                       # Auto-detects .c, runs 8 C-specific templates
culebra scan stage2.c --tags c                              # C templates only
culebra scan stage2.c --id switch-no-break                  # Check for switch fallthrough
culebra scan stage2.c --id missing-typedef                  # Find undefined struct types
culebra diff stage1.c stage2.c                              # Fixed-point: compare C text output
culebra triage stage2.c --brief                             # Quick C summary
culebra summary stage2.c                                    # Full diagnostic (works for .c and .ll)
# C templates: switch-no-break, missing-typedef, null-deref-pattern, goto-dead-label,
#   union-tag-mismatch, large-struct-by-value, missing-return, buffer-overflow-pattern

# --- Debugging feedback loop (v1.2.0) — wrap commands, learn patterns, track journal ---
culebra wrap -- clang -c -O1 stage2.ll -o stage2.o          # Proxy command + log to .culebra-session.jsonl
culebra wrap -- valgrind /tmp/mnc-stage2 /tmp/tiny.mn        # Captures crashes, errors, output
culebra wrap -- llvm-as stage2.ll -o /dev/null               # Log LLVM errors for analysis
culebra learn                                                # Analyze session logs → extract error patterns + suggest templates
culebra learn -v                                             # Verbose: show individual failure details
culebra journal add "State doesn't persist in emit_instr" --action bug --tags "option,state" --function emit_instr
culebra journal add "Fixed MIRFunction field indices" --action fix --tags "field-index"
culebra journal add "mnc-stage2 runs!" --action milestone
culebra journal show                                         # View timeline of bugs/fixes/milestones
culebra journal show option                                  # Search journal by keyword

# --- Semi-dynamic analysis (v1.1.0) — call functions, probe values, test returns ---
culebra eval main.ll --function hardcoded_field_index --arg '"VarInfo"' --arg '"value"'  # Call and print return
culebra eval main.ll --function find_field_index --arg 0 --arg 0      # Integer args
culebra probe stage2.ll --function lower_fn --watch '%state'           # Inject printf, compile, run
culebra probe stage2.ll --function lower_fn --stop-at if_merge         # Stop at specific block
culebra test-fn main.ll --function hardcoded_field_index --arg 0 --arg 0 --expect-ret 1  # Unit test: PASS/FAIL

# --- Summary (v1.0.0) — one command for everything ---
culebra summary stage2.ll                                   # Scan + Types + Fields + Health + Score in 5 lines
culebra summary stage2.ll --struct LowerState               # Filter health to one struct

# --- Type inference + field audit (v0.9.0) — auto-generate types, detect index-0 bug ---
culebra infer-types stage2.ll                               # Infer missing type defs from insertvalue chains
culebra infer-types stage2.ll --ll                          # Output as valid LLVM IR (paste into file)
culebra field-index-audit stage2.ll                         # Find structs where ALL accesses use index 0
culebra field-index-audit stage2.ll --struct-filter LowerState  # Check specific struct

# --- Display + Inspection (v0.8.0) — syntax-highlighted IR, variable dumps, block walk ---
culebra pretty stage2.ll                                    # Module overview: stats, types, function size bars
culebra pretty stage2.ll --function lower_fn                # Syntax-highlighted IR with colored types/labels/terminators
culebra dump stage2.ll --function lower_fn                  # Variable dump: allocas, types, sizes, def-use counts, PHIs
culebra dump stage2.ll --function lower_fn -v               # Verbose: also show GEP chains
culebra inspect stage2.ll --function lower_fn               # Block-by-block control flow walk
culebra inspect stage2.ll --function lower_fn --block if_alpha  # Detail view of one block
culebra stacktrace crash.log --ir stage2.ll                 # Parse valgrind/ASAN/gdb output, map to IR

# --- Missing types (v0.7.0) — find undefined struct/enum types blocking compilation ---
culebra missing-types stage2.ll                             # Find all undefined named types
culebra missing-types stage2.ll -v                          # Also show which functions reference each

# --- Call graph + progress (v0.6.0) ---
culebra callchain stage2.ll --from lower --to current_block_terminated  # Find call paths between functions
culebra callchain stage2.ll --from lower_fn --to add_block --depth 5   # Shows struct types along chain
culebra progress stage2.ll                                              # IR stats + findings + health score
culebra progress stage2.ll -b my-baseline.json                         # Also compare against baseline

# --- Crash debugging (v0.5.0) — offset mapping, variable tracing, struct health ---
culebra crashmap stage2.ll --offset 0x20 --struct FnDefData  # "0x20 = field 4 (name: {ptr, i64})"
culebra crashmap stage2.ll --offset 0x20                     # Check all structs for that offset
culebra crashmap stage2.ll                                   # List all struct types with sizes
culebra trace stage2.ll --function lower_fn --var '%state'   # Follow variable through basic blocks
culebra trace stage2.ll --function tokenize --var '%pos'     # Shows every load/store/phi/call
culebra health stage2.ll --struct LowerState                 # PHI zeroinit, type-pun, null loads
culebra health stage2.ll                                     # Check all structs
culebra suggest stage2.ll --function lower_definition        # Prioritized fix suggestions for a function

# --- Baseline tracking (v0.4.0) — track progress across fix iterations ---
culebra baseline save stage2.ll                             # Save current findings as baseline
culebra baseline diff stage2.ll                             # Compare current scan vs baseline (Fixed/New/Remaining)
culebra baseline diff stage2.ll -b my-baseline.json         # Compare against specific baseline file

# --- Template assertions (v0.4.0) — CI gates and regression tests ---
culebra lint-template stage2.ll return-type-divergence --expect   # FAIL if template doesn't fire
culebra lint-template stage2.ll option-type-pun-zeroinit --reject # FAIL if template fires (regression)

# --- Triage --brief (v0.4.0) — minimal output for AI token efficiency ---
culebra triage stage2.ll --brief                            # One line: "9 root causes, 31 findings: ..."

# --- Diagnostic map (symptom → templates) ---
culebra map crash                                           # "what could cause this crash?"
culebra map "type mismatch"                                 # Search by symptom keyword
culebra map "zero tokens"                                   # Maps to relevant templates
culebra map phi                                             # PHI-related issues

# --- Drain queue (Mapanare integration) ---
culebra drain .culebra-queue.yaml                           # Process dynamically-queued checks
culebra drain .culebra-queue.yaml --clear                   # Process and clear queue

# --- IR analysis ---
culebra strings mapanare/self/main.ll                       # Validate [N x i8] byte counts
culebra audit mapanare/self/main.ll                         # Detect IR pathologies
culebra check mapanare/self/main.ll                         # Validate IR with llvm-as
culebra diff stage1.ll stage2.ll                            # Per-function structural diff
culebra extract mapanare/self/main.ll my_function           # Extract one function's IR
culebra table mapanare/self/main.ll --top 15                # Per-function metrics table

# --- ABI + binary ---
culebra abi mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Struct layout + sret
culebra binary ./mapanare/self/mnc-stage1 --ir main.ll      # ELF/PE inspection + .rodata cross-ref

# --- Bootstrap pipeline ---
culebra phi-check /tmp/stage2.ll                            # Validate transform preserves IR
culebra pipeline                                            # Run full stage pipeline from culebra.toml
culebra fixedpoint ./mnc-stage1 mapanare/self/mnc_all.mn    # Fixed-point convergence detection

# --- Templates + workflows ---
culebra templates list                                      # List all templates
culebra templates show option-type-pun-zeroinit             # Full template details
culebra workflow bootstrap-health-check --input stage1_output=stage1.ll  # Multi-step validation
culebra workflow playground-mapanare --input stage2_output=stage2.ll     # Playground workflow

# --- Misc ---
culebra watch --patterns '*.ll,*.mn' culebra scan main.ll   # Watch + re-scan on change
culebra test                                                # Run all [[tests]] from culebra.toml
culebra run ./mnc-stage1 test.mn --expect "hello"           # Compile, run, check output
culebra init                                                # Generate starter culebra.toml
```

## Testing the Native Compiler

Golden test corpus lives in `tests/golden/*.mn` (15 programs covering all features). Reference IR in `tests/golden/*.ref.ll`.

**Workflow for debugging mnc-stage1:**
1. Make changes to `mapanare/self/*.mn` or `mapanare/emit_llvm_mir.py`
2. Rebuild: `python scripts/build_stage1.py`
3. Test: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. The harness compares mnc-stage1 output against the Python bootstrap — shows exactly which functions are missing or different.

Every run auto-updates `tests/golden/BENCHMARKS.md` with per-test metrics (source lines, IR lines, IR size, function count, compile time). Commit this file to track regressions over time.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I rules), **MyPy** strict mode
- Target Python 3.11+ (for bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source → Lark LALR parser → AST (dataclasses) → Semantic checker → MIR lowering → MIR optimizer (O0-O3) → Emitter
                                                                                                                 ├→ emit_python.py     → Python source (DEPRECATED)
                                                                                                                 ├→ emit_python_mir.py → Python source (DEPRECATED)
                                                                                                                 ├→ emit_llvm.py       → LLVM IR (AST-based)
                                                                                                                 ├→ emit_llvm_mir.py   → LLVM IR (MIR-based, preferred)
                                                                                                                 └→ emit_wasm.py       → WebAssembly (WAT/WASM, v2.0.0)
```

Key modules in `mapanare/`:
- `cli.py` — Entry point, command dispatch (run, build, jit, check, compile, emit-llvm, emit-mir, emit-wasm, fmt, test, lint, doc, deploy, init)
- `parser.py` — Lark transformer: parse tree → AST dataclass nodes
- `ast_nodes.py` — All AST node definitions
- `semantic.py` — Two-pass type checker and scope resolver
- `mir.py` / `mir_builder.py` — MIR data structures and builder
- `lower.py` — AST → MIR lowering (1,397 lines)
- `mir_opt.py` — MIR optimizer passes (constant folding, DCE, copy propagation, block merging)
- `optimizer.py` — AST-level optimizer (constant folding, DCE, agent inlining, stream fusion)
- `emit_python.py` — Python transpiler (DEPRECATED in v2.0.0)
- `emit_python_mir.py` — MIR-based Python transpiler (DEPRECATED in v2.0.0)
- `emit_llvm.py` — LLVM IR generation via llvmlite (AST-based)
- `emit_llvm_mir.py` — LLVM IR generation via llvmlite (MIR-based, preferred for new features)
- `emit_wasm.py` — WebAssembly (WAT) generation from MIR (v2.0.0)
- `wasm_linker.py` — wasm-ld integration for multi-module WASM linking (v2.0.0)
- `types.py` — **Single source of truth** for the type system (TypeKind enum, TypeInfo, builtin registries)
- `mapanare.lark` — LALR grammar with 13-level precedence climbing
- `tracing.py` — OpenTelemetry-compatible tracing
- `diagnostics.py` — Rust-style structured error output
- `test_runner.py` — Built-in test runner for `mapanare test`
- `deploy.py` — Deployment scaffolding (Dockerfile, health checks)

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`, `result.py`, `deploy.py` — asyncio-based agents, reactive signals, async stream operators, Result/Option types, deployment infrastructure. **Legacy — will be replaced by native .mn stdlib.**

**Native C runtime** (`runtime/native/`): Arena-based memory (no GC), lock-free SPSC ring buffers, thread pool with work stealing, cooperative agent scheduler (mobile), agent lifecycle, trace hooks, TCP sockets, TLS (OpenSSL via dlopen), file I/O, event loop (epoll/select), string interning with configurable cap, memory profiling. Used by the LLVM backend.

## LLVM Backend Status (v2.0.0 — full parity + GPU)

**Working:** Functions, structs, enums, pattern matching, control flow, type inference, generics, Result/Option, print (println deprecated), builtins, lists, maps/dicts (Robin Hood hash table), agents (full lifecycle), signals (full reactivity: computed, subscribers, batched updates), streams (map/filter/take/skip/collect/fold, backpressure), closures (free variable capture via environment structs), traits, module imports, pipes (`|>` for function application), pipe definitions (multi-agent composition), all string methods, GPU kernel dispatch (`@gpu`/`@cuda`/`@vulkan` via MIR GpuKernel metadata → PTX/SPIR-V LLVM codegen).

**Not yet on LLVM:** Tensors (experimental, GPU-backed via C runtime but no language-level integration).

New LLVM features should target `emit_llvm_mir.py` (MIR-based emitter), not `emit_llvm.py` (AST-based).

## Type System (mapanare/types.py)

All type definitions, builtin registries, and type-name mappings live in `types.py`:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int, float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare→Python name mapping used by emitters
- `PYTHON_TYPE_MAP`: Type→Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, 9,400+ lines of Mapanare. Mirrors the Python bootstrap pipeline:

| Module | Lines | Role |
|--------|-------|------|
| `ast.mn` | 277 | AST node definitions (structs + enums) + shared constructors |
| `lexer.mn` | 508 | Character-by-character tokenizer |
| `parser.mn` | 1,879 | Recursive descent parser, 13-level precedence |
| `semantic.mn` | 1,617 | Two-pass type checker and scope resolver |
| `mir.mn` | 415 | MIR data structures (types, values, instructions, blocks, module) |
| `lower_state.mn` | 530 | Lowerer state, scope management, lookups, type resolution |
| `lower.mn` | 2,007 | AST → MIR lowering (registration + expression/statement lowering) |
| `emit_llvm_ir.mn` | 258 | LLVM type constants and IR instruction string builders |
| `emit_llvm.mn` | 1,879 | MIR → LLVM IR emitter (state, handlers, module emission) |
| `main.mn` | 79 | Compiler driver |

**Patterns:** Constructor functions (`let r: T = first_field; return r`), state-threading (functions thread state structs), no struct literal syntax in grammar yet.

**Fixed-point verification** blocked by cross-module LLVM compilation (v0.9.0) and enum lowering gaps.

## Key Conventions

- Grammar lives in `mapanare/mapanare.lark` (also bootstrapped copy in `bootstrap/`)
- Emitters detect used features (agents, signals, streams) and import only as needed
- Builtins are dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted compiler sources are in `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Design philosophy: `docs/manifesto.md` | RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Current plan: `docs/roadmap/v2.0.0/PLAN.md`
- Version tracked in `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

Starting with v0.8.0, the project moves toward Python independence:
- **Stdlib in .mn:** New stdlib modules are written in Mapanare (`.mn`), compiled to native code via LLVM. No more Python `.py` stdlib files.
- **C runtime as foundation:** OS-level primitives (sockets, TLS, file I/O) live in the C runtime. Everything above (HTTP, JSON, routing) is pure Mapanare.
- **Test on LLVM:** Every test should run on the LLVM backend, not just Python.
- **Python backend = legacy:** Kept for reference and bootstrapping, but not the target for new features.

## GPU Backend (v2.0.0)

GPU compute via CUDA and Vulkan, loaded dynamically at runtime (no compile-time SDK dependency):
- **C runtime** (`runtime/native/mapanare_gpu.h/.c`): CUDA Driver API + Vulkan compute via dlopen
- **MIR metadata** (`mapanare/mir.py`): `MIRGpuKernel` dataclass with device, PTX/SPIR-V source, grid/block config
- **Lowering** (`mapanare/lower.py`): `@cuda`/`@vulkan`/`@gpu` decorators populate `MIRModule.gpu_kernels`
- **LLVM codegen** (`mapanare/emit_llvm_mir.py`): PTX string embedding + `cuModuleLoadData`/`cuLaunchKernel`, SPIR-V byte embedding + Vulkan pipeline create/dispatch
- **Python layer** (`experimental/gpu.py`): Device detection, kernel dispatch abstractions
- **Stdlib** (`stdlib/gpu/`): `device.mn` (GPU detection), `tensor.mn` (GPU-accelerated tensors), `kernel.mn` (kernel management)
- **Annotations**: `@gpu`, `@cuda`, `@metal`, `@vulkan` on functions for automatic dispatch
- **Built-in kernels**: PTX for CUDA, GLSL/SPIR-V for Vulkan (tensor add/sub/mul/div/matmul)

## WebAssembly Backend (v2.0.0)

Compile Mapanare to WebAssembly for browser and server-side execution:
- **Emitter** (`mapanare/emit_wasm.py`): MIR → WAT text format (~2,785 lines)
- **Linker** (`mapanare/wasm_linker.py`): wasm-ld integration for multi-module linking, memory layout, import/export management
- **CLI**: `mapanare emit-wasm [--binary] [--link] [--wasi] source.mn [source2.mn ...]`
- **Targets**: `wasm32-unknown-unknown` (browser), `wasm32-wasi` (server)
- **JS runtime** (`playground/src/wasm-runtime.js`): Browser host for WASM modules
- **Stdlib** (`stdlib/wasm/`): `bridge.mn` (JS interop), `runtime.mn` (WASI + memory)
- **WASI support**: File I/O, environment, clock, random via WASI preview 1

## Mobile Targets (v2.0.0)

Cross-compilation targets for mobile platforms:
- `aarch64-apple-ios` — iOS ARM64
- `aarch64-linux-android` — Android ARM64
- `x86_64-linux-android` — Android emulator

Mobile-specific runtime features:
- **Cooperative agent scheduler** — single-threaded event-driven execution (default on mobile)
- **epoll event loop** — Linux/Android I/O multiplexing (kqueue on iOS deferred)
- **Smaller defaults** — 4KB arenas, 256-slot ring buffers, 64-slot agent queues, 1ms signal batch
- **String interning cap** — 4K entries on mobile vs 64K on desktop
- **Memory profiling** — `mapanare_memory_stats()` for arena/intern/agent usage tracking

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame/data analysis package (pandas+numpy replacement), written in .mn
- `net/crawl` (web crawler), `security/scan` (vulnerability scanner), `security/fuzz` (fuzzer) — all agents-based
- AI/LLM drivers (`stdlib/ai/`): LLM, embeddings, RAG

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — format check (black) → lint (ruff) → type check (mypy) → tests (pytest). Matrix: Python 3.11, 3.12 on Ubuntu.
- **native** — C runtime tests with plain gcc, AddressSanitizer, ThreadSanitizer.
- **wasm** — WASM cross-compilation: emit WAT, convert to WASM via wat2wasm, run WASI examples on wasmtime.
- **android** — Android cross-compilation: NDK setup, ARM64 + x86_64 `.o` generation, ELF format verification.

4,465+ tests across the full pipeline.

## Skills (slash commands)

These are invocable via `/skill-name` in Claude Code:

| Skill | Description |
|-------|-------------|
| `/golden` | Run the 15/15 golden test suite through mnc-stage1 + llvm-as. Shows delta from last run. |
| `/stage2` | Compile all self-hosted modules through mnc-stage1, validate stage2 IR. Tests self-compilation. |
| `/rebuild` | Full rebuild cycle: concat .mn sources → build mnc-stage1 → run golden tests. |
| `/ir-audit` | Audit LLVM IR for known pathologies (ALLOCA_ALIAS, RET_TYPE_MISMATCH, etc.) with baseline tracking. |
| `/valgrind-map` | Run valgrind on crashing binary, map byte offsets to struct fields automatically. |
| `/bump-version` | Bump version across VERSION, README, CHANGELOG, and all localized docs. |
| `/code-review` | Run a full 7-reviewer panel code review of the codebase. |
| `/create-pr` | Generate PR title and description from the current branch's commits. |
| `/simplify` | Review changed code for reuse, quality, and efficiency, then fix issues found. |
| `/autoresearch` | Autonomous experiment loop — iterative research with automatic follow-up. |
| `/culebra-scan` | Run Culebra v2.0.0 — 49 templates (41 IR + 8 C). Auto-detects .ll vs .c. Autofix, SARIF, triage. |
