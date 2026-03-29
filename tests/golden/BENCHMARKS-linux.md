# Mapanare Benchmarks - Linux

Generated: 2026-03-29 04:04 UTC  
Version: 2.0.1 (`4ffad18`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 566 | `-_-.~__. ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 9 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 7 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 6 | `_       ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 10 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 7 | `        ` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 7 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 6 | `         ^` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 7 | `         ^` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 5 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 6 | `  _     ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 6 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 6 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 5 | `        ` | PASS |
| **Total** | **119** | **990** | **32.0** | **20** | **62** | **872** | **657** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 67 | 3.0 | 1 | 68 | YES | PASS |
| 02_arithmetic | 72 | 3.0 | 1 | 62 | YES | PASS |
| 03_function | 81 | 3.2 | 2 | 66 | YES | PASS |
| 04_if_else | 79 | 3.2 | 1 | 58 | YES | PASS |
| 05_for_loop | 83 | 3.4 | 1 | 58 | YES | PASS |
| 06_struct | 77 | 3.2 | 1 | 58 | YES | PASS |
| 07_enum_match | 69 | 2.9 | 1 | 50 | YES | PASS |
| 08_list | 79 | 3.6 | 1 | 54 | YES | PASS |
| 09_string_methods | 79 | 3.6 | 1 | 50 | YES | PASS |
| 10_result | 99 | 4.0 | 2 | 64 | YES | PASS |
| 11_closure | 77 | 3.1 | 1 | 51 | YES | PASS |
| 12_while | 73 | 3.0 | 1 | 62 | YES | PASS |
| 13_fib | 92 | 3.4 | 2 | 69 | YES | PASS |
| 14_nested_struct | 77 | 3.2 | 1 | 54 | YES | PASS |
| 15_multifunction | 90 | 3.4 | 3 | 62 | YES | PASS |
| **Total** | | | | **884** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 566 | 68 | 8.3x |
| 02_arithmetic | 9 | 62 | 0.1x |
| 03_function | 7 | 66 | 0.1x |
| 04_if_else | 5 | 58 | 0.1x |
| 05_for_loop | 6 | 58 | 0.1x |
| 06_struct | 10 | 58 | 0.2x |
| 07_enum_match | 7 | 50 | 0.1x |
| 08_list | 7 | 54 | 0.1x |
| 09_string_methods | 6 | 50 | 0.1x |
| 10_result | 7 | 64 | 0.1x |
| 11_closure | 5 | 51 | 0.1x |
| 12_while | 6 | 62 | 0.1x |
| 13_fib | 6 | 69 | 0.1x |
| 14_nested_struct | 6 | 54 | 0.1x |
| 15_multifunction | 5 | 62 | 0.1x |

