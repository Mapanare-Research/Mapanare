# Mapanare Benchmarks - Linux

Generated: 2026-04-14 06:27 UTC  
Version: 4.108.0 (`ee10998`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 41 | 1.1 | 1 | 2 | 9 | 745 | `~----~~~ v` | PASS |
| 02_arithmetic | 4 | 55 | 1.7 | 1 | 4 | 25 | 8 | `     _   v` | PASS |
| 03_function | 8 | 59 | 1.8 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 8 | 45 | 1.2 | 1 | 4 | 9 | 6 | `         v` | PASS |
| 05_for_loop | 7 | 105 | 3.3 | 1 | 7 | 75 | 7 | `         v` | PASS |
| 06_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 76 | 2.4 | 1 | 5 | 42 | 15 | `         v` | PASS |
| 08_list | 5 | 112 | 4.1 | 1 | 6 | 121 | 8 | `         v` | PASS |
| 09_string_methods | 5 | 97 | 3.5 | 1 | 6 | 51 | 5 | `         v` | PASS |
| 10_result | 14 | 151 | 5.2 | 2 | 10 | 147 | 6 | `         v` | PASS |
| 11_closure | 5 | 111 | 3.7 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 86 | 2.6 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 10 | 121 | 3.5 | 2 | 9 | 106 | 5 | `         v` | PASS |
| 14_nested_struct | 9 | 70 | 2.3 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 87 | 2.8 | 1 | 10 | 50 | 6 | `         v` | PASS |
| 16_string_escape | 8 | 65 | 2.2 | 1 | 2 | 27 | 5 | `-._.~..* ^` | PASS |
| 17_option | 19 | 197 | 6.5 | 2 | 15 | 173 | 7 | `-~-.*.~~` | PASS |
| 18_method_chain | 9 | 133 | 5.1 | 1 | 8 | 84 | 5 | `~-._....` | PASS |
| 19_nested_match | 18 | 208 | 7.1 | 2 | 15 | 186 | 7 | `.-....--` | PASS |
| 20_recursion | 11 | 139 | 4.3 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 15 | 239 | 8.7 | 2 | 13 | 277 | 6 | `~..~..-_ v` | PASS |
| 22_string_builder | 14 | 176 | 6.2 | 2 | 11 | 134 | 6 | `*~---.-. v` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 1 | 8 | 98 | 6 | `-.._.-..` | PASS |
| 24_enum_methods | 20 | 118 | 4.1 | 2 | 8 | 82 | 6 | `         v` | PASS |
| 25_fizzbuzz | 18 | 213 | 6.9 | 2 | 20 | 166 | 5 | `_.._~.~. v` | PASS |
| 26_generics | 29 | 125 | 4.0 | 1 | 12 | 63 | 7 | `         v` | PASS |
| 27_impl | 21 | 77 | 2.2 | 1 | 6 | 50 | 6 | `_.._-_._ v` | PASS |
| 28_traits | 25 | 82 | 2.5 | 1 | 6 | 58 | 6 | `.--.-.-_ v` | PASS |
| 29_generic_impl | 24 | 89 | 2.7 | 1 | 8 | 59 | 7 | `_...._.  v` | PASS |
| 30_nested_generics | 20 | 124 | 4.5 | 1 | 2 | 117 | 6 | `-.____-_ v` | PASS |
| 31_generic_multi | 35 | 129 | 4.2 | 1 | 12 | 93 | 8 | `         v` | PASS |
| 32_generic_enum | 16 | 48 | 1.3 | 1 | 2 | 18 | 6 | `_       ` | PASS |
| 33_break_continue | 58 | 437 | 13.3 | 5 | 36 | 446 | 11 | `         v` | PASS |
| 34_file_io | 19 | 245 | 10.3 | 1 | 12 | 185 | 9 | `         v` | PASS |
| 35_stdin | 4 | 101 | 3.8 | 1 | 8 | 65 | 6 | `._-__-__` | PASS |
| 36_crypto | 13 | 156 | 6.1 | 1 | 12 | 108 | 7 | `~~._.~.- ^` | PASS |
| 37_regex | 10 | 172 | 7.1 | 1 | 8 | 109 | 6 | `*....**. v` | PASS |
| 38_http | 5 | 83 | 3.0 | 1 | 6 | 49 | 6 | `_ __.~__` | PASS |
| 39_gpu_detect | 8 | 153 | 5.8 | 1 | 13 | 100 | 6 | `         v` | PASS |
| 40_gpu_tensor | 18 | 398 | 16.9 | 1 | 25 | 478 | 7 | `_ ______` | PASS |
| 41_module_let | 13 | 54 | 1.5 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 58 | 1.7 | 1 | 4 | 18 | 6 | `_*---___` | PASS |
| 43_module_let_math | 19 | 58 | 1.7 | 1 | 4 | 18 | 5 | `--____  ` | PASS |
| 45_ffi_bind | 15 | 107 | 2.9 | 2 | 9 | 83 | 5 | `__.     ` | PASS |
| 47_try_operator | 32 | 297 | 10.9 | 4 | 23 | 279 | 8 | `         v` | PASS |
| 48_match_nested_exhaustive | 23 | 346 | 13.8 | 3 | 32 | 309 | 6 | `         v` | PASS |
| 49_match_guards | 16 | 214 | 7.1 | 2 | 16 | 169 | 6 | `_*______` | PASS |
| 49_tensor_literal | 58 | 744 | 30.6 | 1 | 48 | 826 | 9 | `_*. ____` | PASS |
| 50_match_or_patterns | 25 | 186 | 6.9 | 2 | 11 | 140 | 6 | ` *. -.__` | PASS |
| 50_tensor_indexing | 46 | 687 | 28.3 | 1 | 34 | 899 | 7 | `_*_-_- _ ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `____-*__` | FAIL |
| 51_tensor_broadcast | 57 | 632 | 26.0 | 1 | 48 | 660 | 7 | `_-..--_. ^` | PASS |
| 52_tensor_slicing | 49 | 668 | 27.7 | 1 | 42 | 750 | 7 | `-*-_--__` | PASS |
| 53_linear_regression | 43 | 399 | 16.2 | 1 | 25 | 413 | 6 | `..*..*..` | PASS |
| 54_const_basic | 12 | 95 | 3.3 | 1 | 6 | 59 | 5 | `_. * ___` | PASS |
| 55_async_basic | 12 | 143 | 5.0 | 2 | 11 | 41 | 4 | `.. * .  ` | PASS |
| 56_async_await | 17 | 232 | 8.3 | 3 | 22 | 73 | 4 | `_-_- -__` | PASS |
| 57_real_await | 28 | 401 | 14.6 | 5 | 44 | 121 | 5 | `.* . *  ` | PASS |
| 58_async_file_io | 28 | 318 | 11.3 | 4 | 34 | 90 | 4 | `_*   _ . ^` | PASS |
| 58_const_scope | 21 | 70 | 2.0 | 1 | 10 | 18 | 6 | `*.*... . ^` | PASS |
| 59_async_fanout | 63 | 1024 | 37.9 | 12 | 121 | 345 | 7 | `-*-__-_- ^` | PASS |
| 62_list_output | 35 | 304 | 14.3 | 2 | 20 | 289 | 7 | `        ` | PASS |
| 63_else_sino | 40 | 268 | 8.8 | 3 | 20 | 250 | 7 | ` *. . . ^` | PASS |
| 64_closure_typed | 25 | 254 | 8.6 | 1 | 22 | 260 | 7 | `_ * _ ^` | PASS |
| **Total** | **1284** | **12869** | **474.0** | **108** | **981** | **10381** | **1144** | | **63/64** |

