# Mapanare Benchmarks - Linux

Generated: 2026-04-05 20:05 UTC  
Version: 3.7.0 (`534fdb5`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 564 | `____.___ v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 7 | `        ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 5 | `         ^` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 7 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 5 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 6 | `         v` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `         v` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 6 | `         v` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 6 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         v` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 5 | ` _-_ ___` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | `_____.__` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | `_______  v` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `_.____  ` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 5 | `.--____  v` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `____-___` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 4 | `_ __*___` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 7 | `  _ *___` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 4 | `        ` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | ` _ ___  ` | PASS |
| **Total** | **266** | **2222** | **71.4** | **38** | **135** | **2065** | **691** | | **25/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 56 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 59 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 54 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 54 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 60 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 46 | YES | PASS |
| 07_enum_match | 109 | 4.6 | 1 | 67 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 74 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 62 | YES | PASS |
| 10_result | 144 | 6.0 | 2 | 57 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 72 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 77 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 83 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 78 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 62 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 53 | YES | PASS |
| 17_option | 170 | 6.7 | 2 | 58 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 49 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 56 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 55 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 63 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 69 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 47 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 56 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 58 | YES | PASS |
| **Total** | | | | **1524** | **25/25** | **25/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 564 | 56 | 10.2x |
| 02_arithmetic | 7 | 59 | 0.1x |
| 03_function | 5 | 54 | 0.1x |
| 04_if_else | 4 | 54 | 0.1x |
| 05_for_loop | 5 | 60 | 0.1x |
| 06_struct | 5 | 46 | 0.1x |
| 07_enum_match | 7 | 67 | 0.1x |
| 08_list | 6 | 74 | 0.1x |
| 09_string_methods | 5 | 62 | 0.1x |
| 10_result | 6 | 57 | 0.1x |
| 11_closure | 4 | 72 | 0.1x |
| 12_while | 6 | 77 | 0.1x |
| 13_fib | 6 | 83 | 0.1x |
| 14_nested_struct | 6 | 78 | 0.1x |
| 15_multifunction | 4 | 62 | 0.1x |
| 16_string_escape | 5 | 53 | 0.1x |
| 17_option | 5 | 58 | 0.1x |
| 18_method_chain | 4 | 49 | 0.1x |
| 19_nested_match | 6 | 56 | 0.1x |
| 20_recursion | 5 | 55 | 0.1x |
| 21_list_ops | 5 | 63 | 0.1x |
| 22_string_builder | 4 | 69 | 0.1x |
| 23_multi_return | 7 | 47 | 0.1x |
| 24_enum_methods | 4 | 56 | 0.1x |
| 25_fizzbuzz | 4 | 58 | 0.1x |

