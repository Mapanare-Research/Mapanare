# Mapanare Benchmarks - Linux

Generated: 2026-05-01 03:25 UTC  
Version: 5.18.0 (`4ea40e1`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 15.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1017 | `__._._._ v` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 9 | `    _    ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         ^` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         ^` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 5 | `        ` | PASS |
| 10_result | 10 | 147 | 5.3 | 2 | 10 | 155 | 7 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 4 | `        ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 4 | `     _   v` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 6 | `___.~._. ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 7 | `         ^` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `        ` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `______.  v` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 7 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         v` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 8 | `         v` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 6 | `        ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 6 | `         v` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 6 | `     _   v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 5 | `         v` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `        ` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 5 | `         ^` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 5 | `         v` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 5 | `   __    ^` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `________ ^` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 5 | `.   __  ` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         v` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `    _    ^` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | `   .*_ . ^` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `  ___  _ ^` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 5 | `    _    ^` | PASS |
| 47_try_operator | 25 | 306 | 11.7 | 4 | 23 | 311 | 8 | `         ^` | PASS |
| 48_match_nested_exhaustive | 18 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         ^` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 11 | `         ^` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `        ` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `        ` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 8 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 8 | `_.__._..` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 23 | `.__..__- ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 7 | `    _    ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 4 | `......~. v` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | `   __  _ ^` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `   ___ _ ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `__ __ __ v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 5 | `  . ..  ` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | `_  .__ . ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 8 | `____-___ ^` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `        ` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 6 | ` __ _ __ ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         v` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 9 | `         ^` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | `--..~.--` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | ` __ . *_ v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 9 | `_ _ *_-_ v` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `___._ _. ^` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 7 | `____-*__` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 6 | `    * .  v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 4 | `_ -- *_- ^` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `     *_  v` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` _  ___  v` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | ` ._ _*__` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | ` __ _._  v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | `  _ _.  ` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | ` .. .* . ^` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `_  _ *   ^` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `     *  ` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 5 | `` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 5 | `` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 6 | `` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 5 | `` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | `` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 5 | `` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | `` | PASS |
| **Total** | **1459** | **15886** | **596.5** | **137** | **1259** | **13715** | **1567** | | **91/91** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 204 | 11.9 | 1 | 295 | YES | PASS |
| 02_arithmetic | 214 | 12.2 | 1 | 169 | YES | PASS |
| 03_function | 236 | 12.9 | 2 | 182 | YES | PASS |
| 04_if_else | 221 | 12.5 | 1 | 151 | YES | PASS |
| 05_for_loop | 237 | 13.1 | 1 | 181 | YES | PASS |
| 06_struct | 217 | 12.4 | 1 | 155 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 135 | YES | PASS |
| 08_list | 243 | 13.7 | 1 | 158 | YES | PASS |
| 09_string_methods | 227 | 13.1 | 1 | 219 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 153 | YES | PASS |
| 11_closure | 227 | 12.6 | 1 | 147 | YES | PASS |
| 12_while | 223 | 12.5 | 1 | 171 | YES | PASS |
| 13_fib | 234 | 12.7 | 2 | 161 | YES | PASS |
| 14_nested_struct | 217 | 12.4 | 1 | 148 | YES | PASS |
| 15_multifunction | 247 | 13.2 | 3 | 144 | YES | PASS |
| 16_string_escape | 223 | 12.9 | 1 | 112 | YES | PASS |
| 17_option | 299 | 15.3 | 2 | 179 | YES | PASS |
| 18_method_chain | 249 | 14.1 | 1 | 160 | YES | PASS |
| 19_nested_match | 272 | 14.2 | 2 | 168 | YES | PASS |
| 20_recursion | 240 | 13.0 | 2 | 146 | YES | PASS |
| 21_list_ops | 325 | 17.1 | 2 | 186 | YES | PASS |
| 22_string_builder | 292 | 15.6 | 2 | 180 | YES | PASS |
| 23_multi_return | 266 | 14.5 | 2 | 202 | YES | PASS |
| 24_enum_methods | 260 | 14.1 | 2 | 157 | YES | PASS |
| 25_fizzbuzz | 304 | 15.3 | 2 | 168 | YES | PASS |
| 26_generics | 284 | 14.5 | 5 | 170 | YES | PASS |
| 27_impl | 244 | 13.3 | 3 | 154 | YES | PASS |
| 28_traits | 252 | 13.5 | 3 | 136 | YES | PASS |
| 29_generic_impl | 253 | 13.7 | 3 | 157 | YES | PASS |
| 30_nested_generics | 244 | 14.1 | 1 | 137 | YES | PASS |
| 31_generic_multi | 269 | 14.6 | 4 | 174 | YES | PASS |
| 32_generic_enum | 215 | 12.3 | 1 | 143 | YES | PASS |
| 33_break_continue | 428 | 19.1 | 5 | 163 | YES | PASS |
| 34_file_io | 299 | 16.9 | 1 | 141 | YES | PASS |
| 35_stdin | 229 | 13.2 | 1 | 159 | YES | PASS |
| 36_crypto | 258 | 14.6 | 1 | 168 | YES | PASS |
| 37_regex | 269 | 15.3 | 1 | 168 | YES | PASS |
| 38_http | 220 | 12.7 | 1 | 150 | YES | PASS |
| 39_gpu_detect | 247 | 13.9 | 1 | 145 | YES | PASS |
| 40_gpu_tensor | 434 | 22.6 | 1 | 172 | YES | PASS |
| 41_module_let | 218 | 12.2 | 2 | 135 | YES | PASS |
| 42_module_let_string | 221 | 12.4 | 2 | 115 | YES | PASS |
| 43_module_let_math | 225 | 12.6 | 2 | 126 | YES | PASS |
| 45_ffi_bind | 253 | 13.2 | 3 | 161 | YES | PASS |
| 47_try_operator | 356 | 17.9 | 4 | 171 | YES | PASS |
| 48_match_nested_exhaustive | 449 | 22.4 | 3 | 155 | YES | PASS |
| 49_match_guards | 276 | 14.8 | 2 | 165 | YES | PASS |
| 49_tensor_literal | 481 | 24.4 | 1 | 143 | YES | PASS |
| 50_match_or_patterns | 294 | 15.8 | 2 | 164 | YES | PASS |
| 50_tensor_indexing | 453 | 23.2 | 1 | 153 | YES | PASS |
| 51_match_guards_and_or | 345 | 17.5 | 2 | 209 | YES | PASS |
| 51_tensor_broadcast | 465 | 23.3 | 1 | 146 | YES | PASS |
| 52_tensor_slicing | 460 | 23.5 | 1 | 175 | YES | PASS |
| 53_linear_regression | 387 | 19.8 | 1 | 146 | YES | PASS |
| 54_const_basic | 224 | 12.8 | 1 | 107 | YES | PASS |
| 55_async_basic | 266 | 14.3 | 2 | 162 | YES | PASS |
| 56_async_await | 345 | 17.2 | 3 | 160 | YES | PASS |
| 57_real_await | 501 | 23.0 | 5 | 162 | YES | PASS |
| 58_async_file_io | 428 | 20.2 | 4 | 159 | YES | PASS |
| 58_const_scope | 257 | 13.7 | 2 | 152 | YES | PASS |
| 59_async_fanout | 1054 | 44.0 | 12 | 157 | YES | PASS |
| 62_list_output | 385 | 20.8 | 3 | 191 | YES | PASS |
| 63_else_sino | 313 | 15.6 | 3 | 149 | YES | PASS |
| 64_closure_typed | 326 | 15.8 | 3 | 288 | YES | PASS |
| 65_list_int_indexing | 403 | 21.1 | 1 | 179 | YES | PASS |
| 66_qualified_type_ref | 240 | 13.3 | 2 | 147 | YES | PASS |
| 67_implicit_return_one_liner | 267 | 13.9 | 4 | 144 | YES | PASS |
| 68_terse_lambda | 316 | 15.4 | 3 | 150 | YES | PASS |
| 69_list_comp | 368 | 19.5 | 1 | 178 | YES | PASS |
| 70_list_comp_filter | 377 | 19.7 | 1 | 209 | YES | PASS |
| 71_map_comp | 265 | 14.4 | 1 | 157 | YES | PASS |
| 72_string_interp_var | 220 | 12.7 | 1 | 117 | YES | PASS |
| 73_string_interp_int | 220 | 12.7 | 1 | 142 | YES | PASS |
| 74_string_interp_float | 220 | 12.7 | 1 | 141 | YES | PASS |
| 75_string_interp_bool | 221 | 12.7 | 1 | 134 | YES | PASS |
| 76_string_interp_method | 219 | 12.6 | 1 | 172 | YES | PASS |
| 77_string_interp_arith | 219 | 12.6 | 1 | 117 | YES | PASS |
| 78_string_interp_multi | 236 | 13.4 | 1 | 195 | YES | PASS |
| 79_string_interp_mixed | 230 | 13.2 | 1 | 143 | YES | PASS |
| 80_string_interp_escaped | 204 | 12.0 | 1 | 129 | YES | PASS |
| 81_struct_shorthand | 0 | 0.0 | 0 | 30 | - | FAIL |
| 82_struct_update | 0 | 0.0 | 0 | 29 | - | FAIL |
| 83_struct_update_partial | 0 | 0.0 | 0 | 30 | - | FAIL |
| 84_let_destructure | 0 | 0.0 | 0 | 29 | - | FAIL |
| 85_let_destructure_nested | 0 | 0.0 | 0 | 29 | - | FAIL |
| 86_let_destructure_rest | 0 | 0.0 | 0 | 29 | - | FAIL |
| 87_let_destructure_mut | 0 | 0.0 | 0 | 31 | - | FAIL |
| 88_if_let | 0 | 0.0 | 0 | 37 | - | FAIL |
| 89_if_let_else | 0 | 0.0 | 0 | 36 | - | FAIL |
| 90_while_let | 0 | 0.0 | 0 | 37 | - | FAIL |
| 91_let_else | 0 | 0.0 | 0 | 35 | - | FAIL |
| **Total** | | | | **13224** | **80/91** | **80/91** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1017 | 295 | 3.4x |
| 02_arithmetic | 9 | 169 | 0.1x |
| 03_function | 6 | 182 | 0.0x |
| 04_if_else | 6 | 151 | 0.0x |
| 05_for_loop | 5 | 181 | 0.0x |
| 06_struct | 6 | 155 | 0.0x |
| 07_enum_match | 12 | 135 | 0.1x |
| 08_list | 7 | 158 | 0.0x |
| 09_string_methods | 5 | 219 | 0.0x |
| 10_result | 7 | 153 | 0.0x |
| 11_closure | 4 | 147 | 0.0x |
| 12_while | 4 | 171 | 0.0x |
| 13_fib | 5 | 161 | 0.0x |
| 14_nested_struct | 4 | 148 | 0.0x |
| 15_multifunction | 6 | 144 | 0.0x |
| 16_string_escape | 4 | 112 | 0.0x |
| 17_option | 6 | 179 | 0.0x |
| 18_method_chain | 6 | 160 | 0.0x |
| 19_nested_match | 7 | 168 | 0.0x |
| 20_recursion | 5 | 146 | 0.0x |
| 21_list_ops | 6 | 186 | 0.0x |
| 22_string_builder | 6 | 180 | 0.0x |
| 23_multi_return | 7 | 202 | 0.0x |
| 24_enum_methods | 5 | 157 | 0.0x |
| 25_fizzbuzz | 6 | 168 | 0.0x |
| 26_generics | 8 | 170 | 0.0x |
| 27_impl | 8 | 154 | 0.1x |
| 28_traits | 6 | 136 | 0.0x |
| 29_generic_impl | 6 | 157 | 0.0x |
| 30_nested_generics | 6 | 137 | 0.0x |
| 31_generic_multi | 7 | 174 | 0.0x |
| 32_generic_enum | 5 | 143 | 0.0x |
| 33_break_continue | 9 | 163 | 0.1x |
| 34_file_io | 5 | 141 | 0.0x |
| 35_stdin | 5 | 159 | 0.0x |
| 36_crypto | 5 | 168 | 0.0x |
| 37_regex | 6 | 168 | 0.0x |
| 38_http | 5 | 150 | 0.0x |
| 39_gpu_detect | 5 | 145 | 0.0x |
| 40_gpu_tensor | 7 | 172 | 0.0x |
| 41_module_let | 5 | 135 | 0.0x |
| 42_module_let_string | 5 | 115 | 0.0x |
| 43_module_let_math | 5 | 126 | 0.0x |
| 45_ffi_bind | 5 | 161 | 0.0x |
| 47_try_operator | 8 | 171 | 0.0x |
| 48_match_nested_exhaustive | 6 | 155 | 0.0x |
| 49_match_guards | 6 | 165 | 0.0x |
| 49_tensor_literal | 11 | 143 | 0.1x |
| 50_match_or_patterns | 6 | 164 | 0.0x |
| 50_tensor_indexing | 8 | 153 | 0.1x |
| 51_match_guards_and_or | 8 | 209 | 0.0x |
| 51_tensor_broadcast | 8 | 146 | 0.1x |
| 52_tensor_slicing | 23 | 175 | 0.1x |
| 53_linear_regression | 7 | 146 | 0.0x |
| 54_const_basic | 4 | 107 | 0.0x |
| 55_async_basic | 4 | 162 | 0.0x |
| 56_async_await | 5 | 160 | 0.0x |
| 57_real_await | 5 | 162 | 0.0x |
| 58_async_file_io | 5 | 159 | 0.0x |
| 58_const_scope | 5 | 152 | 0.0x |
| 59_async_fanout | 8 | 157 | 0.0x |
| 62_list_output | 7 | 191 | 0.0x |
| 63_else_sino | 6 | 149 | 0.0x |
| 64_closure_typed | 8 | 288 | 0.0x |
| 65_list_int_indexing | 9 | 179 | 0.0x |
| 66_qualified_type_ref | 5 | 147 | 0.0x |
| 67_implicit_return_one_liner | 6 | 144 | 0.0x |
| 68_terse_lambda | 9 | 150 | 0.1x |
| 69_list_comp | 6 | 178 | 0.0x |
| 70_list_comp_filter | 7 | 209 | 0.0x |
| 71_map_comp | 6 | 157 | 0.0x |
| 72_string_interp_var | 4 | 117 | 0.0x |
| 73_string_interp_int | 4 | 142 | 0.0x |
| 74_string_interp_float | 5 | 141 | 0.0x |
| 75_string_interp_bool | 4 | 134 | 0.0x |
| 76_string_interp_method | 5 | 172 | 0.0x |
| 77_string_interp_arith | 4 | 117 | 0.0x |
| 78_string_interp_multi | 5 | 195 | 0.0x |
| 79_string_interp_mixed | 4 | 143 | 0.0x |
| 80_string_interp_escaped | 4 | 129 | 0.0x |

