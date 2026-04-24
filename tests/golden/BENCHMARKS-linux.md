# Mapanare Benchmarks - Linux

Generated: 2026-04-24 15:30 UTC  
Version: 5.6.3 (`578595d`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 13.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 742 | `____ ___ ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 11 | `      __` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 8 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 7 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 7 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 6 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 12 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 7 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `_.._..._ v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 8 | `         v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 6 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 7 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `_ _____. ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 6 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 9 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         ^` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 10 | `         ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 11 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `  _      ^` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 5 | `   _     v` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 10 | `        ` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 8 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 5 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 9 | `_   ____` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 6 | ` _. _. _ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `__..____` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 7 | `        ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 6 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 6 | `-._~.-.- ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 6 | `_ _ __ _ ^` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 6 | `  _     ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 8 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 7 | `        ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 12 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | ` _       v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 9 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 5 | ` . _    ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `_-______ ^` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 9 | `_..___..` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `       _ ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 6 | `--..--..` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | ` ___ _ _ ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | ` _   ___` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `___..___` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 6 | `_.._.__. ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 9 | `._-_..._ v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 8 | `__._.___ ^` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 8 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 8 | `___ ..__` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `    __  ` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 7 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `~.-.~-.* ^` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **1206** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 192 | 11.2 | 1 | 221 | YES | PASS |
| 02_arithmetic | 202 | 11.5 | 1 | 240 | YES | PASS |
| 03_function | 224 | 12.1 | 2 | 183 | YES | PASS |
| 04_if_else | 209 | 11.7 | 1 | 223 | YES | PASS |
| 05_for_loop | 225 | 12.3 | 1 | 177 | YES | PASS |
| 06_struct | 207 | 11.7 | 1 | 161 | YES | PASS |
| 07_enum_match | 215 | 12.0 | 1 | 162 | YES | PASS |
| 08_list | 231 | 12.8 | 1 | 167 | YES | PASS |
| 09_string_methods | 215 | 12.3 | 1 | 179 | YES | PASS |
| 10_result | 260 | 13.8 | 2 | 185 | YES | PASS |
| 11_closure | 227 | 12.2 | 1 | 151 | YES | PASS |
| 12_while | 211 | 11.7 | 1 | 137 | YES | PASS |
| 13_fib | 222 | 11.9 | 2 | 213 | YES | PASS |
| 14_nested_struct | 207 | 11.7 | 1 | 207 | YES | PASS |
| 15_multifunction | 235 | 12.4 | 3 | 195 | YES | PASS |
| 16_string_escape | 211 | 12.1 | 1 | 140 | YES | PASS |
| 17_option | 287 | 14.5 | 2 | 166 | YES | PASS |
| 18_method_chain | 237 | 13.3 | 1 | 175 | YES | PASS |
| 19_nested_match | 260 | 13.5 | 2 | 196 | YES | PASS |
| 20_recursion | 228 | 12.2 | 2 | 178 | YES | PASS |
| 21_list_ops | 310 | 16.1 | 2 | 170 | YES | PASS |
| 22_string_builder | 280 | 14.8 | 2 | 170 | YES | PASS |
| 23_multi_return | 256 | 13.8 | 2 | 155 | YES | PASS |
| 24_enum_methods | 248 | 13.3 | 2 | 198 | YES | PASS |
| 25_fizzbuzz | 292 | 14.6 | 2 | 204 | YES | PASS |
| 26_generics | 272 | 13.7 | 5 | 159 | YES | PASS |
| 27_impl | 234 | 12.6 | 3 | 171 | YES | PASS |
| 28_traits | 242 | 12.8 | 3 | 316 | YES | PASS |
| 29_generic_impl | 241 | 12.9 | 3 | 163 | YES | PASS |
| 30_nested_generics | 232 | 13.3 | 1 | 144 | YES | PASS |
| 31_generic_multi | 257 | 13.8 | 4 | 165 | YES | PASS |
| 32_generic_enum | 203 | 11.5 | 1 | 155 | YES | PASS |
| 33_break_continue | 413 | 18.0 | 5 | 215 | YES | PASS |
| 34_file_io | 285 | 16.0 | 1 | 153 | YES | PASS |
| 35_stdin | 217 | 12.4 | 1 | 167 | YES | PASS |
| 36_crypto | 246 | 13.8 | 1 | 178 | YES | PASS |
| 37_regex | 257 | 14.5 | 1 | 171 | YES | PASS |
| 38_http | 208 | 11.9 | 1 | 163 | YES | PASS |
| 39_gpu_detect | 235 | 13.1 | 1 | 150 | YES | PASS |
| 40_gpu_tensor | 406 | 20.9 | 1 | 178 | YES | PASS |
| 41_module_let | 206 | 11.5 | 2 | 155 | YES | PASS |
| 42_module_let_string | 209 | 11.7 | 2 | 148 | YES | PASS |
| 43_module_let_math | 213 | 11.8 | 2 | 139 | YES | PASS |
| 45_ffi_bind | 241 | 12.4 | 3 | 158 | YES | PASS |
| 47_try_operator | 344 | 17.2 | 4 | 188 | YES | PASS |
| 48_match_nested_exhaustive | 437 | 21.6 | 3 | 185 | YES | PASS |
| 49_match_guards | 264 | 14.1 | 2 | 205 | YES | PASS |
| 49_tensor_literal | 444 | 22.7 | 1 | 156 | YES | PASS |
| 50_match_or_patterns | 281 | 14.9 | 2 | 187 | YES | PASS |
| 50_tensor_indexing | 416 | 21.4 | 1 | 192 | YES | PASS |
| 51_tensor_broadcast | 398 | 20.4 | 1 | 167 | YES | PASS |
| 52_tensor_slicing | 418 | 21.6 | 1 | 162 | YES | PASS |
| 53_linear_regression | 337 | 17.5 | 1 | 171 | YES | PASS |
| 54_const_basic | 212 | 12.1 | 1 | 152 | YES | PASS |
| 55_async_basic | 254 | 13.5 | 2 | 168 | YES | PASS |
| 56_async_await | 333 | 16.4 | 3 | 169 | YES | PASS |
| 57_real_await | 489 | 22.2 | 5 | 202 | YES | PASS |
| 58_async_file_io | 416 | 19.4 | 4 | 279 | YES | PASS |
| 58_const_scope | 245 | 12.9 | 2 | 190 | YES | PASS |
| 59_async_fanout | 1042 | 43.2 | 12 | 162 | YES | PASS |
| 62_list_output | 374 | 19.9 | 3 | 159 | YES | PASS |
| 63_else_sino | 301 | 14.9 | 3 | 165 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 38 | - | FAIL |
| 65_list_int_indexing | 373 | 19.3 | 1 | 166 | YES | PASS |
| 66_qualified_type_ref | 232 | 12.7 | 2 | 139 | YES | PASS |
| **Total** | | | | **11402** | **64/66** | **64/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 742 | 221 | 3.4x |
| 02_arithmetic | 11 | 240 | 0.0x |
| 03_function | 7 | 183 | 0.0x |
| 04_if_else | 8 | 223 | 0.0x |
| 05_for_loop | 7 | 177 | 0.0x |
| 06_struct | 7 | 161 | 0.0x |
| 07_enum_match | 13 | 162 | 0.1x |
| 08_list | 7 | 167 | 0.0x |
| 09_string_methods | 5 | 179 | 0.0x |
| 10_result | 7 | 185 | 0.0x |
| 11_closure | 6 | 151 | 0.0x |
| 12_while | 5 | 137 | 0.0x |
| 13_fib | 5 | 213 | 0.0x |
| 14_nested_struct | 7 | 207 | 0.0x |
| 15_multifunction | 12 | 195 | 0.1x |
| 16_string_escape | 5 | 140 | 0.0x |
| 17_option | 7 | 166 | 0.0x |
| 18_method_chain | 5 | 175 | 0.0x |
| 19_nested_match | 8 | 196 | 0.0x |
| 20_recursion | 6 | 178 | 0.0x |
| 21_list_ops | 7 | 170 | 0.0x |
| 22_string_builder | 6 | 170 | 0.0x |
| 23_multi_return | 6 | 155 | 0.0x |
| 24_enum_methods | 6 | 198 | 0.0x |
| 25_fizzbuzz | 9 | 204 | 0.0x |
| 26_generics | 8 | 159 | 0.0x |
| 27_impl | 6 | 171 | 0.0x |
| 28_traits | 10 | 316 | 0.0x |
| 29_generic_impl | 11 | 163 | 0.1x |
| 30_nested_generics | 6 | 144 | 0.0x |
| 31_generic_multi | 8 | 165 | 0.0x |
| 32_generic_enum | 5 | 155 | 0.0x |
| 33_break_continue | 10 | 215 | 0.0x |
| 34_file_io | 8 | 153 | 0.0x |
| 35_stdin | 5 | 167 | 0.0x |
| 36_crypto | 9 | 178 | 0.1x |
| 37_regex | 6 | 171 | 0.0x |
| 38_http | 5 | 163 | 0.0x |
| 39_gpu_detect | 5 | 150 | 0.0x |
| 40_gpu_tensor | 7 | 178 | 0.0x |
| 41_module_let | 6 | 155 | 0.0x |
| 42_module_let_string | 6 | 148 | 0.0x |
| 43_module_let_math | 6 | 139 | 0.0x |
| 45_ffi_bind | 6 | 158 | 0.0x |
| 47_try_operator | 8 | 188 | 0.0x |
| 48_match_nested_exhaustive | 8 | 185 | 0.0x |
| 49_match_guards | 7 | 205 | 0.0x |
| 49_tensor_literal | 12 | 156 | 0.1x |
| 50_match_or_patterns | 7 | 187 | 0.0x |
| 50_tensor_indexing | 9 | 192 | 0.0x |
| 51_tensor_broadcast | 8 | 167 | 0.1x |
| 52_tensor_slicing | 9 | 162 | 0.1x |
| 53_linear_regression | 7 | 171 | 0.0x |
| 54_const_basic | 6 | 152 | 0.0x |
| 55_async_basic | 5 | 168 | 0.0x |
| 56_async_await | 5 | 169 | 0.0x |
| 57_real_await | 6 | 202 | 0.0x |
| 58_async_file_io | 6 | 279 | 0.0x |
| 58_const_scope | 9 | 190 | 0.0x |
| 59_async_fanout | 8 | 162 | 0.0x |
| 62_list_output | 8 | 159 | 0.1x |
| 63_else_sino | 8 | 165 | 0.0x |
| 65_list_int_indexing | 7 | 166 | 0.0x |
| 66_qualified_type_ref | 5 | 139 | 0.0x |

