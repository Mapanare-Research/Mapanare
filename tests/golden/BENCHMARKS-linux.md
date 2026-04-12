# Mapanare Benchmarks - Linux

Generated: 2026-04-12 04:29 UTC  
Version: 4.33.0 (`6f789fc`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 578 | `.._.-... v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `        ` | PASS |
| 03_function | 8 | 73 | 2.2 | 2 | 6 | 65 | 6 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 4 | `         v` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 5 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.3 | 1 | 6 | 51 | 4 | `         v` | PASS |
| 10_result | 14 | 142 | 5.0 | 2 | 10 | 147 | 5 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.4 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 118 | 3.6 | 3 | 10 | 114 | 4 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `..___.__` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 6 | `.....___` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `__.-____` | PASS |
| 19_nested_match | 18 | 199 | 6.8 | 2 | 15 | 186 | 6 | `__..__._ v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         v` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `___.__ _ ^` | PASS |
| 22_string_builder | 14 | 132 | 4.7 | 2 | 7 | 124 | 4 | `........` | PASS |
| 23_multi_return | 15 | 119 | 4.2 | 2 | 8 | 114 | 4 | ` _  __ _ ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.8 | 2 | 8 | 82 | 4 | `        ` | PASS |
| 25_fizzbuzz | 18 | 186 | 5.9 | 2 | 16 | 166 | 5 | `_______  v` | PASS |
| 26_generics | 29 | 167 | 5.3 | 5 | 12 | 129 | 5 | `        ` | PASS |
| 27_impl | 21 | 99 | 2.8 | 3 | 6 | 106 | 5 | `      __` | PASS |
| 28_traits | 25 | 98 | 2.8 | 3 | 6 | 98 | 5 | `________` | PASS |
| 29_generic_impl | 24 | 101 | 3.1 | 3 | 6 | 99 | 5 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 4 | `.__ ____` | PASS |
| 31_generic_multi | 35 | 145 | 4.7 | 4 | 8 | 141 | 5 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 428 | 13.1 | 5 | 36 | 446 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 3 | `________` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `___..___` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `    ...  v` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `__.____  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 5 | `     _  ` | PASS |
| 41_module_let | 13 | 53 | 1.5 | 2 | 4 | 26 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 57 | 1.7 | 2 | 4 | 26 | 4 | `. ......` | PASS |
| 43_module_let_math | 19 | 57 | 1.7 | 2 | 4 | 26 | 5 | `.*      ` | PASS |
| 45_ffi_bind | 15 | 121 | 3.3 | 3 | 9 | 123 | 5 | ` ******  v` | PASS |
| 47_try_operator | 32 | 288 | 10.6 | 4 | 23 | 279 | 6 | `~~*~   ` | PASS |
| 48_match_nested_exhaustive | 23 | 261 | 10.4 | 3 | 12 | 309 | 6 | ` .* ^` | PASS |
| **Total** | **692** | **5961** | **209.1** | **86** | **413** | **5402** | **798** | | **46/46** |

