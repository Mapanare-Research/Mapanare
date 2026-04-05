# Mapanare Benchmarks - Linux

Generated: 2026-04-05 06:32 UTC  
Version: 3.5.0 (`3bb331d`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 559 | `......_. ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `         ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 4 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 5 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `         v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 6 | `         ^` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 6 | `___ ____` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 8 | `______*- v` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 5 | `    _   ` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `___._*_. ^` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 5 | `_   ___  v` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `     _ _ ^` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `.*  .  * ^` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 5 | `_-__*___` | PASS |
| 24_enum_methods | 20 | 0 | 0.0 | 0 | 0 | 0 | 3 | `        ` | FAIL |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | ` ______- ^` | PASS |
| **Total** | **266** | **2115** | **67.6** | **36** | **127** | **1983** | **684** | | **24/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 85 | 3.7 | 1 | 56 | YES | PASS |
| 02_arithmetic | 90 | 3.7 | 1 | 56 | YES | PASS |
| 03_function | 100 | 4.0 | 2 | 50 | YES | PASS |
| 04_if_else | 102 | 4.3 | 1 | 55 | YES | PASS |
| 05_for_loop | 113 | 4.6 | 1 | 64 | YES | PASS |
| 06_struct | 95 | 4.0 | 1 | 62 | YES | PASS |
| 07_enum_match | 107 | 4.5 | 1 | 69 | YES | PASS |
| 08_list | 117 | 5.0 | 1 | 66 | YES | PASS |
| 09_string_methods | 97 | 4.3 | 1 | 49 | YES | PASS |
| 10_result | 142 | 5.9 | 2 | 58 | YES | PASS |
| 11_closure | 103 | 4.1 | 1 | 51 | DIFF | PASS |
| 12_while | 123 | 4.8 | 1 | 64 | YES | PASS |
| 13_fib | 110 | 4.2 | 2 | 67 | YES | PASS |
| 14_nested_struct | 95 | 4.0 | 1 | 88 | YES | PASS |
| 15_multifunction | 108 | 4.1 | 3 | 74 | YES | PASS |
| 16_string_escape | 104 | 4.7 | 1 | 91 | YES | PASS |
| 17_option | 168 | 6.6 | 2 | 97 | YES | PASS |
| 18_method_chain | 114 | 5.1 | 1 | 73 | YES | PASS |
| 19_nested_match | 150 | 5.7 | 2 | 74 | YES | PASS |
| 20_recursion | 111 | 4.2 | 2 | 60 | YES | PASS |
| 21_list_ops | 176 | 7.2 | 2 | 62 | YES | PASS |
| 22_string_builder | 143 | 6.0 | 2 | 65 | YES | PASS |
| 23_multi_return | 126 | 5.1 | 2 | 59 | YES | PASS |
| 25_fizzbuzz | 160 | 6.0 | 2 | 59 | YES | PASS |
| **Total** | | | | **1569** | **23/25** | **24/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 559 | 56 | 9.9x |
| 02_arithmetic | 6 | 56 | 0.1x |
| 03_function | 5 | 50 | 0.1x |
| 04_if_else | 5 | 55 | 0.1x |
| 05_for_loop | 4 | 64 | 0.1x |
| 06_struct | 5 | 62 | 0.1x |
| 07_enum_match | 6 | 69 | 0.1x |
| 08_list | 6 | 66 | 0.1x |
| 09_string_methods | 4 | 49 | 0.1x |
| 10_result | 5 | 58 | 0.1x |
| 11_closure | 4 | 51 | 0.1x |
| 12_while | 4 | 64 | 0.1x |
| 13_fib | 5 | 67 | 0.1x |
| 14_nested_struct | 6 | 88 | 0.1x |
| 15_multifunction | 6 | 74 | 0.1x |
| 16_string_escape | 6 | 91 | 0.1x |
| 17_option | 8 | 97 | 0.1x |
| 18_method_chain | 5 | 73 | 0.1x |
| 19_nested_match | 6 | 74 | 0.1x |
| 20_recursion | 5 | 60 | 0.1x |
| 21_list_ops | 5 | 62 | 0.1x |
| 22_string_builder | 5 | 65 | 0.1x |
| 23_multi_return | 5 | 59 | 0.1x |
| 25_fizzbuzz | 4 | 59 | 0.1x |

