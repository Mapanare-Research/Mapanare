# Mapanare Benchmarks - Linux

Generated: 2026-04-30 18:49 UTC  
Version: 5.17.1 (`784d91a`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 16.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 937 | `____._._ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `      _  v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 5 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         v` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 8 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 6 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 6 | `       _ ^` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `..___.~. v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `         ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 6 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 8 | `  ______ v` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 7 | ` _      ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 7 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `         v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 9 | `         v` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `        ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 7 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `       _ ^` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 9 | `         ^` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 6 | `        ` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 8 | `        ` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 6 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 6 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | ` _   __  v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `________ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | ` _.   __` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 7 | `         v` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 7 | `      _  v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `_.   .*_ v` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `    ___  v` | PASS |
| 45_ffi_bind | 15 | 98 | 2.8 | 2 | 9 | 83 | 5 | `      _  v` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         v` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         v` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | `         v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         v` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         v` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 9 | `___.__._ v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `...__.._ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `      _  v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 7 | `_-......` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `     __  v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `     ___` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 7 | `  __ __  v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `__  . .. ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | ` __  .__` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `______-_ v` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 7 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 7 | ` _ __ _  v` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 9 | `        ` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 7 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 6 | `.~--..~. v` | PASS |
| 67_implicit_return_one_liner | 17 | 106 | 3.6 | 1 | 14 | 75 | 10 | `.. .. *  v` | PASS |
| 68_terse_lambda | 22 | 213 | 7.2 | 1 | 20 | 227 | 10 | ` -_ _ *_ v` | PASS |
| 69_list_comp | 12 | 287 | 11.4 | 1 | 21 | 325 | 6 | `_____._  v` | PASS |
| 70_list_comp_filter | 11 | 303 | 11.9 | 1 | 24 | 334 | 6 | `-_____-* ^` | PASS |
| 71_map_comp | 12 | 156 | 5.5 | 1 | 11 | 148 | 8 | `      *  v` | PASS |
| 72_string_interp_var | 10 | 63 | 2.4 | 1 | 4 | 41 | 5 | `- _ -- * ^` | PASS |
| 73_string_interp_int | 7 | 72 | 2.7 | 1 | 6 | 49 | 5 | `-_     * ^` | PASS |
| 74_string_interp_float | 6 | 72 | 2.7 | 1 | 6 | 49 | 5 | `   _  __` | PASS |
| 75_string_interp_bool | 7 | 73 | 2.7 | 1 | 6 | 42 | 5 | `__ ._ _* ^` | PASS |
| 76_string_interp_method | 8 | 60 | 2.2 | 1 | 4 | 41 | 5 | `__ __ _. ^` | PASS |
| 77_string_interp_arith | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | `    _ _. ^` | PASS |
| 78_string_interp_multi | 9 | 104 | 4.0 | 1 | 10 | 81 | 4 | `   .. .* ^` | PASS |
| 79_string_interp_mixed | 10 | 92 | 3.6 | 1 | 8 | 65 | 4 | `  _  _ * ^` | PASS |
| 80_string_interp_escaped | 8 | 32 | 1.0 | 1 | 2 | 9 | 4 | `*      * ^` | PASS |
| **Total** | **1480** | **14758** | **555.9** | **126** | **1181** | **12684** | **1435** | | **80/80** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 204 | 11.9 | 1 | 134 | YES | PASS |
| 02_arithmetic | 214 | 12.2 | 1 | 197 | YES | PASS |
| 03_function | 236 | 12.9 | 2 | 138 | YES | PASS |
| 04_if_else | 221 | 12.5 | 1 | 120 | YES | PASS |
| 05_for_loop | 237 | 13.1 | 1 | 154 | YES | PASS |
| 06_struct | 217 | 12.4 | 1 | 167 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 158 | YES | PASS |
| 08_list | 243 | 13.7 | 1 | 138 | YES | PASS |
| 09_string_methods | 227 | 13.1 | 1 | 170 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 178 | YES | PASS |
| 11_closure | 227 | 12.6 | 1 | 174 | YES | PASS |
| 12_while | 223 | 12.5 | 1 | 146 | YES | PASS |
| 13_fib | 234 | 12.7 | 2 | 151 | YES | PASS |
| 14_nested_struct | 217 | 12.4 | 1 | 155 | YES | PASS |
| 15_multifunction | 247 | 13.2 | 3 | 168 | YES | PASS |
| 16_string_escape | 223 | 12.9 | 1 | 179 | YES | PASS |
| 17_option | 299 | 15.3 | 2 | 160 | YES | PASS |
| 18_method_chain | 249 | 14.1 | 1 | 162 | YES | PASS |
| 19_nested_match | 272 | 14.2 | 2 | 185 | YES | PASS |
| 20_recursion | 240 | 13.0 | 2 | 197 | YES | PASS |
| 21_list_ops | 325 | 17.1 | 2 | 294 | YES | PASS |
| 22_string_builder | 292 | 15.6 | 2 | 374 | YES | PASS |
| 23_multi_return | 266 | 14.5 | 2 | 311 | YES | PASS |
| 24_enum_methods | 260 | 14.1 | 2 | 208 | YES | PASS |
| 25_fizzbuzz | 304 | 15.3 | 2 | 225 | YES | PASS |
| 26_generics | 284 | 14.5 | 5 | 233 | YES | PASS |
| 27_impl | 244 | 13.3 | 3 | 164 | YES | PASS |
| 28_traits | 252 | 13.5 | 3 | 178 | YES | PASS |
| 29_generic_impl | 253 | 13.7 | 3 | 190 | YES | PASS |
| 30_nested_generics | 244 | 14.1 | 1 | 193 | YES | PASS |
| 31_generic_multi | 269 | 14.6 | 4 | 193 | YES | PASS |
| 32_generic_enum | 215 | 12.3 | 1 | 137 | YES | PASS |
| 33_break_continue | 428 | 19.1 | 5 | 187 | YES | PASS |
| 34_file_io | 299 | 16.9 | 1 | 167 | YES | PASS |
| 35_stdin | 229 | 13.2 | 1 | 135 | YES | PASS |
| 36_crypto | 258 | 14.6 | 1 | 130 | YES | PASS |
| 37_regex | 269 | 15.3 | 1 | 166 | YES | PASS |
| 38_http | 220 | 12.7 | 1 | 215 | YES | PASS |
| 39_gpu_detect | 247 | 13.9 | 1 | 175 | YES | PASS |
| 40_gpu_tensor | 434 | 22.6 | 1 | 163 | YES | PASS |
| 41_module_let | 218 | 12.2 | 2 | 113 | YES | PASS |
| 42_module_let_string | 221 | 12.4 | 2 | 126 | YES | PASS |
| 43_module_let_math | 225 | 12.6 | 2 | 143 | YES | PASS |
| 45_ffi_bind | 253 | 13.2 | 3 | 159 | YES | PASS |
| 47_try_operator | 356 | 17.9 | 4 | 155 | YES | PASS |
| 48_match_nested_exhaustive | 449 | 22.4 | 3 | 167 | YES | PASS |
| 49_match_guards | 276 | 14.8 | 2 | 173 | YES | PASS |
| 49_tensor_literal | 481 | 24.4 | 1 | 166 | YES | PASS |
| 50_match_or_patterns | 294 | 15.8 | 2 | 180 | YES | PASS |
| 50_tensor_indexing | 453 | 23.2 | 1 | 144 | YES | PASS |
| 51_match_guards_and_or | 345 | 17.5 | 2 | 173 | YES | PASS |
| 51_tensor_broadcast | 465 | 23.3 | 1 | 224 | YES | PASS |
| 52_tensor_slicing | 460 | 23.5 | 1 | 152 | YES | PASS |
| 53_linear_regression | 387 | 19.8 | 1 | 184 | YES | PASS |
| 54_const_basic | 224 | 12.8 | 1 | 153 | YES | PASS |
| 55_async_basic | 266 | 14.3 | 2 | 151 | YES | PASS |
| 56_async_await | 345 | 17.2 | 3 | 239 | YES | PASS |
| 57_real_await | 501 | 23.0 | 5 | 196 | YES | PASS |
| 58_async_file_io | 428 | 20.2 | 4 | 158 | YES | PASS |
| 58_const_scope | 257 | 13.7 | 2 | 174 | YES | PASS |
| 59_async_fanout | 1054 | 44.0 | 12 | 159 | YES | PASS |
| 62_list_output | 385 | 20.8 | 3 | 161 | YES | PASS |
| 63_else_sino | 313 | 15.6 | 3 | 205 | YES | PASS |
| 64_closure_typed | 326 | 15.8 | 3 | 251 | YES | PASS |
| 65_list_int_indexing | 403 | 21.1 | 1 | 279 | YES | PASS |
| 66_qualified_type_ref | 240 | 13.3 | 2 | 285 | YES | PASS |
| 67_implicit_return_one_liner | 267 | 13.9 | 4 | 343 | YES | PASS |
| 68_terse_lambda | 316 | 15.4 | 3 | 225 | YES | PASS |
| 69_list_comp | 368 | 19.5 | 1 | 185 | YES | PASS |
| 70_list_comp_filter | 377 | 19.7 | 1 | 188 | YES | PASS |
| 71_map_comp | 265 | 14.4 | 1 | 188 | YES | PASS |
| 72_string_interp_var | 220 | 12.7 | 1 | 170 | YES | PASS |
| 73_string_interp_int | 220 | 12.7 | 1 | 148 | YES | PASS |
| 74_string_interp_float | 220 | 12.7 | 1 | 249 | YES | PASS |
| 75_string_interp_bool | 221 | 12.7 | 1 | 174 | YES | PASS |
| 76_string_interp_method | 219 | 12.6 | 1 | 163 | YES | PASS |
| 77_string_interp_arith | 219 | 12.6 | 1 | 134 | YES | PASS |
| 78_string_interp_multi | 236 | 13.4 | 1 | 130 | YES | PASS |
| 79_string_interp_mixed | 230 | 13.2 | 1 | 133 | YES | PASS |
| 80_string_interp_escaped | 204 | 12.0 | 1 | 123 | YES | PASS |
| **Total** | | | | **14496** | **80/80** | **80/80** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 937 | 134 | 7.0x |
| 02_arithmetic | 7 | 197 | 0.0x |
| 03_function | 5 | 138 | 0.0x |
| 04_if_else | 5 | 120 | 0.0x |
| 05_for_loop | 5 | 154 | 0.0x |
| 06_struct | 6 | 167 | 0.0x |
| 07_enum_match | 12 | 158 | 0.1x |
| 08_list | 6 | 138 | 0.0x |
| 09_string_methods | 5 | 170 | 0.0x |
| 10_result | 8 | 178 | 0.0x |
| 11_closure | 5 | 174 | 0.0x |
| 12_while | 6 | 146 | 0.0x |
| 13_fib | 5 | 151 | 0.0x |
| 14_nested_struct | 5 | 155 | 0.0x |
| 15_multifunction | 5 | 168 | 0.0x |
| 16_string_escape | 6 | 179 | 0.0x |
| 17_option | 6 | 160 | 0.0x |
| 18_method_chain | 5 | 162 | 0.0x |
| 19_nested_match | 7 | 185 | 0.0x |
| 20_recursion | 5 | 197 | 0.0x |
| 21_list_ops | 6 | 294 | 0.0x |
| 22_string_builder | 8 | 374 | 0.0x |
| 23_multi_return | 7 | 311 | 0.0x |
| 24_enum_methods | 7 | 208 | 0.0x |
| 25_fizzbuzz | 5 | 225 | 0.0x |
| 26_generics | 9 | 233 | 0.0x |
| 27_impl | 7 | 164 | 0.0x |
| 28_traits | 6 | 178 | 0.0x |
| 29_generic_impl | 7 | 190 | 0.0x |
| 30_nested_generics | 6 | 193 | 0.0x |
| 31_generic_multi | 9 | 193 | 0.0x |
| 32_generic_enum | 6 | 137 | 0.0x |
| 33_break_continue | 8 | 187 | 0.0x |
| 34_file_io | 6 | 167 | 0.0x |
| 35_stdin | 6 | 135 | 0.0x |
| 36_crypto | 4 | 130 | 0.0x |
| 37_regex | 5 | 166 | 0.0x |
| 38_http | 4 | 215 | 0.0x |
| 39_gpu_detect | 7 | 175 | 0.0x |
| 40_gpu_tensor | 7 | 163 | 0.0x |
| 41_module_let | 5 | 113 | 0.0x |
| 42_module_let_string | 4 | 126 | 0.0x |
| 43_module_let_math | 5 | 143 | 0.0x |
| 45_ffi_bind | 5 | 159 | 0.0x |
| 47_try_operator | 7 | 155 | 0.0x |
| 48_match_nested_exhaustive | 6 | 167 | 0.0x |
| 49_match_guards | 6 | 173 | 0.0x |
| 49_tensor_literal | 10 | 166 | 0.1x |
| 50_match_or_patterns | 6 | 180 | 0.0x |
| 50_tensor_indexing | 8 | 144 | 0.1x |
| 51_match_guards_and_or | 7 | 173 | 0.0x |
| 51_tensor_broadcast | 9 | 224 | 0.0x |
| 52_tensor_slicing | 8 | 152 | 0.1x |
| 53_linear_regression | 6 | 184 | 0.0x |
| 54_const_basic | 7 | 153 | 0.0x |
| 55_async_basic | 5 | 151 | 0.0x |
| 56_async_await | 5 | 239 | 0.0x |
| 57_real_await | 7 | 196 | 0.0x |
| 58_async_file_io | 5 | 158 | 0.0x |
| 58_const_scope | 5 | 174 | 0.0x |
| 59_async_fanout | 7 | 159 | 0.0x |
| 62_list_output | 7 | 161 | 0.0x |
| 63_else_sino | 7 | 205 | 0.0x |
| 64_closure_typed | 9 | 251 | 0.0x |
| 65_list_int_indexing | 7 | 279 | 0.0x |
| 66_qualified_type_ref | 6 | 285 | 0.0x |
| 67_implicit_return_one_liner | 10 | 343 | 0.0x |
| 68_terse_lambda | 10 | 225 | 0.0x |
| 69_list_comp | 6 | 185 | 0.0x |
| 70_list_comp_filter | 6 | 188 | 0.0x |
| 71_map_comp | 8 | 188 | 0.0x |
| 72_string_interp_var | 5 | 170 | 0.0x |
| 73_string_interp_int | 5 | 148 | 0.0x |
| 74_string_interp_float | 5 | 249 | 0.0x |
| 75_string_interp_bool | 5 | 174 | 0.0x |
| 76_string_interp_method | 5 | 163 | 0.0x |
| 77_string_interp_arith | 4 | 134 | 0.0x |
| 78_string_interp_multi | 4 | 130 | 0.0x |
| 79_string_interp_mixed | 4 | 133 | 0.0x |
| 80_string_interp_escaped | 4 | 123 | 0.0x |

