# Mapanare Benchmarks - Linux

Generated: 2026-05-06 03:50 UTC  
Version: 5.44.1 (`b735589b`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 15.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 893 | `________ ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 6 | `         ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 4 | `        ` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 6 | `        ` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 6 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 4 | `         v` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         v` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 4 | ` ~  _ _  v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         v` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `    _ __` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 7 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         v` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `         v` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 5 | `        ` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 5 | `         v` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 6 | `        ` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `         v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         v` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 10 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 6 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | ` _       v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_ _ __..` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_ .     ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 6 | `         ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 4 | `  _ __.  v` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 4 | `  _   _  v` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 6 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 6 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `        ` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 9 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 5 | `        ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 7 | `        ` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 6 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 7 | `   -     v` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 22 | `--. --~. v` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `        ` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `        ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 8 | `_  _ _  ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 4 | `        ` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `         v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `         v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `_      _ ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `         v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 6 | `         ^` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 6 | `         v` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 12 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 5 | `        ` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 4 | `       . ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 5 | `       _ ^` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 7 | `   __  _ ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 5 | ` _  _-_  v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 5 | ` _       v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 5 | `         ^` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `     _  ` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `        ` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `     _  ` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `. .     ` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 4 | `_      _ ^` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `__~_  _. ^` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 4 | `_ _     ` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `    ~ _  v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | ` _      ` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 5 | ` .     - ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 5 | ` _  _ .  v` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 5 | `   _    ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `        ` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 4 | `        ` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `.        v` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 8 | `        ` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 4 | `        ` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 4 | `    .    v` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | ` _. _   ` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `         v` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `    __  ` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 7 | `  __..  ` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | `     __  v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | ` -    _  v` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 11 | `   _   . ^` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 10 | `  ` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 10 | ` * ^` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 9 | `  ` | PASS |
| **Total** | **1839** | **20598** | **790.9** | **147** | **1589** | **19241** | **1462** | | **99/99** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 209 | 12.3 | 1 | 106 | YES | PASS |
| 02_arithmetic | 219 | 12.5 | 1 | 113 | YES | PASS |
| 03_function | 241 | 13.2 | 2 | 109 | YES | PASS |
| 04_if_else | 226 | 12.8 | 1 | 103 | YES | PASS |
| 05_for_loop | 242 | 13.4 | 1 | 120 | YES | PASS |
| 06_struct | 222 | 12.7 | 1 | 111 | YES | PASS |
| 07_enum_match | 230 | 13.0 | 1 | 109 | YES | PASS |
| 08_list | 248 | 14.1 | 1 | 107 | YES | PASS |
| 09_string_methods | 232 | 13.4 | 1 | 112 | YES | PASS |
| 10_result | 275 | 14.8 | 2 | 135 | YES | PASS |
| 11_closure | 232 | 12.9 | 1 | 205 | YES | PASS |
| 12_while | 228 | 12.8 | 1 | 124 | YES | PASS |
| 13_fib | 239 | 13.0 | 2 | 140 | YES | PASS |
| 14_nested_struct | 222 | 12.7 | 1 | 122 | YES | PASS |
| 15_multifunction | 252 | 13.5 | 3 | 133 | YES | PASS |
| 16_string_escape | 228 | 13.2 | 1 | 122 | YES | PASS |
| 17_option | 311 | 15.8 | 2 | 153 | YES | PASS |
| 18_method_chain | 254 | 14.4 | 1 | 131 | YES | PASS |
| 19_nested_match | 277 | 14.5 | 2 | 154 | YES | PASS |
| 20_recursion | 245 | 13.3 | 2 | 151 | YES | PASS |
| 21_list_ops | 330 | 17.4 | 2 | 149 | YES | PASS |
| 22_string_builder | 297 | 15.9 | 2 | 206 | YES | PASS |
| 23_multi_return | 271 | 14.8 | 2 | 175 | YES | PASS |
| 24_enum_methods | 265 | 14.4 | 2 | 155 | YES | PASS |
| 25_fizzbuzz | 309 | 15.7 | 2 | 197 | YES | PASS |
| 26_generics | 289 | 14.8 | 5 | 127 | YES | PASS |
| 27_impl | 249 | 13.6 | 3 | 131 | YES | PASS |
| 28_traits | 257 | 13.8 | 3 | 116 | YES | PASS |
| 29_generic_impl | 258 | 14.0 | 3 | 130 | YES | PASS |
| 30_nested_generics | 249 | 14.4 | 1 | 111 | YES | PASS |
| 31_generic_multi | 274 | 14.9 | 4 | 145 | YES | PASS |
| 32_generic_enum | 220 | 12.6 | 1 | 142 | YES | PASS |
| 33_break_continue | 433 | 19.4 | 5 | 219 | YES | PASS |
| 34_file_io | 304 | 17.2 | 1 | 138 | YES | PASS |
| 35_stdin | 234 | 13.5 | 1 | 138 | YES | PASS |
| 36_crypto | 263 | 14.9 | 1 | 128 | YES | PASS |
| 37_regex | 274 | 15.6 | 1 | 127 | YES | PASS |
| 38_http | 225 | 13.0 | 1 | 132 | YES | PASS |
| 39_gpu_detect | 252 | 14.2 | 1 | 125 | YES | PASS |
| 40_gpu_tensor | 439 | 23.0 | 1 | 215 | YES | PASS |
| 41_module_let | 223 | 12.6 | 2 | 121 | YES | PASS |
| 42_module_let_string | 226 | 12.8 | 2 | 123 | YES | PASS |
| 43_module_let_math | 230 | 12.9 | 2 | 113 | YES | PASS |
| 45_ffi_bind | 258 | 13.5 | 3 | 142 | YES | PASS |
| 47_try_operator | 357 | 18.1 | 4 | 135 | YES | PASS |
| 48_match_nested_exhaustive | 454 | 22.8 | 3 | 132 | YES | PASS |
| 49_match_guards | 315 | 16.1 | 2 | 128 | YES | PASS |
| 49_tensor_literal | 486 | 24.8 | 1 | 113 | YES | PASS |
| 50_match_or_patterns | 299 | 16.1 | 2 | 130 | YES | PASS |
| 50_tensor_indexing | 458 | 23.5 | 1 | 122 | YES | PASS |
| 51_match_guards_and_or | 381 | 18.9 | 2 | 129 | YES | PASS |
| 51_tensor_broadcast | 470 | 23.7 | 1 | 120 | YES | PASS |
| 52_tensor_slicing | 468 | 23.9 | 1 | 141 | YES | PASS |
| 53_linear_regression | 392 | 20.1 | 1 | 144 | YES | PASS |
| 54_const_basic | 229 | 13.1 | 1 | 113 | YES | PASS |
| 55_async_basic | 271 | 14.6 | 2 | 187 | YES | PASS |
| 56_async_await | 350 | 17.5 | 3 | 140 | YES | PASS |
| 57_real_await | 506 | 23.3 | 5 | 132 | YES | PASS |
| 58_async_file_io | 433 | 20.5 | 4 | 141 | YES | PASS |
| 58_const_scope | 262 | 14.0 | 2 | 141 | YES | PASS |
| 59_async_fanout | 1059 | 44.3 | 12 | 136 | YES | PASS |
| 62_list_output | 390 | 21.1 | 3 | 145 | YES | PASS |
| 63_else_sino | 318 | 16.0 | 3 | 158 | YES | PASS |
| 64_closure_typed | 331 | 16.2 | 3 | 225 | YES | PASS |
| 65_list_int_indexing | 408 | 21.4 | 1 | 153 | YES | PASS |
| 66_qualified_type_ref | 245 | 13.6 | 2 | 114 | YES | PASS |
| 67_implicit_return_one_liner | 272 | 14.2 | 4 | 117 | YES | PASS |
| 68_terse_lambda | 321 | 15.7 | 3 | 122 | YES | PASS |
| 69_list_comp | 373 | 19.8 | 1 | 127 | YES | PASS |
| 70_list_comp_filter | 382 | 20.0 | 1 | 238 | YES | PASS |
| 71_map_comp | 270 | 14.7 | 1 | 131 | YES | PASS |
| 72_string_interp_var | 225 | 13.0 | 1 | 110 | YES | PASS |
| 73_string_interp_int | 225 | 13.0 | 1 | 116 | YES | PASS |
| 74_string_interp_float | 225 | 13.0 | 1 | 115 | YES | PASS |
| 75_string_interp_bool | 226 | 13.0 | 1 | 114 | YES | PASS |
| 76_string_interp_method | 224 | 12.9 | 1 | 130 | YES | PASS |
| 77_string_interp_arith | 224 | 12.9 | 1 | 105 | YES | PASS |
| 78_string_interp_multi | 241 | 13.7 | 1 | 128 | YES | PASS |
| 79_string_interp_mixed | 235 | 13.5 | 1 | 110 | YES | PASS |
| 80_string_interp_escaped | 209 | 12.3 | 1 | 103 | YES | PASS |
| 81_struct_shorthand | 262 | 14.5 | 1 | 123 | YES | PASS |
| 82_struct_update | 258 | 14.4 | 1 | 140 | YES | PASS |
| 83_struct_update_partial | 271 | 15.0 | 1 | 133 | YES | PASS |
| 84_let_destructure | 237 | 13.3 | 1 | 110 | YES | PASS |
| 85_let_destructure_nested | 248 | 13.9 | 1 | 122 | YES | PASS |
| 86_let_destructure_rest | 227 | 12.9 | 1 | 146 | YES | PASS |
| 87_let_destructure_mut | 241 | 13.5 | 1 | 182 | YES | PASS |
| 88_if_let | 240 | 13.3 | 1 | 115 | YES | PASS |
| 89_if_let_else | 235 | 13.2 | 1 | 120 | YES | PASS |
| 90_while_let | 243 | 13.3 | 1 | 137 | YES | PASS |
| 91_let_else | 267 | 14.3 | 2 | 124 | YES | PASS |
| 92_chained_cmp_simple | 283 | 15.0 | 2 | 164 | YES | PASS |
| 93_chained_cmp_4 | 291 | 15.1 | 2 | 176 | YES | PASS |
| 94_chained_cmp_mixed | 338 | 16.7 | 4 | 148 | YES | PASS |
| 95_chained_cmp_side_effect | 306 | 16.1 | 3 | 156 | YES | PASS |
| 96_tensor_reshape | 798 | 39.3 | 1 | 149 | YES | PASS |
| 97_tensor_view_aliasing | 544 | 27.3 | 1 | 151 | YES | PASS |
| 98_tensor_stepped_slice | 631 | 31.3 | 1 | 180 | YES | PASS |
| 99_tensor_reshape_aliased | 609 | 30.2 | 1 | 144 | YES | PASS |
| **Total** | | | | **13632** | **99/99** | **99/99** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 893 | 106 | 8.4x |
| 02_arithmetic | 6 | 113 | 0.1x |
| 03_function | 4 | 109 | 0.0x |
| 04_if_else | 5 | 103 | 0.0x |
| 05_for_loop | 5 | 120 | 0.0x |
| 06_struct | 6 | 111 | 0.1x |
| 07_enum_match | 11 | 109 | 0.1x |
| 08_list | 6 | 107 | 0.1x |
| 09_string_methods | 4 | 112 | 0.0x |
| 10_result | 6 | 135 | 0.0x |
| 11_closure | 4 | 205 | 0.0x |
| 12_while | 5 | 124 | 0.0x |
| 13_fib | 5 | 140 | 0.0x |
| 14_nested_struct | 4 | 122 | 0.0x |
| 15_multifunction | 5 | 133 | 0.0x |
| 16_string_escape | 4 | 122 | 0.0x |
| 17_option | 6 | 153 | 0.0x |
| 18_method_chain | 4 | 131 | 0.0x |
| 19_nested_match | 6 | 154 | 0.0x |
| 20_recursion | 4 | 151 | 0.0x |
| 21_list_ops | 6 | 149 | 0.0x |
| 22_string_builder | 6 | 206 | 0.0x |
| 23_multi_return | 7 | 175 | 0.0x |
| 24_enum_methods | 6 | 155 | 0.0x |
| 25_fizzbuzz | 5 | 197 | 0.0x |
| 26_generics | 8 | 127 | 0.1x |
| 27_impl | 5 | 131 | 0.0x |
| 28_traits | 5 | 116 | 0.0x |
| 29_generic_impl | 6 | 130 | 0.0x |
| 30_nested_generics | 5 | 111 | 0.0x |
| 31_generic_multi | 7 | 145 | 0.0x |
| 32_generic_enum | 4 | 142 | 0.0x |
| 33_break_continue | 10 | 219 | 0.0x |
| 34_file_io | 6 | 138 | 0.0x |
| 35_stdin | 4 | 138 | 0.0x |
| 36_crypto | 5 | 128 | 0.0x |
| 37_regex | 5 | 127 | 0.0x |
| 38_http | 4 | 132 | 0.0x |
| 39_gpu_detect | 4 | 125 | 0.0x |
| 40_gpu_tensor | 6 | 215 | 0.0x |
| 41_module_let | 5 | 121 | 0.0x |
| 42_module_let_string | 4 | 123 | 0.0x |
| 43_module_let_math | 4 | 113 | 0.0x |
| 45_ffi_bind | 5 | 142 | 0.0x |
| 47_try_operator | 6 | 135 | 0.0x |
| 48_match_nested_exhaustive | 6 | 132 | 0.0x |
| 49_match_guards | 6 | 128 | 0.0x |
| 49_tensor_literal | 9 | 113 | 0.1x |
| 50_match_or_patterns | 5 | 130 | 0.0x |
| 50_tensor_indexing | 7 | 122 | 0.1x |
| 51_match_guards_and_or | 6 | 129 | 0.0x |
| 51_tensor_broadcast | 7 | 120 | 0.1x |
| 52_tensor_slicing | 22 | 141 | 0.2x |
| 53_linear_regression | 6 | 144 | 0.0x |
| 54_const_basic | 5 | 113 | 0.0x |
| 55_async_basic | 8 | 187 | 0.0x |
| 56_async_await | 4 | 140 | 0.0x |
| 57_real_await | 5 | 132 | 0.0x |
| 58_async_file_io | 5 | 141 | 0.0x |
| 58_const_scope | 6 | 141 | 0.0x |
| 59_async_fanout | 6 | 136 | 0.0x |
| 62_list_output | 6 | 145 | 0.0x |
| 63_else_sino | 6 | 158 | 0.0x |
| 64_closure_typed | 12 | 225 | 0.1x |
| 65_list_int_indexing | 5 | 153 | 0.0x |
| 66_qualified_type_ref | 4 | 114 | 0.0x |
| 67_implicit_return_one_liner | 5 | 117 | 0.0x |
| 68_terse_lambda | 7 | 122 | 0.1x |
| 69_list_comp | 5 | 127 | 0.0x |
| 70_list_comp_filter | 5 | 238 | 0.0x |
| 71_map_comp | 5 | 131 | 0.0x |
| 72_string_interp_var | 4 | 110 | 0.0x |
| 73_string_interp_int | 4 | 116 | 0.0x |
| 74_string_interp_float | 4 | 115 | 0.0x |
| 75_string_interp_bool | 4 | 114 | 0.0x |
| 76_string_interp_method | 4 | 130 | 0.0x |
| 77_string_interp_arith | 4 | 105 | 0.0x |
| 78_string_interp_multi | 4 | 128 | 0.0x |
| 79_string_interp_mixed | 4 | 110 | 0.0x |
| 80_string_interp_escaped | 4 | 103 | 0.0x |
| 81_struct_shorthand | 5 | 123 | 0.0x |
| 82_struct_update | 5 | 140 | 0.0x |
| 83_struct_update_partial | 5 | 133 | 0.0x |
| 84_let_destructure | 5 | 110 | 0.0x |
| 85_let_destructure_nested | 4 | 122 | 0.0x |
| 86_let_destructure_rest | 5 | 146 | 0.0x |
| 87_let_destructure_mut | 8 | 182 | 0.0x |
| 88_if_let | 4 | 115 | 0.0x |
| 89_if_let_else | 4 | 120 | 0.0x |
| 90_while_let | 5 | 137 | 0.0x |
| 91_let_else | 5 | 124 | 0.0x |
| 92_chained_cmp_simple | 7 | 164 | 0.0x |
| 93_chained_cmp_4 | 7 | 176 | 0.0x |
| 94_chained_cmp_mixed | 8 | 148 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 156 | 0.0x |
| 96_tensor_reshape | 11 | 149 | 0.1x |
| 97_tensor_view_aliasing | 10 | 151 | 0.1x |
| 98_tensor_stepped_slice | 10 | 180 | 0.1x |
| 99_tensor_reshape_aliased | 9 | 144 | 0.1x |

