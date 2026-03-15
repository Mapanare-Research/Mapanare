# Mapanare Compiler Benchmarks

Cross-platform benchmark results. Each platform file is auto-generated
by `python scripts/test_native.py`. Commit both to track regressions.

---

## Windows

Generated: 2026-03-15 07:10 UTC  
Version: 1.0.0 (`793758b`)  
Platform: Windows AMD64, Python 3.11.7  
Total time: 0.5s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 24 | 0.8 | 1 | 490 | PASS |
| 02_arithmetic | 4 | 25 | 0.7 | 1 | 3 | PASS |
| 03_function | 8 | 45 | 1.1 | 2 | 2 | PASS |
| 04_if_else | 8 | 28 | 0.9 | 1 | 2 | PASS |
| 05_for_loop | 7 | 59 | 1.7 | 1 | 2 | PASS |
| 06_struct | 9 | 34 | 1.0 | 1 | 2 | PASS |
| 07_enum_match | 13 | 51 | 1.8 | 1 | 3 | PASS |
| 08_list | 5 | 71 | 2.7 | 1 | 3 | PASS |
| 09_string_methods | 5 | 48 | 1.9 | 1 | 1 | PASS |
| 10_result | 14 | 103 | 4.0 | 2 | 3 | PASS |
| 11_closure | 5 | 44 | 1.6 | 1 | 1 | PASS |
| 12_while | 7 | 45 | 1.2 | 1 | 1 | PASS |
| 13_fib | 10 | 71 | 1.8 | 2 | 1 | PASS |
| 14_nested_struct | 9 | 34 | 1.0 | 1 | 1 | PASS |
| 15_multifunction | 12 | 69 | 1.7 | 3 | 1 | PASS |
| **Total** | **119** | **751** | **23.8** | **20** | **516** | **15/15** |

---

## Linux

Generated: 2026-03-15 21:25 UTC  
Version: 1.0.0 (`4324632`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.3s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 25 | 0.8 | 1 | 526 | PASS |
| 02_arithmetic | 4 | 26 | 0.7 | 1 | 6 | PASS |
| 03_function | 8 | 46 | 1.2 | 2 | 6 | PASS |
| 04_if_else | 8 | 29 | 0.9 | 1 | 5 | PASS |
| 05_for_loop | 7 | 60 | 1.8 | 1 | 6 | PASS |
| 06_struct | 9 | 36 | 1.1 | 1 | 5 | PASS |
| 07_enum_match | 13 | 53 | 1.9 | 1 | 6 | PASS |
| 08_list | 5 | 74 | 2.9 | 1 | 6 | PASS |
| 09_string_methods | 5 | 52 | 2.1 | 1 | 5 | PASS |
| 10_result | 14 | 110 | 4.4 | 2 | 7 | PASS |
| 11_closure | 5 | 46 | 1.7 | 1 | 5 | PASS |
| 12_while | 7 | 46 | 1.3 | 1 | 5 | PASS |
| 13_fib | 10 | 72 | 1.8 | 2 | 6 | PASS |
| 14_nested_struct | 9 | 36 | 1.1 | 1 | 6 | PASS |
| 15_multifunction | 12 | 71 | 1.8 | 3 | 6 | PASS |
| **Total** | **119** | **782** | **25.7** | **20** | **606** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 163 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 196 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 152 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 169 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 194 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 162 | YES | PASS |
| 07_enum_match | 70 | 2.8 | 1 | 171 | YES | PASS |
| 08_list | 0 | 0.0 | 0 | 184 | - | FAIL |
| 09_string_methods | 75 | 3.4 | 1 | 181 | YES | PASS |
| 10_result | 84 | 3.2 | 2 | 181 | YES | PASS |
| 11_closure | 74 | 3.0 | 1 | 180 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 192 | YES | PASS |
| 13_fib | 77 | 3.0 | 2 | 185 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 167 | YES | PASS |
| 15_multifunction | 79 | 3.1 | 3 | 150 | YES | PASS |
| **Total** | | | | **2628** | **14/15** | **14/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 526 | 163 | 3.2x |
| 02_arithmetic | 6 | 196 | 0.0x |
| 03_function | 6 | 152 | 0.0x |
| 04_if_else | 5 | 169 | 0.0x |
| 05_for_loop | 6 | 194 | 0.0x |
| 06_struct | 5 | 162 | 0.0x |
| 07_enum_match | 6 | 171 | 0.0x |
| 09_string_methods | 5 | 181 | 0.0x |
| 10_result | 7 | 181 | 0.0x |
| 11_closure | 5 | 180 | 0.0x |
| 12_while | 5 | 192 | 0.0x |
| 13_fib | 6 | 185 | 0.0x |
| 14_nested_struct | 6 | 167 | 0.0x |
| 15_multifunction | 6 | 150 | 0.0x |

