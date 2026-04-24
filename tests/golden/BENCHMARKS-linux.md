# Mapanare Benchmarks - Linux

Generated: 2026-04-24 14:01 UTC  
Version: 5.6.2 (`b10d7ef`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 12.4s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 686 | ` ____  _ ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `         ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 8 | `         ^` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 8 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 6 | `         v` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 7 | `         ^` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 14 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 7 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 5 | `         v` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 8 | `        ` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 5 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 6 | `         ^` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `         ^` | PASS |
| 17_option | 19 | 188 | 6.4 | 2 | 15 | 173 | 8 | `        ` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 6 | `   _____` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 9 | `         ^` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 7 | `         ^` | PASS |
| 21_list_ops | 15 | 240 | 8.9 | 2 | 15 | 277 | 6 | `         ^` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `   _____` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 7 | `  _     ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 6 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 6 | `        ` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `         ^` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 7 | `         v` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 6 | `         ^` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 8 | `         ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 6 | `        ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 9 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 5 | `        ` | PASS |
| 33_break_continue | 58 | 438 | 13.7 | 5 | 38 | 446 | 9 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 6 | `        ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 5 | `        ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `  _    _ ^` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 6 | `        ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 5 | ` ~ ._ ~_ v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 5 | `        ` | PASS |
| 40_gpu_tensor | 18 | 429 | 18.5 | 1 | 33 | 478 | 6 | `      _  v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `____.._- ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 5 | `     ___` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 6 | `         ^` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 8 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         ^` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 7 | `         ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 12 | `         ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 9 | `        ` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 9 | `         v` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 6 | `_   _   ` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 11 | `_ __. __` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 9 | `____.___` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 7 | `   _    ` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 6 | `._-._..- ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 6 | `  _      ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 7 | `        ` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 6 | `_  _  __` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 7 | `  ___  _ ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 6 | `     ._. ^` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 7 | `   __.__ ^` | PASS |
| 62_list_output | 35 | 305 | 14.8 | 2 | 20 | 313 | 7 | `         v` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 7 | `      __ v` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 8 | `         ^` | PASS |
| 65_list_int_indexing | 31 | 321 | 12.8 | 1 | 26 | 317 | 7 | `         ^` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.4 | 1 | 4 | 33 | 5 | `_._...-~ ^` | PASS |
| **Total** | **1336** | **12735** | **480.4** | **110** | **1019** | **10795** | **1129** | | **65/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 180 | 10.5 | 1 | 111 | YES | PASS |
| 02_arithmetic | 190 | 10.8 | 1 | 154 | YES | PASS |
| 03_function | 212 | 11.4 | 2 | 194 | YES | PASS |
| 04_if_else | 197 | 11.0 | 1 | 172 | YES | PASS |
| 05_for_loop | 213 | 11.6 | 1 | 195 | YES | PASS |
| 06_struct | 195 | 11.0 | 1 | 149 | YES | PASS |
| 07_enum_match | 203 | 11.3 | 1 | 157 | YES | PASS |
| 08_list | 219 | 12.2 | 1 | 179 | YES | PASS |
| 09_string_methods | 203 | 11.6 | 1 | 162 | YES | PASS |
| 10_result | 248 | 13.1 | 2 | 197 | YES | PASS |
| 11_closure | 215 | 11.5 | 1 | 144 | YES | PASS |
| 12_while | 199 | 11.0 | 1 | 141 | YES | PASS |
| 13_fib | 210 | 11.2 | 2 | 175 | YES | PASS |
| 14_nested_struct | 195 | 11.0 | 1 | 172 | YES | PASS |
| 15_multifunction | 223 | 11.7 | 3 | 168 | YES | PASS |
| 16_string_escape | 199 | 11.4 | 1 | 136 | YES | PASS |
| 17_option | 275 | 13.8 | 2 | 192 | YES | PASS |
| 18_method_chain | 225 | 12.6 | 1 | 323 | YES | PASS |
| 19_nested_match | 248 | 12.8 | 2 | 200 | YES | PASS |
| 20_recursion | 216 | 11.5 | 2 | 177 | YES | PASS |
| 21_list_ops | 298 | 15.4 | 2 | 195 | YES | PASS |
| 22_string_builder | 268 | 14.1 | 2 | 185 | YES | PASS |
| 23_multi_return | 244 | 13.1 | 2 | 155 | YES | PASS |
| 24_enum_methods | 236 | 12.6 | 2 | 167 | YES | PASS |
| 25_fizzbuzz | 280 | 13.9 | 2 | 170 | YES | PASS |
| 26_generics | 260 | 13.0 | 5 | 161 | YES | PASS |
| 27_impl | 222 | 11.9 | 3 | 171 | YES | PASS |
| 28_traits | 230 | 12.1 | 3 | 166 | YES | PASS |
| 29_generic_impl | 229 | 12.2 | 3 | 163 | YES | PASS |
| 30_nested_generics | 220 | 12.6 | 1 | 154 | YES | PASS |
| 31_generic_multi | 245 | 13.1 | 4 | 166 | YES | PASS |
| 32_generic_enum | 191 | 10.8 | 1 | 146 | YES | PASS |
| 33_break_continue | 401 | 17.3 | 5 | 193 | YES | PASS |
| 34_file_io | 273 | 15.3 | 1 | 139 | YES | PASS |
| 35_stdin | 205 | 11.7 | 1 | 137 | YES | PASS |
| 36_crypto | 234 | 13.1 | 1 | 143 | YES | PASS |
| 37_regex | 245 | 13.8 | 1 | 147 | YES | PASS |
| 38_http | 196 | 11.3 | 1 | 154 | YES | PASS |
| 39_gpu_detect | 223 | 12.4 | 1 | 151 | YES | PASS |
| 40_gpu_tensor | 394 | 20.2 | 1 | 164 | YES | PASS |
| 41_module_let | 194 | 10.8 | 2 | 137 | YES | PASS |
| 42_module_let_string | 197 | 11.0 | 2 | 141 | YES | PASS |
| 43_module_let_math | 201 | 11.2 | 2 | 162 | YES | PASS |
| 45_ffi_bind | 229 | 11.7 | 3 | 167 | YES | PASS |
| 47_try_operator | 332 | 16.5 | 4 | 180 | YES | PASS |
| 48_match_nested_exhaustive | 425 | 20.9 | 3 | 181 | YES | PASS |
| 49_match_guards | 252 | 13.4 | 2 | 195 | YES | PASS |
| 49_tensor_literal | 432 | 22.0 | 1 | 223 | YES | PASS |
| 50_match_or_patterns | 269 | 14.2 | 2 | 207 | YES | PASS |
| 50_tensor_indexing | 404 | 20.7 | 1 | 173 | YES | PASS |
| 51_tensor_broadcast | 386 | 19.7 | 1 | 162 | YES | PASS |
| 52_tensor_slicing | 0 | 0.0 | 0 | 43 | - | FAIL |
| 53_linear_regression | 325 | 16.7 | 1 | 169 | YES | PASS |
| 54_const_basic | 200 | 11.4 | 1 | 116 | YES | PASS |
| 55_async_basic | 242 | 12.8 | 2 | 184 | YES | PASS |
| 56_async_await | 321 | 15.7 | 3 | 177 | YES | PASS |
| 57_real_await | 477 | 21.5 | 5 | 177 | YES | PASS |
| 58_async_file_io | 404 | 18.8 | 4 | 165 | YES | PASS |
| 58_const_scope | 233 | 12.2 | 2 | 155 | YES | PASS |
| 59_async_fanout | 1030 | 42.5 | 12 | 190 | YES | PASS |
| 62_list_output | 362 | 19.2 | 3 | 183 | YES | PASS |
| 63_else_sino | 289 | 14.2 | 3 | 172 | YES | PASS |
| 64_closure_typed | 0 | 0.0 | 0 | 40 | - | FAIL |
| 65_list_int_indexing | 361 | 18.6 | 1 | 160 | YES | PASS |
| 66_qualified_type_ref | 220 | 12.0 | 2 | 150 | YES | PASS |
| **Total** | | | | **10735** | **63/66** | **63/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 686 | 111 | 6.2x |
| 02_arithmetic | 7 | 154 | 0.0x |
| 03_function | 8 | 194 | 0.0x |
| 04_if_else | 8 | 172 | 0.0x |
| 05_for_loop | 6 | 195 | 0.0x |
| 06_struct | 7 | 149 | 0.0x |
| 07_enum_match | 14 | 157 | 0.1x |
| 08_list | 7 | 179 | 0.0x |
| 09_string_methods | 5 | 162 | 0.0x |
| 10_result | 8 | 197 | 0.0x |
| 11_closure | 5 | 144 | 0.0x |
| 12_while | 5 | 141 | 0.0x |
| 13_fib | 5 | 175 | 0.0x |
| 14_nested_struct | 5 | 172 | 0.0x |
| 15_multifunction | 6 | 168 | 0.0x |
| 16_string_escape | 5 | 136 | 0.0x |
| 17_option | 8 | 192 | 0.0x |
| 18_method_chain | 6 | 323 | 0.0x |
| 19_nested_match | 9 | 200 | 0.0x |
| 20_recursion | 7 | 177 | 0.0x |
| 21_list_ops | 6 | 195 | 0.0x |
| 22_string_builder | 5 | 185 | 0.0x |
| 23_multi_return | 7 | 155 | 0.0x |
| 24_enum_methods | 6 | 167 | 0.0x |
| 25_fizzbuzz | 6 | 170 | 0.0x |
| 26_generics | 7 | 161 | 0.0x |
| 27_impl | 7 | 171 | 0.0x |
| 28_traits | 6 | 166 | 0.0x |
| 29_generic_impl | 8 | 163 | 0.0x |
| 30_nested_generics | 6 | 154 | 0.0x |
| 31_generic_multi | 9 | 166 | 0.1x |
| 32_generic_enum | 5 | 146 | 0.0x |
| 33_break_continue | 9 | 193 | 0.0x |
| 34_file_io | 6 | 139 | 0.0x |
| 35_stdin | 5 | 137 | 0.0x |
| 36_crypto | 5 | 143 | 0.0x |
| 37_regex | 6 | 147 | 0.0x |
| 38_http | 5 | 154 | 0.0x |
| 39_gpu_detect | 5 | 151 | 0.0x |
| 40_gpu_tensor | 6 | 164 | 0.0x |
| 41_module_let | 5 | 137 | 0.0x |
| 42_module_let_string | 5 | 141 | 0.0x |
| 43_module_let_math | 5 | 162 | 0.0x |
| 45_ffi_bind | 6 | 167 | 0.0x |
| 47_try_operator | 8 | 180 | 0.0x |
| 48_match_nested_exhaustive | 7 | 181 | 0.0x |
| 49_match_guards | 7 | 195 | 0.0x |
| 49_tensor_literal | 12 | 223 | 0.1x |
| 50_match_or_patterns | 9 | 207 | 0.0x |
| 50_tensor_indexing | 9 | 173 | 0.1x |
| 51_tensor_broadcast | 11 | 162 | 0.1x |
| 53_linear_regression | 7 | 169 | 0.0x |
| 54_const_basic | 6 | 116 | 0.0x |
| 55_async_basic | 6 | 184 | 0.0x |
| 56_async_await | 7 | 177 | 0.0x |
| 57_real_await | 6 | 177 | 0.0x |
| 58_async_file_io | 7 | 165 | 0.0x |
| 58_const_scope | 6 | 155 | 0.0x |
| 59_async_fanout | 7 | 190 | 0.0x |
| 62_list_output | 7 | 183 | 0.0x |
| 63_else_sino | 7 | 172 | 0.0x |
| 65_list_int_indexing | 7 | 160 | 0.0x |
| 66_qualified_type_ref | 5 | 150 | 0.0x |

