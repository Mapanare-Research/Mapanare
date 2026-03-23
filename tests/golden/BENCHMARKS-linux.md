# Mapanare Benchmarks - Linux

Generated: 2026-03-23 00:00 UTC  
Version: 1.0.11 (`aa540c8`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 439 | `___  _ _ ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `         ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 4 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 5 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 4 | `         v` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `        ` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 4 | `        ` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 4 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 4 | `        ` | PASS |
| **Total** | **119** | **990** | **32.1** | **20** | **62** | **872** | **498** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 67 | 3.0 | 1 | 20 | YES | PASS |
| 02_arithmetic | 72 | 3.0 | 1 | 19 | YES | PASS |
| 03_function | 82 | 3.2 | 2 | 18 | YES | PASS |
| 04_if_else | 79 | 3.2 | 1 | 21 | YES | PASS |
| 05_for_loop | 83 | 3.4 | 1 | 20 | YES | PASS |
| 06_struct | 74 | 3.1 | 1 | 21 | YES | PASS |
| 07_enum_match | 69 | 2.9 | 1 | 25 | YES | PASS |
| 08_list | 79 | 3.6 | 1 | 25 | YES | PASS |
| 09_string_methods | 79 | 3.6 | 1 | 21 | YES | PASS |
| 10_result | 101 | 4.1 | 2 | 21 | YES | PASS |
| 11_closure | 78 | 3.1 | 1 | 21 | YES | PASS |
| 12_while | 73 | 3.0 | 1 | 23 | YES | PASS |
| 13_fib | 94 | 3.5 | 2 | 22 | YES | PASS |
| 14_nested_struct | 74 | 3.1 | 1 | 21 | YES | PASS |
| 15_multifunction | 92 | 3.4 | 3 | 18 | YES | PASS |
| **Total** | | | | **317** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 439 | 20 | 22.3x |
| 02_arithmetic | 5 | 19 | 0.3x |
| 03_function | 4 | 18 | 0.2x |
| 04_if_else | 5 | 21 | 0.2x |
| 05_for_loop | 4 | 20 | 0.2x |
| 06_struct | 5 | 21 | 0.2x |
| 07_enum_match | 5 | 25 | 0.2x |
| 08_list | 5 | 25 | 0.2x |
| 09_string_methods | 4 | 21 | 0.2x |
| 10_result | 5 | 21 | 0.2x |
| 11_closure | 4 | 21 | 0.2x |
| 12_while | 4 | 23 | 0.2x |
| 13_fib | 4 | 22 | 0.2x |
| 14_nested_struct | 4 | 21 | 0.2x |
| 15_multifunction | 4 | 18 | 0.2x |

