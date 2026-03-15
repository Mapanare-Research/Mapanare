# Mapanare Benchmarks - Linux

Generated: 2026-03-15 18:15 UTC  
Version: 1.0.0 (`1afd477`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.2s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 25 | 0.8 | 1 | 500 | PASS |
| 02_arithmetic | 4 | 26 | 0.7 | 1 | 5 | PASS |
| 03_function | 8 | 46 | 1.2 | 2 | 6 | PASS |
| 04_if_else | 8 | 29 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 60 | 1.8 | 1 | 5 | PASS |
| 06_struct | 9 | 36 | 1.1 | 1 | 5 | PASS |
| 07_enum_match | 13 | 53 | 1.9 | 1 | 6 | PASS |
| 08_list | 5 | 74 | 2.9 | 1 | 7 | PASS |
| 09_string_methods | 5 | 52 | 2.1 | 1 | 6 | PASS |
| 10_result | 14 | 110 | 4.4 | 2 | 6 | PASS |
| 11_closure | 5 | 46 | 1.7 | 1 | 6 | PASS |
| 12_while | 7 | 46 | 1.3 | 1 | 4 | PASS |
| 13_fib | 10 | 72 | 1.8 | 2 | 4 | PASS |
| 14_nested_struct | 9 | 36 | 1.1 | 1 | 6 | PASS |
| 15_multifunction | 12 | 71 | 1.8 | 3 | 5 | PASS |
| **Total** | **119** | **782** | **25.7** | **20** | **575** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 56 | 2.4 | 1 | 150 | YES | PASS |
| 02_arithmetic | 59 | 2.4 | 1 | 153 | YES | PASS |
| 03_function | 63 | 2.5 | 2 | 171 | YES | PASS |
| 04_if_else | 67 | 2.7 | 1 | 177 | YES | PASS |
| 05_for_loop | 65 | 2.5 | 1 | 157 | YES | PASS |
| 06_struct | 63 | 2.5 | 1 | 135 | YES | PASS |
| 07_enum_match | 0 | 0.0 | 0 | 173 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 164 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 182 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 205 | - | FAIL |
| 11_closure | 66 | 2.5 | 2 | 158 | DIFF | PASS |
| 12_while | 59 | 2.3 | 1 | 140 | YES | PASS |
| 13_fib | 69 | 2.5 | 2 | 197 | YES | PASS |
| 14_nested_struct | 63 | 2.6 | 1 | 179 | YES | PASS |
| 15_multifunction | 71 | 2.7 | 3 | 168 | YES | PASS |
| **Total** | | | | **2510** | **10/15** | **11/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 500 | 150 | 3.3x |
| 02_arithmetic | 5 | 153 | 0.0x |
| 03_function | 6 | 171 | 0.0x |
| 04_if_else | 5 | 177 | 0.0x |
| 05_for_loop | 5 | 157 | 0.0x |
| 06_struct | 5 | 135 | 0.0x |
| 11_closure | 6 | 158 | 0.0x |
| 12_while | 4 | 140 | 0.0x |
| 13_fib | 4 | 197 | 0.0x |
| 14_nested_struct | 6 | 179 | 0.0x |
| 15_multifunction | 5 | 168 | 0.0x |

