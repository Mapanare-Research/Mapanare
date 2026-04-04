# Mapanare Benchmarks - Linux

Generated: 2026-04-04 23:12 UTC  
Version: 3.4.0 (`99640b9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.3s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 554 | `.......~ ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 7 | `   _    ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 6 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `        ` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `        ` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 5 | `         ^` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `         v` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 6 | `         ^` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | ` *___  _ ^` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | ` **    * ^` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | `  ***  * ^` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | ` .* ..  ` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 4 | `. .*..*  v` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `   . * . ^` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 4 | `.. .**..` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 5 | `*..*.. . ^` | PASS |
| 24_enum_methods | 20 | 0 | 0.0 | 0 | 0 | 0 | 3 | `   *    ` | FAIL |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 5 | `   *-__  v` | PASS |
| **Total** | **266** | **2115** | **67.6** | **36** | **127** | **1983** | **672** | | **24/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 82 | 3.6 | 1 | 58 | YES | PASS |
| 02_arithmetic | 87 | 3.6 | 1 | 63 | YES | PASS |
| 03_function | 97 | 3.8 | 2 | 52 | YES | PASS |
| 04_if_else | 99 | 4.1 | 1 | 47 | YES | PASS |
| 05_for_loop | 110 | 4.5 | 1 | 54 | YES | PASS |
| 06_struct | 92 | 3.8 | 1 | 53 | YES | PASS |
| 07_enum_match | 104 | 4.4 | 1 | 58 | YES | PASS |
| 08_list | 114 | 4.8 | 1 | 60 | YES | PASS |
| 09_string_methods | 94 | 4.2 | 1 | 67 | YES | PASS |
| 10_result | 139 | 5.8 | 2 | 73 | YES | PASS |
| 11_closure | 100 | 3.9 | 1 | 61 | DIFF | PASS |
| 12_while | 120 | 4.7 | 1 | 75 | YES | PASS |
| 13_fib | 107 | 4.0 | 2 | 79 | YES | PASS |
| 14_nested_struct | 92 | 3.9 | 1 | 78 | YES | PASS |
| 15_multifunction | 105 | 4.0 | 3 | 70 | YES | PASS |
| 16_string_escape | 101 | 4.5 | 1 | 58 | YES | PASS |
| 17_option | 165 | 6.5 | 2 | 56 | YES | PASS |
| 18_method_chain | 111 | 5.0 | 1 | 48 | YES | PASS |
| 19_nested_match | 147 | 5.6 | 2 | 54 | YES | PASS |
| 20_recursion | 108 | 4.1 | 2 | 49 | YES | PASS |
| 21_list_ops | 173 | 7.1 | 2 | 56 | YES | PASS |
| 22_string_builder | 140 | 5.9 | 2 | 62 | YES | PASS |
| 23_multi_return | 123 | 5.0 | 2 | 56 | YES | PASS |
| 25_fizzbuzz | 157 | 5.9 | 2 | 57 | YES | PASS |
| **Total** | | | | **1442** | **23/25** | **24/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 554 | 58 | 9.6x |
| 02_arithmetic | 7 | 63 | 0.1x |
| 03_function | 6 | 52 | 0.1x |
| 04_if_else | 4 | 47 | 0.1x |
| 05_for_loop | 4 | 54 | 0.1x |
| 06_struct | 5 | 53 | 0.1x |
| 07_enum_match | 5 | 58 | 0.1x |
| 08_list | 6 | 60 | 0.1x |
| 09_string_methods | 5 | 67 | 0.1x |
| 10_result | 6 | 73 | 0.1x |
| 11_closure | 4 | 61 | 0.1x |
| 12_while | 4 | 75 | 0.1x |
| 13_fib | 5 | 79 | 0.1x |
| 14_nested_struct | 5 | 78 | 0.1x |
| 15_multifunction | 6 | 70 | 0.1x |
| 16_string_escape | 4 | 58 | 0.1x |
| 17_option | 5 | 56 | 0.1x |
| 18_method_chain | 4 | 48 | 0.1x |
| 19_nested_match | 6 | 54 | 0.1x |
| 20_recursion | 4 | 49 | 0.1x |
| 21_list_ops | 5 | 56 | 0.1x |
| 22_string_builder | 4 | 62 | 0.1x |
| 23_multi_return | 5 | 56 | 0.1x |
| 25_fizzbuzz | 5 | 57 | 0.1x |

