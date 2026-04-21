# Mapanare Benchmarks - Linux

Generated: 2026-04-19 20:47 UTC  
Version: 4.155.0 (`8a425b7`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 7.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 682 | `______   v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 10 | `        ` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 12 | `        ` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 8 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `  _      v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `        ` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `*...-*..` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `-  _     ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 6 | `__ _ .  ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `__*_____` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 5 | `__*__ __` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `.  ____  v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 6 | `         v` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 5 | `___-___  v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `  __     v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 6 | ` __   _  v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `_____~._ v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 6 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 9 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 7 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 5 | ` _ _ __  v` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 7 | `-.____  ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 7 | `  _ _    v` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `  __.   ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | ` _  __   ^` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `.._-.*__` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | ` .___-  ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.8 | 2 | 9 | 83 | 5 | `..  _.   ^` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         v` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 5 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | ` _~  _  ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `._*.-.*_ v` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | ` _.___*  v` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `__- _ -  v` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `__.___-_ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `      _  v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 6 | `..-.-.-. v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `  .__    v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | ` _ __    v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | ` *.__ _  v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 4 | `  ._..  ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `__-*..*_ v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 10 | `___.__~  v` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 10 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `  _     ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `__.__._  v` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 6 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `__..._._ v` | PASS |
| **Total** | **1336** | **12615** | **475.3** | **110** | **995** | **10795** | **1077** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 125 | 7.4 | 1 | 146 | YES | PASS |
| 02_arithmetic | 130 | 7.4 | 1 | 144 | YES | PASS |
| 03_function | 140 | 7.7 | 2 | 131 | YES | PASS |
| 04_if_else | 142 | 7.9 | 1 | 106 | YES | PASS |
| 05_for_loop | 153 | 8.3 | 1 | 103 | YES | PASS |
| 06_struct | 135 | 7.7 | 1 | 77 | YES | PASS |
| 07_enum_match | 148 | 8.2 | 1 | 78 | YES | PASS |
| 08_list | 157 | 8.7 | 1 | 87 | YES | PASS |
| 09_string_methods | 138 | 8.0 | 1 | 89 | YES | PASS |
| 10_result | 183 | 9.5 | 2 | 112 | YES | PASS |
| 11_closure | 143 | 7.8 | 1 | 99 | YES | PASS |
| 12_while | 139 | 7.7 | 1 | 75 | YES | PASS |
| 13_fib | 150 | 7.9 | 2 | 83 | YES | PASS |
| 14_nested_struct | 135 | 7.7 | 1 | 82 | YES | PASS |
| 15_multifunction | 148 | 7.8 | 3 | 96 | YES | PASS |
| 16_string_escape | 144 | 8.3 | 1 | 90 | YES | PASS |
| 17_option | 210 | 10.3 | 2 | 99 | YES | PASS |
| 18_method_chain | 155 | 8.8 | 1 | 86 | YES | PASS |
| 19_nested_match | 183 | 9.2 | 2 | 103 | YES | PASS |
| 20_recursion | 151 | 8.0 | 2 | 108 | YES | PASS |
| 21_list_ops | 216 | 11.1 | 2 | 109 | YES | PASS |
| 22_string_builder | 183 | 9.7 | 2 | 97 | YES | PASS |
| 23_multi_return | 159 | 8.6 | 2 | 88 | YES | PASS |
| 24_enum_methods | 171 | 9.1 | 2 | 119 | YES | PASS |
| 25_fizzbuzz | 200 | 9.7 | 2 | 106 | YES | PASS |
| 26_generics | 197 | 9.6 | 5 | 70 | YES | PASS |
| 27_impl | 158 | 8.4 | 3 | 79 | YES | PASS |
| 28_traits | 163 | 8.5 | 3 | 76 | YES | PASS |
| 29_generic_impl | 165 | 8.8 | 3 | 107 | YES | PASS |
| 30_nested_generics | 165 | 9.4 | 1 | 89 | YES | PASS |
| 31_generic_multi | 181 | 9.6 | 4 | 95 | YES | PASS |
| 32_generic_enum | 142 | 8.0 | 1 | 117 | YES | PASS |
| 33_break_continue | 334 | 13.7 | 5 | 211 | YES | PASS |
| 34_file_io | 193 | 11.0 | 1 | 156 | YES | PASS |
| 35_stdin | 135 | 7.9 | 1 | 155 | YES | PASS |
| 36_crypto | 154 | 8.9 | 1 | 200 | YES | PASS |
| 37_regex | 175 | 10.0 | 1 | 177 | YES | PASS |
| 38_http | 131 | 7.7 | 1 | 115 | YES | PASS |
| 39_gpu_detect | 148 | 8.4 | 1 | 106 | YES | PASS |
| 40_gpu_tensor | 255 | 13.4 | 1 | 111 | YES | PASS |
| 41_module_let | 133 | 7.5 | 2 | 95 | YES | PASS |
| 42_module_let_string | 136 | 7.7 | 2 | 105 | YES | PASS |
| 43_module_let_math | 138 | 7.8 | 2 | 95 | YES | PASS |
| 45_ffi_bind | 162 | 8.2 | 3 | 93 | YES | PASS |
| 47_try_operator | 249 | 12.0 | 4 | 107 | YES | PASS |
| 48_match_nested_exhaustive | 218 | 11.3 | 3 | 86 | YES | PASS |
| 49_match_guards | 177 | 9.4 | 2 | 98 | YES | PASS |
| 49_tensor_literal | 0 | 0.0 | 0 | 31 | - | FAIL |
| 50_match_or_patterns | 189 | 10.0 | 2 | 108 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 35 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 35 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 40 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 33 | - | FAIL |
| 54_const_basic | 135 | 7.8 | 1 | 71 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 30 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 28 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 29 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 27 | - | FAIL |
| 58_const_scope | 168 | 8.8 | 2 | 164 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 56 | - | FAIL |
| 62_list_output | 248 | 13.3 | 3 | 134 | YES | PASS |
| 63_else_sino | 204 | 9.7 | 3 | 87 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 29 | - | FAIL |
| 65_list_int_indexing | 219 | 11.7 | 1 | 96 | YES | PASS |
| 66_qualified_type_ref | 146 | 8.0 | 2 | 83 | YES | PASS |
| **Total** | | | | **6165** | **54/66** | **54/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 682 | 146 | 4.7x |
| 02_arithmetic | 10 | 144 | 0.1x |
| 03_function | 7 | 131 | 0.0x |
| 04_if_else | 6 | 106 | 0.1x |
| 05_for_loop | 5 | 103 | 0.0x |
| 06_struct | 5 | 77 | 0.1x |
| 07_enum_match | 12 | 78 | 0.2x |
| 08_list | 8 | 87 | 0.1x |
| 09_string_methods | 4 | 89 | 0.0x |
| 10_result | 6 | 112 | 0.1x |
| 11_closure | 5 | 99 | 0.1x |
| 12_while | 5 | 75 | 0.1x |
| 13_fib | 5 | 83 | 0.1x |
| 14_nested_struct | 5 | 82 | 0.1x |
| 15_multifunction | 5 | 96 | 0.1x |
| 16_string_escape | 5 | 90 | 0.1x |
| 17_option | 6 | 99 | 0.1x |
| 18_method_chain | 4 | 86 | 0.1x |
| 19_nested_match | 6 | 103 | 0.1x |
| 20_recursion | 5 | 108 | 0.0x |
| 21_list_ops | 6 | 109 | 0.1x |
| 22_string_builder | 5 | 97 | 0.1x |
| 23_multi_return | 5 | 88 | 0.1x |
| 24_enum_methods | 5 | 119 | 0.0x |
| 25_fizzbuzz | 6 | 106 | 0.1x |
| 26_generics | 6 | 70 | 0.1x |
| 27_impl | 5 | 79 | 0.1x |
| 28_traits | 5 | 76 | 0.1x |
| 29_generic_impl | 6 | 107 | 0.1x |
| 30_nested_generics | 6 | 89 | 0.1x |
| 31_generic_multi | 6 | 95 | 0.1x |
| 32_generic_enum | 4 | 117 | 0.0x |
| 33_break_continue | 9 | 211 | 0.0x |
| 34_file_io | 7 | 156 | 0.0x |
| 35_stdin | 5 | 155 | 0.0x |
| 36_crypto | 7 | 200 | 0.0x |
| 37_regex | 7 | 177 | 0.0x |
| 38_http | 5 | 115 | 0.0x |
| 39_gpu_detect | 5 | 106 | 0.0x |
| 40_gpu_tensor | 6 | 111 | 0.1x |
| 41_module_let | 5 | 95 | 0.0x |
| 42_module_let_string | 5 | 105 | 0.0x |
| 43_module_let_math | 5 | 95 | 0.1x |
| 45_ffi_bind | 5 | 93 | 0.0x |
| 47_try_operator | 7 | 107 | 0.1x |
| 48_match_nested_exhaustive | 7 | 86 | 0.1x |
| 49_match_guards | 5 | 98 | 0.1x |
| 50_match_or_patterns | 5 | 108 | 0.1x |
| 54_const_basic | 6 | 71 | 0.1x |
| 58_const_scope | 6 | 164 | 0.0x |
| 62_list_output | 10 | 134 | 0.1x |
| 63_else_sino | 6 | 87 | 0.1x |
| 65_list_int_indexing | 6 | 96 | 0.1x |
| 66_qualified_type_ref | 5 | 83 | 0.1x |

