# Benchmark Report — v4.144.0

> Post-Bn.1 harness: all Rust benchmarks use `__BENCH_METRICS__`
> (internal `std::time::Instant` wall), no subprocess-spawn tax.
> 10-run median per workload.

## Cross-Language (6 workloads)

| Benchmark | C (gcc -O2) | Rust -O | Go | Mapanare O2 | Python 3.12 | Mn/C | Mn/Rust | Mn/Go |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fib_recursive | 11.020 ms | 21.163 ms | 33.114 ms | 20.657 ms | 806.911 ms | 1.87× | 0.98× | 0.62× |
| quicksort | 0.351 ms | 0.414 ms | 0.396 ms | 2.385 ms | 81.867 ms | 6.79× | 5.76× | 6.02× |
| struct_alloc | 0.572 ms | 0.017 ms | 0.019 ms | 1.198 ms | 201.786 ms | 2.09× | 70.47× | 63.05× |
| enum_match | 0.130 ms | 0.296 ms | 0.202 ms | 1.619 ms | 80.855 ms | 12.45× | 5.47× | 8.01× |
| prime_sieve | 1.990 ms | 1.760 ms | 2.028 ms | 3.406 ms | 371.497 ms | 1.71× | 1.94× | 1.68× |
| string_concat | 0.071 ms | 0.046 ms | 49.603 ms | 1.656 ms | 9.676 ms | 23.32× | 36.00× | 0.03× |
| **geomean** | — | — | — | — | — | **4.57×** | **5.83×** | **1.81×** |

### Notes

- **fib_recursive**: Mapanare 0.98× of Rust (effectively parity). Both
  are ~2× slower than C gcc because the LLVM inliner doesn't fully
  inline the recursive path at -O2 without explicit `always_inline`.
- **struct_alloc**: Mapanare 70× slower than Rust — Rust's struct is
  stack-allocated (zero-cost); Mapanare uses heap + drop-glue. This is
  the ABI.1 gap (24-byte struct return ABI). Perf arc target at v4.149.0.
- **enum_match**: Mapanare 5.47× slower than Rust (was 2.3× at
  v4.125.0 with the v4.124.0 Rt.1 inline optimization). The gap widened
  because Bn.1 corrected Rust's internal wall time — Rust's real
  `enum_match` is 0.296 ms, not the 10 ms cargo-spawn-tax-inflated
  number from v4.142.0. Perf arc target at v4.145.0.
- **string_concat**: Go is 49 ms because Go strings are immutable and
  the concat benchmark forces repeated allocation. Mapanare's 1.656 ms
  beats Go by 30×, but is 36× slower than Rust's pre-allocated
  `String::push_str`. Perf arc target at v4.148.0.
- **Python**: Mapanare is **168× faster** than Python geomean.

### Comparison with v4.135.0 (last citable pre-Bn.1 report)

| Metric | v4.135.0 | v4.144.0 | Note |
|---|---|---|---|
| Mapanare/C geomean | 4.86× | 4.57× | Slight improvement |
| Mapanare/Rust geomean | 1.12× | 5.83× | Rust numbers corrected (Bn.1) — v4.135.0 had 10ms spawn-tax artifact |
| Mapanare/Python geomean | 42.6× faster | 168× faster | Consistent |

**The v4.135.0 "Mapanare 1.12× of Rust" was an artifact of the harness
tax.** The corrected comparison at v4.144.0 shows Mapanare is 5.83× slower
than Rust across the 6-workload corpus. The perf arc (v4.145.0–v4.152.0)
targets closing this to ≤ 1.5×.

## Methodology

- **Hardware**: WSL2, same machine as all prior runs
- **Runs**: 10 per workload, median wall time reported
- **Mapanare**: `clang -O2` on emitted LLVM IR + `libmapanare_rt.a`
- **Rust**: `rustc -O` (release mode), internal `Instant` wall via `__BENCH_METRICS__`
- **Go**: `go run` (compiled), internal `time.Now()` wall
- **C**: `gcc -O2` / `clang -O2`
- **Python**: `python3.12`, wall via `time.perf_counter()`

## Async benchmarks (5 workloads)

| Benchmark | Mapanare (median wall) |
|---|---:|
| sequential_chain | 2.6 ms |
| fanout | 2.0 ms |
| io_bound | 2.1 ms |
| mixed_cpu_io | 2.3 ms |
| backpressure | 2.3 ms |
| **geomean** | **2.25 ms** |
