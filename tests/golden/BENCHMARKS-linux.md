# Mapanare Benchmarks - Linux

Generated: 2026-03-22 16:34 UTC  
Version: 1.0.11 (`bad0594`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 414 | `__   __  v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 4 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `        ` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 5 | `        ` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 3 | `        ` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `         ^` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 4 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 3 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 3 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 3 | `         v` | PASS |
| **Total** | **119** | **990** | **32.0** | **20** | **62** | **872** | **470** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 73 | 3.1 | 1 | 20 | YES | PASS |
| 02_arithmetic | 89 | 3.5 | 1 | 20 | YES | PASS |
| 03_function | 100 | 3.7 | 2 | 19 | YES | PASS |
| 04_if_else | 94 | 3.7 | 1 | 25 | YES | PASS |
| 05_for_loop | 103 | 4.0 | 1 | 22 | YES | PASS |
| 06_struct | 88 | 3.5 | 1 | 25 | YES | PASS |
| 07_enum_match | 76 | 3.1 | 1 | 24 | YES | PASS |
| 08_list | 95 | 4.1 | 1 | 21 | YES | PASS |
| 09_string_methods | 95 | 4.1 | 1 | 21 | YES | PASS |
| 10_result | 131 | 5.4 | 2 | 20 | YES | PASS |
| 11_closure | 107 | 4.0 | 1 | 20 | YES | PASS |
| 12_while | 90 | 3.5 | 1 | 21 | YES | PASS |
| 13_fib | 129 | 4.6 | 2 | 20 | YES | PASS |
| 14_nested_struct | 88 | 3.5 | 1 | 21 | YES | PASS |
| 15_multifunction | 128 | 4.5 | 3 | 21 | YES | PASS |
| **Total** | | | | **320** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 414 | 20 | 20.8x |
| 02_arithmetic | 5 | 20 | 0.2x |
| 03_function | 4 | 19 | 0.2x |
| 04_if_else | 4 | 25 | 0.2x |
| 05_for_loop | 4 | 22 | 0.2x |
| 06_struct | 4 | 25 | 0.2x |
| 07_enum_match | 5 | 24 | 0.2x |
| 08_list | 5 | 21 | 0.2x |
| 09_string_methods | 3 | 21 | 0.2x |
| 10_result | 5 | 20 | 0.2x |
| 11_closure | 4 | 20 | 0.2x |
| 12_while | 3 | 21 | 0.2x |
| 13_fib | 4 | 20 | 0.2x |
| 14_nested_struct | 3 | 21 | 0.2x |
| 15_multifunction | 3 | 21 | 0.2x |

