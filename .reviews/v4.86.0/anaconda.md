# Anaconda — Toolchain Review (Arc 11)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

**Benchmark methodology:** Sound. Median-of-5 with warmup, drop highest and lowest, fresh baseline on same hardware session. Verification run confirms stability. Cross-language programs use the same algorithm with the same checksum — apples-to-apples.

**Harness design (run_baseline.py):** Well-structured. Compiles each .mn through the full pipeline (emit-llvm -> llvm-as -> opt -> llc -> link), measures wall-clock time, verifies checksum, records JSON. Supports `--only`, `--cross-language`, `--runs` flags. The harness is the kind of infrastructure that pays dividends across multiple arcs.

**The negative result is itself a finding.** The benchmark infrastructure proved that IR annotations alone don't move the needle when the hot path crosses the FFI boundary. This correctly redirects future optimization effort toward runtime inlining and MIR-level passes.

**Reproducibility:** All JSON files committed. The `run_baseline.py` script can reproduce the measurements on any machine with LLVM 18 + clang.

## Score justification

9/10 — excellent measurement infrastructure and methodology. The honest negative result is more valuable than a false positive. One point reserved because the sub-2ms benchmarks (quicksort, matmul, agent) are in the noise floor and don't provide meaningful signal.
