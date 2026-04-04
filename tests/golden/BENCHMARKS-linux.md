# Mapanare Benchmarks - Linux

Generated: 2026-04-04 22:54 UTC  
Version: 3.4.0 (`cd0ec28`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 567 | `........ v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 7 | `_    _  ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 6 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 5 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `        ` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 4 | `         ^` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 5 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 5 | `         v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | ` *___  v` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | ` **   ` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | `  ***  v` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | ` .* ..` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 6 | `. .*..` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `   . * ^` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `.. .**` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 4 | `*  *  ` | PASS |
| 24_enum_methods | 20 | 0 | 0.0 | 0 | 0 | 0 | 3 | `   *  ` | FAIL |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 5 | `   *-_ v` | PASS |
| **Total** | **266** | **2115** | **67.6** | **36** | **127** | **1983** | **686** | | **24/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 81 | 3.5 | 1 | 50 | YES | PASS |
| 02_arithmetic | 86 | 3.6 | 1 | 48 | YES | PASS |
| 03_function | 96 | 3.8 | 2 | 48 | YES | PASS |
| 04_if_else | 98 | 4.1 | 1 | 60 | YES | PASS |
| 05_for_loop | 109 | 4.4 | 1 | 58 | YES | PASS |
| 06_struct | 91 | 3.8 | 1 | 59 | YES | PASS |
| 07_enum_match | 103 | 4.3 | 1 | 67 | YES | PASS |
| 08_list | 113 | 4.8 | 1 | 57 | YES | PASS |
| 09_string_methods | 93 | 4.2 | 1 | 55 | YES | PASS |
| 10_result | 138 | 5.7 | 2 | 49 | YES | PASS |
| 11_closure | 99 | 3.9 | 1 | 61 | DIFF | PASS |
| 12_while | 119 | 4.7 | 1 | 52 | YES | PASS |
| 13_fib | 106 | 4.0 | 2 | 53 | YES | PASS |
| 14_nested_struct | 91 | 3.8 | 1 | 54 | YES | PASS |
| 15_multifunction | 104 | 3.9 | 3 | 57 | YES | PASS |
| 16_string_escape | 100 | 4.5 | 1 | 45 | YES | PASS |
| 17_option | 164 | 6.4 | 2 | 55 | YES | PASS |
| 18_method_chain | 110 | 4.9 | 1 | 52 | YES | PASS |
| 19_nested_match | 146 | 5.6 | 2 | 62 | YES | PASS |
| 20_recursion | 107 | 4.1 | 2 | 71 | YES | PASS |
| 21_list_ops | 172 | 7.1 | 2 | 80 | YES | PASS |
| 22_string_builder | 139 | 5.8 | 2 | 65 | YES | PASS |
| 23_multi_return | 122 | 5.0 | 2 | 54 | YES | PASS |
| 25_fizzbuzz | 156 | 5.8 | 2 | 59 | YES | PASS |
| **Total** | | | | **1371** | **23/25** | **24/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 567 | 50 | 11.3x |
| 02_arithmetic | 7 | 48 | 0.1x |
| 03_function | 6 | 48 | 0.1x |
| 04_if_else | 5 | 60 | 0.1x |
| 05_for_loop | 5 | 58 | 0.1x |
| 06_struct | 5 | 59 | 0.1x |
| 07_enum_match | 6 | 67 | 0.1x |
| 08_list | 6 | 57 | 0.1x |
| 09_string_methods | 4 | 55 | 0.1x |
| 10_result | 6 | 49 | 0.1x |
| 11_closure | 5 | 61 | 0.1x |
| 12_while | 5 | 52 | 0.1x |
| 13_fib | 4 | 53 | 0.1x |
| 14_nested_struct | 4 | 54 | 0.1x |
| 15_multifunction | 4 | 57 | 0.1x |
| 16_string_escape | 4 | 45 | 0.1x |
| 17_option | 5 | 55 | 0.1x |
| 18_method_chain | 4 | 52 | 0.1x |
| 19_nested_match | 6 | 62 | 0.1x |
| 20_recursion | 6 | 71 | 0.1x |
| 21_list_ops | 5 | 80 | 0.1x |
| 22_string_builder | 5 | 65 | 0.1x |
| 23_multi_return | 4 | 54 | 0.1x |
| 25_fizzbuzz | 5 | 59 | 0.1x |

