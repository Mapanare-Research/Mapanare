---
aliases: [Performance, Speed]
tags: [benchmark]
---

# Benchmarks Overview

## Current Numbers (v4.98.0, -O2, AMD Ryzen 9 7950X)

| Benchmark | Mapanare | Python | Rust | vs Python | vs Rust |
|-----------|----------|--------|------|-----------|---------|
| fib(35) | 19.6ms | 799.7ms | 17.4ms | **41x faster** | 1.1x slower |
| quicksort 10K | 2.0ms | 48.9ms | 1.0ms | **24x faster** | 2.0x slower |
| struct_alloc 100K | 0.6ms | 72.9ms | 0.8ms | **122x faster** | faster |
| enum_match 100K | 2.3ms | 49.6ms | 1.1ms | **22x faster** | 2.1x slower |
| prime_sieve 100K | 3.0ms | 91.0ms | 2.6ms | **30x faster** | 1.2x slower |
| string_concat 10K | 95.2ms | 43.7ms | 0.7ms | 2.2x **slower** | 136x slower |

> [!warning] String concat is the one embarrassment
> 2.2x slower than Python. Fix planned in [[v4.108.0]] via auto-StringBuilder.

> [!missing] Go and C not yet in suite
> Added in [[v4.107.0]]. Full 5-language comparison.

## Position on the Spectrum

```
C (gcc -O2) --> Rust --> Go --> Mapanare --> Python
   fastest                                  slowest
```

Mapanare sits between Go and Python on most benchmarks, within 2x of Rust on compute-heavy work.

## Optimization History

| Arc | Versions | What was added | fib(35) delta |
|-----|----------|----------------|---------------|
| Baseline | v4.82.0 | Measurement only | 19.5ms |
| Arc 11 | v4.83.0-v4.85.0 | nsw/nuw, TBAA, function attrs | **0ms** (no change) |
| Arc 12 | v4.87.0-v4.90.0 | MIR inlining, LICM, escape analysis | TBD |

> [!important] Optimization ROI was ZERO
> Arcs 11-12 added nsw/nuw/TBAA/inlining/LICM. Delta at -O2: zero.
> Investigation in [[v4.109.0]]. Hypothesis: LLVM was already optimizing.

## GPU Performance (RTX 4090)

- Element-wise: 896 GB/s (89% theoretical bandwidth)
- MatMul: 1,297 GFLOPS at 4096x4096
- Reduction: 744.7 GB/s with 105.7x CPU speedup

## Key Files

- `benchmarks/cross_language/` — cross-language suite
- `benchmarks/optimizer/` — optimizer-specific benchmarks
- `benchmarks/async/` — async benchmarks
- `benchmarks/GPU_REPORT.md` — GPU details
- `tests/golden/BENCHMARKS.md` — golden test compile metrics
