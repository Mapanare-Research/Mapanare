# Mapanare Benchmarks - Linux

Generated: 2026-05-03 04:45 UTC  
Version: 5.31.0 (`2633711`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 19.3s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1201 | `_....__. ^` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 10 | `         ^` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 8 | `        ` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 5 | `       _ ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         ^` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 14 | `        ` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 10 | `         ^` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 8 | `         ^` | PASS |
| 10_result | 10 | 147 | 5.3 | 2 | 10 | 155 | 10 | `         v` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 6 | `        ` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 6 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 4 | `        ` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 7 | `        ` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `_.__ _.  v` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 10 | `         ^` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         ^` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | `_. .__ _ ^` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 6 | `         ^` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 5 | `         ^` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 8 | `         ^` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 7 | `        ` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 5 | `        ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         ^` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 6 | `         v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         ^` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 7 | `         ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 11 | `         ^` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 6 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 6 | `         ^` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 6 | `_       ` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `_-______ v` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 4 | ` .   . _ ^` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 6 | `         ^` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 9 | `        ` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 4 | `         v` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | `___ . __` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 6 | `    _   ` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 12 | `         ^` | PASS |
| 47_try_operator | 25 | 308 | 11.8 | 4 | 23 | 311 | 9 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 345 | 14.0 | 3 | 32 | 325 | 8 | `        ` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 12 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 7 | `         v` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `        ` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 11 | `_        ^` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 10 | ` _       ^` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 8 | `    _  . ^` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `         ^` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 4 | ` _      ` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `       . ^` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 5 | `.    .   ^` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 6 | ` __ ____` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 7 | ` .  .  _ ^` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 28 | ` ._.. ._ v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 7 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | ` .    _- ^` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         ^` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `        ` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 6 | `.____ _  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `  _     ` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 8 | ` . _   _ ^` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 5 | `-._ ____` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 7 | `.        v` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 7 | `__ _    ` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 5 | `__     _ ^` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` _      ` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` .     _ ^` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 4 | ` -  .  _ ^` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 4 | ` _  _  * ^` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` .    .  v` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | ` - __   ` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `-  _     v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `_.___.__` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 7 | `.  __  _ ^` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 7 | ` ___    ` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 6 | `        ` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 7 | `___     ` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 5 | `-  . . _ ^` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 5 | ` _ __. . ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 6 | `  _ _   ` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 5 | `    _   ` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `________` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | ` _      ` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 6 | ` _  _   ` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 8 | ` - .  .  v` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 6 | ` _    .  v` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | `    .   ` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `        ` | PASS |
| **Total** | **1540** | **16605** | **621.3** | **143** | **1333** | **14182** | **1840** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 206 | 12.1 | 1 | 244 | YES | PASS |
| 02_arithmetic | 216 | 12.4 | 1 | 203 | YES | PASS |
| 03_function | 238 | 13.0 | 2 | 156 | YES | PASS |
| 04_if_else | 223 | 12.7 | 1 | 168 | YES | PASS |
| 05_for_loop | 239 | 13.2 | 1 | 211 | YES | PASS |
| 06_struct | 219 | 12.6 | 1 | 167 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 302 | YES | PASS |
| 08_list | 245 | 13.9 | 1 | 199 | YES | PASS |
| 09_string_methods | 229 | 13.2 | 1 | 203 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 234 | YES | PASS |
| 11_closure | 229 | 12.7 | 1 | 173 | YES | PASS |
| 12_while | 225 | 12.6 | 1 | 168 | YES | PASS |
| 13_fib | 236 | 12.8 | 2 | 179 | YES | PASS |
| 14_nested_struct | 219 | 12.6 | 1 | 148 | YES | PASS |
| 15_multifunction | 249 | 13.4 | 3 | 163 | YES | PASS |
| 16_string_escape | 225 | 13.0 | 1 | 148 | YES | PASS |
| 17_option | 308 | 15.7 | 2 | 185 | YES | PASS |
| 18_method_chain | 251 | 14.2 | 1 | 181 | YES | PASS |
| 19_nested_match | 274 | 14.4 | 2 | 254 | YES | PASS |
| 20_recursion | 242 | 13.1 | 2 | 163 | YES | PASS |
| 21_list_ops | 327 | 17.3 | 2 | 193 | YES | PASS |
| 22_string_builder | 294 | 15.7 | 2 | 178 | YES | PASS |
| 23_multi_return | 268 | 14.7 | 2 | 204 | YES | PASS |
| 24_enum_methods | 262 | 14.2 | 2 | 182 | YES | PASS |
| 25_fizzbuzz | 306 | 15.5 | 2 | 165 | YES | PASS |
| 26_generics | 286 | 14.6 | 5 | 166 | YES | PASS |
| 27_impl | 246 | 13.4 | 3 | 159 | YES | PASS |
| 28_traits | 254 | 13.7 | 3 | 167 | YES | PASS |
| 29_generic_impl | 255 | 13.9 | 3 | 184 | YES | PASS |
| 30_nested_generics | 246 | 14.2 | 1 | 143 | YES | PASS |
| 31_generic_multi | 271 | 14.7 | 4 | 210 | YES | PASS |
| 32_generic_enum | 217 | 12.5 | 1 | 184 | YES | PASS |
| 33_break_continue | 430 | 19.3 | 5 | 191 | YES | PASS |
| 34_file_io | 301 | 17.0 | 1 | 191 | YES | PASS |
| 35_stdin | 231 | 13.3 | 1 | 228 | YES | PASS |
| 36_crypto | 260 | 14.8 | 1 | 203 | YES | PASS |
| 37_regex | 271 | 15.4 | 1 | 205 | YES | PASS |
| 38_http | 222 | 12.9 | 1 | 156 | YES | PASS |
| 39_gpu_detect | 249 | 14.1 | 1 | 149 | YES | PASS |
| 40_gpu_tensor | 436 | 22.8 | 1 | 199 | YES | PASS |
| 41_module_let | 220 | 12.4 | 2 | 129 | YES | PASS |
| 42_module_let_string | 223 | 12.6 | 2 | 128 | YES | PASS |
| 43_module_let_math | 227 | 12.8 | 2 | 270 | YES | PASS |
| 45_ffi_bind | 255 | 13.3 | 3 | 218 | YES | PASS |
| 47_try_operator | 354 | 18.0 | 4 | 170 | YES | PASS |
| 48_match_nested_exhaustive | 451 | 22.6 | 3 | 232 | YES | PASS |
| 49_match_guards | 312 | 15.9 | 2 | 152 | YES | PASS |
| 49_tensor_literal | 483 | 24.6 | 1 | 146 | YES | PASS |
| 50_match_or_patterns | 296 | 15.9 | 2 | 179 | YES | PASS |
| 50_tensor_indexing | 455 | 23.3 | 1 | 152 | YES | PASS |
| 51_match_guards_and_or | 378 | 18.7 | 2 | 188 | YES | PASS |
| 51_tensor_broadcast | 467 | 23.5 | 1 | 271 | YES | PASS |
| 52_tensor_slicing | 462 | 23.7 | 1 | 209 | YES | PASS |
| 53_linear_regression | 389 | 19.9 | 1 | 193 | YES | PASS |
| 54_const_basic | 226 | 13.0 | 1 | 170 | YES | PASS |
| 55_async_basic | 268 | 14.5 | 2 | 155 | YES | PASS |
| 56_async_await | 347 | 17.4 | 3 | 167 | YES | PASS |
| 57_real_await | 503 | 23.1 | 5 | 152 | YES | PASS |
| 58_async_file_io | 430 | 20.4 | 4 | 168 | YES | PASS |
| 58_const_scope | 259 | 13.9 | 2 | 159 | YES | PASS |
| 59_async_fanout | 1056 | 44.1 | 12 | 154 | YES | PASS |
| 62_list_output | 387 | 20.9 | 3 | 193 | YES | PASS |
| 63_else_sino | 315 | 15.8 | 3 | 174 | YES | PASS |
| 64_closure_typed | 328 | 16.0 | 3 | 156 | YES | PASS |
| 65_list_int_indexing | 405 | 21.3 | 1 | 174 | YES | PASS |
| 66_qualified_type_ref | 242 | 13.4 | 2 | 150 | YES | PASS |
| 67_implicit_return_one_liner | 269 | 14.0 | 4 | 144 | YES | PASS |
| 68_terse_lambda | 318 | 15.6 | 3 | 230 | YES | PASS |
| 69_list_comp | 370 | 19.6 | 1 | 156 | YES | PASS |
| 70_list_comp_filter | 379 | 19.8 | 1 | 187 | YES | PASS |
| 71_map_comp | 267 | 14.6 | 1 | 188 | YES | PASS |
| 72_string_interp_var | 222 | 12.9 | 1 | 132 | YES | PASS |
| 73_string_interp_int | 222 | 12.8 | 1 | 124 | YES | PASS |
| 74_string_interp_float | 222 | 12.8 | 1 | 156 | YES | PASS |
| 75_string_interp_bool | 223 | 12.8 | 1 | 135 | YES | PASS |
| 76_string_interp_method | 221 | 12.7 | 1 | 144 | YES | PASS |
| 77_string_interp_arith | 221 | 12.8 | 1 | 142 | YES | PASS |
| 78_string_interp_multi | 238 | 13.5 | 1 | 144 | YES | PASS |
| 79_string_interp_mixed | 232 | 13.4 | 1 | 127 | YES | PASS |
| 80_string_interp_escaped | 206 | 12.2 | 1 | 115 | YES | PASS |
| 81_struct_shorthand | 259 | 14.3 | 1 | 168 | YES | PASS |
| 82_struct_update | 255 | 14.3 | 1 | 201 | YES | PASS |
| 83_struct_update_partial | 268 | 14.8 | 1 | 175 | YES | PASS |
| 84_let_destructure | 234 | 13.2 | 1 | 155 | YES | PASS |
| 85_let_destructure_nested | 245 | 13.7 | 1 | 149 | YES | PASS |
| 86_let_destructure_rest | 224 | 12.8 | 1 | 150 | YES | PASS |
| 87_let_destructure_mut | 238 | 13.3 | 1 | 159 | YES | PASS |
| 88_if_let | 237 | 13.1 | 1 | 157 | YES | PASS |
| 89_if_let_else | 232 | 13.0 | 1 | 158 | YES | PASS |
| 90_while_let | 240 | 13.2 | 1 | 173 | YES | PASS |
| 91_let_else | 264 | 14.1 | 2 | 155 | YES | PASS |
| 92_chained_cmp_simple | 280 | 14.8 | 2 | 162 | YES | PASS |
| 93_chained_cmp_4 | 288 | 15.0 | 2 | 152 | YES | PASS |
| 94_chained_cmp_mixed | 335 | 16.5 | 4 | 160 | YES | PASS |
| 95_chained_cmp_side_effect | 303 | 15.9 | 3 | 215 | YES | PASS |
| **Total** | | | | **16724** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1201 | 244 | 4.9x |
| 02_arithmetic | 10 | 203 | 0.0x |
| 03_function | 8 | 156 | 0.0x |
| 04_if_else | 5 | 168 | 0.0x |
| 05_for_loop | 5 | 211 | 0.0x |
| 06_struct | 6 | 167 | 0.0x |
| 07_enum_match | 14 | 302 | 0.0x |
| 08_list | 10 | 199 | 0.1x |
| 09_string_methods | 8 | 203 | 0.0x |
| 10_result | 10 | 234 | 0.0x |
| 11_closure | 6 | 173 | 0.0x |
| 12_while | 6 | 168 | 0.0x |
| 13_fib | 5 | 179 | 0.0x |
| 14_nested_struct | 5 | 148 | 0.0x |
| 15_multifunction | 6 | 163 | 0.0x |
| 16_string_escape | 4 | 148 | 0.0x |
| 17_option | 7 | 185 | 0.0x |
| 18_method_chain | 5 | 181 | 0.0x |
| 19_nested_match | 10 | 254 | 0.0x |
| 20_recursion | 5 | 163 | 0.0x |
| 21_list_ops | 6 | 193 | 0.0x |
| 22_string_builder | 6 | 178 | 0.0x |
| 23_multi_return | 6 | 204 | 0.0x |
| 24_enum_methods | 6 | 182 | 0.0x |
| 25_fizzbuzz | 5 | 165 | 0.0x |
| 26_generics | 8 | 166 | 0.0x |
| 27_impl | 7 | 159 | 0.0x |
| 28_traits | 5 | 167 | 0.0x |
| 29_generic_impl | 7 | 184 | 0.0x |
| 30_nested_generics | 6 | 143 | 0.0x |
| 31_generic_multi | 8 | 210 | 0.0x |
| 32_generic_enum | 7 | 184 | 0.0x |
| 33_break_continue | 11 | 191 | 0.1x |
| 34_file_io | 6 | 191 | 0.0x |
| 35_stdin | 6 | 228 | 0.0x |
| 36_crypto | 6 | 203 | 0.0x |
| 37_regex | 6 | 205 | 0.0x |
| 38_http | 4 | 156 | 0.0x |
| 39_gpu_detect | 6 | 149 | 0.0x |
| 40_gpu_tensor | 9 | 199 | 0.0x |
| 41_module_let | 4 | 129 | 0.0x |
| 42_module_let_string | 5 | 128 | 0.0x |
| 43_module_let_math | 6 | 270 | 0.0x |
| 45_ffi_bind | 12 | 218 | 0.1x |
| 47_try_operator | 9 | 170 | 0.1x |
| 48_match_nested_exhaustive | 8 | 232 | 0.0x |
| 49_match_guards | 6 | 152 | 0.0x |
| 49_tensor_literal | 12 | 146 | 0.1x |
| 50_match_or_patterns | 7 | 179 | 0.0x |
| 50_tensor_indexing | 8 | 152 | 0.1x |
| 51_match_guards_and_or | 7 | 188 | 0.0x |
| 51_tensor_broadcast | 11 | 271 | 0.0x |
| 52_tensor_slicing | 10 | 209 | 0.0x |
| 53_linear_regression | 8 | 193 | 0.0x |
| 54_const_basic | 5 | 170 | 0.0x |
| 55_async_basic | 4 | 155 | 0.0x |
| 56_async_await | 5 | 167 | 0.0x |
| 57_real_await | 5 | 152 | 0.0x |
| 58_async_file_io | 6 | 168 | 0.0x |
| 58_const_scope | 7 | 159 | 0.0x |
| 59_async_fanout | 28 | 154 | 0.2x |
| 62_list_output | 7 | 193 | 0.0x |
| 63_else_sino | 7 | 174 | 0.0x |
| 64_closure_typed | 8 | 156 | 0.1x |
| 65_list_int_indexing | 6 | 174 | 0.0x |
| 66_qualified_type_ref | 6 | 150 | 0.0x |
| 67_implicit_return_one_liner | 6 | 144 | 0.0x |
| 68_terse_lambda | 8 | 230 | 0.0x |
| 69_list_comp | 5 | 156 | 0.0x |
| 70_list_comp_filter | 7 | 187 | 0.0x |
| 71_map_comp | 7 | 188 | 0.0x |
| 72_string_interp_var | 5 | 132 | 0.0x |
| 73_string_interp_int | 5 | 124 | 0.0x |
| 74_string_interp_float | 5 | 156 | 0.0x |
| 75_string_interp_bool | 4 | 135 | 0.0x |
| 76_string_interp_method | 4 | 144 | 0.0x |
| 77_string_interp_arith | 4 | 142 | 0.0x |
| 78_string_interp_multi | 5 | 144 | 0.0x |
| 79_string_interp_mixed | 4 | 127 | 0.0x |
| 80_string_interp_escaped | 4 | 115 | 0.0x |
| 81_struct_shorthand | 7 | 168 | 0.0x |
| 82_struct_update | 7 | 201 | 0.0x |
| 83_struct_update_partial | 6 | 175 | 0.0x |
| 84_let_destructure | 7 | 155 | 0.0x |
| 85_let_destructure_nested | 5 | 149 | 0.0x |
| 86_let_destructure_rest | 5 | 150 | 0.0x |
| 87_let_destructure_mut | 6 | 159 | 0.0x |
| 88_if_let | 5 | 157 | 0.0x |
| 89_if_let_else | 5 | 158 | 0.0x |
| 90_while_let | 5 | 173 | 0.0x |
| 91_let_else | 6 | 155 | 0.0x |
| 92_chained_cmp_simple | 8 | 162 | 0.0x |
| 93_chained_cmp_4 | 6 | 152 | 0.0x |
| 94_chained_cmp_mixed | 8 | 160 | 0.1x |
| 95_chained_cmp_side_effect | 6 | 215 | 0.0x |

