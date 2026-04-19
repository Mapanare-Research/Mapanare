# Python vs Mapanare-Compiled — Benchmark Results

Median of 10 runs per script.

| Script | Python 3 | Mapanare (native) | Speedup | Output Match |
|--------|----------|-------------------|---------|-------------|
| numerical_compute | 2557 ms | 10.7 ms | 239x | yes |
| collatz_explorer | 30636 ms | 446.8 ms | 69x | yes |
| prime_sieve | 3832 ms | 108.8 ms | 35x | yes |
| fibonacci(40) | 8220 ms | 193.7 ms | 42x | yes |
| primes(500K) | 995 ms | 30.6 ms | 33x | yes |

