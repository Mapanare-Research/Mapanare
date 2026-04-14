# Mapanare Benchmarks - Linux

Generated: 2026-04-14 16:14 UTC  
Version: 4.113.0 (`0860ede`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 6.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 41 | 1.1 | 1 | 2 | 9 | 647 | `~~...--~ ^` | PASS |
| 02_arithmetic | 4 | 55 | 1.7 | 1 | 4 | 25 | 7 | `      _  v` | PASS |
| 03_function | 8 | 59 | 1.8 | 1 | 6 | 25 | 7 | `     *  ` | PASS |
| 04_if_else | 8 | 45 | 1.2 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 105 | 3.3 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 07_enum_match | 13 | 76 | 2.4 | 1 | 5 | 42 | 14 | `         v` | PASS |
| 08_list | 5 | 112 | 4.1 | 1 | 6 | 121 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 97 | 3.5 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 10_result | 14 | 151 | 5.2 | 2 | 10 | 147 | 7 | `        ` | PASS |
| 11_closure | 5 | 111 | 3.7 | 1 | 8 | 89 | 5 | `         ^` | PASS |
| 12_while | 7 | 86 | 2.6 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 10 | 121 | 3.5 | 2 | 9 | 106 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 87 | 2.8 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 65 | 2.2 | 1 | 2 | 27 | 4 | `_   *   ` | PASS |
| 17_option | 19 | 197 | 6.5 | 2 | 15 | 173 | 6 | `~-.....~ ^` | PASS |
| 18_method_chain | 9 | 133 | 5.1 | 1 | 8 | 84 | 5 | `........` | PASS |
| 19_nested_match | 18 | 208 | 7.1 | 2 | 15 | 186 | 6 | `-.__-...` | PASS |
| 20_recursion | 11 | 139 | 4.3 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 15 | 239 | 8.7 | 2 | 13 | 277 | 6 | `_._.__-. v` | PASS |
| 22_string_builder | 14 | 176 | 6.2 | 2 | 11 | 134 | 8 | `.-.~..-~ ^` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 1 | 8 | 98 | 7 | `.._-__..` | PASS |
| 24_enum_methods | 20 | 118 | 4.1 | 2 | 8 | 82 | 7 | `         v` | PASS |
| 25_fizzbuzz | 18 | 213 | 6.9 | 2 | 20 | 166 | 8 | `.__._.._ v` | PASS |
| 26_generics | 29 | 125 | 4.0 | 1 | 12 | 63 | 8 | `        ` | PASS |
| 27_impl | 21 | 77 | 2.2 | 1 | 6 | 50 | 11 | `_______. ^` | PASS |
| 28_traits | 25 | 82 | 2.5 | 1 | 6 | 58 | 8 | `_._---.- ^` | PASS |
| 29_generic_impl | 24 | 89 | 2.7 | 1 | 8 | 59 | 7 | ` ._.._._ v` | PASS |
| 30_nested_generics | 20 | 124 | 4.5 | 1 | 2 | 117 | 7 | `_._~__-_ v` | PASS |
| 31_generic_multi | 35 | 129 | 4.2 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 48 | 1.3 | 1 | 2 | 18 | 4 | ` _ _   _ ^` | PASS |
| 33_break_continue | 58 | 437 | 13.3 | 5 | 36 | 446 | 9 | `         v` | PASS |
| 34_file_io | 19 | 245 | 10.3 | 1 | 12 | 185 | 5 | `         v` | PASS |
| 35_stdin | 4 | 101 | 3.8 | 1 | 8 | 65 | 4 | `_-.._*-. v` | PASS |
| 36_crypto | 13 | 156 | 6.1 | 1 | 12 | 108 | 5 | `-~.._...` | PASS |
| 37_regex | 10 | 172 | 7.1 | 1 | 8 | 109 | 6 | `.*.....* ^` | PASS |
| 38_http | 5 | 83 | 3.0 | 1 | 6 | 49 | 4 | `_. _  _  v` | PASS |
| 39_gpu_detect | 8 | 153 | 5.8 | 1 | 13 | 100 | 4 | `         v` | PASS |
| 40_gpu_tensor | 18 | 398 | 16.9 | 1 | 25 | 478 | 8 | `__    .  v` | PASS |
| 41_module_let | 13 | 54 | 1.5 | 1 | 4 | 18 | 6 | `        ` | PASS |
| 42_module_let_string | 19 | 58 | 1.7 | 1 | 4 | 18 | 6 | `_*-*_--* ^` | PASS |
| 43_module_let_math | 19 | 58 | 1.7 | 1 | 4 | 18 | 6 | ` _____-_ v` | PASS |
| 45_ffi_bind | 15 | 107 | 2.9 | 2 | 9 | 83 | 7 | `      .  v` | PASS |
| 47_try_operator | 32 | 297 | 10.9 | 4 | 23 | 279 | 7 | `         v` | PASS |
| 48_match_nested_exhaustive | 23 | 346 | 13.8 | 3 | 32 | 309 | 8 | `         ^` | PASS |
| 49_match_guards | 16 | 214 | 7.1 | 2 | 16 | 169 | 6 | `___ __*- v` | PASS |
| 49_tensor_literal | 58 | 744 | 30.6 | 1 | 48 | 826 | 10 | `_ ______` | PASS |
| 50_match_or_patterns | 25 | 186 | 6.9 | 2 | 11 | 140 | 6 | `__ ____  v` | PASS |
| 50_tensor_indexing | 46 | 687 | 28.3 | 1 | 34 | 899 | 8 | `_   ___  v` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 5 | `_ _ ___  v` | FAIL |
| 51_tensor_broadcast | 57 | 632 | 26.0 | 1 | 48 | 660 | 8 | `._._.___` | PASS |
| 52_tensor_slicing | 49 | 668 | 27.7 | 1 | 42 | 750 | 8 | `__**---_ v` | PASS |
| 53_linear_regression | 43 | 399 | 16.2 | 1 | 25 | 413 | 7 | `___*____` | PASS |
| 54_const_basic | 12 | 95 | 3.3 | 1 | 6 | 59 | 5 | `__*._ __` | PASS |
| 55_async_basic | 12 | 143 | 5.0 | 2 | 11 | 41 | 5 | `  ..  *. v` | PASS |
| 56_async_await | 17 | 232 | 8.3 | 3 | 22 | 73 | 4 | `_  ___-_ v` | PASS |
| 57_real_await | 28 | 401 | 14.6 | 5 | 44 | 121 | 5 | `   .  *. v` | PASS |
| 58_async_file_io | 28 | 318 | 11.3 | 4 | 34 | 90 | 5 | `- ____--` | PASS |
| 58_const_scope | 21 | 70 | 2.0 | 1 | 10 | 18 | 5 | `..  . ..` | PASS |
| 59_async_fanout | 63 | 1024 | 37.9 | 12 | 121 | 345 | 6 | `-_ __ __` | PASS |
| 62_list_output | 35 | 304 | 14.3 | 2 | 20 | 289 | 7 | `        ` | PASS |
| 63_else_sino | 40 | 268 | 8.8 | 3 | 20 | 250 | 6 | `__* *_  ` | PASS |
| 64_closure_typed | 25 | 254 | 8.6 | 1 | 22 | 260 | 7 | `_ _ __._ v` | PASS |
| **Total** | **1284** | **12869** | **474.0** | **108** | **981** | **10381** | **1042** | | **63/64** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 132 | 7.8 | 1 | 139 | YES | PASS |
| 02_arithmetic | 137 | 7.8 | 1 | 132 | YES | PASS |
| 03_function | 147 | 8.0 | 2 | 135 | DIFF | PASS |
| 04_if_else | 149 | 8.3 | 1 | 105 | YES | PASS |
| 05_for_loop | 160 | 8.7 | 1 | 86 | YES | PASS |
| 06_struct | 142 | 8.0 | 1 | 80 | YES | PASS |
| 07_enum_match | 154 | 8.6 | 1 | 86 | YES | PASS |
| 08_list | 164 | 9.1 | 1 | 97 | YES | PASS |
| 09_string_methods | 145 | 8.4 | 1 | 87 | YES | PASS |
| 10_result | 189 | 10.0 | 2 | 97 | YES | PASS |
| 11_closure | 150 | 8.1 | 1 | 108 | YES | PASS |
| 12_while | 146 | 8.0 | 1 | 74 | YES | PASS |
| 13_fib | 0 | 0.0 | 0 | 72 | - | FAIL |
| 14_nested_struct | 142 | 8.0 | 1 | 67 | YES | PASS |
| 15_multifunction | 155 | 8.2 | 3 | 73 | DIFF | PASS |
| 16_string_escape | 151 | 8.7 | 1 | 67 | YES | PASS |
| 17_option | 215 | 10.7 | 2 | 97 | YES | PASS |
| 18_method_chain | 162 | 9.2 | 1 | 84 | YES | PASS |
| 19_nested_match | 0 | 0.0 | 0 | 94 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 86 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 107 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 135 | - | FAIL |
| 23_multi_return | 166 | 8.9 | 2 | 96 | DIFF | PASS |
| 24_enum_methods | 178 | 9.4 | 2 | 121 | YES | PASS |
| 25_fizzbuzz | 207 | 10.1 | 2 | 135 | YES | PASS |
| 26_generics | 204 | 10.0 | 5 | 128 | DIFF | PASS |
| 27_impl | 165 | 8.8 | 3 | 138 | DIFF | PASS |
| 28_traits | 170 | 8.8 | 3 | 124 | DIFF | PASS |
| 29_generic_impl | 0 | 0.0 | 0 | 120 | - | FAIL |
| 30_nested_generics | 172 | 9.8 | 1 | 109 | YES | PASS |
| 31_generic_multi | 0 | 0.0 | 0 | 90 | - | FAIL |
| 32_generic_enum | 149 | 8.3 | 1 | 66 | YES | PASS |
| 33_break_continue | 0 | 0.0 | 0 | 63 | - | FAIL |
| 34_file_io | 200 | 11.4 | 1 | 70 | YES | PASS |
| 35_stdin | 142 | 8.3 | 1 | 97 | YES | PASS |
| 36_crypto | 161 | 9.3 | 1 | 100 | YES | PASS |
| 37_regex | 182 | 10.4 | 1 | 79 | YES | PASS |
| 38_http | 138 | 8.1 | 1 | 79 | YES | PASS |
| 39_gpu_detect | 155 | 8.8 | 1 | 90 | YES | PASS |
| 40_gpu_tensor | 0 | 0.0 | 0 | 89 | - | FAIL |
| 41_module_let | 137 | 7.8 | 2 | 125 | DIFF | PASS |
| 42_module_let_string | 140 | 8.0 | 2 | 102 | DIFF | PASS |
| 43_module_let_math | 142 | 8.1 | 2 | 107 | DIFF | PASS |
| 45_ffi_bind | 169 | 8.5 | 3 | 111 | DIFF | PASS |
| 47_try_operator | 0 | 0.0 | 0 | 111 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 81 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 78 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 32 | - | FAIL |
| 50_match_or_patterns | 196 | 10.4 | 2 | 107 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 42 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 45 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 41 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 39 | - | FAIL |
| 54_const_basic | 0 | 0.0 | 0 | 33 | - | FAIL |
| 55_async_basic | 0 | 0.0 | 0 | 32 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 28 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 26 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 25 | - | FAIL |
| 58_const_scope | 0 | 0.0 | 0 | 25 | - | FAIL |
| 59_async_fanout | 0 | 0.0 | 0 | 27 | - | FAIL |
| 62_list_output | 0 | 0.0 | 0 | 84 | - | FAIL |
| 63_else_sino | 0 | 0.0 | 0 | 93 | - | FAIL |
| 64_closure_typed | 0 | 0.0 | 0 | 28 | - | FAIL |
| **Total** | | | | **5322** | **26/64** | **36/64** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 647 | 139 | 4.7x |
| 02_arithmetic | 7 | 132 | 0.1x |
| 03_function | 7 | 135 | 0.1x |
| 04_if_else | 6 | 105 | 0.1x |
| 05_for_loop | 5 | 86 | 0.1x |
| 06_struct | 5 | 80 | 0.1x |
| 07_enum_match | 14 | 86 | 0.2x |
| 08_list | 6 | 97 | 0.1x |
| 09_string_methods | 4 | 87 | 0.1x |
| 10_result | 7 | 97 | 0.1x |
| 11_closure | 5 | 108 | 0.0x |
| 12_while | 4 | 74 | 0.1x |
| 14_nested_struct | 4 | 67 | 0.1x |
| 15_multifunction | 5 | 73 | 0.1x |
| 16_string_escape | 4 | 67 | 0.1x |
| 17_option | 6 | 97 | 0.1x |
| 18_method_chain | 5 | 84 | 0.1x |
| 23_multi_return | 7 | 96 | 0.1x |
| 24_enum_methods | 7 | 121 | 0.1x |
| 25_fizzbuzz | 8 | 135 | 0.1x |
| 26_generics | 8 | 128 | 0.1x |
| 27_impl | 11 | 138 | 0.1x |
| 28_traits | 8 | 124 | 0.1x |
| 30_nested_generics | 7 | 109 | 0.1x |
| 32_generic_enum | 4 | 66 | 0.1x |
| 34_file_io | 5 | 70 | 0.1x |
| 35_stdin | 4 | 97 | 0.0x |
| 36_crypto | 5 | 100 | 0.0x |
| 37_regex | 6 | 79 | 0.1x |
| 38_http | 4 | 79 | 0.1x |
| 39_gpu_detect | 4 | 90 | 0.0x |
| 41_module_let | 6 | 125 | 0.1x |
| 42_module_let_string | 6 | 102 | 0.1x |
| 43_module_let_math | 6 | 107 | 0.1x |
| 45_ffi_bind | 7 | 111 | 0.1x |
| 50_match_or_patterns | 6 | 107 | 0.1x |

