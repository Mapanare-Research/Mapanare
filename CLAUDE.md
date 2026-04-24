# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases (last 6). Full history at
`docs/roadmap/ROADMAP.md`:

- **v5.4.4** (shipped) — **Own.1 Phase 2 — Move-aware drop-glue
  infrastructure; guard-lift deferred.** Three new `EmitState`
  fields (`str_owned_source`, `list_owned_source`, `boxed_owned_source`)
  parallel to the existing owner lists, carrying the bare SSA source
  name the slot was allocated for; registry 22/22 clean. Python
  mirror: `_local_strings_source` / `_local_boxed_source` /
  `_list_vars_source` lists + `_moved_locals: set[str]`. Lowerer Move
  emission in both `lower.mn` and `lower.py`: `Move(val)` fires after
  every resource-consuming op (list.push, map/list IndexSet,
  StructInit per field, EnumInit per payload, Some / Ok / Err, and
  MapInit literals). Drop-glue helpers rewritten to accept
  `List<String>` of ret-ptrs; `is_moved` check consults the parallel
  source array. Also fixes a latent `emit_fn` flush cap of 65536 that
  silently truncated large functions' drop-glue tail (raised to 1M).
  Guard-lift for `%struct.*` returns was implemented (one-level field
  walk extracting each escaping String/List/ptr) and reverted: the
  ~40 extractvalue lines per `%struct.EmitState`-returning call site
  inflated stage2.ll by 5× and triggered mnc-stage2 runtime segfault
  during lex of mnc_all.mn. v5.4.5+ re-lifts with a size gate.
  62_list_output stays LEAK; baseline unchanged from v5.4.3. Goldens
  54/66, UAF 55/11/0, valgrind 0 new ERRORS — all preserved.
  **Ve.1 regressed:** stage2.ll `llvm-as` OK but mnc-stage2 segfaults
  before stage3 emission (previously crashed on teardown with non-
  empty stage3). Not remediated this release. See
  `docs/roadmap/v5/v5.4.4/`.
- **v5.4.3** (shipped) — **Own.1 Phase 2 — close Rt.03 (loop-
  reassignment leaks).** Adds `EmitState.loop_depth: Int` (19th field,
  Reg.1 gate 24 → 25 clean) with matched push/pop around `for_body` /
  `while_body` / `mapfor_body` label emission in `emit_mir_basic_block`;
  Python `LLVMTextEmitter._loop_depth` + `_emit_fn` reset + push/pop
  around `for bb in fn.blocks` provide parity. `emit_track_string` /
  `_boxed` / `_closure` (self-hosted) + `_track_string` / `_track_boxed`
  / `_track_closure` (Python) prepend a `load {slot_ty}, slot` +
  `@__mn_str_free` / `@free` before the store when `loop_depth > 0`;
  outside loops the emission is byte-identical to v5.4.2. Zero-init in
  the entry-block prelude + null-tolerant runtime free fns make the
  first-iteration free a no-op. Closes Rt.03: 22_string_builder 6 objs
  / 19 B → CLEAN; baseline TSV refreshed; regression back to leaking
  now fails CI. D3 UAF risk (aliased copies + reassignment) did not
  materialize on the current corpus — UAF sweep byte-identical (55
  CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN). Goldens 54/66 preserved;
  valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved; leak sweep 45 CLEAN /
  3 LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 169280 lines (+0.19% vs v5.4.2); `llvm-as`
  OK. `docs/known_issues.md` Rt.03 row flipped to CLOSED. See
  `docs/roadmap/v5/v5.4.3/`.
- **v5.4.2** (shipped) — **Own.1 Phase 2 — ASan leak-detection
  gate.** Flips `detect_leaks=1` across all 66 goldens via new
  `scripts/run_asan_leak_goldens.sh` (compile with `mnc-stage1`, `llc`
  to object, link with `libmapanare_rt.a` under `-fsanitize=address`,
  run under LSan). First sweep revealed 5 leak classes; 2 fixed by
  extending Phase 3.2's tracking hook with `is_string_returning_
  builtin(fn_name)` (13 Mapanare-level builtins whose MIR dest
  defaults to `mir_unknown()` in lower.mn's generic call path — 4
  goldens, 9 objs / 202 B) and adding `emit_track_boxed(ep)` in
  `emit_enum_init`'s boxed-payload branch (1 golden / 16 B).
  Suppressions (`scripts/asan_leak_suppressions.txt`, LSan format via
  `LSAN_OPTIONS`) trim libcuda cuInit; Mesa/Vulkan loader
  (`<unknown module>`) + loop-reassignment + struct-return
  intermediates are baseline-gated in `scripts/check_leak_summary.py`
  with PLAN.md §D3 / §D4 deferrals to v5.4.3. `make leak-check` +
  `.github/workflows/sanitizers.yml` leak-check job ratify the sweep
  as a merge gate. Goldens 54/66 preserved; UAF sweep 55/11
  preserved; valgrind 0 ERRORS preserved; leak sweep 44 CLEAN / 4
  LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 168k lines (+1.8%); `llvm-as` OK. See
  `docs/roadmap/v5/v5.4.2/`.
- **v5.4.1** (shipped) — **Own.1 Phase 2 — make v5.4.0 drop-glue
  actually fire.** Populates v5.4.0's dormant owner lists with the
  shadow-slot architecture ported from Python. Three new `EmitState`
  fields (`entry_prelude_lines`, `entry_block_body`,
  `in_entry_block`) buffer the function body while `emit_track_*`
  can fire from any basic block; prelude flushes into the entry
  block at function close. Owner lists populated at `emit_mir_call`
  dispatch (runtime + user String returns), `emit_binop +` (String
  concat), `emit_interp_concat` (intermediates), `emit_list_init`
  (allocas hoisted + zero-init so they dominate all drop-glue
  loads). Drop-glue revised with per-slot `icmp eq ptr` +
  multi-block branch to skip frees that would alias the returned
  value (scalar String / List / ptr). Aggregate returns (struct /
  enum / Option / Result) conservatively skip all drops — UAF-safe,
  leaks until v5.4.2. Runtime free declarations landed. String
  literals intentionally NOT tracked (Python omits; rodata, is_heap=0
  no-ops, tracking each would explode IR quadratically). Goldens
  54/66; valgrind 0 new ERRORS; ASan 55 CLEAN / 11 CRASH_NO_ASAN
  unchanged; narrow leak test (`greet()`) reports 0 leaks under
  `detect_leaks=1`. stage2.ll 165k lines (+33% vs baseline, within
  R3 budget); stage2 `llvm-as` OK. See `docs/roadmap/v5/v5.4.1/`.
- **v5.4.0** (shipped) — **Own.1 Phase 2 — self-hosted drop-glue
  infrastructure.** Phase 0 baseline revealed all 11 Sh.2 tests
  already pass; release rescoped from "close 11 Sh.2 goldens" to
  "memory-correctness infrastructure, 0 new goldens". Ships: `Move`
  MIR variant (both emitters), four ownership slots in `EmitState`,
  three drop-glue helpers + `emit_drop_glue` dispatcher wired into
  `emit_mir_return`, Python `_do_move` routing to `_move_resource`,
  self-hosted `"move"` kind populating `moved_locals`. Goldens
  54/66 preserved; valgrind + ASan byte-identical to baseline.
  Owner-list population + lowerer Move emission + runtime free
  declarations deferred to v5.4.1. See `docs/roadmap/v5/v5.4.0/`.
- **v5.3.3** (shipped) — **SPEC + docs polish.** Zero compiler
  changes. SPEC §30 Package Management (manifest, install, lock,
  constraints, registry API). SPEC header 4.143.0 → 5.3.3 (27-release
  staleness closed). `examples/signals/counter.mn` signal demo. All
  three Coral LOW carry-forwards closed. Closeout arc complete.
  See `docs/roadmap/v5/v5.3.3/`.
### Planned / in-progress

- **v5.4.5** — **Close Rt.04 + fix Ve.1 regression.** Re-lift the
  `%struct.*` aggregate-return guard with a size gate (skip field
  walk when struct has >N fields, or when the calling function has
  >M tracked slots). Diagnose and remediate the Ve.1 regression
  introduced in v5.4.4 (mnc-stage2 segfault during lex of
  mnc_all.mn).
- **v5.5.0** — **Sh.4 — self-hosted async.** `block_on`/`await` +
  coroutine lowering.
- **v5.6.0** — **Sh.6 — self-hosted tensor.** `Tensor`/`Float` types
  + nested-array literal parser.
- **v5.7.0** — **Sh.7 + or-pattern fix — 66/66.**
- **v5.7.1** — SPEC + docs polish (pre-panel).
- **v5.8.0** — **RE-PANEL** (target 9.7+). Features first, panel last.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline:** 54/66. The 12 gap: Sh.2 (11), Sh.4 (5),
Sh.6 (5), Sh.7 (1), bootstrap-also-fails (1). Closure tracked
across v5.4.0–v5.7.0.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.0.0 — 49 templates (41 IR + 8 C) |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (27160 symbols, 60866 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
