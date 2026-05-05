# Mapanare Benchmarks - Linux

Generated: 2026-05-05 03:41 UTC  
Version: 5.41.0 (`c6fb4637`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 29.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1662 | `_______- ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 13 | `   _  __ ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 10 | ` _     _ ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 9 | `       _ ^` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 9 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 19 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 11 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 9 | `        ` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 10 | `         ^` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 9 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 9 | `        ` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 8 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 8 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 12 | ` _       ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 7 | ` _       ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 10 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 7 | `._  _._- ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 11 | `       _ ^` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 12 | `         ^` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 10 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 8 | ` _   ___ ^` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 13 | `         ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 9 | `         ^` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 8 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 10 | `         ^` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 13 | `         ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 10 | `         ^` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 13 | `       _ ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 7 | `_    _   ^` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 11 | `         ^` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 14 | `     _ _ ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 14 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 7 | `         ^` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 7 | `         ^` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 7 | `       . ^` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 7 | `_______. ^` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 7 | `__    .. ^` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 8 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 12 | `_      _ ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 8 | `         ^` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 8 | `__ _  _. ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 9 | ` _ _ _ . ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 8 | `       _ ^` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 21 | `         ^` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 15 | `         ^` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 8 | `         ^` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 15 | `         ^` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 12 | `       _ ^` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 13 | `       _ ^` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 11 | `         ^` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 12 | ` _     _ ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 10 | `       _ ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 10 | `       _ ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 7 | `         ^` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 8 | `       . ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 10 | `       . ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 9 | ` . -  _  v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 9 | `       _ ^` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 10 | `.  _ __* ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 76 | `_ _ __ . ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 12 | `         ^` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 11 | `       _ ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 11 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 9 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 10 | `.  __  . ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 7 | ` _     _ ^` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 12 | `_- *_  . ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 8 | ` _ _   . ^` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 9 | `  __   * ^` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 9 | `      _. ^` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 7 | `_ __ _ * ^` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 8 | `       . ^` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 10 | `  -   .- ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 8 | `__.    - ^` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 9 | ` .  .  - ^` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 6 | ` .__   - ^` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 6 | `   _ . . ^` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 7 | `..     - ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 6 | `       * ^` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 8 | `. __-_.~ ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 7 | `      _~ ^` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 9 | `      _. ^` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 11 | `      _. ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 11 | `       _ ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 8 | `__.-   ~ ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 9 | `   _   _ ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 7 | `_      * ^` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 10 | `_._____~ ^` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 9 | `     . ~ ^` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 9 | `       - ^` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 12 | `_   _  - ^` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 13 | `.      . ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 12 | `       . ^` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 10 | `      .- ^` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.6 | 1 | 90 | 1704 | 22 | ` ` | PASS |
| **Total** | **1626** | **17927** | **678.3** | **144** | **1423** | **15806** | **2666** | | **96/96** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 207 | 12.2 | 1 | 346 | YES | PASS |
| 02_arithmetic | 217 | 12.4 | 1 | 307 | YES | PASS |
| 03_function | 239 | 13.1 | 2 | 244 | YES | PASS |
| 04_if_else | 224 | 12.7 | 1 | 269 | YES | PASS |
| 05_for_loop | 240 | 13.3 | 1 | 266 | YES | PASS |
| 06_struct | 220 | 12.6 | 1 | 317 | YES | PASS |
| 07_enum_match | 228 | 12.9 | 1 | 308 | YES | PASS |
| 08_list | 246 | 14.0 | 1 | 276 | YES | PASS |
| 09_string_methods | 230 | 13.3 | 1 | 277 | YES | PASS |
| 10_result | 273 | 14.7 | 2 | 271 | YES | PASS |
| 11_closure | 230 | 12.8 | 1 | 255 | YES | PASS |
| 12_while | 226 | 12.7 | 1 | 233 | YES | PASS |
| 13_fib | 237 | 12.9 | 2 | 255 | YES | PASS |
| 14_nested_struct | 220 | 12.6 | 1 | 307 | YES | PASS |
| 15_multifunction | 250 | 13.4 | 3 | 237 | YES | PASS |
| 16_string_escape | 226 | 13.1 | 1 | 195 | YES | PASS |
| 17_option | 309 | 15.7 | 2 | 272 | YES | PASS |
| 18_method_chain | 252 | 14.3 | 1 | 243 | YES | PASS |
| 19_nested_match | 275 | 14.4 | 2 | 354 | YES | PASS |
| 20_recursion | 243 | 13.2 | 2 | 279 | YES | PASS |
| 21_list_ops | 328 | 17.3 | 2 | 288 | YES | PASS |
| 22_string_builder | 295 | 15.8 | 2 | 256 | YES | PASS |
| 23_multi_return | 269 | 14.7 | 2 | 326 | YES | PASS |
| 24_enum_methods | 263 | 14.3 | 2 | 250 | YES | PASS |
| 25_fizzbuzz | 307 | 15.6 | 2 | 259 | YES | PASS |
| 26_generics | 287 | 14.7 | 5 | 263 | YES | PASS |
| 27_impl | 247 | 13.5 | 3 | 291 | YES | PASS |
| 28_traits | 255 | 13.7 | 3 | 319 | YES | PASS |
| 29_generic_impl | 256 | 13.9 | 3 | 301 | YES | PASS |
| 30_nested_generics | 247 | 14.3 | 1 | 230 | YES | PASS |
| 31_generic_multi | 272 | 14.8 | 4 | 306 | YES | PASS |
| 32_generic_enum | 218 | 12.5 | 1 | 213 | YES | PASS |
| 33_break_continue | 431 | 19.3 | 5 | 321 | YES | PASS |
| 34_file_io | 302 | 17.1 | 1 | 196 | YES | PASS |
| 35_stdin | 232 | 13.4 | 1 | 235 | YES | PASS |
| 36_crypto | 261 | 14.8 | 1 | 232 | YES | PASS |
| 37_regex | 272 | 15.5 | 1 | 257 | YES | PASS |
| 38_http | 223 | 12.9 | 1 | 245 | YES | PASS |
| 39_gpu_detect | 250 | 14.1 | 1 | 238 | YES | PASS |
| 40_gpu_tensor | 437 | 22.9 | 1 | 323 | YES | PASS |
| 41_module_let | 221 | 12.5 | 2 | 221 | YES | PASS |
| 42_module_let_string | 224 | 12.7 | 2 | 198 | YES | PASS |
| 43_module_let_math | 228 | 12.8 | 2 | 204 | YES | PASS |
| 45_ffi_bind | 256 | 13.4 | 3 | 396 | YES | PASS |
| 47_try_operator | 355 | 18.0 | 4 | 424 | YES | PASS |
| 48_match_nested_exhaustive | 452 | 22.6 | 3 | 334 | YES | PASS |
| 49_match_guards | 313 | 16.0 | 2 | 243 | YES | PASS |
| 49_tensor_literal | 484 | 24.7 | 1 | 343 | YES | PASS |
| 50_match_or_patterns | 297 | 16.0 | 2 | 255 | YES | PASS |
| 50_tensor_indexing | 456 | 23.4 | 1 | 258 | YES | PASS |
| 51_match_guards_and_or | 379 | 18.8 | 2 | 265 | YES | PASS |
| 51_tensor_broadcast | 468 | 23.6 | 1 | 247 | YES | PASS |
| 52_tensor_slicing | 463 | 23.8 | 1 | 223 | YES | PASS |
| 53_linear_regression | 390 | 20.0 | 1 | 281 | YES | PASS |
| 54_const_basic | 227 | 13.0 | 1 | 193 | YES | PASS |
| 55_async_basic | 269 | 14.5 | 2 | 269 | YES | PASS |
| 56_async_await | 348 | 17.4 | 3 | 513 | YES | PASS |
| 57_real_await | 504 | 23.2 | 5 | 234 | YES | PASS |
| 58_async_file_io | 431 | 20.4 | 4 | 282 | YES | PASS |
| 58_const_scope | 260 | 13.9 | 2 | 270 | YES | PASS |
| 59_async_fanout | 1057 | 44.2 | 12 | 237 | YES | PASS |
| 62_list_output | 388 | 21.0 | 3 | 274 | YES | PASS |
| 63_else_sino | 316 | 15.9 | 3 | 264 | YES | PASS |
| 64_closure_typed | 329 | 16.1 | 3 | 270 | YES | PASS |
| 65_list_int_indexing | 406 | 21.3 | 1 | 346 | YES | PASS |
| 66_qualified_type_ref | 243 | 13.5 | 2 | 308 | YES | PASS |
| 67_implicit_return_one_liner | 270 | 14.1 | 4 | 231 | YES | PASS |
| 68_terse_lambda | 319 | 15.6 | 3 | 250 | YES | PASS |
| 69_list_comp | 371 | 19.7 | 1 | 276 | YES | PASS |
| 70_list_comp_filter | 380 | 19.9 | 1 | 321 | YES | PASS |
| 71_map_comp | 268 | 14.6 | 1 | 257 | YES | PASS |
| 72_string_interp_var | 223 | 12.9 | 1 | 218 | YES | PASS |
| 73_string_interp_int | 223 | 12.9 | 1 | 211 | YES | PASS |
| 74_string_interp_float | 223 | 12.9 | 1 | 269 | YES | PASS |
| 75_string_interp_bool | 224 | 12.9 | 1 | 195 | YES | PASS |
| 76_string_interp_method | 222 | 12.8 | 1 | 246 | YES | PASS |
| 77_string_interp_arith | 222 | 12.8 | 1 | 202 | YES | PASS |
| 78_string_interp_multi | 239 | 13.6 | 1 | 213 | YES | PASS |
| 79_string_interp_mixed | 233 | 13.4 | 1 | 216 | YES | PASS |
| 80_string_interp_escaped | 207 | 12.2 | 1 | 189 | YES | PASS |
| 81_struct_shorthand | 260 | 14.4 | 1 | 229 | YES | PASS |
| 82_struct_update | 256 | 14.3 | 1 | 240 | YES | PASS |
| 83_struct_update_partial | 269 | 14.9 | 1 | 465 | YES | PASS |
| 84_let_destructure | 235 | 13.2 | 1 | 273 | YES | PASS |
| 85_let_destructure_nested | 246 | 13.8 | 1 | 227 | YES | PASS |
| 86_let_destructure_rest | 225 | 12.8 | 1 | 242 | YES | PASS |
| 87_let_destructure_mut | 239 | 13.4 | 1 | 241 | YES | PASS |
| 88_if_let | 238 | 13.2 | 1 | 258 | YES | PASS |
| 89_if_let_else | 233 | 13.1 | 1 | 259 | YES | PASS |
| 90_while_let | 241 | 13.2 | 1 | 247 | YES | PASS |
| 91_let_else | 265 | 14.2 | 2 | 229 | YES | PASS |
| 92_chained_cmp_simple | 281 | 14.8 | 2 | 211 | YES | PASS |
| 93_chained_cmp_4 | 289 | 15.0 | 2 | 292 | YES | PASS |
| 94_chained_cmp_mixed | 336 | 16.6 | 4 | 223 | YES | PASS |
| 95_chained_cmp_side_effect | 304 | 16.0 | 3 | 285 | YES | PASS |
| 96_tensor_reshape | 796 | 39.2 | 1 | 268 | YES | PASS |
| **Total** | | | | **25694** | **96/96** | **96/96** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1662 | 346 | 4.8x |
| 02_arithmetic | 13 | 307 | 0.0x |
| 03_function | 8 | 244 | 0.0x |
| 04_if_else | 10 | 269 | 0.0x |
| 05_for_loop | 9 | 266 | 0.0x |
| 06_struct | 9 | 317 | 0.0x |
| 07_enum_match | 19 | 308 | 0.1x |
| 08_list | 11 | 276 | 0.0x |
| 09_string_methods | 9 | 277 | 0.0x |
| 10_result | 10 | 271 | 0.0x |
| 11_closure | 9 | 255 | 0.0x |
| 12_while | 9 | 233 | 0.0x |
| 13_fib | 8 | 255 | 0.0x |
| 14_nested_struct | 8 | 307 | 0.0x |
| 15_multifunction | 12 | 237 | 0.1x |
| 16_string_escape | 7 | 195 | 0.0x |
| 17_option | 10 | 272 | 0.0x |
| 18_method_chain | 7 | 243 | 0.0x |
| 19_nested_match | 11 | 354 | 0.0x |
| 20_recursion | 12 | 279 | 0.0x |
| 21_list_ops | 10 | 288 | 0.0x |
| 22_string_builder | 8 | 256 | 0.0x |
| 23_multi_return | 13 | 326 | 0.0x |
| 24_enum_methods | 9 | 250 | 0.0x |
| 25_fizzbuzz | 8 | 259 | 0.0x |
| 26_generics | 10 | 263 | 0.0x |
| 27_impl | 13 | 291 | 0.0x |
| 28_traits | 10 | 319 | 0.0x |
| 29_generic_impl | 13 | 301 | 0.0x |
| 30_nested_generics | 7 | 230 | 0.0x |
| 31_generic_multi | 11 | 306 | 0.0x |
| 32_generic_enum | 14 | 213 | 0.1x |
| 33_break_continue | 14 | 321 | 0.0x |
| 34_file_io | 7 | 196 | 0.0x |
| 35_stdin | 7 | 235 | 0.0x |
| 36_crypto | 7 | 232 | 0.0x |
| 37_regex | 7 | 257 | 0.0x |
| 38_http | 7 | 245 | 0.0x |
| 39_gpu_detect | 8 | 238 | 0.0x |
| 40_gpu_tensor | 12 | 323 | 0.0x |
| 41_module_let | 8 | 221 | 0.0x |
| 42_module_let_string | 8 | 198 | 0.0x |
| 43_module_let_math | 9 | 204 | 0.0x |
| 45_ffi_bind | 8 | 396 | 0.0x |
| 47_try_operator | 21 | 424 | 0.0x |
| 48_match_nested_exhaustive | 15 | 334 | 0.0x |
| 49_match_guards | 8 | 243 | 0.0x |
| 49_tensor_literal | 15 | 343 | 0.0x |
| 50_match_or_patterns | 12 | 255 | 0.0x |
| 50_tensor_indexing | 13 | 258 | 0.1x |
| 51_match_guards_and_or | 11 | 265 | 0.0x |
| 51_tensor_broadcast | 12 | 247 | 0.1x |
| 52_tensor_slicing | 10 | 223 | 0.0x |
| 53_linear_regression | 10 | 281 | 0.0x |
| 54_const_basic | 7 | 193 | 0.0x |
| 55_async_basic | 8 | 269 | 0.0x |
| 56_async_await | 10 | 513 | 0.0x |
| 57_real_await | 9 | 234 | 0.0x |
| 58_async_file_io | 9 | 282 | 0.0x |
| 58_const_scope | 10 | 270 | 0.0x |
| 59_async_fanout | 76 | 237 | 0.3x |
| 62_list_output | 12 | 274 | 0.0x |
| 63_else_sino | 11 | 264 | 0.0x |
| 64_closure_typed | 11 | 270 | 0.0x |
| 65_list_int_indexing | 9 | 346 | 0.0x |
| 66_qualified_type_ref | 10 | 308 | 0.0x |
| 67_implicit_return_one_liner | 7 | 231 | 0.0x |
| 68_terse_lambda | 12 | 250 | 0.0x |
| 69_list_comp | 8 | 276 | 0.0x |
| 70_list_comp_filter | 9 | 321 | 0.0x |
| 71_map_comp | 9 | 257 | 0.0x |
| 72_string_interp_var | 7 | 218 | 0.0x |
| 73_string_interp_int | 8 | 211 | 0.0x |
| 74_string_interp_float | 10 | 269 | 0.0x |
| 75_string_interp_bool | 8 | 195 | 0.0x |
| 76_string_interp_method | 9 | 246 | 0.0x |
| 77_string_interp_arith | 6 | 202 | 0.0x |
| 78_string_interp_multi | 6 | 213 | 0.0x |
| 79_string_interp_mixed | 7 | 216 | 0.0x |
| 80_string_interp_escaped | 6 | 189 | 0.0x |
| 81_struct_shorthand | 8 | 229 | 0.0x |
| 82_struct_update | 7 | 240 | 0.0x |
| 83_struct_update_partial | 9 | 465 | 0.0x |
| 84_let_destructure | 11 | 273 | 0.0x |
| 85_let_destructure_nested | 11 | 227 | 0.0x |
| 86_let_destructure_rest | 8 | 242 | 0.0x |
| 87_let_destructure_mut | 9 | 241 | 0.0x |
| 88_if_let | 7 | 258 | 0.0x |
| 89_if_let_else | 10 | 259 | 0.0x |
| 90_while_let | 9 | 247 | 0.0x |
| 91_let_else | 9 | 229 | 0.0x |
| 92_chained_cmp_simple | 12 | 211 | 0.1x |
| 93_chained_cmp_4 | 13 | 292 | 0.0x |
| 94_chained_cmp_mixed | 12 | 223 | 0.1x |
| 95_chained_cmp_side_effect | 10 | 285 | 0.0x |
| 96_tensor_reshape | 22 | 268 | 0.1x |

