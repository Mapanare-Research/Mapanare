# Mapanare Benchmarks - Linux

Generated: 2026-04-26 04:03 UTC  
Version: 5.6.13 (`b2987ef`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 10.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 581 | ` _ _____ ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `   __    v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `     _  ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `     _  ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 5 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `_   _._- ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `        ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 5 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `     ___` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 6 | `    _    ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `         ^` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `_   _    ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `        ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         ^` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 9 | `        ` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 8 | `    _   ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_.._-___` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 8 | `    __ _ ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `         v` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 5 | `    _    ^` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `__._.__. ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `  _     ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.8 | 2 | 9 | 83 | 4 | `         ^` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 6 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 5 | `        ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 9 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `         v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `         v` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | `    _   ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `_-______` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `__._____ ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `    ____ v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `...~._._ v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `    __   v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | `         ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `_  _  __` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `   . _  ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `. __-__. ^` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `___ ___  v` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 7 | `         ^` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `_  _ _  ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `        ` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 4 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `.._..-__` | PASS |
| **Total** | **1336** | **12735** | **480.5** | **110** | **1019** | **10795** | **945** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 192 | 11.2 | 1 | 93 | YES | PASS |
| 02_arithmetic | 202 | 11.5 | 1 | 126 | YES | PASS |
| 03_function | 224 | 12.1 | 2 | 150 | YES | PASS |
| 04_if_else | 209 | 11.7 | 1 | 127 | YES | PASS |
| 05_for_loop | 225 | 12.3 | 1 | 130 | YES | PASS |
| 06_struct | 205 | 11.6 | 1 | 120 | YES | PASS |
| 07_enum_match | 215 | 12.0 | 1 | 115 | YES | PASS |
| 08_list | 229 | 12.8 | 1 | 141 | YES | PASS |
| 09_string_methods | 215 | 12.3 | 1 | 154 | YES | PASS |
| 10_result | 260 | 13.8 | 2 | 145 | YES | PASS |
| 11_closure | 227 | 12.2 | 1 | 122 | YES | PASS |
| 12_while | 211 | 11.7 | 1 | 125 | YES | PASS |
| 13_fib | 222 | 11.9 | 2 | 157 | YES | PASS |
| 14_nested_struct | 205 | 11.6 | 1 | 122 | YES | PASS |
| 15_multifunction | 235 | 12.4 | 3 | 126 | YES | PASS |
| 16_string_escape | 211 | 12.1 | 1 | 114 | YES | PASS |
| 17_option | 287 | 14.5 | 2 | 150 | YES | PASS |
| 18_method_chain | 237 | 13.3 | 1 | 148 | YES | PASS |
| 19_nested_match | 260 | 13.5 | 2 | 172 | YES | PASS |
| 20_recursion | 228 | 12.2 | 2 | 122 | YES | PASS |
| 21_list_ops | 311 | 16.2 | 2 | 135 | YES | PASS |
| 22_string_builder | 280 | 14.8 | 2 | 165 | YES | PASS |
| 23_multi_return | 254 | 13.7 | 2 | 159 | YES | PASS |
| 24_enum_methods | 248 | 13.3 | 2 | 172 | YES | PASS |
| 25_fizzbuzz | 292 | 14.6 | 2 | 158 | YES | PASS |
| 26_generics | 272 | 13.7 | 5 | 160 | YES | PASS |
| 27_impl | 232 | 12.5 | 3 | 180 | YES | PASS |
| 28_traits | 240 | 12.7 | 3 | 165 | YES | PASS |
| 29_generic_impl | 241 | 13.0 | 3 | 139 | YES | PASS |
| 30_nested_generics | 232 | 13.3 | 1 | 114 | YES | PASS |
| 31_generic_multi | 257 | 13.8 | 4 | 208 | YES | PASS |
| 32_generic_enum | 203 | 11.5 | 1 | 126 | YES | PASS |
| 33_break_continue | 414 | 18.2 | 5 | 132 | YES | PASS |
| 34_file_io | 285 | 16.0 | 1 | 145 | YES | PASS |
| 35_stdin | 217 | 12.4 | 1 | 175 | YES | PASS |
| 36_crypto | 246 | 13.8 | 1 | 206 | YES | PASS |
| 37_regex | 257 | 14.5 | 1 | 130 | YES | PASS |
| 38_http | 208 | 11.9 | 1 | 122 | YES | PASS |
| 39_gpu_detect | 235 | 13.1 | 1 | 108 | YES | PASS |
| 40_gpu_tensor | 414 | 21.3 | 1 | 143 | YES | PASS |
| 41_module_let | 206 | 11.5 | 2 | 110 | YES | PASS |
| 42_module_let_string | 209 | 11.7 | 2 | 111 | YES | PASS |
| 43_module_let_math | 213 | 11.8 | 2 | 111 | YES | PASS |
| 45_ffi_bind | 241 | 12.4 | 3 | 133 | YES | PASS |
| 47_try_operator | 344 | 17.2 | 4 | 119 | YES | PASS |
| 48_match_nested_exhaustive | 437 | 21.6 | 3 | 138 | YES | PASS |
| 49_match_guards | 264 | 14.1 | 2 | 144 | YES | PASS |
| 49_tensor_literal | 469 | 23.7 | 1 | 118 | YES | PASS |
| 50_match_or_patterns | 282 | 15.0 | 2 | 114 | YES | PASS |
| 50_tensor_indexing | 441 | 22.4 | 1 | 122 | YES | PASS |
| 51_tensor_broadcast | 453 | 22.6 | 1 | 150 | YES | PASS |
| 52_tensor_slicing | 448 | 22.8 | 1 | 131 | YES | PASS |
| 53_linear_regression | 375 | 19.0 | 1 | 149 | YES | PASS |
| 54_const_basic | 212 | 12.1 | 1 | 110 | YES | PASS |
| 55_async_basic | 254 | 13.5 | 2 | 113 | YES | PASS |
| 56_async_await | 333 | 16.4 | 3 | 128 | YES | PASS |
| 57_real_await | 489 | 22.2 | 5 | 144 | YES | PASS |
| 58_async_file_io | 416 | 19.4 | 4 | 126 | YES | PASS |
| 58_const_scope | 245 | 12.9 | 2 | 120 | YES | PASS |
| 59_async_fanout | 1042 | 43.2 | 12 | 119 | YES | PASS |
| 62_list_output | 371 | 19.9 | 3 | 183 | YES | PASS |
| 63_else_sino | 301 | 14.9 | 3 | 139 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 31 | - | FAIL |
| 65_list_int_indexing | 389 | 20.2 | 1 | 121 | YES | PASS |
| 66_qualified_type_ref | 228 | 12.5 | 2 | 117 | YES | PASS |
| **Total** | | | | **8802** | **64/66** | **64/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 581 | 93 | 6.3x |
| 02_arithmetic | 6 | 126 | 0.0x |
| 03_function | 8 | 150 | 0.1x |
| 04_if_else | 5 | 127 | 0.0x |
| 05_for_loop | 5 | 130 | 0.0x |
| 06_struct | 5 | 120 | 0.0x |
| 07_enum_match | 12 | 115 | 0.1x |
| 08_list | 6 | 141 | 0.0x |
| 09_string_methods | 5 | 154 | 0.0x |
| 10_result | 6 | 145 | 0.0x |
| 11_closure | 4 | 122 | 0.0x |
| 12_while | 4 | 125 | 0.0x |
| 13_fib | 5 | 157 | 0.0x |
| 14_nested_struct | 4 | 122 | 0.0x |
| 15_multifunction | 5 | 126 | 0.0x |
| 16_string_escape | 5 | 114 | 0.0x |
| 17_option | 5 | 150 | 0.0x |
| 18_method_chain | 5 | 148 | 0.0x |
| 19_nested_match | 7 | 172 | 0.0x |
| 20_recursion | 5 | 122 | 0.0x |
| 21_list_ops | 5 | 135 | 0.0x |
| 22_string_builder | 5 | 165 | 0.0x |
| 23_multi_return | 6 | 159 | 0.0x |
| 24_enum_methods | 5 | 172 | 0.0x |
| 25_fizzbuzz | 6 | 158 | 0.0x |
| 26_generics | 7 | 160 | 0.0x |
| 27_impl | 7 | 180 | 0.0x |
| 28_traits | 6 | 165 | 0.0x |
| 29_generic_impl | 5 | 139 | 0.0x |
| 30_nested_generics | 5 | 114 | 0.0x |
| 31_generic_multi | 8 | 208 | 0.0x |
| 32_generic_enum | 4 | 126 | 0.0x |
| 33_break_continue | 9 | 132 | 0.1x |
| 34_file_io | 5 | 145 | 0.0x |
| 35_stdin | 4 | 175 | 0.0x |
| 36_crypto | 8 | 206 | 0.0x |
| 37_regex | 5 | 130 | 0.0x |
| 38_http | 8 | 122 | 0.1x |
| 39_gpu_detect | 4 | 108 | 0.0x |
| 40_gpu_tensor | 5 | 143 | 0.0x |
| 41_module_let | 4 | 110 | 0.0x |
| 42_module_let_string | 4 | 111 | 0.0x |
| 43_module_let_math | 5 | 111 | 0.0x |
| 45_ffi_bind | 4 | 133 | 0.0x |
| 47_try_operator | 6 | 119 | 0.1x |
| 48_match_nested_exhaustive | 6 | 138 | 0.0x |
| 49_match_guards | 5 | 144 | 0.0x |
| 49_tensor_literal | 9 | 118 | 0.1x |
| 50_match_or_patterns | 5 | 114 | 0.0x |
| 50_tensor_indexing | 7 | 122 | 0.1x |
| 51_tensor_broadcast | 8 | 150 | 0.1x |
| 52_tensor_slicing | 8 | 131 | 0.1x |
| 53_linear_regression | 6 | 149 | 0.0x |
| 54_const_basic | 5 | 110 | 0.0x |
| 55_async_basic | 4 | 113 | 0.0x |
| 56_async_await | 4 | 128 | 0.0x |
| 57_real_await | 5 | 144 | 0.0x |
| 58_async_file_io | 5 | 126 | 0.0x |
| 58_const_scope | 5 | 120 | 0.0x |
| 59_async_fanout | 6 | 119 | 0.1x |
| 62_list_output | 7 | 183 | 0.0x |
| 63_else_sino | 6 | 139 | 0.0x |
| 65_list_int_indexing | 4 | 121 | 0.0x |
| 66_qualified_type_ref | 5 | 117 | 0.0x |

