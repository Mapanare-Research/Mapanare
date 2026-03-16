# Mapanare Benchmarks - Linux

Generated: 2026-03-16 17:36 UTC  
Version: 1.0.10 (`0f8fe58`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 25 | 0.8 | 1 | 2 | 9 | 440 | `~_ ._-_* ^` | PASS |
| 02_arithmetic | 4 | 26 | 0.7 | 1 | 2 | 17 | 5 | `*** ***  v` | PASS |
| 03_function | 8 | 46 | 1.2 | 2 | 4 | 57 | 4 | `    *   ` | PASS |
| 04_if_else | 8 | 29 | 0.9 | 1 | 4 | 9 | 4 | `....*...` | PASS |
| 05_for_loop | 7 | 60 | 1.8 | 1 | 5 | 58 | 5 | `  ** *  ` | PASS |
| 06_struct | 9 | 36 | 1.1 | 1 | 2 | 41 | 4 | `      ..` | PASS |
| 07_enum_match | 13 | 53 | 1.9 | 1 | 5 | 38 | 5 | `.   ...  v` | PASS |
| 08_list | 5 | 74 | 2.9 | 1 | 2 | 121 | 5 | `...**...` | PASS |
| 09_string_methods | 5 | 52 | 2.1 | 1 | 2 | 35 | 4 | `********` | PASS |
| 10_result | 14 | 110 | 4.4 | 2 | 10 | 132 | 5 | `  ** **  v` | PASS |
| 11_closure | 5 | 46 | 1.7 | 1 | 2 | 33 | 3 | `********` | PASS |
| 12_while | 7 | 46 | 1.3 | 1 | 5 | 42 | 4 | `..*.*..  v` | PASS |
| 13_fib | 10 | 72 | 1.9 | 2 | 7 | 98 | 5 | `.*....*. v` | PASS |
| 14_nested_struct | 9 | 36 | 1.1 | 1 | 2 | 41 | 5 | `......**` | PASS |
| 15_multifunction | 12 | 71 | 1.8 | 3 | 6 | 98 | 4 | ` .....**` | PASS |
| **Total** | **119** | **782** | **25.7** | **20** | **60** | **829** | **501** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 29 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 30 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 30 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 34 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 33 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 23 | YES | PASS |
| 07_enum_match | 70 | 2.8 | 1 | 27 | YES | PASS |
| 08_list | 86 | 3.8 | 1 | 33 | YES | PASS |
| 09_string_methods | 0 | 0.0 | 0 | 28 | - | FAIL |
| 10_result | 84 | 3.2 | 2 | 34 | YES | PASS |
| 11_closure | 74 | 3.0 | 1 | 33 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 37 | YES | PASS |
| 13_fib | 78 | 3.1 | 2 | 39 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 31 | YES | PASS |
| 15_multifunction | 79 | 3.1 | 3 | 43 | YES | PASS |
| **Total** | | | | **486** | **14/15** | **14/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 440 | 29 | 15.2x |
| 02_arithmetic | 5 | 30 | 0.2x |
| 03_function | 4 | 30 | 0.1x |
| 04_if_else | 4 | 34 | 0.1x |
| 05_for_loop | 5 | 33 | 0.1x |
| 06_struct | 4 | 23 | 0.2x |
| 07_enum_match | 5 | 27 | 0.2x |
| 08_list | 5 | 33 | 0.1x |
| 10_result | 5 | 34 | 0.2x |
| 11_closure | 3 | 33 | 0.1x |
| 12_while | 4 | 37 | 0.1x |
| 13_fib | 5 | 39 | 0.1x |
| 14_nested_struct | 5 | 31 | 0.2x |
| 15_multifunction | 4 | 43 | 0.1x |

