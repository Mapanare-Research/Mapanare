# Mapanare Benchmarks - Linux

Generated: 2026-04-13 21:25 UTC  
Version: 4.97.0 (`e701e6e`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 5.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 41 | 1.1 | 1 | 2 | 9 | 740 | `~-.--.-- ^` | PASS |
| 02_arithmetic | 4 | 55 | 1.7 | 1 | 4 | 25 | 6 | `        ` | PASS |
| 03_function | 8 | 59 | 1.8 | 1 | 6 | 25 | 6 | `        ` | PASS |
| 04_if_else | 8 | 45 | 1.2 | 1 | 4 | 9 | 5 | `         ^` | PASS |
| 05_for_loop | 7 | 105 | 3.3 | 1 | 7 | 75 | 6 | `         ^` | PASS |
| 06_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 6 | `        ` | PASS |
| 07_enum_match | 13 | 76 | 2.4 | 1 | 5 | 42 | 13 | `        ` | PASS |
| 08_list | 5 | 112 | 4.1 | 1 | 6 | 121 | 8 | `        ` | PASS |
| 09_string_methods | 5 | 97 | 3.5 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 151 | 5.2 | 2 | 10 | 147 | 7 | `         ^` | PASS |
| 11_closure | 5 | 111 | 3.7 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 86 | 2.6 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 121 | 3.5 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 87 | 2.8 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 65 | 2.2 | 1 | 2 | 27 | 4 | `._______` | PASS |
| 17_option | 19 | 197 | 6.5 | 2 | 15 | 173 | 5 | `...__-..` | PASS |
| 18_method_chain | 9 | 133 | 5.1 | 1 | 8 | 84 | 5 | `....___. ^` | PASS |
| 19_nested_match | 18 | 208 | 7.1 | 2 | 15 | 186 | 6 | `__-.___. ^` | PASS |
| 20_recursion | 11 | 139 | 4.3 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 15 | 239 | 8.7 | 2 | 13 | 277 | 6 | `_______. ^` | PASS |
| 22_string_builder | 14 | 159 | 5.7 | 2 | 11 | 124 | 5 | `._--...- ^` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 1 | 8 | 98 | 6 | `_ __-___` | PASS |
| 24_enum_methods | 20 | 118 | 4.1 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 213 | 6.9 | 2 | 20 | 166 | 5 | `__*____. ^` | PASS |
| 26_generics | 29 | 125 | 4.0 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 77 | 2.2 | 1 | 6 | 50 | 6 | `       _ ^` | PASS |
| 28_traits | 25 | 82 | 2.5 | 1 | 6 | 58 | 6 | `_ _____. ^` | PASS |
| 29_generic_impl | 24 | 89 | 2.7 | 1 | 8 | 59 | 6 | ` _ _  __` | PASS |
| 30_nested_generics | 20 | 124 | 4.5 | 1 | 2 | 117 | 5 | ` _ .___. ^` | PASS |
| 31_generic_multi | 35 | 129 | 4.2 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 16 | 48 | 1.3 | 1 | 2 | 18 | 5 | `         v` | PASS |
| 33_break_continue | 58 | 437 | 13.3 | 5 | 36 | 446 | 12 | `        ` | PASS |
| 34_file_io | 19 | 245 | 10.3 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 101 | 3.8 | 1 | 8 | 65 | 5 | `  ____ - ^` | PASS |
| 36_crypto | 13 | 156 | 6.1 | 1 | 12 | 108 | 5 | `._._.___` | PASS |
| 37_regex | 10 | 172 | 7.1 | 1 | 8 | 109 | 5 | ` . .....` | PASS |
| 38_http | 5 | 83 | 3.0 | 1 | 6 | 49 | 5 | `       _ ^` | PASS |
| 39_gpu_detect | 8 | 153 | 5.8 | 1 | 13 | 100 | 6 | `         v` | PASS |
| 40_gpu_tensor | 18 | 398 | 16.9 | 1 | 25 | 478 | 7 | `        ` | PASS |
| 41_module_let | 13 | 54 | 1.5 | 1 | 4 | 18 | 5 | `         ^` | PASS |
| 42_module_let_string | 19 | 58 | 1.7 | 1 | 4 | 18 | 5 | `......**` | PASS |
| 43_module_let_math | 19 | 58 | 1.7 | 1 | 4 | 18 | 5 | `.     .* ^` | PASS |
| 45_ffi_bind | 15 | 107 | 2.9 | 2 | 9 | 83 | 9 | `........` | PASS |
| 47_try_operator | 32 | 297 | 10.9 | 4 | 23 | 279 | 12 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 346 | 13.8 | 3 | 32 | 309 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 214 | 7.1 | 2 | 16 | 169 | 5 | `. ..  .* ^` | PASS |
| 49_tensor_literal | 58 | 744 | 30.6 | 1 | 48 | 826 | 10 | `   . *..` | PASS |
| 50_match_or_patterns | 25 | 186 | 6.9 | 2 | 11 | 140 | 6 | `*  .   . ^` | PASS |
| 50_tensor_indexing | 46 | 687 | 28.3 | 1 | 34 | 899 | 8 | `  **  **` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 4 | `***    * ^` | FAIL |
| 51_tensor_broadcast | 57 | 632 | 26.0 | 1 | 48 | 660 | 8 | `....* . ^` | PASS |
| 52_tensor_slicing | 49 | 668 | 27.7 | 1 | 42 | 750 | 8 | `..* . . ^` | PASS |
| 53_linear_regression | 43 | 399 | 16.2 | 1 | 25 | 413 | 6 | ` ** ***` | PASS |
| 54_const_basic | 12 | 95 | 3.3 | 1 | 6 | 59 | 5 | `    ` | PASS |
| 55_async_basic | 12 | 145 | 5.2 | 2 | 11 | 41 | 5 | `  ` | PASS |
| 56_async_await | 17 | 234 | 8.4 | 3 | 22 | 73 | 5 | ` * ^` | PASS |
| 57_real_await | 28 | 403 | 14.7 | 5 | 44 | 121 | 6 | `  ` | PASS |
| 58_async_file_io | 28 | 320 | 11.4 | 4 | 34 | 90 | 5 | ` * ^` | PASS |
| 58_const_scope | 21 | 70 | 2.0 | 1 | 10 | 18 | 5 | `  ` | PASS |
| 59_async_fanout | 63 | 1026 | 38.0 | 12 | 121 | 345 | 7 | `  ` | PASS |
| **Total** | **1184** | **12036** | **442.4** | **102** | **919** | **9572** | **1103** | | **60/61** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 132 | 8.2 | 0 | 78 | - | FAIL |
| 02_arithmetic | 152 | 8.6 | 0 | 89 | - | FAIL |
| 03_function | 147 | 8.9 | 0 | 87 | - | FAIL |
| 04_if_else | 149 | 8.5 | 0 | 107 | - | FAIL |
| 05_for_loop | 0 | 0.0 | 0 | 92 | - | FAIL |
| 06_struct | 0 | 0.0 | 0 | 41 | - | FAIL |
| 07_enum_match | 154 | 9.7 | 0 | 94 | - | FAIL |
| 08_list | 161 | 9.2 | 0 | 102 | - | FAIL |
| 09_string_methods | 160 | 9.0 | 0 | 110 | - | FAIL |
| 10_result | 189 | 10.3 | 0 | 107 | - | FAIL |
| 11_closure | 146 | 9.4 | 0 | 90 | - | FAIL |
| 12_while | 0 | 0.0 | 0 | 75 | - | FAIL |
| 13_fib | 0 | 0.0 | 0 | 86 | - | FAIL |
| 14_nested_struct | 0 | 0.0 | 0 | 30 | - | FAIL |
| 15_multifunction | 0 | 0.0 | 0 | 76 | - | FAIL |
| 16_string_escape | 151 | 9.5 | 0 | 79 | - | FAIL |
| 17_option | 0 | 0.0 | 0 | 83 | - | FAIL |
| 18_method_chain | 163 | 9.5 | 0 | 81 | - | FAIL |
| 19_nested_match | 0 | 0.0 | 0 | 99 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 112 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 82 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 82 | - | FAIL |
| 23_multi_return | 0 | 0.0 | 0 | 32 | - | FAIL |
| 24_enum_methods | 0 | 0.0 | 0 | 87 | - | FAIL |
| 25_fizzbuzz | 0 | 0.0 | 0 | 91 | - | FAIL |
| 26_generics | 0 | 0.0 | 0 | 37 | - | FAIL |
| 27_impl | 0 | 0.0 | 0 | 37 | - | FAIL |
| 28_traits | 0 | 0.0 | 0 | 38 | - | FAIL |
| 29_generic_impl | 0 | 0.0 | 0 | 33 | - | FAIL |
| 30_nested_generics | 0 | 0.0 | 0 | 34 | - | FAIL |
| 31_generic_multi | 0 | 0.0 | 0 | 37 | - | FAIL |
| 32_generic_enum | 164 | 8.7 | 0 | 107 | - | FAIL |
| 33_break_continue | 0 | 0.0 | 0 | 78 | - | FAIL |
| 34_file_io | 200 | 12.2 | 0 | 91 | - | FAIL |
| 35_stdin | 142 | 8.9 | 0 | 90 | - | FAIL |
| 36_crypto | 187 | 10.1 | 0 | 96 | - | FAIL |
| 37_regex | 183 | 10.9 | 0 | 96 | - | FAIL |
| 38_http | 138 | 9.0 | 0 | 96 | - | FAIL |
| 39_gpu_detect | 155 | 9.4 | 0 | 102 | - | FAIL |
| 40_gpu_tensor | 0 | 0.0 | 0 | 59 | - | FAIL |
| 41_module_let | 135 | 8.3 | 0 | 82 | - | FAIL |
| 42_module_let_string | 135 | 8.6 | 0 | 77 | - | FAIL |
| 43_module_let_math | 143 | 9.0 | 0 | 132 | - | FAIL |
| 45_ffi_bind | 0 | 0.0 | 0 | 157 | - | FAIL |
| 47_try_operator | 0 | 0.0 | 0 | 126 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 92 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 84 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 36 | - | FAIL |
| 50_match_or_patterns | 0 | 0.0 | 0 | 94 | - | FAIL |
| 50_tensor_indexing | 0 | 0.0 | 0 | 36 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 31 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 32 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 33 | - | FAIL |
| 54_const_basic | 0 | 0.0 | 0 | 31 | - | FAIL |
| 55_async_basic | 0 | 0.0 | 0 | 32 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 31 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 38 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 31 | - | FAIL |
| 58_const_scope | 0 | 0.0 | 0 | 32 | - | FAIL |
| 59_async_fanout | 0 | 0.0 | 0 | 31 | - | FAIL |
| **Total** | | | | **4361** | **0/61** | **0/61** |

