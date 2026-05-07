# Mapanare Benchmarks - Linux

Generated: 2026-05-07 23:26 UTC  
Version: 5.49.0 (`a3854be3`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 20.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1753 | `_____-_. ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 8 | `         ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 8 | `         ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 7 | `         ^` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 8 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 21 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         v` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 100_result_complex_destructure | 72 | 819 | 37.2 | 3 | 101 | 602 | 12 | `_____-..` | PASS |
| 101_match_rewrap_propagation | 60 | 340 | 18.4 | 4 | 23 | 338 | 9 | `_ _..__- ^` | PASS |
| 102_nested_15arm_match | 75 | 577 | 23.9 | 5 | 40 | 428 | 10 | `_     .  v` | PASS |
| 103_variant_name_collision | 72 | 421 | 16.3 | 3 | 38 | 396 | 8 | `   _*  _ ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 5 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 4 | `    _    ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `        ` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         v` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | ` _._ _..` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 7 | `      _  v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `        ` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `  _ _   ` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 7 | `         ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.9 | 1 | 12 | 63 | 8 | `         ^` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `        ` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         ^` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `     _   ^` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `    ~   ` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 6 | `        ` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         v` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `   _     v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `__ __. . ^` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 5 | `      .  v` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `     _  ` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 6 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 7 | `  _ _ _. ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `     . _ ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 30 | `         ^` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 6 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `         v` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `      _  v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 8 | `       _ ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 7 | `       _ ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 7 | `       _ ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 6 | `  _      ^` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | `_  _ _ _ ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 7 | `_ ____ _ ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 13 | `        ` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `        ` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | ` _  _ _  v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 8 | `         ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 9 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `        ` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 10 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 8 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `   _   _ ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 8 | `         v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 9 | `_____.__` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `_  _____ v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | `__      ` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | ` _.  __  v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `  .  ___` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | `_ .  ..  v` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `  _  . _ ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `  _.  _  v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | ` __ .___` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `_.___.__` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 4 | `__ _  __` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 5 | ` _.  __. ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `         v` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 7 | `..   __  v` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 7 | ` _   .  ` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 7 | `  __  _  v` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `._. _ _  v` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 6 | `         v` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `    _   ` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 6 | `   _  _  v` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `   _  _  v` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | ` .       v` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `._  - .- ^` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 6 | `    _    ^` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `  _   _  v` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `   _.  _ ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 10 | `        ` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 7 | `     ~   v` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 13 | `   _ _   ^` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 12 | `  *__-*  v` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 10 | `_____.-. v` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 16 | `   _  _  v` | PASS |
| **Total** | **2118** | **22755** | **886.8** | **162** | **1791** | **21005** | **2458** | | **103/103** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 210 | 12.4 | 1 | 160 | YES | PASS |
| 02_arithmetic | 220 | 12.6 | 1 | 171 | YES | PASS |
| 03_function | 242 | 13.3 | 2 | 241 | YES | PASS |
| 04_if_else | 227 | 12.9 | 1 | 202 | YES | PASS |
| 05_for_loop | 243 | 13.5 | 1 | 183 | YES | PASS |
| 06_struct | 223 | 12.8 | 1 | 229 | YES | PASS |
| 07_enum_match | 231 | 13.1 | 1 | 173 | YES | PASS |
| 08_list | 249 | 14.1 | 1 | 143 | YES | PASS |
| 09_string_methods | 233 | 13.5 | 1 | 159 | YES | PASS |
| 100_result_complex_destructure | 520 | 26.7 | 3 | 168 | YES | PASS |
| 101_match_rewrap_propagation | 435 | 23.8 | 5 | 195 | YES | PASS |
| 102_nested_15arm_match | 559 | 28.5 | 5 | 155 | YES | PASS |
| 103_variant_name_collision | 430 | 21.7 | 3 | 164 | YES | PASS |
| 10_result | 276 | 14.9 | 2 | 166 | YES | PASS |
| 11_closure | 233 | 13.0 | 1 | 146 | YES | PASS |
| 12_while | 229 | 12.9 | 1 | 131 | YES | PASS |
| 13_fib | 240 | 13.1 | 2 | 143 | YES | PASS |
| 14_nested_struct | 223 | 12.8 | 1 | 127 | YES | PASS |
| 15_multifunction | 253 | 13.6 | 3 | 174 | YES | PASS |
| 16_string_escape | 229 | 13.3 | 1 | 134 | YES | PASS |
| 17_option | 312 | 15.9 | 2 | 156 | YES | PASS |
| 18_method_chain | 255 | 14.5 | 1 | 145 | YES | PASS |
| 19_nested_match | 278 | 14.6 | 2 | 161 | YES | PASS |
| 20_recursion | 246 | 13.4 | 2 | 141 | YES | PASS |
| 21_list_ops | 331 | 17.5 | 2 | 176 | YES | PASS |
| 22_string_builder | 298 | 16.0 | 2 | 250 | YES | PASS |
| 23_multi_return | 272 | 14.9 | 2 | 181 | YES | PASS |
| 24_enum_methods | 266 | 14.5 | 2 | 152 | YES | PASS |
| 25_fizzbuzz | 310 | 15.7 | 2 | 159 | YES | PASS |
| 26_generics | 290 | 14.9 | 5 | 167 | YES | PASS |
| 27_impl | 250 | 13.7 | 3 | 147 | YES | PASS |
| 28_traits | 258 | 13.9 | 3 | 234 | YES | PASS |
| 29_generic_impl | 259 | 14.1 | 3 | 148 | YES | PASS |
| 30_nested_generics | 250 | 14.5 | 1 | 132 | YES | PASS |
| 31_generic_multi | 275 | 15.0 | 4 | 138 | YES | PASS |
| 32_generic_enum | 221 | 12.7 | 1 | 130 | YES | PASS |
| 33_break_continue | 434 | 19.5 | 5 | 178 | YES | PASS |
| 34_file_io | 305 | 17.3 | 1 | 161 | YES | PASS |
| 35_stdin | 235 | 13.6 | 1 | 141 | YES | PASS |
| 36_crypto | 264 | 15.0 | 1 | 138 | YES | PASS |
| 37_regex | 275 | 15.7 | 1 | 149 | YES | PASS |
| 38_http | 226 | 13.1 | 1 | 142 | YES | PASS |
| 39_gpu_detect | 253 | 14.3 | 1 | 146 | YES | PASS |
| 40_gpu_tensor | 440 | 23.0 | 1 | 201 | YES | PASS |
| 41_module_let | 224 | 12.6 | 2 | 225 | YES | PASS |
| 42_module_let_string | 227 | 12.9 | 2 | 176 | YES | PASS |
| 43_module_let_math | 231 | 13.0 | 2 | 132 | YES | PASS |
| 45_ffi_bind | 259 | 13.6 | 3 | 143 | YES | PASS |
| 47_try_operator | 358 | 18.2 | 4 | 169 | YES | PASS |
| 48_match_nested_exhaustive | 455 | 22.8 | 3 | 162 | YES | PASS |
| 49_match_guards | 316 | 16.2 | 2 | 158 | YES | PASS |
| 49_tensor_literal | 487 | 24.9 | 1 | 142 | YES | PASS |
| 50_match_or_patterns | 300 | 16.2 | 2 | 189 | YES | PASS |
| 50_tensor_indexing | 459 | 23.6 | 1 | 142 | YES | PASS |
| 51_match_guards_and_or | 382 | 19.0 | 2 | 164 | YES | PASS |
| 51_tensor_broadcast | 471 | 23.8 | 1 | 160 | YES | PASS |
| 52_tensor_slicing | 469 | 24.0 | 1 | 149 | YES | PASS |
| 53_linear_regression | 393 | 20.2 | 1 | 227 | YES | PASS |
| 54_const_basic | 230 | 13.2 | 1 | 133 | YES | PASS |
| 55_async_basic | 272 | 14.7 | 2 | 146 | YES | PASS |
| 56_async_await | 351 | 17.6 | 3 | 242 | YES | PASS |
| 57_real_await | 507 | 23.4 | 5 | 189 | YES | PASS |
| 58_async_file_io | 434 | 20.6 | 4 | 160 | YES | PASS |
| 58_const_scope | 263 | 14.1 | 2 | 153 | YES | PASS |
| 59_async_fanout | 1060 | 44.4 | 12 | 149 | YES | PASS |
| 62_list_output | 391 | 21.2 | 3 | 166 | YES | PASS |
| 63_else_sino | 319 | 16.1 | 3 | 149 | YES | PASS |
| 64_closure_typed | 332 | 16.2 | 3 | 153 | YES | PASS |
| 65_list_int_indexing | 409 | 21.5 | 1 | 163 | YES | PASS |
| 66_qualified_type_ref | 246 | 13.7 | 2 | 159 | YES | PASS |
| 67_implicit_return_one_liner | 273 | 14.3 | 4 | 198 | YES | PASS |
| 68_terse_lambda | 322 | 15.8 | 3 | 157 | YES | PASS |
| 69_list_comp | 374 | 19.9 | 1 | 163 | YES | PASS |
| 70_list_comp_filter | 383 | 20.1 | 1 | 169 | YES | PASS |
| 71_map_comp | 271 | 14.8 | 1 | 173 | YES | PASS |
| 72_string_interp_var | 226 | 13.1 | 1 | 138 | YES | PASS |
| 73_string_interp_int | 226 | 13.1 | 1 | 122 | YES | PASS |
| 74_string_interp_float | 226 | 13.1 | 1 | 132 | YES | PASS |
| 75_string_interp_bool | 227 | 13.1 | 1 | 121 | YES | PASS |
| 76_string_interp_method | 225 | 13.0 | 1 | 147 | YES | PASS |
| 77_string_interp_arith | 225 | 13.0 | 1 | 124 | YES | PASS |
| 78_string_interp_multi | 242 | 13.8 | 1 | 136 | YES | PASS |
| 79_string_interp_mixed | 236 | 13.6 | 1 | 134 | YES | PASS |
| 80_string_interp_escaped | 210 | 12.4 | 1 | 115 | YES | PASS |
| 81_struct_shorthand | 263 | 14.6 | 1 | 221 | YES | PASS |
| 82_struct_update | 259 | 14.5 | 1 | 255 | YES | PASS |
| 83_struct_update_partial | 272 | 15.1 | 1 | 167 | YES | PASS |
| 84_let_destructure | 238 | 13.4 | 1 | 151 | YES | PASS |
| 85_let_destructure_nested | 249 | 14.0 | 1 | 168 | YES | PASS |
| 86_let_destructure_rest | 228 | 13.0 | 1 | 149 | YES | PASS |
| 87_let_destructure_mut | 242 | 13.6 | 1 | 158 | YES | PASS |
| 88_if_let | 241 | 13.4 | 1 | 156 | YES | PASS |
| 89_if_let_else | 236 | 13.3 | 1 | 149 | YES | PASS |
| 90_while_let | 244 | 13.4 | 1 | 153 | YES | PASS |
| 91_let_else | 268 | 14.4 | 2 | 159 | YES | PASS |
| 92_chained_cmp_simple | 284 | 15.0 | 2 | 142 | YES | PASS |
| 93_chained_cmp_4 | 292 | 15.2 | 2 | 152 | YES | PASS |
| 94_chained_cmp_mixed | 339 | 16.8 | 4 | 247 | YES | PASS |
| 95_chained_cmp_side_effect | 307 | 16.2 | 3 | 170 | YES | PASS |
| 96_tensor_reshape | 799 | 39.4 | 1 | 169 | YES | PASS |
| 97_tensor_view_aliasing | 545 | 27.4 | 1 | 163 | YES | PASS |
| 98_tensor_stepped_slice | 617 | 30.7 | 1 | 167 | YES | PASS |
| 99_tensor_reshape_aliased | 595 | 29.6 | 1 | 258 | YES | PASS |
| **Total** | | | | **16918** | **103/103** | **103/103** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1753 | 160 | 11.0x |
| 02_arithmetic | 8 | 171 | 0.0x |
| 03_function | 8 | 241 | 0.0x |
| 04_if_else | 8 | 202 | 0.0x |
| 05_for_loop | 7 | 183 | 0.0x |
| 06_struct | 8 | 229 | 0.0x |
| 07_enum_match | 21 | 173 | 0.1x |
| 08_list | 7 | 143 | 0.0x |
| 09_string_methods | 5 | 159 | 0.0x |
| 100_result_complex_destructure | 12 | 168 | 0.1x |
| 101_match_rewrap_propagation | 9 | 195 | 0.0x |
| 102_nested_15arm_match | 10 | 155 | 0.1x |
| 103_variant_name_collision | 8 | 164 | 0.0x |
| 10_result | 5 | 166 | 0.0x |
| 11_closure | 4 | 146 | 0.0x |
| 12_while | 4 | 131 | 0.0x |
| 13_fib | 4 | 143 | 0.0x |
| 14_nested_struct | 4 | 127 | 0.0x |
| 15_multifunction | 4 | 174 | 0.0x |
| 16_string_escape | 5 | 134 | 0.0x |
| 17_option | 6 | 156 | 0.0x |
| 18_method_chain | 5 | 145 | 0.0x |
| 19_nested_match | 7 | 161 | 0.0x |
| 20_recursion | 4 | 141 | 0.0x |
| 21_list_ops | 6 | 176 | 0.0x |
| 22_string_builder | 6 | 250 | 0.0x |
| 23_multi_return | 7 | 181 | 0.0x |
| 24_enum_methods | 5 | 152 | 0.0x |
| 25_fizzbuzz | 6 | 159 | 0.0x |
| 26_generics | 8 | 167 | 0.0x |
| 27_impl | 6 | 147 | 0.0x |
| 28_traits | 6 | 234 | 0.0x |
| 29_generic_impl | 7 | 148 | 0.0x |
| 30_nested_generics | 5 | 132 | 0.0x |
| 31_generic_multi | 7 | 138 | 0.0x |
| 32_generic_enum | 4 | 130 | 0.0x |
| 33_break_continue | 9 | 178 | 0.0x |
| 34_file_io | 6 | 161 | 0.0x |
| 35_stdin | 4 | 141 | 0.0x |
| 36_crypto | 5 | 138 | 0.0x |
| 37_regex | 6 | 149 | 0.0x |
| 38_http | 5 | 142 | 0.0x |
| 39_gpu_detect | 4 | 146 | 0.0x |
| 40_gpu_tensor | 7 | 201 | 0.0x |
| 41_module_let | 6 | 225 | 0.0x |
| 42_module_let_string | 7 | 176 | 0.0x |
| 43_module_let_math | 5 | 132 | 0.0x |
| 45_ffi_bind | 5 | 143 | 0.0x |
| 47_try_operator | 30 | 169 | 0.2x |
| 48_match_nested_exhaustive | 6 | 162 | 0.0x |
| 49_match_guards | 6 | 158 | 0.0x |
| 49_tensor_literal | 10 | 142 | 0.1x |
| 50_match_or_patterns | 6 | 189 | 0.0x |
| 50_tensor_indexing | 8 | 142 | 0.1x |
| 51_match_guards_and_or | 7 | 164 | 0.0x |
| 51_tensor_broadcast | 8 | 160 | 0.1x |
| 52_tensor_slicing | 7 | 149 | 0.0x |
| 53_linear_regression | 7 | 227 | 0.0x |
| 54_const_basic | 6 | 133 | 0.0x |
| 55_async_basic | 4 | 146 | 0.0x |
| 56_async_await | 7 | 242 | 0.0x |
| 57_real_await | 13 | 189 | 0.1x |
| 58_async_file_io | 5 | 160 | 0.0x |
| 58_const_scope | 6 | 153 | 0.0x |
| 59_async_fanout | 8 | 149 | 0.1x |
| 62_list_output | 9 | 166 | 0.1x |
| 63_else_sino | 7 | 149 | 0.0x |
| 64_closure_typed | 10 | 153 | 0.1x |
| 65_list_int_indexing | 8 | 163 | 0.0x |
| 66_qualified_type_ref | 5 | 159 | 0.0x |
| 67_implicit_return_one_liner | 8 | 198 | 0.0x |
| 68_terse_lambda | 9 | 157 | 0.1x |
| 69_list_comp | 6 | 163 | 0.0x |
| 70_list_comp_filter | 6 | 169 | 0.0x |
| 71_map_comp | 6 | 173 | 0.0x |
| 72_string_interp_var | 4 | 138 | 0.0x |
| 73_string_interp_int | 5 | 122 | 0.0x |
| 74_string_interp_float | 4 | 132 | 0.0x |
| 75_string_interp_bool | 4 | 121 | 0.0x |
| 76_string_interp_method | 5 | 147 | 0.0x |
| 77_string_interp_arith | 4 | 124 | 0.0x |
| 78_string_interp_multi | 4 | 136 | 0.0x |
| 79_string_interp_mixed | 5 | 134 | 0.0x |
| 80_string_interp_escaped | 4 | 115 | 0.0x |
| 81_struct_shorthand | 7 | 221 | 0.0x |
| 82_struct_update | 7 | 255 | 0.0x |
| 83_struct_update_partial | 7 | 167 | 0.0x |
| 84_let_destructure | 5 | 151 | 0.0x |
| 85_let_destructure_nested | 6 | 168 | 0.0x |
| 86_let_destructure_rest | 5 | 149 | 0.0x |
| 87_let_destructure_mut | 6 | 158 | 0.0x |
| 88_if_let | 5 | 156 | 0.0x |
| 89_if_let_else | 5 | 149 | 0.0x |
| 90_while_let | 5 | 153 | 0.0x |
| 91_let_else | 6 | 159 | 0.0x |
| 92_chained_cmp_simple | 7 | 142 | 0.1x |
| 93_chained_cmp_4 | 6 | 152 | 0.0x |
| 94_chained_cmp_mixed | 10 | 247 | 0.0x |
| 95_chained_cmp_side_effect | 7 | 170 | 0.0x |
| 96_tensor_reshape | 13 | 169 | 0.1x |
| 97_tensor_view_aliasing | 12 | 163 | 0.1x |
| 98_tensor_stepped_slice | 10 | 167 | 0.1x |
| 99_tensor_reshape_aliased | 16 | 258 | 0.1x |

