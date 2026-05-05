# Mapanare Benchmarks - Linux

Generated: 2026-05-05 05:18 UTC  
Version: 5.42.0 (`5e6463da`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 16.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1103 | `______-- ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 8 | `  _  ___ ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         v` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 6 | `_     __ ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 6 | `      __ v` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         v` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 6 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 10_result | 10 | 140 | 5.0 | 2 | 10 | 139 | 6 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | `_      _ ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 4 | `_      _ ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `_  _._-. v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 9 | `      __` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         v` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 5 | `_   ____` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 6 | `       _ ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 6 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         ^` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 6 | `       _ ^` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 8 | `      __ ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `    _   ` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `    _ _. ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 8 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 5 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 5 | `         v` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 6 | `      ._ v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 5 | `______..` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_    ...` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `      __ ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 7 | `         v` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | `_ _  _.- ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `_ _ _ .. v` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 6 | `      __ v` | PASS |
| 47_try_operator | 25 | 293 | 11.2 | 4 | 23 | 279 | 10 | `         ^` | PASS |
| 48_match_nested_exhaustive | 18 | 331 | 13.4 | 3 | 32 | 293 | 9 | `         ^` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 11 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `      __ ^` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `      __ v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         ^` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 8 | `_     __ v` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `      _  v` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `      __` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `        ` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | `      ..` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `      .. ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 6 | `. -  _   ^` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 6 | `      __ ^` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 6 | `  _ __*~ v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 32 | ` _ __ .- ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 9 | `         ^` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 6 | `      __ ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         v` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `        ` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `  __  .- ^` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 7 | `_     _  v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 10 | `- *_  ..` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 5 | `_ _   .. v` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | ` __   *- v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | `     _..` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | ` __ _ *- v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 7 | `      .- ^` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` .   _.* ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | `_.    -~ ^` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 4 | `.  .  -. v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `.__   -. v` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 4 | `  _ . ._ v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 5 | `.     -. v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `      *_ v` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 6 | ` __-_.~- v` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 5 | `     _~_ v` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 7 | `     _..` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `     _.* ^` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `      __ ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `_.-   ~. v` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `  _   __ ^` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 6 | `      *. v` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 6 | `_     -* ^` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 4 | `    . ~~` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `      -~ ^` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 7 | `   _  -- ^` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | `      .~ ^` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 9 | `      .. v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `     .--` | PASS |
| 96_tensor_reshape | 86 | 1358 | 58.6 | 1 | 90 | 1704 | 12 | ` * ^` | PASS |
| **Total** | **1626** | **17927** | **678.3** | **144** | **1423** | **15806** | **1704** | | **96/96** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 207 | 12.2 | 1 | 215 | YES | PASS |
| 02_arithmetic | 217 | 12.4 | 1 | 157 | YES | PASS |
| 03_function | 239 | 13.1 | 2 | 136 | YES | PASS |
| 04_if_else | 224 | 12.7 | 1 | 147 | YES | PASS |
| 05_for_loop | 240 | 13.3 | 1 | 166 | YES | PASS |
| 06_struct | 220 | 12.6 | 1 | 144 | YES | PASS |
| 07_enum_match | 228 | 12.9 | 1 | 154 | YES | PASS |
| 08_list | 246 | 14.0 | 1 | 153 | YES | PASS |
| 09_string_methods | 230 | 13.3 | 1 | 136 | YES | PASS |
| 10_result | 273 | 14.7 | 2 | 155 | YES | PASS |
| 11_closure | 230 | 12.8 | 1 | 137 | YES | PASS |
| 12_while | 226 | 12.7 | 1 | 128 | YES | PASS |
| 13_fib | 237 | 12.9 | 2 | 148 | YES | PASS |
| 14_nested_struct | 220 | 12.6 | 1 | 195 | YES | PASS |
| 15_multifunction | 250 | 13.4 | 3 | 123 | YES | PASS |
| 16_string_escape | 226 | 13.1 | 1 | 98 | YES | PASS |
| 17_option | 309 | 15.7 | 2 | 133 | YES | PASS |
| 18_method_chain | 252 | 14.3 | 1 | 152 | YES | PASS |
| 19_nested_match | 275 | 14.4 | 2 | 249 | YES | PASS |
| 20_recursion | 243 | 13.2 | 2 | 145 | YES | PASS |
| 21_list_ops | 328 | 17.3 | 2 | 167 | YES | PASS |
| 22_string_builder | 295 | 15.8 | 2 | 143 | YES | PASS |
| 23_multi_return | 269 | 14.7 | 2 | 129 | YES | PASS |
| 24_enum_methods | 263 | 14.3 | 2 | 148 | YES | PASS |
| 25_fizzbuzz | 307 | 15.6 | 2 | 156 | YES | PASS |
| 26_generics | 287 | 14.7 | 5 | 138 | YES | PASS |
| 27_impl | 247 | 13.5 | 3 | 145 | YES | PASS |
| 28_traits | 255 | 13.7 | 3 | 190 | YES | PASS |
| 29_generic_impl | 256 | 13.9 | 3 | 187 | YES | PASS |
| 30_nested_generics | 247 | 14.3 | 1 | 124 | YES | PASS |
| 31_generic_multi | 272 | 14.8 | 4 | 149 | YES | PASS |
| 32_generic_enum | 218 | 12.5 | 1 | 105 | YES | PASS |
| 33_break_continue | 431 | 19.3 | 5 | 153 | YES | PASS |
| 34_file_io | 302 | 17.1 | 1 | 119 | YES | PASS |
| 35_stdin | 232 | 13.4 | 1 | 201 | YES | PASS |
| 36_crypto | 261 | 14.8 | 1 | 161 | YES | PASS |
| 37_regex | 272 | 15.5 | 1 | 119 | YES | PASS |
| 38_http | 223 | 12.9 | 1 | 122 | YES | PASS |
| 39_gpu_detect | 250 | 14.1 | 1 | 131 | YES | PASS |
| 40_gpu_tensor | 437 | 22.9 | 1 | 149 | YES | PASS |
| 41_module_let | 221 | 12.5 | 2 | 130 | YES | PASS |
| 42_module_let_string | 224 | 12.7 | 2 | 119 | YES | PASS |
| 43_module_let_math | 228 | 12.8 | 2 | 121 | YES | PASS |
| 45_ffi_bind | 256 | 13.4 | 3 | 239 | YES | PASS |
| 47_try_operator | 355 | 18.0 | 4 | 184 | YES | PASS |
| 48_match_nested_exhaustive | 452 | 22.6 | 3 | 172 | YES | PASS |
| 49_match_guards | 313 | 16.0 | 2 | 161 | YES | PASS |
| 49_tensor_literal | 484 | 24.7 | 1 | 140 | YES | PASS |
| 50_match_or_patterns | 297 | 16.0 | 2 | 163 | YES | PASS |
| 50_tensor_indexing | 456 | 23.4 | 1 | 156 | YES | PASS |
| 51_match_guards_and_or | 379 | 18.8 | 2 | 149 | YES | PASS |
| 51_tensor_broadcast | 468 | 23.6 | 1 | 122 | YES | PASS |
| 52_tensor_slicing | 463 | 23.8 | 1 | 128 | YES | PASS |
| 53_linear_regression | 390 | 20.0 | 1 | 137 | YES | PASS |
| 54_const_basic | 227 | 13.0 | 1 | 111 | YES | PASS |
| 55_async_basic | 269 | 14.5 | 2 | 120 | YES | PASS |
| 56_async_await | 348 | 17.4 | 3 | 132 | YES | PASS |
| 57_real_await | 504 | 23.2 | 5 | 128 | YES | PASS |
| 58_async_file_io | 431 | 20.4 | 4 | 228 | YES | PASS |
| 58_const_scope | 260 | 13.9 | 2 | 150 | YES | PASS |
| 59_async_fanout | 1057 | 44.2 | 12 | 142 | YES | PASS |
| 62_list_output | 388 | 21.0 | 3 | 153 | YES | PASS |
| 63_else_sino | 316 | 15.9 | 3 | 148 | YES | PASS |
| 64_closure_typed | 329 | 16.1 | 3 | 137 | YES | PASS |
| 65_list_int_indexing | 406 | 21.3 | 1 | 144 | YES | PASS |
| 66_qualified_type_ref | 243 | 13.5 | 2 | 185 | YES | PASS |
| 67_implicit_return_one_liner | 270 | 14.1 | 4 | 194 | YES | PASS |
| 68_terse_lambda | 319 | 15.6 | 3 | 153 | YES | PASS |
| 69_list_comp | 371 | 19.7 | 1 | 153 | YES | PASS |
| 70_list_comp_filter | 380 | 19.9 | 1 | 160 | YES | PASS |
| 71_map_comp | 268 | 14.6 | 1 | 160 | YES | PASS |
| 72_string_interp_var | 223 | 12.9 | 1 | 159 | YES | PASS |
| 73_string_interp_int | 223 | 12.9 | 1 | 158 | YES | PASS |
| 74_string_interp_float | 223 | 12.9 | 1 | 112 | YES | PASS |
| 75_string_interp_bool | 224 | 12.9 | 1 | 107 | YES | PASS |
| 76_string_interp_method | 222 | 12.8 | 1 | 120 | YES | PASS |
| 77_string_interp_arith | 222 | 12.8 | 1 | 97 | YES | PASS |
| 78_string_interp_multi | 239 | 13.6 | 1 | 107 | YES | PASS |
| 79_string_interp_mixed | 233 | 13.4 | 1 | 100 | YES | PASS |
| 80_string_interp_escaped | 207 | 12.2 | 1 | 105 | YES | PASS |
| 81_struct_shorthand | 260 | 14.4 | 1 | 136 | YES | PASS |
| 82_struct_update | 256 | 14.3 | 1 | 164 | YES | PASS |
| 83_struct_update_partial | 269 | 14.9 | 1 | 147 | YES | PASS |
| 84_let_destructure | 235 | 13.2 | 1 | 135 | YES | PASS |
| 85_let_destructure_nested | 246 | 13.8 | 1 | 137 | YES | PASS |
| 86_let_destructure_rest | 225 | 12.8 | 1 | 137 | YES | PASS |
| 87_let_destructure_mut | 239 | 13.4 | 1 | 207 | YES | PASS |
| 88_if_let | 238 | 13.2 | 1 | 210 | YES | PASS |
| 89_if_let_else | 233 | 13.1 | 1 | 189 | YES | PASS |
| 90_while_let | 241 | 13.2 | 1 | 150 | YES | PASS |
| 91_let_else | 265 | 14.2 | 2 | 154 | YES | PASS |
| 92_chained_cmp_simple | 281 | 14.8 | 2 | 134 | YES | PASS |
| 93_chained_cmp_4 | 289 | 15.0 | 2 | 137 | YES | PASS |
| 94_chained_cmp_mixed | 336 | 16.6 | 4 | 121 | YES | PASS |
| 95_chained_cmp_side_effect | 304 | 16.0 | 3 | 126 | YES | PASS |
| 96_tensor_reshape | 796 | 39.2 | 1 | 131 | YES | PASS |
| **Total** | | | | **14205** | **96/96** | **96/96** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1103 | 215 | 5.1x |
| 02_arithmetic | 8 | 157 | 0.1x |
| 03_function | 6 | 136 | 0.0x |
| 04_if_else | 6 | 147 | 0.0x |
| 05_for_loop | 6 | 166 | 0.0x |
| 06_struct | 5 | 144 | 0.0x |
| 07_enum_match | 12 | 154 | 0.1x |
| 08_list | 6 | 153 | 0.0x |
| 09_string_methods | 4 | 136 | 0.0x |
| 10_result | 6 | 155 | 0.0x |
| 11_closure | 5 | 137 | 0.0x |
| 12_while | 4 | 128 | 0.0x |
| 13_fib | 5 | 148 | 0.0x |
| 14_nested_struct | 5 | 195 | 0.0x |
| 15_multifunction | 6 | 123 | 0.0x |
| 16_string_escape | 4 | 98 | 0.0x |
| 17_option | 6 | 133 | 0.0x |
| 18_method_chain | 5 | 152 | 0.0x |
| 19_nested_match | 9 | 249 | 0.0x |
| 20_recursion | 5 | 145 | 0.0x |
| 21_list_ops | 6 | 167 | 0.0x |
| 22_string_builder | 5 | 143 | 0.0x |
| 23_multi_return | 6 | 129 | 0.0x |
| 24_enum_methods | 5 | 148 | 0.0x |
| 25_fizzbuzz | 5 | 156 | 0.0x |
| 26_generics | 6 | 138 | 0.0x |
| 27_impl | 7 | 145 | 0.0x |
| 28_traits | 6 | 190 | 0.0x |
| 29_generic_impl | 8 | 187 | 0.0x |
| 30_nested_generics | 5 | 124 | 0.0x |
| 31_generic_multi | 7 | 149 | 0.0x |
| 32_generic_enum | 5 | 105 | 0.0x |
| 33_break_continue | 8 | 153 | 0.1x |
| 34_file_io | 5 | 119 | 0.0x |
| 35_stdin | 5 | 201 | 0.0x |
| 36_crypto | 6 | 161 | 0.0x |
| 37_regex | 5 | 119 | 0.0x |
| 38_http | 4 | 122 | 0.0x |
| 39_gpu_detect | 5 | 131 | 0.0x |
| 40_gpu_tensor | 7 | 149 | 0.0x |
| 41_module_let | 7 | 130 | 0.1x |
| 42_module_let_string | 5 | 119 | 0.0x |
| 43_module_let_math | 5 | 121 | 0.0x |
| 45_ffi_bind | 6 | 239 | 0.0x |
| 47_try_operator | 10 | 184 | 0.1x |
| 48_match_nested_exhaustive | 9 | 172 | 0.1x |
| 49_match_guards | 6 | 161 | 0.0x |
| 49_tensor_literal | 11 | 140 | 0.1x |
| 50_match_or_patterns | 6 | 163 | 0.0x |
| 50_tensor_indexing | 8 | 156 | 0.1x |
| 51_match_guards_and_or | 7 | 149 | 0.0x |
| 51_tensor_broadcast | 8 | 122 | 0.1x |
| 52_tensor_slicing | 8 | 128 | 0.1x |
| 53_linear_regression | 6 | 137 | 0.0x |
| 54_const_basic | 5 | 111 | 0.0x |
| 55_async_basic | 4 | 120 | 0.0x |
| 56_async_await | 5 | 132 | 0.0x |
| 57_real_await | 6 | 128 | 0.0x |
| 58_async_file_io | 6 | 228 | 0.0x |
| 58_const_scope | 6 | 150 | 0.0x |
| 59_async_fanout | 32 | 142 | 0.2x |
| 62_list_output | 9 | 153 | 0.1x |
| 63_else_sino | 6 | 148 | 0.0x |
| 64_closure_typed | 8 | 137 | 0.1x |
| 65_list_int_indexing | 6 | 144 | 0.0x |
| 66_qualified_type_ref | 5 | 185 | 0.0x |
| 67_implicit_return_one_liner | 7 | 194 | 0.0x |
| 68_terse_lambda | 10 | 153 | 0.1x |
| 69_list_comp | 5 | 153 | 0.0x |
| 70_list_comp_filter | 6 | 160 | 0.0x |
| 71_map_comp | 6 | 160 | 0.0x |
| 72_string_interp_var | 4 | 159 | 0.0x |
| 73_string_interp_int | 7 | 158 | 0.0x |
| 74_string_interp_float | 4 | 112 | 0.0x |
| 75_string_interp_bool | 4 | 107 | 0.0x |
| 76_string_interp_method | 4 | 120 | 0.0x |
| 77_string_interp_arith | 4 | 97 | 0.0x |
| 78_string_interp_multi | 4 | 107 | 0.0x |
| 79_string_interp_mixed | 5 | 100 | 0.0x |
| 80_string_interp_escaped | 4 | 105 | 0.0x |
| 81_struct_shorthand | 6 | 136 | 0.0x |
| 82_struct_update | 5 | 164 | 0.0x |
| 83_struct_update_partial | 7 | 147 | 0.0x |
| 84_let_destructure | 5 | 135 | 0.0x |
| 85_let_destructure_nested | 5 | 137 | 0.0x |
| 86_let_destructure_rest | 5 | 137 | 0.0x |
| 87_let_destructure_mut | 5 | 207 | 0.0x |
| 88_if_let | 6 | 210 | 0.0x |
| 89_if_let_else | 6 | 189 | 0.0x |
| 90_while_let | 4 | 150 | 0.0x |
| 91_let_else | 5 | 154 | 0.0x |
| 92_chained_cmp_simple | 7 | 134 | 0.1x |
| 93_chained_cmp_4 | 6 | 137 | 0.0x |
| 94_chained_cmp_mixed | 9 | 121 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 126 | 0.0x |
| 96_tensor_reshape | 12 | 131 | 0.1x |

