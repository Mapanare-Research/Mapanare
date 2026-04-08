# Mapanare Benchmarks - Linux

Generated: 2026-04-08 05:18 UTC  
Version: 3.39.0 (`29b0242`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 558 | `.._...-_ v` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 6 | `        ` | PASS |
| 03_function | 8 | 71 | 2.1 | 2 | 6 | 65 | 6 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 5 | `         v` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 7 | `        ` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 85 | 3.2 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 6 | `        ` | PASS |
| 11_closure | 5 | 100 | 3.3 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 4 | `        ` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 5 | `         v` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 116 | 3.5 | 3 | 10 | 114 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 5 | `-....._. ^` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 6 | `-....*._ v` | PASS |
| 18_method_chain | 9 | 121 | 4.7 | 1 | 8 | 84 | 6 | `.--..._- ^` | PASS |
| 19_nested_match | 18 | 197 | 6.7 | 2 | 15 | 186 | 8 | `----*._- ^` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 15 | 224 | 8.2 | 2 | 13 | 269 | 6 | `-..-..__` | PASS |
| 22_string_builder | 14 | 126 | 4.4 | 2 | 7 | 116 | 5 | `*--.-...` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 5 | `*_.___  ` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 184 | 5.8 | 2 | 16 | 166 | 6 | `-....___` | PASS |
| 26_generics | 29 | 164 | 5.2 | 5 | 12 | 129 | 7 | `         v` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 6 | `_ .__   ` | PASS |
| 28_traits | 25 | 96 | 2.8 | 3 | 6 | 98 | 5 | `..~..___` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 5 | `._~ -   ` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 5 | `..._*__  v` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 6 | `        ` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 4 | `*----__- ^` | PASS |
| 33_break_continue | 58 | 402 | 12.2 | 5 | 36 | 398 | 7 | `--**-_ _ ^` | PASS |
| **Total** | **494** | **3770** | **124.3** | **63** | **273** | **3439** | **731** | | **33/33** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 88 | 4.1 | 1 | 49 | YES | PASS |
| 02_arithmetic | 93 | 4.1 | 1 | 51 | YES | PASS |
| 03_function | 103 | 4.3 | 2 | 53 | YES | PASS |
| 04_if_else | 105 | 4.6 | 1 | 51 | YES | PASS |
| 05_for_loop | 116 | 4.9 | 1 | 53 | YES | PASS |
| 06_struct | 98 | 4.3 | 1 | 51 | YES | PASS |
| 07_enum_match | 110 | 4.9 | 1 | 55 | YES | PASS |
| 08_list | 120 | 5.4 | 1 | 56 | YES | PASS |
| 09_string_methods | 100 | 4.7 | 1 | 46 | YES | PASS |
| 10_result | 145 | 6.3 | 2 | 53 | YES | PASS |
| 11_closure | 106 | 4.4 | 1 | 52 | YES | PASS |
| 12_while | 102 | 4.3 | 1 | 60 | YES | PASS |
| 13_fib | 113 | 4.5 | 2 | 58 | YES | PASS |
| 14_nested_struct | 98 | 4.3 | 1 | 47 | YES | PASS |
| 15_multifunction | 111 | 4.5 | 3 | 52 | YES | PASS |
| 16_string_escape | 107 | 5.0 | 1 | 66 | YES | PASS |
| 17_option | 171 | 6.9 | 2 | 62 | YES | PASS |
| 18_method_chain | 117 | 5.5 | 1 | 59 | YES | PASS |
| 19_nested_match | 153 | 6.1 | 2 | 65 | YES | PASS |
| 20_recursion | 114 | 4.6 | 2 | 67 | YES | PASS |
| 21_list_ops | 179 | 7.7 | 2 | 78 | YES | PASS |
| 22_string_builder | 146 | 6.4 | 2 | 61 | YES | PASS |
| 23_multi_return | 129 | 5.5 | 2 | 56 | YES | PASS |
| 24_enum_methods | 134 | 5.7 | 2 | 62 | YES | PASS |
| 25_fizzbuzz | 163 | 6.4 | 2 | 84 | YES | PASS |
| 26_generics | 159 | 6.2 | 5 | 60 | YES | PASS |
| 27_impl | 127 | 5.2 | 3 | 51 | YES | PASS |
| 28_traits | 129 | 5.2 | 3 | 60 | YES | PASS |
| 29_generic_impl | 136 | 5.7 | 3 | 55 | YES | PASS |
| 30_nested_generics | 128 | 6.1 | 1 | 53 | YES | PASS |
| 31_generic_multi | 154 | 6.5 | 4 | 56 | YES | PASS |
| 32_generic_enum | 105 | 4.6 | 1 | 61 | YES | PASS |
| 33_break_continue | 297 | 10.2 | 5 | 63 | YES | PASS |
| **Total** | | | | **1907** | **33/33** | **33/33** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 558 | 49 | 11.4x |
| 02_arithmetic | 6 | 51 | 0.1x |
| 03_function | 6 | 53 | 0.1x |
| 04_if_else | 5 | 51 | 0.1x |
| 05_for_loop | 5 | 53 | 0.1x |
| 06_struct | 5 | 51 | 0.1x |
| 07_enum_match | 7 | 55 | 0.1x |
| 08_list | 6 | 56 | 0.1x |
| 09_string_methods | 5 | 46 | 0.1x |
| 10_result | 6 | 53 | 0.1x |
| 11_closure | 4 | 52 | 0.1x |
| 12_while | 4 | 60 | 0.1x |
| 13_fib | 5 | 58 | 0.1x |
| 14_nested_struct | 4 | 47 | 0.1x |
| 15_multifunction | 5 | 52 | 0.1x |
| 16_string_escape | 5 | 66 | 0.1x |
| 17_option | 6 | 62 | 0.1x |
| 18_method_chain | 6 | 59 | 0.1x |
| 19_nested_match | 8 | 65 | 0.1x |
| 20_recursion | 5 | 67 | 0.1x |
| 21_list_ops | 6 | 78 | 0.1x |
| 22_string_builder | 5 | 61 | 0.1x |
| 23_multi_return | 5 | 56 | 0.1x |
| 24_enum_methods | 5 | 62 | 0.1x |
| 25_fizzbuzz | 6 | 84 | 0.1x |
| 26_generics | 7 | 60 | 0.1x |
| 27_impl | 6 | 51 | 0.1x |
| 28_traits | 5 | 60 | 0.1x |
| 29_generic_impl | 5 | 55 | 0.1x |
| 30_nested_generics | 5 | 53 | 0.1x |
| 31_generic_multi | 6 | 56 | 0.1x |
| 32_generic_enum | 4 | 61 | 0.1x |
| 33_break_continue | 7 | 63 | 0.1x |

