# v4.145.0 Baseline — E1 (enum_match)

## enum_match target (20 runs, median)

| Language | Median (ms) | Ratio vs Rust |
|---|---:|---:|
| C (gcc -O2) | 0.130 | 0.46× |
| C (clang -O2) | 0.144 | 0.51× |
| Go | 0.195 | 0.69× |
| **Rust -O** | **0.281** | **1.00×** |
| **Mapanare O2** | **1.327** | **4.72×** |
| Python 3.12 | 76.192 | 271× |

## Full suite (5% rule floor, 20 runs, median)

| Workload | C gcc (ms) | C clang (ms) | Rust (ms) | Go (ms) | Mapanare (ms) | Python (ms) | MN/Rust |
|---|---:|---:|---:|---:|---:|---:|---:|
| fib_recursive | 11.055 | 18.454 | 18.193 | 33.601 | 20.092 | 762.803 | 1.10× |
| quicksort | 0.344 | 0.334 | 0.369 | 0.387 | 2.364 | 79.867 | 6.40× |
| struct_alloc | 0.583 | 0.017 | 0.017 | 0.019 | 1.258 | 203.668 | 74.0× |
| **enum_match** | **0.130** | **0.144** | **0.281** | **0.195** | **1.327** | **76.192** | **4.72×** |
| prime_sieve | 1.950 | 1.733 | 1.750 | 2.010 | 3.227 | 357.466 | 1.84× |
| string_concat | 0.070 | 0.051 | 0.037 | 31.336 | 1.273 | 9.582 | 34.4× |

## Environment

- CPU: WSL2 (Intel/AMD x86_64)
- OS: Linux 5.15.167.4-microsoft-standard-WSL2
- LLVM: 18.1.3 (llvm-as, opt -O2, llc, clang linking)
- Rust: rustc -O
- Mapanare: v4.145.0 (Python bootstrap emit → llvm-as → opt -O2 → llc → clang link)
- Runtime: libmapanare_rt.a (gcc -O2, 8 modules)

## Notes

- Ratio vs Rust **4.72×** is worse than the PLAN's estimated 3.37× — the
  prior number was from v4.124.0/v4.135.0 measurements which may have used
  different methodology (Bn.1 internal-timing vs subprocess-spawn timing).
- `fib_recursive` at 1.10× Rust is excellent — pure CPU calling convention
  is nearly at parity.
- `struct_alloc` and `string_concat` have massive gaps (74× and 34×) but
  those are E4/E5 scope, not E1.
