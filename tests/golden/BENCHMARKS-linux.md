# Mapanare Benchmarks - Linux

Generated: 2026-04-14 23:06 UTC  
Version: 4.123.0 (`5b90ccb`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 6.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 637 | `~..-.-.. v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `         ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 9 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 142 | 5.1 | 2 | 10 | 147 | 6 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `        ` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 6 | `-__*_~-_ v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `.._*.~__` | PASS |
| 19_nested_match | 18 | 199 | 6.9 | 2 | 15 | 186 | 7 | `.__-_*..` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `.._-_-_- ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `~*~~.*.- ^` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 7 | `.-.-_-__` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         v` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `_~_-_*__` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 8 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `.*__ -__` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `-~.-.*_. ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `_.__.-_. ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `_-_._-__` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 5 | `_    __  v` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 8 | `         v` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 6 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `.__._*.- ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `___. *__` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `__   *  ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `   _ *_. ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | ` _   ._  v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `         v` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `--___*_. ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 6 | `_-_ _-__` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 6 | ` .   - _ ^` | PASS |
| 47_try_operator | 32 | 288 | 10.7 | 4 | 23 | 279 | 9 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 337 | 13.6 | 3 | 32 | 309 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 8 | `-_____-  v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `__ ___  ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | ` __. __  v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | ` __- -  ` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | ` -   ___` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 7 | `_.______` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `_-___-__` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `_-______` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `__ _ _.  v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 5 | `..  ...  v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | `_  _ __  v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `-__  -__` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `-_____._ v` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `.    ..  v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `_     -  v` | PASS |
| 62_list_output | 35 | 295 | 14.1 | 2 | 20 | 289 | 6 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.6 | 3 | 20 | 250 | 6 | `___  .._ v` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `._. .-.- ^` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 5 | ` * ^` | PASS |
| **Total** | **1315** | **12563** | **472.4** | **109** | **995** | **10698** | **1016** | | **64/65** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 132 | 7.8 | 1 | 88 | YES | PASS |
| 02_arithmetic | 137 | 7.8 | 1 | 106 | YES | PASS |
| 03_function | 147 | 8.0 | 2 | 153 | DIFF | PASS |
| 04_if_else | 149 | 8.3 | 1 | 129 | YES | PASS |
| 05_for_loop | 160 | 8.7 | 1 | 112 | YES | PASS |
| 06_struct | 142 | 8.0 | 1 | 85 | YES | PASS |
| 07_enum_match | 155 | 8.6 | 1 | 83 | YES | PASS |
| 08_list | 164 | 9.1 | 1 | 92 | YES | PASS |
| 09_string_methods | 145 | 8.4 | 1 | 76 | YES | PASS |
| 10_result | 190 | 10.0 | 2 | 108 | YES | PASS |
| 11_closure | 150 | 8.1 | 1 | 90 | YES | PASS |
| 12_while | 146 | 8.0 | 1 | 108 | YES | PASS |
| 13_fib | 0 | 0.0 | 0 | 116 | - | FAIL |
| 14_nested_struct | 142 | 8.0 | 1 | 75 | YES | PASS |
| 15_multifunction | 155 | 8.2 | 3 | 77 | DIFF | PASS |
| 16_string_escape | 151 | 8.7 | 1 | 67 | YES | PASS |
| 17_option | 217 | 10.7 | 2 | 104 | YES | PASS |
| 18_method_chain | 162 | 9.2 | 1 | 98 | YES | PASS |
| 19_nested_match | 0 | 0.0 | 0 | 100 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 96 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 68 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 119 | - | FAIL |
| 23_multi_return | 166 | 8.9 | 2 | 122 | DIFF | PASS |
| 24_enum_methods | 178 | 9.4 | 2 | 107 | YES | PASS |
| 25_fizzbuzz | 207 | 10.1 | 2 | 99 | YES | PASS |
| 26_generics | 204 | 10.0 | 5 | 90 | DIFF | PASS |
| 27_impl | 165 | 8.8 | 3 | 84 | DIFF | PASS |
| 28_traits | 170 | 8.8 | 3 | 82 | DIFF | PASS |
| 29_generic_impl | 0 | 0.0 | 0 | 80 | - | FAIL |
| 30_nested_generics | 172 | 9.8 | 1 | 88 | YES | PASS |
| 31_generic_multi | 0 | 0.0 | 0 | 94 | - | FAIL |
| 32_generic_enum | 149 | 8.3 | 1 | 105 | YES | PASS |
| 33_break_continue | 0 | 0.0 | 0 | 87 | - | FAIL |
| 34_file_io | 200 | 11.4 | 1 | 82 | YES | PASS |
| 35_stdin | 142 | 8.3 | 1 | 74 | YES | PASS |
| 36_crypto | 161 | 9.3 | 1 | 74 | YES | PASS |
| 37_regex | 182 | 10.4 | 1 | 83 | YES | PASS |
| 38_http | 138 | 8.1 | 1 | 98 | YES | PASS |
| 39_gpu_detect | 155 | 8.8 | 1 | 93 | YES | PASS |
| 40_gpu_tensor | 0 | 0.0 | 0 | 59 | - | FAIL |
| 41_module_let | 137 | 7.8 | 2 | 82 | DIFF | PASS |
| 42_module_let_string | 140 | 8.0 | 2 | 84 | DIFF | PASS |
| 43_module_let_math | 142 | 8.1 | 2 | 88 | DIFF | PASS |
| 45_ffi_bind | 169 | 8.5 | 3 | 132 | DIFF | PASS |
| 47_try_operator | 0 | 0.0 | 0 | 110 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 128 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 154 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 48 | - | FAIL |
| 50_match_or_patterns | 196 | 10.4 | 2 | 88 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 26 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 25 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 26 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 31 | - | FAIL |
| 54_const_basic | 0 | 0.0 | 0 | 31 | - | FAIL |
| 55_async_basic | 0 | 0.0 | 0 | 34 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 33 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 33 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 32 | - | FAIL |
| 58_const_scope | 0 | 0.0 | 0 | 29 | - | FAIL |
| 59_async_fanout | 0 | 0.0 | 0 | 29 | - | FAIL |
| 62_list_output | 0 | 0.0 | 0 | 84 | - | FAIL |
| 63_else_sino | 0 | 0.0 | 0 | 87 | - | FAIL |
| 64_closure_typed | 0 | 0.0 | 0 | 26 | - | FAIL |
| 65_list_int_indexing | 226 | 12.2 | 1 | 88 | YES | PASS |
| **Total** | | | | **5278** | **27/65** | **37/65** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 637 | 88 | 7.2x |
| 02_arithmetic | 7 | 106 | 0.1x |
| 03_function | 9 | 153 | 0.1x |
| 04_if_else | 6 | 129 | 0.0x |
| 05_for_loop | 6 | 112 | 0.0x |
| 06_struct | 5 | 85 | 0.1x |
| 07_enum_match | 11 | 83 | 0.1x |
| 08_list | 6 | 92 | 0.1x |
| 09_string_methods | 5 | 76 | 0.1x |
| 10_result | 6 | 108 | 0.1x |
| 11_closure | 5 | 90 | 0.1x |
| 12_while | 4 | 108 | 0.0x |
| 14_nested_struct | 5 | 75 | 0.1x |
| 15_multifunction | 5 | 77 | 0.1x |
| 16_string_escape | 4 | 67 | 0.1x |
| 17_option | 6 | 104 | 0.1x |
| 18_method_chain | 5 | 98 | 0.1x |
| 23_multi_return | 7 | 122 | 0.1x |
| 24_enum_methods | 6 | 107 | 0.1x |
| 25_fizzbuzz | 6 | 99 | 0.1x |
| 26_generics | 8 | 90 | 0.1x |
| 27_impl | 6 | 84 | 0.1x |
| 28_traits | 6 | 82 | 0.1x |
| 30_nested_generics | 5 | 88 | 0.1x |
| 32_generic_enum | 5 | 105 | 0.0x |
| 34_file_io | 6 | 82 | 0.1x |
| 35_stdin | 4 | 74 | 0.1x |
| 36_crypto | 5 | 74 | 0.1x |
| 37_regex | 4 | 83 | 0.1x |
| 38_http | 5 | 98 | 0.0x |
| 39_gpu_detect | 5 | 93 | 0.1x |
| 41_module_let | 4 | 82 | 0.1x |
| 42_module_let_string | 4 | 84 | 0.0x |
| 43_module_let_math | 6 | 88 | 0.1x |
| 45_ffi_bind | 6 | 132 | 0.0x |
| 50_match_or_patterns | 7 | 88 | 0.1x |
| 65_list_int_indexing | 5 | 88 | 0.1x |

