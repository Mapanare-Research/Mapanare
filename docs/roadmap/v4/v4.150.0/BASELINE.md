# v4.150.0 E6 Baseline

## Quality gates (pre-release)

| Gate | Result |
|------|--------|
| ruff check | 0 findings |
| black --check | 353 unchanged |
| mypy mapanare/ runtime/ | 0 issues (53 files) |
| Non-bootstrap pytest | 5288 passed / 0 failed / 115 skipped / 9 xfailed |
| Bootstrap pytest | 212 passed / 13 failed (byte-identical) |
| Native goldens | 54/66 |
| Fixed-point | NEAR FIXED POINT (4 diff lines / 110,127 — version metadata only) |
| Ch.1 TSan canary | 3/3 pass (Plain + ASan + TSan) |
| ASan sweep | 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN |
| Valgrind sweep | 0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS (Ge.1 pre-existing) |
| mnc-stage1 | 3,583,120 bytes (stripped) |
| stage2.ll | 110,127 lines |

## Benchmark baselines

### Async geomean (10-run, cross-language with Go)

| Benchmark | Mapanare (ms) | Go (ms) | Ratio |
|---|---:|---:|---:|
| 01_sequential_chain | 2.3 | 1.3 | 1.77x |
| 02_fanout | 2.2 | 1.3 | 1.69x |
| 03_io_bound | 2.1 | 2.0 | 1.05x |
| 04_mixed_cpu_io | 2.4 | 1.3 | 1.85x |
| 05_backpressure | 2.4 | 1.0 | 2.40x |
| **Geomean** | **2.277** | **1.345** | **1.69x** |

### Cross-language CPU (10-run, Mapanare column)

| Benchmark | Mapanare O2 (ms) |
|---|---:|
| fib_recursive | 15.304 |
| quicksort | 1.167 |
| struct_alloc | 0.025 |
| enum_match | 0.177 |
| prime_sieve | 2.051 |
| string_concat | 0.072 |
| **Geomean** | **0.476** |

### Thread pool noop overhead (32-core machine)

| Threads | Median startup (ms) |
|---:|---:|
| 1 | 0.97 |
| 2 | 1.03 |
| 4 | 1.08 |
| 8 | 1.17 |
| 16 | 1.52 |
| 32 (default) | 2.37 |

Raw data: `benchmarks/async/v4.150.0-baseline.json`,
`benchmarks/cross_language/v4.150.0-baseline.json`.
