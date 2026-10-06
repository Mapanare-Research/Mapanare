# Mapanare Benchmarks - Linux

Generated: 2026-05-09 06:40 UTC  
Version: 5.51.0 (`48bbbb3a`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 22.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1007 | `_-_.-.._ v` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 8 | `     _   v` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 5 | `         v` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 9 | `        ` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 6 | `        ` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 8 | `        ` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 14 | `         v` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 100_result_complex_destructure | 72 | 819 | 37.2 | 3 | 101 | 602 | 13 | `_..._*..` | PASS |
| 101_match_rewrap_propagation | 60 | 340 | 18.4 | 4 | 23 | 338 | 10 | `   _ * _ ^` | PASS |
| 102_nested_15arm_match | 75 | 577 | 23.9 | 5 | 40 | 428 | 13 | `  .  --. v` | PASS |
| 103_variant_name_collision | 72 | 421 | 16.3 | 3 | 38 | 396 | 12 | `*  _ - . ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 7 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 7 | `        ` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 6 | `         v` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | `_       ` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 8 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | ` _.._..- ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 8 | `  _    _ ^` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 7 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 5 | `_     _  v` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 7 | `         ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `        ` | PASS |
| 26_generics | 25 | 116 | 3.9 | 1 | 12 | 63 | 10 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 8 | `         ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 7 | `         ^` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 6 | ` _       v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `~     _  v` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 10 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 7 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 5 | `         v` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 6 | `     __  v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_. ._.__` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `  . _.  ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | ` _      ` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 4 | `_ _..__. ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | ` . _ _  ` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `     _  ` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 31 | `         ^` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 6 | `         ^` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 7 | `         ^` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `        ` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `         v` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 10 | `  _     ` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `        ` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 10 | `   _     ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 9 | `   _  .  v` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `   _    ` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `        ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | ` _ _ _   ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `__ ___  ` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 6 | `         v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 8 | `     _   ^` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `_ _ _._  v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `         ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 9 | `        ` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 6 | `     _   ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 9 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 7 | `        ` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 7 | `   _ _  ` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `    __  ` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 11 | `_.______` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `________` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | `     ___` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 8 | ` __  __  v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 5 | ` ___ -__` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` .. _._. ^` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` . _ . _ ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 5 | `  _  -_  v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | `.____. _ ^` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `_.___.._ v` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `  __ . . ^` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 7 | ` __._. . ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `     _   ^` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 8 | ` __ ..__` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 7 | ` .  ._._ v` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 8 | `  _ _-  ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 6 | `_ _  _.  v` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `        ` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 6 | `_    _  ` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `  _  _ _ ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `  _  _ _ ^` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `     .  ` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 6 | `- .- . - ^` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `_    .  ` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `  _  ___` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `.  _ .  ` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | `    _.__` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | ` ~  _.  ` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 24 | ` _  _.__` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 10 | `_-* -. _ ^` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 11 | ` _._ -*  v` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 10 | `  _ *.__ ^` | PASS |
| **Total** | **2118** | **22755** | **886.8** | **162** | **1791** | **21005** | **1745** | | **103/103** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 211 | 12.4 | 1 | 139 | YES | PASS |
| 02_arithmetic | 221 | 12.7 | 1 | 147 | YES | PASS |
| 03_function | 243 | 13.3 | 2 | 171 | YES | PASS |
| 04_if_else | 228 | 13.0 | 1 | 246 | YES | PASS |
| 05_for_loop | 244 | 13.5 | 1 | 226 | YES | PASS |
| 06_struct | 224 | 12.9 | 1 | 197 | YES | PASS |
| 07_enum_match | 232 | 13.1 | 1 | 157 | YES | PASS |
| 08_list | 250 | 14.2 | 1 | 186 | YES | PASS |
| 09_string_methods | 234 | 13.5 | 1 | 197 | YES | PASS |
| 100_result_complex_destructure | 521 | 26.8 | 3 | 225 | YES | PASS |
| 101_match_rewrap_propagation | 436 | 23.8 | 5 | 197 | YES | PASS |
| 102_nested_15arm_match | 560 | 28.5 | 5 | 216 | YES | PASS |
| 103_variant_name_collision | 431 | 21.7 | 3 | 260 | YES | PASS |
| 10_result | 277 | 14.9 | 2 | 253 | YES | PASS |
| 11_closure | 234 | 13.0 | 1 | 244 | YES | PASS |
| 12_while | 230 | 12.9 | 1 | 180 | YES | PASS |
| 13_fib | 241 | 13.1 | 2 | 197 | YES | PASS |
| 14_nested_struct | 224 | 12.9 | 1 | 172 | YES | PASS |
| 15_multifunction | 254 | 13.7 | 3 | 187 | YES | PASS |
| 16_string_escape | 230 | 13.3 | 1 | 172 | YES | PASS |
| 17_option | 313 | 16.0 | 2 | 227 | YES | PASS |
| 18_method_chain | 256 | 14.5 | 1 | 166 | YES | PASS |
| 19_nested_match | 279 | 14.7 | 2 | 190 | YES | PASS |
| 20_recursion | 247 | 13.4 | 2 | 192 | YES | PASS |
| 21_list_ops | 332 | 17.6 | 2 | 189 | YES | PASS |
| 22_string_builder | 299 | 16.0 | 2 | 220 | YES | PASS |
| 23_multi_return | 273 | 15.0 | 2 | 185 | YES | PASS |
| 24_enum_methods | 267 | 14.5 | 2 | 205 | YES | PASS |
| 25_fizzbuzz | 311 | 15.8 | 2 | 226 | YES | PASS |
| 26_generics | 291 | 14.9 | 5 | 272 | YES | PASS |
| 27_impl | 251 | 13.7 | 3 | 195 | YES | PASS |
| 28_traits | 259 | 14.0 | 3 | 187 | YES | PASS |
| 29_generic_impl | 260 | 14.2 | 3 | 183 | YES | PASS |
| 30_nested_generics | 251 | 14.5 | 1 | 148 | YES | PASS |
| 31_generic_multi | 276 | 15.0 | 4 | 211 | YES | PASS |
| 32_generic_enum | 222 | 12.8 | 1 | 161 | YES | PASS |
| 33_break_continue | 435 | 19.6 | 5 | 261 | YES | PASS |
| 34_file_io | 306 | 17.3 | 1 | 215 | YES | PASS |
| 35_stdin | 236 | 13.6 | 1 | 170 | YES | PASS |
| 36_crypto | 265 | 15.0 | 1 | 205 | YES | PASS |
| 37_regex | 276 | 15.7 | 1 | 149 | YES | PASS |
| 38_http | 227 | 13.2 | 1 | 150 | YES | PASS |
| 39_gpu_detect | 254 | 14.4 | 1 | 159 | YES | PASS |
| 40_gpu_tensor | 441 | 23.1 | 1 | 206 | YES | PASS |
| 41_module_let | 225 | 12.7 | 2 | 153 | YES | PASS |
| 42_module_let_string | 228 | 12.9 | 2 | 131 | YES | PASS |
| 43_module_let_math | 232 | 13.1 | 2 | 129 | YES | PASS |
| 45_ffi_bind | 260 | 13.6 | 3 | 178 | YES | PASS |
| 47_try_operator | 359 | 18.2 | 4 | 195 | YES | PASS |
| 48_match_nested_exhaustive | 456 | 22.9 | 3 | 232 | YES | PASS |
| 49_match_guards | 317 | 16.2 | 2 | 216 | YES | PASS |
| 49_tensor_literal | 488 | 24.9 | 1 | 175 | YES | PASS |
| 50_match_or_patterns | 301 | 16.2 | 2 | 186 | YES | PASS |
| 50_tensor_indexing | 460 | 23.6 | 1 | 156 | YES | PASS |
| 51_match_guards_and_or | 383 | 19.0 | 2 | 196 | YES | PASS |
| 51_tensor_broadcast | 472 | 23.8 | 1 | 181 | YES | PASS |
| 52_tensor_slicing | 470 | 24.1 | 1 | 189 | YES | PASS |
| 53_linear_regression | 394 | 20.2 | 1 | 184 | YES | PASS |
| 54_const_basic | 231 | 13.3 | 1 | 148 | YES | PASS |
| 55_async_basic | 273 | 14.8 | 2 | 172 | YES | PASS |
| 56_async_await | 352 | 17.7 | 3 | 184 | YES | PASS |
| 57_real_await | 508 | 23.4 | 5 | 204 | YES | PASS |
| 58_async_file_io | 435 | 20.7 | 4 | 284 | YES | PASS |
| 58_const_scope | 264 | 14.2 | 2 | 182 | YES | PASS |
| 59_async_fanout | 1061 | 44.4 | 12 | 179 | YES | PASS |
| 62_list_output | 392 | 21.2 | 3 | 169 | YES | PASS |
| 63_else_sino | 320 | 16.1 | 3 | 168 | YES | PASS |
| 64_closure_typed | 333 | 16.3 | 3 | 198 | YES | PASS |
| 65_list_int_indexing | 410 | 21.6 | 1 | 220 | YES | PASS |
| 66_qualified_type_ref | 247 | 13.7 | 2 | 182 | YES | PASS |
| 67_implicit_return_one_liner | 274 | 14.3 | 4 | 167 | YES | PASS |
| 68_terse_lambda | 323 | 15.9 | 3 | 200 | YES | PASS |
| 69_list_comp | 375 | 19.9 | 1 | 199 | YES | PASS |
| 70_list_comp_filter | 384 | 20.1 | 1 | 249 | YES | PASS |
| 71_map_comp | 272 | 14.9 | 1 | 246 | YES | PASS |
| 72_string_interp_var | 227 | 13.2 | 1 | 158 | YES | PASS |
| 73_string_interp_int | 227 | 13.1 | 1 | 184 | YES | PASS |
| 74_string_interp_float | 227 | 13.1 | 1 | 143 | YES | PASS |
| 75_string_interp_bool | 228 | 13.1 | 1 | 138 | YES | PASS |
| 76_string_interp_method | 226 | 13.0 | 1 | 176 | YES | PASS |
| 77_string_interp_arith | 226 | 13.1 | 1 | 153 | YES | PASS |
| 78_string_interp_multi | 243 | 13.8 | 1 | 154 | YES | PASS |
| 79_string_interp_mixed | 237 | 13.7 | 1 | 149 | YES | PASS |
| 80_string_interp_escaped | 211 | 12.5 | 1 | 131 | YES | PASS |
| 81_struct_shorthand | 264 | 14.6 | 1 | 269 | YES | PASS |
| 82_struct_update | 260 | 14.6 | 1 | 239 | YES | PASS |
| 83_struct_update_partial | 273 | 15.1 | 1 | 245 | YES | PASS |
| 84_let_destructure | 239 | 13.5 | 1 | 165 | YES | PASS |
| 85_let_destructure_nested | 250 | 14.0 | 1 | 175 | YES | PASS |
| 86_let_destructure_rest | 229 | 13.1 | 1 | 183 | YES | PASS |
| 87_let_destructure_mut | 243 | 13.6 | 1 | 160 | YES | PASS |
| 88_if_let | 242 | 13.4 | 1 | 155 | YES | PASS |
| 89_if_let_else | 237 | 13.3 | 1 | 170 | YES | PASS |
| 90_while_let | 245 | 13.4 | 1 | 180 | YES | PASS |
| 91_let_else | 269 | 14.4 | 2 | 166 | YES | PASS |
| 92_chained_cmp_simple | 285 | 15.1 | 2 | 177 | YES | PASS |
| 93_chained_cmp_4 | 293 | 15.3 | 2 | 161 | YES | PASS |
| 94_chained_cmp_mixed | 340 | 16.8 | 4 | 177 | YES | PASS |
| 95_chained_cmp_side_effect | 308 | 16.2 | 3 | 209 | YES | PASS |
| 96_tensor_reshape | 800 | 39.4 | 1 | 220 | YES | PASS |
| 97_tensor_view_aliasing | 546 | 27.4 | 1 | 166 | YES | PASS |
| 98_tensor_stepped_slice | 618 | 30.7 | 1 | 188 | YES | PASS |
| 99_tensor_reshape_aliased | 596 | 29.7 | 1 | 197 | YES | PASS |
| **Total** | | | | **19478** | **103/103** | **103/103** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1007 | 139 | 7.2x |
| 02_arithmetic | 8 | 147 | 0.1x |
| 03_function | 5 | 171 | 0.0x |
| 04_if_else | 9 | 246 | 0.0x |
| 05_for_loop | 6 | 226 | 0.0x |
| 06_struct | 8 | 197 | 0.0x |
| 07_enum_match | 14 | 157 | 0.1x |
| 08_list | 7 | 186 | 0.0x |
| 09_string_methods | 5 | 197 | 0.0x |
| 100_result_complex_destructure | 13 | 225 | 0.1x |
| 101_match_rewrap_propagation | 10 | 197 | 0.1x |
| 102_nested_15arm_match | 13 | 216 | 0.1x |
| 103_variant_name_collision | 12 | 260 | 0.0x |
| 10_result | 7 | 253 | 0.0x |
| 11_closure | 7 | 244 | 0.0x |
| 12_while | 5 | 180 | 0.0x |
| 13_fib | 6 | 197 | 0.0x |
| 14_nested_struct | 6 | 172 | 0.0x |
| 15_multifunction | 6 | 187 | 0.0x |
| 16_string_escape | 5 | 172 | 0.0x |
| 17_option | 8 | 227 | 0.0x |
| 18_method_chain | 5 | 166 | 0.0x |
| 19_nested_match | 8 | 190 | 0.0x |
| 20_recursion | 5 | 192 | 0.0x |
| 21_list_ops | 7 | 189 | 0.0x |
| 22_string_builder | 5 | 220 | 0.0x |
| 23_multi_return | 7 | 185 | 0.0x |
| 24_enum_methods | 5 | 205 | 0.0x |
| 25_fizzbuzz | 6 | 226 | 0.0x |
| 26_generics | 10 | 272 | 0.0x |
| 27_impl | 8 | 195 | 0.0x |
| 28_traits | 7 | 187 | 0.0x |
| 29_generic_impl | 7 | 183 | 0.0x |
| 30_nested_generics | 6 | 148 | 0.0x |
| 31_generic_multi | 7 | 211 | 0.0x |
| 32_generic_enum | 5 | 161 | 0.0x |
| 33_break_continue | 10 | 261 | 0.0x |
| 34_file_io | 7 | 215 | 0.0x |
| 35_stdin | 5 | 170 | 0.0x |
| 36_crypto | 6 | 205 | 0.0x |
| 37_regex | 5 | 149 | 0.0x |
| 38_http | 4 | 150 | 0.0x |
| 39_gpu_detect | 4 | 159 | 0.0x |
| 40_gpu_tensor | 7 | 206 | 0.0x |
| 41_module_let | 5 | 153 | 0.0x |
| 42_module_let_string | 4 | 131 | 0.0x |
| 43_module_let_math | 5 | 129 | 0.0x |
| 45_ffi_bind | 5 | 178 | 0.0x |
| 47_try_operator | 31 | 195 | 0.2x |
| 48_match_nested_exhaustive | 6 | 232 | 0.0x |
| 49_match_guards | 7 | 216 | 0.0x |
| 49_tensor_literal | 10 | 175 | 0.1x |
| 50_match_or_patterns | 6 | 186 | 0.0x |
| 50_tensor_indexing | 10 | 156 | 0.1x |
| 51_match_guards_and_or | 7 | 196 | 0.0x |
| 51_tensor_broadcast | 10 | 181 | 0.1x |
| 52_tensor_slicing | 9 | 189 | 0.0x |
| 53_linear_regression | 6 | 184 | 0.0x |
| 54_const_basic | 5 | 148 | 0.0x |
| 55_async_basic | 5 | 172 | 0.0x |
| 56_async_await | 5 | 184 | 0.0x |
| 57_real_await | 6 | 204 | 0.0x |
| 58_async_file_io | 8 | 284 | 0.0x |
| 58_const_scope | 6 | 182 | 0.0x |
| 59_async_fanout | 7 | 179 | 0.0x |
| 62_list_output | 9 | 169 | 0.1x |
| 63_else_sino | 6 | 168 | 0.0x |
| 64_closure_typed | 9 | 198 | 0.0x |
| 65_list_int_indexing | 7 | 220 | 0.0x |
| 66_qualified_type_ref | 7 | 182 | 0.0x |
| 67_implicit_return_one_liner | 6 | 167 | 0.0x |
| 68_terse_lambda | 11 | 200 | 0.1x |
| 69_list_comp | 6 | 199 | 0.0x |
| 70_list_comp_filter | 6 | 249 | 0.0x |
| 71_map_comp | 8 | 246 | 0.0x |
| 72_string_interp_var | 5 | 158 | 0.0x |
| 73_string_interp_int | 5 | 184 | 0.0x |
| 74_string_interp_float | 4 | 143 | 0.0x |
| 75_string_interp_bool | 5 | 138 | 0.0x |
| 76_string_interp_method | 5 | 176 | 0.0x |
| 77_string_interp_arith | 4 | 153 | 0.0x |
| 78_string_interp_multi | 5 | 154 | 0.0x |
| 79_string_interp_mixed | 7 | 149 | 0.0x |
| 80_string_interp_escaped | 4 | 131 | 0.0x |
| 81_struct_shorthand | 8 | 269 | 0.0x |
| 82_struct_update | 7 | 239 | 0.0x |
| 83_struct_update_partial | 8 | 245 | 0.0x |
| 84_let_destructure | 6 | 165 | 0.0x |
| 85_let_destructure_nested | 5 | 175 | 0.0x |
| 86_let_destructure_rest | 6 | 183 | 0.0x |
| 87_let_destructure_mut | 5 | 160 | 0.0x |
| 88_if_let | 5 | 155 | 0.0x |
| 89_if_let_else | 5 | 170 | 0.0x |
| 90_while_let | 6 | 180 | 0.0x |
| 91_let_else | 5 | 166 | 0.0x |
| 92_chained_cmp_simple | 7 | 177 | 0.0x |
| 93_chained_cmp_4 | 6 | 161 | 0.0x |
| 94_chained_cmp_mixed | 8 | 177 | 0.0x |
| 95_chained_cmp_side_effect | 6 | 209 | 0.0x |
| 96_tensor_reshape | 24 | 220 | 0.1x |
| 97_tensor_view_aliasing | 10 | 166 | 0.1x |
| 98_tensor_stepped_slice | 11 | 188 | 0.1x |
| 99_tensor_reshape_aliased | 10 | 197 | 0.1x |

