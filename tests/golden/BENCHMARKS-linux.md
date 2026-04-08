# Mapanare Benchmarks - Linux

Generated: 2026-04-08 16:21 UTC  
Version: 3.41.0 (`c28aae9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 488 | `___.____ ^` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 6 | `        ` | PASS |
| 03_function | 8 | 71 | 2.1 | 2 | 6 | 65 | 5 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `        ` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 5 | `         ^` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 85 | 3.2 | 1 | 6 | 51 | 3 | `        ` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 6 | `         ^` | PASS |
| 11_closure | 5 | 100 | 3.3 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 5 | `        ` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 4 | `         ^` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 116 | 3.5 | 3 | 10 | 114 | 4 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `...___._ v` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 5 | `_..__-._ v` | PASS |
| 18_method_chain | 9 | 121 | 4.7 | 1 | 8 | 84 | 4 | `--__.___` | PASS |
| 19_nested_match | 18 | 197 | 6.7 | 2 | 15 | 186 | 5 | `--.*- __` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 224 | 8.2 | 2 | 13 | 269 | 5 | `_._~-__. ^` | PASS |
| 22_string_builder | 14 | 126 | 4.4 | 2 | 7 | 116 | 4 | `.._.-_..` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 6 | ` _.___ _ ^` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 7 | `        ` | PASS |
| 25_fizzbuzz | 18 | 184 | 5.8 | 2 | 16 | 166 | 5 | `_._..   ` | PASS |
| 26_generics | 29 | 164 | 5.2 | 5 | 12 | 129 | 6 | `         v` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 4 | ` _      ` | PASS |
| 28_traits | 25 | 96 | 2.8 | 3 | 6 | 98 | 4 | `__.__   ` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 4 | `         ^` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 4 | ` _.     ` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 6 | `        ` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 5 | `-_______` | PASS |
| 33_break_continue | 58 | 402 | 12.2 | 5 | 36 | 398 | 8 | `_  __   ` | PASS |
| 34_file_io | 19 | 232 | 9.9 | 1 | 12 | 185 | 5 | `  *  v` | PASS |
| 35_stdin | 4 | 90 | 3.5 | 1 | 8 | 65 | 4 | `  * ^` | PASS |
| 36_crypto | 13 | 145 | 5.8 | 1 | 12 | 108 | 5 | ` ` | PASS |
| 37_regex | 10 | 159 | 6.7 | 1 | 8 | 109 | 4 | ` ` | PASS |
| 38_http | 5 | 72 | 2.7 | 1 | 6 | 49 | 6 | ` ` | PASS |
| **Total** | **545** | **4468** | **152.9** | **68** | **319** | **3955** | **668** | | **38/38** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 88 | 4.1 | 1 | 52 | YES | PASS |
| 02_arithmetic | 93 | 4.1 | 1 | 52 | YES | PASS |
| 03_function | 103 | 4.3 | 2 | 55 | YES | PASS |
| 04_if_else | 105 | 4.6 | 1 | 55 | YES | PASS |
| 05_for_loop | 116 | 4.9 | 1 | 58 | YES | PASS |
| 06_struct | 98 | 4.3 | 1 | 59 | YES | PASS |
| 07_enum_match | 110 | 4.9 | 1 | 53 | YES | PASS |
| 08_list | 120 | 5.4 | 1 | 55 | YES | PASS |
| 09_string_methods | 100 | 4.7 | 1 | 55 | YES | PASS |
| 10_result | 145 | 6.3 | 2 | 85 | YES | PASS |
| 11_closure | 106 | 4.4 | 1 | 76 | YES | PASS |
| 12_while | 102 | 4.3 | 1 | 62 | YES | PASS |
| 13_fib | 113 | 4.5 | 2 | 66 | YES | PASS |
| 14_nested_struct | 98 | 4.3 | 1 | 63 | YES | PASS |
| 15_multifunction | 111 | 4.5 | 3 | 59 | YES | PASS |
| 16_string_escape | 107 | 5.0 | 1 | 43 | YES | PASS |
| 17_option | 171 | 6.9 | 2 | 56 | YES | PASS |
| 18_method_chain | 117 | 5.5 | 1 | 44 | YES | PASS |
| 19_nested_match | 153 | 6.1 | 2 | 58 | YES | PASS |
| 20_recursion | 114 | 4.6 | 2 | 52 | YES | PASS |
| 21_list_ops | 179 | 7.7 | 2 | 61 | YES | PASS |
| 22_string_builder | 146 | 6.4 | 2 | 62 | YES | PASS |
| 23_multi_return | 129 | 5.5 | 2 | 88 | YES | PASS |
| 24_enum_methods | 134 | 5.7 | 2 | 93 | YES | PASS |
| 25_fizzbuzz | 163 | 6.4 | 2 | 64 | YES | PASS |
| 26_generics | 159 | 6.2 | 5 | 55 | YES | PASS |
| 27_impl | 127 | 5.2 | 3 | 56 | YES | PASS |
| 28_traits | 129 | 5.2 | 3 | 58 | YES | PASS |
| 29_generic_impl | 136 | 5.7 | 3 | 61 | YES | PASS |
| 30_nested_generics | 128 | 6.1 | 1 | 58 | YES | PASS |
| 31_generic_multi | 154 | 6.5 | 4 | 70 | YES | PASS |
| 32_generic_enum | 105 | 4.6 | 1 | 63 | YES | PASS |
| 33_break_continue | 297 | 10.2 | 5 | 64 | YES | PASS |
| 34_file_io | 152 | 7.5 | 1 | 56 | YES | PASS |
| 35_stdin | 98 | 4.6 | 1 | 50 | YES | PASS |
| 36_crypto | 117 | 5.5 | 1 | 51 | YES | PASS |
| 37_regex | 128 | 6.2 | 1 | 49 | YES | PASS |
| 38_http | 94 | 4.3 | 1 | 46 | YES | PASS |
| **Total** | | | | **2262** | **38/38** | **38/38** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 488 | 52 | 9.5x |
| 02_arithmetic | 6 | 52 | 0.1x |
| 03_function | 5 | 55 | 0.1x |
| 04_if_else | 4 | 55 | 0.1x |
| 05_for_loop | 5 | 58 | 0.1x |
| 06_struct | 4 | 59 | 0.1x |
| 07_enum_match | 5 | 53 | 0.1x |
| 08_list | 5 | 55 | 0.1x |
| 09_string_methods | 3 | 55 | 0.1x |
| 10_result | 6 | 85 | 0.1x |
| 11_closure | 5 | 76 | 0.1x |
| 12_while | 5 | 62 | 0.1x |
| 13_fib | 4 | 66 | 0.1x |
| 14_nested_struct | 5 | 63 | 0.1x |
| 15_multifunction | 4 | 59 | 0.1x |
| 16_string_escape | 4 | 43 | 0.1x |
| 17_option | 5 | 56 | 0.1x |
| 18_method_chain | 4 | 44 | 0.1x |
| 19_nested_match | 5 | 58 | 0.1x |
| 20_recursion | 4 | 52 | 0.1x |
| 21_list_ops | 5 | 61 | 0.1x |
| 22_string_builder | 4 | 62 | 0.1x |
| 23_multi_return | 6 | 88 | 0.1x |
| 24_enum_methods | 7 | 93 | 0.1x |
| 25_fizzbuzz | 5 | 64 | 0.1x |
| 26_generics | 6 | 55 | 0.1x |
| 27_impl | 4 | 56 | 0.1x |
| 28_traits | 4 | 58 | 0.1x |
| 29_generic_impl | 4 | 61 | 0.1x |
| 30_nested_generics | 4 | 58 | 0.1x |
| 31_generic_multi | 6 | 70 | 0.1x |
| 32_generic_enum | 5 | 63 | 0.1x |
| 33_break_continue | 8 | 64 | 0.1x |
| 34_file_io | 5 | 56 | 0.1x |
| 35_stdin | 4 | 50 | 0.1x |
| 36_crypto | 5 | 51 | 0.1x |
| 37_regex | 4 | 49 | 0.1x |
| 38_http | 6 | 46 | 0.1x |

