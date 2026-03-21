# Mapanare Benchmarks - Linux

Generated: 2026-03-21 08:56 UTC  
Version: 1.0.11 (`45eed4d`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 490 | `_______  v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `        ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 4 | `        ` | PASS |
| 04_if_else | 8 | 34 | 1.0 | 1 | 4 | 9 | 4 | `        ` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 5 | `        ` | PASS |
| 08_list | 5 | 85 | 3.3 | 1 | 2 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 3 | `         v` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `         v` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 4 | `      *  v` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 4 | `         v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 4 | `         v` | PASS |
| **Total** | **119** | **994** | **32.5** | **20** | **62** | **880** | **547** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 20 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 19 | YES | PASS |
| 03_function | 74 | 3.0 | 2 | 26 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 22 | YES | PASS |
| 05_for_loop | 76 | 3.1 | 1 | 23 | YES | PASS |
| 06_struct | 67 | 2.9 | 1 | 21 | YES | PASS |
| 07_enum_match | 67 | 2.7 | 1 | 20 | YES | PASS |
| 08_list | 85 | 3.7 | 1 | 19 | YES | PASS |
| 09_string_methods | 75 | 3.4 | 1 | 20 | YES | PASS |
| 10_result | 88 | 3.4 | 2 | 19 | YES | PASS |
| 11_closure | 75 | 3.0 | 1 | 20 | DIFF | PASS |
| 12_while | 67 | 2.8 | 1 | 19 | YES | PASS |
| 13_fib | 80 | 3.1 | 2 | 21 | YES | PASS |
| 14_nested_struct | 67 | 2.9 | 1 | 21 | YES | PASS |
| 15_multifunction | 85 | 3.4 | 3 | 19 | YES | PASS |
| **Total** | | | | **310** | **14/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 490 | 20 | 24.4x |
| 02_arithmetic | 5 | 19 | 0.3x |
| 03_function | 4 | 26 | 0.2x |
| 04_if_else | 4 | 22 | 0.2x |
| 05_for_loop | 4 | 23 | 0.2x |
| 06_struct | 4 | 21 | 0.2x |
| 07_enum_match | 5 | 20 | 0.2x |
| 08_list | 5 | 19 | 0.2x |
| 09_string_methods | 3 | 20 | 0.2x |
| 10_result | 5 | 19 | 0.3x |
| 11_closure | 4 | 20 | 0.2x |
| 12_while | 4 | 19 | 0.2x |
| 13_fib | 4 | 21 | 0.2x |
| 14_nested_struct | 4 | 21 | 0.2x |
| 15_multifunction | 4 | 19 | 0.2x |

