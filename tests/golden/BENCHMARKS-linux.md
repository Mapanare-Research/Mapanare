# Mapanare Benchmarks - Linux

Generated: 2026-03-15 07:18 UTC  
Version: 1.0.0 (`793758b`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 4.5s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 24 | 0.8 | 1 | 563 | PASS |
| 02_arithmetic | 4 | 25 | 0.7 | 1 | 7 | PASS |
| 03_function | 8 | 45 | 1.1 | 2 | 6 | PASS |
| 04_if_else | 8 | 28 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 59 | 1.7 | 1 | 5 | PASS |
| 06_struct | 9 | 34 | 1.0 | 1 | 5 | PASS |
| 07_enum_match | 13 | 51 | 1.8 | 1 | 6 | PASS |
| 08_list | 5 | 71 | 2.7 | 1 | 6 | PASS |
| 09_string_methods | 5 | 48 | 1.9 | 1 | 5 | PASS |
| 10_result | 14 | 103 | 4.0 | 2 | 7 | PASS |
| 11_closure | 5 | 44 | 1.6 | 1 | 6 | PASS |
| 12_while | 7 | 45 | 1.2 | 1 | 4 | PASS |
| 13_fib | 10 | 71 | 1.8 | 2 | 5 | PASS |
| 14_nested_struct | 9 | 34 | 1.0 | 1 | 5 | PASS |
| 15_multifunction | 12 | 69 | 1.7 | 3 | 5 | PASS |
| **Total** | **119** | **751** | **23.9** | **20** | **639** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 56 | 2.4 | 1 | 278 | YES | PASS |
| 02_arithmetic | 0 | 0.0 | 0 | 264 | - | FAIL |
| 03_function | 63 | 2.5 | 2 | 233 | YES | PASS |
| 04_if_else | 0 | 0.0 | 0 | 257 | - | FAIL |
| 05_for_loop | 0 | 0.0 | 0 | 225 | - | FAIL |
| 06_struct | 72 | 2.8 | 2 | 249 | DIFF | PASS |
| 07_enum_match | 0 | 0.0 | 0 | 261 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 238 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 248 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 268 | - | FAIL |
| 11_closure | 0 | 0.0 | 0 | 268 | - | FAIL |
| 12_while | 0 | 0.0 | 0 | 209 | - | FAIL |
| 13_fib | 69 | 2.5 | 2 | 249 | YES | PASS |
| 14_nested_struct | 72 | 2.8 | 2 | 244 | DIFF | PASS |
| 15_multifunction | 71 | 2.7 | 3 | 239 | YES | PASS |
| **Total** | | | | **3731** | **4/15** | **6/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 563 | 278 | 2.0x |
| 03_function | 6 | 233 | 0.0x |
| 06_struct | 5 | 249 | 0.0x |
| 13_fib | 5 | 249 | 0.0x |
| 14_nested_struct | 5 | 244 | 0.0x |
| 15_multifunction | 5 | 239 | 0.0x |

