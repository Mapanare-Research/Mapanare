# Mapanare Benchmarks - Linux

Generated: 2026-05-01 09:08 UTC  
Version: 5.21.1 (`24d5be7`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 26.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1109 | `._._.... ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 7 | `   _     v` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 9 | `    _   ` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 8 | `         v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         v` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 15 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 8 | `         v` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `        ` | PASS |
| 10_result | 10 | 147 | 5.3 | 2 | 10 | 155 | 8 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 6 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 7 | `        ` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 9 | `        ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 8 | `         ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 6 | `      _  v` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 8 | `         v` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 6 | `._._.._. ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 10 | `         v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 7 | `         ^` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 9 | `        ` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 10 | `    _.__` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 8 | ` _      ` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 7 | `         ^` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 8 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 9 | `         ^` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 8 | `         v` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 7 | `        ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 9 | `_    _ _ ^` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `     _ _ ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 11 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 9 | `        ` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 6 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 7 | `___    . ^` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 9 | `_____.__` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 10 | `  .  .__` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 7 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 8 | `     __  v` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 7 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 9 | `. _ _*_. ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 12 | `_ _ __  ` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 8 | `   _ _   v` | PASS |
| 47_try_operator | 25 | 306 | 11.7 | 4 | 23 | 311 | 12 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 345 | 14.0 | 3 | 32 | 325 | 11 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 7 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 12 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 8 | `    __  ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 14 | `  _      v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 8 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 11 | `     _ _ ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 11 | `_     _  v` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 8 | `-    ._  v` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | ` _     _ ^` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 6 | `___  ___ ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 6 | `__   ___ ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 7 | `__ .____` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 6 | `.     ._ v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `____  .. v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 41 | `*...-~.. v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 14 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 12 | `_ . ____` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 10 | `         v` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 6 | `.     .  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `_    *_  v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 9 | `. . __*_ v` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 7 | `-__._.*_ v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | `_  . _*  v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 7 | `.   __*. v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 8 | `._   _*_ v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 8 | `    _..  v` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 5 | `.    _*_ v` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 5 | `_-____*_ v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | `._.- _ _ ^` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 6 | `_   _._. ^` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `__ _-_--` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 6 | `       _ ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 5 | `    _ _* ^` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 6 | `_ _*__.* ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 8 | `__ *_  * ^` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 11 | `  .  ._* ^` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 7 | `  __ __* ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 10 | `  _  *_* ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 9 | `      _* ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 6 | `-     _* ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 7 | `     ._* ^` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 6 | `  -  ._* ^` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 8 | `_-   ._* ^` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 7 | `__   ._* ^` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 9 | `     ..* ^` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 9 | `.    __* ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 13 | `. .  * ~ ^` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 7 | `     .**` | PASS |
| **Total** | **1540** | **16603** | **621.1** | **143** | **1333** | **14182** | **1893** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 204 | 11.9 | 1 | 146 | YES | PASS |
| 02_arithmetic | 214 | 12.2 | 1 | 206 | YES | PASS |
| 03_function | 236 | 12.9 | 2 | 188 | YES | PASS |
| 04_if_else | 221 | 12.5 | 1 | 327 | YES | PASS |
| 05_for_loop | 237 | 13.1 | 1 | 290 | YES | PASS |
| 06_struct | 217 | 12.4 | 1 | 175 | YES | PASS |
| 07_enum_match | 225 | 12.7 | 1 | 226 | YES | PASS |
| 08_list | 243 | 13.7 | 1 | 173 | YES | PASS |
| 09_string_methods | 227 | 13.1 | 1 | 217 | YES | PASS |
| 10_result | 270 | 14.5 | 2 | 223 | YES | PASS |
| 11_closure | 227 | 12.6 | 1 | 203 | YES | PASS |
| 12_while | 223 | 12.5 | 1 | 209 | YES | PASS |
| 13_fib | 234 | 12.7 | 2 | 264 | YES | PASS |
| 14_nested_struct | 217 | 12.4 | 1 | 291 | YES | PASS |
| 15_multifunction | 247 | 13.2 | 3 | 229 | YES | PASS |
| 16_string_escape | 223 | 12.9 | 1 | 211 | YES | PASS |
| 17_option | 295 | 15.1 | 2 | 266 | YES | PASS |
| 18_method_chain | 249 | 14.1 | 1 | 244 | YES | PASS |
| 19_nested_match | 272 | 14.2 | 2 | 330 | YES | PASS |
| 20_recursion | 240 | 13.0 | 2 | 310 | YES | PASS |
| 21_list_ops | 325 | 17.1 | 2 | 325 | YES | PASS |
| 22_string_builder | 292 | 15.6 | 2 | 336 | YES | PASS |
| 23_multi_return | 266 | 14.5 | 2 | 271 | YES | PASS |
| 24_enum_methods | 260 | 14.1 | 2 | 315 | YES | PASS |
| 25_fizzbuzz | 304 | 15.3 | 2 | 297 | YES | PASS |
| 26_generics | 284 | 14.5 | 5 | 271 | YES | PASS |
| 27_impl | 244 | 13.3 | 3 | 245 | YES | PASS |
| 28_traits | 252 | 13.5 | 3 | 268 | YES | PASS |
| 29_generic_impl | 253 | 13.7 | 3 | 267 | YES | PASS |
| 30_nested_generics | 244 | 14.1 | 1 | 257 | YES | PASS |
| 31_generic_multi | 269 | 14.6 | 4 | 218 | YES | PASS |
| 32_generic_enum | 215 | 12.3 | 1 | 171 | YES | PASS |
| 33_break_continue | 428 | 19.1 | 5 | 334 | YES | PASS |
| 34_file_io | 299 | 16.9 | 1 | 262 | YES | PASS |
| 35_stdin | 229 | 13.2 | 1 | 263 | YES | PASS |
| 36_crypto | 258 | 14.6 | 1 | 352 | YES | PASS |
| 37_regex | 269 | 15.3 | 1 | 391 | YES | PASS |
| 38_http | 220 | 12.7 | 1 | 404 | YES | PASS |
| 39_gpu_detect | 247 | 13.9 | 1 | 302 | YES | PASS |
| 40_gpu_tensor | 434 | 22.6 | 1 | 335 | YES | PASS |
| 41_module_let | 218 | 12.2 | 2 | 252 | YES | PASS |
| 42_module_let_string | 221 | 12.4 | 2 | 370 | YES | PASS |
| 43_module_let_math | 225 | 12.6 | 2 | 274 | YES | PASS |
| 45_ffi_bind | 253 | 13.2 | 3 | 363 | YES | PASS |
| 47_try_operator | 352 | 17.8 | 4 | 354 | YES | PASS |
| 48_match_nested_exhaustive | 449 | 22.4 | 3 | 324 | YES | PASS |
| 49_match_guards | 276 | 14.8 | 2 | 268 | YES | PASS |
| 49_tensor_literal | 481 | 24.4 | 1 | 264 | YES | PASS |
| 50_match_or_patterns | 294 | 15.8 | 2 | 283 | YES | PASS |
| 50_tensor_indexing | 453 | 23.2 | 1 | 280 | YES | PASS |
| 51_match_guards_and_or | 345 | 17.5 | 2 | 322 | YES | PASS |
| 51_tensor_broadcast | 465 | 23.3 | 1 | 305 | YES | PASS |
| 52_tensor_slicing | 460 | 23.5 | 1 | 259 | YES | PASS |
| 53_linear_regression | 387 | 19.8 | 1 | 272 | YES | PASS |
| 54_const_basic | 224 | 12.8 | 1 | 196 | YES | PASS |
| 55_async_basic | 266 | 14.3 | 2 | 207 | YES | PASS |
| 56_async_await | 345 | 17.2 | 3 | 191 | YES | PASS |
| 57_real_await | 501 | 23.0 | 5 | 177 | YES | PASS |
| 58_async_file_io | 428 | 20.2 | 4 | 226 | YES | PASS |
| 58_const_scope | 257 | 13.7 | 2 | 186 | YES | PASS |
| 59_async_fanout | 1054 | 44.0 | 12 | 271 | YES | PASS |
| 62_list_output | 385 | 20.8 | 3 | 267 | YES | PASS |
| 63_else_sino | 313 | 15.6 | 3 | 233 | YES | PASS |
| 64_closure_typed | 326 | 15.8 | 3 | 200 | YES | PASS |
| 65_list_int_indexing | 403 | 21.1 | 1 | 197 | YES | PASS |
| 66_qualified_type_ref | 240 | 13.3 | 2 | 192 | YES | PASS |
| 67_implicit_return_one_liner | 267 | 13.9 | 4 | 192 | YES | PASS |
| 68_terse_lambda | 316 | 15.4 | 3 | 199 | YES | PASS |
| 69_list_comp | 368 | 19.5 | 1 | 201 | YES | PASS |
| 70_list_comp_filter | 377 | 19.7 | 1 | 201 | YES | PASS |
| 71_map_comp | 265 | 14.4 | 1 | 318 | YES | PASS |
| 72_string_interp_var | 220 | 12.7 | 1 | 219 | YES | PASS |
| 73_string_interp_int | 220 | 12.7 | 1 | 207 | YES | PASS |
| 74_string_interp_float | 220 | 12.7 | 1 | 148 | YES | PASS |
| 75_string_interp_bool | 221 | 12.7 | 1 | 146 | YES | PASS |
| 76_string_interp_method | 219 | 12.6 | 1 | 233 | YES | PASS |
| 77_string_interp_arith | 219 | 12.6 | 1 | 191 | YES | PASS |
| 78_string_interp_multi | 236 | 13.4 | 1 | 192 | YES | PASS |
| 79_string_interp_mixed | 230 | 13.2 | 1 | 213 | YES | PASS |
| 80_string_interp_escaped | 204 | 12.0 | 1 | 178 | YES | PASS |
| 81_struct_shorthand | 257 | 14.2 | 1 | 233 | YES | PASS |
| 82_struct_update | 253 | 14.1 | 1 | 261 | YES | PASS |
| 83_struct_update_partial | 266 | 14.7 | 1 | 280 | YES | PASS |
| 84_let_destructure | 232 | 13.0 | 1 | 302 | YES | PASS |
| 85_let_destructure_nested | 243 | 13.5 | 1 | 311 | YES | PASS |
| 86_let_destructure_rest | 222 | 12.6 | 1 | 225 | YES | PASS |
| 87_let_destructure_mut | 236 | 13.1 | 1 | 209 | YES | PASS |
| 88_if_let | 230 | 12.8 | 1 | 230 | YES | PASS |
| 89_if_let_else | 230 | 12.9 | 1 | 193 | YES | PASS |
| 90_while_let | 233 | 12.8 | 1 | 255 | YES | PASS |
| 91_let_else | 252 | 13.6 | 2 | 192 | YES | PASS |
| 92_chained_cmp_simple | 278 | 14.6 | 2 | 149 | YES | PASS |
| 93_chained_cmp_4 | 286 | 14.8 | 2 | 208 | YES | PASS |
| 94_chained_cmp_mixed | 333 | 16.4 | 4 | 176 | YES | PASS |
| 95_chained_cmp_side_effect | 301 | 15.8 | 3 | 212 | YES | PASS |
| **Total** | | | | **23615** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1109 | 146 | 7.6x |
| 02_arithmetic | 7 | 206 | 0.0x |
| 03_function | 6 | 188 | 0.0x |
| 04_if_else | 9 | 327 | 0.0x |
| 05_for_loop | 8 | 290 | 0.0x |
| 06_struct | 7 | 175 | 0.0x |
| 07_enum_match | 15 | 226 | 0.1x |
| 08_list | 8 | 173 | 0.0x |
| 09_string_methods | 5 | 217 | 0.0x |
| 10_result | 8 | 223 | 0.0x |
| 11_closure | 6 | 203 | 0.0x |
| 12_while | 7 | 209 | 0.0x |
| 13_fib | 6 | 264 | 0.0x |
| 14_nested_struct | 9 | 291 | 0.0x |
| 15_multifunction | 8 | 229 | 0.0x |
| 16_string_escape | 6 | 211 | 0.0x |
| 17_option | 8 | 266 | 0.0x |
| 18_method_chain | 6 | 244 | 0.0x |
| 19_nested_match | 10 | 330 | 0.0x |
| 20_recursion | 7 | 310 | 0.0x |
| 21_list_ops | 9 | 325 | 0.0x |
| 22_string_builder | 10 | 336 | 0.0x |
| 23_multi_return | 8 | 271 | 0.0x |
| 24_enum_methods | 7 | 315 | 0.0x |
| 25_fizzbuzz | 8 | 297 | 0.0x |
| 26_generics | 9 | 271 | 0.0x |
| 27_impl | 8 | 245 | 0.0x |
| 28_traits | 7 | 268 | 0.0x |
| 29_generic_impl | 7 | 267 | 0.0x |
| 30_nested_generics | 9 | 257 | 0.0x |
| 31_generic_multi | 8 | 218 | 0.0x |
| 32_generic_enum | 5 | 171 | 0.0x |
| 33_break_continue | 11 | 334 | 0.0x |
| 34_file_io | 9 | 262 | 0.0x |
| 35_stdin | 6 | 263 | 0.0x |
| 36_crypto | 7 | 352 | 0.0x |
| 37_regex | 9 | 391 | 0.0x |
| 38_http | 10 | 404 | 0.0x |
| 39_gpu_detect | 7 | 302 | 0.0x |
| 40_gpu_tensor | 8 | 335 | 0.0x |
| 41_module_let | 7 | 252 | 0.0x |
| 42_module_let_string | 9 | 370 | 0.0x |
| 43_module_let_math | 12 | 274 | 0.0x |
| 45_ffi_bind | 8 | 363 | 0.0x |
| 47_try_operator | 12 | 354 | 0.0x |
| 48_match_nested_exhaustive | 11 | 324 | 0.0x |
| 49_match_guards | 7 | 268 | 0.0x |
| 49_tensor_literal | 12 | 264 | 0.0x |
| 50_match_or_patterns | 8 | 283 | 0.0x |
| 50_tensor_indexing | 14 | 280 | 0.1x |
| 51_match_guards_and_or | 8 | 322 | 0.0x |
| 51_tensor_broadcast | 11 | 305 | 0.0x |
| 52_tensor_slicing | 11 | 259 | 0.0x |
| 53_linear_regression | 8 | 272 | 0.0x |
| 54_const_basic | 5 | 196 | 0.0x |
| 55_async_basic | 6 | 207 | 0.0x |
| 56_async_await | 6 | 191 | 0.0x |
| 57_real_await | 7 | 177 | 0.0x |
| 58_async_file_io | 6 | 226 | 0.0x |
| 58_const_scope | 6 | 186 | 0.0x |
| 59_async_fanout | 41 | 271 | 0.1x |
| 62_list_output | 14 | 267 | 0.1x |
| 63_else_sino | 12 | 233 | 0.1x |
| 64_closure_typed | 10 | 200 | 0.0x |
| 65_list_int_indexing | 6 | 197 | 0.0x |
| 66_qualified_type_ref | 6 | 192 | 0.0x |
| 67_implicit_return_one_liner | 6 | 192 | 0.0x |
| 68_terse_lambda | 9 | 199 | 0.0x |
| 69_list_comp | 7 | 201 | 0.0x |
| 70_list_comp_filter | 6 | 201 | 0.0x |
| 71_map_comp | 7 | 318 | 0.0x |
| 72_string_interp_var | 8 | 219 | 0.0x |
| 73_string_interp_int | 8 | 207 | 0.0x |
| 74_string_interp_float | 5 | 148 | 0.0x |
| 75_string_interp_bool | 5 | 146 | 0.0x |
| 76_string_interp_method | 5 | 233 | 0.0x |
| 77_string_interp_arith | 6 | 191 | 0.0x |
| 78_string_interp_multi | 5 | 192 | 0.0x |
| 79_string_interp_mixed | 6 | 213 | 0.0x |
| 80_string_interp_escaped | 5 | 178 | 0.0x |
| 81_struct_shorthand | 6 | 233 | 0.0x |
| 82_struct_update | 8 | 261 | 0.0x |
| 83_struct_update_partial | 11 | 280 | 0.0x |
| 84_let_destructure | 7 | 302 | 0.0x |
| 85_let_destructure_nested | 10 | 311 | 0.0x |
| 86_let_destructure_rest | 9 | 225 | 0.0x |
| 87_let_destructure_mut | 6 | 209 | 0.0x |
| 88_if_let | 7 | 230 | 0.0x |
| 89_if_let_else | 6 | 193 | 0.0x |
| 90_while_let | 8 | 255 | 0.0x |
| 91_let_else | 7 | 192 | 0.0x |
| 92_chained_cmp_simple | 9 | 149 | 0.1x |
| 93_chained_cmp_4 | 9 | 208 | 0.0x |
| 94_chained_cmp_mixed | 13 | 176 | 0.1x |
| 95_chained_cmp_side_effect | 7 | 212 | 0.0x |

