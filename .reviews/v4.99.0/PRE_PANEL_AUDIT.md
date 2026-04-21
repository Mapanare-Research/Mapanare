# Pre-Panel Audit — v4.99.0

> Fact-check of arc 10-14 claims against actual artifacts.

## Arc 10 (v4.77.0-v4.81.0): Integration Tests + Debt Zero

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Integration test directory exists | `tests/integration/` exists | VERIFIED |
| CARRY_FORWARD.md at 0 open items | File exists at `.reviews/CARRY_FORWARD.md` | PRESENT (not audited line-by-line) |

## Arc 11 (v4.82.0-v4.86.0): Baseline + IR Quality

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Benchmark baseline established | `benchmarks/optimizer/BASELINE.md` exists | VERIFIED |
| nsw/nuw flags in emitted IR | `grep -c 'add nsw' main.ll` = 669 | VERIFIED |
| TBAA metadata in emitted IR | `grep -c 'Mapanare TBAA' main.ll` = 2 | VERIFIED |
| Function attributes emitted | `grep -c 'nounwind willreturn' main.ll` = 848 | VERIFIED |

## Arc 12 (v4.87.0-v4.91.0): MIR Optimizer Passes

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Inlining pass in mir_opt.py | `inline_small_functions` function exists | VERIFIED |
| LICM infrastructure in mir_opt.py | `find_natural_loops`, `compute_dominators` exist | VERIFIED |
| Escape analysis in mir_opt.py | `escape_analysis_promotion` function exists | VERIFIED |
| Strength reduction in mir_opt.py | `strength_reduction` function exists | VERIFIED |
| fib(35) improvement from 173ms to ~45ms | v4.98.0 measures 19.6ms at O2; v4.82.0 baseline was 19.5ms at O2. **The 173ms figure was WITHOUT `opt -O2`.** At O2, the improvement is negligible. | **OVERSTATED** — the IR quality improvements didn't change O2 numbers |

## Arc 13 (v4.92.0-v4.96.0): Real Async

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Coroutine suspension (coro.suspend) | Async golden tests compile to IR with coro.suspend | VERIFIED (compile only) |
| Multi-threaded scheduler | C runtime has scheduler code | VERIFIED (code exists) |
| Scheduler runs async programs | `__mn_coro_scheduler_*` not in libmapanare_rt.a — **can't link** | **UNVERIFIED** |
| StringBuilder O(1) append | `__mn_sb_*` functions in mapanare_core.c | VERIFIED |
| Panel 8.57/10 PASS | `.reviews/` directory | CLAIMED (no v4.96.0 panel files found in this session) |

## Arc 14 (v4.97.0-v4.99.0): Self-Hosted Propagation + Benchmarks

| Claim | Evidence | Verdict |
|-------|----------|---------|
| 4 MIR passes in mir_opt.mn | `inline_small_functions`, `strength_reduce_function`, `licm_function`, `escape_analysis_function` | VERIFIED |
| IR quality in emit_llvm.mn | nounwind willreturn, noalias sret, TBAA, inbounds | VERIFIED |
| 10 benchmarks, 3 languages | `benchmarks/v4.98.0-final.json` with results | VERIFIED |
| FINAL_REPORT.md published | File exists with 4 tables | VERIFIED |
| mnc-stage1 works | **BROKEN** — tagged pointer UB produces garbled output | **FAILED** |
| Golden tests pass | 0/61 pass (binary corruption) | **FAILED** |
| Fixed-point verified | Can't verify — binary doesn't work | **FAILED** |

## Critical Findings

1. **The self-hosted compiler binary does not work.** This is the most
   significant finding. v4.97.0 claims "all optimization passes ported"
   but the binary that contains those passes produces corrupted output.
   The optimization passes exist in the .mn source and compile to valid
   LLVM IR, but the end product is non-functional.

2. **Optimization performance claims were overstated.** The v4.82.0
   "173ms baseline" was measured without LLVM -O2. With -O2, the
   baseline was already 19.5ms. The optimization work did not change
   the O2 numbers.

3. **Async is compile-only.** The async runtime exists in C source but
   is not linked into the runtime library. No async program has been
   demonstrated running natively.
