# Mapanare Benchmarks - Linux

Generated: 2026-04-24 06:58 UTC  
Version: 5.6.0 (`d5bed19`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 8.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 629 | `___    _ ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `       _ ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 6 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `    _    v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 5 | `        ` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `  -.   _ ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `        ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 5 | `        ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `_  ___  ` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `         ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 6 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `         ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 7 | `         ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `_        ^` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         v` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 10 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `  _    _ ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `_       ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `.     _  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `         v` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 6 | `        ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `_.._____` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | ` _       v` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 6 | `         v` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 5 | `        ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 9 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `        ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `        ` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 5 | `   _  _  v` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 9 | `_ _.  _  v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `________ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `        ` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `__-__._- ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `      _  v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `         v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `_    _  ` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 4 | `.   _   ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `.       ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `_  _ _  ` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 6 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | ` _   .  ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `         ^` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 5 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 4 | `_._._.._ v` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **989** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 156 | 8.9 | 1 | 94 | YES | PASS |
| 02_arithmetic | 166 | 9.2 | 1 | 104 | YES | PASS |
| 03_function | 188 | 9.8 | 2 | 100 | YES | PASS |
| 04_if_else | 173 | 9.5 | 1 | 91 | YES | PASS |
| 05_for_loop | 189 | 10.0 | 1 | 102 | YES | PASS |
| 06_struct | 171 | 9.4 | 1 | 104 | YES | PASS |
| 07_enum_match | 179 | 9.7 | 1 | 141 | YES | PASS |
| 08_list | 195 | 10.6 | 1 | 116 | YES | PASS |
| 09_string_methods | 179 | 10.0 | 1 | 106 | YES | PASS |
| 10_result | 224 | 11.5 | 2 | 106 | YES | PASS |
| 11_closure | 191 | 9.9 | 1 | 93 | YES | PASS |
| 12_while | 175 | 9.4 | 1 | 108 | YES | PASS |
| 13_fib | 186 | 9.6 | 2 | 132 | YES | PASS |
| 14_nested_struct | 171 | 9.4 | 1 | 120 | YES | PASS |
| 15_multifunction | 199 | 10.2 | 3 | 162 | YES | PASS |
| 16_string_escape | 175 | 9.8 | 1 | 88 | YES | PASS |
| 17_option | 251 | 12.2 | 2 | 112 | YES | PASS |
| 18_method_chain | 201 | 11.0 | 1 | 116 | YES | PASS |
| 19_nested_match | 224 | 11.2 | 2 | 135 | YES | PASS |
| 20_recursion | 192 | 9.9 | 2 | 137 | YES | PASS |
| 21_list_ops | 274 | 13.8 | 2 | 118 | YES | PASS |
| 22_string_builder | 244 | 12.5 | 2 | 117 | YES | PASS |
| 23_multi_return | 220 | 11.5 | 2 | 99 | YES | PASS |
| 24_enum_methods | 212 | 11.0 | 2 | 133 | YES | PASS |
| 25_fizzbuzz | 256 | 12.3 | 2 | 138 | YES | PASS |
| 26_generics | 236 | 11.4 | 5 | 120 | YES | PASS |
| 27_impl | 198 | 10.3 | 3 | 103 | YES | PASS |
| 28_traits | 206 | 10.5 | 3 | 109 | YES | PASS |
| 29_generic_impl | 205 | 10.7 | 3 | 129 | YES | PASS |
| 30_nested_generics | 196 | 11.0 | 1 | 117 | YES | PASS |
| 31_generic_multi | 221 | 11.5 | 4 | 120 | YES | PASS |
| 32_generic_enum | 167 | 9.3 | 1 | 132 | YES | PASS |
| 33_break_continue | 377 | 15.7 | 5 | 135 | YES | PASS |
| 34_file_io | 249 | 13.7 | 1 | 99 | YES | PASS |
| 35_stdin | 181 | 10.1 | 1 | 111 | YES | PASS |
| 36_crypto | 210 | 11.5 | 1 | 107 | YES | PASS |
| 37_regex | 221 | 12.2 | 1 | 106 | YES | PASS |
| 38_http | 172 | 9.7 | 1 | 95 | YES | PASS |
| 39_gpu_detect | 199 | 10.9 | 1 | 97 | YES | PASS |
| 40_gpu_tensor | 370 | 18.6 | 1 | 103 | YES | PASS |
| 41_module_let | 170 | 9.2 | 2 | 98 | YES | PASS |
| 42_module_let_string | 173 | 9.4 | 2 | 99 | YES | PASS |
| 43_module_let_math | 177 | 9.6 | 2 | 100 | YES | PASS |
| 45_ffi_bind | 205 | 10.1 | 3 | 109 | YES | PASS |
| 47_try_operator | 308 | 14.9 | 4 | 111 | YES | PASS |
| 48_match_nested_exhaustive | 401 | 19.3 | 3 | 113 | YES | PASS |
| 49_match_guards | 228 | 11.8 | 2 | 125 | YES | PASS |
| 49_tensor_literal | 408 | 20.4 | 1 | 115 | YES | PASS |
| 50_match_or_patterns | 245 | 12.6 | 2 | 113 | YES | PASS |
| 50_tensor_indexing | 544 | 25.7 | 1 | 108 | YES | PASS |
| 51_tensor_broadcast | 362 | 17.8 | 1 | 124 | YES | PASS |
| 52_tensor_slicing | 0 | 0.0 | 0 | 28 | - | FAIL |
| 53_linear_regression | 301 | 15.0 | 1 | 122 | YES | PASS |
| 54_const_basic | 176 | 9.8 | 1 | 91 | YES | PASS |
| 55_async_basic | 218 | 11.3 | 2 | 110 | YES | PASS |
| 56_async_await | 297 | 14.2 | 3 | 101 | YES | PASS |
| 57_real_await | 453 | 19.9 | 5 | 100 | YES | PASS |
| 58_async_file_io | 380 | 17.2 | 4 | 113 | YES | PASS |
| 58_const_scope | 209 | 10.7 | 2 | 118 | YES | PASS |
| 59_async_fanout | 1006 | 40.9 | 12 | 116 | YES | PASS |
| 62_list_output | 338 | 17.6 | 3 | 118 | YES | PASS |
| 63_else_sino | 265 | 12.6 | 3 | 100 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 26 | - | FAIL |
| 65_list_int_indexing | 337 | 17.0 | 1 | 103 | YES | PASS |
| 66_qualified_type_ref | 196 | 10.4 | 2 | 112 | YES | PASS |
| **Total** | | | | **7129** | **63/66** | **63/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 629 | 94 | 6.7x |
| 02_arithmetic | 6 | 104 | 0.1x |
| 03_function | 6 | 100 | 0.1x |
| 04_if_else | 5 | 91 | 0.0x |
| 05_for_loop | 6 | 102 | 0.1x |
| 06_struct | 5 | 104 | 0.1x |
| 07_enum_match | 11 | 141 | 0.1x |
| 08_list | 6 | 116 | 0.0x |
| 09_string_methods | 6 | 106 | 0.1x |
| 10_result | 6 | 106 | 0.1x |
| 11_closure | 4 | 93 | 0.0x |
| 12_while | 5 | 108 | 0.0x |
| 13_fib | 6 | 132 | 0.0x |
| 14_nested_struct | 4 | 120 | 0.0x |
| 15_multifunction | 6 | 162 | 0.0x |
| 16_string_escape | 4 | 88 | 0.0x |
| 17_option | 5 | 112 | 0.0x |
| 18_method_chain | 4 | 116 | 0.0x |
| 19_nested_match | 6 | 135 | 0.0x |
| 20_recursion | 5 | 137 | 0.0x |
| 21_list_ops | 5 | 118 | 0.0x |
| 22_string_builder | 5 | 117 | 0.0x |
| 23_multi_return | 5 | 99 | 0.0x |
| 24_enum_methods | 5 | 133 | 0.0x |
| 25_fizzbuzz | 5 | 138 | 0.0x |
| 26_generics | 6 | 120 | 0.1x |
| 27_impl | 6 | 103 | 0.1x |
| 28_traits | 5 | 109 | 0.0x |
| 29_generic_impl | 7 | 129 | 0.1x |
| 30_nested_generics | 5 | 117 | 0.0x |
| 31_generic_multi | 7 | 120 | 0.1x |
| 32_generic_enum | 4 | 132 | 0.0x |
| 33_break_continue | 10 | 135 | 0.1x |
| 34_file_io | 5 | 99 | 0.0x |
| 35_stdin | 4 | 111 | 0.0x |
| 36_crypto | 4 | 107 | 0.0x |
| 37_regex | 4 | 106 | 0.0x |
| 38_http | 4 | 95 | 0.0x |
| 39_gpu_detect | 4 | 97 | 0.0x |
| 40_gpu_tensor | 6 | 103 | 0.1x |
| 41_module_let | 4 | 98 | 0.0x |
| 42_module_let_string | 4 | 99 | 0.0x |
| 43_module_let_math | 5 | 100 | 0.0x |
| 45_ffi_bind | 5 | 109 | 0.0x |
| 47_try_operator | 7 | 111 | 0.1x |
| 48_match_nested_exhaustive | 6 | 113 | 0.1x |
| 49_match_guards | 5 | 125 | 0.0x |
| 49_tensor_literal | 9 | 115 | 0.1x |
| 50_match_or_patterns | 5 | 113 | 0.0x |
| 50_tensor_indexing | 7 | 108 | 0.1x |
| 51_tensor_broadcast | 9 | 124 | 0.1x |
| 53_linear_regression | 6 | 122 | 0.0x |
| 54_const_basic | 5 | 91 | 0.1x |
| 55_async_basic | 4 | 110 | 0.0x |
| 56_async_await | 5 | 101 | 0.0x |
| 57_real_await | 6 | 100 | 0.1x |
| 58_async_file_io | 4 | 113 | 0.0x |
| 58_const_scope | 5 | 118 | 0.0x |
| 59_async_fanout | 6 | 116 | 0.1x |
| 62_list_output | 6 | 118 | 0.1x |
| 63_else_sino | 6 | 100 | 0.1x |
| 65_list_int_indexing | 5 | 103 | 0.0x |
| 66_qualified_type_ref | 4 | 112 | 0.0x |

