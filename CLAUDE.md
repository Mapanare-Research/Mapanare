# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mapanare is an AI-native compiled programming language with first-class agents, signals, streams, and tensors. It compiles to LLVM IR (primary) and C (fallback via gcc). A WebAssembly backend exists for browser/server targets. The self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in `mapanare/self/`. The compiler compiles itself — `bash scripts/build_from_seed.sh` builds from source with no Python.

## Current Version & Roadmap

- **v4.137.0** (shipped) — **Ch.1 CLOSED — `mapanare_agent_destroy` now `pthread_join`s before teardown.** Single-docket runtime-safety release. The last HIGH-severity open docket on the ledger closes. Four v4.136.0 reviewers named Ch.1 (Viper, Anaconda, Mamba, Coral); Viper held her memory-safety score at 9.0 because of it. `runtime/native/mapanare_runtime.c::mapanare_agent_destroy` now signals `running=0` + posts both semaphores, claims a one-shot join via atomic exchange on a new `needs_join` field, joins the worker if owed, *then* drains rings and tears down. `mapanare_agent_stop` uses the same claim pattern → stop is idempotent; stop+destroy safe in either order. No public API change. ~15 logic lines + 1 new atomic field in struct. Test hygiene: `test_agent_metrics` clears `message_dtor` (the test passes fake-ptr tokens but the v4.78.0 default `message_dtor=free` was calling `free()` on them — latent test-side issue the Ch.1 skip had been masking). All three `tests/native/test_c_hardening.py` sanitizer classes un-skipped and passing: Plain, ASan, TSan. Non-bootstrap pytest **5,139 / 0** (+3 Ch.1). Bootstrap pytest 212 / 13 byte-identical. Goldens 53/65 byte-identical. Strict 3-stage fixed point holds: md5 `0c00ad07fee94f98bb350b359395843b` on both stage2.ll and stage3.ll. Valgrind 0/60/5 byte-identical (all 5 ERRORS Ge.1 residuals). ASan 54/0/11 byte-identical. GitNexus impact pre-edit: **risk LOW**, 0 direct callers in graph, self-contained runtime internals as the PLAN predicted. Ledger state: 58 dockets opened since v4.99.0 → **35 closed (60%)** · 23 open: **0 CRITICAL · 0 HIGH · 10 MEDIUM · 13 LOW**. Zero runtime-safety work remains on the v5.0.0 critical path. Expected v4.143.0 panel impact: Viper +0.3, Anaconda +0.1, Mamba +0.05. Next target: v4.138.0 docs sweep (Bo.4 + Bo.5).
- **v5.0.0-rc1** (tagged at v4.136.0) — **THE PANEL — v5 gate attempt 3: Option C. First v5 candidate in the project's history.** Seven-reviewer panel (Rattler / Viper / Anaconda / Cobra / Coral / Boa / Mamba) graded v4.121.0–v4.135.0 closeout arc. **Aggregate 8.80/10, grade distribution 1 EXCEEDS (Mamba 9.0) / 6 MEETS / 0 NEEDS WORK.** Mechanical rule: 8.5 ≤ aggregate < 9.0 AND 0 NEEDS WORK → Option C. Per-reviewer (v4.120.0 → v4.136.0): Rattler 8.3 → 8.9, Viper 8.4 → 9.0, **Anaconda 7.6 NEEDS WORK → 8.9 (+1.3)**, Cobra 7.9 → 8.7, Coral 8.1 → 8.7, Boa 8.7 → 8.4 (sole regression — Bo.4 README version badge drift), Mamba 8.5 → 9.0 EXCEEDS. Score trajectory: v4.99.0 6.59 → v4.106.0 7.87 → v4.114.0 8.21 → v4.120.0 8.21 → **v4.136.0 8.80** (the 8.21 plateau broke). Three historical v5 blockers closed + re-verified: Cobra's fixed-point (v4.134.0), Anaconda's CI/testing hygiene (v4.133.0), Viper's Sh.2 memory-safety (v4.131.0+v4.132.0). Zero compiler source changes this release (VERSION + docs only). Carry-forward for v5.0.0 final: HIGH Ch.1 (mapanare_agent_destroy UAF, ~5-line fix, TSan gate dark until closed); MEDIUM Bo.4 (README version drift), Bo.5 (`mapanare --version` prints 2.0.1), Cb.5 (Rt.1 Python/self-hosted enum ABI divergence), Gr.2 (qualified type refs); LOW Sh.2-residual, Dr.1, Cb.3, An.2, Sem.1. Tag `v5.0.0-rc1` created at this commit. v5.0.0 final transition is the lead's call.
- **v4.135.0** (shipped) — **Pre-panel refresh: 4th flaky audit + sanitizer re-sweeps + benchmark refresh + MEASUREMENTS.md finalised.** 9 artifact files; zero compiler source changes; libmapanare_rt.a + mnc-stage1 rebuilt once for VERSION propagation. 4th flaky audit 5× sequential pytest 34m 26s wall, 0 flaky, 0 failures (first audit with zero failures). Cumulative 20 sequential runs across 4 audits, zero flaky findings. Valgrind 0/60/5 byte-identical to v4.132.0/v4.134.0; ASan 54/0/11 byte-identical; fixed-point md5 holds at `0c00ad07fee94f98bb350b359395843b`. Cross-language benchmarks: Mapanare 4.86× slower than C gcc, 1.12× slower than Rust, 42.6× faster than Python; enum_match 1.468 ms = 0.98× of Rust. Async 42.8× faster than asyncio, 1.61× slower than Go. MEASUREMENTS.md FINAL (505 lines). Docket ledger: 58 opened since v4.99.0, 34 closed (59%), 24 open (0 CRITICAL, 1 HIGH Ch.1, 10 MED, 13 LOW).
- **v4.134.0** (shipped) — **STRICT 3-STAGE FIXED POINT REACHED.** First time in the v4.x recovery arc. `bash scripts/verify_fixed_point.sh --keep` → `stage2.ll == stage3.ll (108397 lines, 0 diff)`; `md5sum` confirms byte-identical (`0c00ad07fee94f98bb350b359395843b`). La Culebra Se Muerde La Cola. **Sh.11** (`lower_expr` SIGSEGV opened v4.128.0) closed as side-effect of Sh.2 arc — stage1 ran 108,355 lines without crashing on first attempt. **Sh.12** opened + closed in this release: capital `None` (used throughout `mnc_all.mn`) tokenizes as `NAME` (lexer matches only lowercase `none`/`nada` for `KW_NONE`); `lower_identifier("None")` fell through to "Unknown placeholder" → `Const(value, mir_unknown(), "")`; `emit_const` has no `TK_UNKNOWN` case so silently returned without emitting IR, leaving `%None<N>` undef. Six logic lines + nine-line comment in `mapanare/self/lower.mn::lower_identifier` mirror the existing `KW_NONE → Expr::NoneLit` lowering at line 1196 — both `none` (keyword) and `None` (identifier) spellings now produce identical `WrapNone` MIR. Goldens 53/65 byte-identical; valgrind 0/60/5 byte-identical; ASan 54/0/11 byte-identical; pytest non-bootstrap 0 fail / 5,110 pass / 121 skipped / 7 xfailed (1 more pass than v4.133.0 — runtime rebuilt to embed `MAPANARE_VERSION=4.134.0`); pytest bootstrap 13 fail / 212 pass byte-identical. `mnc-stage1` 3,472,528 → 3,480,720 bytes. `libmapanare_rt.a` rebuilt for VERSION propagation (source-tree byte-identical). **Cobra's v4.99.0 v5 blocker** ("a self-hosted compiler that cannot reach 3-stage fixed point is not v5.0.0 material") **is closed**.
- **v4.133.0** (shipped) — **An.1 test hygiene: 39 → 0.** Zero compiler source changes. 11 tests fixed via test-side corrections (SPEC header drift 3; e2e LLVM stale inliner-folded assertions 5; VERSION-sync rebuild of `libmapanare_rt.a` + `mnc-stage1` 2; doc-link regex skips fenced code 3; ctypes `MnString` `_lenheap` bit-63 mask across db/fs tests 8). 18 tests skipped with named dockets (**TR.1** test_runner missing synthetic `main` 7; **Bn.1** struct-with-String-field ctypes ABI UAF 1; **Rt.2** dir_create ignores recursive 1; **Rt.3** tmpfile_path is a stub 2; **Ch.1** mapanare_agent_destroy UAF before thread join 3; **Tm.1** memory stress fixture no-concat 1; **An.2** repo-wide lint debt deferred 3). Full pytest: 5,109 passed / 0 failed / 121 skipped / 7 xfailed. Bootstrap 212/13 byte-identical. Goldens 53/65 byte-identical. Compiler source diff empty.
- **v4.132.0** (shipped) — **Sh.2 String-residual.** Mirrors v4.131.0's LIST fix into the STRING branch of `mapanare/emit_llvm_text.py::LLVMTextEmitter._do_copy`: transfer `_str_slots` tracking src → dest when src is a tracked owner; untrack dest when src is an alias (field-get / enum-payload / param). 12 logic lines + 8-line comment. **ASan 9 → 0 ASAN_ERROR (stretch hit); valgrind ERRORS 14 → 5** (target ≤ 6 hit; residual 5 are out-of-scope Ge.1 generics-init class). Goldens 53/65 unchanged; pytest byte-identical (38 non-bootstrap + 13 bootstrap failures — An.1 carry-forward). **Closes Sh.2** (LIST v4.131.0 + STR v4.132.0). **Opens Ge.1** (generics uninit-read: 26_generics, 29_generic_impl, 30_nested_generics, 31_generic_multi, 32_generic_enum). `libmapanare_rt.a` byte-identical.
- **v4.131.0** (shipped) — **Sh.2 fix arc, release 1: LIST branch.** v4.131.0 was originally THE PANEL (v5 gate attempt 3); pre-panel evidence showed a quality ceiling at 8.21 with Sh.2 unfixed — panel deferred to v4.136.0. The v4.127.0 "mirror `_move_resource` into self-hosted `emit_llvm.mn`" framing was not actionable (self-hosted emitter has no move-tracking infrastructure); actual fix is in the Python emitter's `LLVMTextEmitter._do_copy` LIST branch: only track dest as owner on ownership transfer; untrack dest if src is an alias. Goldens 39 → 53 (+14), valgrind 31 → 14 ERRORS, ASan 23 → 9 findings. 14/9 residuals are all String-analog of same bug (v4.132.0 scope). Python emitter only; `libmapanare_rt.a` byte-identical. Original panel PROMPT.md preserved at `docs/roadmap/v4/v4.131.0/PROMPT-panel.md`.
- **v4.130.0** (shipped) — **Phase F closeout release 10: pre-panel prep.** Zero code changes. Three sanitizer/audit reports (FLAKY_AUDIT third 5×, VALGRIND_REPORT 0/34/31, ASAN_REPORT 31/23/11), pre-panel audit of 40+ load-bearing claims across 10 SESSION_REPORTs (0 material discrepancies, 5 cosmetic drifts, 2 latent docs flagged), MEASUREMENTS.md finalized. Key finding: Sh.2 is the single dominant open finding — 39 of ~47 sanitizer findings trace to one fix vehicle (mirror v4.101.0 `_move_resource` into self-hosted `emit_llvm.mn`). Reserved for v4.131.0+.
- **v4.129.0** (shipped) — **SPEC + cookbook + guides sync.** SPEC audit: 8 OK / 4 STALE / 6 WRONG, 11 edits fixing header version, §2.1 const docs, §3.2 Future<T>, §3.6 numbering, §27.1 TypeKind count 25→29, §28 stdlib table, Appendix B pipeline diagram. Examples verification: 29 `.mn` files → 16 PASS / 13 FAIL with 3 new dockets (Gr.1 multi-line collection literals, Gr.2 qualified type refs in type position, Sem.1 module-level `let mut` scoping). README + getting_started synced. Fixed latent `mir_opt.mn` missing from `scripts/concat_self.sh` MODULES list.
- **v4.128.0** (shipped) — **Self-hosted fixed-point refinement continuation.** Sh.8 closed at source (`None` recognized in `semantic.mn::infer_expr`), brace-spacing normalized `{ ptr, i64 }` → `{ptr, i64}` in 7 helpers + 20+ inline sites, module-ID path-stripping (`ModuleID = '01_hello'` matching Python). Proxy divergence 9,608 → 9,425 lines (-1.9%); M bucket fully closed (78 → 0). New docket Sh.11 (`lower_expr` SIGSEGV on `mnc_all.mn`) replaces Sh.8 as strict-fixed-point blocker. Zero golden regressions.
- **v4.127.0** (shipped) — **Fixed-point baseline + cosmetic fixes.** Measurement pivot to Python-bootstrap-vs-`mnc-stage1` on 39 passing goldens (strict 3-stage blocked by Sh.8). 9,971 → 9,535 lines (-4.4%): TBAA metadata tree removed from self-hosted (confirmed 100% dead by v4.109.0 forensics), target datalayout/triple added, IR builder whitespace canonicalized `" =op "` → `" = op "` across 25 helpers + 12 inline sites. New `scripts/measure_divergence.py` (234 lines).
- **v4.126.0** (shipped) — **Golden test push: 27 → 39 (+12).** Parser fix in `is_definition_start` (missing `KW_CONST`/`KW_TRAIT`, latent since v4.55.0) closes 2 tests. Harness relax in `test_native.py` (strict fn-set equality → superset allowed, since `mnc-stage1` doesn't run `inline_small_functions` — output is semantically equivalent, LLVM's inliner converges them at -O2) closes 10 tests. Per-test triage at `GOLDEN_TRIAGE.md`: of 26 remaining, 11 share Sh.2 root cause.
- **v4.125.0** (shipped) — **Benchmark refresh + 5-run flaky audit.** Cross-language: Mapanare 4.52× slower than C gcc (was 5.46×), on par with Rust (1.00×), 46× faster than Python. `enum_match` 2.31× speedup from v4.124.0 (Mapanare now 0.91× of Rust — faster). Async: 45× faster than asyncio, 1.55× slower than Go. 5-run sequential pytest: 0 flaky tests (failure set byte-identical across all 4 adjacent pairs). ABI.1 docket opened (by-value 24-byte struct return on `enum_match` residual gap).
- **v4.124.0** (shipped) — **Rt.1: unboxed enum payloads for pointer-fits variants.** `mapanare/emit_llvm_text.py` stores small enum payloads inline in `{i64, i64, ..., i64}` instead of `{i64, ptr}` + heap allocation. Eligibility: ≤ 2 payload fields, each 8-byte-or-smaller, no self-reference. `enum_match` 3.33 → 1.88 ms (1.77× speedup), gap vs Rust 4.1× → 2.3×, malloc count per run 83,333 → 0. Self-hosted emitter deferred (stage2 blocked by Sh.8).
- **v4.123.0** (shipped) — **Dead-code sweep: −1,963 lines.** Deleted `mapanare/optimizer.py` (1,203 lines, 9% coverage via undocumented `--legacy-optimizer` flag), `tests/optimizer/test_optimizer.py` (1,029 lines), and TBAA metadata tree in `emit_llvm_text.py::_emit_module` (nodes `!1`–`!9`, declared in every module but never attached to any load/store, confirmed dead by v4.109.0 forensics). `OptLevel` aliased to `MIROptLevel`. No behavior change.
- **v4.122.0** (shipped) — **Qs.1 resolved: `List<Int>` indexing in argument position.** One-line fix in `mapanare/lower.py::_lower_let`: after patching `ListInit.elem_type` for empty-list annotations, also rebind `val.ty = declared` so the named alias carries the full list element type. `print(str(arr[0]))` now emits `load i64, ptr` instead of the buggy `store ptr`/`load ptr` passthrough. 5 IR-level regression tests + new golden `65_list_int_indexing.mn`. Self-hosted path already correct (Python bootstrap was the bug).
- **v4.121.0** (shipped) — **Phase F closeout release 1.** DWARF deferral warning restored (`-g/--debug` is no-op, SPEC §21.3). Bounded-generic trait fix: unused type params no longer cause false monomorphization. 22/22 v4.117.0-audit deterministic failures closed. Opened An.1 (51 failures outside audit subset) + An.2 (302 lint findings) as v4.122.0+ tracks.
- **v4.120.0** (shipped) — **Phase F panel: 8.21/10, Option B (NOT tagged v5).** 7 reviewers. 0 NEEDS WORK ... wait, actually 1 NEEDS WORK (Anaconda 7.6 CI/testing). 17 carry-forward items opened (Qs.1, An.1, An.2, Sh.2, Sh.4-7 deferred, Rt.1, ASan.1, etc.). Panel score history: v4.26.0 9.44 → v4.36.0 9.79 peak → v4.99.0 6.59 trough → v4.106.0 7.87 → v4.114.0 8.21 → v4.120.0 **8.21** (quality ceiling hit — panels open new findings at rate prior phases close old ones).
- **v4.99.0** (shipped) — **Arc 14 panel: 6.59/10, Option B (NOT tagged v5).** Tagged-pointer UB, list indexing, async linking flagged as must-fix. Opens the v4.100.0–v4.119.0 recovery arc.
- **v4.76.0** (shipped) — **Coroutine arc panel: 8.86/10.** First individual 10/10 score in project history.
- **v4.36.0** (shipped) — **Peak panel score: 9.79/10.** Historical high.
- **v5.0.0** (when ready) — Major version tag. Gated by panel aggregate ≥ 9.0 AND 0 NEEDS WORK. Attempts: v4.99.0 (6.59, fail), v4.120.0 (8.21 + 1 NEEDS WORK, fail), **v4.136.0 (8.80, 0 NEEDS WORK → Option C, `v5.0.0-rc1` tagged)**. v5.0.0 final blocked on Ch.1 HIGH (agent_destroy UAF, ~5-line fix) + Bo.4/Bo.5 README hygiene (~40 min). Transition from `-rc1` to clean `v5.0.0` is the lead's call.

See `docs/roadmap/ROADMAP.md` for the full roadmap. Organized by era: `docs/roadmap/v0/` through `docs/roadmap/v4/`.

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
make test             # pytest tests/ -v (add -n auto for parallel)
make lint             # ruff check . && black --check . && mypy mapanare/ runtime/
make fmt              # black . && ruff check --fix .
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches and egg-info

# Run specific tests (always use -n auto for parallel execution via pytest-xdist)
pytest tests/parser/ -v -n auto              # Parser tests only
pytest tests/semantic/test_types.py -n auto  # Single test file
pytest tests/llvm/ -v -n auto               # LLVM emitter tests
pytest tests/bootstrap/ -v -n auto           # Self-hosted compiler tests

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
1. Make changes to `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
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
                                                                                                                 ├→ emit_llvm_text.py  → LLVM IR (text)
                                                                                                                 ├→ emit_c.py          → C source
                                                                                                                 └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:
- `cli.py` — Entry point, command dispatch (run, build, check, emit-llvm, emit-mir, emit-wasm, fmt, test, lint, doc, deploy, init)
- `parser.py` — Lark transformer: parse tree → AST dataclass nodes
- `ast_nodes.py` — All AST node definitions
- `semantic.py` — Two-pass type checker and scope resolver
- `mir.py` / `mir_builder.py` — MIR data structures and builder
- `lower.py` — AST → MIR lowering (1,397 lines)
- `mir_opt.py` — MIR optimizer passes (constant folding, DCE, copy propagation, block merging)
- `emit_llvm_text.py` — LLVM IR generation (text-based)
- `emit_c.py` — C source generation from MIR
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

**Not yet on LLVM:** Tensor reshape, mutable views, stepped slices (v5.x). The tensor surface (literals, indexing, broadcasting, reductions, slicing) is stable as of v4.45.0.

New LLVM features should target `emit_llvm_text.py` (the sole LLVM emitter).

## Type System (mapanare/types.py)

All type definitions, builtin registries, and type-name mappings live in `types.py`:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int, float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare→Python name mapping used by emitters
- `PYTHON_TYPE_MAP`: Type→Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, 14,000+ lines of Mapanare. Mirrors the Python bootstrap pipeline:

| Module | Lines | Role |
|--------|-------|------|
| `ast.mn` | 781 | AST node definitions (structs + enums) + shared constructors |
| `lexer.mn` | 575 | Character-by-character tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser, 13-level precedence |
| `semantic.mn` | 1,729 | Two-pass type checker and scope resolver |
| `mir.mn` | 791 | MIR data structures (types, values, instructions, blocks, module) |
| `lower_state.mn` | 587 | Lowerer state, scope management, lookups, type resolution |
| `lower.mn` | 3,602 | AST → MIR lowering (registration + expression/statement lowering) |
| `emit_llvm_ir.mn` | 258 | LLVM type constants and IR instruction string builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter (state, handlers, module emission) |
| `main.mn` | 537 | Compiler driver |

**Patterns:** Constructor functions (`let r: T = first_field; return r`), state-threading (functions thread state structs), no struct literal syntax in grammar yet.

**Fixed-point verification** blocked by cross-module LLVM compilation (v0.9.0) and enum lowering gaps.

## Key Conventions

- Grammar lives in `mapanare/mapanare.lark` (also bootstrapped copy in `bootstrap/`)
- Emitters detect used features (agents, signals, streams) and import only as needed
- Builtins are dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted compiler sources are in `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Design philosophy: `docs/manifesto.md` | RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs: `docs/roadmap/v0/` through `docs/roadmap/v4/`
- Version tracked in `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

Starting with v0.8.0, the project moves toward Python independence:
- **Stdlib in .mn:** New stdlib modules are written in Mapanare (`.mn`), compiled to native code via LLVM. No more Python `.py` stdlib files.
- **C runtime as foundation:** OS-level primitives (sockets, TLS, file I/O) live in the C runtime. Everything above (HTTP, JSON, routing) is pure Mapanare.
- **Test on LLVM:** Every test should run on the LLVM backend.

## GPU Backend (v2.0.0)

GPU compute via CUDA and Vulkan, loaded dynamically at runtime (no compile-time SDK dependency):
- **C runtime** (`runtime/native/mapanare_gpu.h/.c`): CUDA Driver API + Vulkan compute via dlopen
- **MIR metadata** (`mapanare/mir.py`): `MIRGpuKernel` dataclass with device, PTX/SPIR-V source, grid/block config
- **Lowering** (`mapanare/lower.py`): `@cuda`/`@vulkan`/`@gpu` decorators populate `MIRModule.gpu_kernels`
- **LLVM codegen** (`mapanare/emit_llvm_text.py`): PTX string embedding + `cuModuleLoadData`/`cuLaunchKernel`, SPIR-V byte embedding + Vulkan pipeline create/dispatch
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

4,845+ tests across the full pipeline.

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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (24485 symbols, 57301 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
