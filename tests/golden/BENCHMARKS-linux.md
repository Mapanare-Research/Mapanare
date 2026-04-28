# Mapanare Benchmarks - Linux

Generated: 2026-04-28 06:48 UTC  
Version: 5.10.0 (`26f566e`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 12.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 690 | ` ___ __  v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `         v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 12 | `         v` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 7 | `         v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 9 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `__  _.._ v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `        ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 7 | `        ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `_  __ _  v` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 6 | `         ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 7 | `         ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 7 | `         v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 7 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `         v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         ^` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         v` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 6 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `        ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` ______  v` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `    _ _  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 7 | `       _ ^` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 6 | ` __  _._ v` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 7 | `        ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.8 | 2 | 9 | 83 | 6 | `         v` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | `        ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `        ` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 8 | `        ` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `________` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `_____.__` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `      _  v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `_._-_._. ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 6 | ` _   _  ` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `         v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `  _ _   ` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `        ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `        ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | ` _ . _  ` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 8 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | ` ____   ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `        ` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 7 | `         v` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 6 | `.._.-_..` | PASS |
| **Total** | **1336** | **13053** | **492.4** | **112** | **1039** | **11149** | **1090** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 202 | 11.8 | 1 | 139 | YES | PASS |
| 02_arithmetic | 212 | 12.1 | 1 | 137 | YES | PASS |
| 03_function | 234 | 12.8 | 2 | 195 | YES | PASS |
| 04_if_else | 219 | 12.4 | 1 | 157 | YES | PASS |
| 05_for_loop | 235 | 13.0 | 1 | 136 | YES | PASS |
| 06_struct | 215 | 12.3 | 1 | 117 | YES | PASS |
| 07_enum_match | 225 | 12.6 | 1 | 161 | YES | PASS |
| 08_list | 241 | 13.6 | 1 | 184 | YES | PASS |
| 09_string_methods | 225 | 12.9 | 1 | 151 | YES | PASS |
| 10_result | 270 | 14.4 | 2 | 166 | YES | PASS |
| 11_closure | 225 | 12.5 | 1 | 145 | YES | PASS |
| 12_while | 221 | 12.3 | 1 | 136 | YES | PASS |
| 13_fib | 232 | 12.6 | 2 | 163 | YES | PASS |
| 14_nested_struct | 215 | 12.3 | 1 | 133 | YES | PASS |
| 15_multifunction | 245 | 13.1 | 3 | 167 | YES | PASS |
| 16_string_escape | 221 | 12.8 | 1 | 265 | YES | PASS |
| 17_option | 297 | 15.2 | 2 | 230 | YES | PASS |
| 18_method_chain | 247 | 13.9 | 1 | 149 | YES | PASS |
| 19_nested_match | 270 | 14.1 | 2 | 192 | YES | PASS |
| 20_recursion | 238 | 12.9 | 2 | 165 | YES | PASS |
| 21_list_ops | 323 | 17.0 | 2 | 189 | YES | PASS |
| 22_string_builder | 290 | 15.4 | 2 | 173 | YES | PASS |
| 23_multi_return | 264 | 14.4 | 2 | 137 | YES | PASS |
| 24_enum_methods | 258 | 14.0 | 2 | 174 | YES | PASS |
| 25_fizzbuzz | 302 | 15.2 | 2 | 184 | YES | PASS |
| 26_generics | 282 | 14.3 | 5 | 170 | YES | PASS |
| 27_impl | 242 | 13.2 | 3 | 178 | YES | PASS |
| 28_traits | 250 | 13.4 | 3 | 210 | YES | PASS |
| 29_generic_impl | 251 | 13.6 | 3 | 174 | YES | PASS |
| 30_nested_generics | 242 | 13.9 | 1 | 145 | YES | PASS |
| 31_generic_multi | 267 | 14.4 | 4 | 136 | YES | PASS |
| 32_generic_enum | 213 | 12.2 | 1 | 126 | YES | PASS |
| 33_break_continue | 426 | 19.0 | 5 | 193 | YES | PASS |
| 34_file_io | 297 | 16.7 | 1 | 148 | YES | PASS |
| 35_stdin | 227 | 13.0 | 1 | 124 | YES | PASS |
| 36_crypto | 256 | 14.5 | 1 | 128 | YES | PASS |
| 37_regex | 267 | 15.1 | 1 | 138 | YES | PASS |
| 38_http | 218 | 12.6 | 1 | 137 | YES | PASS |
| 39_gpu_detect | 245 | 13.8 | 1 | 155 | YES | PASS |
| 40_gpu_tensor | 432 | 22.5 | 1 | 178 | YES | PASS |
| 41_module_let | 216 | 12.1 | 2 | 111 | YES | PASS |
| 42_module_let_string | 219 | 12.3 | 2 | 210 | YES | PASS |
| 43_module_let_math | 223 | 12.5 | 2 | 170 | YES | PASS |
| 45_ffi_bind | 251 | 13.0 | 3 | 149 | YES | PASS |
| 47_try_operator | 354 | 17.8 | 4 | 149 | YES | PASS |
| 48_match_nested_exhaustive | 447 | 22.3 | 3 | 165 | YES | PASS |
| 49_match_guards | 274 | 14.7 | 2 | 153 | YES | PASS |
| 49_tensor_literal | 479 | 24.3 | 1 | 150 | YES | PASS |
| 50_match_or_patterns | 292 | 15.7 | 2 | 161 | YES | PASS |
| 50_tensor_indexing | 451 | 23.1 | 1 | 130 | YES | PASS |
| 51_match_guards_and_or | 343 | 17.4 | 2 | 168 | YES | PASS |
| 51_tensor_broadcast | 463 | 23.2 | 1 | 169 | YES | PASS |
| 52_tensor_slicing | 458 | 23.4 | 1 | 145 | YES | PASS |
| 53_linear_regression | 385 | 19.7 | 1 | 172 | YES | PASS |
| 54_const_basic | 222 | 12.7 | 1 | 150 | YES | PASS |
| 55_async_basic | 264 | 14.2 | 2 | 155 | YES | PASS |
| 56_async_await | 343 | 17.1 | 3 | 152 | YES | PASS |
| 57_real_await | 499 | 22.9 | 5 | 154 | YES | PASS |
| 58_async_file_io | 426 | 20.1 | 4 | 135 | YES | PASS |
| 58_const_scope | 255 | 13.6 | 2 | 141 | YES | PASS |
| 59_async_fanout | 1052 | 43.9 | 12 | 175 | YES | PASS |
| 62_list_output | 383 | 20.6 | 3 | 162 | YES | PASS |
| 63_else_sino | 311 | 15.5 | 3 | 136 | YES | PASS |
| 64_closure_typed | 324 | 15.7 | 3 | 164 | YES | PASS |
| 65_list_int_indexing | 401 | 21.0 | 1 | 161 | YES | PASS |
| 66_qualified_type_ref | 238 | 13.2 | 2 | 156 | YES | PASS |
| **Total** | | | | **10528** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 690 | 139 | 5.0x |
| 02_arithmetic | 7 | 137 | 0.1x |
| 03_function | 6 | 195 | 0.0x |
| 04_if_else | 5 | 157 | 0.0x |
| 05_for_loop | 6 | 136 | 0.0x |
| 06_struct | 6 | 117 | 0.0x |
| 07_enum_match | 12 | 161 | 0.1x |
| 08_list | 7 | 184 | 0.0x |
| 09_string_methods | 5 | 151 | 0.0x |
| 10_result | 6 | 166 | 0.0x |
| 11_closure | 5 | 145 | 0.0x |
| 12_while | 4 | 136 | 0.0x |
| 13_fib | 6 | 163 | 0.0x |
| 14_nested_struct | 5 | 133 | 0.0x |
| 15_multifunction | 6 | 167 | 0.0x |
| 16_string_escape | 7 | 265 | 0.0x |
| 17_option | 9 | 230 | 0.0x |
| 18_method_chain | 4 | 149 | 0.0x |
| 19_nested_match | 6 | 192 | 0.0x |
| 20_recursion | 5 | 165 | 0.0x |
| 21_list_ops | 7 | 189 | 0.0x |
| 22_string_builder | 6 | 173 | 0.0x |
| 23_multi_return | 6 | 137 | 0.0x |
| 24_enum_methods | 6 | 174 | 0.0x |
| 25_fizzbuzz | 7 | 184 | 0.0x |
| 26_generics | 7 | 170 | 0.0x |
| 27_impl | 7 | 178 | 0.0x |
| 28_traits | 7 | 210 | 0.0x |
| 29_generic_impl | 7 | 174 | 0.0x |
| 30_nested_generics | 5 | 145 | 0.0x |
| 31_generic_multi | 7 | 136 | 0.0x |
| 32_generic_enum | 4 | 126 | 0.0x |
| 33_break_continue | 9 | 193 | 0.0x |
| 34_file_io | 6 | 148 | 0.0x |
| 35_stdin | 4 | 124 | 0.0x |
| 36_crypto | 5 | 128 | 0.0x |
| 37_regex | 5 | 138 | 0.0x |
| 38_http | 4 | 137 | 0.0x |
| 39_gpu_detect | 5 | 155 | 0.0x |
| 40_gpu_tensor | 7 | 178 | 0.0x |
| 41_module_let | 4 | 111 | 0.0x |
| 42_module_let_string | 6 | 210 | 0.0x |
| 43_module_let_math | 7 | 170 | 0.0x |
| 45_ffi_bind | 6 | 149 | 0.0x |
| 47_try_operator | 7 | 149 | 0.0x |
| 48_match_nested_exhaustive | 6 | 165 | 0.0x |
| 49_match_guards | 6 | 153 | 0.0x |
| 49_tensor_literal | 11 | 150 | 0.1x |
| 50_match_or_patterns | 6 | 161 | 0.0x |
| 50_tensor_indexing | 7 | 130 | 0.1x |
| 51_match_guards_and_or | 8 | 168 | 0.0x |
| 51_tensor_broadcast | 7 | 169 | 0.0x |
| 52_tensor_slicing | 8 | 145 | 0.1x |
| 53_linear_regression | 6 | 172 | 0.0x |
| 54_const_basic | 5 | 150 | 0.0x |
| 55_async_basic | 6 | 155 | 0.0x |
| 56_async_await | 5 | 152 | 0.0x |
| 57_real_await | 6 | 154 | 0.0x |
| 58_async_file_io | 5 | 135 | 0.0x |
| 58_const_scope | 5 | 141 | 0.0x |
| 59_async_fanout | 6 | 175 | 0.0x |
| 62_list_output | 8 | 162 | 0.1x |
| 63_else_sino | 6 | 136 | 0.0x |
| 64_closure_typed | 7 | 164 | 0.0x |
| 65_list_int_indexing | 7 | 161 | 0.0x |
| 66_qualified_type_ref | 6 | 156 | 0.0x |

