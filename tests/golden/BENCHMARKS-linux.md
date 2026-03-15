# Mapanare Benchmarks - Linux

Generated: 2026-03-15 22:27 UTC  
Version: 1.0.0 (`4aa1cf5`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.0s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 25 | 0.8 | 1 | 546 | PASS |
| 02_arithmetic | 4 | 26 | 0.7 | 1 | 5 | PASS |
| 03_function | 8 | 46 | 1.2 | 2 | 8 | PASS |
| 04_if_else | 8 | 29 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 60 | 1.8 | 1 | 5 | PASS |
| 06_struct | 9 | 36 | 1.1 | 1 | 6 | PASS |
| 07_enum_match | 13 | 53 | 1.9 | 1 | 7 | PASS |
| 08_list | 5 | 74 | 2.9 | 1 | 6 | PASS |
| 09_string_methods | 5 | 52 | 2.1 | 1 | 5 | PASS |
| 10_result | 14 | 110 | 4.4 | 2 | 6 | PASS |
| 11_closure | 5 | 46 | 1.7 | 1 | 5 | PASS |
| 12_while | 7 | 46 | 1.3 | 1 | 6 | PASS |
| 13_fib | 10 | 72 | 1.8 | 2 | 5 | PASS |
| 14_nested_struct | 9 | 36 | 1.1 | 1 | 5 | PASS |
| 15_multifunction | 12 | 71 | 1.8 | 3 | 5 | PASS |
| **Total** | **119** | **782** | **25.7** | **20** | **626** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 151 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 157 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 153 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 195 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 181 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 128 | YES | PASS |
| 07_enum_match | 70 | 2.8 | 1 | 177 | YES | PASS |
| 08_list | 86 | 3.8 | 1 | 189 | YES | PASS |
| 09_string_methods | 75 | 3.4 | 1 | 137 | YES | PASS |
| 10_result | 84 | 3.2 | 2 | 189 | YES | PASS |
| 11_closure | 74 | 3.0 | 1 | 199 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 153 | YES | PASS |
| 13_fib | 77 | 3.0 | 2 | 150 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 132 | YES | PASS |
| 15_multifunction | 79 | 3.1 | 3 | 13 | YES | PASS |
| **Total** | | | | **2304** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 546 | 151 | 3.6x |
| 02_arithmetic | 5 | 157 | 0.0x |
| 03_function | 8 | 153 | 0.0x |
| 04_if_else | 5 | 195 | 0.0x |
| 05_for_loop | 5 | 181 | 0.0x |
| 06_struct | 6 | 128 | 0.0x |
| 07_enum_match | 7 | 177 | 0.0x |
| 08_list | 6 | 189 | 0.0x |
| 09_string_methods | 5 | 137 | 0.0x |
| 10_result | 6 | 189 | 0.0x |
| 11_closure | 5 | 199 | 0.0x |
| 12_while | 6 | 153 | 0.0x |
| 13_fib | 5 | 150 | 0.0x |
| 14_nested_struct | 5 | 132 | 0.0x |
| 15_multifunction | 5 | 13 | 0.4x |

