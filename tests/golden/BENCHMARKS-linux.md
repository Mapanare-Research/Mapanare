# Mapanare Benchmarks - Linux

Generated: 2026-04-08 18:57 UTC  
Version: 3.45.0 (`1c5b67a`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 540 | `________ v` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 6 | `         ^` | PASS |
| 03_function | 8 | 71 | 2.1 | 2 | 6 | 65 | 5 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 4 | `         ^` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 5 | `         ^` | PASS |
| 09_string_methods | 5 | 86 | 3.3 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 6 | `        ` | PASS |
| 11_closure | 5 | 100 | 3.3 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 4 | `         ^` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 116 | 3.5 | 3 | 10 | 114 | 4 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `__.__  _ ^` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 5 | `_-._____` | PASS |
| 18_method_chain | 9 | 122 | 4.8 | 1 | 8 | 84 | 5 | `._______` | PASS |
| 19_nested_match | 18 | 197 | 6.7 | 2 | 15 | 186 | 6 | `- __   _ ^` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 224 | 8.2 | 2 | 13 | 269 | 7 | `-__._ .- ^` | PASS |
| 22_string_builder | 14 | 126 | 4.4 | 2 | 7 | 116 | 5 | `-_..__-* ^` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 4 | `__ _. ._ v` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 184 | 5.8 | 2 | 16 | 166 | 6 | `.   _ __` | PASS |
| 26_generics | 29 | 165 | 5.2 | 5 | 12 | 129 | 8 | `        ` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 7 | `        ` | PASS |
| 28_traits | 25 | 96 | 2.8 | 3 | 6 | 98 | 7 | `_       ` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 6 | `        ` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 5 | `        ` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 6 | `        ` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 4 | `____-___` | PASS |
| 33_break_continue | 58 | 402 | 12.2 | 5 | 36 | 398 | 7 | `_   _   ` | PASS |
| 34_file_io | 19 | 234 | 10.0 | 1 | 12 | 185 | 6 | `  *     ` | PASS |
| 35_stdin | 4 | 90 | 3.5 | 1 | 8 | 65 | 5 | `  ** **` | PASS |
| 36_crypto | 13 | 145 | 5.8 | 1 | 12 | 108 | 4 | ` *  * ^` | PASS |
| 37_regex | 10 | 161 | 6.8 | 1 | 8 | 109 | 5 | `   **` | PASS |
| 38_http | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` *   ` | PASS |
| **Total** | **545** | **4475** | **153.1** | **68** | **319** | **3955** | **730** | | **38/38** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 88 | 4.1 | 1 | 51 | YES | PASS |
| 02_arithmetic | 93 | 4.1 | 1 | 49 | YES | PASS |
| 03_function | 103 | 4.3 | 2 | 56 | YES | PASS |
| 04_if_else | 105 | 4.6 | 1 | 54 | YES | PASS |
| 05_for_loop | 116 | 4.9 | 1 | 59 | YES | PASS |
| 06_struct | 98 | 4.3 | 1 | 59 | YES | PASS |
| 07_enum_match | 110 | 4.9 | 1 | 55 | YES | PASS |
| 08_list | 120 | 5.4 | 1 | 54 | YES | PASS |
| 09_string_methods | 100 | 4.7 | 1 | 66 | YES | PASS |
| 10_result | 145 | 6.3 | 2 | 76 | YES | PASS |
| 11_closure | 106 | 4.4 | 1 | 60 | YES | PASS |
| 12_while | 102 | 4.3 | 1 | 55 | YES | PASS |
| 13_fib | 113 | 4.5 | 2 | 62 | YES | PASS |
| 14_nested_struct | 98 | 4.3 | 1 | 51 | YES | PASS |
| 15_multifunction | 111 | 4.5 | 3 | 60 | YES | PASS |
| 16_string_escape | 107 | 5.0 | 1 | 59 | YES | PASS |
| 17_option | 171 | 6.9 | 2 | 83 | YES | PASS |
| 18_method_chain | 117 | 5.5 | 1 | 65 | YES | PASS |
| 19_nested_match | 153 | 6.1 | 2 | 81 | YES | PASS |
| 20_recursion | 114 | 4.6 | 2 | 71 | YES | PASS |
| 21_list_ops | 179 | 7.7 | 2 | 83 | YES | PASS |
| 22_string_builder | 146 | 6.4 | 2 | 75 | YES | PASS |
| 23_multi_return | 129 | 5.5 | 2 | 61 | YES | PASS |
| 24_enum_methods | 134 | 5.7 | 2 | 75 | YES | PASS |
| 25_fizzbuzz | 163 | 6.4 | 2 | 83 | YES | PASS |
| 26_generics | 159 | 6.2 | 5 | 99 | YES | PASS |
| 27_impl | 127 | 5.2 | 3 | 89 | YES | PASS |
| 28_traits | 129 | 5.2 | 3 | 73 | YES | PASS |
| 29_generic_impl | 136 | 5.7 | 3 | 79 | YES | PASS |
| 30_nested_generics | 128 | 6.1 | 1 | 71 | YES | PASS |
| 31_generic_multi | 154 | 6.5 | 4 | 68 | YES | PASS |
| 32_generic_enum | 105 | 4.6 | 1 | 51 | YES | PASS |
| 33_break_continue | 297 | 10.2 | 5 | 61 | YES | PASS |
| 34_file_io | 152 | 7.6 | 1 | 66 | YES | PASS |
| 35_stdin | 98 | 4.6 | 1 | 75 | YES | PASS |
| 36_crypto | 117 | 5.6 | 1 | 68 | YES | PASS |
| 37_regex | 128 | 6.2 | 1 | 72 | YES | PASS |
| 38_http | 94 | 4.4 | 1 | 70 | YES | PASS |
| **Total** | | | | **2545** | **38/38** | **38/38** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 540 | 51 | 10.6x |
| 02_arithmetic | 6 | 49 | 0.1x |
| 03_function | 5 | 56 | 0.1x |
| 04_if_else | 4 | 54 | 0.1x |
| 05_for_loop | 4 | 59 | 0.1x |
| 06_struct | 5 | 59 | 0.1x |
| 07_enum_match | 5 | 55 | 0.1x |
| 08_list | 5 | 54 | 0.1x |
| 09_string_methods | 4 | 66 | 0.1x |
| 10_result | 6 | 76 | 0.1x |
| 11_closure | 4 | 60 | 0.1x |
| 12_while | 4 | 55 | 0.1x |
| 13_fib | 5 | 62 | 0.1x |
| 14_nested_struct | 5 | 51 | 0.1x |
| 15_multifunction | 4 | 60 | 0.1x |
| 16_string_escape | 4 | 59 | 0.1x |
| 17_option | 5 | 83 | 0.1x |
| 18_method_chain | 5 | 65 | 0.1x |
| 19_nested_match | 6 | 81 | 0.1x |
| 20_recursion | 4 | 71 | 0.1x |
| 21_list_ops | 7 | 83 | 0.1x |
| 22_string_builder | 5 | 75 | 0.1x |
| 23_multi_return | 4 | 61 | 0.1x |
| 24_enum_methods | 5 | 75 | 0.1x |
| 25_fizzbuzz | 6 | 83 | 0.1x |
| 26_generics | 8 | 99 | 0.1x |
| 27_impl | 7 | 89 | 0.1x |
| 28_traits | 7 | 73 | 0.1x |
| 29_generic_impl | 6 | 79 | 0.1x |
| 30_nested_generics | 5 | 71 | 0.1x |
| 31_generic_multi | 6 | 68 | 0.1x |
| 32_generic_enum | 4 | 51 | 0.1x |
| 33_break_continue | 7 | 61 | 0.1x |
| 34_file_io | 6 | 66 | 0.1x |
| 35_stdin | 5 | 75 | 0.1x |
| 36_crypto | 4 | 68 | 0.1x |
| 37_regex | 5 | 72 | 0.1x |
| 38_http | 4 | 70 | 0.1x |

