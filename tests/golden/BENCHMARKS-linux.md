# Mapanare Benchmarks - Linux

Generated: 2026-04-05 20:02 UTC  
Version: 3.7.0 (`0e50ee9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 520 | `_____.__ v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `         ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `        ` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 5 | `         v` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 6 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 8 | `        ` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 5 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 5 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 3 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 3 | `         v` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 4 | `         ^` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `_ _-_ __` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | `______._ v` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 3 | `        ` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 5 | `__.____  v` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 3 | ` _--    ` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `.____-__` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 4 | `._ __*__` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 5 | `.  _ *__` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 4 | `        ` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | `- _ ___  v` | PASS |
| **Total** | **266** | **2222** | **71.4** | **38** | **135** | **2065** | **632** | | **25/25** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 53 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 57 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 62 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 58 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 102 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 84 | YES | PASS |
| 07_enum_match | 109 | 4.6 | 1 | 102 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 97 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 58 | YES | PASS |
| 10_result | 144 | 6.0 | 2 | 63 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 66 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 59 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 59 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 55 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 56 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 41 | YES | PASS |
| 17_option | 170 | 6.7 | 2 | 51 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 41 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 47 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 66 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 59 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 75 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 57 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 65 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 56 | YES | PASS |
| **Total** | | | | **1588** | **25/25** | **25/25** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 520 | 53 | 9.8x |
| 02_arithmetic | 6 | 57 | 0.1x |
| 03_function | 5 | 62 | 0.1x |
| 04_if_else | 5 | 58 | 0.1x |
| 05_for_loop | 5 | 102 | 0.0x |
| 06_struct | 6 | 84 | 0.1x |
| 07_enum_match | 8 | 102 | 0.1x |
| 08_list | 6 | 97 | 0.1x |
| 09_string_methods | 5 | 58 | 0.1x |
| 10_result | 5 | 63 | 0.1x |
| 11_closure | 4 | 66 | 0.1x |
| 12_while | 3 | 59 | 0.1x |
| 13_fib | 3 | 59 | 0.1x |
| 14_nested_struct | 4 | 55 | 0.1x |
| 15_multifunction | 4 | 56 | 0.1x |
| 16_string_escape | 4 | 41 | 0.1x |
| 17_option | 5 | 51 | 0.1x |
| 18_method_chain | 3 | 41 | 0.1x |
| 19_nested_match | 5 | 47 | 0.1x |
| 20_recursion | 3 | 66 | 0.1x |
| 21_list_ops | 5 | 59 | 0.1x |
| 22_string_builder | 4 | 75 | 0.1x |
| 23_multi_return | 5 | 57 | 0.1x |
| 24_enum_methods | 4 | 65 | 0.1x |
| 25_fizzbuzz | 4 | 56 | 0.1x |

