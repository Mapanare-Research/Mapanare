# E2 Baseline — v4.146.0 (pre-patch)

## fib_recursive (20 runs)

| Language | Median (ms) | Peak RSS (KB) | Binary (KB) | LOC |
|---|---:|---:|---:|---:|
| C (gcc -O2) | 10.729 | — | 15.8 | 14 |
| C (clang -O2) | 17.981 | — | 15.8 | 14 |
| **Rust -O** | **18.042** | 2304 | 3894.6 | 11 |
| Go | 32.129 | 2484 | 1878.8 | 23 |
| **Mapanare O2** | **20.045** | 2132 | 58.3 | 8 |
| Python 3.12 | 794.478 | 12584 | N/A | 9 |

**Mapanare / Rust = 1.11×** (20.045 / 18.042)

## Full cross-language sweep (20 runs, 5% rule floor)

| Benchmark | C gcc | C clang | Rust | Go | Mapanare | MN/Rust |
|---|---:|---:|---:|---:|---:|---:|
| fib_recursive | 10.729 | 17.981 | 18.042 | 32.129 | 20.045 | 1.11× |
| quicksort | 0.353 | 0.343 | 0.372 | 0.396 | 2.508 | 6.74× |
| struct_alloc | 0.576 | 0.017 | 0.018 | 0.020 | 1.377 | 76.5× |
| enum_match | 0.134 | 0.147 | 0.293 | 0.200 | 1.442 | 4.92× |
| prime_sieve | 2.000 | 1.803 | 1.812 | 2.063 | 3.500 | 1.93× |
| string_concat | 0.072 | 0.051 | 0.041 | 40.904 | 1.463 | 35.7× |

## Methodology note

- Mapanare: external timing via `time.perf_counter()` around `subprocess.run()`
  (includes ~1-3ms subprocess spawn + process startup/shutdown overhead)
- Rust/C/Go/Python: internal timing via `__BENCH_METRICS__` (excludes spawn)
- The `fib_recursive` gap (1.11×) is within the expected subprocess overhead range
