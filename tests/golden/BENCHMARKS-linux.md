# Mapanare Benchmarks - Linux

Generated: 2026-04-23 19:28 UTC  
Version: 5.4.3 (`6bfb595`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 7.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 616 | ` _    _  v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 10 | `         ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `       _ ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 10 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 7 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `         v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 5 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `_       ` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 6 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 7 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `    _  _ ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 7 | `        ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 9 | `         v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `         v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 6 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 8 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `       _ ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `       _ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `_  _    ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 13 | `         v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `___.____` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `         v` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `         v` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `        ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 9 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `        ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `    _   ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `__  _  _ ^` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `_._____. ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `    .  _ ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `___..-_. ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `         ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | `       _ ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `       _ ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `       _ ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `        ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `_     __` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 6 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 7 | `        ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `         v` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 5 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `-_.____. ^` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **988** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 129 | 7.6 | 1 | 174 | YES | PASS |
| 02_arithmetic | 139 | 7.9 | 1 | 182 | YES | PASS |
| 03_function | 161 | 8.5 | 2 | 167 | YES | PASS |
| 04_if_else | 146 | 8.1 | 1 | 99 | YES | PASS |
| 05_for_loop | 162 | 8.7 | 1 | 90 | YES | PASS |
| 06_struct | 144 | 8.1 | 1 | 82 | YES | PASS |
| 07_enum_match | 152 | 8.4 | 1 | 84 | YES | PASS |
| 08_list | 168 | 9.2 | 1 | 112 | YES | PASS |
| 09_string_methods | 152 | 8.7 | 1 | 106 | YES | PASS |
| 10_result | 197 | 10.2 | 2 | 131 | YES | PASS |
| 11_closure | 164 | 8.6 | 1 | 78 | YES | PASS |
| 12_while | 148 | 8.1 | 1 | 80 | YES | PASS |
| 13_fib | 159 | 8.3 | 2 | 88 | YES | PASS |
| 14_nested_struct | 144 | 8.1 | 1 | 90 | YES | PASS |
| 15_multifunction | 172 | 8.8 | 3 | 104 | YES | PASS |
| 16_string_escape | 148 | 8.5 | 1 | 96 | YES | PASS |
| 17_option | 224 | 10.9 | 2 | 112 | YES | PASS |
| 18_method_chain | 174 | 9.7 | 1 | 92 | YES | PASS |
| 19_nested_match | 197 | 9.8 | 2 | 131 | YES | PASS |
| 20_recursion | 165 | 8.6 | 2 | 141 | YES | PASS |
| 21_list_ops | 247 | 12.5 | 2 | 116 | YES | PASS |
| 22_string_builder | 211 | 10.9 | 2 | 115 | YES | PASS |
| 23_multi_return | 193 | 10.2 | 2 | 93 | YES | PASS |
| 24_enum_methods | 185 | 9.7 | 2 | 93 | YES | PASS |
| 25_fizzbuzz | 223 | 10.7 | 2 | 86 | YES | PASS |
| 26_generics | 209 | 10.1 | 5 | 104 | YES | PASS |
| 27_impl | 171 | 9.0 | 3 | 114 | YES | PASS |
| 28_traits | 179 | 9.2 | 3 | 178 | YES | PASS |
| 29_generic_impl | 178 | 9.3 | 3 | 132 | YES | PASS |
| 30_nested_generics | 169 | 9.7 | 1 | 88 | YES | PASS |
| 31_generic_multi | 194 | 10.2 | 4 | 89 | YES | PASS |
| 32_generic_enum | 140 | 7.9 | 1 | 91 | YES | PASS |
| 33_break_continue | 350 | 14.4 | 5 | 125 | YES | PASS |
| 34_file_io | 222 | 12.4 | 1 | 113 | YES | PASS |
| 35_stdin | 154 | 8.8 | 1 | 100 | YES | PASS |
| 36_crypto | 183 | 10.2 | 1 | 92 | YES | PASS |
| 37_regex | 194 | 10.9 | 1 | 134 | YES | PASS |
| 38_http | 145 | 8.3 | 1 | 114 | YES | PASS |
| 39_gpu_detect | 172 | 9.5 | 1 | 225 | YES | PASS |
| 40_gpu_tensor | 343 | 17.3 | 1 | 158 | YES | PASS |
| 41_module_let | 143 | 7.9 | 2 | 95 | YES | PASS |
| 42_module_let_string | 146 | 8.1 | 2 | 77 | YES | PASS |
| 43_module_let_math | 150 | 8.2 | 2 | 77 | YES | PASS |
| 45_ffi_bind | 178 | 8.8 | 3 | 87 | YES | PASS |
| 47_try_operator | 281 | 13.6 | 4 | 129 | YES | PASS |
| 48_match_nested_exhaustive | 326 | 15.8 | 3 | 122 | YES | PASS |
| 49_match_guards | 201 | 10.5 | 2 | 94 | YES | PASS |
| 49_tensor_literal | 0 | 0.0 | 0 | 25 | - | FAIL |
| 50_match_or_patterns | 218 | 11.3 | 2 | 104 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 22 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 25 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 25 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 23 | - | FAIL |
| 54_const_basic | 149 | 8.4 | 1 | 79 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 27 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 29 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 26 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 26 | - | FAIL |
| 58_const_scope | 182 | 9.3 | 2 | 92 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 28 | - | FAIL |
| 62_list_output | 311 | 16.3 | 3 | 128 | YES | PASS |
| 63_else_sino | 238 | 11.3 | 3 | 106 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 29 | - | FAIL |
| 65_list_int_indexing | 310 | 15.7 | 1 | 98 | YES | PASS |
| 66_qualified_type_ref | 169 | 9.1 | 2 | 95 | YES | PASS |
| **Total** | | | | **6265** | **54/66** | **54/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 616 | 174 | 3.5x |
| 02_arithmetic | 10 | 182 | 0.1x |
| 03_function | 8 | 167 | 0.0x |
| 04_if_else | 6 | 99 | 0.1x |
| 05_for_loop | 5 | 90 | 0.1x |
| 06_struct | 5 | 82 | 0.1x |
| 07_enum_match | 10 | 84 | 0.1x |
| 08_list | 6 | 112 | 0.1x |
| 09_string_methods | 5 | 106 | 0.0x |
| 10_result | 7 | 131 | 0.1x |
| 11_closure | 4 | 78 | 0.0x |
| 12_while | 4 | 80 | 0.1x |
| 13_fib | 4 | 88 | 0.0x |
| 14_nested_struct | 4 | 90 | 0.0x |
| 15_multifunction | 5 | 104 | 0.0x |
| 16_string_escape | 4 | 96 | 0.0x |
| 17_option | 5 | 112 | 0.0x |
| 18_method_chain | 4 | 92 | 0.0x |
| 19_nested_match | 6 | 131 | 0.0x |
| 20_recursion | 6 | 141 | 0.0x |
| 21_list_ops | 7 | 116 | 0.1x |
| 22_string_builder | 6 | 115 | 0.0x |
| 23_multi_return | 5 | 93 | 0.1x |
| 24_enum_methods | 5 | 93 | 0.1x |
| 25_fizzbuzz | 5 | 86 | 0.1x |
| 26_generics | 7 | 104 | 0.1x |
| 27_impl | 6 | 114 | 0.1x |
| 28_traits | 7 | 178 | 0.0x |
| 29_generic_impl | 9 | 132 | 0.1x |
| 30_nested_generics | 5 | 88 | 0.1x |
| 31_generic_multi | 6 | 89 | 0.1x |
| 32_generic_enum | 4 | 91 | 0.0x |
| 33_break_continue | 8 | 125 | 0.1x |
| 34_file_io | 5 | 113 | 0.0x |
| 35_stdin | 4 | 100 | 0.0x |
| 36_crypto | 4 | 92 | 0.0x |
| 37_regex | 5 | 134 | 0.0x |
| 38_http | 5 | 114 | 0.0x |
| 39_gpu_detect | 5 | 225 | 0.0x |
| 40_gpu_tensor | 13 | 158 | 0.1x |
| 41_module_let | 5 | 95 | 0.1x |
| 42_module_let_string | 4 | 77 | 0.1x |
| 43_module_let_math | 4 | 77 | 0.1x |
| 45_ffi_bind | 5 | 87 | 0.1x |
| 47_try_operator | 8 | 129 | 0.1x |
| 48_match_nested_exhaustive | 7 | 122 | 0.1x |
| 49_match_guards | 6 | 94 | 0.1x |
| 50_match_or_patterns | 5 | 104 | 0.0x |
| 54_const_basic | 4 | 79 | 0.0x |
| 58_const_scope | 5 | 92 | 0.1x |
| 62_list_output | 6 | 128 | 0.0x |
| 63_else_sino | 7 | 106 | 0.1x |
| 65_list_int_indexing | 5 | 98 | 0.0x |
| 66_qualified_type_ref | 5 | 95 | 0.1x |

