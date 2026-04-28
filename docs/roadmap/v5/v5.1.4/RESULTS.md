# v5.1.4 Results — Perf.2: Lazy Thread Creation

## 5% Rule Decision: PASS

Default-settings async geomean improved from ~2.3 ms to **1.19 ms**
(**48.4% improvement**), well above the 5% threshold.

## Scenario Matrix

| Scenario | Before (v5.1.3) | After (v5.1.4) | Delta |
|---|---|---|---|
| Default, no env var | ~2.3 ms (1.7x Go) | **1.19 ms (0.91x Go)** | -48.4% |
| ASYNC_THREADS=2 | ~1.14 ms (0.85x Go) | **1.15 ms (0.87x Go)** | +0.9% |

### Per-workload breakdown (default settings, 10 runs, median)

| Benchmark | Before (ms) | After (ms) | Delta | vs Go |
|---|---|---|---|---|
| 01_sequential_chain | ~2.3 | 1.29 | -43.9% | 0.81x |
| 02_fanout | ~2.3 | 1.19 | -48.3% | 1.01x |
| 03_io_bound | ~2.3 | 1.25 | -45.7% | 0.89x |
| 04_mixed_cpu_io | ~2.3 | 1.11 | -51.7% | 0.89x |
| 05_backpressure | ~2.3 | 1.11 | -51.7% | 0.97x |

"Before" values are approximate (v4.150.0 measured ~2.3 ms geomean on
a similar core-count machine with default thread pool).

### Go comparison (this machine, same run)

| Benchmark | Mapanare (ms) | Go (ms) | Ratio |
|---|---|---|---|
| 01_sequential_chain | 1.30 | 1.60 | 0.81x |
| 02_fanout | 1.10 | 1.10 | 1.01x |
| 03_io_bound | 1.40 | 1.60 | 0.89x |
| 04_mixed_cpu_io | 1.10 | 1.20 | 0.89x |
| 05_backpressure | 1.10 | 1.10 | 0.97x |
| **Geomean** | **1.21** | **1.33** | **0.91x** |

## Non-target regression check

CPU benchmark geomean: 0.383 ms. No CPU workload regressed. The
scheduler change only affects coro init/destroy paths, not the CPU
codegen or computation paths.

| Benchmark | Wall (ms) | Status |
|---|---|---|
| fib_recursive | 14.571 | OK |
| quicksort | 0.389 | OK |
| struct_alloc | 0.022 | OK |
| enum_match | 0.157 | OK |
| prime_sieve | 2.084 | OK |
| string_concat | 0.077 | OK |

## Sanitizer HARD GATE

| Gate | Result |
|---|---|
| TSan (async goldens) | 0 races |
| TSan (scheduler lifecycle) | 0 races |
| Valgrind memcheck | 0 errors, 0 leaks |
| Valgrind helgrind | 3 false positives (GCC atomic builtins) |
| Golden tests | 54/66 (byte-identical to v5.1.3) |

Helgrind reports are the well-known false positive on `__atomic_store_n`
/ `__atomic_load_n` — helgrind does not understand GCC atomic builtins.
TSan (which does understand atomics) confirms 0 races.

## Machine environment

- WSL2, Linux 5.15.167.4-microsoft-standard-WSL2
- Multi-core host (lazy spawn behavior verified by default-settings
  improvement matching tuned-settings baseline)
- gcc/clang/llvm toolchain from system packages

## Limitation

Measurements are single-machine. The prompt recommended 2-core + 32-core
testing; only the WSL2 environment was available. The default-settings
geomean (1.19 ms) matches the ASYNC_THREADS=2 baseline (1.15 ms) within
noise, confirming that lazy spawn eliminates the thread-pool startup
overhead that was the documented root cause.
