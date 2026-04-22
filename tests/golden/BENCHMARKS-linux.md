# Mapanare Benchmarks - Linux

Generated: 2026-04-22 03:14 UTC  
Version: 5.0.6 (`0d97cc1`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 7.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 772 | `__  ____ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 10 | `    _    v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 6 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 8 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `        ` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `        ` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `-*.._._- ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 8 | `       _ ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 6 | ` .  _._  v` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `________` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `_ __ ___ v` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 9 | `         v` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 7 | `___ _  _ ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 6 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `___  ___ v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | `  _      v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `_~._.___` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         ^` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `       _ ^` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 9 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | ` __ _   ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `__  -*__` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `_   ._  ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 6 | `.   __  ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 6 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 8 | `__   _  ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 7 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `.*__..._ v` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 8 | `_-  __  ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 7 | `_.   __  v` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 8 | `         v` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | ` _   _..` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `-.*_..._ v` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | `__* _._  v` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 10 | `_ -  _._ v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `__-___._ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `  _   _  v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `-.-.-_--` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `_    . . ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `_    .__ v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `_ _ _. _ ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `..   ~ _ ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `..*_.-_- ^` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `__~ .. _ ^` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 7 | `         ^` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `     ~  ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `_._ _.__` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 6 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 7 | `._._....` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **1185** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 126 | 7.4 | 1 | 150 | YES | PASS |
| 02_arithmetic | 131 | 7.5 | 1 | 172 | YES | PASS |
| 03_function | 141 | 7.7 | 2 | 138 | YES | PASS |
| 04_if_else | 143 | 8.0 | 1 | 117 | YES | PASS |
| 05_for_loop | 154 | 8.3 | 1 | 111 | YES | PASS |
| 06_struct | 136 | 7.7 | 1 | 77 | YES | PASS |
| 07_enum_match | 149 | 8.2 | 1 | 87 | YES | PASS |
| 08_list | 158 | 8.7 | 1 | 98 | YES | PASS |
| 09_string_methods | 139 | 8.1 | 1 | 114 | YES | PASS |
| 10_result | 189 | 9.8 | 2 | 116 | YES | PASS |
| 11_closure | 144 | 7.8 | 1 | 85 | YES | PASS |
| 12_while | 140 | 7.7 | 1 | 91 | YES | PASS |
| 13_fib | 151 | 7.9 | 2 | 84 | YES | PASS |
| 14_nested_struct | 136 | 7.7 | 1 | 90 | YES | PASS |
| 15_multifunction | 149 | 7.9 | 3 | 110 | YES | PASS |
| 16_string_escape | 145 | 8.4 | 1 | 84 | YES | PASS |
| 17_option | 211 | 10.3 | 2 | 101 | YES | PASS |
| 18_method_chain | 156 | 8.9 | 1 | 97 | YES | PASS |
| 19_nested_match | 184 | 9.2 | 2 | 107 | YES | PASS |
| 20_recursion | 152 | 8.0 | 2 | 87 | YES | PASS |
| 21_list_ops | 227 | 11.5 | 2 | 145 | YES | PASS |
| 22_string_builder | 184 | 9.7 | 2 | 107 | YES | PASS |
| 23_multi_return | 160 | 8.6 | 2 | 112 | YES | PASS |
| 24_enum_methods | 172 | 9.1 | 2 | 111 | YES | PASS |
| 25_fizzbuzz | 201 | 9.7 | 2 | 89 | YES | PASS |
| 26_generics | 198 | 9.7 | 5 | 74 | YES | PASS |
| 27_impl | 159 | 8.5 | 3 | 95 | YES | PASS |
| 28_traits | 164 | 8.5 | 3 | 113 | YES | PASS |
| 29_generic_impl | 166 | 8.8 | 3 | 100 | YES | PASS |
| 30_nested_generics | 166 | 9.5 | 1 | 88 | YES | PASS |
| 31_generic_multi | 182 | 9.7 | 4 | 95 | YES | PASS |
| 32_generic_enum | 143 | 8.0 | 1 | 88 | YES | PASS |
| 33_break_continue | 345 | 14.1 | 5 | 118 | YES | PASS |
| 34_file_io | 194 | 11.1 | 1 | 88 | YES | PASS |
| 35_stdin | 136 | 8.0 | 1 | 87 | YES | PASS |
| 36_crypto | 155 | 8.9 | 1 | 93 | YES | PASS |
| 37_regex | 176 | 10.0 | 1 | 111 | YES | PASS |
| 38_http | 132 | 7.7 | 1 | 130 | YES | PASS |
| 39_gpu_detect | 149 | 8.5 | 1 | 128 | YES | PASS |
| 40_gpu_tensor | 296 | 15.0 | 1 | 174 | YES | PASS |
| 41_module_let | 134 | 7.5 | 2 | 117 | YES | PASS |
| 42_module_let_string | 137 | 7.7 | 2 | 127 | YES | PASS |
| 43_module_let_math | 139 | 7.8 | 2 | 144 | YES | PASS |
| 45_ffi_bind | 163 | 8.2 | 3 | 146 | YES | PASS |
| 47_try_operator | 268 | 13.0 | 4 | 115 | YES | PASS |
| 48_match_nested_exhaustive | 227 | 11.8 | 3 | 91 | YES | PASS |
| 49_match_guards | 178 | 9.4 | 2 | 96 | YES | PASS |
| 49_tensor_literal | 0 | 0.0 | 0 | 31 | - | FAIL |
| 50_match_or_patterns | 190 | 10.1 | 2 | 103 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 36 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 41 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 33 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 26 | - | FAIL |
| 54_const_basic | 136 | 7.8 | 1 | 70 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 36 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 25 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 26 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 35 | - | FAIL |
| 58_const_scope | 169 | 8.8 | 2 | 111 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 38 | - | FAIL |
| 62_list_output | 263 | 14.0 | 3 | 120 | YES | PASS |
| 63_else_sino | 205 | 9.7 | 3 | 105 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 33 | - | FAIL |
| 65_list_int_indexing | 280 | 14.2 | 1 | 127 | YES | PASS |
| 66_qualified_type_ref | 147 | 8.0 | 2 | 115 | YES | PASS |
| **Total** | | | | **6211** | **54/66** | **54/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 772 | 150 | 5.2x |
| 02_arithmetic | 10 | 172 | 0.1x |
| 03_function | 7 | 138 | 0.0x |
| 04_if_else | 5 | 117 | 0.0x |
| 05_for_loop | 5 | 111 | 0.0x |
| 06_struct | 5 | 77 | 0.1x |
| 07_enum_match | 11 | 87 | 0.1x |
| 08_list | 6 | 98 | 0.1x |
| 09_string_methods | 6 | 114 | 0.0x |
| 10_result | 8 | 116 | 0.1x |
| 11_closure | 5 | 85 | 0.1x |
| 12_while | 4 | 91 | 0.0x |
| 13_fib | 4 | 84 | 0.1x |
| 14_nested_struct | 4 | 90 | 0.0x |
| 15_multifunction | 6 | 110 | 0.1x |
| 16_string_escape | 5 | 84 | 0.1x |
| 17_option | 6 | 101 | 0.1x |
| 18_method_chain | 5 | 97 | 0.0x |
| 19_nested_match | 8 | 107 | 0.1x |
| 20_recursion | 5 | 87 | 0.1x |
| 21_list_ops | 6 | 145 | 0.0x |
| 22_string_builder | 6 | 107 | 0.1x |
| 23_multi_return | 5 | 112 | 0.0x |
| 24_enum_methods | 9 | 111 | 0.1x |
| 25_fizzbuzz | 7 | 89 | 0.1x |
| 26_generics | 6 | 74 | 0.1x |
| 27_impl | 6 | 95 | 0.1x |
| 28_traits | 6 | 113 | 0.0x |
| 29_generic_impl | 6 | 100 | 0.1x |
| 30_nested_generics | 6 | 88 | 0.1x |
| 31_generic_multi | 7 | 95 | 0.1x |
| 32_generic_enum | 4 | 88 | 0.1x |
| 33_break_continue | 9 | 118 | 0.1x |
| 34_file_io | 5 | 88 | 0.1x |
| 35_stdin | 4 | 87 | 0.1x |
| 36_crypto | 4 | 93 | 0.0x |
| 37_regex | 5 | 111 | 0.0x |
| 38_http | 6 | 130 | 0.0x |
| 39_gpu_detect | 6 | 128 | 0.0x |
| 40_gpu_tensor | 8 | 174 | 0.0x |
| 41_module_let | 7 | 117 | 0.1x |
| 42_module_let_string | 5 | 127 | 0.0x |
| 43_module_let_math | 8 | 144 | 0.1x |
| 45_ffi_bind | 7 | 146 | 0.0x |
| 47_try_operator | 8 | 115 | 0.1x |
| 48_match_nested_exhaustive | 8 | 91 | 0.1x |
| 49_match_guards | 6 | 96 | 0.1x |
| 50_match_or_patterns | 6 | 103 | 0.1x |
| 54_const_basic | 4 | 70 | 0.1x |
| 58_const_scope | 6 | 111 | 0.1x |
| 62_list_output | 7 | 120 | 0.1x |
| 63_else_sino | 6 | 105 | 0.1x |
| 65_list_int_indexing | 6 | 127 | 0.0x |
| 66_qualified_type_ref | 7 | 115 | 0.1x |

