# Mapanare Benchmarks - Linux

Generated: 2026-04-28 02:58 UTC  
Version: 5.9.1 (`58e67a9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 11.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 643 | `__   ___ ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `         ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         ^` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 7 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         ^` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `  _     ` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 8 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `___ __  ` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `         ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 5 | `         v` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 6 | `_ _ _  _ ^` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 5 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 6 | `        ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `        ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `        ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 5 | `         ^` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         v` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 5 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `         v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 5 | ` . _ ___` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | `   _    ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `         v` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 6 | ` _      ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `_  _ __  v` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 4 | `   _    ` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `        ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         v` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | `         ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `         ^` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         ^` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `________` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `___-____ ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `         v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `..-._._- ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `     _   ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 5 | `         v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `  _   _  v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `        ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `_ _     ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `     _ . ^` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 8 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 7 | `_    ___` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `        ` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 6 | `...-.._. ^` | PASS |
| **Total** | **1336** | **13053** | **492.4** | **112** | **1039** | **11149** | **1027** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 201 | 11.8 | 1 | 101 | YES | PASS |
| 02_arithmetic | 211 | 12.1 | 1 | 112 | YES | PASS |
| 03_function | 233 | 12.7 | 2 | 135 | YES | PASS |
| 04_if_else | 218 | 12.3 | 1 | 137 | YES | PASS |
| 05_for_loop | 234 | 12.9 | 1 | 172 | YES | PASS |
| 06_struct | 214 | 12.2 | 1 | 130 | YES | PASS |
| 07_enum_match | 224 | 12.6 | 1 | 130 | YES | PASS |
| 08_list | 240 | 13.6 | 1 | 137 | YES | PASS |
| 09_string_methods | 224 | 12.9 | 1 | 172 | YES | PASS |
| 10_result | 269 | 14.4 | 2 | 193 | YES | PASS |
| 11_closure | 224 | 12.4 | 1 | 133 | YES | PASS |
| 12_while | 220 | 12.3 | 1 | 146 | YES | PASS |
| 13_fib | 231 | 12.5 | 2 | 162 | YES | PASS |
| 14_nested_struct | 214 | 12.2 | 1 | 132 | YES | PASS |
| 15_multifunction | 244 | 13.0 | 3 | 148 | YES | PASS |
| 16_string_escape | 220 | 12.7 | 1 | 156 | YES | PASS |
| 17_option | 296 | 15.1 | 2 | 246 | YES | PASS |
| 18_method_chain | 246 | 13.9 | 1 | 205 | YES | PASS |
| 19_nested_match | 269 | 14.1 | 2 | 155 | YES | PASS |
| 20_recursion | 237 | 12.8 | 2 | 133 | YES | PASS |
| 21_list_ops | 322 | 16.9 | 2 | 181 | YES | PASS |
| 22_string_builder | 289 | 15.4 | 2 | 193 | YES | PASS |
| 23_multi_return | 263 | 14.3 | 2 | 151 | YES | PASS |
| 24_enum_methods | 257 | 13.9 | 2 | 155 | YES | PASS |
| 25_fizzbuzz | 301 | 15.2 | 2 | 149 | YES | PASS |
| 26_generics | 281 | 14.3 | 5 | 157 | YES | PASS |
| 27_impl | 241 | 13.1 | 3 | 164 | YES | PASS |
| 28_traits | 249 | 13.3 | 3 | 140 | YES | PASS |
| 29_generic_impl | 250 | 13.6 | 3 | 145 | YES | PASS |
| 30_nested_generics | 241 | 13.9 | 1 | 154 | YES | PASS |
| 31_generic_multi | 266 | 14.4 | 4 | 188 | YES | PASS |
| 32_generic_enum | 212 | 12.1 | 1 | 152 | YES | PASS |
| 33_break_continue | 425 | 18.9 | 5 | 180 | YES | PASS |
| 34_file_io | 296 | 16.7 | 1 | 148 | YES | PASS |
| 35_stdin | 226 | 13.0 | 1 | 195 | YES | PASS |
| 36_crypto | 255 | 14.4 | 1 | 154 | YES | PASS |
| 37_regex | 266 | 15.1 | 1 | 124 | YES | PASS |
| 38_http | 217 | 12.5 | 1 | 135 | YES | PASS |
| 39_gpu_detect | 244 | 13.7 | 1 | 156 | YES | PASS |
| 40_gpu_tensor | 431 | 22.5 | 1 | 160 | YES | PASS |
| 41_module_let | 215 | 12.1 | 2 | 122 | YES | PASS |
| 42_module_let_string | 218 | 12.3 | 2 | 138 | YES | PASS |
| 43_module_let_math | 222 | 12.4 | 2 | 112 | YES | PASS |
| 45_ffi_bind | 250 | 13.0 | 3 | 172 | YES | PASS |
| 47_try_operator | 353 | 17.8 | 4 | 191 | YES | PASS |
| 48_match_nested_exhaustive | 446 | 22.2 | 3 | 155 | YES | PASS |
| 49_match_guards | 273 | 14.7 | 2 | 138 | YES | PASS |
| 49_tensor_literal | 478 | 24.3 | 1 | 164 | YES | PASS |
| 50_match_or_patterns | 291 | 15.6 | 2 | 181 | YES | PASS |
| 50_tensor_indexing | 450 | 23.0 | 1 | 151 | YES | PASS |
| 51_match_guards_and_or | 342 | 17.3 | 2 | 154 | YES | PASS |
| 51_tensor_broadcast | 462 | 23.2 | 1 | 135 | YES | PASS |
| 52_tensor_slicing | 457 | 23.4 | 1 | 162 | YES | PASS |
| 53_linear_regression | 384 | 19.6 | 1 | 171 | YES | PASS |
| 54_const_basic | 221 | 12.7 | 1 | 104 | YES | PASS |
| 55_async_basic | 263 | 14.1 | 2 | 127 | YES | PASS |
| 56_async_await | 342 | 17.0 | 3 | 167 | YES | PASS |
| 57_real_await | 498 | 22.8 | 5 | 178 | YES | PASS |
| 58_async_file_io | 425 | 20.0 | 4 | 160 | YES | PASS |
| 58_const_scope | 254 | 13.5 | 2 | 144 | YES | PASS |
| 59_async_fanout | 1051 | 43.8 | 12 | 145 | YES | PASS |
| 62_list_output | 382 | 20.6 | 3 | 207 | YES | PASS |
| 63_else_sino | 310 | 15.5 | 3 | 160 | YES | PASS |
| 64_closure_typed | 323 | 15.7 | 3 | 138 | YES | PASS |
| 65_list_int_indexing | 400 | 21.0 | 1 | 147 | YES | PASS |
| 66_qualified_type_ref | 237 | 13.1 | 2 | 157 | YES | PASS |
| **Total** | | | | **10194** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 643 | 101 | 6.4x |
| 02_arithmetic | 6 | 112 | 0.1x |
| 03_function | 7 | 135 | 0.0x |
| 04_if_else | 5 | 137 | 0.0x |
| 05_for_loop | 5 | 172 | 0.0x |
| 06_struct | 6 | 130 | 0.0x |
| 07_enum_match | 13 | 130 | 0.1x |
| 08_list | 6 | 137 | 0.0x |
| 09_string_methods | 4 | 172 | 0.0x |
| 10_result | 7 | 193 | 0.0x |
| 11_closure | 4 | 133 | 0.0x |
| 12_while | 4 | 146 | 0.0x |
| 13_fib | 6 | 162 | 0.0x |
| 14_nested_struct | 4 | 132 | 0.0x |
| 15_multifunction | 5 | 148 | 0.0x |
| 16_string_escape | 4 | 156 | 0.0x |
| 17_option | 8 | 246 | 0.0x |
| 18_method_chain | 5 | 205 | 0.0x |
| 19_nested_match | 6 | 155 | 0.0x |
| 20_recursion | 5 | 133 | 0.0x |
| 21_list_ops | 5 | 181 | 0.0x |
| 22_string_builder | 6 | 193 | 0.0x |
| 23_multi_return | 5 | 151 | 0.0x |
| 24_enum_methods | 5 | 155 | 0.0x |
| 25_fizzbuzz | 5 | 149 | 0.0x |
| 26_generics | 7 | 157 | 0.0x |
| 27_impl | 6 | 164 | 0.0x |
| 28_traits | 6 | 140 | 0.0x |
| 29_generic_impl | 5 | 145 | 0.0x |
| 30_nested_generics | 6 | 154 | 0.0x |
| 31_generic_multi | 7 | 188 | 0.0x |
| 32_generic_enum | 5 | 152 | 0.0x |
| 33_break_continue | 9 | 180 | 0.1x |
| 34_file_io | 5 | 148 | 0.0x |
| 35_stdin | 4 | 195 | 0.0x |
| 36_crypto | 5 | 154 | 0.0x |
| 37_regex | 5 | 124 | 0.0x |
| 38_http | 5 | 135 | 0.0x |
| 39_gpu_detect | 5 | 156 | 0.0x |
| 40_gpu_tensor | 6 | 160 | 0.0x |
| 41_module_let | 4 | 122 | 0.0x |
| 42_module_let_string | 4 | 138 | 0.0x |
| 43_module_let_math | 4 | 112 | 0.0x |
| 45_ffi_bind | 5 | 172 | 0.0x |
| 47_try_operator | 8 | 191 | 0.0x |
| 48_match_nested_exhaustive | 7 | 155 | 0.0x |
| 49_match_guards | 6 | 138 | 0.0x |
| 49_tensor_literal | 10 | 164 | 0.1x |
| 50_match_or_patterns | 6 | 181 | 0.0x |
| 50_tensor_indexing | 8 | 151 | 0.1x |
| 51_match_guards_and_or | 7 | 154 | 0.0x |
| 51_tensor_broadcast | 8 | 135 | 0.1x |
| 52_tensor_slicing | 7 | 162 | 0.0x |
| 53_linear_regression | 7 | 171 | 0.0x |
| 54_const_basic | 4 | 104 | 0.0x |
| 55_async_basic | 4 | 127 | 0.0x |
| 56_async_await | 5 | 167 | 0.0x |
| 57_real_await | 6 | 178 | 0.0x |
| 58_async_file_io | 5 | 160 | 0.0x |
| 58_const_scope | 5 | 144 | 0.0x |
| 59_async_fanout | 6 | 145 | 0.0x |
| 62_list_output | 8 | 207 | 0.0x |
| 63_else_sino | 7 | 160 | 0.0x |
| 64_closure_typed | 7 | 138 | 0.1x |
| 65_list_int_indexing | 6 | 147 | 0.0x |
| 66_qualified_type_ref | 6 | 157 | 0.0x |

