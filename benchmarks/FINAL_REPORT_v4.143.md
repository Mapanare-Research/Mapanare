# Mapanare v4.142.0 — Benchmark Refresh for the v4.143.0 Panel

> Refreshed 2026-04-16 after the Ge.1 closure release. Canonical raw
> artifacts:
>
> - `benchmarks/cross_language/v4.142.0-results.json`
> - `benchmarks/async/v4.142.0-async.json`
>
> `generate_report.py` currently writes a one-line stub plus
> `docs/benchmarks/index.html`, so this markdown summary is the human
> readable panel artifact.

## TL;DR

- **Cross-language geomean:** Mapanare **5.841 ms**
- **Relative position:** 10.96× slower than C gcc, 19.43× slower than C clang, 5.52× slower than Go, **0.50× of Rust** (about 2.0× faster), and **18.55× faster than Python**
- **Async geomean:** Mapanare **5.817 ms**, **11.98× faster than Python**
- **Correctness:** every reported cross-language and async cell is marked `[ok]` / `OK`

## Cross-language wall time table

| Benchmark | C gcc | C clang | Rust | Go | Mapanare | Python |
|---|---:|---:|---:|---:|---:|---:|
| `fib_recursive` | 9.896 ms | 16.621 ms | 25.176 ms | 30.123 ms | **21.178 ms** | 673.686 ms |
| `quicksort` | 0.317 ms | 0.307 ms | 9.993 ms | 0.326 ms | **4.945 ms** | 71.300 ms |
| `struct_alloc` | 0.534 ms | 0.015 ms | 9.578 ms | 0.017 ms | **3.856 ms** | 181.290 ms |
| `enum_match` | 0.117 ms | 0.131 ms | 10.079 ms | 0.186 ms | **4.043 ms** | 68.024 ms |
| `prime_sieve` | 1.800 ms | 1.637 ms | 10.971 ms | 1.883 ms | **5.894 ms** | 315.200 ms |
| `string_concat` | 0.065 ms | 0.045 ms | 9.973 ms | 24.044 ms | **4.128 ms** | 8.660 ms |

### Cross-language geomean

| Language | Geomean |
|---|---:|
| C gcc | 0.533 ms |
| C clang | 0.301 ms |
| Rust | 11.769 ms |
| Go | 1.058 ms |
| **Mapanare** | **5.841 ms** |
| Python | 108.338 ms |

## Async wall time table

| Benchmark | Mapanare | Python |
|---|---:|---:|
| `01_sequential_chain` | 5.8 ms | 69.8 ms |
| `02_fanout` | 5.6 ms | 70.3 ms |
| `03_io_bound` | 5.8 ms | 71.5 ms |
| `04_mixed_cpu_io` | 6.2 ms | 68.4 ms |
| `05_backpressure` | 5.7 ms | 68.6 ms |
| **Geomean** | **5.817 ms** | **69.711 ms** |

## Notes for Boa / Mamba

- The cross-language runner still prints a stale `v4.125.0` banner, but
  the raw output file path and JSON payload are the live v4.142.0
  artifacts.
- The async harness emitted Python comparison cells in this refresh; it
  did not populate a live Go comparison table in the v4.142.0 output.
- This release is not a benchmark-optimization arc. The purpose of the
  refresh is a **fresh-number** evidence pack after Ge.1 closure.
