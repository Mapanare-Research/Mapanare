# Mapanare Benchmarks - Linux

Generated: 2026-05-07 14:50 UTC  
Version: 5.48.1 (`7dfabae6`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 18.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 925 | `________ ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 6 | `         v` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `        ` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 6 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 100_result_complex_destructure | 72 | 819 | 37.2 | 3 | 101 | 602 | 12 | `~   ____` | PASS |
| 101_match_rewrap_propagation | 60 | 340 | 18.4 | 4 | 23 | 338 | 8 | ` ___..__` | PASS |
| 102_nested_15arm_match | 78 | 577 | 23.9 | 5 | 40 | 428 | 11 | `    _ ._ v` | PASS |
| 103_variant_name_collision | 72 | 421 | 16.3 | 3 | 38 | 396 | 8 | ` .....*  v` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 5 | `        ` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 6 | `         v` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 6 | `         v` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 4 | `        ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 4 | `        ` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 4 | `  _ _    ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `   __ .  v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 7 | `        ` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `  _ _   ` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 6 | `        ` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 9 | `         v` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 25 | 116 | 3.9 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         v` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         ^` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `    _    v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         v` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `    _   ` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 8 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 8 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 4 | `_       ` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `_ ___-__ ^` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `.     _  v` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 4 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 6 | `        ` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 4 | `_ -  .  ` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 29 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 6 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 5 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 12 | `        ` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 7 | `   _    ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 9 | `         ^` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 8 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 8 | `  _   _  v` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 7 | `        ` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `  _     ` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `         v` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | `   _   _ ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `   _   _ ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `         v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `        ` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `  _.    ` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 8 | `         ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `        ` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `_       ` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 11 | `         v` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `_    __  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `  _     ` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 9 | `_ _ _ __ ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 5 | `__  _ ._ v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 7 | `  .   ._ v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 8 | `   _     v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `_     _  v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `_    ___` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `. _  _  ` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `-  _  _  v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | `_   __  ` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 5 | `___.____` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `    _  _ ^` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 5 | `_   _.  ` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 5 | `  .   _  v` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 7 | ` _     . ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | ` __.  _  v` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 5 | `        ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 6 | `  _    . ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `         ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `  _.    ` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `        ` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `.  _    ` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 8 | `_    *   ^` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 6 | `     _ . ^` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `         ^` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 6 | `     -  ` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `  _  _   ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | ` .    .  v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `_   _    v` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 11 | `_   _    ^` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 9 | `~__~-_._ v` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 10 | `-__.____` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 9 | `_  __   ` | PASS |
| **Total** | **2121** | **22755** | **886.8** | **162** | **1791** | **21005** | **1585** | | **103/103** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 210 | 12.4 | 1 | 217 | YES | PASS |
| 02_arithmetic | 220 | 12.6 | 1 | 199 | YES | PASS |
| 03_function | 242 | 13.3 | 2 | 127 | YES | PASS |
| 04_if_else | 227 | 12.9 | 1 | 144 | YES | PASS |
| 05_for_loop | 243 | 13.5 | 1 | 175 | YES | PASS |
| 06_struct | 223 | 12.8 | 1 | 149 | YES | PASS |
| 07_enum_match | 231 | 13.1 | 1 | 142 | YES | PASS |
| 08_list | 249 | 14.1 | 1 | 168 | YES | PASS |
| 09_string_methods | 233 | 13.5 | 1 | 157 | YES | PASS |
| 100_result_complex_destructure | 520 | 26.7 | 3 | 182 | YES | PASS |
| 101_match_rewrap_propagation | 435 | 23.8 | 5 | 192 | YES | PASS |
| 102_nested_15arm_match | 559 | 28.5 | 5 | 168 | YES | PASS |
| 103_variant_name_collision | 430 | 21.7 | 3 | 175 | YES | PASS |
| 10_result | 276 | 14.9 | 2 | 214 | YES | PASS |
| 11_closure | 233 | 13.0 | 1 | 265 | YES | PASS |
| 12_while | 229 | 12.9 | 1 | 171 | YES | PASS |
| 13_fib | 240 | 13.1 | 2 | 135 | YES | PASS |
| 14_nested_struct | 223 | 12.8 | 1 | 113 | YES | PASS |
| 15_multifunction | 253 | 13.6 | 3 | 107 | YES | PASS |
| 16_string_escape | 229 | 13.3 | 1 | 101 | YES | PASS |
| 17_option | 312 | 15.9 | 2 | 134 | YES | PASS |
| 18_method_chain | 255 | 14.5 | 1 | 127 | YES | PASS |
| 19_nested_match | 278 | 14.6 | 2 | 154 | YES | PASS |
| 20_recursion | 246 | 13.4 | 2 | 149 | YES | PASS |
| 21_list_ops | 331 | 17.5 | 2 | 190 | YES | PASS |
| 22_string_builder | 298 | 16.0 | 2 | 226 | YES | PASS |
| 23_multi_return | 272 | 14.9 | 2 | 248 | YES | PASS |
| 24_enum_methods | 266 | 14.5 | 2 | 189 | YES | PASS |
| 25_fizzbuzz | 310 | 15.7 | 2 | 164 | YES | PASS |
| 26_generics | 290 | 14.9 | 5 | 162 | YES | PASS |
| 27_impl | 250 | 13.7 | 3 | 147 | YES | PASS |
| 28_traits | 258 | 13.9 | 3 | 169 | YES | PASS |
| 29_generic_impl | 259 | 14.1 | 3 | 161 | YES | PASS |
| 30_nested_generics | 250 | 14.5 | 1 | 134 | YES | PASS |
| 31_generic_multi | 275 | 15.0 | 4 | 149 | YES | PASS |
| 32_generic_enum | 221 | 12.7 | 1 | 114 | YES | PASS |
| 33_break_continue | 434 | 19.5 | 5 | 147 | YES | PASS |
| 34_file_io | 305 | 17.3 | 1 | 119 | YES | PASS |
| 35_stdin | 235 | 13.6 | 1 | 118 | YES | PASS |
| 36_crypto | 264 | 15.0 | 1 | 124 | YES | PASS |
| 37_regex | 275 | 15.7 | 1 | 200 | YES | PASS |
| 38_http | 226 | 13.1 | 1 | 115 | YES | PASS |
| 39_gpu_detect | 253 | 14.3 | 1 | 125 | YES | PASS |
| 40_gpu_tensor | 440 | 23.0 | 1 | 151 | YES | PASS |
| 41_module_let | 224 | 12.6 | 2 | 113 | YES | PASS |
| 42_module_let_string | 227 | 12.9 | 2 | 114 | YES | PASS |
| 43_module_let_math | 231 | 13.0 | 2 | 121 | YES | PASS |
| 45_ffi_bind | 259 | 13.6 | 3 | 149 | YES | PASS |
| 47_try_operator | 358 | 18.2 | 4 | 157 | YES | PASS |
| 48_match_nested_exhaustive | 455 | 22.8 | 3 | 140 | YES | PASS |
| 49_match_guards | 316 | 16.2 | 2 | 156 | YES | PASS |
| 49_tensor_literal | 487 | 24.9 | 1 | 211 | YES | PASS |
| 50_match_or_patterns | 300 | 16.2 | 2 | 188 | YES | PASS |
| 50_tensor_indexing | 459 | 23.6 | 1 | 219 | YES | PASS |
| 51_match_guards_and_or | 382 | 19.0 | 2 | 175 | YES | PASS |
| 51_tensor_broadcast | 471 | 23.8 | 1 | 132 | YES | PASS |
| 52_tensor_slicing | 469 | 24.0 | 1 | 148 | YES | PASS |
| 53_linear_regression | 393 | 20.2 | 1 | 153 | YES | PASS |
| 54_const_basic | 230 | 13.2 | 1 | 111 | YES | PASS |
| 55_async_basic | 272 | 14.7 | 2 | 133 | YES | PASS |
| 56_async_await | 351 | 17.6 | 3 | 129 | YES | PASS |
| 57_real_await | 507 | 23.4 | 5 | 126 | YES | PASS |
| 58_async_file_io | 434 | 20.6 | 4 | 160 | YES | PASS |
| 58_const_scope | 263 | 14.1 | 2 | 181 | YES | PASS |
| 59_async_fanout | 1060 | 44.4 | 12 | 163 | YES | PASS |
| 62_list_output | 391 | 21.2 | 3 | 168 | YES | PASS |
| 63_else_sino | 319 | 16.1 | 3 | 184 | YES | PASS |
| 64_closure_typed | 332 | 16.2 | 3 | 214 | YES | PASS |
| 65_list_int_indexing | 409 | 21.5 | 1 | 154 | YES | PASS |
| 66_qualified_type_ref | 246 | 13.7 | 2 | 165 | YES | PASS |
| 67_implicit_return_one_liner | 273 | 14.3 | 4 | 152 | YES | PASS |
| 68_terse_lambda | 322 | 15.8 | 3 | 167 | YES | PASS |
| 69_list_comp | 374 | 19.9 | 1 | 158 | YES | PASS |
| 70_list_comp_filter | 383 | 20.1 | 1 | 228 | YES | PASS |
| 71_map_comp | 271 | 14.8 | 1 | 241 | YES | PASS |
| 72_string_interp_var | 226 | 13.1 | 1 | 107 | YES | PASS |
| 73_string_interp_int | 226 | 13.1 | 1 | 111 | YES | PASS |
| 74_string_interp_float | 226 | 13.1 | 1 | 115 | YES | PASS |
| 75_string_interp_bool | 227 | 13.1 | 1 | 104 | YES | PASS |
| 76_string_interp_method | 225 | 13.0 | 1 | 207 | YES | PASS |
| 77_string_interp_arith | 225 | 13.0 | 1 | 161 | YES | PASS |
| 78_string_interp_multi | 242 | 13.8 | 1 | 136 | YES | PASS |
| 79_string_interp_mixed | 236 | 13.6 | 1 | 149 | YES | PASS |
| 80_string_interp_escaped | 210 | 12.4 | 1 | 134 | YES | PASS |
| 81_struct_shorthand | 263 | 14.6 | 1 | 225 | YES | PASS |
| 82_struct_update | 259 | 14.5 | 1 | 179 | YES | PASS |
| 83_struct_update_partial | 272 | 15.1 | 1 | 191 | YES | PASS |
| 84_let_destructure | 238 | 13.4 | 1 | 171 | YES | PASS |
| 85_let_destructure_nested | 249 | 14.0 | 1 | 173 | YES | PASS |
| 86_let_destructure_rest | 228 | 13.0 | 1 | 137 | YES | PASS |
| 87_let_destructure_mut | 242 | 13.6 | 1 | 145 | YES | PASS |
| 88_if_let | 241 | 13.4 | 1 | 192 | YES | PASS |
| 89_if_let_else | 236 | 13.3 | 1 | 213 | YES | PASS |
| 90_while_let | 244 | 13.4 | 1 | 149 | YES | PASS |
| 91_let_else | 268 | 14.4 | 2 | 151 | YES | PASS |
| 92_chained_cmp_simple | 284 | 15.0 | 2 | 126 | YES | PASS |
| 93_chained_cmp_4 | 292 | 15.2 | 2 | 125 | YES | PASS |
| 94_chained_cmp_mixed | 339 | 16.8 | 4 | 124 | YES | PASS |
| 95_chained_cmp_side_effect | 307 | 16.2 | 3 | 142 | YES | PASS |
| 96_tensor_reshape | 799 | 39.4 | 1 | 132 | YES | PASS |
| 97_tensor_view_aliasing | 545 | 27.4 | 1 | 135 | YES | PASS |
| 98_tensor_stepped_slice | 617 | 30.7 | 1 | 135 | YES | PASS |
| 99_tensor_reshape_aliased | 595 | 29.6 | 1 | 160 | YES | PASS |
| **Total** | | | | **16252** | **103/103** | **103/103** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 925 | 217 | 4.3x |
| 02_arithmetic | 6 | 199 | 0.0x |
| 03_function | 7 | 127 | 0.1x |
| 04_if_else | 5 | 144 | 0.0x |
| 05_for_loop | 5 | 175 | 0.0x |
| 06_struct | 6 | 149 | 0.0x |
| 07_enum_match | 11 | 142 | 0.1x |
| 08_list | 6 | 168 | 0.0x |
| 09_string_methods | 4 | 157 | 0.0x |
| 100_result_complex_destructure | 12 | 182 | 0.1x |
| 101_match_rewrap_propagation | 8 | 192 | 0.0x |
| 102_nested_15arm_match | 11 | 168 | 0.1x |
| 103_variant_name_collision | 8 | 175 | 0.0x |
| 10_result | 5 | 214 | 0.0x |
| 11_closure | 6 | 265 | 0.0x |
| 12_while | 6 | 171 | 0.0x |
| 13_fib | 5 | 135 | 0.0x |
| 14_nested_struct | 4 | 113 | 0.0x |
| 15_multifunction | 4 | 107 | 0.0x |
| 16_string_escape | 4 | 101 | 0.0x |
| 17_option | 6 | 134 | 0.0x |
| 18_method_chain | 5 | 127 | 0.0x |
| 19_nested_match | 7 | 154 | 0.0x |
| 20_recursion | 5 | 149 | 0.0x |
| 21_list_ops | 6 | 190 | 0.0x |
| 22_string_builder | 6 | 226 | 0.0x |
| 23_multi_return | 6 | 248 | 0.0x |
| 24_enum_methods | 9 | 189 | 0.0x |
| 25_fizzbuzz | 5 | 164 | 0.0x |
| 26_generics | 7 | 162 | 0.0x |
| 27_impl | 6 | 147 | 0.0x |
| 28_traits | 6 | 169 | 0.0x |
| 29_generic_impl | 5 | 161 | 0.0x |
| 30_nested_generics | 5 | 134 | 0.0x |
| 31_generic_multi | 8 | 149 | 0.1x |
| 32_generic_enum | 5 | 114 | 0.0x |
| 33_break_continue | 8 | 147 | 0.1x |
| 34_file_io | 8 | 119 | 0.1x |
| 35_stdin | 4 | 118 | 0.0x |
| 36_crypto | 4 | 124 | 0.0x |
| 37_regex | 6 | 200 | 0.0x |
| 38_http | 4 | 115 | 0.0x |
| 39_gpu_detect | 4 | 125 | 0.0x |
| 40_gpu_tensor | 6 | 151 | 0.0x |
| 41_module_let | 4 | 113 | 0.0x |
| 42_module_let_string | 4 | 114 | 0.0x |
| 43_module_let_math | 5 | 121 | 0.0x |
| 45_ffi_bind | 5 | 149 | 0.0x |
| 47_try_operator | 29 | 157 | 0.2x |
| 48_match_nested_exhaustive | 6 | 140 | 0.0x |
| 49_match_guards | 5 | 156 | 0.0x |
| 49_tensor_literal | 12 | 211 | 0.1x |
| 50_match_or_patterns | 7 | 188 | 0.0x |
| 50_tensor_indexing | 9 | 219 | 0.0x |
| 51_match_guards_and_or | 8 | 175 | 0.0x |
| 51_tensor_broadcast | 8 | 132 | 0.1x |
| 52_tensor_slicing | 7 | 148 | 0.0x |
| 53_linear_regression | 6 | 153 | 0.0x |
| 54_const_basic | 5 | 111 | 0.0x |
| 55_async_basic | 5 | 133 | 0.0x |
| 56_async_await | 5 | 129 | 0.0x |
| 57_real_await | 5 | 126 | 0.0x |
| 58_async_file_io | 5 | 160 | 0.0x |
| 58_const_scope | 6 | 181 | 0.0x |
| 59_async_fanout | 8 | 163 | 0.0x |
| 62_list_output | 7 | 168 | 0.0x |
| 63_else_sino | 7 | 184 | 0.0x |
| 64_closure_typed | 11 | 214 | 0.0x |
| 65_list_int_indexing | 6 | 154 | 0.0x |
| 66_qualified_type_ref | 5 | 165 | 0.0x |
| 67_implicit_return_one_liner | 6 | 152 | 0.0x |
| 68_terse_lambda | 9 | 167 | 0.1x |
| 69_list_comp | 5 | 158 | 0.0x |
| 70_list_comp_filter | 7 | 228 | 0.0x |
| 71_map_comp | 8 | 241 | 0.0x |
| 72_string_interp_var | 4 | 107 | 0.0x |
| 73_string_interp_int | 4 | 111 | 0.0x |
| 74_string_interp_float | 4 | 115 | 0.0x |
| 75_string_interp_bool | 4 | 104 | 0.0x |
| 76_string_interp_method | 5 | 207 | 0.0x |
| 77_string_interp_arith | 5 | 161 | 0.0x |
| 78_string_interp_multi | 5 | 136 | 0.0x |
| 79_string_interp_mixed | 5 | 149 | 0.0x |
| 80_string_interp_escaped | 5 | 134 | 0.0x |
| 81_struct_shorthand | 7 | 225 | 0.0x |
| 82_struct_update | 6 | 179 | 0.0x |
| 83_struct_update_partial | 5 | 191 | 0.0x |
| 84_let_destructure | 6 | 171 | 0.0x |
| 85_let_destructure_nested | 5 | 173 | 0.0x |
| 86_let_destructure_rest | 5 | 137 | 0.0x |
| 87_let_destructure_mut | 5 | 145 | 0.0x |
| 88_if_let | 5 | 192 | 0.0x |
| 89_if_let_else | 8 | 213 | 0.0x |
| 90_while_let | 6 | 149 | 0.0x |
| 91_let_else | 5 | 151 | 0.0x |
| 92_chained_cmp_simple | 6 | 126 | 0.0x |
| 93_chained_cmp_4 | 6 | 125 | 0.0x |
| 94_chained_cmp_mixed | 8 | 124 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 142 | 0.0x |
| 96_tensor_reshape | 11 | 132 | 0.1x |
| 97_tensor_view_aliasing | 9 | 135 | 0.1x |
| 98_tensor_stepped_slice | 10 | 135 | 0.1x |
| 99_tensor_reshape_aliased | 9 | 160 | 0.1x |

