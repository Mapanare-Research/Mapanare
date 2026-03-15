# Mapanare Benchmarks - Linux

Generated: 2026-03-15 20:47 UTC  
Version: 1.0.0 (`e6575f4`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.5s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 25 | 0.8 | 1 | 540 | PASS |
| 02_arithmetic | 4 | 26 | 0.7 | 1 | 6 | PASS |
| 03_function | 8 | 46 | 1.2 | 2 | 7 | PASS |
| 04_if_else | 8 | 29 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 60 | 1.8 | 1 | 5 | PASS |
| 06_struct | 9 | 36 | 1.1 | 1 | 6 | PASS |
| 07_enum_match | 13 | 53 | 1.9 | 1 | 7 | PASS |
| 08_list | 5 | 74 | 2.9 | 1 | 7 | PASS |
| 09_string_methods | 5 | 52 | 2.1 | 1 | 6 | PASS |
| 10_result | 14 | 110 | 4.4 | 2 | 7 | PASS |
| 11_closure | 5 | 46 | 1.7 | 1 | 5 | PASS |
| 12_while | 7 | 46 | 1.3 | 1 | 5 | PASS |
| 13_fib | 10 | 72 | 1.8 | 2 | 6 | PASS |
| 14_nested_struct | 9 | 36 | 1.1 | 1 | 6 | PASS |
| 15_multifunction | 12 | 71 | 1.8 | 3 | 6 | PASS |
| **Total** | **119** | **782** | **25.7** | **20** | **622** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 201 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 179 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 206 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 214 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 191 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 183 | YES | PASS |
| 07_enum_match | 70 | 2.8 | 1 | 212 | YES | PASS |
| 08_list | 0 | 0.0 | 0 | 184 | - | FAIL |
| 09_string_methods | 75 | 3.4 | 1 | 191 | YES | PASS |
| 10_result | 84 | 3.2 | 2 | 230 | YES | PASS |
| 11_closure | 74 | 3.0 | 1 | 199 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 213 | YES | PASS |
| 13_fib | 77 | 3.0 | 2 | 193 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 6 | YES | PASS |
| 15_multifunction | 79 | 3.1 | 3 | 181 | YES | PASS |
| **Total** | | | | **2782** | **14/15** | **14/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 540 | 201 | 2.7x |
| 02_arithmetic | 6 | 179 | 0.0x |
| 03_function | 7 | 206 | 0.0x |
| 04_if_else | 5 | 214 | 0.0x |
| 05_for_loop | 5 | 191 | 0.0x |
| 06_struct | 6 | 183 | 0.0x |
| 07_enum_match | 7 | 212 | 0.0x |
| 09_string_methods | 6 | 191 | 0.0x |
| 10_result | 7 | 230 | 0.0x |
| 11_closure | 5 | 199 | 0.0x |
| 12_while | 5 | 213 | 0.0x |
| 13_fib | 6 | 193 | 0.0x |
| 14_nested_struct | 6 | 6 | 0.9x |
| 15_multifunction | 6 | 181 | 0.0x |

