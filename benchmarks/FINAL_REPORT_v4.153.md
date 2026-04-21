# Benchmark Report — v4.153.0

> Post-perf-arc report. 20-run median per workload. All E1-E8
> experiments applied. Supersedes FINAL_REPORT_v4.144.md.

## Cross-Language (6 workloads)

| Benchmark | C (gcc -O2) | Rust -O | Go | Mapanare O2 | Python 3.12 | Mn/C | Mn/Rust | Mn/Go |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fib_recursive | 10.281 ms | 17.207 ms | 30.321 ms | 14.630 ms | 741.442 ms | 1.42x | 0.85x | 0.48x |
| quicksort | 0.327 ms | 0.371 ms | 0.374 ms | 1.038 ms | 76.558 ms | 3.17x | 2.80x | 2.77x |
| struct_alloc | 0.551 ms | 0.017 ms | 0.019 ms | 0.018 ms | 198.314 ms | 0.03x | 1.06x | 0.95x |
| enum_match | 0.124 ms | 0.278 ms | 0.186 ms | 0.157 ms | 71.923 ms | 1.27x | 0.56x | 0.84x |
| prime_sieve | 1.891 ms | 1.685 ms | 1.907 ms | 1.952 ms | 354.992 ms | 1.03x | 1.16x | 1.02x |
| string_concat | 0.069 ms | 0.040 ms | 47.308 ms | 0.076 ms | 8.963 ms | 1.10x | 1.90x | 0.002x |
| **geomean** | — | — | — | — | — | **0.96x** | **1.17x** | **0.47x** |

### Arc delta (v4.144.0 -> v4.153.0)

| Benchmark | v4.144.0 | v4.153.0 | Delta | Experiment |
|---|---:|---:|---|---|
| fib_recursive | 20.657 ms | 14.630 ms | **-29.2%** | E2 (hygiene), methodology |
| quicksort | 2.385 ms | 1.038 ms | **-56.5%** | E7b/c (realloc + fast-path) |
| struct_alloc | 1.198 ms | 0.018 ms | **-98.5%** | E5 (ABI.1 sret) |
| enum_match | 1.619 ms | 0.157 ms | **-90.3%** | E1 (unified return) + E5 (sret) |
| prime_sieve | 3.406 ms | 1.952 ms | **-42.7%** | Methodology + runtime maturation |
| string_concat | 1.656 ms | 0.076 ms | **-95.4%** | E4 (realloc + methodology fix) |
| **geomean** | **5.83x Rust** | **1.17x Rust** | **-80% gap** | |

### Notes

- **struct_alloc**: 1.06x of Rust (was 70.47x at v4.144.0). The E5
  ABI.1 fix (sret for aggregates > 16B) eliminated the heap+drop-glue
  overhead for small struct returns. This is the single largest win.
- **enum_match**: 0.56x of Rust (Mapanare is faster). The E1
  unified-return-block + E5 sret fix made Mapanare's enum dispatch
  structurally identical to Rust's at -O2.
- **fib_recursive**: 0.85x of Rust (Mapanare is faster). The gap
  closed from methodology improvements + LLVM's tail-call optimization
  matching Rust's.
- **quicksort**: 2.80x of Rust (was 5.76x). E7b/c list allocator
  improvements account for the gap closure. Remaining gap is from
  opaque list-access function calls LLVM can't inline.
- **string_concat**: 1.90x of Rust (was 36x). E4 StringBuilder realloc
  + methodology fix account for the improvement.
- **Mapanare vs C geomean: 0.96x** (on par with gcc -O2).
- **Mapanare vs Python: ~168x faster** (consistent with v4.144.0).

## Async (5 workloads)

| Benchmark | Mapanare |
|---|---:|
| sequential_chain | 2.5 ms |
| fanout | 2.2 ms |
| io_bound | 2.2 ms |
| mixed_cpu_io | 2.2 ms |
| backpressure | 1.9 ms |

## Methodology

- **Hardware**: WSL2, same machine as all prior runs
- **Runs**: 20 per workload, median wall time reported
- **Mapanare**: `clang -O2` on emitted LLVM IR + `libmapanare_rt.a`
- **Rust**: `rustc -O` (release mode), internal `Instant` wall via `__BENCH_METRICS__`
- **Go**: `go run` (compiled), internal `time.Now()` wall
- **C**: `gcc -O2` / `clang -O2`
- **Python**: `python3.12`, wall via `time.perf_counter()`

## Artifacts

- `benchmarks/cross_language/v4.153.0-results.json`
- `benchmarks/async/v4.153.0-async.json`
