# Mapanare Benchmarks - Linux

Generated: 2026-04-14 04:53 UTC  
Version: 4.105.0 (`9c77e46`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 7.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 41 | 1.1 | 1 | 2 | 9 | 787 | `-.~----~ ^` | PASS |
| 02_arithmetic | 4 | 55 | 1.7 | 1 | 4 | 25 | 8 | `       _ ^` | PASS |
| 03_function | 8 | 59 | 1.8 | 1 | 6 | 25 | 7 | `         ^` | PASS |
| 04_if_else | 8 | 45 | 1.2 | 1 | 4 | 9 | 7 | `        ` | PASS |
| 05_for_loop | 7 | 105 | 3.3 | 1 | 7 | 75 | 7 | `         ^` | PASS |
| 06_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 7 | `        ` | PASS |
| 07_enum_match | 13 | 76 | 2.4 | 1 | 5 | 42 | 25 | `         ^` | PASS |
| 08_list | 5 | 112 | 4.1 | 1 | 6 | 121 | 7 | `         ^` | PASS |
| 09_string_methods | 5 | 97 | 3.5 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 151 | 5.2 | 2 | 10 | 147 | 7 | `        ` | PASS |
| 11_closure | 5 | 111 | 3.7 | 1 | 8 | 89 | 6 | `        ` | PASS |
| 12_while | 7 | 86 | 2.6 | 1 | 7 | 58 | 7 | `         ^` | PASS |
| 13_fib | 10 | 121 | 3.5 | 2 | 9 | 106 | 6 | `         ^` | PASS |
| 14_nested_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 87 | 2.8 | 1 | 10 | 50 | 7 | `         v` | PASS |
| 16_string_escape | 8 | 65 | 2.2 | 1 | 2 | 27 | 5 | `.*-._.*. v` | PASS |
| 17_option | 19 | 197 | 6.5 | 2 | 15 | 173 | 8 | `.~-~-.*. v` | PASS |
| 18_method_chain | 9 | 133 | 5.1 | 1 | 8 | 84 | 5 | `_-~-._..` | PASS |
| 19_nested_match | 18 | 208 | 7.1 | 2 | 15 | 186 | 8 | `_..-....` | PASS |
| 20_recursion | 11 | 139 | 4.3 | 2 | 11 | 123 | 6 | `        ` | PASS |
| 21_list_ops | 15 | 239 | 8.7 | 2 | 13 | 277 | 7 | `..~..~..` | PASS |
| 22_string_builder | 14 | 159 | 5.7 | 2 | 11 | 124 | 6 | `..*~---. v` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 1 | 8 | 98 | 6 | `---.._.- ^` | PASS |
| 24_enum_methods | 20 | 118 | 4.1 | 2 | 8 | 82 | 7 | `         v` | PASS |
| 25_fizzbuzz | 18 | 213 | 6.9 | 2 | 20 | 166 | 8 | `.._.._~. v` | PASS |
| 26_generics | 29 | 125 | 4.0 | 1 | 12 | 63 | 8 | `         v` | PASS |
| 27_impl | 21 | 77 | 2.2 | 1 | 6 | 50 | 8 | `_._.._-_ v` | PASS |
| 28_traits | 25 | 82 | 2.5 | 1 | 6 | 58 | 7 | `.~.--.-. v` | PASS |
| 29_generic_impl | 24 | 89 | 2.7 | 1 | 8 | 59 | 7 | `___...._ v` | PASS |
| 30_nested_generics | 20 | 124 | 4.5 | 1 | 2 | 117 | 7 | `.--.____` | PASS |
| 31_generic_multi | 35 | 129 | 4.2 | 1 | 12 | 93 | 8 | `        ` | PASS |
| 32_generic_enum | 16 | 48 | 1.3 | 1 | 2 | 18 | 5 | ` __     ` | PASS |
| 33_break_continue | 58 | 437 | 13.3 | 5 | 36 | 446 | 10 | `        ` | PASS |
| 34_file_io | 19 | 245 | 10.3 | 1 | 12 | 185 | 7 | `         v` | PASS |
| 35_stdin | 4 | 101 | 3.8 | 1 | 8 | 65 | 4 | `_.._-__- ^` | PASS |
| 36_crypto | 13 | 156 | 6.1 | 1 | 12 | 108 | 5 | `.~~~._.~ ^` | PASS |
| 37_regex | 10 | 172 | 7.1 | 1 | 8 | 109 | 6 | ` .*....* ^` | PASS |
| 38_http | 5 | 83 | 3.0 | 1 | 6 | 49 | 5 | `_ _ __.~ ^` | PASS |
| 39_gpu_detect | 8 | 153 | 5.8 | 1 | 13 | 100 | 8 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 398 | 16.9 | 1 | 25 | 478 | 7 | `___ ____ v` | PASS |
| 41_module_let | 13 | 54 | 1.5 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 58 | 1.7 | 1 | 4 | 18 | 4 | `-*_*---_ v` | PASS |
| 43_module_let_math | 19 | 58 | 1.7 | 1 | 4 | 18 | 4 | `_---____` | PASS |
| 45_ffi_bind | 15 | 107 | 2.9 | 2 | 9 | 83 | 5 | ` .__.   ` | PASS |
| 47_try_operator | 32 | 297 | 10.9 | 4 | 23 | 279 | 8 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 346 | 13.8 | 3 | 32 | 309 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 214 | 7.1 | 2 | 16 | 169 | 6 | `_*_*____` | PASS |
| 49_tensor_literal | 58 | 744 | 30.6 | 1 | 48 | 826 | 10 | `___*. __` | PASS |
| 50_match_or_patterns | 25 | 186 | 6.9 | 2 | 11 | 140 | 6 | `-_ *. -. v` | PASS |
| 50_tensor_indexing | 46 | 687 | 28.3 | 1 | 34 | 899 | 7 | `___*_-_- ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | `______-* ^` | FAIL |
| 51_tensor_broadcast | 57 | 632 | 26.0 | 1 | 48 | 660 | 7 | `.._-..--` | PASS |
| 52_tensor_slicing | 49 | 668 | 27.7 | 1 | 42 | 750 | 7 | `_--*-_--` | PASS |
| 53_linear_regression | 43 | 399 | 16.2 | 1 | 25 | 413 | 6 | `....*..* ^` | PASS |
| 54_const_basic | 12 | 95 | 3.3 | 1 | 6 | 59 | 5 | `___. * _ ^` | PASS |
| 55_async_basic | 12 | 143 | 5.0 | 2 | 11 | 41 | 4 | `.... * . ^` | PASS |
| 56_async_await | 17 | 232 | 8.3 | 3 | 22 | 73 | 5 | `_*_-_- - ^` | PASS |
| 57_real_await | 28 | 401 | 14.6 | 5 | 44 | 121 | 5 | `  .* . * ^` | PASS |
| 58_async_file_io | 28 | 318 | 11.3 | 4 | 34 | 90 | 5 | `_ _*   _ ^` | PASS |
| 58_const_scope | 21 | 70 | 2.0 | 1 | 10 | 18 | 5 | `..*.*...` | PASS |
| 59_async_fanout | 63 | 1024 | 37.9 | 12 | 121 | 345 | 7 | `---*-__- ^` | PASS |
| 62_list_output | 35 | 304 | 14.3 | 2 | 20 | 289 | 8 | `         ^` | PASS |
| 63_else_sino | 40 | 268 | 8.8 | 3 | 20 | 250 | 6 | ` *. . ^` | PASS |
| 64_closure_typed | 25 | 254 | 8.6 | 1 | 22 | 260 | 7 | `_ * ^` | PASS |
| **Total** | **1284** | **12852** | **473.5** | **108** | **981** | **10371** | **1209** | | **63/64** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 132 | 7.8 | 1 | 121 | YES | PASS |
| 02_arithmetic | 137 | 7.8 | 1 | 122 | YES | PASS |
| 03_function | 0 | 0.0 | 0 | 123 | - | FAIL |
| 04_if_else | 149 | 8.3 | 1 | 133 | YES | PASS |
| 05_for_loop | 0 | 0.0 | 0 | 129 | - | FAIL |
| 06_struct | 142 | 8.0 | 1 | 153 | YES | PASS |
| 07_enum_match | 154 | 8.6 | 1 | 137 | YES | PASS |
| 08_list | 164 | 9.1 | 1 | 106 | YES | PASS |
| 09_string_methods | 145 | 8.4 | 1 | 103 | YES | PASS |
| 10_result | 189 | 10.0 | 2 | 150 | YES | PASS |
| 11_closure | 0 | 0.0 | 0 | 119 | - | FAIL |
| 12_while | 146 | 8.0 | 1 | 128 | YES | PASS |
| 13_fib | 0 | 0.0 | 0 | 129 | - | FAIL |
| 14_nested_struct | 142 | 8.0 | 1 | 109 | YES | PASS |
| 15_multifunction | 0 | 0.0 | 0 | 104 | - | FAIL |
| 16_string_escape | 151 | 8.7 | 1 | 97 | YES | PASS |
| 17_option | 215 | 10.7 | 2 | 137 | YES | PASS |
| 18_method_chain | 162 | 9.2 | 1 | 105 | YES | PASS |
| 19_nested_match | 0 | 0.0 | 0 | 145 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 102 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 75 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 77 | - | FAIL |
| 23_multi_return | 0 | 0.0 | 0 | 75 | - | FAIL |
| 24_enum_methods | 0 | 0.0 | 0 | 139 | - | FAIL |
| 25_fizzbuzz | 0 | 0.0 | 0 | 132 | - | FAIL |
| 26_generics | 0 | 0.0 | 0 | 98 | - | FAIL |
| 27_impl | 0 | 0.0 | 0 | 115 | - | FAIL |
| 28_traits | 0 | 0.0 | 0 | 110 | - | FAIL |
| 29_generic_impl | 0 | 0.0 | 0 | 102 | - | FAIL |
| 30_nested_generics | 172 | 9.8 | 1 | 110 | YES | PASS |
| 31_generic_multi | 0 | 0.0 | 0 | 95 | - | FAIL |
| 32_generic_enum | 149 | 8.3 | 1 | 105 | YES | PASS |
| 33_break_continue | 0 | 0.0 | 0 | 109 | - | FAIL |
| 34_file_io | 200 | 11.4 | 1 | 106 | YES | PASS |
| 35_stdin | 142 | 8.3 | 1 | 89 | YES | PASS |
| 36_crypto | 161 | 9.3 | 1 | 91 | YES | PASS |
| 37_regex | 182 | 10.4 | 1 | 108 | YES | PASS |
| 38_http | 138 | 8.1 | 1 | 152 | YES | PASS |
| 39_gpu_detect | 155 | 8.8 | 1 | 150 | YES | PASS |
| 40_gpu_tensor | 0 | 0.0 | 0 | 55 | - | FAIL |
| 41_module_let | 0 | 0.0 | 0 | 63 | - | FAIL |
| 42_module_let_string | 0 | 0.0 | 0 | 57 | - | FAIL |
| 43_module_let_math | 0 | 0.0 | 0 | 58 | - | FAIL |
| 45_ffi_bind | 0 | 0.0 | 0 | 76 | - | FAIL |
| 47_try_operator | 0 | 0.0 | 0 | 146 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 97 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 103 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 37 | - | FAIL |
| 50_match_or_patterns | 0 | 0.0 | 0 | 104 | - | FAIL |
| 50_tensor_indexing | 0 | 0.0 | 0 | 31 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 29 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 27 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 29 | - | FAIL |
| 54_const_basic | 0 | 0.0 | 0 | 26 | - | FAIL |
| 55_async_basic | 0 | 0.0 | 0 | 28 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 29 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 30 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 31 | - | FAIL |
| 58_const_scope | 0 | 0.0 | 0 | 33 | - | FAIL |
| 59_async_fanout | 0 | 0.0 | 0 | 35 | - | FAIL |
| 62_list_output | 0 | 0.0 | 0 | 94 | - | FAIL |
| 63_else_sino | 0 | 0.0 | 0 | 82 | - | FAIL |
| 64_closure_typed | 0 | 0.0 | 0 | 36 | - | FAIL |
| **Total** | | | | **5824** | **21/64** | **21/64** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 787 | 121 | 6.5x |
| 02_arithmetic | 8 | 122 | 0.1x |
| 04_if_else | 7 | 133 | 0.0x |
| 06_struct | 7 | 153 | 0.0x |
| 07_enum_match | 25 | 137 | 0.2x |
| 08_list | 7 | 106 | 0.1x |
| 09_string_methods | 5 | 103 | 0.1x |
| 10_result | 7 | 150 | 0.0x |
| 12_while | 7 | 128 | 0.1x |
| 14_nested_struct | 5 | 109 | 0.0x |
| 16_string_escape | 5 | 97 | 0.1x |
| 17_option | 8 | 137 | 0.1x |
| 18_method_chain | 5 | 105 | 0.1x |
| 30_nested_generics | 7 | 110 | 0.1x |
| 32_generic_enum | 5 | 105 | 0.0x |
| 34_file_io | 7 | 106 | 0.1x |
| 35_stdin | 4 | 89 | 0.0x |
| 36_crypto | 5 | 91 | 0.1x |
| 37_regex | 6 | 108 | 0.1x |
| 38_http | 5 | 152 | 0.0x |
| 39_gpu_detect | 8 | 150 | 0.1x |

