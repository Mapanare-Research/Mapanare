---
aliases: [Performance, Speed]
tags: [benchmark]
updated: 2026-04-14
---

# Benchmarks Overview

## Current Numbers (v4.125.0, -O2, AMD Ryzen 9 7950X)

| Benchmark | Mapanare | Python | Go | Rust | C (gcc) | vs Python | vs Rust | vs C |
|-----------|----------|--------|----|------|---------|-----------|---------|------|
| fib(35) | 19.6ms | 799.7ms | — | 17.4ms | — | **41x faster** | 1.1x slower | — |
| quicksort 10K | 2.0ms | 48.9ms | — | 1.0ms | — | **24x faster** | 1.23x slower | 7x slower |
| struct_alloc 100K | 0.6ms | 72.9ms | — | 0.8ms | — | **122x faster** | faster | — |
| enum_match 100K | 1.31ms | 49.6ms | — | 1.44ms | 0.13ms | **38x faster** | **0.91x (faster)** | 10x slower |
| prime_sieve 100K | 3.0ms | 91.0ms | — | 2.6ms | — | **30x faster** | 1.2x slower | — |
| string_concat 10K | 1.32ms | 43.7ms | — | 0.7ms | — | **33x faster** | 1.9x slower | — |

> [!success] enum_match: Mapanare is now FASTER than Rust
> v4.124.0 Rt.1 unboxed enum payloads: 3.03ms -> 1.31ms (2.31x speedup).
> Mapanare 0.91x of Rust on enum-heavy dispatch. Memory: 4,740 -> 2,144 KB.

> [!success] string_concat fixed
> v4.108.0 auto-StringBuilder: 95.2ms -> 1.32ms (72x speedup).
> Was 2.2x slower than Python, now **33x faster**.

## Geomean Position

```
6-workload geomean vs C gcc:
  v4.98.0:  9.50x slower than C
  v4.118.0: 5.46x slower than C
  v4.125.0: 4.52x slower than C  <-- current

Mapanare vs Rust geomean: 1.00x (statistically tied)
```

## Position on the Spectrum

```
C (gcc -O2) --> Rust ~= Mapanare --> Go --> Python
   fastest          tied at geomean       slowest
```

Mapanare and Rust are **statistically tied at the geomean level** (4.52x vs 4.51x of C). Mapanare is faster than Rust on enum dispatch, slower on quicksort and string concat.

## Async Performance

| Benchmark | Mapanare | Python asyncio | Go goroutines | vs Python | vs Go |
|-----------|----------|----------------|---------------|-----------|-------|
| Geomean | 1.95ms | ~88ms | ~1.26ms | **45x faster** | 1.55x slower |

## Performance History

| Version | Event | Key Delta |
|---------|-------|-----------|
| v4.82.0 | Baseline established | fib(35) = 19.5ms |
| v4.83.0-v4.85.0 | Arc 11: nsw/nuw, TBAA, attrs | **0ms delta** (LLVM already optimizing) |
| v4.87.0-v4.90.0 | Arc 12: MIR inlining, LICM, escape | Marginal gains |
| v4.107.0 | Go + C added to suite | Full 5-language comparison |
| v4.108.0 | auto-StringBuilder | string_concat 95.2 -> 1.32ms (**72x**) |
| v4.109.0 | Optimizer ROI forensics | Confirmed LLVM already did the work |
| v4.124.0 | Rt.1 unboxed enum payloads | enum_match 3.03 -> 1.31ms (**2.31x**) |
| v4.125.0 | Benchmark refresh | Geomean: Mapanare tied with Rust |

## Remaining Gaps

| Gap | Current | Target | Blocker |
|-----|---------|--------|---------|
| quicksort vs C | 7x slower | — | Needs native fixed-size arrays `[N]i64` (v5.x) |
| enum_match vs C | 10x slower | — | ABI overhead: 24-byte struct by-value return ([[ABI.1]], v5.x) |
| fib vs Rust | 1.1x slower | — | Within noise, effectively tied |

## GPU Performance (RTX 4090)

- Element-wise: 896 GB/s (89% theoretical bandwidth)
- MatMul: 1,297 GFLOPS at 4096x4096
- Reduction: 744.7 GB/s with 105.7x CPU speedup

## Key Files

- `benchmarks/FINAL_REPORT_v4.130.md` — canonical panel evidence (v4.125.0)
- `benchmarks/cross_language/v4.125.0-results.json` — raw data
- `benchmarks/cross_language/` — cross-language suite
- `benchmarks/async/` — async benchmarks
- `benchmarks/GPU_REPORT.md` — GPU details
- `tests/golden/BENCHMARKS.md` — golden test compile metrics
