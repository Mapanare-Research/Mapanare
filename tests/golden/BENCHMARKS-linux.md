# Mapanare Benchmarks - Linux

Generated: 2026-04-18 05:00 UTC  
Version: 4.142.0 (`21421c8`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 6.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 656 | ` _ __    ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 8 | `        ` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 8 | `     _  ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `   *~   ` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 142 | 5.1 | 2 | 10 | 147 | 6 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 5 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `        ` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 5 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `__...~ _ ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `     _   ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `--___   ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `._.-_. _ ^` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 6 | `_ _  _   ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `_.__.-  ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 5 | `_____.   ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `~  ___  ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 7 | `    _    ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `____._  ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `    _   ` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 9 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 6 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `    __  ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `  __ _  ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `     _  ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `  _  _  ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | `    -   ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `_._... _ ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `.__... _ ^` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `     _  ` | PASS |
| 47_try_operator | 32 | 288 | 10.7 | 4 | 23 | 279 | 8 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 337 | 13.6 | 3 | 32 | 309 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | ` -_ __  ` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `   ._-  ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `.__...  ` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `-    -  ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `_    _  ` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `*_____   ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `--__ _  ` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `._____ _ ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `        ` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `         ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `______ _ ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `         ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `.___._  ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `_       ` | PASS |
| 62_list_output | 35 | 295 | 14.1 | 2 | 20 | 289 | 8 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.6 | 3 | 20 | 250 | 6 | `_.____  ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `._.___  ` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 7 | `        ` | PASS |
| 66_qualified_type_ref | 17 | 46 | 1.4 | 1 | 4 | 33 | 6 | `-*_  v` | PASS |
| **Total** | **1332** | **12574** | **472.5** | **110** | **995** | **10715** | **1033** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 125 | 7.4 | 1 | 91 | YES | PASS |
| 02_arithmetic | 130 | 7.4 | 1 | 96 | YES | PASS |
| 03_function | 140 | 7.7 | 2 | 84 | YES | PASS |
| 04_if_else | 142 | 7.9 | 1 | 120 | YES | PASS |
| 05_for_loop | 153 | 8.3 | 1 | 140 | YES | PASS |
| 06_struct | 135 | 7.7 | 1 | 101 | YES | PASS |
| 07_enum_match | 148 | 8.2 | 1 | 87 | YES | PASS |
| 08_list | 157 | 8.7 | 1 | 90 | YES | PASS |
| 09_string_methods | 138 | 8.0 | 1 | 81 | YES | PASS |
| 10_result | 183 | 9.5 | 2 | 97 | YES | PASS |
| 11_closure | 143 | 7.8 | 1 | 85 | YES | PASS |
| 12_while | 139 | 7.7 | 1 | 74 | YES | PASS |
| 13_fib | 150 | 7.9 | 2 | 83 | YES | PASS |
| 14_nested_struct | 135 | 7.7 | 1 | 92 | YES | PASS |
| 15_multifunction | 148 | 7.8 | 3 | 90 | YES | PASS |
| 16_string_escape | 144 | 8.3 | 1 | 78 | YES | PASS |
| 17_option | 210 | 10.3 | 2 | 125 | YES | PASS |
| 18_method_chain | 155 | 8.8 | 1 | 71 | YES | PASS |
| 19_nested_match | 183 | 9.2 | 2 | 81 | YES | PASS |
| 20_recursion | 151 | 8.0 | 2 | 85 | YES | PASS |
| 21_list_ops | 216 | 11.1 | 2 | 88 | YES | PASS |
| 22_string_builder | 183 | 9.7 | 2 | 91 | YES | PASS |
| 23_multi_return | 159 | 8.6 | 2 | 114 | YES | PASS |
| 24_enum_methods | 171 | 9.1 | 2 | 122 | YES | PASS |
| 25_fizzbuzz | 200 | 9.7 | 2 | 109 | YES | PASS |
| 26_generics | 197 | 9.6 | 5 | 75 | YES | PASS |
| 27_impl | 158 | 8.4 | 3 | 75 | YES | PASS |
| 28_traits | 163 | 8.5 | 3 | 82 | YES | PASS |
| 29_generic_impl | 165 | 8.8 | 3 | 102 | YES | PASS |
| 30_nested_generics | 165 | 9.5 | 1 | 100 | YES | PASS |
| 31_generic_multi | 181 | 9.6 | 4 | 112 | YES | PASS |
| 32_generic_enum | 142 | 8.0 | 1 | 86 | YES | PASS |
| 33_break_continue | 334 | 13.7 | 5 | 95 | YES | PASS |
| 34_file_io | 193 | 11.0 | 1 | 72 | YES | PASS |
| 35_stdin | 135 | 7.9 | 1 | 68 | YES | PASS |
| 36_crypto | 154 | 8.9 | 1 | 81 | YES | PASS |
| 37_regex | 175 | 10.0 | 1 | 75 | YES | PASS |
| 38_http | 131 | 7.7 | 1 | 85 | YES | PASS |
| 39_gpu_detect | 148 | 8.4 | 1 | 96 | YES | PASS |
| 40_gpu_tensor | 255 | 13.4 | 1 | 91 | YES | PASS |
| 41_module_let | 133 | 7.5 | 2 | 78 | YES | PASS |
| 42_module_let_string | 136 | 7.7 | 2 | 71 | YES | PASS |
| 43_module_let_math | 138 | 7.8 | 2 | 74 | YES | PASS |
| 45_ffi_bind | 162 | 8.2 | 3 | 100 | YES | PASS |
| 47_try_operator | 249 | 12.0 | 4 | 145 | YES | PASS |
| 48_match_nested_exhaustive | 218 | 11.3 | 3 | 95 | YES | PASS |
| 49_match_guards | 177 | 9.4 | 2 | 81 | YES | PASS |
| 49_tensor_literal | 0 | 0.0 | 0 | 29 | - | FAIL |
| 50_match_or_patterns | 189 | 10.0 | 2 | 81 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 30 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 29 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 32 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 35 | - | FAIL |
| 54_const_basic | 135 | 7.8 | 1 | 73 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 28 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 30 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 29 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 28 | - | FAIL |
| 58_const_scope | 168 | 8.8 | 2 | 83 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 30 | - | FAIL |
| 62_list_output | 248 | 13.3 | 3 | 94 | YES | PASS |
| 63_else_sino | 204 | 9.7 | 3 | 79 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 29 | - | FAIL |
| 65_list_int_indexing | 219 | 11.7 | 1 | 97 | YES | PASS |
| 66_qualified_type_ref | 146 | 8.0 | 2 | 121 | YES | PASS |
| **Total** | | | | **5273** | **54/66** | **54/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 656 | 91 | 7.2x |
| 02_arithmetic | 8 | 96 | 0.1x |
| 03_function | 7 | 84 | 0.1x |
| 04_if_else | 5 | 120 | 0.0x |
| 05_for_loop | 8 | 140 | 0.1x |
| 06_struct | 6 | 101 | 0.1x |
| 07_enum_match | 13 | 87 | 0.1x |
| 08_list | 7 | 90 | 0.1x |
| 09_string_methods | 4 | 81 | 0.1x |
| 10_result | 6 | 97 | 0.1x |
| 11_closure | 4 | 85 | 0.0x |
| 12_while | 5 | 74 | 0.1x |
| 13_fib | 5 | 83 | 0.1x |
| 14_nested_struct | 4 | 92 | 0.0x |
| 15_multifunction | 5 | 90 | 0.1x |
| 16_string_escape | 4 | 78 | 0.1x |
| 17_option | 5 | 125 | 0.0x |
| 18_method_chain | 5 | 71 | 0.1x |
| 19_nested_match | 6 | 81 | 0.1x |
| 20_recursion | 4 | 85 | 0.1x |
| 21_list_ops | 5 | 88 | 0.1x |
| 22_string_builder | 5 | 91 | 0.1x |
| 23_multi_return | 6 | 114 | 0.0x |
| 24_enum_methods | 6 | 122 | 0.0x |
| 25_fizzbuzz | 5 | 109 | 0.0x |
| 26_generics | 7 | 75 | 0.1x |
| 27_impl | 5 | 75 | 0.1x |
| 28_traits | 5 | 82 | 0.1x |
| 29_generic_impl | 7 | 102 | 0.1x |
| 30_nested_generics | 5 | 100 | 0.1x |
| 31_generic_multi | 8 | 112 | 0.1x |
| 32_generic_enum | 4 | 86 | 0.1x |
| 33_break_continue | 9 | 95 | 0.1x |
| 34_file_io | 6 | 72 | 0.1x |
| 35_stdin | 4 | 68 | 0.1x |
| 36_crypto | 4 | 81 | 0.1x |
| 37_regex | 4 | 75 | 0.1x |
| 38_http | 4 | 85 | 0.0x |
| 39_gpu_detect | 4 | 96 | 0.0x |
| 40_gpu_tensor | 6 | 91 | 0.1x |
| 41_module_let | 5 | 78 | 0.1x |
| 42_module_let_string | 5 | 71 | 0.1x |
| 43_module_let_math | 5 | 74 | 0.1x |
| 45_ffi_bind | 5 | 100 | 0.1x |
| 47_try_operator | 8 | 145 | 0.1x |
| 48_match_nested_exhaustive | 7 | 95 | 0.1x |
| 49_match_guards | 6 | 81 | 0.1x |
| 50_match_or_patterns | 5 | 81 | 0.1x |
| 54_const_basic | 4 | 73 | 0.1x |
| 58_const_scope | 5 | 83 | 0.1x |
| 62_list_output | 8 | 94 | 0.1x |
| 63_else_sino | 6 | 79 | 0.1x |
| 65_list_int_indexing | 7 | 97 | 0.1x |
| 66_qualified_type_ref | 6 | 121 | 0.0x |

