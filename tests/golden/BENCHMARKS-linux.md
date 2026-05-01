# Mapanare Benchmarks - Linux

Generated: 2026-05-01 12:39 UTC  
Version: 5.23.1 (`9b91a68`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 17.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 919 | `...._... v` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 7 | `         ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 5 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 6 | `        ` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 19 | `        ` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 7 | `        ` | PASS |
| 10_result | 10 | 147 | 5.3 | 2 | 10 | 155 | 8 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 7 | `        ` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `___ ___  v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 7 | `        ` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `__._  __` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 9 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 7 | `        ` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 8 | `        ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 6 | ` _       v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 6 | `     _  ` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         v` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 6 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `_  _    ` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` __-____` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `  _.    ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         v` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `  _      v` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         v` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | ` _  __._ v` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `     _ _ ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `         v` | PASS |
| 47_try_operator | 25 | 306 | 11.7 | 4 | 23 | 311 | 8 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         v` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 7 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 11 | `        ` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `_        v` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `        ` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `        ` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 10 | `   _   _ ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `        ` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 7 | `__    _  v` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 6 | `        ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | `_       ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 6 | ` _   __  v` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 6 | `    ~ *  v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 6 | `.  .  _  v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `  _   _  v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 25 | `-__. . . ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | ` _  _ __` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 7 | `        ` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `   _  _  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 5 | `        ` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 8 | ` .    _* ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 7 | `_ __-._- ^` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 9 | `    .~   ^` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | `        ` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 5 | ` .._   _ ^` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `         ^` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` _ ___ _ ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `.     _. ^` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 4 | `   __ _  v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `  _     ` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `_  _ __  v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `      _  v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | ` __.____` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 5 | ` _  _ .  v` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 6 | `       _ ^` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 8 | ` _      ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 6 | ` _ -._  ` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `   . _  ` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `     _  ` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 19 | `  _  .  ` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 7 | `  .     ` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | ` _____-_ v` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `_     _  v` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 6 | `  -   -  v` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 8 | `        ` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 7 | `   _    ` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | ` _    .  v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 9 | `_       ` | PASS |
| **Total** | **1540** | **16603** | **621.1** | **143** | **1333** | **14182** | **1541** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 204 | 11.9 | 1 | 128 | YES | PASS |
| 02_arithmetic | 214 | 12.2 | 1 | 124 | YES | PASS |
| 03_function | 236 | 12.9 | 2 | 135 | YES | PASS |
| 04_if_else | 221 | 12.5 | 1 | 162 | YES | PASS |
| 05_for_loop | 237 | 13.1 | 1 | 151 | YES | PASS |
| 06_struct | 217 | 12.4 | 1 | 131 | YES | PASS |
| 07_enum_match | 225 | 12.7 | 1 | 205 | YES | PASS |
| 08_list | 243 | 13.7 | 1 | 236 | YES | PASS |
| 09_string_methods | 227 | 13.1 | 1 | 187 | YES | PASS |
| 10_result | 270 | 14.5 | 2 | 191 | YES | PASS |
| 11_closure | 227 | 12.6 | 1 | 144 | YES | PASS |
| 12_while | 223 | 12.5 | 1 | 140 | YES | PASS |
| 13_fib | 234 | 12.7 | 2 | 238 | YES | PASS |
| 14_nested_struct | 217 | 12.4 | 1 | 175 | YES | PASS |
| 15_multifunction | 247 | 13.2 | 3 | 159 | YES | PASS |
| 16_string_escape | 223 | 12.9 | 1 | 139 | YES | PASS |
| 17_option | 306 | 15.5 | 2 | 171 | YES | PASS |
| 18_method_chain | 249 | 14.1 | 1 | 157 | YES | PASS |
| 19_nested_match | 272 | 14.2 | 2 | 197 | YES | PASS |
| 20_recursion | 240 | 13.0 | 2 | 151 | YES | PASS |
| 21_list_ops | 325 | 17.1 | 2 | 191 | YES | PASS |
| 22_string_builder | 292 | 15.6 | 2 | 201 | YES | PASS |
| 23_multi_return | 266 | 14.5 | 2 | 251 | YES | PASS |
| 24_enum_methods | 260 | 14.1 | 2 | 207 | YES | PASS |
| 25_fizzbuzz | 304 | 15.3 | 2 | 174 | YES | PASS |
| 26_generics | 284 | 14.5 | 5 | 202 | YES | PASS |
| 27_impl | 244 | 13.3 | 3 | 150 | YES | PASS |
| 28_traits | 252 | 13.5 | 3 | 154 | YES | PASS |
| 29_generic_impl | 253 | 13.7 | 3 | 180 | YES | PASS |
| 30_nested_generics | 244 | 14.1 | 1 | 134 | YES | PASS |
| 31_generic_multi | 269 | 14.6 | 4 | 144 | YES | PASS |
| 32_generic_enum | 215 | 12.3 | 1 | 144 | YES | PASS |
| 33_break_continue | 428 | 19.1 | 5 | 182 | YES | PASS |
| 34_file_io | 299 | 16.9 | 1 | 132 | YES | PASS |
| 35_stdin | 229 | 13.2 | 1 | 142 | YES | PASS |
| 36_crypto | 258 | 14.6 | 1 | 142 | YES | PASS |
| 37_regex | 269 | 15.3 | 1 | 135 | YES | PASS |
| 38_http | 220 | 12.7 | 1 | 144 | YES | PASS |
| 39_gpu_detect | 247 | 13.9 | 1 | 151 | YES | PASS |
| 40_gpu_tensor | 434 | 22.6 | 1 | 235 | YES | PASS |
| 41_module_let | 218 | 12.2 | 2 | 128 | YES | PASS |
| 42_module_let_string | 221 | 12.4 | 2 | 126 | YES | PASS |
| 43_module_let_math | 225 | 12.6 | 2 | 118 | YES | PASS |
| 45_ffi_bind | 253 | 13.2 | 3 | 140 | YES | PASS |
| 47_try_operator | 352 | 17.8 | 4 | 167 | YES | PASS |
| 48_match_nested_exhaustive | 449 | 22.4 | 3 | 149 | YES | PASS |
| 49_match_guards | 276 | 14.8 | 2 | 161 | YES | PASS |
| 49_tensor_literal | 481 | 24.4 | 1 | 146 | YES | PASS |
| 50_match_or_patterns | 294 | 15.8 | 2 | 145 | YES | PASS |
| 50_tensor_indexing | 453 | 23.2 | 1 | 141 | YES | PASS |
| 51_match_guards_and_or | 365 | 18.2 | 2 | 162 | YES | PASS |
| 51_tensor_broadcast | 465 | 23.3 | 1 | 135 | YES | PASS |
| 52_tensor_slicing | 460 | 23.5 | 1 | 164 | YES | PASS |
| 53_linear_regression | 387 | 19.8 | 1 | 230 | YES | PASS |
| 54_const_basic | 224 | 12.8 | 1 | 129 | YES | PASS |
| 55_async_basic | 266 | 14.3 | 2 | 154 | YES | PASS |
| 56_async_await | 345 | 17.2 | 3 | 152 | YES | PASS |
| 57_real_await | 501 | 23.0 | 5 | 137 | YES | PASS |
| 58_async_file_io | 428 | 20.2 | 4 | 151 | YES | PASS |
| 58_const_scope | 257 | 13.7 | 2 | 167 | YES | PASS |
| 59_async_fanout | 1054 | 44.0 | 12 | 139 | YES | PASS |
| 62_list_output | 385 | 20.8 | 3 | 160 | YES | PASS |
| 63_else_sino | 313 | 15.6 | 3 | 159 | YES | PASS |
| 64_closure_typed | 326 | 15.8 | 3 | 145 | YES | PASS |
| 65_list_int_indexing | 403 | 21.1 | 1 | 167 | YES | PASS |
| 66_qualified_type_ref | 240 | 13.3 | 2 | 144 | YES | PASS |
| 67_implicit_return_one_liner | 267 | 13.9 | 4 | 133 | YES | PASS |
| 68_terse_lambda | 316 | 15.4 | 3 | 208 | YES | PASS |
| 69_list_comp | 368 | 19.5 | 1 | 255 | YES | PASS |
| 70_list_comp_filter | 377 | 19.7 | 1 | 228 | YES | PASS |
| 71_map_comp | 265 | 14.4 | 1 | 179 | YES | PASS |
| 72_string_interp_var | 220 | 12.7 | 1 | 128 | YES | PASS |
| 73_string_interp_int | 220 | 12.7 | 1 | 121 | YES | PASS |
| 74_string_interp_float | 220 | 12.7 | 1 | 135 | YES | PASS |
| 75_string_interp_bool | 221 | 12.7 | 1 | 128 | YES | PASS |
| 76_string_interp_method | 219 | 12.6 | 1 | 141 | YES | PASS |
| 77_string_interp_arith | 219 | 12.6 | 1 | 130 | YES | PASS |
| 78_string_interp_multi | 236 | 13.4 | 1 | 141 | YES | PASS |
| 79_string_interp_mixed | 230 | 13.2 | 1 | 128 | YES | PASS |
| 80_string_interp_escaped | 204 | 12.0 | 1 | 116 | YES | PASS |
| 81_struct_shorthand | 257 | 14.2 | 1 | 151 | YES | PASS |
| 82_struct_update | 253 | 14.1 | 1 | 210 | YES | PASS |
| 83_struct_update_partial | 266 | 14.7 | 1 | 182 | YES | PASS |
| 84_let_destructure | 232 | 13.0 | 1 | 158 | YES | PASS |
| 85_let_destructure_nested | 243 | 13.5 | 1 | 144 | YES | PASS |
| 86_let_destructure_rest | 222 | 12.6 | 1 | 169 | YES | PASS |
| 87_let_destructure_mut | 236 | 13.1 | 1 | 262 | YES | PASS |
| 88_if_let | 235 | 13.0 | 1 | 190 | YES | PASS |
| 89_if_let_else | 230 | 12.9 | 1 | 156 | YES | PASS |
| 90_while_let | 238 | 13.0 | 1 | 156 | YES | PASS |
| 91_let_else | 262 | 14.0 | 2 | 151 | YES | PASS |
| 92_chained_cmp_simple | 278 | 14.6 | 2 | 225 | YES | PASS |
| 93_chained_cmp_4 | 286 | 14.8 | 2 | 163 | YES | PASS |
| 94_chained_cmp_mixed | 333 | 16.4 | 4 | 164 | YES | PASS |
| 95_chained_cmp_side_effect | 301 | 15.8 | 3 | 200 | YES | PASS |
| **Total** | | | | **15485** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 919 | 128 | 7.2x |
| 02_arithmetic | 7 | 124 | 0.1x |
| 03_function | 5 | 135 | 0.0x |
| 04_if_else | 6 | 162 | 0.0x |
| 05_for_loop | 5 | 151 | 0.0x |
| 06_struct | 6 | 131 | 0.0x |
| 07_enum_match | 12 | 205 | 0.1x |
| 08_list | 19 | 236 | 0.1x |
| 09_string_methods | 7 | 187 | 0.0x |
| 10_result | 8 | 191 | 0.0x |
| 11_closure | 5 | 144 | 0.0x |
| 12_while | 4 | 140 | 0.0x |
| 13_fib | 6 | 238 | 0.0x |
| 14_nested_struct | 7 | 175 | 0.0x |
| 15_multifunction | 5 | 159 | 0.0x |
| 16_string_escape | 5 | 139 | 0.0x |
| 17_option | 7 | 171 | 0.0x |
| 18_method_chain | 5 | 157 | 0.0x |
| 19_nested_match | 7 | 197 | 0.0x |
| 20_recursion | 5 | 151 | 0.0x |
| 21_list_ops | 6 | 191 | 0.0x |
| 22_string_builder | 6 | 201 | 0.0x |
| 23_multi_return | 9 | 251 | 0.0x |
| 24_enum_methods | 7 | 207 | 0.0x |
| 25_fizzbuzz | 5 | 174 | 0.0x |
| 26_generics | 8 | 202 | 0.0x |
| 27_impl | 6 | 150 | 0.0x |
| 28_traits | 8 | 154 | 0.1x |
| 29_generic_impl | 6 | 180 | 0.0x |
| 30_nested_generics | 6 | 134 | 0.0x |
| 31_generic_multi | 7 | 144 | 0.1x |
| 32_generic_enum | 4 | 144 | 0.0x |
| 33_break_continue | 9 | 182 | 0.0x |
| 34_file_io | 6 | 132 | 0.0x |
| 35_stdin | 4 | 142 | 0.0x |
| 36_crypto | 5 | 142 | 0.0x |
| 37_regex | 5 | 135 | 0.0x |
| 38_http | 4 | 144 | 0.0x |
| 39_gpu_detect | 5 | 151 | 0.0x |
| 40_gpu_tensor | 7 | 235 | 0.0x |
| 41_module_let | 5 | 128 | 0.0x |
| 42_module_let_string | 5 | 126 | 0.0x |
| 43_module_let_math | 5 | 118 | 0.0x |
| 45_ffi_bind | 5 | 140 | 0.0x |
| 47_try_operator | 8 | 167 | 0.0x |
| 48_match_nested_exhaustive | 6 | 149 | 0.0x |
| 49_match_guards | 7 | 161 | 0.0x |
| 49_tensor_literal | 11 | 146 | 0.1x |
| 50_match_or_patterns | 6 | 145 | 0.0x |
| 50_tensor_indexing | 8 | 141 | 0.1x |
| 51_match_guards_and_or | 7 | 162 | 0.0x |
| 51_tensor_broadcast | 10 | 135 | 0.1x |
| 52_tensor_slicing | 8 | 164 | 0.0x |
| 53_linear_regression | 7 | 230 | 0.0x |
| 54_const_basic | 6 | 129 | 0.0x |
| 55_async_basic | 5 | 154 | 0.0x |
| 56_async_await | 6 | 152 | 0.0x |
| 57_real_await | 6 | 137 | 0.0x |
| 58_async_file_io | 6 | 151 | 0.0x |
| 58_const_scope | 6 | 167 | 0.0x |
| 59_async_fanout | 25 | 139 | 0.2x |
| 62_list_output | 7 | 160 | 0.0x |
| 63_else_sino | 7 | 159 | 0.0x |
| 64_closure_typed | 7 | 145 | 0.1x |
| 65_list_int_indexing | 6 | 167 | 0.0x |
| 66_qualified_type_ref | 5 | 144 | 0.0x |
| 67_implicit_return_one_liner | 5 | 133 | 0.0x |
| 68_terse_lambda | 8 | 208 | 0.0x |
| 69_list_comp | 7 | 255 | 0.0x |
| 70_list_comp_filter | 9 | 228 | 0.0x |
| 71_map_comp | 6 | 179 | 0.0x |
| 72_string_interp_var | 5 | 128 | 0.0x |
| 73_string_interp_int | 4 | 121 | 0.0x |
| 74_string_interp_float | 4 | 135 | 0.0x |
| 75_string_interp_bool | 4 | 128 | 0.0x |
| 76_string_interp_method | 4 | 141 | 0.0x |
| 77_string_interp_arith | 4 | 130 | 0.0x |
| 78_string_interp_multi | 5 | 141 | 0.0x |
| 79_string_interp_mixed | 4 | 128 | 0.0x |
| 80_string_interp_escaped | 4 | 116 | 0.0x |
| 81_struct_shorthand | 5 | 151 | 0.0x |
| 82_struct_update | 6 | 210 | 0.0x |
| 83_struct_update_partial | 8 | 182 | 0.0x |
| 84_let_destructure | 6 | 158 | 0.0x |
| 85_let_destructure_nested | 5 | 144 | 0.0x |
| 86_let_destructure_rest | 5 | 169 | 0.0x |
| 87_let_destructure_mut | 19 | 262 | 0.1x |
| 88_if_let | 7 | 190 | 0.0x |
| 89_if_let_else | 5 | 156 | 0.0x |
| 90_while_let | 5 | 156 | 0.0x |
| 91_let_else | 6 | 151 | 0.0x |
| 92_chained_cmp_simple | 8 | 225 | 0.0x |
| 93_chained_cmp_4 | 7 | 163 | 0.0x |
| 94_chained_cmp_mixed | 8 | 164 | 0.0x |
| 95_chained_cmp_side_effect | 9 | 200 | 0.0x |

