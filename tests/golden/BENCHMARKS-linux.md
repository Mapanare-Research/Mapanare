# Mapanare Benchmarks - Linux

Generated: 2026-05-04 02:14 UTC  
Version: 5.39.4 (`af1e34ee`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 18.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 897 | `___*____ ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 6 | ` _ _     ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 11 | `         ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `   -     ^` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `        ` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 14 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 8 | `        ` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 5 | `        ` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 7 | `         v` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 7 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 8 | `   _     ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 14 | `   _     ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 7 | `_  _    ` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 7 | `        ` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | ` __.___. ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 8 | `         v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 6 | `        ` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `        ` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 9 | `  _*     ^` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 6 | `   _     ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 7 | `         ^` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `   _    ` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `        ` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 7 | `   _    ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 7 | `   ~____` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 9 | `         v` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `   _     v` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 7 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 5 | `         ^` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `_ __    ` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `________` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 5 | `.  __. _ ^` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 6 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 6 | `   _   _ ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | `__--   _ ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 8 | ` _ ~    ` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `   _    ` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 8 | `        ` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 7 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `   -     ^` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `   _    ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 10 | `   _ _   ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 9 | `   _     ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 7 | `   *     ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 7 | `   _    ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | `   -__  ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `  __ __  v` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 26 | `         v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `   *     ^` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | ` _____ . ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `___*____ ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 8 | `         ^` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `   *     ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `        ` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `   __  . ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 10 | `   . _  ` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 14 | `  _*   _ ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 7 | `_  *    ` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | `   _    ` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | `_  _    ` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `-_ -_  _ ^` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | `        ` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `   _- _  v` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 5 | `  __  __` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 8 | `   _    ` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 6 | `   -    ` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `   *     v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 7 | `       . ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 5 | ` __*_  _ ^` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 5 | ` _ - _ . ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | `   -    ` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 6 | `  _.     ^` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 6 | `   *     ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 6 | `   *    ` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 6 | ` ._- _ _ ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 6 | ` _ _     ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `  ____._ v` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 6 | `...~____` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `   -.   ` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `__ _.   ` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `   -~_ _ ^` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `   -_  . ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 9 | `   *    ` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `   ~     ^` | PASS |
| **Total** | **1540** | **16569** | **619.7** | **143** | **1333** | **14102** | **1547** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 206 | 12.1 | 1 | 142 | YES | PASS |
| 02_arithmetic | 216 | 12.4 | 1 | 159 | YES | PASS |
| 03_function | 238 | 13.0 | 2 | 355 | YES | PASS |
| 04_if_else | 223 | 12.7 | 1 | 204 | YES | PASS |
| 05_for_loop | 239 | 13.2 | 1 | 178 | YES | PASS |
| 06_struct | 219 | 12.6 | 1 | 171 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 187 | YES | PASS |
| 08_list | 245 | 13.9 | 1 | 166 | YES | PASS |
| 09_string_methods | 229 | 13.2 | 1 | 174 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 241 | YES | PASS |
| 11_closure | 229 | 12.7 | 1 | 211 | YES | PASS |
| 12_while | 225 | 12.6 | 1 | 316 | YES | PASS |
| 13_fib | 236 | 12.8 | 2 | 342 | YES | PASS |
| 14_nested_struct | 219 | 12.6 | 1 | 446 | YES | PASS |
| 15_multifunction | 249 | 13.4 | 3 | 383 | YES | PASS |
| 16_string_escape | 225 | 13.0 | 1 | 181 | YES | PASS |
| 17_option | 308 | 15.7 | 2 | 249 | YES | PASS |
| 18_method_chain | 251 | 14.2 | 1 | 178 | YES | PASS |
| 19_nested_match | 274 | 14.4 | 2 | 280 | YES | PASS |
| 20_recursion | 242 | 13.1 | 2 | 185 | YES | PASS |
| 21_list_ops | 327 | 17.3 | 2 | 196 | YES | PASS |
| 22_string_builder | 294 | 15.7 | 2 | 218 | YES | PASS |
| 23_multi_return | 268 | 14.7 | 2 | 177 | YES | PASS |
| 24_enum_methods | 262 | 14.2 | 2 | 202 | YES | PASS |
| 25_fizzbuzz | 306 | 15.5 | 2 | 193 | YES | PASS |
| 26_generics | 286 | 14.6 | 5 | 188 | YES | PASS |
| 27_impl | 246 | 13.4 | 3 | 199 | YES | PASS |
| 28_traits | 254 | 13.7 | 3 | 217 | YES | PASS |
| 29_generic_impl | 255 | 13.9 | 3 | 193 | YES | PASS |
| 30_nested_generics | 246 | 14.2 | 1 | 246 | YES | PASS |
| 31_generic_multi | 271 | 14.7 | 4 | 207 | YES | PASS |
| 32_generic_enum | 217 | 12.5 | 1 | 160 | YES | PASS |
| 33_break_continue | 430 | 19.3 | 5 | 231 | YES | PASS |
| 34_file_io | 301 | 17.0 | 1 | 176 | YES | PASS |
| 35_stdin | 231 | 13.3 | 1 | 142 | YES | PASS |
| 36_crypto | 260 | 14.8 | 1 | 148 | YES | PASS |
| 37_regex | 271 | 15.4 | 1 | 138 | YES | PASS |
| 38_http | 222 | 12.9 | 1 | 138 | YES | PASS |
| 39_gpu_detect | 249 | 14.1 | 1 | 138 | YES | PASS |
| 40_gpu_tensor | 436 | 22.8 | 1 | 195 | YES | PASS |
| 41_module_let | 220 | 12.4 | 2 | 134 | YES | PASS |
| 42_module_let_string | 223 | 12.6 | 2 | 225 | YES | PASS |
| 43_module_let_math | 227 | 12.8 | 2 | 210 | YES | PASS |
| 45_ffi_bind | 255 | 13.3 | 3 | 187 | YES | PASS |
| 47_try_operator | 354 | 18.0 | 4 | 204 | YES | PASS |
| 48_match_nested_exhaustive | 451 | 22.6 | 3 | 202 | YES | PASS |
| 49_match_guards | 312 | 15.9 | 2 | 163 | YES | PASS |
| 49_tensor_literal | 483 | 24.6 | 1 | 160 | YES | PASS |
| 50_match_or_patterns | 296 | 15.9 | 2 | 189 | YES | PASS |
| 50_tensor_indexing | 455 | 23.3 | 1 | 183 | YES | PASS |
| 51_match_guards_and_or | 378 | 18.7 | 2 | 191 | YES | PASS |
| 51_tensor_broadcast | 467 | 23.5 | 1 | 172 | YES | PASS |
| 52_tensor_slicing | 462 | 23.7 | 1 | 174 | YES | PASS |
| 53_linear_regression | 389 | 19.9 | 1 | 217 | YES | PASS |
| 54_const_basic | 226 | 13.0 | 1 | 150 | YES | PASS |
| 55_async_basic | 268 | 14.5 | 2 | 144 | YES | PASS |
| 56_async_await | 347 | 17.4 | 3 | 160 | YES | PASS |
| 57_real_await | 503 | 23.1 | 5 | 162 | YES | PASS |
| 58_async_file_io | 430 | 20.4 | 4 | 164 | YES | PASS |
| 58_const_scope | 259 | 13.9 | 2 | 193 | YES | PASS |
| 59_async_fanout | 1056 | 44.1 | 12 | 166 | YES | PASS |
| 62_list_output | 387 | 20.9 | 3 | 206 | YES | PASS |
| 63_else_sino | 315 | 15.8 | 3 | 186 | YES | PASS |
| 64_closure_typed | 328 | 16.0 | 3 | 201 | YES | PASS |
| 65_list_int_indexing | 405 | 21.3 | 1 | 178 | YES | PASS |
| 66_qualified_type_ref | 242 | 13.4 | 2 | 211 | YES | PASS |
| 67_implicit_return_one_liner | 269 | 14.0 | 4 | 270 | YES | PASS |
| 68_terse_lambda | 318 | 15.6 | 3 | 243 | YES | PASS |
| 69_list_comp | 370 | 19.6 | 1 | 204 | YES | PASS |
| 70_list_comp_filter | 379 | 19.8 | 1 | 191 | YES | PASS |
| 71_map_comp | 267 | 14.6 | 1 | 187 | YES | PASS |
| 72_string_interp_var | 222 | 12.9 | 1 | 134 | YES | PASS |
| 73_string_interp_int | 222 | 12.8 | 1 | 133 | YES | PASS |
| 74_string_interp_float | 222 | 12.8 | 1 | 136 | YES | PASS |
| 75_string_interp_bool | 223 | 12.8 | 1 | 265 | YES | PASS |
| 76_string_interp_method | 221 | 12.7 | 1 | 179 | YES | PASS |
| 77_string_interp_arith | 221 | 12.8 | 1 | 132 | YES | PASS |
| 78_string_interp_multi | 238 | 13.5 | 1 | 189 | YES | PASS |
| 79_string_interp_mixed | 232 | 13.4 | 1 | 179 | YES | PASS |
| 80_string_interp_escaped | 206 | 12.2 | 1 | 8 | YES | PASS |
| 81_struct_shorthand | 259 | 14.3 | 1 | 25 | YES | PASS |
| 82_struct_update | 255 | 14.3 | 1 | 9 | YES | PASS |
| 83_struct_update_partial | 268 | 14.8 | 1 | 9 | YES | PASS |
| 84_let_destructure | 234 | 13.2 | 1 | 9 | YES | PASS |
| 85_let_destructure_nested | 245 | 13.7 | 1 | 9 | YES | PASS |
| 86_let_destructure_rest | 224 | 12.8 | 1 | 9 | YES | PASS |
| 87_let_destructure_mut | 238 | 13.3 | 1 | 13 | YES | PASS |
| 88_if_let | 237 | 13.1 | 1 | 25 | YES | PASS |
| 89_if_let_else | 232 | 13.0 | 1 | 8 | YES | PASS |
| 90_while_let | 240 | 13.2 | 1 | 12 | YES | PASS |
| 91_let_else | 264 | 14.1 | 2 | 12 | YES | PASS |
| 92_chained_cmp_simple | 280 | 14.8 | 2 | 8 | YES | PASS |
| 93_chained_cmp_4 | 288 | 15.0 | 2 | 8 | YES | PASS |
| 94_chained_cmp_mixed | 335 | 16.5 | 4 | 9 | YES | PASS |
| 95_chained_cmp_side_effect | 303 | 15.9 | 3 | 8 | YES | PASS |
| **Total** | | | | **15805** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 897 | 142 | 6.3x |
| 02_arithmetic | 6 | 159 | 0.0x |
| 03_function | 6 | 355 | 0.0x |
| 04_if_else | 11 | 204 | 0.1x |
| 05_for_loop | 5 | 178 | 0.0x |
| 06_struct | 6 | 171 | 0.0x |
| 07_enum_match | 14 | 187 | 0.1x |
| 08_list | 7 | 166 | 0.0x |
| 09_string_methods | 5 | 174 | 0.0x |
| 10_result | 8 | 241 | 0.0x |
| 11_closure | 5 | 211 | 0.0x |
| 12_while | 7 | 316 | 0.0x |
| 13_fib | 7 | 342 | 0.0x |
| 14_nested_struct | 8 | 446 | 0.0x |
| 15_multifunction | 14 | 383 | 0.0x |
| 16_string_escape | 7 | 181 | 0.0x |
| 17_option | 7 | 249 | 0.0x |
| 18_method_chain | 5 | 178 | 0.0x |
| 19_nested_match | 8 | 280 | 0.0x |
| 20_recursion | 6 | 185 | 0.0x |
| 21_list_ops | 6 | 196 | 0.0x |
| 22_string_builder | 9 | 218 | 0.0x |
| 23_multi_return | 6 | 177 | 0.0x |
| 24_enum_methods | 7 | 202 | 0.0x |
| 25_fizzbuzz | 6 | 193 | 0.0x |
| 26_generics | 7 | 188 | 0.0x |
| 27_impl | 6 | 199 | 0.0x |
| 28_traits | 7 | 217 | 0.0x |
| 29_generic_impl | 7 | 193 | 0.0x |
| 30_nested_generics | 7 | 246 | 0.0x |
| 31_generic_multi | 9 | 207 | 0.0x |
| 32_generic_enum | 5 | 160 | 0.0x |
| 33_break_continue | 9 | 231 | 0.0x |
| 34_file_io | 7 | 176 | 0.0x |
| 35_stdin | 5 | 142 | 0.0x |
| 36_crypto | 5 | 148 | 0.0x |
| 37_regex | 6 | 138 | 0.0x |
| 38_http | 5 | 138 | 0.0x |
| 39_gpu_detect | 6 | 138 | 0.0x |
| 40_gpu_tensor | 6 | 195 | 0.0x |
| 41_module_let | 5 | 134 | 0.0x |
| 42_module_let_string | 5 | 225 | 0.0x |
| 43_module_let_math | 8 | 210 | 0.0x |
| 45_ffi_bind | 5 | 187 | 0.0x |
| 47_try_operator | 8 | 204 | 0.0x |
| 48_match_nested_exhaustive | 7 | 202 | 0.0x |
| 49_match_guards | 6 | 163 | 0.0x |
| 49_tensor_literal | 10 | 160 | 0.1x |
| 50_match_or_patterns | 6 | 189 | 0.0x |
| 50_tensor_indexing | 8 | 183 | 0.0x |
| 51_match_guards_and_or | 7 | 191 | 0.0x |
| 51_tensor_broadcast | 10 | 172 | 0.1x |
| 52_tensor_slicing | 9 | 174 | 0.1x |
| 53_linear_regression | 7 | 217 | 0.0x |
| 54_const_basic | 7 | 150 | 0.0x |
| 55_async_basic | 5 | 144 | 0.0x |
| 56_async_await | 5 | 160 | 0.0x |
| 57_real_await | 26 | 162 | 0.2x |
| 58_async_file_io | 5 | 164 | 0.0x |
| 58_const_scope | 5 | 193 | 0.0x |
| 59_async_fanout | 7 | 166 | 0.0x |
| 62_list_output | 8 | 206 | 0.0x |
| 63_else_sino | 7 | 186 | 0.0x |
| 64_closure_typed | 8 | 201 | 0.0x |
| 65_list_int_indexing | 6 | 178 | 0.0x |
| 66_qualified_type_ref | 5 | 211 | 0.0x |
| 67_implicit_return_one_liner | 10 | 270 | 0.0x |
| 68_terse_lambda | 14 | 243 | 0.1x |
| 69_list_comp | 7 | 204 | 0.0x |
| 70_list_comp_filter | 6 | 191 | 0.0x |
| 71_map_comp | 6 | 187 | 0.0x |
| 72_string_interp_var | 4 | 134 | 0.0x |
| 73_string_interp_int | 5 | 133 | 0.0x |
| 74_string_interp_float | 4 | 136 | 0.0x |
| 75_string_interp_bool | 5 | 265 | 0.0x |
| 76_string_interp_method | 8 | 179 | 0.0x |
| 77_string_interp_arith | 6 | 132 | 0.0x |
| 78_string_interp_multi | 5 | 189 | 0.0x |
| 79_string_interp_mixed | 7 | 179 | 0.0x |
| 80_string_interp_escaped | 5 | 8 | 0.6x |
| 81_struct_shorthand | 5 | 25 | 0.2x |
| 82_struct_update | 6 | 9 | 0.6x |
| 83_struct_update_partial | 6 | 9 | 0.7x |
| 84_let_destructure | 6 | 9 | 0.6x |
| 85_let_destructure_nested | 6 | 9 | 0.7x |
| 86_let_destructure_rest | 6 | 9 | 0.6x |
| 87_let_destructure_mut | 6 | 13 | 0.4x |
| 88_if_let | 5 | 25 | 0.2x |
| 89_if_let_else | 6 | 8 | 0.8x |
| 90_while_let | 5 | 12 | 0.4x |
| 91_let_else | 5 | 12 | 0.4x |
| 92_chained_cmp_simple | 7 | 8 | 0.9x |
| 93_chained_cmp_4 | 6 | 8 | 0.8x |
| 94_chained_cmp_mixed | 9 | 9 | 1.0x |
| 95_chained_cmp_side_effect | 6 | 8 | 0.7x |

