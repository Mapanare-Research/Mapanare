# Mapanare Benchmarks - Linux

Generated: 2026-03-20 19:14 UTC  
Version: 1.0.11 (`62d075e`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 28 | 1.0 | 1 | 2 | 9 | 446 | ` _       v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `____-___` | PASS |
| 03_function | 8 | 63 | 1.7 | 2 | 4 | 57 | 4 | `        ` | PASS |
| 04_if_else | 8 | 32 | 1.0 | 1 | 4 | 9 | 4 | `.. .....` | PASS |
| 05_for_loop | 7 | 77 | 2.4 | 1 | 5 | 58 | 4 | `   ..* . ^` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `.  ..*..` | PASS |
| 07_enum_match | 13 | 65 | 2.4 | 1 | 5 | 42 | 6 | `     -  ` | PASS |
| 08_list | 5 | 89 | 3.6 | 1 | 2 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 62 | 2.5 | 1 | 2 | 35 | 4 | `         ^` | PASS |
| 10_result | 14 | 141 | 5.7 | 2 | 10 | 132 | 6 | `         ^` | PASS |
| 11_closure | 5 | 54 | 2.0 | 1 | 2 | 33 | 4 | `_*___-__` | PASS |
| 12_while | 7 | 59 | 1.7 | 1 | 5 | 42 | 4 | ` _______` | PASS |
| 13_fib | 10 | 100 | 2.8 | 2 | 7 | 98 | 4 | `_-_*--_- ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | ` ..*....` | PASS |
| 15_multifunction | 12 | 99 | 2.8 | 3 | 6 | 98 | 4 | `_-___-__` | PASS |
| **Total** | **119** | **992** | **33.6** | **20** | **60** | **833** | **507** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 26 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 25 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 26 | YES | PASS |
| 04_if_else | 80 | 3.4 | 1 | 27 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 26 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 25 | YES | PASS |
| 07_enum_match | 67 | 2.7 | 1 | 25 | YES | PASS |
| 08_list | 85 | 3.7 | 1 | 30 | YES | PASS |
| 09_string_methods | 75 | 3.4 | 1 | 26 | YES | PASS |
| 10_result | 91 | 3.7 | 2 | 32 | YES | PASS |
| 11_closure | 74 | 3.0 | 1 | 26 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 26 | YES | PASS |
| 13_fib | 83 | 3.1 | 2 | 31 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 26 | YES | PASS |
| 15_multifunction | 81 | 3.1 | 3 | 26 | YES | PASS |
| **Total** | | | | **403** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 446 | 26 | 17.1x |
| 02_arithmetic | 5 | 25 | 0.2x |
| 03_function | 4 | 26 | 0.2x |
| 04_if_else | 4 | 27 | 0.1x |
| 05_for_loop | 4 | 26 | 0.2x |
| 06_struct | 4 | 25 | 0.2x |
| 07_enum_match | 6 | 25 | 0.2x |
| 08_list | 5 | 30 | 0.2x |
| 09_string_methods | 4 | 26 | 0.1x |
| 10_result | 6 | 32 | 0.2x |
| 11_closure | 4 | 26 | 0.1x |
| 12_while | 4 | 26 | 0.1x |
| 13_fib | 4 | 31 | 0.1x |
| 14_nested_struct | 4 | 26 | 0.2x |
| 15_multifunction | 4 | 26 | 0.2x |

