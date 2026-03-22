# Mapanare Benchmarks - Linux

Generated: 2026-03-22 15:12 UTC  
Version: 1.0.11 (`46690a3`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 443 | `_ ___ __` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 4 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 3 | `        ` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 5 | `         v` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 3 | `         ^` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 5 | `        ` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 3 | `         v` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 3 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 3 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 3 | `        ` | PASS |
| **Total** | **119** | **990** | **32.0** | **20** | **62** | **872** | **498** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 67 | 3.0 | 1 | 20 | YES | PASS |
| 02_arithmetic | 72 | 3.0 | 1 | 20 | YES | PASS |
| 03_function | 78 | 3.1 | 2 | 20 | YES | PASS |
| 04_if_else | 79 | 3.2 | 1 | 19 | YES | PASS |
| 05_for_loop | 83 | 3.4 | 1 | 20 | YES | PASS |
| 06_struct | 73 | 3.0 | 1 | 20 | YES | PASS |
| 07_enum_match | 69 | 2.9 | 1 | 19 | YES | PASS |
| 08_list | 78 | 3.5 | 1 | 19 | YES | PASS |
| 09_string_methods | 78 | 3.5 | 1 | 19 | YES | PASS |
| 10_result | 98 | 4.1 | 2 | 21 | YES | PASS |
| 11_closure | 82 | 3.2 | 1 | 19 | YES | PASS |
| 12_while | 74 | 3.0 | 1 | 18 | YES | PASS |
| 13_fib | 92 | 3.4 | 2 | 19 | YES | PASS |
| 14_nested_struct | 73 | 3.0 | 1 | 19 | YES | PASS |
| 15_multifunction | 90 | 3.4 | 3 | 19 | YES | PASS |
| **Total** | | | | **292** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 443 | 20 | 22.0x |
| 02_arithmetic | 5 | 20 | 0.3x |
| 03_function | 4 | 20 | 0.2x |
| 04_if_else | 3 | 19 | 0.2x |
| 05_for_loop | 4 | 20 | 0.2x |
| 06_struct | 4 | 20 | 0.2x |
| 07_enum_match | 5 | 19 | 0.2x |
| 08_list | 5 | 19 | 0.2x |
| 09_string_methods | 3 | 19 | 0.2x |
| 10_result | 5 | 21 | 0.2x |
| 11_closure | 3 | 19 | 0.2x |
| 12_while | 3 | 18 | 0.2x |
| 13_fib | 4 | 19 | 0.2x |
| 14_nested_struct | 3 | 19 | 0.2x |
| 15_multifunction | 3 | 19 | 0.2x |

