# Mapanare Benchmarks - Linux

Generated: 2026-05-09 04:23 UTC  
Version: 5.50.0 (`df94629b`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 19.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1056 | `__-_.-.. v` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 7 | `      _  v` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 5 | `        ` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         v` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         v` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         v` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 8 | `         v` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         v` | PASS |
| 100_result_complex_destructure | 72 | 819 | 37.2 | 3 | 101 | 602 | 13 | `__..._*. v` | PASS |
| 101_match_rewrap_propagation | 60 | 340 | 18.4 | 4 | 23 | 338 | 11 | `    _ *  v` | PASS |
| 102_nested_15arm_match | 75 | 577 | 23.9 | 5 | 40 | 428 | 14 | `   .  -- v` | PASS |
| 103_variant_name_collision | 72 | 421 | 16.3 | 3 | 38 | 396 | 10 | `_*  _ -  v` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 7 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 6 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 7 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 7 | `        ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | ` _       v` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         v` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 8 | `         v` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 8 | `_ _.._..` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 12 | `   _     v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 6 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 9 | `         v` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 5 | ` _     _ ^` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 8 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         v` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         v` | PASS |
| 26_generics | 25 | 116 | 3.9 | 1 | 12 | 63 | 7 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 8 | `         v` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 7 | `         v` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 6 | `         v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `  _      v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 6 | ` ~     _ ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 10 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 6 | `        ` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `_     __` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | `__. ._._ v` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `   . _.  v` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `  _      v` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 9 | `         v` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 7 | ` _ _..__ v` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `  . _ _  v` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `      _  v` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 36 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 8 | `         v` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 7 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `        ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `   _     v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 9 | `    _    v` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `    _  . ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 7 | `    _    v` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `        ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | `_ _ _ _  v` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `___ ___  v` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `        ` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 6 | `      _  v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | ` _ _ _._ v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `         v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `      _  v` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         v` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `_   _ _  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `     __  v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 9 | `__._____ v` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `________ v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 7 | `      __` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | `  __  __` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 5 | `  ___ -_ v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 7 | `  .. _._ v` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 5 | `  . _ .  v` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `.  _  -_ v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | ` .____.  v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `__.___..` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 7 | `_  __ .  v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 7 | `  __._.  v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `      _  v` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 6 | `  __ .._ v` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | `  .  ._. ^` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 6 | `_  _ _-  v` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | ` _ _  _. ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `         v` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | ` _    _  v` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 8 | `_  _  _  v` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 6 | `_  _  _  v` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `      .  v` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 8 | ` - .- .  v` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | ` _    .  v` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 8 | `   _  __ v` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `_.  _ .  v` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 10 | `     _._ v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `  ~  _.  v` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.5 | 1 | 90 | 1704 | 13 | `_ _  _._ v` | PASS |
| 97_tensor_view_aliasing | 67 | 805 | 33.9 | 1 | 52 | 1005 | 10 | `__-* -.  v` | PASS |
| 98_tensor_stepped_slice | 84 | 1000 | 41.8 | 1 | 60 | 1276 | 10 | `  _._ -* ^` | PASS |
| 99_tensor_reshape_aliased | 62 | 866 | 37.1 | 1 | 54 | 1154 | 11 | `_  _ *._ v` | PASS |
| **Total** | **2118** | **22755** | **886.8** | **162** | **1791** | **21005** | **1783** | | **103/103** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 211 | 12.4 | 1 | 121 | YES | PASS |
| 02_arithmetic | 221 | 12.7 | 1 | 152 | YES | PASS |
| 03_function | 243 | 13.3 | 2 | 127 | YES | PASS |
| 04_if_else | 228 | 13.0 | 1 | 141 | YES | PASS |
| 05_for_loop | 244 | 13.5 | 1 | 157 | YES | PASS |
| 06_struct | 224 | 12.9 | 1 | 154 | YES | PASS |
| 07_enum_match | 232 | 13.1 | 1 | 163 | YES | PASS |
| 08_list | 250 | 14.2 | 1 | 142 | YES | PASS |
| 09_string_methods | 234 | 13.5 | 1 | 139 | YES | PASS |
| 100_result_complex_destructure | 521 | 26.8 | 3 | 185 | YES | PASS |
| 101_match_rewrap_propagation | 436 | 23.8 | 5 | 264 | YES | PASS |
| 102_nested_15arm_match | 560 | 28.5 | 5 | 197 | YES | PASS |
| 103_variant_name_collision | 431 | 21.7 | 3 | 182 | YES | PASS |
| 10_result | 277 | 14.9 | 2 | 196 | YES | PASS |
| 11_closure | 234 | 13.0 | 1 | 174 | YES | PASS |
| 12_while | 230 | 12.9 | 1 | 212 | YES | PASS |
| 13_fib | 241 | 13.1 | 2 | 188 | YES | PASS |
| 14_nested_struct | 224 | 12.9 | 1 | 174 | YES | PASS |
| 15_multifunction | 254 | 13.7 | 3 | 178 | YES | PASS |
| 16_string_escape | 230 | 13.3 | 1 | 162 | YES | PASS |
| 17_option | 313 | 16.0 | 2 | 193 | YES | PASS |
| 18_method_chain | 256 | 14.5 | 1 | 304 | YES | PASS |
| 19_nested_match | 279 | 14.7 | 2 | 271 | YES | PASS |
| 20_recursion | 247 | 13.4 | 2 | 174 | YES | PASS |
| 21_list_ops | 332 | 17.6 | 2 | 160 | YES | PASS |
| 22_string_builder | 299 | 16.0 | 2 | 192 | YES | PASS |
| 23_multi_return | 273 | 15.0 | 2 | 203 | YES | PASS |
| 24_enum_methods | 267 | 14.5 | 2 | 184 | YES | PASS |
| 25_fizzbuzz | 311 | 15.8 | 2 | 149 | YES | PASS |
| 26_generics | 291 | 14.9 | 5 | 184 | YES | PASS |
| 27_impl | 251 | 13.7 | 3 | 161 | YES | PASS |
| 28_traits | 259 | 14.0 | 3 | 193 | YES | PASS |
| 29_generic_impl | 260 | 14.2 | 3 | 166 | YES | PASS |
| 30_nested_generics | 251 | 14.5 | 1 | 138 | YES | PASS |
| 31_generic_multi | 276 | 15.0 | 4 | 210 | YES | PASS |
| 32_generic_enum | 222 | 12.8 | 1 | 162 | YES | PASS |
| 33_break_continue | 435 | 19.6 | 5 | 183 | YES | PASS |
| 34_file_io | 306 | 17.3 | 1 | 136 | YES | PASS |
| 35_stdin | 236 | 13.6 | 1 | 134 | YES | PASS |
| 36_crypto | 265 | 15.0 | 1 | 147 | YES | PASS |
| 37_regex | 276 | 15.7 | 1 | 146 | YES | PASS |
| 38_http | 227 | 13.2 | 1 | 143 | YES | PASS |
| 39_gpu_detect | 254 | 14.4 | 1 | 132 | YES | PASS |
| 40_gpu_tensor | 441 | 23.1 | 1 | 187 | YES | PASS |
| 41_module_let | 225 | 12.7 | 2 | 226 | YES | PASS |
| 42_module_let_string | 228 | 12.9 | 2 | 155 | YES | PASS |
| 43_module_let_math | 232 | 13.1 | 2 | 128 | YES | PASS |
| 45_ffi_bind | 260 | 13.6 | 3 | 141 | YES | PASS |
| 47_try_operator | 359 | 18.2 | 4 | 239 | YES | PASS |
| 48_match_nested_exhaustive | 456 | 22.9 | 3 | 182 | YES | PASS |
| 49_match_guards | 317 | 16.2 | 2 | 165 | YES | PASS |
| 49_tensor_literal | 488 | 24.9 | 1 | 149 | YES | PASS |
| 50_match_or_patterns | 301 | 16.2 | 2 | 148 | YES | PASS |
| 50_tensor_indexing | 460 | 23.6 | 1 | 158 | YES | PASS |
| 51_match_guards_and_or | 383 | 19.0 | 2 | 185 | YES | PASS |
| 51_tensor_broadcast | 472 | 23.8 | 1 | 166 | YES | PASS |
| 52_tensor_slicing | 470 | 24.1 | 1 | 149 | YES | PASS |
| 53_linear_regression | 394 | 20.2 | 1 | 160 | YES | PASS |
| 54_const_basic | 231 | 13.3 | 1 | 125 | YES | PASS |
| 55_async_basic | 273 | 14.8 | 2 | 156 | YES | PASS |
| 56_async_await | 352 | 17.7 | 3 | 154 | YES | PASS |
| 57_real_await | 508 | 23.4 | 5 | 142 | YES | PASS |
| 58_async_file_io | 435 | 20.7 | 4 | 241 | YES | PASS |
| 58_const_scope | 264 | 14.2 | 2 | 154 | YES | PASS |
| 59_async_fanout | 1061 | 44.4 | 12 | 164 | YES | PASS |
| 62_list_output | 392 | 21.2 | 3 | 158 | YES | PASS |
| 63_else_sino | 320 | 16.1 | 3 | 146 | YES | PASS |
| 64_closure_typed | 333 | 16.3 | 3 | 156 | YES | PASS |
| 65_list_int_indexing | 410 | 21.6 | 1 | 179 | YES | PASS |
| 66_qualified_type_ref | 247 | 13.7 | 2 | 148 | YES | PASS |
| 67_implicit_return_one_liner | 274 | 14.3 | 4 | 141 | YES | PASS |
| 68_terse_lambda | 323 | 15.9 | 3 | 152 | YES | PASS |
| 69_list_comp | 375 | 19.9 | 1 | 181 | YES | PASS |
| 70_list_comp_filter | 384 | 20.1 | 1 | 201 | YES | PASS |
| 71_map_comp | 272 | 14.9 | 1 | 177 | YES | PASS |
| 72_string_interp_var | 227 | 13.2 | 1 | 195 | YES | PASS |
| 73_string_interp_int | 227 | 13.1 | 1 | 167 | YES | PASS |
| 74_string_interp_float | 227 | 13.1 | 1 | 155 | YES | PASS |
| 75_string_interp_bool | 228 | 13.1 | 1 | 113 | YES | PASS |
| 76_string_interp_method | 226 | 13.0 | 1 | 143 | YES | PASS |
| 77_string_interp_arith | 226 | 13.1 | 1 | 178 | YES | PASS |
| 78_string_interp_multi | 243 | 13.8 | 1 | 238 | YES | PASS |
| 79_string_interp_mixed | 237 | 13.7 | 1 | 201 | YES | PASS |
| 80_string_interp_escaped | 211 | 12.5 | 1 | 112 | YES | PASS |
| 81_struct_shorthand | 264 | 14.6 | 1 | 133 | YES | PASS |
| 82_struct_update | 260 | 14.6 | 1 | 154 | YES | PASS |
| 83_struct_update_partial | 273 | 15.1 | 1 | 167 | YES | PASS |
| 84_let_destructure | 239 | 13.5 | 1 | 162 | YES | PASS |
| 85_let_destructure_nested | 250 | 14.0 | 1 | 148 | YES | PASS |
| 86_let_destructure_rest | 229 | 13.1 | 1 | 192 | YES | PASS |
| 87_let_destructure_mut | 243 | 13.6 | 1 | 175 | YES | PASS |
| 88_if_let | 242 | 13.4 | 1 | 170 | YES | PASS |
| 89_if_let_else | 237 | 13.3 | 1 | 148 | YES | PASS |
| 90_while_let | 245 | 13.4 | 1 | 160 | YES | PASS |
| 91_let_else | 269 | 14.4 | 2 | 151 | YES | PASS |
| 92_chained_cmp_simple | 285 | 15.1 | 2 | 155 | YES | PASS |
| 93_chained_cmp_4 | 293 | 15.3 | 2 | 152 | YES | PASS |
| 94_chained_cmp_mixed | 340 | 16.8 | 4 | 133 | YES | PASS |
| 95_chained_cmp_side_effect | 308 | 16.2 | 3 | 133 | YES | PASS |
| 96_tensor_reshape | 800 | 39.4 | 1 | 144 | YES | PASS |
| 97_tensor_view_aliasing | 546 | 27.4 | 1 | 188 | YES | PASS |
| 98_tensor_stepped_slice | 618 | 30.7 | 1 | 166 | YES | PASS |
| 99_tensor_reshape_aliased | 596 | 29.7 | 1 | 141 | YES | PASS |
| **Total** | | | | **17259** | **103/103** | **103/103** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1056 | 121 | 8.7x |
| 02_arithmetic | 7 | 152 | 0.0x |
| 03_function | 5 | 127 | 0.0x |
| 04_if_else | 6 | 141 | 0.0x |
| 05_for_loop | 5 | 157 | 0.0x |
| 06_struct | 7 | 154 | 0.0x |
| 07_enum_match | 12 | 163 | 0.1x |
| 08_list | 8 | 142 | 0.1x |
| 09_string_methods | 5 | 139 | 0.0x |
| 100_result_complex_destructure | 13 | 185 | 0.1x |
| 101_match_rewrap_propagation | 11 | 264 | 0.0x |
| 102_nested_15arm_match | 14 | 197 | 0.1x |
| 103_variant_name_collision | 10 | 182 | 0.1x |
| 10_result | 7 | 196 | 0.0x |
| 11_closure | 5 | 174 | 0.0x |
| 12_while | 6 | 212 | 0.0x |
| 13_fib | 7 | 188 | 0.0x |
| 14_nested_struct | 7 | 174 | 0.0x |
| 15_multifunction | 6 | 178 | 0.0x |
| 16_string_escape | 5 | 162 | 0.0x |
| 17_option | 8 | 193 | 0.0x |
| 18_method_chain | 8 | 304 | 0.0x |
| 19_nested_match | 12 | 271 | 0.0x |
| 20_recursion | 6 | 174 | 0.0x |
| 21_list_ops | 9 | 160 | 0.1x |
| 22_string_builder | 5 | 192 | 0.0x |
| 23_multi_return | 8 | 203 | 0.0x |
| 24_enum_methods | 6 | 184 | 0.0x |
| 25_fizzbuzz | 6 | 149 | 0.0x |
| 26_generics | 7 | 184 | 0.0x |
| 27_impl | 8 | 161 | 0.0x |
| 28_traits | 7 | 193 | 0.0x |
| 29_generic_impl | 6 | 166 | 0.0x |
| 30_nested_generics | 5 | 138 | 0.0x |
| 31_generic_multi | 8 | 210 | 0.0x |
| 32_generic_enum | 6 | 162 | 0.0x |
| 33_break_continue | 10 | 183 | 0.1x |
| 34_file_io | 6 | 136 | 0.0x |
| 35_stdin | 4 | 134 | 0.0x |
| 36_crypto | 5 | 147 | 0.0x |
| 37_regex | 5 | 146 | 0.0x |
| 38_http | 4 | 143 | 0.0x |
| 39_gpu_detect | 5 | 132 | 0.0x |
| 40_gpu_tensor | 7 | 187 | 0.0x |
| 41_module_let | 9 | 226 | 0.0x |
| 42_module_let_string | 7 | 155 | 0.0x |
| 43_module_let_math | 5 | 128 | 0.0x |
| 45_ffi_bind | 5 | 141 | 0.0x |
| 47_try_operator | 36 | 239 | 0.2x |
| 48_match_nested_exhaustive | 8 | 182 | 0.0x |
| 49_match_guards | 7 | 165 | 0.0x |
| 49_tensor_literal | 10 | 149 | 0.1x |
| 50_match_or_patterns | 6 | 148 | 0.0x |
| 50_tensor_indexing | 8 | 158 | 0.0x |
| 51_match_guards_and_or | 7 | 185 | 0.0x |
| 51_tensor_broadcast | 9 | 166 | 0.1x |
| 52_tensor_slicing | 8 | 149 | 0.1x |
| 53_linear_regression | 7 | 160 | 0.0x |
| 54_const_basic | 5 | 125 | 0.0x |
| 55_async_basic | 5 | 156 | 0.0x |
| 56_async_await | 5 | 154 | 0.0x |
| 57_real_await | 5 | 142 | 0.0x |
| 58_async_file_io | 6 | 241 | 0.0x |
| 58_const_scope | 5 | 154 | 0.0x |
| 59_async_fanout | 7 | 164 | 0.0x |
| 62_list_output | 7 | 158 | 0.0x |
| 63_else_sino | 7 | 146 | 0.0x |
| 64_closure_typed | 8 | 156 | 0.1x |
| 65_list_int_indexing | 6 | 179 | 0.0x |
| 66_qualified_type_ref | 5 | 148 | 0.0x |
| 67_implicit_return_one_liner | 6 | 141 | 0.0x |
| 68_terse_lambda | 9 | 152 | 0.1x |
| 69_list_comp | 6 | 181 | 0.0x |
| 70_list_comp_filter | 7 | 201 | 0.0x |
| 71_map_comp | 6 | 177 | 0.0x |
| 72_string_interp_var | 5 | 195 | 0.0x |
| 73_string_interp_int | 7 | 167 | 0.0x |
| 74_string_interp_float | 5 | 155 | 0.0x |
| 75_string_interp_bool | 4 | 113 | 0.0x |
| 76_string_interp_method | 5 | 143 | 0.0x |
| 77_string_interp_arith | 4 | 178 | 0.0x |
| 78_string_interp_multi | 7 | 238 | 0.0x |
| 79_string_interp_mixed | 7 | 201 | 0.0x |
| 80_string_interp_escaped | 4 | 112 | 0.0x |
| 81_struct_shorthand | 6 | 133 | 0.0x |
| 82_struct_update | 6 | 154 | 0.0x |
| 83_struct_update_partial | 6 | 167 | 0.0x |
| 84_let_destructure | 5 | 162 | 0.0x |
| 85_let_destructure_nested | 5 | 148 | 0.0x |
| 86_let_destructure_rest | 5 | 192 | 0.0x |
| 87_let_destructure_mut | 8 | 175 | 0.0x |
| 88_if_let | 6 | 170 | 0.0x |
| 89_if_let_else | 5 | 148 | 0.0x |
| 90_while_let | 8 | 160 | 0.0x |
| 91_let_else | 5 | 151 | 0.0x |
| 92_chained_cmp_simple | 8 | 155 | 0.0x |
| 93_chained_cmp_4 | 6 | 152 | 0.0x |
| 94_chained_cmp_mixed | 10 | 133 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 133 | 0.0x |
| 96_tensor_reshape | 13 | 144 | 0.1x |
| 97_tensor_view_aliasing | 10 | 188 | 0.1x |
| 98_tensor_stepped_slice | 10 | 166 | 0.1x |
| 99_tensor_reshape_aliased | 11 | 141 | 0.1x |

