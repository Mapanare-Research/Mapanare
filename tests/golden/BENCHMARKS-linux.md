# Mapanare Benchmarks - Linux

Generated: 2026-03-22 22:58 UTC  
Version: 1.0.11 (`e7b0dd9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.3s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 432 | `__  .___ ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `        ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 4 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `         v` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 5 | `        ` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 3 | `        ` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `        ` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 3 | `        ` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 4 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 4 | `        ` | PASS |
| **Total** | **119** | **990** | **32.1** | **20** | **62** | **872** | **491** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 75 | 3.3 | 1 | 23 | YES | PASS |
| 02_arithmetic | 101 | 4.0 | 1 | 23 | YES | PASS |
| 03_function | 110 | 4.2 | 2 | 22 | YES | PASS |
| 04_if_else | 100 | 4.0 | 1 | 23 | YES | PASS |
| 05_for_loop | 120 | 4.8 | 1 | 25 | YES | PASS |
| 06_struct | 99 | 4.0 | 1 | 24 | YES | PASS |
| 07_enum_match | 75 | 3.1 | 1 | 24 | YES | PASS |
| 08_list | 104 | 4.6 | 1 | 24 | YES | PASS |
| 09_string_methods | 105 | 4.6 | 1 | 24 | YES | PASS |
| 10_result | 145 | 6.2 | 2 | 24 | YES | PASS |
| 11_closure | 118 | 4.4 | 1 | 23 | YES | PASS |
| 12_while | 100 | 4.0 | 1 | 24 | YES | PASS |
| 13_fib | 155 | 5.6 | 2 | 24 | YES | PASS |
| 14_nested_struct | 99 | 4.0 | 1 | 27 | YES | PASS |
| 15_multifunction | 150 | 5.4 | 3 | 25 | YES | PASS |
| **Total** | | | | **359** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 432 | 23 | 18.7x |
| 02_arithmetic | 5 | 23 | 0.2x |
| 03_function | 4 | 22 | 0.2x |
| 04_if_else | 4 | 23 | 0.2x |
| 05_for_loop | 4 | 25 | 0.2x |
| 06_struct | 4 | 24 | 0.2x |
| 07_enum_match | 5 | 24 | 0.2x |
| 08_list | 5 | 24 | 0.2x |
| 09_string_methods | 3 | 24 | 0.1x |
| 10_result | 5 | 24 | 0.2x |
| 11_closure | 3 | 23 | 0.1x |
| 12_while | 4 | 24 | 0.2x |
| 13_fib | 4 | 24 | 0.2x |
| 14_nested_struct | 4 | 27 | 0.2x |
| 15_multifunction | 4 | 25 | 0.1x |

