# Mapanare Benchmarks - Linux

Generated: 2026-04-29 21:17 UTC  
Version: 5.16.0 (`cc70ff7`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 16.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 865 | `___._... v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | ` _     _ ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 6 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         ^` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 8 | `         ^` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 7 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `        ` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 7 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `        ` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `        ` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 7 | `_____._. ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `  _     ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 10 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 7 | ` _   _.  v` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 6 | `         ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `        ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `         ^` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         ^` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 14 | `         ^` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 7 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 6 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `       . ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_._ ____ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `__. _  . ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 6 | `         v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | ` _.   __` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 45_ffi_bind | 15 | 98 | 2.8 | 2 | 9 | 83 | 5 | `         v` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | `         ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 9 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 8 | `         ^` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 9 | `_-__._._ v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 9 | `_.__..._ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 10 | `       _ ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `...--.-. v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `_        v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `       _ ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | ` __   _. ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `     _ _ ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `__ ___._ v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `__ _____` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 7 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 7 | ` _  _  _ ^` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         ^` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `.-.....- ^` | PASS |
| 67_implicit_return_one_liner | 17 | 106 | 3.6 | 1 | 14 | 75 | 6 | `**. .*..` | PASS |
| 68_terse_lambda | 22 | 213 | 7.2 | 1 | 20 | 227 | 8 | `_   ___  v` | PASS |
| 69_list_comp | 12 | 287 | 11.4 | 1 | 21 | 325 | 10 | `*.*  v` | PASS |
| 70_list_comp_filter | 11 | 303 | 11.9 | 1 | 24 | 334 | 6 | `*  * ^` | PASS |
| 71_map_comp | 12 | 156 | 5.5 | 1 | 11 | 148 | 6 | `*   ` | PASS |
| 72_string_interp_var | 10 | 63 | 2.4 | 1 | 4 | 41 | 4 | ` ` | PASS |
| 73_string_interp_int | 7 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` ` | PASS |
| 74_string_interp_float | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` ` | PASS |
| 75_string_interp_bool | 7 | 73 | 2.7 | 1 | 6 | 42 | 4 | ` ` | PASS |
| 76_string_interp_method | 8 | 60 | 2.2 | 1 | 4 | 41 | 6 | ` ` | PASS |
| 77_string_interp_arith | 5 | 72 | 2.7 | 1 | 6 | 49 | 5 | ` ` | PASS |
| 78_string_interp_multi | 9 | 104 | 4.0 | 1 | 10 | 81 | 5 | ` ` | PASS |
| 79_string_interp_mixed | 10 | 92 | 3.6 | 1 | 8 | 65 | 5 | ` ` | PASS |
| 80_string_interp_escaped | 8 | 32 | 1.0 | 1 | 2 | 9 | 4 | ` ` | PASS |
| **Total** | **1480** | **14758** | **555.9** | **126** | **1181** | **12684** | **1363** | | **80/80** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 204 | 11.9 | 1 | 119 | YES | PASS |
| 02_arithmetic | 214 | 12.2 | 1 | 141 | YES | PASS |
| 03_function | 236 | 12.9 | 2 | 132 | YES | PASS |
| 04_if_else | 221 | 12.5 | 1 | 142 | YES | PASS |
| 05_for_loop | 237 | 13.1 | 1 | 179 | YES | PASS |
| 06_struct | 217 | 12.4 | 1 | 148 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 152 | YES | PASS |
| 08_list | 243 | 13.7 | 1 | 228 | YES | PASS |
| 09_string_methods | 227 | 13.1 | 1 | 163 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 191 | YES | PASS |
| 11_closure | 227 | 12.6 | 1 | 155 | YES | PASS |
| 12_while | 223 | 12.5 | 1 | 134 | YES | PASS |
| 13_fib | 234 | 12.7 | 2 | 165 | YES | PASS |
| 14_nested_struct | 217 | 12.4 | 1 | 170 | YES | PASS |
| 15_multifunction | 247 | 13.2 | 3 | 147 | YES | PASS |
| 16_string_escape | 223 | 12.9 | 1 | 120 | YES | PASS |
| 17_option | 299 | 15.3 | 2 | 192 | YES | PASS |
| 18_method_chain | 249 | 14.1 | 1 | 193 | YES | PASS |
| 19_nested_match | 272 | 14.2 | 2 | 187 | YES | PASS |
| 20_recursion | 240 | 13.0 | 2 | 204 | YES | PASS |
| 21_list_ops | 325 | 17.1 | 2 | 234 | YES | PASS |
| 22_string_builder | 292 | 15.6 | 2 | 193 | YES | PASS |
| 23_multi_return | 266 | 14.5 | 2 | 151 | YES | PASS |
| 24_enum_methods | 260 | 14.1 | 2 | 162 | YES | PASS |
| 25_fizzbuzz | 304 | 15.3 | 2 | 182 | YES | PASS |
| 26_generics | 284 | 14.5 | 5 | 157 | YES | PASS |
| 27_impl | 244 | 13.3 | 3 | 173 | YES | PASS |
| 28_traits | 252 | 13.5 | 3 | 166 | YES | PASS |
| 29_generic_impl | 253 | 13.7 | 3 | 178 | YES | PASS |
| 30_nested_generics | 244 | 14.1 | 1 | 180 | YES | PASS |
| 31_generic_multi | 269 | 14.6 | 4 | 182 | YES | PASS |
| 32_generic_enum | 215 | 12.3 | 1 | 174 | YES | PASS |
| 33_break_continue | 428 | 19.1 | 5 | 403 | YES | PASS |
| 34_file_io | 299 | 16.9 | 1 | 182 | YES | PASS |
| 35_stdin | 229 | 13.2 | 1 | 175 | YES | PASS |
| 36_crypto | 258 | 14.6 | 1 | 132 | YES | PASS |
| 37_regex | 269 | 15.3 | 1 | 138 | YES | PASS |
| 38_http | 220 | 12.7 | 1 | 165 | YES | PASS |
| 39_gpu_detect | 247 | 13.9 | 1 | 180 | YES | PASS |
| 40_gpu_tensor | 434 | 22.6 | 1 | 172 | YES | PASS |
| 41_module_let | 218 | 12.2 | 2 | 138 | YES | PASS |
| 42_module_let_string | 221 | 12.4 | 2 | 146 | YES | PASS |
| 43_module_let_math | 225 | 12.6 | 2 | 126 | YES | PASS |
| 45_ffi_bind | 253 | 13.2 | 3 | 185 | YES | PASS |
| 47_try_operator | 356 | 17.9 | 4 | 225 | YES | PASS |
| 48_match_nested_exhaustive | 449 | 22.4 | 3 | 161 | YES | PASS |
| 49_match_guards | 276 | 14.8 | 2 | 198 | YES | PASS |
| 49_tensor_literal | 481 | 24.4 | 1 | 153 | YES | PASS |
| 50_match_or_patterns | 294 | 15.8 | 2 | 177 | YES | PASS |
| 50_tensor_indexing | 453 | 23.2 | 1 | 195 | YES | PASS |
| 51_match_guards_and_or | 345 | 17.5 | 2 | 194 | YES | PASS |
| 51_tensor_broadcast | 465 | 23.3 | 1 | 219 | YES | PASS |
| 52_tensor_slicing | 460 | 23.5 | 1 | 253 | YES | PASS |
| 53_linear_regression | 387 | 19.8 | 1 | 244 | YES | PASS |
| 54_const_basic | 224 | 12.8 | 1 | 143 | YES | PASS |
| 55_async_basic | 266 | 14.3 | 2 | 207 | YES | PASS |
| 56_async_await | 345 | 17.2 | 3 | 171 | YES | PASS |
| 57_real_await | 501 | 23.0 | 5 | 169 | YES | PASS |
| 58_async_file_io | 428 | 20.2 | 4 | 158 | YES | PASS |
| 58_const_scope | 257 | 13.7 | 2 | 176 | YES | PASS |
| 59_async_fanout | 1054 | 44.0 | 12 | 141 | YES | PASS |
| 62_list_output | 385 | 20.8 | 3 | 171 | YES | PASS |
| 63_else_sino | 313 | 15.6 | 3 | 188 | YES | PASS |
| 64_closure_typed | 326 | 15.8 | 3 | 210 | YES | PASS |
| 65_list_int_indexing | 403 | 21.1 | 1 | 167 | YES | PASS |
| 66_qualified_type_ref | 240 | 13.3 | 2 | 171 | YES | PASS |
| 67_implicit_return_one_liner | 267 | 13.9 | 4 | 148 | YES | PASS |
| 68_terse_lambda | 316 | 15.4 | 3 | 228 | YES | PASS |
| 69_list_comp | 368 | 19.5 | 1 | 166 | YES | PASS |
| 70_list_comp_filter | 377 | 19.7 | 1 | 177 | YES | PASS |
| 71_map_comp | 265 | 14.4 | 1 | 198 | YES | PASS |
| 72_string_interp_var | 220 | 12.7 | 1 | 156 | YES | PASS |
| 73_string_interp_int | 220 | 12.7 | 1 | 137 | YES | PASS |
| 74_string_interp_float | 220 | 12.7 | 1 | 141 | YES | PASS |
| 75_string_interp_bool | 221 | 12.7 | 1 | 137 | YES | PASS |
| 76_string_interp_method | 219 | 12.6 | 1 | 230 | YES | PASS |
| 77_string_interp_arith | 219 | 12.6 | 1 | 194 | YES | PASS |
| 78_string_interp_multi | 236 | 13.4 | 1 | 144 | YES | PASS |
| 79_string_interp_mixed | 230 | 13.2 | 1 | 155 | YES | PASS |
| 80_string_interp_escaped | 204 | 12.0 | 1 | 152 | YES | PASS |
| **Total** | | | | **13990** | **80/80** | **80/80** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 865 | 119 | 7.3x |
| 02_arithmetic | 7 | 141 | 0.1x |
| 03_function | 6 | 132 | 0.0x |
| 04_if_else | 5 | 142 | 0.0x |
| 05_for_loop | 5 | 179 | 0.0x |
| 06_struct | 6 | 148 | 0.0x |
| 07_enum_match | 12 | 152 | 0.1x |
| 08_list | 8 | 228 | 0.0x |
| 09_string_methods | 5 | 163 | 0.0x |
| 10_result | 7 | 191 | 0.0x |
| 11_closure | 5 | 155 | 0.0x |
| 12_while | 4 | 134 | 0.0x |
| 13_fib | 5 | 165 | 0.0x |
| 14_nested_struct | 6 | 170 | 0.0x |
| 15_multifunction | 7 | 147 | 0.0x |
| 16_string_escape | 4 | 120 | 0.0x |
| 17_option | 6 | 192 | 0.0x |
| 18_method_chain | 7 | 193 | 0.0x |
| 19_nested_match | 7 | 187 | 0.0x |
| 20_recursion | 5 | 204 | 0.0x |
| 21_list_ops | 10 | 234 | 0.0x |
| 22_string_builder | 7 | 193 | 0.0x |
| 23_multi_return | 6 | 151 | 0.0x |
| 24_enum_methods | 5 | 162 | 0.0x |
| 25_fizzbuzz | 6 | 182 | 0.0x |
| 26_generics | 7 | 157 | 0.0x |
| 27_impl | 6 | 173 | 0.0x |
| 28_traits | 6 | 166 | 0.0x |
| 29_generic_impl | 7 | 178 | 0.0x |
| 30_nested_generics | 6 | 180 | 0.0x |
| 31_generic_multi | 8 | 182 | 0.0x |
| 32_generic_enum | 4 | 174 | 0.0x |
| 33_break_continue | 14 | 403 | 0.0x |
| 34_file_io | 7 | 182 | 0.0x |
| 35_stdin | 6 | 175 | 0.0x |
| 36_crypto | 5 | 132 | 0.0x |
| 37_regex | 5 | 138 | 0.0x |
| 38_http | 5 | 165 | 0.0x |
| 39_gpu_detect | 5 | 180 | 0.0x |
| 40_gpu_tensor | 6 | 172 | 0.0x |
| 41_module_let | 5 | 138 | 0.0x |
| 42_module_let_string | 5 | 146 | 0.0x |
| 43_module_let_math | 5 | 126 | 0.0x |
| 45_ffi_bind | 5 | 185 | 0.0x |
| 47_try_operator | 7 | 225 | 0.0x |
| 48_match_nested_exhaustive | 6 | 161 | 0.0x |
| 49_match_guards | 6 | 198 | 0.0x |
| 49_tensor_literal | 11 | 153 | 0.1x |
| 50_match_or_patterns | 6 | 177 | 0.0x |
| 50_tensor_indexing | 9 | 195 | 0.0x |
| 51_match_guards_and_or | 8 | 194 | 0.0x |
| 51_tensor_broadcast | 9 | 219 | 0.0x |
| 52_tensor_slicing | 9 | 253 | 0.0x |
| 53_linear_regression | 10 | 244 | 0.0x |
| 54_const_basic | 5 | 143 | 0.0x |
| 55_async_basic | 5 | 207 | 0.0x |
| 56_async_await | 5 | 171 | 0.0x |
| 57_real_await | 5 | 169 | 0.0x |
| 58_async_file_io | 5 | 158 | 0.0x |
| 58_const_scope | 6 | 176 | 0.0x |
| 59_async_fanout | 7 | 141 | 0.0x |
| 62_list_output | 7 | 171 | 0.0x |
| 63_else_sino | 7 | 188 | 0.0x |
| 64_closure_typed | 8 | 210 | 0.0x |
| 65_list_int_indexing | 6 | 167 | 0.0x |
| 66_qualified_type_ref | 5 | 171 | 0.0x |
| 67_implicit_return_one_liner | 6 | 148 | 0.0x |
| 68_terse_lambda | 8 | 228 | 0.0x |
| 69_list_comp | 10 | 166 | 0.1x |
| 70_list_comp_filter | 6 | 177 | 0.0x |
| 71_map_comp | 6 | 198 | 0.0x |
| 72_string_interp_var | 4 | 156 | 0.0x |
| 73_string_interp_int | 4 | 137 | 0.0x |
| 74_string_interp_float | 5 | 141 | 0.0x |
| 75_string_interp_bool | 4 | 137 | 0.0x |
| 76_string_interp_method | 6 | 230 | 0.0x |
| 77_string_interp_arith | 5 | 194 | 0.0x |
| 78_string_interp_multi | 5 | 144 | 0.0x |
| 79_string_interp_mixed | 5 | 155 | 0.0x |
| 80_string_interp_escaped | 4 | 152 | 0.0x |

