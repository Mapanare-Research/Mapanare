# Mapanare Benchmarks - Linux

Generated: 2026-04-04 04:59 UTC  
Version: 3.0.1 (`97bbf1d`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 605 | `_.-..-.- ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 9 | `       _ ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 7 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 6 | `         ^` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 9 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 7 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 6 | `         ^` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 7 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 6 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 6 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         ^` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 5 | `         ^` | PASS |
| **Total** | **119** | **982** | **30.1** | **20** | **62** | **872** | **696** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 70 | - | FAIL |
| 02_arithmetic | 0 | 0.0 | 0 | 66 | - | FAIL |
| 03_function | 0 | 0.0 | 0 | 63 | - | FAIL |
| 04_if_else | 0 | 0.0 | 0 | 64 | - | FAIL |
| 05_for_loop | 0 | 0.0 | 0 | 60 | - | FAIL |
| 06_struct | 0 | 0.0 | 0 | 55 | - | FAIL |
| 07_enum_match | 0 | 0.0 | 0 | 63 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 65 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 68 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 74 | - | FAIL |
| 11_closure | 0 | 0.0 | 0 | 47 | - | FAIL |
| 12_while | 0 | 0.0 | 0 | 48 | - | FAIL |
| 13_fib | 0 | 0.0 | 0 | 47 | - | FAIL |
| 14_nested_struct | 0 | 0.0 | 0 | 46 | - | FAIL |
| 15_multifunction | 0 | 0.0 | 0 | 47 | - | FAIL |
| **Total** | | | | **884** | **0/15** | **0/15** |

