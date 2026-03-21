# Mapanare Benchmarks - Linux

Generated: 2026-03-21 01:29 UTC  
Version: 1.0.11 (`8ad7066`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 28 | 1.0 | 1 | 2 | 9 | 457 | `__ _ _._ v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `_-____-_ v` | PASS |
| 03_function | 8 | 63 | 1.7 | 2 | 4 | 57 | 4 | `     _*_ v` | PASS |
| 04_if_else | 8 | 32 | 1.0 | 1 | 4 | 9 | 4 | `.....**. v` | PASS |
| 05_for_loop | 7 | 77 | 2.4 | 1 | 5 | 58 | 4 | `  *. ...` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 5 | ` ... .*  v` | PASS |
| 07_enum_match | 13 | 65 | 2.4 | 1 | 5 | 42 | 6 | `      ~  v` | PASS |
| 08_list | 5 | 89 | 3.6 | 1 | 2 | 121 | 5 | `         v` | PASS |
| 09_string_methods | 5 | 62 | 2.5 | 1 | 2 | 35 | 4 | `        ` | PASS |
| 10_result | 14 | 141 | 5.7 | 2 | 10 | 132 | 6 | `        ` | PASS |
| 11_closure | 5 | 54 | 2.0 | 1 | 2 | 33 | 5 | `_____-__` | PASS |
| 12_while | 7 | 59 | 1.7 | 1 | 5 | 42 | 5 | `________` | PASS |
| 13_fib | 10 | 100 | 2.8 | 2 | 7 | 98 | 5 | `_--__---` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `........` | PASS |
| 15_multifunction | 12 | 99 | 2.8 | 3 | 6 | 98 | 5 | `_____--_ v` | PASS |
| **Total** | **119** | **992** | **33.6** | **20** | **60** | **833** | **524** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 23 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 22 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 21 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 23 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 23 | YES | PASS |
| 06_struct | 67 | 2.9 | 1 | 24 | YES | PASS |
| 07_enum_match | 67 | 2.7 | 1 | 22 | YES | PASS |
| 08_list | 85 | 3.7 | 1 | 25 | YES | PASS |
| 09_string_methods | 75 | 3.4 | 1 | 21 | YES | PASS |
| 10_result | 0 | 0.0 | 0 | 25 | - | FAIL |
| 11_closure | 74 | 3.0 | 1 | 22 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 26 | YES | PASS |
| 13_fib | 77 | 3.0 | 2 | 25 | YES | PASS |
| 14_nested_struct | 67 | 2.9 | 1 | 26 | YES | PASS |
| 15_multifunction | 79 | 3.1 | 3 | 23 | YES | PASS |
| **Total** | | | | **351** | **14/15** | **14/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 457 | 23 | 19.6x |
| 02_arithmetic | 6 | 22 | 0.3x |
| 03_function | 4 | 21 | 0.2x |
| 04_if_else | 4 | 23 | 0.2x |
| 05_for_loop | 4 | 23 | 0.2x |
| 06_struct | 5 | 24 | 0.2x |
| 07_enum_match | 6 | 22 | 0.3x |
| 08_list | 5 | 25 | 0.2x |
| 09_string_methods | 4 | 21 | 0.2x |
| 11_closure | 5 | 22 | 0.2x |
| 12_while | 5 | 26 | 0.2x |
| 13_fib | 5 | 25 | 0.2x |
| 14_nested_struct | 4 | 26 | 0.2x |
| 15_multifunction | 5 | 23 | 0.2x |

