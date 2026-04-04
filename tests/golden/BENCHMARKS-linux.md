# Mapanare Benchmarks - Linux

Generated: 2026-04-04 23:34 UTC  
Version: 3.4.0 (`fe9f344`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 555 | `.....~_. ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | ` _      ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 8 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 6 | `        ` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 4 | `         v` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 5 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `___  _  ` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 7 | `*    *  ` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | `***  * * ^` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `* ..   . ^` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 4 | `.*..*  . ^` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | ` . * .  ` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | ` .**.. . ^` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 5 | `.*.. ...` | PASS |
| 24_enum_methods | 20 | 0 | 0.0 | 0 | 0 | 0 | 3 | ` *      ` | FAIL |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 5 | ` *-__ _  v` | PASS |
| **Total** | **266** | **2115** | **67.6** | **36** | **127** | **1983** | **677** | | **24/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 84 | 3.6 | 1 | 50 | YES | PASS |
| 02_arithmetic | 89 | 3.7 | 1 | 53 | YES | PASS |
| 03_function | 99 | 3.9 | 2 | 81 | YES | PASS |
| 04_if_else | 101 | 4.2 | 1 | 69 | YES | PASS |
| 05_for_loop | 112 | 4.5 | 1 | 70 | YES | PASS |
| 06_struct | 94 | 3.9 | 1 | 56 | YES | PASS |
| 07_enum_match | 106 | 4.5 | 1 | 63 | YES | PASS |
| 08_list | 116 | 4.9 | 1 | 57 | YES | PASS |
| 09_string_methods | 96 | 4.3 | 1 | 45 | YES | PASS |
| 10_result | 141 | 5.9 | 2 | 71 | YES | PASS |
| 11_closure | 102 | 4.0 | 1 | 71 | DIFF | PASS |
| 12_while | 122 | 4.8 | 1 | 87 | YES | PASS |
| 13_fib | 109 | 4.1 | 2 | 77 | YES | PASS |
| 14_nested_struct | 94 | 3.9 | 1 | 65 | YES | PASS |
| 15_multifunction | 107 | 4.1 | 3 | 61 | YES | PASS |
| 16_string_escape | 103 | 4.6 | 1 | 72 | YES | PASS |
| 17_option | 167 | 6.5 | 2 | 92 | YES | PASS |
| 18_method_chain | 113 | 5.1 | 1 | 57 | YES | PASS |
| 19_nested_match | 149 | 5.7 | 2 | 57 | YES | PASS |
| 20_recursion | 110 | 4.2 | 2 | 51 | YES | PASS |
| 21_list_ops | 175 | 7.2 | 2 | 58 | YES | PASS |
| 22_string_builder | 142 | 6.0 | 2 | 59 | YES | PASS |
| 23_multi_return | 125 | 5.1 | 2 | 56 | YES | PASS |
| 25_fizzbuzz | 159 | 6.0 | 2 | 69 | YES | PASS |
| **Total** | | | | **1548** | **23/25** | **24/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 555 | 50 | 11.1x |
| 02_arithmetic | 6 | 53 | 0.1x |
| 03_function | 8 | 81 | 0.1x |
| 04_if_else | 6 | 69 | 0.1x |
| 05_for_loop | 4 | 70 | 0.1x |
| 06_struct | 5 | 56 | 0.1x |
| 07_enum_match | 6 | 63 | 0.1x |
| 08_list | 6 | 57 | 0.1x |
| 09_string_methods | 4 | 45 | 0.1x |
| 10_result | 6 | 71 | 0.1x |
| 11_closure | 5 | 71 | 0.1x |
| 12_while | 5 | 87 | 0.1x |
| 13_fib | 5 | 77 | 0.1x |
| 14_nested_struct | 5 | 65 | 0.1x |
| 15_multifunction | 4 | 61 | 0.1x |
| 16_string_escape | 4 | 72 | 0.1x |
| 17_option | 7 | 92 | 0.1x |
| 18_method_chain | 4 | 57 | 0.1x |
| 19_nested_match | 6 | 57 | 0.1x |
| 20_recursion | 4 | 51 | 0.1x |
| 21_list_ops | 5 | 58 | 0.1x |
| 22_string_builder | 5 | 59 | 0.1x |
| 23_multi_return | 5 | 56 | 0.1x |
| 25_fizzbuzz | 5 | 69 | 0.1x |

