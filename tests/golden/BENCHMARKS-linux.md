# Mapanare Benchmarks - Linux

Generated: 2026-04-26 05:01 UTC  
Version: 5.7.0 (`8dd658c`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 13.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 725 | ` _____   ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 10 | ` __     ` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `   _    ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 7 | `   _     ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 15 | `        ` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 8 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 6 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 6 | `  _._-_  v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `        ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 6 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 6 | `        ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `   ___ _ ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 6 | `  _     ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 8 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 10 | `  _      v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 7 | `        ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 6 | `        ` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 7 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 5 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `  _   .  v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `._-_____` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `  __ _~  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 6 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 7 | `  _      ^` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `._.__._. ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `_       ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 7 | `         ^` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 5 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | `         ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 7 | `       * ^` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `________ v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `._______ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `  ____   ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `.~._._._ v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 13 | `  __    ` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 6 | `         ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | ` _  __  ` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 6 | ` . _    ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `__-__.  ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `_ ___   ` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 8 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | ` _ _   _ ^` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `      ~* ^` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 7 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 6 | `_..-__.- ^` | PASS |
| **Total** | **1336** | **13033** | **490.9** | **112** | **1039** | **11069** | **1159** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 192 | 11.2 | 1 | 245 | YES | PASS |
| 02_arithmetic | 202 | 11.5 | 1 | 271 | YES | PASS |
| 03_function | 224 | 12.1 | 2 | 163 | YES | PASS |
| 04_if_else | 209 | 11.7 | 1 | 191 | YES | PASS |
| 05_for_loop | 225 | 12.3 | 1 | 243 | YES | PASS |
| 06_struct | 205 | 11.6 | 1 | 205 | YES | PASS |
| 07_enum_match | 215 | 12.0 | 1 | 172 | YES | PASS |
| 08_list | 229 | 12.8 | 1 | 173 | YES | PASS |
| 09_string_methods | 215 | 12.3 | 1 | 194 | YES | PASS |
| 10_result | 260 | 13.8 | 2 | 235 | YES | PASS |
| 11_closure | 215 | 11.8 | 1 | 157 | YES | PASS |
| 12_while | 211 | 11.7 | 1 | 153 | YES | PASS |
| 13_fib | 222 | 11.9 | 2 | 164 | YES | PASS |
| 14_nested_struct | 205 | 11.6 | 1 | 142 | YES | PASS |
| 15_multifunction | 235 | 12.4 | 3 | 180 | YES | PASS |
| 16_string_escape | 211 | 12.1 | 1 | 139 | YES | PASS |
| 17_option | 287 | 14.5 | 2 | 205 | YES | PASS |
| 18_method_chain | 237 | 13.3 | 1 | 191 | YES | PASS |
| 19_nested_match | 260 | 13.5 | 2 | 197 | YES | PASS |
| 20_recursion | 228 | 12.2 | 2 | 153 | YES | PASS |
| 21_list_ops | 311 | 16.2 | 2 | 199 | YES | PASS |
| 22_string_builder | 280 | 14.8 | 2 | 196 | YES | PASS |
| 23_multi_return | 254 | 13.7 | 2 | 191 | YES | PASS |
| 24_enum_methods | 248 | 13.3 | 2 | 156 | YES | PASS |
| 25_fizzbuzz | 292 | 14.6 | 2 | 157 | YES | PASS |
| 26_generics | 272 | 13.7 | 5 | 221 | YES | PASS |
| 27_impl | 232 | 12.5 | 3 | 240 | YES | PASS |
| 28_traits | 240 | 12.7 | 3 | 228 | YES | PASS |
| 29_generic_impl | 241 | 13.0 | 3 | 180 | YES | PASS |
| 30_nested_generics | 232 | 13.3 | 1 | 179 | YES | PASS |
| 31_generic_multi | 257 | 13.8 | 4 | 214 | YES | PASS |
| 32_generic_enum | 203 | 11.5 | 1 | 156 | YES | PASS |
| 33_break_continue | 414 | 18.2 | 5 | 223 | YES | PASS |
| 34_file_io | 285 | 16.0 | 1 | 200 | YES | PASS |
| 35_stdin | 217 | 12.4 | 1 | 165 | YES | PASS |
| 36_crypto | 246 | 13.8 | 1 | 168 | YES | PASS |
| 37_regex | 257 | 14.5 | 1 | 155 | YES | PASS |
| 38_http | 208 | 11.9 | 1 | 195 | YES | PASS |
| 39_gpu_detect | 235 | 13.1 | 1 | 199 | YES | PASS |
| 40_gpu_tensor | 414 | 21.3 | 1 | 195 | YES | PASS |
| 41_module_let | 206 | 11.5 | 2 | 141 | YES | PASS |
| 42_module_let_string | 209 | 11.7 | 2 | 8 | YES | PASS |
| 43_module_let_math | 213 | 11.8 | 2 | 169 | YES | PASS |
| 45_ffi_bind | 241 | 12.4 | 3 | 200 | YES | PASS |
| 47_try_operator | 344 | 17.2 | 4 | 221 | YES | PASS |
| 48_match_nested_exhaustive | 437 | 21.6 | 3 | 164 | YES | PASS |
| 49_match_guards | 264 | 14.1 | 2 | 144 | YES | PASS |
| 49_tensor_literal | 469 | 23.7 | 1 | 162 | YES | PASS |
| 50_match_or_patterns | 282 | 15.0 | 2 | 176 | YES | PASS |
| 50_tensor_indexing | 441 | 22.4 | 1 | 163 | YES | PASS |
| 51_match_guards_and_or | 333 | 16.7 | 2 | 187 | YES | PASS |
| 51_tensor_broadcast | 453 | 22.6 | 1 | 141 | YES | PASS |
| 52_tensor_slicing | 448 | 22.8 | 1 | 185 | YES | PASS |
| 53_linear_regression | 375 | 19.0 | 1 | 201 | YES | PASS |
| 54_const_basic | 212 | 12.1 | 1 | 151 | YES | PASS |
| 55_async_basic | 254 | 13.5 | 2 | 287 | YES | PASS |
| 56_async_await | 333 | 16.4 | 3 | 173 | YES | PASS |
| 57_real_await | 489 | 22.2 | 5 | 169 | YES | PASS |
| 58_async_file_io | 416 | 19.4 | 4 | 200 | YES | PASS |
| 58_const_scope | 245 | 12.9 | 2 | 181 | YES | PASS |
| 59_async_fanout | 1042 | 43.2 | 12 | 193 | YES | PASS |
| 62_list_output | 371 | 19.9 | 3 | 198 | YES | PASS |
| 63_else_sino | 301 | 14.9 | 3 | 142 | YES | PASS |
| 64_closure_typed | 314 | 15.1 | 3 | 191 | YES | PASS |
| 65_list_int_indexing | 389 | 20.2 | 1 | 206 | YES | PASS |
| 66_qualified_type_ref | 228 | 12.5 | 2 | 172 | YES | PASS |
| **Total** | | | | **12112** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 725 | 245 | 3.0x |
| 02_arithmetic | 10 | 271 | 0.0x |
| 03_function | 7 | 163 | 0.0x |
| 04_if_else | 6 | 191 | 0.0x |
| 05_for_loop | 7 | 243 | 0.0x |
| 06_struct | 7 | 205 | 0.0x |
| 07_enum_match | 15 | 172 | 0.1x |
| 08_list | 7 | 173 | 0.0x |
| 09_string_methods | 5 | 194 | 0.0x |
| 10_result | 8 | 235 | 0.0x |
| 11_closure | 4 | 157 | 0.0x |
| 12_while | 4 | 153 | 0.0x |
| 13_fib | 5 | 164 | 0.0x |
| 14_nested_struct | 5 | 142 | 0.0x |
| 15_multifunction | 6 | 180 | 0.0x |
| 16_string_escape | 5 | 139 | 0.0x |
| 17_option | 6 | 205 | 0.0x |
| 18_method_chain | 6 | 191 | 0.0x |
| 19_nested_match | 7 | 197 | 0.0x |
| 20_recursion | 6 | 153 | 0.0x |
| 21_list_ops | 6 | 199 | 0.0x |
| 22_string_builder | 6 | 196 | 0.0x |
| 23_multi_return | 6 | 191 | 0.0x |
| 24_enum_methods | 6 | 156 | 0.0x |
| 25_fizzbuzz | 6 | 157 | 0.0x |
| 26_generics | 8 | 221 | 0.0x |
| 27_impl | 7 | 240 | 0.0x |
| 28_traits | 10 | 228 | 0.0x |
| 29_generic_impl | 6 | 180 | 0.0x |
| 30_nested_generics | 7 | 179 | 0.0x |
| 31_generic_multi | 8 | 214 | 0.0x |
| 32_generic_enum | 6 | 156 | 0.0x |
| 33_break_continue | 8 | 223 | 0.0x |
| 34_file_io | 7 | 200 | 0.0x |
| 35_stdin | 5 | 165 | 0.0x |
| 36_crypto | 5 | 168 | 0.0x |
| 37_regex | 5 | 155 | 0.0x |
| 38_http | 5 | 195 | 0.0x |
| 39_gpu_detect | 6 | 199 | 0.0x |
| 40_gpu_tensor | 7 | 195 | 0.0x |
| 41_module_let | 5 | 141 | 0.0x |
| 42_module_let_string | 5 | 8 | 0.6x |
| 43_module_let_math | 5 | 169 | 0.0x |
| 45_ffi_bind | 7 | 200 | 0.0x |
| 47_try_operator | 7 | 221 | 0.0x |
| 48_match_nested_exhaustive | 6 | 164 | 0.0x |
| 49_match_guards | 5 | 144 | 0.0x |
| 49_tensor_literal | 10 | 162 | 0.1x |
| 50_match_or_patterns | 7 | 176 | 0.0x |
| 50_tensor_indexing | 8 | 163 | 0.0x |
| 51_match_guards_and_or | 7 | 187 | 0.0x |
| 51_tensor_broadcast | 8 | 141 | 0.1x |
| 52_tensor_slicing | 7 | 185 | 0.0x |
| 53_linear_regression | 7 | 201 | 0.0x |
| 54_const_basic | 5 | 151 | 0.0x |
| 55_async_basic | 13 | 287 | 0.0x |
| 56_async_await | 6 | 173 | 0.0x |
| 57_real_await | 5 | 169 | 0.0x |
| 58_async_file_io | 6 | 200 | 0.0x |
| 58_const_scope | 6 | 181 | 0.0x |
| 59_async_fanout | 7 | 193 | 0.0x |
| 62_list_output | 8 | 198 | 0.0x |
| 63_else_sino | 6 | 142 | 0.0x |
| 64_closure_typed | 8 | 191 | 0.0x |
| 65_list_int_indexing | 7 | 206 | 0.0x |
| 66_qualified_type_ref | 6 | 172 | 0.0x |

