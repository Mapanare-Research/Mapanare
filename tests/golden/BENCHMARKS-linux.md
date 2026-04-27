# Mapanare Benchmarks - Linux

Generated: 2026-04-27 16:25 UTC  
Version: 5.8.4 (`d2188aa`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 10.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 656 | `_  __ __ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `   _    ` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `     _ _ ^` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `-_ ..-.- ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `     _   ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 5 | `        ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `_ __ __. ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `         ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `         v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 6 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 5 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `   _    ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | `         v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `     __  v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 7 | `    ____` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | ` .   ___` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_____..- ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_~ _.--~ ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 6 | `    __ _ ^` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 7 | `_ ___.-* ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 6 | `    .___` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 6 | `      __` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 8 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `      _  v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 6 | `  *     ` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `_____... v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `_____.-. v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `_    ___` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `_._._-~~` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `   ~ _._ v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `   _ _..` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `_    .-. v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `   _ .*. v` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 7 | `.  __.-. v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `   __.-. v` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 7 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `  _ _-..` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | ` ~*      v` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 5 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `_.--.***` | PASS |
| **Total** | **1336** | **13033** | **490.9** | **112** | **1039** | **11069** | **1028** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 193 | 11.2 | 1 | 98 | YES | PASS |
| 02_arithmetic | 203 | 11.5 | 1 | 112 | YES | PASS |
| 03_function | 225 | 12.2 | 2 | 154 | YES | PASS |
| 04_if_else | 210 | 11.8 | 1 | 138 | YES | PASS |
| 05_for_loop | 226 | 12.4 | 1 | 140 | YES | PASS |
| 06_struct | 206 | 11.7 | 1 | 134 | YES | PASS |
| 07_enum_match | 216 | 12.0 | 1 | 126 | YES | PASS |
| 08_list | 230 | 12.9 | 1 | 120 | YES | PASS |
| 09_string_methods | 216 | 12.3 | 1 | 150 | YES | PASS |
| 10_result | 261 | 13.8 | 2 | 152 | YES | PASS |
| 11_closure | 216 | 11.8 | 1 | 124 | YES | PASS |
| 12_while | 212 | 11.7 | 1 | 115 | YES | PASS |
| 13_fib | 223 | 11.9 | 2 | 161 | YES | PASS |
| 14_nested_struct | 206 | 11.7 | 1 | 136 | YES | PASS |
| 15_multifunction | 236 | 12.5 | 3 | 140 | YES | PASS |
| 16_string_escape | 212 | 12.2 | 1 | 120 | YES | PASS |
| 17_option | 288 | 14.6 | 2 | 135 | YES | PASS |
| 18_method_chain | 238 | 13.3 | 1 | 189 | YES | PASS |
| 19_nested_match | 261 | 13.5 | 2 | 164 | YES | PASS |
| 20_recursion | 229 | 12.3 | 2 | 136 | YES | PASS |
| 21_list_ops | 312 | 16.3 | 2 | 147 | YES | PASS |
| 22_string_builder | 281 | 14.8 | 2 | 151 | YES | PASS |
| 23_multi_return | 255 | 13.8 | 2 | 127 | YES | PASS |
| 24_enum_methods | 249 | 13.4 | 2 | 149 | YES | PASS |
| 25_fizzbuzz | 293 | 14.6 | 2 | 149 | YES | PASS |
| 26_generics | 273 | 13.7 | 5 | 126 | YES | PASS |
| 27_impl | 233 | 12.5 | 3 | 162 | YES | PASS |
| 28_traits | 241 | 12.8 | 3 | 153 | YES | PASS |
| 29_generic_impl | 242 | 13.0 | 3 | 128 | YES | PASS |
| 30_nested_generics | 233 | 13.3 | 1 | 106 | YES | PASS |
| 31_generic_multi | 258 | 13.8 | 4 | 152 | YES | PASS |
| 32_generic_enum | 204 | 11.6 | 1 | 154 | YES | PASS |
| 33_break_continue | 415 | 18.2 | 5 | 173 | YES | PASS |
| 34_file_io | 286 | 16.0 | 1 | 136 | YES | PASS |
| 35_stdin | 218 | 12.4 | 1 | 119 | YES | PASS |
| 36_crypto | 247 | 13.9 | 1 | 122 | YES | PASS |
| 37_regex | 258 | 14.5 | 1 | 137 | YES | PASS |
| 38_http | 209 | 12.0 | 1 | 135 | YES | PASS |
| 39_gpu_detect | 236 | 13.2 | 1 | 118 | YES | PASS |
| 40_gpu_tensor | 415 | 21.4 | 1 | 138 | YES | PASS |
| 41_module_let | 207 | 11.5 | 2 | 175 | YES | PASS |
| 42_module_let_string | 210 | 11.7 | 2 | 178 | YES | PASS |
| 43_module_let_math | 214 | 11.9 | 2 | 128 | YES | PASS |
| 45_ffi_bind | 242 | 12.4 | 3 | 153 | YES | PASS |
| 47_try_operator | 345 | 17.2 | 4 | 171 | YES | PASS |
| 48_match_nested_exhaustive | 438 | 21.7 | 3 | 171 | YES | PASS |
| 49_match_guards | 265 | 14.1 | 2 | 161 | YES | PASS |
| 49_tensor_literal | 470 | 23.7 | 1 | 115 | YES | PASS |
| 50_match_or_patterns | 283 | 15.0 | 2 | 128 | YES | PASS |
| 50_tensor_indexing | 442 | 22.5 | 1 | 139 | YES | PASS |
| 51_match_guards_and_or | 334 | 16.8 | 2 | 149 | YES | PASS |
| 51_tensor_broadcast | 454 | 22.6 | 1 | 134 | YES | PASS |
| 52_tensor_slicing | 449 | 22.8 | 1 | 148 | YES | PASS |
| 53_linear_regression | 376 | 19.0 | 1 | 144 | YES | PASS |
| 54_const_basic | 213 | 12.1 | 1 | 111 | YES | PASS |
| 55_async_basic | 255 | 13.6 | 2 | 155 | YES | PASS |
| 56_async_await | 334 | 16.5 | 3 | 136 | YES | PASS |
| 57_real_await | 490 | 22.3 | 5 | 115 | YES | PASS |
| 58_async_file_io | 417 | 19.5 | 4 | 181 | YES | PASS |
| 58_const_scope | 246 | 13.0 | 2 | 159 | YES | PASS |
| 59_async_fanout | 1043 | 43.3 | 12 | 137 | YES | PASS |
| 62_list_output | 372 | 19.9 | 3 | 158 | YES | PASS |
| 63_else_sino | 302 | 14.9 | 3 | 130 | YES | PASS |
| 64_closure_typed | 315 | 15.1 | 3 | 133 | YES | PASS |
| 65_list_int_indexing | 390 | 20.2 | 1 | 154 | YES | PASS |
| 66_qualified_type_ref | 229 | 12.6 | 2 | 140 | YES | PASS |
| **Total** | | | | **9329** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 656 | 98 | 6.7x |
| 02_arithmetic | 6 | 112 | 0.1x |
| 03_function | 6 | 154 | 0.0x |
| 04_if_else | 6 | 138 | 0.0x |
| 05_for_loop | 5 | 140 | 0.0x |
| 06_struct | 5 | 134 | 0.0x |
| 07_enum_match | 13 | 126 | 0.1x |
| 08_list | 6 | 120 | 0.0x |
| 09_string_methods | 4 | 150 | 0.0x |
| 10_result | 6 | 152 | 0.0x |
| 11_closure | 4 | 124 | 0.0x |
| 12_while | 4 | 115 | 0.0x |
| 13_fib | 4 | 161 | 0.0x |
| 14_nested_struct | 5 | 136 | 0.0x |
| 15_multifunction | 5 | 140 | 0.0x |
| 16_string_escape | 5 | 120 | 0.0x |
| 17_option | 6 | 135 | 0.0x |
| 18_method_chain | 4 | 189 | 0.0x |
| 19_nested_match | 7 | 164 | 0.0x |
| 20_recursion | 4 | 136 | 0.0x |
| 21_list_ops | 5 | 147 | 0.0x |
| 22_string_builder | 5 | 151 | 0.0x |
| 23_multi_return | 5 | 127 | 0.0x |
| 24_enum_methods | 5 | 149 | 0.0x |
| 25_fizzbuzz | 6 | 149 | 0.0x |
| 26_generics | 6 | 126 | 0.0x |
| 27_impl | 5 | 162 | 0.0x |
| 28_traits | 5 | 153 | 0.0x |
| 29_generic_impl | 6 | 128 | 0.0x |
| 30_nested_generics | 5 | 106 | 0.0x |
| 31_generic_multi | 7 | 152 | 0.0x |
| 32_generic_enum | 7 | 154 | 0.0x |
| 33_break_continue | 8 | 173 | 0.0x |
| 34_file_io | 5 | 136 | 0.0x |
| 35_stdin | 4 | 119 | 0.0x |
| 36_crypto | 4 | 122 | 0.0x |
| 37_regex | 5 | 137 | 0.0x |
| 38_http | 4 | 135 | 0.0x |
| 39_gpu_detect | 4 | 118 | 0.0x |
| 40_gpu_tensor | 6 | 138 | 0.0x |
| 41_module_let | 5 | 175 | 0.0x |
| 42_module_let_string | 7 | 178 | 0.0x |
| 43_module_let_math | 6 | 128 | 0.0x |
| 45_ffi_bind | 6 | 153 | 0.0x |
| 47_try_operator | 7 | 171 | 0.0x |
| 48_match_nested_exhaustive | 8 | 171 | 0.0x |
| 49_match_guards | 6 | 161 | 0.0x |
| 49_tensor_literal | 10 | 115 | 0.1x |
| 50_match_or_patterns | 5 | 128 | 0.0x |
| 50_tensor_indexing | 7 | 139 | 0.1x |
| 51_match_guards_and_or | 6 | 149 | 0.0x |
| 51_tensor_broadcast | 8 | 134 | 0.1x |
| 52_tensor_slicing | 7 | 148 | 0.0x |
| 53_linear_regression | 6 | 144 | 0.0x |
| 54_const_basic | 4 | 111 | 0.0x |
| 55_async_basic | 5 | 155 | 0.0x |
| 56_async_await | 5 | 136 | 0.0x |
| 57_real_await | 5 | 115 | 0.0x |
| 58_async_file_io | 5 | 181 | 0.0x |
| 58_const_scope | 7 | 159 | 0.0x |
| 59_async_fanout | 7 | 137 | 0.0x |
| 62_list_output | 7 | 158 | 0.0x |
| 63_else_sino | 6 | 130 | 0.0x |
| 64_closure_typed | 7 | 133 | 0.1x |
| 65_list_int_indexing | 5 | 154 | 0.0x |
| 66_qualified_type_ref | 5 | 140 | 0.0x |

