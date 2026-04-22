# Mapanare Benchmarks - Linux

Generated: 2026-04-22 02:14 UTC  
Version: 5.0.5 (`d9bbc19`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 7.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 716 | `___  ___ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 8 | `     _   ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 8 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 8 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 7 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 6 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `        ` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 6 | `.-*.._._ v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 8 | `_       ` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `_ .  _._ v` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `________` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 6 | `__ __ __` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `____ _  ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `-___  __` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `_       ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `   _    ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `__~._.__` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 6 | `        ` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 9 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 8 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `_ __ _  ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `___  -*_ v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` _   ._  v` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_.   __  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | ` __   _  v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `-.*__...` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 4 | `__-  __  v` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | ` _.   __` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 8 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | `  _   _. ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `.-.*_...` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `___* _._ v` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | ` _ -  _. ^` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `___-___. ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `   _   _ ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 6 | `.-.-.-_- ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 7 | `__    .  v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 6 | `__    ._ v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 7 | `__ _ _.  v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 6 | `_..   ~  v` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 7 | `*..*_.-_ v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `.__~ ..  v` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 8 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `      ~  v` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `__._ _._ v` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `.._._...` | PASS |
| **Total** | **1336** | **12615** | **475.2** | **110** | **995** | **10795** | **1123** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 125 | 7.4 | 1 | 134 | YES | PASS |
| 02_arithmetic | 130 | 7.4 | 1 | 125 | YES | PASS |
| 03_function | 140 | 7.7 | 2 | 151 | YES | PASS |
| 04_if_else | 142 | 7.9 | 1 | 186 | YES | PASS |
| 05_for_loop | 153 | 8.3 | 1 | 156 | YES | PASS |
| 06_struct | 135 | 7.7 | 1 | 92 | YES | PASS |
| 07_enum_match | 148 | 8.2 | 1 | 89 | YES | PASS |
| 08_list | 157 | 8.7 | 1 | 100 | YES | PASS |
| 09_string_methods | 138 | 8.0 | 1 | 104 | YES | PASS |
| 10_result | 188 | 9.8 | 2 | 120 | YES | PASS |
| 11_closure | 143 | 7.8 | 1 | 100 | YES | PASS |
| 12_while | 139 | 7.7 | 1 | 133 | YES | PASS |
| 13_fib | 150 | 7.9 | 2 | 140 | YES | PASS |
| 14_nested_struct | 135 | 7.7 | 1 | 81 | YES | PASS |
| 15_multifunction | 148 | 7.8 | 3 | 95 | YES | PASS |
| 16_string_escape | 144 | 8.3 | 1 | 77 | YES | PASS |
| 17_option | 210 | 10.3 | 2 | 108 | YES | PASS |
| 18_method_chain | 155 | 8.8 | 1 | 112 | YES | PASS |
| 19_nested_match | 183 | 9.2 | 2 | 113 | YES | PASS |
| 20_recursion | 151 | 8.0 | 2 | 99 | YES | PASS |
| 21_list_ops | 216 | 11.1 | 2 | 103 | YES | PASS |
| 22_string_builder | 183 | 9.7 | 2 | 106 | YES | PASS |
| 23_multi_return | 159 | 8.6 | 2 | 102 | YES | PASS |
| 24_enum_methods | 171 | 9.1 | 2 | 111 | YES | PASS |
| 25_fizzbuzz | 200 | 9.7 | 2 | 110 | YES | PASS |
| 26_generics | 197 | 9.6 | 5 | 105 | YES | PASS |
| 27_impl | 158 | 8.4 | 3 | 89 | YES | PASS |
| 28_traits | 163 | 8.5 | 3 | 91 | YES | PASS |
| 29_generic_impl | 165 | 8.8 | 3 | 81 | YES | PASS |
| 30_nested_generics | 165 | 9.4 | 1 | 86 | YES | PASS |
| 31_generic_multi | 181 | 9.6 | 4 | 116 | YES | PASS |
| 32_generic_enum | 142 | 8.0 | 1 | 137 | YES | PASS |
| 33_break_continue | 334 | 13.7 | 5 | 117 | YES | PASS |
| 34_file_io | 193 | 11.0 | 1 | 82 | YES | PASS |
| 35_stdin | 135 | 7.9 | 1 | 85 | YES | PASS |
| 36_crypto | 154 | 8.9 | 1 | 93 | YES | PASS |
| 37_regex | 175 | 10.0 | 1 | 89 | YES | PASS |
| 38_http | 131 | 7.7 | 1 | 93 | YES | PASS |
| 39_gpu_detect | 148 | 8.4 | 1 | 98 | YES | PASS |
| 40_gpu_tensor | 255 | 13.4 | 1 | 119 | YES | PASS |
| 41_module_let | 133 | 7.5 | 2 | 91 | YES | PASS |
| 42_module_let_string | 136 | 7.7 | 2 | 78 | YES | PASS |
| 43_module_let_math | 138 | 7.8 | 2 | 83 | YES | PASS |
| 45_ffi_bind | 162 | 8.2 | 3 | 98 | YES | PASS |
| 47_try_operator | 267 | 12.9 | 4 | 126 | YES | PASS |
| 48_match_nested_exhaustive | 226 | 11.8 | 3 | 120 | YES | PASS |
| 49_match_guards | 177 | 9.4 | 2 | 159 | YES | PASS |
| 49_tensor_literal | 0 | 0.0 | 0 | 45 | - | FAIL |
| 50_match_or_patterns | 189 | 10.0 | 2 | 124 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 31 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 28 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 31 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 40 | - | FAIL |
| 54_const_basic | 135 | 7.8 | 1 | 128 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 60 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 55 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 50 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 46 | - | FAIL |
| 58_const_scope | 168 | 8.8 | 2 | 93 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 26 | - | FAIL |
| 62_list_output | 262 | 13.9 | 3 | 87 | YES | PASS |
| 63_else_sino | 204 | 9.7 | 3 | 80 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 33 | - | FAIL |
| 65_list_int_indexing | 219 | 11.7 | 1 | 99 | YES | PASS |
| 66_qualified_type_ref | 146 | 8.0 | 2 | 89 | YES | PASS |
| **Total** | | | | **6230** | **54/66** | **54/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 716 | 134 | 5.4x |
| 02_arithmetic | 8 | 125 | 0.1x |
| 03_function | 8 | 151 | 0.1x |
| 04_if_else | 8 | 186 | 0.0x |
| 05_for_loop | 8 | 156 | 0.1x |
| 06_struct | 5 | 92 | 0.1x |
| 07_enum_match | 13 | 89 | 0.1x |
| 08_list | 6 | 100 | 0.1x |
| 09_string_methods | 4 | 104 | 0.0x |
| 10_result | 7 | 120 | 0.1x |
| 11_closure | 6 | 100 | 0.1x |
| 12_while | 5 | 133 | 0.0x |
| 13_fib | 6 | 140 | 0.0x |
| 14_nested_struct | 5 | 81 | 0.1x |
| 15_multifunction | 5 | 95 | 0.0x |
| 16_string_escape | 4 | 77 | 0.1x |
| 17_option | 6 | 108 | 0.1x |
| 18_method_chain | 6 | 112 | 0.1x |
| 19_nested_match | 8 | 113 | 0.1x |
| 20_recursion | 5 | 99 | 0.1x |
| 21_list_ops | 5 | 103 | 0.1x |
| 22_string_builder | 6 | 106 | 0.1x |
| 23_multi_return | 6 | 102 | 0.1x |
| 24_enum_methods | 5 | 111 | 0.0x |
| 25_fizzbuzz | 6 | 110 | 0.1x |
| 26_generics | 7 | 105 | 0.1x |
| 27_impl | 6 | 89 | 0.1x |
| 28_traits | 5 | 91 | 0.1x |
| 29_generic_impl | 5 | 81 | 0.1x |
| 30_nested_generics | 5 | 86 | 0.1x |
| 31_generic_multi | 8 | 116 | 0.1x |
| 32_generic_enum | 6 | 137 | 0.0x |
| 33_break_continue | 9 | 117 | 0.1x |
| 34_file_io | 8 | 82 | 0.1x |
| 35_stdin | 4 | 85 | 0.0x |
| 36_crypto | 5 | 93 | 0.1x |
| 37_regex | 5 | 89 | 0.1x |
| 38_http | 4 | 93 | 0.0x |
| 39_gpu_detect | 5 | 98 | 0.0x |
| 40_gpu_tensor | 6 | 119 | 0.0x |
| 41_module_let | 5 | 91 | 0.1x |
| 42_module_let_string | 4 | 78 | 0.1x |
| 43_module_let_math | 4 | 83 | 0.1x |
| 45_ffi_bind | 5 | 98 | 0.0x |
| 47_try_operator | 8 | 126 | 0.1x |
| 48_match_nested_exhaustive | 7 | 120 | 0.1x |
| 49_match_guards | 8 | 159 | 0.0x |
| 50_match_or_patterns | 7 | 124 | 0.1x |
| 54_const_basic | 6 | 128 | 0.0x |
| 58_const_scope | 7 | 93 | 0.1x |
| 62_list_output | 8 | 87 | 0.1x |
| 63_else_sino | 6 | 80 | 0.1x |
| 65_list_int_indexing | 6 | 99 | 0.1x |
| 66_qualified_type_ref | 5 | 89 | 0.1x |

