# v4.82.0 Session Report — 2026-04-13

## Verdict

- 5 benchmarks, 3 opt levels, 2 cross-language comparisons. All correct.
- Zero IR changes. Pure measurement.
- Mapanare within 1.1-1.6x of Rust on compute workloads.
- String concatenation is 2.7x slower than Python (runtime issue, not IR).

## Benchmark results

| Benchmark | O0 | O1 | O2 | vs Python | vs Rust |
|-----------|----|----|----|-----------|---------| 
| fib_recursive | 57.4ms | 19.6ms | 19.5ms | 41x faster | 1.1x slower |
| quicksort | 2.3ms | 1.8ms | 1.6ms | 26x faster | 1.5x slower |
| matmul_naive | 2.0ms | 1.3ms | 1.3ms | 50x faster | 1.6x slower |
| string_concat | 99.7ms | 102.3ms | 96.1ms | 2.7x slower | 120x slower |
| agent_fanout | 0.6ms | 0.6ms | 0.7ms | 43x faster | 1.4x slower |

## What the baseline reveals

The compiler produces correct, fast code for pure compute. The Rust gap
(1.1-1.6x) is attributable to missing IR metadata:
- No `nsw`/`nuw` on integer arithmetic
- No `inbounds` on GEPs  
- No TBAA metadata for alias analysis
- No function attributes (`nounwind`, `willreturn`)
- Alloca patterns that block mem2reg

The string_concat regression is a runtime allocation issue, not an IR issue.

## Deliverables

| File | Purpose |
|------|---------|
| `benchmarks/optimizer/*.mn` (5) | Benchmark programs |
| `benchmarks/optimizer/run_baseline.py` | Harness |
| `benchmarks/optimizer/*.{py,go,rs}` (15) | Cross-language equivalents |
| `benchmarks/optimizer/v4.82.0-baseline.json` | Raw data |
| `benchmarks/optimizer/BASELINE.md` | Analysis |

## Next session should start with

- v4.83.0: `nsw`/`nuw` flags on integer arithmetic + `inbounds` on GEPs.
  Re-run benchmarks to measure the improvement against v4.82.0 baseline.
