# Mapanare Benchmarks - Linux

Generated: 2026-04-28 01:42 UTC  
Version: 5.9.0 (`362cb64`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 11.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 642 | ` __ __   ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `         v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 6 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `         v` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 13 | `         v` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 6 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         v` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 7 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `_ _   _  v` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 8 | `         v` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `-.- ___  v` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 7 | `_        v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 4 | `         ^` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 7 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 7 | `__. _ _  v` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 6 | `        ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `        ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 7 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `         v` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `        ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 5 | `         v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `__       v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `____    ` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 6 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `         ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `___     ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `..-_ . _ ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `--~    _ ^` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 6 | `_ _  _  ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 4 | `.-*-_  _ ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `____   _ ^` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | ` __      ^` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 7 | `         v` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 6 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 6 | ` _      ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 8 | `        ` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 6 | `         v` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 8 | `..._____` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 8 | `.-.____- ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `___      v` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `-~~_..-. v` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 4 | `_._     ` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 4 | `_..      v` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 5 | `.-.   _  v` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `.*.      ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `.-.._ _  v` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | `.-._    ` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 7 | `        ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 6 | `-.. _   ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `        ` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 5 | `        ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `***....- ^` | PASS |
| **Total** | **1336** | **13053** | **492.4** | **112** | **1039** | **11149** | **1025** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 201 | 11.8 | 1 | 109 | YES | PASS |
| 02_arithmetic | 211 | 12.1 | 1 | 114 | YES | PASS |
| 03_function | 233 | 12.7 | 2 | 147 | YES | PASS |
| 04_if_else | 218 | 12.3 | 1 | 152 | YES | PASS |
| 05_for_loop | 234 | 12.9 | 1 | 145 | YES | PASS |
| 06_struct | 214 | 12.2 | 1 | 120 | YES | PASS |
| 07_enum_match | 224 | 12.6 | 1 | 162 | YES | PASS |
| 08_list | 240 | 13.6 | 1 | 150 | YES | PASS |
| 09_string_methods | 224 | 12.9 | 1 | 150 | YES | PASS |
| 10_result | 269 | 14.4 | 2 | 164 | YES | PASS |
| 11_closure | 224 | 12.4 | 1 | 135 | YES | PASS |
| 12_while | 220 | 12.3 | 1 | 150 | YES | PASS |
| 13_fib | 231 | 12.5 | 2 | 218 | YES | PASS |
| 14_nested_struct | 214 | 12.2 | 1 | 128 | YES | PASS |
| 15_multifunction | 244 | 13.0 | 3 | 130 | YES | PASS |
| 16_string_escape | 220 | 12.7 | 1 | 164 | YES | PASS |
| 17_option | 296 | 15.1 | 2 | 187 | YES | PASS |
| 18_method_chain | 246 | 13.9 | 1 | 170 | YES | PASS |
| 19_nested_match | 269 | 14.1 | 2 | 185 | YES | PASS |
| 20_recursion | 237 | 12.8 | 2 | 142 | YES | PASS |
| 21_list_ops | 322 | 16.9 | 2 | 276 | YES | PASS |
| 22_string_builder | 289 | 15.4 | 2 | 216 | YES | PASS |
| 23_multi_return | 263 | 14.3 | 2 | 135 | YES | PASS |
| 24_enum_methods | 257 | 13.9 | 2 | 190 | YES | PASS |
| 25_fizzbuzz | 301 | 15.2 | 2 | 177 | YES | PASS |
| 26_generics | 281 | 14.3 | 5 | 162 | YES | PASS |
| 27_impl | 241 | 13.1 | 3 | 170 | YES | PASS |
| 28_traits | 249 | 13.3 | 3 | 135 | YES | PASS |
| 29_generic_impl | 250 | 13.6 | 3 | 146 | YES | PASS |
| 30_nested_generics | 241 | 13.9 | 1 | 168 | YES | PASS |
| 31_generic_multi | 266 | 14.4 | 4 | 154 | YES | PASS |
| 32_generic_enum | 212 | 12.1 | 1 | 119 | YES | PASS |
| 33_break_continue | 425 | 18.9 | 5 | 209 | YES | PASS |
| 34_file_io | 296 | 16.7 | 1 | 140 | YES | PASS |
| 35_stdin | 226 | 13.0 | 1 | 143 | YES | PASS |
| 36_crypto | 255 | 14.4 | 1 | 136 | YES | PASS |
| 37_regex | 266 | 15.1 | 1 | 131 | YES | PASS |
| 38_http | 217 | 12.5 | 1 | 174 | YES | PASS |
| 39_gpu_detect | 244 | 13.7 | 1 | 161 | YES | PASS |
| 40_gpu_tensor | 431 | 22.5 | 1 | 147 | YES | PASS |
| 41_module_let | 215 | 12.1 | 2 | 109 | YES | PASS |
| 42_module_let_string | 218 | 12.3 | 2 | 121 | YES | PASS |
| 43_module_let_math | 222 | 12.4 | 2 | 158 | YES | PASS |
| 45_ffi_bind | 250 | 13.0 | 3 | 172 | YES | PASS |
| 47_try_operator | 353 | 17.8 | 4 | 196 | YES | PASS |
| 48_match_nested_exhaustive | 446 | 22.2 | 3 | 158 | YES | PASS |
| 49_match_guards | 273 | 14.7 | 2 | 155 | YES | PASS |
| 49_tensor_literal | 478 | 24.3 | 1 | 157 | YES | PASS |
| 50_match_or_patterns | 291 | 15.6 | 2 | 144 | YES | PASS |
| 50_tensor_indexing | 450 | 23.0 | 1 | 126 | YES | PASS |
| 51_match_guards_and_or | 342 | 17.3 | 2 | 219 | YES | PASS |
| 51_tensor_broadcast | 462 | 23.2 | 1 | 160 | YES | PASS |
| 52_tensor_slicing | 457 | 23.4 | 1 | 167 | YES | PASS |
| 53_linear_regression | 384 | 19.6 | 1 | 171 | YES | PASS |
| 54_const_basic | 221 | 12.7 | 1 | 113 | YES | PASS |
| 55_async_basic | 263 | 14.1 | 2 | 152 | YES | PASS |
| 56_async_await | 342 | 17.0 | 3 | 162 | YES | PASS |
| 57_real_await | 498 | 22.8 | 5 | 160 | YES | PASS |
| 58_async_file_io | 425 | 20.0 | 4 | 145 | YES | PASS |
| 58_const_scope | 254 | 13.5 | 2 | 152 | YES | PASS |
| 59_async_fanout | 1051 | 43.8 | 12 | 160 | YES | PASS |
| 62_list_output | 382 | 20.6 | 3 | 173 | YES | PASS |
| 63_else_sino | 310 | 15.5 | 3 | 152 | YES | PASS |
| 64_closure_typed | 323 | 15.7 | 3 | 194 | YES | PASS |
| 65_list_int_indexing | 400 | 21.0 | 1 | 150 | YES | PASS |
| 66_qualified_type_ref | 237 | 13.1 | 2 | 164 | YES | PASS |
| **Total** | | | | **10403** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 642 | 109 | 5.9x |
| 02_arithmetic | 6 | 114 | 0.1x |
| 03_function | 6 | 147 | 0.0x |
| 04_if_else | 5 | 152 | 0.0x |
| 05_for_loop | 6 | 145 | 0.0x |
| 06_struct | 6 | 120 | 0.0x |
| 07_enum_match | 13 | 162 | 0.1x |
| 08_list | 6 | 150 | 0.0x |
| 09_string_methods | 4 | 150 | 0.0x |
| 10_result | 6 | 164 | 0.0x |
| 11_closure | 4 | 135 | 0.0x |
| 12_while | 5 | 150 | 0.0x |
| 13_fib | 7 | 218 | 0.0x |
| 14_nested_struct | 4 | 128 | 0.0x |
| 15_multifunction | 5 | 130 | 0.0x |
| 16_string_escape | 4 | 164 | 0.0x |
| 17_option | 8 | 187 | 0.0x |
| 18_method_chain | 5 | 170 | 0.0x |
| 19_nested_match | 7 | 185 | 0.0x |
| 20_recursion | 4 | 142 | 0.0x |
| 21_list_ops | 7 | 276 | 0.0x |
| 22_string_builder | 7 | 216 | 0.0x |
| 23_multi_return | 6 | 135 | 0.0x |
| 24_enum_methods | 5 | 190 | 0.0x |
| 25_fizzbuzz | 7 | 177 | 0.0x |
| 26_generics | 7 | 162 | 0.0x |
| 27_impl | 7 | 170 | 0.0x |
| 28_traits | 6 | 135 | 0.0x |
| 29_generic_impl | 5 | 146 | 0.0x |
| 30_nested_generics | 5 | 168 | 0.0x |
| 31_generic_multi | 7 | 154 | 0.0x |
| 32_generic_enum | 4 | 119 | 0.0x |
| 33_break_continue | 8 | 209 | 0.0x |
| 34_file_io | 6 | 140 | 0.0x |
| 35_stdin | 4 | 143 | 0.0x |
| 36_crypto | 5 | 136 | 0.0x |
| 37_regex | 4 | 131 | 0.0x |
| 38_http | 4 | 174 | 0.0x |
| 39_gpu_detect | 5 | 161 | 0.0x |
| 40_gpu_tensor | 6 | 147 | 0.0x |
| 41_module_let | 5 | 109 | 0.0x |
| 42_module_let_string | 4 | 121 | 0.0x |
| 43_module_let_math | 5 | 158 | 0.0x |
| 45_ffi_bind | 5 | 172 | 0.0x |
| 47_try_operator | 7 | 196 | 0.0x |
| 48_match_nested_exhaustive | 7 | 158 | 0.0x |
| 49_match_guards | 6 | 155 | 0.0x |
| 49_tensor_literal | 10 | 157 | 0.1x |
| 50_match_or_patterns | 6 | 144 | 0.0x |
| 50_tensor_indexing | 8 | 126 | 0.1x |
| 51_match_guards_and_or | 6 | 219 | 0.0x |
| 51_tensor_broadcast | 8 | 160 | 0.0x |
| 52_tensor_slicing | 8 | 167 | 0.0x |
| 53_linear_regression | 7 | 171 | 0.0x |
| 54_const_basic | 4 | 113 | 0.0x |
| 55_async_basic | 4 | 152 | 0.0x |
| 56_async_await | 4 | 162 | 0.0x |
| 57_real_await | 5 | 160 | 0.0x |
| 58_async_file_io | 5 | 145 | 0.0x |
| 58_const_scope | 5 | 152 | 0.0x |
| 59_async_fanout | 6 | 160 | 0.0x |
| 62_list_output | 7 | 173 | 0.0x |
| 63_else_sino | 6 | 152 | 0.0x |
| 64_closure_typed | 8 | 194 | 0.0x |
| 65_list_int_indexing | 5 | 150 | 0.0x |
| 66_qualified_type_ref | 5 | 164 | 0.0x |

