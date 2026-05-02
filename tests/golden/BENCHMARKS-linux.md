# Mapanare Benchmarks - Linux

Generated: 2026-05-02 07:32 UTC  
Version: 5.26.1 (`cc55cb0`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 21.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 2 | 32 | 0.9 | 1 | 2 | 9 | 1036 | `_..._... v` | PASS |
| 02_arithmetic | 3 | 46 | 1.5 | 1 | 4 | 25 | 7 | `  _  _   v` | PASS |
| 03_function | 6 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 6 | 36 | 1.0 | 1 | 4 | 9 | 11 | `         ^` | PASS |
| 05_for_loop | 5 | 96 | 3.1 | 1 | 7 | 75 | 7 | `        ` | PASS |
| 06_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 9 | `         ^` | PASS |
| 07_enum_match | 10 | 67 | 2.2 | 1 | 5 | 42 | 24 | `         ^` | PASS |
| 08_list | 4 | 105 | 4.1 | 1 | 6 | 129 | 7 | `         v` | PASS |
| 09_string_methods | 4 | 88 | 3.4 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 10 | 147 | 5.3 | 2 | 10 | 155 | 6 | `        ` | PASS |
| 11_closure | 4 | 102 | 3.5 | 1 | 8 | 89 | 6 | `        ` | PASS |
| 12_while | 5 | 77 | 2.4 | 1 | 7 | 58 | 7 | `         ^` | PASS |
| 13_fib | 7 | 112 | 3.4 | 2 | 9 | 106 | 7 | `        ` | PASS |
| 14_nested_struct | 7 | 61 | 2.1 | 1 | 4 | 49 | 5 | `  _     ` | PASS |
| 15_multifunction | 9 | 78 | 2.6 | 1 | 10 | 50 | 6 | `  _      ^` | PASS |
| 16_string_escape | 7 | 56 | 2.0 | 1 | 2 | 27 | 5 | `_      . ^` | PASS |
| 17_option | 14 | 188 | 6.4 | 2 | 15 | 173 | 7 | `         ^` | PASS |
| 18_method_chain | 8 | 124 | 4.9 | 1 | 8 | 84 | 5 | `_____  _ ^` | PASS |
| 19_nested_match | 14 | 164 | 5.6 | 2 | 11 | 170 | 8 | `         v` | PASS |
| 20_recursion | 8 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         v` | PASS |
| 21_list_ops | 12 | 242 | 9.1 | 2 | 15 | 285 | 6 | `        ` | PASS |
| 22_string_builder | 11 | 167 | 6.0 | 2 | 11 | 134 | 6 | ` _____._ v` | PASS |
| 23_multi_return | 12 | 108 | 4.0 | 1 | 8 | 98 | 5 | `         v` | PASS |
| 24_enum_methods | 16 | 109 | 3.9 | 2 | 8 | 82 | 8 | `        ` | PASS |
| 25_fizzbuzz | 12 | 204 | 6.7 | 2 | 20 | 166 | 6 | `    _    v` | PASS |
| 26_generics | 25 | 116 | 3.8 | 1 | 12 | 63 | 8 | `        ` | PASS |
| 27_impl | 16 | 68 | 2.1 | 1 | 6 | 50 | 6 | `         v` | PASS |
| 28_traits | 20 | 73 | 2.3 | 1 | 6 | 58 | 6 | `        ` | PASS |
| 29_generic_impl | 19 | 80 | 2.5 | 1 | 8 | 59 | 7 | `        ` | PASS |
| 30_nested_generics | 18 | 115 | 4.3 | 1 | 2 | 117 | 5 | `      _  v` | PASS |
| 31_generic_multi | 29 | 120 | 4.0 | 1 | 12 | 93 | 8 | `         ^` | PASS |
| 32_generic_enum | 14 | 39 | 1.1 | 1 | 2 | 18 | 4 | `         ^` | PASS |
| 33_break_continue | 45 | 440 | 13.8 | 5 | 38 | 454 | 9 | `         v` | PASS |
| 34_file_io | 18 | 238 | 10.3 | 1 | 12 | 193 | 7 | `         v` | PASS |
| 35_stdin | 3 | 92 | 3.6 | 1 | 8 | 65 | 4 | `        ` | PASS |
| 36_crypto | 12 | 147 | 5.9 | 1 | 12 | 108 | 6 | `   _  _  v` | PASS |
| 37_regex | 9 | 163 | 6.9 | 1 | 8 | 109 | 6 | `_._ ___  v` | PASS |
| 38_http | 4 | 74 | 2.8 | 1 | 6 | 49 | 5 | ` ._   .  v` | PASS |
| 39_gpu_detect | 6 | 144 | 5.6 | 1 | 13 | 100 | 6 | `         v` | PASS |
| 40_gpu_tensor | 16 | 437 | 19.1 | 1 | 33 | 510 | 7 | `         v` | PASS |
| 41_module_let | 11 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 17 | 49 | 1.6 | 1 | 4 | 18 | 5 | `________` | PASS |
| 43_module_let_math | 17 | 49 | 1.5 | 1 | 4 | 18 | 5 | `      _  v` | PASS |
| 45_ffi_bind | 12 | 98 | 2.8 | 2 | 9 | 83 | 7 | `      _  v` | PASS |
| 47_try_operator | 25 | 308 | 11.8 | 4 | 23 | 311 | 13 | `         v` | PASS |
| 48_match_nested_exhaustive | 18 | 345 | 14.0 | 3 | 32 | 325 | 7 | `         v` | PASS |
| 49_match_guards | 13 | 205 | 6.9 | 2 | 16 | 169 | 9 | `         v` | PASS |
| 49_tensor_literal | 57 | 735 | 30.4 | 1 | 48 | 826 | 10 | `         v` | PASS |
| 50_match_or_patterns | 21 | 177 | 6.7 | 2 | 11 | 140 | 6 | `      _  v` | PASS |
| 50_tensor_indexing | 45 | 678 | 28.2 | 1 | 34 | 899 | 8 | `   _     v` | PASS |
| 51_match_guards_and_or | 14 | 298 | 10.4 | 2 | 20 | 274 | 7 | `         v` | PASS |
| 51_tensor_broadcast | 56 | 623 | 25.8 | 1 | 48 | 660 | 8 | `  _ _   ` | PASS |
| 52_tensor_slicing | 48 | 659 | 27.6 | 1 | 42 | 750 | 8 | `         v` | PASS |
| 53_linear_regression | 41 | 390 | 16.0 | 1 | 25 | 413 | 6 | `      _  v` | PASS |
| 54_const_basic | 11 | 86 | 3.1 | 1 | 6 | 59 | 5 | `      .  v` | PASS |
| 55_async_basic | 10 | 134 | 4.9 | 2 | 11 | 41 | 5 | `_     .  v` | PASS |
| 56_async_await | 14 | 223 | 8.1 | 3 | 22 | 73 | 5 | `     ___` | PASS |
| 57_real_await | 23 | 392 | 14.4 | 5 | 44 | 121 | 15 | `   -     v` | PASS |
| 58_async_file_io | 23 | 309 | 11.1 | 4 | 34 | 90 | 7 | `  _   ._ v` | PASS |
| 58_const_scope | 17 | 61 | 1.8 | 1 | 10 | 18 | 5 | `_   ._._ v` | PASS |
| 59_async_fanout | 51 | 1015 | 37.7 | 12 | 121 | 345 | 25 | `... ..~. v` | PASS |
| 62_list_output | 31 | 307 | 14.9 | 2 | 20 | 321 | 8 | `         v` | PASS |
| 63_else_sino | 33 | 259 | 8.7 | 3 | 20 | 250 | 7 | `_ _ _ __ v` | PASS |
| 64_closure_typed | 22 | 245 | 8.4 | 1 | 22 | 260 | 8 | `        ` | PASS |
| 65_list_int_indexing | 30 | 323 | 13.0 | 1 | 26 | 325 | 6 | `         v` | PASS |
| 66_qualified_type_ref | 18 | 46 | 1.4 | 1 | 4 | 33 | 5 | ` __.  _  v` | PASS |
| 67_implicit_return_one_liner | 16 | 106 | 3.6 | 1 | 14 | 75 | 6 | `      _  v` | PASS |
| 68_terse_lambda | 19 | 213 | 7.2 | 1 | 20 | 227 | 8 | ` _____._ v` | PASS |
| 69_list_comp | 11 | 287 | 11.4 | 1 | 21 | 325 | 6 | `.__ -..- ^` | PASS |
| 70_list_comp_filter | 10 | 303 | 11.9 | 1 | 24 | 334 | 6 | `-       ` | PASS |
| 71_map_comp | 11 | 156 | 5.5 | 1 | 11 | 148 | 9 | `___   _  v` | PASS |
| 72_string_interp_var | 9 | 63 | 2.4 | 1 | 4 | 41 | 5 | `.__   .  v` | PASS |
| 73_string_interp_int | 6 | 72 | 2.7 | 1 | 6 | 49 | 4 | `        ` | PASS |
| 74_string_interp_float | 5 | 72 | 2.7 | 1 | 6 | 49 | 6 | `.  _ _  ` | PASS |
| 75_string_interp_bool | 6 | 73 | 2.7 | 1 | 6 | 42 | 5 | `_ _   _  v` | PASS |
| 76_string_interp_method | 7 | 60 | 2.2 | 1 | 4 | 41 | 5 | `__  _ _  v` | PASS |
| 77_string_interp_arith | 4 | 72 | 2.7 | 1 | 6 | 49 | 5 | `__ -_ -  v` | PASS |
| 78_string_interp_multi | 8 | 104 | 4.0 | 1 | 10 | 81 | 5 | `-* _  *  v` | PASS |
| 79_string_interp_mixed | 9 | 92 | 3.6 | 1 | 8 | 65 | 4 | `- _      v` | PASS |
| 80_string_interp_escaped | 7 | 32 | 1.0 | 1 | 2 | 9 | 4 | `-_._____` | PASS |
| 81_struct_shorthand | 25 | 149 | 5.6 | 1 | 10 | 140 | 5 | `___  ___` | PASS |
| 82_struct_update | 17 | 140 | 5.3 | 1 | 8 | 139 | 5 | `-_     - ^` | PASS |
| 83_struct_update_partial | 20 | 176 | 6.8 | 1 | 10 | 180 | 6 | `     _   ^` | PASS |
| 84_let_destructure | 17 | 87 | 3.1 | 1 | 6 | 74 | 9 | `_       ` | PASS |
| 85_let_destructure_nested | 21 | 102 | 3.8 | 1 | 6 | 98 | 6 | `___   __` | PASS |
| 86_let_destructure_rest | 15 | 66 | 2.3 | 1 | 4 | 57 | 6 | `       _ ^` | PASS |
| 87_let_destructure_mut | 16 | 102 | 3.6 | 1 | 6 | 98 | 6 | `        ` | PASS |
| 88_if_let | 10 | 66 | 2.1 | 1 | 5 | 57 | 6 | `      .  v` | PASS |
| 89_if_let_else | 11 | 73 | 2.4 | 1 | 5 | 58 | 5 | `____~_._ v` | PASS |
| 90_while_let | 20 | 70 | 2.2 | 1 | 7 | 57 | 5 | `_   .-  ` | PASS |
| 91_let_else | 24 | 97 | 3.3 | 1 | 11 | 73 | 5 | ` _   _.  v` | PASS |
| 92_chained_cmp_simple | 16 | 167 | 5.8 | 1 | 22 | 90 | 8 | ` - .  .  v` | PASS |
| 93_chained_cmp_4 | 15 | 109 | 3.7 | 1 | 14 | 54 | 7 | `  _   -  v` | PASS |
| 94_chained_cmp_mixed | 24 | 275 | 9.5 | 2 | 28 | 201 | 8 | `      .  v` | PASS |
| 95_chained_cmp_side_effect | 26 | 166 | 5.8 | 2 | 10 | 122 | 6 | `  _ .  _ ^` | PASS |
| **Total** | **1540** | **16605** | **621.3** | **143** | **1333** | **14182** | **1679** | | **95/95** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 206 | 12.1 | 1 | 447 | YES | PASS |
| 02_arithmetic | 216 | 12.4 | 1 | 250 | YES | PASS |
| 03_function | 238 | 13.0 | 2 | 239 | YES | PASS |
| 04_if_else | 223 | 12.7 | 1 | 359 | YES | PASS |
| 05_for_loop | 239 | 13.2 | 1 | 353 | YES | PASS |
| 06_struct | 219 | 12.6 | 1 | 435 | YES | PASS |
| 07_enum_match | 227 | 12.8 | 1 | 284 | YES | PASS |
| 08_list | 245 | 13.9 | 1 | 194 | YES | PASS |
| 09_string_methods | 229 | 13.2 | 1 | 199 | YES | PASS |
| 10_result | 272 | 14.6 | 2 | 236 | YES | PASS |
| 11_closure | 229 | 12.7 | 1 | 187 | YES | PASS |
| 12_while | 225 | 12.6 | 1 | 263 | YES | PASS |
| 13_fib | 236 | 12.8 | 2 | 218 | YES | PASS |
| 14_nested_struct | 219 | 12.6 | 1 | 204 | YES | PASS |
| 15_multifunction | 249 | 13.4 | 3 | 195 | YES | PASS |
| 16_string_escape | 225 | 13.0 | 1 | 148 | YES | PASS |
| 17_option | 308 | 15.7 | 2 | 199 | YES | PASS |
| 18_method_chain | 251 | 14.2 | 1 | 173 | YES | PASS |
| 19_nested_match | 274 | 14.4 | 2 | 185 | YES | PASS |
| 20_recursion | 242 | 13.1 | 2 | 194 | YES | PASS |
| 21_list_ops | 327 | 17.3 | 2 | 178 | YES | PASS |
| 22_string_builder | 294 | 15.7 | 2 | 170 | YES | PASS |
| 23_multi_return | 268 | 14.7 | 2 | 230 | YES | PASS |
| 24_enum_methods | 262 | 14.2 | 2 | 202 | YES | PASS |
| 25_fizzbuzz | 306 | 15.5 | 2 | 222 | YES | PASS |
| 26_generics | 286 | 14.6 | 5 | 167 | YES | PASS |
| 27_impl | 246 | 13.4 | 3 | 160 | YES | PASS |
| 28_traits | 254 | 13.7 | 3 | 194 | YES | PASS |
| 29_generic_impl | 255 | 13.9 | 3 | 163 | YES | PASS |
| 30_nested_generics | 246 | 14.2 | 1 | 159 | YES | PASS |
| 31_generic_multi | 271 | 14.7 | 4 | 187 | YES | PASS |
| 32_generic_enum | 217 | 12.5 | 1 | 146 | YES | PASS |
| 33_break_continue | 430 | 19.3 | 5 | 245 | YES | PASS |
| 34_file_io | 301 | 17.0 | 1 | 178 | YES | PASS |
| 35_stdin | 231 | 13.3 | 1 | 206 | YES | PASS |
| 36_crypto | 260 | 14.8 | 1 | 219 | YES | PASS |
| 37_regex | 271 | 15.4 | 1 | 150 | YES | PASS |
| 38_http | 222 | 12.9 | 1 | 161 | YES | PASS |
| 39_gpu_detect | 249 | 14.1 | 1 | 194 | YES | PASS |
| 40_gpu_tensor | 436 | 22.8 | 1 | 176 | YES | PASS |
| 41_module_let | 220 | 12.4 | 2 | 133 | YES | PASS |
| 42_module_let_string | 223 | 12.6 | 2 | 175 | YES | PASS |
| 43_module_let_math | 227 | 12.8 | 2 | 209 | YES | PASS |
| 45_ffi_bind | 255 | 13.3 | 3 | 228 | YES | PASS |
| 47_try_operator | 354 | 18.0 | 4 | 322 | YES | PASS |
| 48_match_nested_exhaustive | 451 | 22.6 | 3 | 272 | YES | PASS |
| 49_match_guards | 312 | 15.9 | 2 | 210 | YES | PASS |
| 49_tensor_literal | 483 | 24.6 | 1 | 163 | YES | PASS |
| 50_match_or_patterns | 296 | 15.9 | 2 | 275 | YES | PASS |
| 50_tensor_indexing | 455 | 23.3 | 1 | 168 | YES | PASS |
| 51_match_guards_and_or | 378 | 18.7 | 2 | 189 | YES | PASS |
| 51_tensor_broadcast | 467 | 23.5 | 1 | 176 | YES | PASS |
| 52_tensor_slicing | 462 | 23.7 | 1 | 157 | YES | PASS |
| 53_linear_regression | 389 | 19.9 | 1 | 183 | YES | PASS |
| 54_const_basic | 226 | 13.0 | 1 | 147 | YES | PASS |
| 55_async_basic | 268 | 14.5 | 2 | 149 | YES | PASS |
| 56_async_await | 347 | 17.4 | 3 | 203 | YES | PASS |
| 57_real_await | 503 | 23.1 | 5 | 302 | YES | PASS |
| 58_async_file_io | 430 | 20.4 | 4 | 167 | YES | PASS |
| 58_const_scope | 259 | 13.9 | 2 | 172 | YES | PASS |
| 59_async_fanout | 1056 | 44.1 | 12 | 160 | YES | PASS |
| 62_list_output | 387 | 20.9 | 3 | 216 | YES | PASS |
| 63_else_sino | 315 | 15.8 | 3 | 192 | YES | PASS |
| 64_closure_typed | 328 | 16.0 | 3 | 158 | YES | PASS |
| 65_list_int_indexing | 405 | 21.3 | 1 | 176 | YES | PASS |
| 66_qualified_type_ref | 242 | 13.4 | 2 | 170 | YES | PASS |
| 67_implicit_return_one_liner | 269 | 14.0 | 4 | 144 | YES | PASS |
| 68_terse_lambda | 318 | 15.6 | 3 | 184 | YES | PASS |
| 69_list_comp | 370 | 19.6 | 1 | 188 | YES | PASS |
| 70_list_comp_filter | 379 | 19.8 | 1 | 238 | YES | PASS |
| 71_map_comp | 267 | 14.6 | 1 | 228 | YES | PASS |
| 72_string_interp_var | 222 | 12.9 | 1 | 141 | YES | PASS |
| 73_string_interp_int | 222 | 12.8 | 1 | 142 | YES | PASS |
| 74_string_interp_float | 222 | 12.8 | 1 | 171 | YES | PASS |
| 75_string_interp_bool | 223 | 12.8 | 1 | 137 | YES | PASS |
| 76_string_interp_method | 221 | 12.7 | 1 | 161 | YES | PASS |
| 77_string_interp_arith | 221 | 12.8 | 1 | 154 | YES | PASS |
| 78_string_interp_multi | 238 | 13.5 | 1 | 148 | YES | PASS |
| 79_string_interp_mixed | 232 | 13.4 | 1 | 136 | YES | PASS |
| 80_string_interp_escaped | 206 | 12.2 | 1 | 136 | YES | PASS |
| 81_struct_shorthand | 259 | 14.3 | 1 | 179 | YES | PASS |
| 82_struct_update | 255 | 14.3 | 1 | 170 | YES | PASS |
| 83_struct_update_partial | 268 | 14.8 | 1 | 239 | YES | PASS |
| 84_let_destructure | 234 | 13.2 | 1 | 238 | YES | PASS |
| 85_let_destructure_nested | 245 | 13.7 | 1 | 174 | YES | PASS |
| 86_let_destructure_rest | 224 | 12.8 | 1 | 190 | YES | PASS |
| 87_let_destructure_mut | 238 | 13.3 | 1 | 168 | YES | PASS |
| 88_if_let | 237 | 13.1 | 1 | 178 | YES | PASS |
| 89_if_let_else | 232 | 13.0 | 1 | 191 | YES | PASS |
| 90_while_let | 240 | 13.2 | 1 | 172 | YES | PASS |
| 91_let_else | 264 | 14.1 | 2 | 196 | YES | PASS |
| 92_chained_cmp_simple | 280 | 14.8 | 2 | 180 | YES | PASS |
| 93_chained_cmp_4 | 288 | 15.0 | 2 | 150 | YES | PASS |
| 94_chained_cmp_mixed | 335 | 16.5 | 4 | 184 | YES | PASS |
| 95_chained_cmp_side_effect | 303 | 15.9 | 3 | 160 | YES | PASS |
| **Total** | | | | **18814** | **95/95** | **95/95** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 1036 | 447 | 2.3x |
| 02_arithmetic | 7 | 250 | 0.0x |
| 03_function | 7 | 239 | 0.0x |
| 04_if_else | 11 | 359 | 0.0x |
| 05_for_loop | 7 | 353 | 0.0x |
| 06_struct | 9 | 435 | 0.0x |
| 07_enum_match | 24 | 284 | 0.1x |
| 08_list | 7 | 194 | 0.0x |
| 09_string_methods | 4 | 199 | 0.0x |
| 10_result | 6 | 236 | 0.0x |
| 11_closure | 6 | 187 | 0.0x |
| 12_while | 7 | 263 | 0.0x |
| 13_fib | 7 | 218 | 0.0x |
| 14_nested_struct | 5 | 204 | 0.0x |
| 15_multifunction | 6 | 195 | 0.0x |
| 16_string_escape | 5 | 148 | 0.0x |
| 17_option | 7 | 199 | 0.0x |
| 18_method_chain | 5 | 173 | 0.0x |
| 19_nested_match | 8 | 185 | 0.0x |
| 20_recursion | 5 | 194 | 0.0x |
| 21_list_ops | 6 | 178 | 0.0x |
| 22_string_builder | 6 | 170 | 0.0x |
| 23_multi_return | 5 | 230 | 0.0x |
| 24_enum_methods | 8 | 202 | 0.0x |
| 25_fizzbuzz | 6 | 222 | 0.0x |
| 26_generics | 8 | 167 | 0.0x |
| 27_impl | 6 | 160 | 0.0x |
| 28_traits | 6 | 194 | 0.0x |
| 29_generic_impl | 7 | 163 | 0.0x |
| 30_nested_generics | 5 | 159 | 0.0x |
| 31_generic_multi | 8 | 187 | 0.0x |
| 32_generic_enum | 4 | 146 | 0.0x |
| 33_break_continue | 9 | 245 | 0.0x |
| 34_file_io | 7 | 178 | 0.0x |
| 35_stdin | 4 | 206 | 0.0x |
| 36_crypto | 6 | 219 | 0.0x |
| 37_regex | 6 | 150 | 0.0x |
| 38_http | 5 | 161 | 0.0x |
| 39_gpu_detect | 6 | 194 | 0.0x |
| 40_gpu_tensor | 7 | 176 | 0.0x |
| 41_module_let | 4 | 133 | 0.0x |
| 42_module_let_string | 5 | 175 | 0.0x |
| 43_module_let_math | 5 | 209 | 0.0x |
| 45_ffi_bind | 7 | 228 | 0.0x |
| 47_try_operator | 13 | 322 | 0.0x |
| 48_match_nested_exhaustive | 7 | 272 | 0.0x |
| 49_match_guards | 9 | 210 | 0.0x |
| 49_tensor_literal | 10 | 163 | 0.1x |
| 50_match_or_patterns | 6 | 275 | 0.0x |
| 50_tensor_indexing | 8 | 168 | 0.0x |
| 51_match_guards_and_or | 7 | 189 | 0.0x |
| 51_tensor_broadcast | 8 | 176 | 0.0x |
| 52_tensor_slicing | 8 | 157 | 0.0x |
| 53_linear_regression | 6 | 183 | 0.0x |
| 54_const_basic | 5 | 147 | 0.0x |
| 55_async_basic | 5 | 149 | 0.0x |
| 56_async_await | 5 | 203 | 0.0x |
| 57_real_await | 15 | 302 | 0.0x |
| 58_async_file_io | 7 | 167 | 0.0x |
| 58_const_scope | 5 | 172 | 0.0x |
| 59_async_fanout | 25 | 160 | 0.2x |
| 62_list_output | 8 | 216 | 0.0x |
| 63_else_sino | 7 | 192 | 0.0x |
| 64_closure_typed | 8 | 158 | 0.0x |
| 65_list_int_indexing | 6 | 176 | 0.0x |
| 66_qualified_type_ref | 5 | 170 | 0.0x |
| 67_implicit_return_one_liner | 6 | 144 | 0.0x |
| 68_terse_lambda | 8 | 184 | 0.0x |
| 69_list_comp | 6 | 188 | 0.0x |
| 70_list_comp_filter | 6 | 238 | 0.0x |
| 71_map_comp | 9 | 228 | 0.0x |
| 72_string_interp_var | 5 | 141 | 0.0x |
| 73_string_interp_int | 4 | 142 | 0.0x |
| 74_string_interp_float | 6 | 171 | 0.0x |
| 75_string_interp_bool | 5 | 137 | 0.0x |
| 76_string_interp_method | 5 | 161 | 0.0x |
| 77_string_interp_arith | 5 | 154 | 0.0x |
| 78_string_interp_multi | 5 | 148 | 0.0x |
| 79_string_interp_mixed | 4 | 136 | 0.0x |
| 80_string_interp_escaped | 4 | 136 | 0.0x |
| 81_struct_shorthand | 5 | 179 | 0.0x |
| 82_struct_update | 5 | 170 | 0.0x |
| 83_struct_update_partial | 6 | 239 | 0.0x |
| 84_let_destructure | 9 | 238 | 0.0x |
| 85_let_destructure_nested | 6 | 174 | 0.0x |
| 86_let_destructure_rest | 6 | 190 | 0.0x |
| 87_let_destructure_mut | 6 | 168 | 0.0x |
| 88_if_let | 6 | 178 | 0.0x |
| 89_if_let_else | 5 | 191 | 0.0x |
| 90_while_let | 5 | 172 | 0.0x |
| 91_let_else | 5 | 196 | 0.0x |
| 92_chained_cmp_simple | 8 | 180 | 0.0x |
| 93_chained_cmp_4 | 7 | 150 | 0.0x |
| 94_chained_cmp_mixed | 8 | 184 | 0.0x |
| 95_chained_cmp_side_effect | 6 | 160 | 0.0x |

