# Mapanare Benchmarks - Linux

Generated: 2026-05-06 19:25 UTC  
Version: 5.46.0 (`03646658`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 16.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 833 | `____.___ ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 6 | `    -  _ ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 5 | `        ` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 5 | `    _    v` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 7 | `    -    v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 6 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         v` | PASS |
| 100_result_complex_destructure | 72 | 819 | 37.2 | 3 | 101 | 602 | 11 | ` *. _ ^` | PASS |
| 101_match_rewrap_propagation | 60 | 340 | 18.4 | 4 | 23 | 338 | 8 | ` *_  ` | PASS |
| 102_nested_15arm_match | 78 | 577 | 23.9 | 5 | 40 | 428 | 10 | ` *   ` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 5 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 4 | `         v` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 8 | `        ` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 7 | `        ` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 4 | ` _ --..  v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         ^` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `   -_    ^` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 5 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `    *    ^` | PASS |
| 26_generics | 25 | 116 | 3.9 | 1 | 12 | 63 | 7 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 5 | `    _    ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 7 | `    _   ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 6 | `    _    ^` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 9 | `         ^` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `    _   ` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 7 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 5 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         v` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `  _ ._   v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` ___-__  v` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_   .   ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 6 | `    _    ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 6 | `         v` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | ` ___-_ _ ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 4 | `   __    ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 7 | `  _   _  v` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 7 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 9 | `         v` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 26 | `    *.__` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 5 | `    .   ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 7 | `   ~_    v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 6 | `        ` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 10 | `  * .   ` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `~.  _    ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 5 | `    .    v` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 4 | `    .    ^` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | `  _ __  ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 4 | `    _  _ ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `         ^` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `    __   v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | `    _. _ ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `        ` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 5 | `    _ _  v` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 7 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 5 | `        ` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 4 | `    __   v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 5 | `_   _  _ ^` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 8 | `   __    ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 5 | `    _   ` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 5 | `    . .  v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 5 | `    .   ` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | ` _  .__  v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `  . _  . ^` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 7 | `    _.  ` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `   . _   v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 3 | ` _       v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `_  ..--_ v` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 4 | `    _._  v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `   _ __  v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 3 | `         v` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 7 | `    _    v` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | `  _ .   ` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 5 | `_ ___   ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `    ._ _ ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 4 | `         ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 4 | `  _ .   ` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `    _  _ ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 4 | ` _     _ ^` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | ` _  _   ` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 7 | ` _  -._  v` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 4 | ` _  _   ` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `-  ___  ` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 5 | ` _  _    ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 7 | `         ^` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `    _    ^` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 10 | ` -     _ ^` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 9 | ` .*..*.  v` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 9 | `..  . .* ^` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 9 | `      *  v` | PASS |
| **Total** | **2049** | **22334** | **870.5** | **159** | **1753** | **20609** | **1441** | | **102/102** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 209 | 12.3 | 1 | 109 | YES | PASS |
| 02_arithmetic | 219 | 12.5 | 1 | 115 | YES | PASS |
| 03_function | 241 | 13.2 | 2 | 119 | YES | PASS |
| 04_if_else | 226 | 12.8 | 1 | 161 | YES | PASS |
| 05_for_loop | 242 | 13.4 | 1 | 173 | YES | PASS |
| 06_struct | 222 | 12.7 | 1 | 121 | YES | PASS |
| 07_enum_match | 230 | 13.0 | 1 | 127 | YES | PASS |
| 08_list | 248 | 14.1 | 1 | 126 | YES | PASS |
| 09_string_methods | 232 | 13.4 | 1 | 137 | YES | PASS |
| 100_result_complex_destructure | 519 | 26.7 | 3 | 148 | YES | PASS |
| 101_match_rewrap_propagation | 434 | 23.7 | 5 | 152 | YES | PASS |
| 102_nested_15arm_match | 558 | 28.4 | 5 | 132 | YES | PASS |
| 10_result | 275 | 14.8 | 2 | 130 | YES | PASS |
| 11_closure | 232 | 12.9 | 1 | 112 | YES | PASS |
| 12_while | 228 | 12.8 | 1 | 105 | YES | PASS |
| 13_fib | 239 | 13.0 | 2 | 118 | YES | PASS |
| 14_nested_struct | 222 | 12.7 | 1 | 132 | YES | PASS |
| 15_multifunction | 252 | 13.5 | 3 | 200 | YES | PASS |
| 16_string_escape | 228 | 13.2 | 1 | 193 | YES | PASS |
| 17_option | 311 | 15.8 | 2 | 158 | YES | PASS |
| 18_method_chain | 254 | 14.4 | 1 | 130 | YES | PASS |
| 19_nested_match | 277 | 14.5 | 2 | 148 | YES | PASS |
| 20_recursion | 245 | 13.3 | 2 | 139 | YES | PASS |
| 21_list_ops | 330 | 17.4 | 2 | 180 | YES | PASS |
| 22_string_builder | 297 | 15.9 | 2 | 141 | YES | PASS |
| 23_multi_return | 271 | 14.8 | 2 | 126 | YES | PASS |
| 24_enum_methods | 265 | 14.4 | 2 | 147 | YES | PASS |
| 25_fizzbuzz | 309 | 15.7 | 2 | 153 | YES | PASS |
| 26_generics | 289 | 14.8 | 5 | 132 | YES | PASS |
| 27_impl | 249 | 13.6 | 3 | 132 | YES | PASS |
| 28_traits | 257 | 13.8 | 3 | 154 | YES | PASS |
| 29_generic_impl | 258 | 14.0 | 3 | 122 | YES | PASS |
| 30_nested_generics | 249 | 14.4 | 1 | 177 | YES | PASS |
| 31_generic_multi | 274 | 14.9 | 4 | 146 | YES | PASS |
| 32_generic_enum | 220 | 12.6 | 1 | 100 | YES | PASS |
| 33_break_continue | 433 | 19.4 | 5 | 136 | YES | PASS |
| 34_file_io | 304 | 17.2 | 1 | 116 | YES | PASS |
| 35_stdin | 234 | 13.5 | 1 | 106 | YES | PASS |
| 36_crypto | 263 | 14.9 | 1 | 124 | YES | PASS |
| 37_regex | 274 | 15.6 | 1 | 124 | YES | PASS |
| 38_http | 225 | 13.0 | 1 | 126 | YES | PASS |
| 39_gpu_detect | 252 | 14.2 | 1 | 134 | YES | PASS |
| 40_gpu_tensor | 439 | 23.0 | 1 | 172 | YES | PASS |
| 41_module_let | 223 | 12.6 | 2 | 177 | YES | PASS |
| 42_module_let_string | 226 | 12.8 | 2 | 138 | YES | PASS |
| 43_module_let_math | 230 | 12.9 | 2 | 111 | YES | PASS |
| 45_ffi_bind | 258 | 13.5 | 3 | 138 | YES | PASS |
| 47_try_operator | 357 | 18.1 | 4 | 242 | YES | PASS |
| 48_match_nested_exhaustive | 454 | 22.8 | 3 | 167 | YES | PASS |
| 49_match_guards | 315 | 16.1 | 2 | 141 | YES | PASS |
| 49_tensor_literal | 486 | 24.8 | 1 | 124 | YES | PASS |
| 50_match_or_patterns | 299 | 16.1 | 2 | 141 | YES | PASS |
| 50_tensor_indexing | 458 | 23.5 | 1 | 123 | YES | PASS |
| 51_match_guards_and_or | 381 | 18.9 | 2 | 177 | YES | PASS |
| 51_tensor_broadcast | 470 | 23.7 | 1 | 168 | YES | PASS |
| 52_tensor_slicing | 468 | 23.9 | 1 | 153 | YES | PASS |
| 53_linear_regression | 392 | 20.1 | 1 | 124 | YES | PASS |
| 54_const_basic | 229 | 13.1 | 1 | 93 | YES | PASS |
| 55_async_basic | 271 | 14.6 | 2 | 109 | YES | PASS |
| 56_async_await | 350 | 17.5 | 3 | 131 | YES | PASS |
| 57_real_await | 506 | 23.3 | 5 | 127 | YES | PASS |
| 58_async_file_io | 433 | 20.5 | 4 | 220 | YES | PASS |
| 58_const_scope | 262 | 14.0 | 2 | 143 | YES | PASS |
| 59_async_fanout | 1059 | 44.3 | 12 | 124 | YES | PASS |
| 62_list_output | 390 | 21.1 | 3 | 140 | YES | PASS |
| 63_else_sino | 318 | 16.0 | 3 | 132 | YES | PASS |
| 64_closure_typed | 331 | 16.2 | 3 | 132 | YES | PASS |
| 65_list_int_indexing | 408 | 21.4 | 1 | 140 | YES | PASS |
| 66_qualified_type_ref | 245 | 13.6 | 2 | 121 | YES | PASS |
| 67_implicit_return_one_liner | 272 | 14.2 | 4 | 124 | YES | PASS |
| 68_terse_lambda | 321 | 15.7 | 3 | 132 | YES | PASS |
| 69_list_comp | 373 | 19.8 | 1 | 145 | YES | PASS |
| 70_list_comp_filter | 382 | 20.0 | 1 | 140 | YES | PASS |
| 71_map_comp | 270 | 14.7 | 1 | 139 | YES | PASS |
| 72_string_interp_var | 225 | 13.0 | 1 | 98 | YES | PASS |
| 73_string_interp_int | 225 | 13.0 | 1 | 115 | YES | PASS |
| 74_string_interp_float | 225 | 13.0 | 1 | 160 | YES | PASS |
| 75_string_interp_bool | 226 | 13.0 | 1 | 101 | YES | PASS |
| 76_string_interp_method | 224 | 12.9 | 1 | 129 | YES | PASS |
| 77_string_interp_arith | 224 | 12.9 | 1 | 96 | YES | PASS |
| 78_string_interp_multi | 241 | 13.7 | 1 | 112 | YES | PASS |
| 79_string_interp_mixed | 235 | 13.5 | 1 | 113 | YES | PASS |
| 80_string_interp_escaped | 209 | 12.3 | 1 | 100 | YES | PASS |
| 81_struct_shorthand | 262 | 14.5 | 1 | 188 | YES | PASS |
| 82_struct_update | 258 | 14.4 | 1 | 168 | YES | PASS |
| 83_struct_update_partial | 271 | 15.0 | 1 | 125 | YES | PASS |
| 84_let_destructure | 237 | 13.3 | 1 | 117 | YES | PASS |
| 85_let_destructure_nested | 248 | 13.9 | 1 | 118 | YES | PASS |
| 86_let_destructure_rest | 227 | 12.9 | 1 | 126 | YES | PASS |
| 87_let_destructure_mut | 241 | 13.5 | 1 | 124 | YES | PASS |
| 88_if_let | 240 | 13.3 | 1 | 131 | YES | PASS |
| 89_if_let_else | 235 | 13.2 | 1 | 197 | YES | PASS |
| 90_while_let | 243 | 13.3 | 1 | 148 | YES | PASS |
| 91_let_else | 267 | 14.3 | 2 | 135 | YES | PASS |
| 92_chained_cmp_simple | 283 | 15.0 | 2 | 121 | YES | PASS |
| 93_chained_cmp_4 | 291 | 15.1 | 2 | 115 | YES | PASS |
| 94_chained_cmp_mixed | 338 | 16.7 | 4 | 127 | YES | PASS |
| 95_chained_cmp_side_effect | 306 | 16.1 | 3 | 136 | YES | PASS |
| 96_tensor_reshape | 798 | 39.3 | 1 | 122 | YES | PASS |
| 97_tensor_view_aliasing | 544 | 27.3 | 1 | 142 | YES | PASS |
| 98_tensor_stepped_slice | 631 | 31.3 | 1 | 138 | YES | PASS |
| 99_tensor_reshape_aliased | 609 | 30.2 | 1 | 147 | YES | PASS |
| **Total** | | | | **14004** | **102/102** | **102/102** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 833 | 109 | 7.7x |
| 02_arithmetic | 6 | 115 | 0.1x |
| 03_function | 5 | 119 | 0.0x |
| 04_if_else | 5 | 161 | 0.0x |
| 05_for_loop | 7 | 173 | 0.0x |
| 06_struct | 6 | 121 | 0.0x |
| 07_enum_match | 11 | 127 | 0.1x |
| 08_list | 6 | 126 | 0.0x |
| 09_string_methods | 4 | 137 | 0.0x |
| 100_result_complex_destructure | 11 | 148 | 0.1x |
| 101_match_rewrap_propagation | 8 | 152 | 0.1x |
| 102_nested_15arm_match | 10 | 132 | 0.1x |
| 10_result | 5 | 130 | 0.0x |
| 11_closure | 4 | 112 | 0.0x |
| 12_while | 4 | 105 | 0.0x |
| 13_fib | 4 | 118 | 0.0x |
| 14_nested_struct | 4 | 132 | 0.0x |
| 15_multifunction | 8 | 200 | 0.0x |
| 16_string_escape | 5 | 193 | 0.0x |
| 17_option | 7 | 158 | 0.0x |
| 18_method_chain | 4 | 130 | 0.0x |
| 19_nested_match | 6 | 148 | 0.0x |
| 20_recursion | 5 | 139 | 0.0x |
| 21_list_ops | 6 | 180 | 0.0x |
| 22_string_builder | 6 | 141 | 0.0x |
| 23_multi_return | 5 | 126 | 0.0x |
| 24_enum_methods | 5 | 147 | 0.0x |
| 25_fizzbuzz | 6 | 153 | 0.0x |
| 26_generics | 7 | 132 | 0.1x |
| 27_impl | 5 | 132 | 0.0x |
| 28_traits | 7 | 154 | 0.0x |
| 29_generic_impl | 5 | 122 | 0.0x |
| 30_nested_generics | 6 | 177 | 0.0x |
| 31_generic_multi | 9 | 146 | 0.1x |
| 32_generic_enum | 4 | 100 | 0.0x |
| 33_break_continue | 7 | 136 | 0.1x |
| 34_file_io | 5 | 116 | 0.0x |
| 35_stdin | 4 | 106 | 0.0x |
| 36_crypto | 5 | 124 | 0.0x |
| 37_regex | 5 | 124 | 0.0x |
| 38_http | 4 | 126 | 0.0x |
| 39_gpu_detect | 4 | 134 | 0.0x |
| 40_gpu_tensor | 6 | 172 | 0.0x |
| 41_module_let | 6 | 177 | 0.0x |
| 42_module_let_string | 5 | 138 | 0.0x |
| 43_module_let_math | 4 | 111 | 0.0x |
| 45_ffi_bind | 7 | 138 | 0.1x |
| 47_try_operator | 7 | 242 | 0.0x |
| 48_match_nested_exhaustive | 9 | 167 | 0.1x |
| 49_match_guards | 6 | 141 | 0.0x |
| 49_tensor_literal | 26 | 124 | 0.2x |
| 50_match_or_patterns | 5 | 141 | 0.0x |
| 50_tensor_indexing | 7 | 123 | 0.1x |
| 51_match_guards_and_or | 6 | 177 | 0.0x |
| 51_tensor_broadcast | 10 | 168 | 0.1x |
| 52_tensor_slicing | 8 | 153 | 0.1x |
| 53_linear_regression | 5 | 124 | 0.0x |
| 54_const_basic | 4 | 93 | 0.0x |
| 55_async_basic | 4 | 109 | 0.0x |
| 56_async_await | 4 | 131 | 0.0x |
| 57_real_await | 5 | 127 | 0.0x |
| 58_async_file_io | 5 | 220 | 0.0x |
| 58_const_scope | 5 | 143 | 0.0x |
| 59_async_fanout | 6 | 124 | 0.0x |
| 62_list_output | 7 | 140 | 0.1x |
| 63_else_sino | 5 | 132 | 0.0x |
| 64_closure_typed | 7 | 132 | 0.0x |
| 65_list_int_indexing | 5 | 140 | 0.0x |
| 66_qualified_type_ref | 4 | 121 | 0.0x |
| 67_implicit_return_one_liner | 5 | 124 | 0.0x |
| 68_terse_lambda | 8 | 132 | 0.1x |
| 69_list_comp | 5 | 145 | 0.0x |
| 70_list_comp_filter | 5 | 140 | 0.0x |
| 71_map_comp | 5 | 139 | 0.0x |
| 72_string_interp_var | 4 | 98 | 0.0x |
| 73_string_interp_int | 4 | 115 | 0.0x |
| 74_string_interp_float | 7 | 160 | 0.0x |
| 75_string_interp_bool | 4 | 101 | 0.0x |
| 76_string_interp_method | 3 | 129 | 0.0x |
| 77_string_interp_arith | 4 | 96 | 0.0x |
| 78_string_interp_multi | 4 | 112 | 0.0x |
| 79_string_interp_mixed | 4 | 113 | 0.0x |
| 80_string_interp_escaped | 3 | 100 | 0.0x |
| 81_struct_shorthand | 7 | 188 | 0.0x |
| 82_struct_update | 6 | 168 | 0.0x |
| 83_struct_update_partial | 5 | 125 | 0.0x |
| 84_let_destructure | 5 | 117 | 0.0x |
| 85_let_destructure_nested | 4 | 118 | 0.0x |
| 86_let_destructure_rest | 4 | 126 | 0.0x |
| 87_let_destructure_mut | 5 | 124 | 0.0x |
| 88_if_let | 4 | 131 | 0.0x |
| 89_if_let_else | 5 | 197 | 0.0x |
| 90_while_let | 7 | 148 | 0.0x |
| 91_let_else | 4 | 135 | 0.0x |
| 92_chained_cmp_simple | 7 | 121 | 0.1x |
| 93_chained_cmp_4 | 5 | 115 | 0.0x |
| 94_chained_cmp_mixed | 7 | 127 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 136 | 0.0x |
| 96_tensor_reshape | 10 | 122 | 0.1x |
| 97_tensor_view_aliasing | 9 | 142 | 0.1x |
| 98_tensor_stepped_slice | 9 | 138 | 0.1x |
| 99_tensor_reshape_aliased | 9 | 147 | 0.1x |

