# Mapanare Benchmarks - Linux

Generated: 2026-03-15 18:10 UTC  
Version: 1.0.0 (`4a86115`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.5s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 24 | 0.8 | 1 | 485 | PASS |
| 02_arithmetic | 4 | 25 | 0.7 | 1 | 6 | PASS |
| 03_function | 8 | 45 | 1.1 | 2 | 6 | PASS |
| 04_if_else | 8 | 28 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 59 | 1.7 | 1 | 5 | PASS |
| 06_struct | 9 | 34 | 1.0 | 1 | 5 | PASS |
| 07_enum_match | 13 | 51 | 1.8 | 1 | 6 | PASS |
| 08_list | 5 | 71 | 2.7 | 1 | 7 | PASS |
| 09_string_methods | 5 | 48 | 1.9 | 1 | 4 | PASS |
| 10_result | 14 | 103 | 4.0 | 2 | 6 | PASS |
| 11_closure | 5 | 44 | 1.6 | 1 | 4 | PASS |
| 12_while | 7 | 45 | 1.2 | 1 | 4 | PASS |
| 13_fib | 10 | 71 | 1.8 | 2 | 5 | PASS |
| 14_nested_struct | 9 | 34 | 1.0 | 1 | 4 | PASS |
| 15_multifunction | 12 | 69 | 1.7 | 3 | 4 | PASS |
| **Total** | **119** | **751** | **23.9** | **20** | **556** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 130 | - | FAIL |
| 02_arithmetic | 59 | 2.4 | 1 | 131 | YES | PASS |
| 03_function | 63 | 2.5 | 2 | 140 | YES | PASS |
| 04_if_else | 67 | 2.7 | 1 | 167 | YES | PASS |
| 05_for_loop | 0 | 0.0 | 0 | 137 | - | FAIL |
| 06_struct | 63 | 2.5 | 1 | 110 | YES | PASS |
| 07_enum_match | 0 | 0.0 | 0 | 114 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 160 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 137 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 56 | - | FAIL |
| 11_closure | 0 | 0.0 | 0 | 66 | - | FAIL |
| 12_while | 0 | 0.0 | 0 | 120 | - | FAIL |
| 13_fib | 69 | 2.5 | 2 | 169 | YES | PASS |
| 14_nested_struct | 63 | 2.6 | 1 | 115 | YES | PASS |
| 15_multifunction | 71 | 2.7 | 3 | 133 | YES | PASS |
| **Total** | | | | **1886** | **7/15** | **7/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 02_arithmetic | 6 | 131 | 0.0x |
| 03_function | 6 | 140 | 0.0x |
| 04_if_else | 5 | 167 | 0.0x |
| 06_struct | 5 | 110 | 0.0x |
| 13_fib | 5 | 169 | 0.0x |
| 14_nested_struct | 4 | 115 | 0.0x |
| 15_multifunction | 4 | 133 | 0.0x |

