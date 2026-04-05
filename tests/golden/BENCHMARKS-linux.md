# Mapanare Benchmarks - Linux

Generated: 2026-04-05 16:15 UTC  
Version: 3.6.0 (`3203047`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 533 | `..._...- ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 7 | `         ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 6 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 5 | `         ^` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 4 | `         ^` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `        ` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `         v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `__..__.  v` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 6 | `__.._.__` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 5 | `_ __ -  ` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `_____-__` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 5 | `__ _ -  ` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `_.._..__` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `_ _ ___- ^` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 4 | `-____ _- ^` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 4 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | `__ -____` | PASS |
| **Total** | **266** | **2222** | **71.4** | **38** | **135** | **2065** | **649** | | **25/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 4 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 3 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 3 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 3 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 3 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 3 | YES | PASS |
| 07_enum_match | 108 | 4.5 | 1 | 3 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 3 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 3 | YES | PASS |
| 10_result | 143 | 5.9 | 2 | 3 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 3 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 3 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 3 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 3 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 3 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 3 | YES | PASS |
| 17_option | 168 | 6.5 | 2 | 4 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 3 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 3 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 3 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 4 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 3 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 3 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 3 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 3 | YES | PASS |
| **Total** | | | | **79** | **25/25** | **25/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 533 | 4 | 145.0x |
| 02_arithmetic | 7 | 3 | 2.2x |
| 03_function | 6 | 3 | 1.9x |
| 04_if_else | 4 | 3 | 1.4x |
| 05_for_loop | 5 | 3 | 1.4x |
| 06_struct | 6 | 3 | 1.8x |
| 07_enum_match | 6 | 3 | 1.6x |
| 08_list | 6 | 3 | 2.0x |
| 09_string_methods | 4 | 3 | 1.2x |
| 10_result | 6 | 3 | 1.7x |
| 11_closure | 4 | 3 | 1.3x |
| 12_while | 4 | 3 | 1.3x |
| 13_fib | 4 | 3 | 1.4x |
| 14_nested_struct | 4 | 3 | 1.3x |
| 15_multifunction | 4 | 3 | 1.3x |
| 16_string_escape | 4 | 3 | 1.4x |
| 17_option | 6 | 4 | 1.6x |
| 18_method_chain | 5 | 3 | 1.4x |
| 19_nested_match | 6 | 3 | 1.9x |
| 20_recursion | 5 | 3 | 1.4x |
| 21_list_ops | 5 | 4 | 1.4x |
| 22_string_builder | 5 | 3 | 1.7x |
| 23_multi_return | 4 | 3 | 1.4x |
| 24_enum_methods | 4 | 3 | 1.5x |
| 25_fizzbuzz | 4 | 3 | 1.4x |

