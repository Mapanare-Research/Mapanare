# Mapanare Benchmarks - Linux

Generated: 2026-04-02 00:57 UTC  
Version: 2.1.0 (`2d636c6`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 579 | `________ ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 7 | `         ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 6 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 72 | 2.1 | 1 | 5 | 58 | 5 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 08_list | 5 | 77 | 2.6 | 1 | 2 | 113 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 4 | `         ^` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `        ` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 6 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 5 | `         ^` | PASS |
| **Total** | **119** | **981** | **30.1** | **20** | **62** | **872** | **655** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 70 | 3.1 | 1 | 59 | YES | PASS |
| 02_arithmetic | 75 | 3.1 | 1 | 63 | YES | PASS |
| 03_function | 85 | 3.3 | 2 | 68 | YES | PASS |
| 04_if_else | 87 | 3.6 | 1 | 67 | YES | PASS |
| 05_for_loop | 98 | 4.0 | 1 | 71 | YES | PASS |
| 06_struct | 80 | 3.4 | 1 | 56 | YES | PASS |
| 07_enum_match | 90 | 3.8 | 1 | 59 | YES | PASS |
| 08_list | 102 | 4.3 | 1 | 60 | YES | PASS |
| 09_string_methods | 82 | 3.7 | 1 | 57 | YES | PASS |
| 10_result | 126 | 5.2 | 2 | 69 | YES | PASS |
| 11_closure | 88 | 3.4 | 1 | 62 | DIFF | PASS |
| 12_while | 76 | 3.1 | 1 | 64 | YES | PASS |
| 13_fib | 95 | 3.5 | 2 | 68 | YES | PASS |
| 14_nested_struct | 80 | 3.4 | 1 | 67 | YES | PASS |
| 15_multifunction | 93 | 3.5 | 3 | 76 | YES | PASS |
| **Total** | | | | **966** | **14/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 579 | 59 | 9.8x |
| 02_arithmetic | 7 | 63 | 0.1x |
| 03_function | 6 | 68 | 0.1x |
| 04_if_else | 5 | 67 | 0.1x |
| 05_for_loop | 5 | 71 | 0.1x |
| 06_struct | 6 | 56 | 0.1x |
| 07_enum_match | 6 | 59 | 0.1x |
| 08_list | 6 | 60 | 0.1x |
| 09_string_methods | 4 | 57 | 0.1x |
| 10_result | 6 | 69 | 0.1x |
| 11_closure | 6 | 62 | 0.1x |
| 12_while | 5 | 64 | 0.1x |
| 13_fib | 5 | 68 | 0.1x |
| 14_nested_struct | 5 | 67 | 0.1x |
| 15_multifunction | 5 | 76 | 0.1x |

