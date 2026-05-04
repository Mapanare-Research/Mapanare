# Mapanare Benchmarks - Linux

Generated: 2026-05-04 22:42 UTC  
Version: 5.39.7 (`c97ef6b9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 15.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1076 | `*_______ ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 8 | `_      _ ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         v` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 5 | `     _   v` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 6 | `-        v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 6 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 5 | `_       ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 7 | `_    _  ` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `_    _  ` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `.___._  ` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 7 | `        ` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         v` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `*    _  ` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 5 | `_       ` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `_        ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 5 | `_       ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 7 | `~____   ` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `_       ` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 5 | `        ` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 4 | `_        v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | `________` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `__. __  ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 6 | `_   _    v` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 4 | `-   __ _ ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `~    _ _ ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `_        ^` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 7 | `        ` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 7 | `         ^` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 7 | `        ` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `-       ` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 5 | `_       ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         ^` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 6 | `         ^` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 7 | `_ _  _  ` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `_       ` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `*        ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 4 | `_        v` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | `-__     ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `_ __    ` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `     . - ^` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `*       ` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | `___ .  _ ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 27 | `*____ _  v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `        ` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `*       ` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 7 | `        ` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 15 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 6 | `__  .  _ ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 7 | `. _  _   ^` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 11 | `~   _- * ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `*    _ _ ^` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 5 | `_     __` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 5 | `_       ` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `-_  _ __` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `         v` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `_- _  -  v` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `_  ___.  v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 8 | `_    .   v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `-    .__` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 4 | `*      _ ^` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `    ..   ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `*_  __  ` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 8 | `- _ . __` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | `-       ` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 5 | `.        v` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `*        ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `*        v` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 4 | `- _ __.- ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `_      _ ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 4 | `___._   ` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `~____.__` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `-.      ` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `_.      ` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 8 | `-~_ _   ` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 7 | `-_  .   ` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | `*       ` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 5 | `~        v` | PASS |
| **Total** | **1540** | **16569** | **619.7** | **143** | **1333** | **14102** | **1645** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 206 | 12.1 | 1 | 240 | YES | PASS |
| 02_arithmetic | 216 | 12.4 | 1 | 232 | YES | PASS |
| 03_function | 238 | 13.0 | 2 | 154 | YES | PASS |
| 04_if_else | 223 | 12.7 | 1 | 148 | YES | PASS |
| 05_for_loop | 239 | 13.2 | 1 | 173 | YES | PASS |
| 06_struct | 219 | 12.6 | 1 | 160 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 162 | YES | PASS |
| 08_list | 245 | 13.9 | 1 | 136 | YES | PASS |
| 09_string_methods | 229 | 13.2 | 1 | 133 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 134 | YES | PASS |
| 11_closure | 229 | 12.7 | 1 | 128 | YES | PASS |
| 12_while | 225 | 12.6 | 1 | 107 | YES | PASS |
| 13_fib | 236 | 12.8 | 2 | 131 | YES | PASS |
| 14_nested_struct | 219 | 12.6 | 1 | 145 | YES | PASS |
| 15_multifunction | 249 | 13.4 | 3 | 173 | YES | PASS |
| 16_string_escape | 225 | 13.0 | 1 | 119 | YES | PASS |
| 17_option | 308 | 15.7 | 2 | 151 | YES | PASS |
| 18_method_chain | 251 | 14.2 | 1 | 131 | YES | PASS |
| 19_nested_match | 274 | 14.4 | 2 | 161 | YES | PASS |
| 20_recursion | 242 | 13.1 | 2 | 143 | YES | PASS |
| 21_list_ops | 327 | 17.3 | 2 | 154 | YES | PASS |
| 22_string_builder | 294 | 15.7 | 2 | 152 | YES | PASS |
| 23_multi_return | 268 | 14.7 | 2 | 129 | YES | PASS |
| 24_enum_methods | 262 | 14.2 | 2 | 149 | YES | PASS |
| 25_fizzbuzz | 306 | 15.5 | 2 | 146 | YES | PASS |
| 26_generics | 286 | 14.6 | 5 | 133 | YES | PASS |
| 27_impl | 246 | 13.4 | 3 | 145 | YES | PASS |
| 28_traits | 254 | 13.7 | 3 | 135 | YES | PASS |
| 29_generic_impl | 255 | 13.9 | 3 | 128 | YES | PASS |
| 30_nested_generics | 246 | 14.2 | 1 | 186 | YES | PASS |
| 31_generic_multi | 271 | 14.7 | 4 | 122 | YES | PASS |
| 32_generic_enum | 217 | 12.5 | 1 | 104 | YES | PASS |
| 33_break_continue | 430 | 19.3 | 5 | 142 | YES | PASS |
| 34_file_io | 301 | 17.0 | 1 | 113 | YES | PASS |
| 35_stdin | 231 | 13.3 | 1 | 118 | YES | PASS |
| 36_crypto | 260 | 14.8 | 1 | 131 | YES | PASS |
| 37_regex | 271 | 15.4 | 1 | 130 | YES | PASS |
| 38_http | 222 | 12.9 | 1 | 137 | YES | PASS |
| 39_gpu_detect | 249 | 14.1 | 1 | 135 | YES | PASS |
| 40_gpu_tensor | 436 | 22.8 | 1 | 149 | YES | PASS |
| 41_module_let | 220 | 12.4 | 2 | 111 | YES | PASS |
| 42_module_let_string | 223 | 12.6 | 2 | 117 | YES | PASS |
| 43_module_let_math | 227 | 12.8 | 2 | 119 | YES | PASS |
| 45_ffi_bind | 255 | 13.3 | 3 | 136 | YES | PASS |
| 47_try_operator | 354 | 18.0 | 4 | 159 | YES | PASS |
| 48_match_nested_exhaustive | 451 | 22.6 | 3 | 192 | YES | PASS |
| 49_match_guards | 312 | 15.9 | 2 | 159 | YES | PASS |
| 49_tensor_literal | 483 | 24.6 | 1 | 131 | YES | PASS |
| 50_match_or_patterns | 296 | 15.9 | 2 | 150 | YES | PASS |
| 50_tensor_indexing | 455 | 23.3 | 1 | 121 | YES | PASS |
| 51_match_guards_and_or | 378 | 18.7 | 2 | 133 | YES | PASS |
| 51_tensor_broadcast | 467 | 23.5 | 1 | 117 | YES | PASS |
| 52_tensor_slicing | 462 | 23.7 | 1 | 128 | YES | PASS |
| 53_linear_regression | 389 | 19.9 | 1 | 139 | YES | PASS |
| 54_const_basic | 226 | 13.0 | 1 | 102 | YES | PASS |
| 55_async_basic | 268 | 14.5 | 2 | 118 | YES | PASS |
| 56_async_await | 347 | 17.4 | 3 | 127 | YES | PASS |
| 57_real_await | 503 | 23.1 | 5 | 141 | YES | PASS |
| 58_async_file_io | 430 | 20.4 | 4 | 146 | YES | PASS |
| 58_const_scope | 259 | 13.9 | 2 | 137 | YES | PASS |
| 59_async_fanout | 1056 | 44.1 | 12 | 133 | YES | PASS |
| 62_list_output | 387 | 20.9 | 3 | 206 | YES | PASS |
| 63_else_sino | 315 | 15.8 | 3 | 146 | YES | PASS |
| 64_closure_typed | 328 | 16.0 | 3 | 147 | YES | PASS |
| 65_list_int_indexing | 405 | 21.3 | 1 | 222 | YES | PASS |
| 66_qualified_type_ref | 242 | 13.4 | 2 | 210 | YES | PASS |
| 67_implicit_return_one_liner | 269 | 14.0 | 4 | 200 | YES | PASS |
| 68_terse_lambda | 318 | 15.6 | 3 | 210 | YES | PASS |
| 69_list_comp | 370 | 19.6 | 1 | 190 | YES | PASS |
| 70_list_comp_filter | 379 | 19.8 | 1 | 164 | YES | PASS |
| 71_map_comp | 267 | 14.6 | 1 | 144 | YES | PASS |
| 72_string_interp_var | 222 | 12.9 | 1 | 115 | YES | PASS |
| 73_string_interp_int | 222 | 12.8 | 1 | 104 | YES | PASS |
| 74_string_interp_float | 222 | 12.8 | 1 | 106 | YES | PASS |
| 75_string_interp_bool | 223 | 12.8 | 1 | 129 | YES | PASS |
| 76_string_interp_method | 221 | 12.7 | 1 | 166 | YES | PASS |
| 77_string_interp_arith | 221 | 12.8 | 1 | 122 | YES | PASS |
| 78_string_interp_multi | 238 | 13.5 | 1 | 121 | YES | PASS |
| 79_string_interp_mixed | 232 | 13.4 | 1 | 121 | YES | PASS |
| 80_string_interp_escaped | 206 | 12.2 | 1 | 108 | YES | PASS |
| 81_struct_shorthand | 259 | 14.3 | 1 | 136 | YES | PASS |
| 82_struct_update | 255 | 14.3 | 1 | 141 | YES | PASS |
| 83_struct_update_partial | 268 | 14.8 | 1 | 139 | YES | PASS |
| 84_let_destructure | 234 | 13.2 | 1 | 136 | YES | PASS |
| 85_let_destructure_nested | 245 | 13.7 | 1 | 136 | YES | PASS |
| 86_let_destructure_rest | 224 | 12.8 | 1 | 133 | YES | PASS |
| 87_let_destructure_mut | 238 | 13.3 | 1 | 137 | YES | PASS |
| 88_if_let | 237 | 13.1 | 1 | 130 | YES | PASS |
| 89_if_let_else | 232 | 13.0 | 1 | 137 | YES | PASS |
| 90_while_let | 240 | 13.2 | 1 | 139 | YES | PASS |
| 91_let_else | 264 | 14.1 | 2 | 152 | YES | PASS |
| 92_chained_cmp_simple | 280 | 14.8 | 2 | 180 | YES | PASS |
| 93_chained_cmp_4 | 288 | 15.0 | 2 | 116 | YES | PASS |
| 94_chained_cmp_mixed | 335 | 16.5 | 4 | 113 | YES | PASS |
| 95_chained_cmp_side_effect | 303 | 15.9 | 3 | 116 | YES | PASS |
| **Total** | | | | **13587** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1076 | 240 | 4.5x |
| 02_arithmetic | 8 | 232 | 0.0x |
| 03_function | 6 | 154 | 0.0x |
| 04_if_else | 5 | 148 | 0.0x |
| 05_for_loop | 6 | 173 | 0.0x |
| 06_struct | 6 | 160 | 0.0x |
| 07_enum_match | 13 | 162 | 0.1x |
| 08_list | 7 | 136 | 0.0x |
| 09_string_methods | 4 | 133 | 0.0x |
| 10_result | 6 | 134 | 0.0x |
| 11_closure | 5 | 128 | 0.0x |
| 12_while | 4 | 107 | 0.0x |
| 13_fib | 5 | 131 | 0.0x |
| 14_nested_struct | 5 | 145 | 0.0x |
| 15_multifunction | 7 | 173 | 0.0x |
| 16_string_escape | 5 | 119 | 0.0x |
| 17_option | 6 | 151 | 0.0x |
| 18_method_chain | 5 | 131 | 0.0x |
| 19_nested_match | 7 | 161 | 0.0x |
| 20_recursion | 5 | 143 | 0.0x |
| 21_list_ops | 6 | 154 | 0.0x |
| 22_string_builder | 6 | 152 | 0.0x |
| 23_multi_return | 5 | 129 | 0.0x |
| 24_enum_methods | 5 | 149 | 0.0x |
| 25_fizzbuzz | 5 | 146 | 0.0x |
| 26_generics | 7 | 133 | 0.0x |
| 27_impl | 6 | 145 | 0.0x |
| 28_traits | 5 | 135 | 0.0x |
| 29_generic_impl | 5 | 128 | 0.0x |
| 30_nested_generics | 7 | 186 | 0.0x |
| 31_generic_multi | 7 | 122 | 0.1x |
| 32_generic_enum | 4 | 104 | 0.0x |
| 33_break_continue | 9 | 142 | 0.1x |
| 34_file_io | 5 | 113 | 0.0x |
| 35_stdin | 4 | 118 | 0.0x |
| 36_crypto | 4 | 131 | 0.0x |
| 37_regex | 5 | 130 | 0.0x |
| 38_http | 4 | 137 | 0.0x |
| 39_gpu_detect | 5 | 135 | 0.0x |
| 40_gpu_tensor | 6 | 149 | 0.0x |
| 41_module_let | 4 | 111 | 0.0x |
| 42_module_let_string | 4 | 117 | 0.0x |
| 43_module_let_math | 5 | 119 | 0.0x |
| 45_ffi_bind | 5 | 136 | 0.0x |
| 47_try_operator | 7 | 159 | 0.0x |
| 48_match_nested_exhaustive | 7 | 192 | 0.0x |
| 49_match_guards | 7 | 159 | 0.0x |
| 49_tensor_literal | 10 | 131 | 0.1x |
| 50_match_or_patterns | 5 | 150 | 0.0x |
| 50_tensor_indexing | 8 | 121 | 0.1x |
| 51_match_guards_and_or | 6 | 133 | 0.0x |
| 51_tensor_broadcast | 7 | 117 | 0.1x |
| 52_tensor_slicing | 8 | 128 | 0.1x |
| 53_linear_regression | 6 | 139 | 0.0x |
| 54_const_basic | 4 | 102 | 0.0x |
| 55_async_basic | 4 | 118 | 0.0x |
| 56_async_await | 5 | 127 | 0.0x |
| 57_real_await | 5 | 141 | 0.0x |
| 58_async_file_io | 5 | 146 | 0.0x |
| 58_const_scope | 5 | 137 | 0.0x |
| 59_async_fanout | 27 | 133 | 0.2x |
| 62_list_output | 7 | 206 | 0.0x |
| 63_else_sino | 7 | 146 | 0.1x |
| 64_closure_typed | 7 | 147 | 0.0x |
| 65_list_int_indexing | 15 | 222 | 0.1x |
| 66_qualified_type_ref | 6 | 210 | 0.0x |
| 67_implicit_return_one_liner | 7 | 200 | 0.0x |
| 68_terse_lambda | 11 | 210 | 0.1x |
| 69_list_comp | 6 | 190 | 0.0x |
| 70_list_comp_filter | 5 | 164 | 0.0x |
| 71_map_comp | 5 | 144 | 0.0x |
| 72_string_interp_var | 4 | 115 | 0.0x |
| 73_string_interp_int | 4 | 104 | 0.0x |
| 74_string_interp_float | 4 | 106 | 0.0x |
| 75_string_interp_bool | 4 | 129 | 0.0x |
| 76_string_interp_method | 8 | 166 | 0.0x |
| 77_string_interp_arith | 4 | 122 | 0.0x |
| 78_string_interp_multi | 4 | 121 | 0.0x |
| 79_string_interp_mixed | 4 | 121 | 0.0x |
| 80_string_interp_escaped | 4 | 108 | 0.0x |
| 81_struct_shorthand | 8 | 136 | 0.1x |
| 82_struct_update | 6 | 141 | 0.0x |
| 83_struct_update_partial | 5 | 139 | 0.0x |
| 84_let_destructure | 5 | 136 | 0.0x |
| 85_let_destructure_nested | 5 | 136 | 0.0x |
| 86_let_destructure_rest | 4 | 133 | 0.0x |
| 87_let_destructure_mut | 5 | 137 | 0.0x |
| 88_if_let | 4 | 130 | 0.0x |
| 89_if_let_else | 5 | 137 | 0.0x |
| 90_while_let | 5 | 139 | 0.0x |
| 91_let_else | 5 | 152 | 0.0x |
| 92_chained_cmp_simple | 8 | 180 | 0.0x |
| 93_chained_cmp_4 | 7 | 116 | 0.1x |
| 94_chained_cmp_mixed | 8 | 113 | 0.1x |
| 95_chained_cmp_side_effect | 5 | 116 | 0.0x |

