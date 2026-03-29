# Mapanare Benchmarks - Linux

Generated: 2026-03-29 04:52 UTC  
Version: 2.0.1 (`8565fd1`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 561 | `-.~__..  v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `         v` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 5 | `         v` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 6 | `         v` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 5 | `         v` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `         v` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 4 | `         v` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 4 | `_        v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 4 | `        ` | PASS |
| **Total** | **119** | **990** | **32.0** | **20** | **62** | **872** | **627** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 67 | 3.0 | 1 | 41 | YES | PASS |
| 02_arithmetic | 72 | 3.0 | 1 | 44 | YES | PASS |
| 03_function | 81 | 3.2 | 2 | 49 | YES | PASS |
| 04_if_else | 79 | 3.2 | 1 | 58 | YES | PASS |
| 05_for_loop | 83 | 3.4 | 1 | 52 | YES | PASS |
| 06_struct | 77 | 3.2 | 1 | 47 | YES | PASS |
| 07_enum_match | 69 | 2.9 | 1 | 45 | YES | PASS |
| 08_list | 79 | 3.6 | 1 | 49 | YES | PASS |
| 09_string_methods | 79 | 3.6 | 1 | 44 | YES | PASS |
| 10_result | 99 | 4.1 | 2 | 44 | YES | PASS |
| 11_closure | 77 | 3.1 | 1 | 40 | YES | PASS |
| 12_while | 73 | 3.0 | 1 | 40 | YES | PASS |
| 13_fib | 92 | 3.4 | 2 | 41 | YES | PASS |
| 14_nested_struct | 77 | 3.2 | 1 | 43 | YES | PASS |
| 15_multifunction | 90 | 3.4 | 3 | 65 | YES | PASS |
| **Total** | | | | **702** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 561 | 41 | 13.7x |
| 02_arithmetic | 6 | 44 | 0.1x |
| 03_function | 5 | 49 | 0.1x |
| 04_if_else | 5 | 58 | 0.1x |
| 05_for_loop | 4 | 52 | 0.1x |
| 06_struct | 5 | 47 | 0.1x |
| 07_enum_match | 6 | 45 | 0.1x |
| 08_list | 6 | 49 | 0.1x |
| 09_string_methods | 5 | 44 | 0.1x |
| 10_result | 5 | 44 | 0.1x |
| 11_closure | 4 | 40 | 0.1x |
| 12_while | 4 | 40 | 0.1x |
| 13_fib | 4 | 41 | 0.1x |
| 14_nested_struct | 4 | 43 | 0.1x |
| 15_multifunction | 4 | 65 | 0.1x |

