# Mapanare Benchmarks - Linux

Generated: 2026-04-15 01:58 UTC  
Version: 4.126.0 (`d77e5bd`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 8.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 801 | `~.-.-... ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 8 | `_        v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 7 | `_        ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 14 | `*       ` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 6 | `        ` | PASS |
| 10_result | 14 | 142 | 5.1 | 2 | 10 | 147 | 6 | `*        ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 7 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 7 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `_  _     ^` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 9 | `*        ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `*-..-__. ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 11 | `*     _  v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 7 | `~-.-_.__` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `-*.__.__` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 6 | `.* _._ - ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `-___.__~ ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         ^` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 8 | `._.__  . ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 10 | `~-.._.._ v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | `~__ ___  v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 7 | `-.__.___` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 6 | `   _     ^` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 9 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `-.______` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 7 | `._ _._ _ ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 6 | `-      _ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `. _    _ ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | `_       ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 7 | `.-__.__- ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 6 | `__ __ --` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 7 | ` _     _ ^` | PASS |
| 47_try_operator | 32 | 288 | 10.7 | 4 | 23 | 279 | 8 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 337 | 13.6 | 3 | 32 | 309 | 9 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 7 | `_____- _ ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 12 | `_  __   ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | `____    ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `_ ___  - ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `___ __ _ ^` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `._._____` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `--*_____` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `---__ __` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `_.. _  _ ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `.*  .  . ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `___ __  ` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `- __-_-_ v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `._____.  v` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `. .. .*  v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `_  * _-_ v` | PASS |
| 62_list_output | 35 | 295 | 14.1 | 2 | 20 | 289 | 8 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.6 | 3 | 20 | 250 | 8 | `..______` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `-.__.__. ^` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 5 | `         ^` | PASS |
| **Total** | **1315** | **12528** | **471.2** | **109** | **991** | **10682** | **1235** | | **64/65** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 132 | 7.8 | 1 | 129 | YES | PASS |
| 02_arithmetic | 137 | 7.8 | 1 | 134 | YES | PASS |
| 03_function | 147 | 8.0 | 2 | 144 | YES | PASS |
| 04_if_else | 149 | 8.3 | 1 | 141 | YES | PASS |
| 05_for_loop | 160 | 8.7 | 1 | 127 | YES | PASS |
| 06_struct | 142 | 8.0 | 1 | 109 | YES | PASS |
| 07_enum_match | 155 | 8.6 | 1 | 115 | YES | PASS |
| 08_list | 164 | 9.1 | 1 | 94 | YES | PASS |
| 09_string_methods | 145 | 8.4 | 1 | 81 | YES | PASS |
| 10_result | 190 | 10.0 | 2 | 121 | YES | PASS |
| 11_closure | 150 | 8.1 | 1 | 146 | YES | PASS |
| 12_while | 146 | 8.0 | 1 | 108 | YES | PASS |
| 13_fib | 0 | 0.0 | 0 | 148 | - | FAIL |
| 14_nested_struct | 142 | 8.0 | 1 | 109 | YES | PASS |
| 15_multifunction | 155 | 8.2 | 3 | 117 | YES | PASS |
| 16_string_escape | 151 | 8.7 | 1 | 97 | YES | PASS |
| 17_option | 217 | 10.7 | 2 | 146 | YES | PASS |
| 18_method_chain | 162 | 9.2 | 1 | 122 | YES | PASS |
| 19_nested_match | 0 | 0.0 | 0 | 150 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 108 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 73 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 94 | - | FAIL |
| 23_multi_return | 166 | 8.9 | 2 | 121 | YES | PASS |
| 24_enum_methods | 178 | 9.4 | 2 | 110 | YES | PASS |
| 25_fizzbuzz | 207 | 10.1 | 2 | 119 | YES | PASS |
| 26_generics | 204 | 10.0 | 5 | 127 | YES | PASS |
| 27_impl | 165 | 8.8 | 3 | 150 | YES | PASS |
| 28_traits | 170 | 8.8 | 3 | 138 | YES | PASS |
| 29_generic_impl | 0 | 0.0 | 0 | 118 | - | FAIL |
| 30_nested_generics | 172 | 9.8 | 1 | 106 | YES | PASS |
| 31_generic_multi | 0 | 0.0 | 0 | 123 | - | FAIL |
| 32_generic_enum | 149 | 8.3 | 1 | 96 | YES | PASS |
| 33_break_continue | 0 | 0.0 | 0 | 74 | - | FAIL |
| 34_file_io | 200 | 11.4 | 1 | 83 | YES | PASS |
| 35_stdin | 142 | 8.3 | 1 | 104 | YES | PASS |
| 36_crypto | 161 | 9.3 | 1 | 127 | YES | PASS |
| 37_regex | 182 | 10.4 | 1 | 110 | YES | PASS |
| 38_http | 138 | 8.1 | 1 | 105 | YES | PASS |
| 39_gpu_detect | 155 | 8.8 | 1 | 87 | YES | PASS |
| 40_gpu_tensor | 0 | 0.0 | 0 | 74 | - | FAIL |
| 41_module_let | 137 | 7.8 | 2 | 99 | YES | PASS |
| 42_module_let_string | 140 | 8.0 | 2 | 114 | YES | PASS |
| 43_module_let_math | 142 | 8.1 | 2 | 111 | YES | PASS |
| 45_ffi_bind | 169 | 8.5 | 3 | 137 | YES | PASS |
| 47_try_operator | 0 | 0.0 | 0 | 136 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 134 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 90 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 46 | - | FAIL |
| 50_match_or_patterns | 196 | 10.4 | 2 | 123 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 35 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 35 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 30 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 33 | - | FAIL |
| 54_const_basic | 138 | 8.1 | 1 | 74 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 26 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 26 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 28 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 29 | - | FAIL |
| 58_const_scope | 173 | 9.1 | 2 | 85 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 35 | - | FAIL |
| 62_list_output | 0 | 0.0 | 0 | 117 | - | FAIL |
| 63_else_sino | 0 | 0.0 | 0 | 98 | - | FAIL |
| 64_closure_typed | 0 | 0.0 | 0 | 34 | - | FAIL |
| 65_list_int_indexing | 226 | 12.2 | 1 | 100 | YES | PASS |
| **Total** | | | | **6361** | **39/65** | **39/65** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 801 | 129 | 6.2x |
| 02_arithmetic | 8 | 134 | 0.1x |
| 03_function | 8 | 144 | 0.1x |
| 04_if_else | 6 | 141 | 0.0x |
| 05_for_loop | 7 | 127 | 0.1x |
| 06_struct | 7 | 109 | 0.1x |
| 07_enum_match | 14 | 115 | 0.1x |
| 08_list | 7 | 94 | 0.1x |
| 09_string_methods | 6 | 81 | 0.1x |
| 10_result | 6 | 121 | 0.0x |
| 11_closure | 7 | 146 | 0.0x |
| 12_while | 5 | 108 | 0.0x |
| 14_nested_struct | 7 | 109 | 0.1x |
| 15_multifunction | 7 | 117 | 0.1x |
| 16_string_escape | 5 | 97 | 0.1x |
| 17_option | 9 | 146 | 0.1x |
| 18_method_chain | 5 | 122 | 0.0x |
| 23_multi_return | 6 | 121 | 0.1x |
| 24_enum_methods | 6 | 110 | 0.1x |
| 25_fizzbuzz | 6 | 119 | 0.0x |
| 26_generics | 8 | 127 | 0.1x |
| 27_impl | 8 | 150 | 0.1x |
| 28_traits | 10 | 138 | 0.1x |
| 30_nested_generics | 7 | 106 | 0.1x |
| 32_generic_enum | 6 | 96 | 0.1x |
| 34_file_io | 5 | 83 | 0.1x |
| 35_stdin | 4 | 104 | 0.0x |
| 36_crypto | 7 | 127 | 0.1x |
| 37_regex | 6 | 110 | 0.1x |
| 38_http | 5 | 105 | 0.1x |
| 39_gpu_detect | 5 | 87 | 0.1x |
| 41_module_let | 5 | 99 | 0.1x |
| 42_module_let_string | 7 | 114 | 0.1x |
| 43_module_let_math | 6 | 111 | 0.1x |
| 45_ffi_bind | 7 | 137 | 0.1x |
| 50_match_or_patterns | 7 | 123 | 0.1x |
| 54_const_basic | 5 | 74 | 0.1x |
| 58_const_scope | 5 | 85 | 0.1x |
| 65_list_int_indexing | 5 | 100 | 0.1x |

