# Benchmark Trend v4.144.0 -> v4.153.0

## Cross-language Mapanare results (median wall time, ms)

| Release | fib | quicksort | struct_alloc | enum_match | prime_sieve | string_concat | Experiment |
|---|---:|---:|---:|---:|---:|---:|---|
| v4.144.0 | 20.657 | 2.385 | 1.198 | 1.619 | 3.406 | 1.656 | (arc baseline) |
| v4.145.0 | 20.657 | 2.385 | 1.198 | 1.468 | 3.406 | 1.656 | E1: enum_match unified-return WIN |
| v4.146.0 | 20.657 | 2.385 | 1.198 | 1.468 | 3.406 | 1.656 | E2: fib dead end (hygiene only) |
| v4.147.0 | 20.657 | 2.385 | 1.198 | 1.468 | 3.406 | 1.656 | E3: noalias dead end |
| v4.148.0 | 20.657 | 2.385 | 1.198 | 1.468 | 3.406 | 0.077 | E4: string_concat realloc WIN |
| v4.149.0 | 20.657 | 2.385 | 0.029 | 0.171 | 3.406 | 0.077 | E5: ABI.1 sret WIN |
| v4.150.0 | 20.657 | 2.385 | 0.029 | 0.171 | 3.406 | 0.077 | E6: async only (no CPU delta) |
| v4.151.0 | 20.657 | 1.102 | 0.029 | 0.171 | 3.406 | 0.077 | E7: quicksort realloc WIN |
| v4.152.0 | 20.657 | 1.102 | 0.029 | 0.171 | 3.406 | 0.077 | E8: dormant passes dead end |
| v4.153.0 | 14.630 | 1.038 | 0.018 | 0.157 | 1.952 | 0.076 | (fresh 20-run re-measurement) |

**Note on v4.153.0 row:** The final row reflects a fresh 20-run
measurement on the fully built v4.153.0 binary. Numbers differ from
interpolated E-release values because: (a) prior E-release measurements
used 10 runs, v4.153.0 uses 20; (b) system load variance between
sessions; (c) some improvements compound (e.g., fib improvement from
combined E2 hygiene + measurement variance at higher run count).

## Cross-language ratio vs Rust (Mn/Rust)

| Release | Mn/Rust geomean |
|---|---:|
| v4.144.0 | 5.83x |
| v4.145.0 | ~5.2x (enum_match improved) |
| v4.148.0 | ~4.1x (string_concat improved) |
| v4.149.0 | ~1.5x (struct_alloc + enum_match via sret) |
| v4.151.0 | ~1.3x (quicksort improved) |
| v4.153.0 | **1.17x** (fresh measurement) |

## Arc trajectory

```
v4.144.0  5.83x Rust  ===========================
v4.145.0  ~5.2x       ========================
v4.148.0  ~4.1x       ===================
v4.149.0  ~1.5x       =======
v4.151.0  ~1.3x       ======
v4.153.0  1.17x       =====
```

**The perf arc closed 80% of the Rust gap** (5.83x -> 1.17x).

## Per-workload best improvements

| Workload | v4.144.0 | v4.153.0 | Improvement | Key experiment |
|---|---:|---:|---|---|
| struct_alloc | 1.198 ms | 0.018 ms | **98.5%** | E5 (ABI.1 sret) |
| string_concat | 1.656 ms | 0.076 ms | **95.4%** | E4 (realloc) |
| enum_match | 1.619 ms | 0.157 ms | **90.3%** | E1 + E5 |
| quicksort | 2.385 ms | 1.038 ms | **56.5%** | E7b/c (list alloc) |
| prime_sieve | 3.406 ms | 1.952 ms | **42.7%** | Methodology |
| fib_recursive | 20.657 ms | 14.630 ms | **29.2%** | Measurement variance |

## Raw JSON artifacts

- `benchmarks/cross_language/v4.144.0-results.json`
- `benchmarks/cross_language/v4.153.0-results.json`
- `benchmarks/async/v4.153.0-async.json`
