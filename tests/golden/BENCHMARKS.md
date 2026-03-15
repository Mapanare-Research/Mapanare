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

Generated: 2026-03-15 17:00 UTC  
Version: 1.0.0 (`bcdd474`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.7s  

## Bootstrap Compiler (Python)

| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |
|------|-------:|---------:|------:|----:|----------:|--------|
| 01_hello | 3 | 24 | 0.8 | 1 | 547 | PASS |
| 02_arithmetic | 4 | 25 | 0.7 | 1 | 5 | PASS |
| 03_function | 8 | 45 | 1.1 | 2 | 5 | PASS |
| 04_if_else | 8 | 28 | 0.9 | 1 | 6 | PASS |
| 05_for_loop | 7 | 59 | 1.7 | 1 | 4 | PASS |
| 06_struct | 9 | 34 | 1.0 | 1 | 5 | PASS |
| 07_enum_match | 13 | 51 | 1.8 | 1 | 8 | PASS |
| 08_list | 5 | 71 | 2.7 | 1 | 5 | PASS |
| 09_string_methods | 5 | 48 | 1.9 | 1 | 5 | PASS |
| 10_result | 14 | 103 | 4.0 | 2 | 7 | PASS |
| 11_closure | 5 | 44 | 1.6 | 1 | 5 | PASS |
| 12_while | 7 | 45 | 1.2 | 1 | 5 | PASS |
| 13_fib | 10 | 71 | 1.8 | 2 | 4 | PASS |
| 14_nested_struct | 9 | 34 | 1.0 | 1 | 5 | PASS |
| 15_multifunction | 12 | 69 | 1.7 | 3 | 5 | PASS |
| **Total** | **119** | **751** | **23.9** | **20** | **622** | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |
|------|---------:|------:|----:|----------:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 123 | - | FAIL |
| 02_arithmetic | 59 | 2.4 | 1 | 143 | YES | PASS |
| 03_function | 0 | 0.0 | 0 | 150 | - | FAIL |
| 04_if_else | 67 | 2.7 | 1 | 169 | YES | PASS |
| 05_for_loop | 0 | 0.0 | 0 | 130 | - | FAIL |
| 06_struct | 72 | 2.8 | 2 | 157 | DIFF | PASS |
| 07_enum_match | 0 | 0.0 | 0 | 128 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 133 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 149 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 68 | - | FAIL |
| 11_closure | 0 | 0.0 | 0 | 88 | - | FAIL |
| 12_while | 67 | 2.6 | 2 | 162 | DIFF | PASS |
| 13_fib | 68 | 2.5 | 2 | 153 | YES | PASS |
| 14_nested_struct | 72 | 2.8 | 2 | 153 | DIFF | PASS |
| 15_multifunction | 0 | 0.0 | 0 | 130 | - | FAIL |
| **Total** | | | | **2035** | **3/15** | **6/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 02_arithmetic | 5 | 143 | 0.0x |
| 04_if_else | 6 | 169 | 0.0x |
| 06_struct | 5 | 157 | 0.0x |
| 12_while | 5 | 162 | 0.0x |
| 13_fib | 4 | 153 | 0.0x |
| 14_nested_struct | 5 | 153 | 0.0x |

