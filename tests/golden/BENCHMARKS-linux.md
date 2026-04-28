# Mapanare Benchmarks - Linux

Generated: 2026-04-28 03:36 UTC  
Version: 5.9.2 (`912dad1`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 4.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 715 | `_   ___  v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 8 | `         v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 4 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         v` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | ` _      ` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 6 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 6 | `__ __  _ ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 6 | `        ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | ` _ _  __` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 5 | `        ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `        ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `         ^` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 5 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         v` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `         ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | `. _ ____` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `  _    _ ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 6 | `_       ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `  _ __  ` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `  _      v` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 6 | `        ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 11 | `        ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 7 | `         v` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 10 | `         v` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 9 | `        ` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `________` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 9 | `__-_____ v` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `         ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 5 | `.-._._-_ v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 6 | `    _    v` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `         ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | ` _   _ _ ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `        ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | ` _      ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `    _ .  v` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 8 | `         ^` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `    ____` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `         v` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 5 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 4 | `..-.._.- ^` | PASS |
| **Total** | **1336** | **13053** | **492.4** | **112** | **1039** | **11149** | **1104** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 201 | 11.8 | 1 | 215 | YES | PASS |
| 02_arithmetic | 211 | 12.1 | 1 | 207 | YES | PASS |
| 03_function | 233 | 12.7 | 2 | 132 | YES | PASS |
| 04_if_else | 218 | 12.3 | 1 | 151 | YES | PASS |
| 05_for_loop | 234 | 12.9 | 1 | 187 | YES | PASS |
| 06_struct | 214 | 12.2 | 1 | 149 | YES | PASS |
| 07_enum_match | 224 | 12.6 | 1 | 136 | YES | PASS |
| 08_list | 240 | 13.6 | 1 | 177 | YES | PASS |
| 09_string_methods | 224 | 12.9 | 1 | 193 | YES | PASS |
| 10_result | 269 | 14.4 | 2 | 159 | YES | PASS |
| 11_closure | 224 | 12.4 | 1 | 149 | YES | PASS |
| 12_while | 220 | 12.3 | 1 | 116 | YES | PASS |
| 13_fib | 231 | 12.5 | 2 | 147 | YES | PASS |
| 14_nested_struct | 214 | 12.2 | 1 | 161 | YES | PASS |
| 15_multifunction | 244 | 13.0 | 3 | 159 | YES | PASS |
| 16_string_escape | 220 | 12.7 | 1 | 112 | YES | PASS |
| 17_option | 296 | 15.1 | 2 | 167 | YES | PASS |
| 18_method_chain | 246 | 13.9 | 1 | 172 | YES | PASS |
| 19_nested_match | 269 | 14.1 | 2 | 29 | YES | PASS |
| 20_recursion | 237 | 12.8 | 2 | 8 | YES | PASS |
| 21_list_ops | 322 | 16.9 | 2 | 14 | YES | PASS |
| 22_string_builder | 289 | 15.4 | 2 | 8 | YES | PASS |
| 23_multi_return | 263 | 14.3 | 2 | 10 | YES | PASS |
| 24_enum_methods | 257 | 13.9 | 2 | 8 | YES | PASS |
| 25_fizzbuzz | 301 | 15.2 | 2 | 8 | YES | PASS |
| 26_generics | 281 | 14.3 | 5 | 8 | YES | PASS |
| 27_impl | 241 | 13.1 | 3 | 8 | YES | PASS |
| 28_traits | 249 | 13.3 | 3 | 8 | YES | PASS |
| 29_generic_impl | 250 | 13.6 | 3 | 8 | YES | PASS |
| 30_nested_generics | 241 | 13.9 | 1 | 7 | YES | PASS |
| 31_generic_multi | 266 | 14.4 | 4 | 8 | YES | PASS |
| 32_generic_enum | 212 | 12.1 | 1 | 7 | YES | PASS |
| 33_break_continue | 425 | 18.9 | 5 | 9 | YES | PASS |
| 34_file_io | 296 | 16.7 | 1 | 7 | YES | PASS |
| 35_stdin | 226 | 13.0 | 1 | 8 | YES | PASS |
| 36_crypto | 255 | 14.4 | 1 | 8 | YES | PASS |
| 37_regex | 266 | 15.1 | 1 | 9 | YES | PASS |
| 38_http | 217 | 12.5 | 1 | 8 | YES | PASS |
| 39_gpu_detect | 244 | 13.7 | 1 | 9 | YES | PASS |
| 40_gpu_tensor | 431 | 22.5 | 1 | 8 | YES | PASS |
| 41_module_let | 215 | 12.1 | 2 | 8 | YES | PASS |
| 42_module_let_string | 218 | 12.3 | 2 | 8 | YES | PASS |
| 43_module_let_math | 222 | 12.4 | 2 | 8 | YES | PASS |
| 45_ffi_bind | 250 | 13.0 | 3 | 8 | YES | PASS |
| 47_try_operator | 353 | 17.8 | 4 | 9 | YES | PASS |
| 48_match_nested_exhaustive | 446 | 22.2 | 3 | 9 | YES | PASS |
| 49_match_guards | 273 | 14.7 | 2 | 8 | YES | PASS |
| 49_tensor_literal | 478 | 24.3 | 1 | 9 | YES | PASS |
| 50_match_or_patterns | 291 | 15.6 | 2 | 10 | YES | PASS |
| 50_tensor_indexing | 450 | 23.0 | 1 | 10 | YES | PASS |
| 51_match_guards_and_or | 342 | 17.3 | 2 | 10 | YES | PASS |
| 51_tensor_broadcast | 462 | 23.2 | 1 | 10 | YES | PASS |
| 52_tensor_slicing | 457 | 23.4 | 1 | 9 | YES | PASS |
| 53_linear_regression | 384 | 19.6 | 1 | 9 | YES | PASS |
| 54_const_basic | 221 | 12.7 | 1 | 7 | YES | PASS |
| 55_async_basic | 263 | 14.1 | 2 | 8 | YES | PASS |
| 56_async_await | 342 | 17.0 | 3 | 7 | YES | PASS |
| 57_real_await | 498 | 22.8 | 5 | 7 | YES | PASS |
| 58_async_file_io | 425 | 20.0 | 4 | 8 | YES | PASS |
| 58_const_scope | 254 | 13.5 | 2 | 7 | YES | PASS |
| 59_async_fanout | 1051 | 43.8 | 12 | 10 | YES | PASS |
| 62_list_output | 382 | 20.6 | 3 | 9 | YES | PASS |
| 63_else_sino | 310 | 15.5 | 3 | 8 | YES | PASS |
| 64_closure_typed | 323 | 15.7 | 3 | 8 | YES | PASS |
| 65_list_int_indexing | 400 | 21.0 | 1 | 7 | YES | PASS |
| 66_qualified_type_ref | 237 | 13.1 | 2 | 8 | YES | PASS |
| **Total** | | | | **3312** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 715 | 215 | 3.3x |
| 02_arithmetic | 8 | 207 | 0.0x |
| 03_function | 7 | 132 | 0.1x |
| 04_if_else | 4 | 151 | 0.0x |
| 05_for_loop | 5 | 187 | 0.0x |
| 06_struct | 6 | 149 | 0.0x |
| 07_enum_match | 13 | 136 | 0.1x |
| 08_list | 6 | 177 | 0.0x |
| 09_string_methods | 5 | 193 | 0.0x |
| 10_result | 6 | 159 | 0.0x |
| 11_closure | 5 | 149 | 0.0x |
| 12_while | 4 | 116 | 0.0x |
| 13_fib | 5 | 147 | 0.0x |
| 14_nested_struct | 4 | 161 | 0.0x |
| 15_multifunction | 5 | 159 | 0.0x |
| 16_string_escape | 5 | 112 | 0.0x |
| 17_option | 6 | 167 | 0.0x |
| 18_method_chain | 6 | 172 | 0.0x |
| 19_nested_match | 6 | 29 | 0.2x |
| 20_recursion | 5 | 8 | 0.6x |
| 21_list_ops | 6 | 14 | 0.4x |
| 22_string_builder | 5 | 8 | 0.6x |
| 23_multi_return | 5 | 10 | 0.5x |
| 24_enum_methods | 6 | 8 | 0.8x |
| 25_fizzbuzz | 5 | 8 | 0.7x |
| 26_generics | 7 | 8 | 0.9x |
| 27_impl | 5 | 8 | 0.6x |
| 28_traits | 5 | 8 | 0.7x |
| 29_generic_impl | 5 | 8 | 0.7x |
| 30_nested_generics | 5 | 7 | 0.8x |
| 31_generic_multi | 7 | 8 | 0.8x |
| 32_generic_enum | 4 | 7 | 0.6x |
| 33_break_continue | 8 | 9 | 0.8x |
| 34_file_io | 5 | 7 | 0.7x |
| 35_stdin | 4 | 8 | 0.5x |
| 36_crypto | 4 | 8 | 0.5x |
| 37_regex | 5 | 9 | 0.6x |
| 38_http | 4 | 8 | 0.6x |
| 39_gpu_detect | 5 | 9 | 0.6x |
| 40_gpu_tensor | 6 | 8 | 0.7x |
| 41_module_let | 5 | 8 | 0.6x |
| 42_module_let_string | 5 | 8 | 0.6x |
| 43_module_let_math | 5 | 8 | 0.6x |
| 45_ffi_bind | 6 | 8 | 0.7x |
| 47_try_operator | 7 | 9 | 0.8x |
| 48_match_nested_exhaustive | 7 | 9 | 0.7x |
| 49_match_guards | 6 | 8 | 0.7x |
| 49_tensor_literal | 11 | 9 | 1.3x |
| 50_match_or_patterns | 7 | 10 | 0.7x |
| 50_tensor_indexing | 10 | 10 | 1.0x |
| 51_match_guards_and_or | 9 | 10 | 0.9x |
| 51_tensor_broadcast | 8 | 10 | 0.8x |
| 52_tensor_slicing | 9 | 9 | 1.0x |
| 53_linear_regression | 7 | 9 | 0.8x |
| 54_const_basic | 5 | 7 | 0.7x |
| 55_async_basic | 6 | 8 | 0.7x |
| 56_async_await | 5 | 7 | 0.7x |
| 57_real_await | 5 | 7 | 0.7x |
| 58_async_file_io | 5 | 8 | 0.6x |
| 58_const_scope | 5 | 7 | 0.7x |
| 59_async_fanout | 7 | 10 | 0.7x |
| 62_list_output | 8 | 9 | 0.9x |
| 63_else_sino | 6 | 8 | 0.8x |
| 64_closure_typed | 7 | 8 | 0.8x |
| 65_list_int_indexing | 5 | 7 | 0.7x |
| 66_qualified_type_ref | 4 | 8 | 0.6x |

