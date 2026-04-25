# Mapanare Benchmarks - Linux

Generated: 2026-04-25 06:04 UTC  
Version: 5.6.9 (`a72d8fe`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 642 | `         ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `        ` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 9 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `         ^` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `  _     ` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 6 | `         v` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `  _    _ ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 7 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 7 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `         v` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `        ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 7 | `         v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `         v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 5 | `        ` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 8 | `        ` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `    _   ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` _  __ _ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `         v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 6 | `         v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `__._____` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 6 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         v` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `        ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `         ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `     _  ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `___ ___  v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 6 | `  ______` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `        ` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `_ ._____` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `         v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | `        ` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `     _  ` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `  _     ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `         ^` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `         ^` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 7 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `  _    _ ^` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `         v` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 6 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `_.___-_- ^` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **1010** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 192 | 11.2 | 1 | 147 | YES | PASS |
| 02_arithmetic | 202 | 11.5 | 1 | 211 | YES | PASS |
| 03_function | 224 | 12.1 | 2 | 166 | YES | PASS |
| 04_if_else | 209 | 11.7 | 1 | 127 | YES | PASS |
| 05_for_loop | 225 | 12.3 | 1 | 36 | YES | PASS |
| 06_struct | 207 | 11.7 | 1 | 12 | YES | PASS |
| 07_enum_match | 215 | 12.0 | 1 | 14 | YES | PASS |
| 08_list | 231 | 12.8 | 1 | 17 | YES | PASS |
| 09_string_methods | 215 | 12.3 | 1 | 9 | YES | PASS |
| 10_result | 260 | 13.8 | 2 | 9 | YES | PASS |
| 11_closure | 227 | 12.2 | 1 | 7 | YES | PASS |
| 12_while | 211 | 11.7 | 1 | 7 | YES | PASS |
| 13_fib | 222 | 11.9 | 2 | 8 | YES | PASS |
| 14_nested_struct | 207 | 11.7 | 1 | 7 | YES | PASS |
| 15_multifunction | 235 | 12.4 | 3 | 7 | YES | PASS |
| 16_string_escape | 211 | 12.1 | 1 | 6 | YES | PASS |
| 17_option | 287 | 14.5 | 2 | 7 | YES | PASS |
| 18_method_chain | 237 | 13.3 | 1 | 7 | YES | PASS |
| 19_nested_match | 260 | 13.5 | 2 | 7 | YES | PASS |
| 20_recursion | 228 | 12.2 | 2 | 8 | YES | PASS |
| 21_list_ops | 310 | 16.1 | 2 | 8 | YES | PASS |
| 22_string_builder | 280 | 14.8 | 2 | 8 | YES | PASS |
| 23_multi_return | 256 | 13.8 | 2 | 9 | YES | PASS |
| 24_enum_methods | 248 | 13.3 | 2 | 8 | YES | PASS |
| 25_fizzbuzz | 292 | 14.6 | 2 | 8 | YES | PASS |
| 26_generics | 272 | 13.7 | 5 | 7 | YES | PASS |
| 27_impl | 234 | 12.6 | 3 | 8 | YES | PASS |
| 28_traits | 242 | 12.8 | 3 | 8 | YES | PASS |
| 29_generic_impl | 241 | 12.9 | 3 | 8 | YES | PASS |
| 30_nested_generics | 232 | 13.3 | 1 | 7 | YES | PASS |
| 31_generic_multi | 257 | 13.8 | 4 | 8 | YES | PASS |
| 32_generic_enum | 203 | 11.5 | 1 | 7 | YES | PASS |
| 33_break_continue | 413 | 18.0 | 5 | 9 | YES | PASS |
| 34_file_io | 285 | 16.0 | 1 | 8 | YES | PASS |
| 35_stdin | 217 | 12.4 | 1 | 8 | YES | PASS |
| 36_crypto | 246 | 13.8 | 1 | 8 | YES | PASS |
| 37_regex | 257 | 14.5 | 1 | 8 | YES | PASS |
| 38_http | 208 | 11.9 | 1 | 8 | YES | PASS |
| 39_gpu_detect | 235 | 13.1 | 1 | 7 | YES | PASS |
| 40_gpu_tensor | 406 | 20.9 | 1 | 8 | YES | PASS |
| 41_module_let | 206 | 11.5 | 2 | 7 | YES | PASS |
| 42_module_let_string | 209 | 11.7 | 2 | 7 | YES | PASS |
| 43_module_let_math | 213 | 11.8 | 2 | 7 | YES | PASS |
| 45_ffi_bind | 241 | 12.4 | 3 | 8 | YES | PASS |
| 47_try_operator | 344 | 17.2 | 4 | 8 | YES | PASS |
| 48_match_nested_exhaustive | 437 | 21.6 | 3 | 8 | YES | PASS |
| 49_match_guards | 264 | 14.1 | 2 | 7 | YES | PASS |
| 49_tensor_literal | 469 | 23.7 | 1 | 8 | YES | PASS |
| 50_match_or_patterns | 282 | 15.0 | 2 | 8 | YES | PASS |
| 50_tensor_indexing | 441 | 22.4 | 1 | 7 | YES | PASS |
| 51_tensor_broadcast | 453 | 22.6 | 1 | 8 | YES | PASS |
| 52_tensor_slicing | 448 | 22.8 | 1 | 8 | YES | PASS |
| 53_linear_regression | 375 | 19.0 | 1 | 8 | YES | PASS |
| 54_const_basic | 212 | 12.1 | 1 | 7 | YES | PASS |
| 55_async_basic | 254 | 13.5 | 2 | 6 | YES | PASS |
| 56_async_await | 333 | 16.4 | 3 | 8 | YES | PASS |
| 57_real_await | 489 | 22.2 | 5 | 8 | YES | PASS |
| 58_async_file_io | 416 | 19.4 | 4 | 8 | YES | PASS |
| 58_const_scope | 245 | 12.9 | 2 | 8 | YES | PASS |
| 59_async_fanout | 1042 | 43.2 | 12 | 8 | YES | PASS |
| 62_list_output | 375 | 20.0 | 3 | 8 | YES | PASS |
| 63_else_sino | 301 | 14.9 | 3 | 8 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 4 | - | FAIL |
| 65_list_int_indexing | 373 | 19.3 | 1 | 7 | YES | PASS |
| 66_qualified_type_ref | 232 | 12.7 | 2 | 8 | YES | PASS |
| **Total** | | | | **1161** | **64/66** | **64/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 642 | 147 | 4.4x |
| 02_arithmetic | 7 | 211 | 0.0x |
| 03_function | 9 | 166 | 0.1x |
| 04_if_else | 4 | 127 | 0.0x |
| 05_for_loop | 6 | 36 | 0.2x |
| 06_struct | 5 | 12 | 0.5x |
| 07_enum_match | 13 | 14 | 0.9x |
| 08_list | 7 | 17 | 0.4x |
| 09_string_methods | 5 | 9 | 0.5x |
| 10_result | 6 | 9 | 0.7x |
| 11_closure | 4 | 7 | 0.5x |
| 12_while | 4 | 7 | 0.5x |
| 13_fib | 4 | 8 | 0.5x |
| 14_nested_struct | 4 | 7 | 0.6x |
| 15_multifunction | 5 | 7 | 0.7x |
| 16_string_escape | 4 | 6 | 0.6x |
| 17_option | 6 | 7 | 0.8x |
| 18_method_chain | 4 | 7 | 0.6x |
| 19_nested_match | 6 | 7 | 0.8x |
| 20_recursion | 4 | 8 | 0.6x |
| 21_list_ops | 6 | 8 | 0.7x |
| 22_string_builder | 6 | 8 | 0.8x |
| 23_multi_return | 7 | 9 | 0.8x |
| 24_enum_methods | 7 | 8 | 0.8x |
| 25_fizzbuzz | 6 | 8 | 0.7x |
| 26_generics | 7 | 7 | 0.9x |
| 27_impl | 6 | 8 | 0.7x |
| 28_traits | 7 | 8 | 0.9x |
| 29_generic_impl | 6 | 8 | 0.9x |
| 30_nested_generics | 5 | 7 | 0.6x |
| 31_generic_multi | 7 | 8 | 0.9x |
| 32_generic_enum | 5 | 7 | 0.7x |
| 33_break_continue | 8 | 9 | 0.9x |
| 34_file_io | 5 | 8 | 0.7x |
| 35_stdin | 4 | 8 | 0.6x |
| 36_crypto | 5 | 8 | 0.6x |
| 37_regex | 5 | 8 | 0.7x |
| 38_http | 5 | 8 | 0.6x |
| 39_gpu_detect | 4 | 7 | 0.6x |
| 40_gpu_tensor | 6 | 8 | 0.8x |
| 41_module_let | 4 | 7 | 0.6x |
| 42_module_let_string | 4 | 7 | 0.6x |
| 43_module_let_math | 4 | 7 | 0.6x |
| 45_ffi_bind | 5 | 8 | 0.6x |
| 47_try_operator | 6 | 8 | 0.8x |
| 48_match_nested_exhaustive | 6 | 8 | 0.8x |
| 49_match_guards | 6 | 7 | 0.8x |
| 49_tensor_literal | 10 | 8 | 1.3x |
| 50_match_or_patterns | 5 | 8 | 0.7x |
| 50_tensor_indexing | 7 | 7 | 1.0x |
| 51_tensor_broadcast | 7 | 8 | 0.9x |
| 52_tensor_slicing | 6 | 8 | 0.8x |
| 53_linear_regression | 6 | 8 | 0.8x |
| 54_const_basic | 4 | 7 | 0.6x |
| 55_async_basic | 4 | 6 | 0.6x |
| 56_async_await | 4 | 8 | 0.6x |
| 57_real_await | 6 | 8 | 0.7x |
| 58_async_file_io | 5 | 8 | 0.7x |
| 58_const_scope | 6 | 8 | 0.7x |
| 59_async_fanout | 6 | 8 | 0.7x |
| 62_list_output | 7 | 8 | 0.9x |
| 63_else_sino | 6 | 8 | 0.8x |
| 65_list_int_indexing | 6 | 7 | 0.8x |
| 66_qualified_type_ref | 5 | 8 | 0.6x |

