# Mapanare Benchmarks - Linux

Generated: 2026-04-15 02:28 UTC  
Version: 4.127.0 (`83dfaf4`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 6.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 581 | `_ _   _* ^` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `       _ ^` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 7 | `         v` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 6 | `         ^` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 5 | `       _ ^` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 16 | `         ^` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 8 | `         ^` | PASS |
| 09_string_methods | 5 | 88 | 3.4 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 142 | 5.1 | 2 | 10 | 147 | 6 | `         ^` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `         ^` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 6 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | ` _      ` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 7 | `         ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 4 | `..-__..- ^` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 6 | `    _ .  v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `         ^` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `.-_.__--` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 5 | `.__.___* ^` | PASS |
| 23_multi_return | 15 | 108 | 4.0 | 1 | 8 | 98 | 5 | ` _._ -_. ^` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 5 | `__.__~.* ^` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 7 | `        ` | PASS |
| 27_impl | 21 | 68 | 2.1 | 1 | 6 | 50 | 5 | `___  _.* ^` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 5 | `__ __ *- v` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 8 | `       * ^` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `__.___-. v` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 7 | `         ^` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | ` _    _~ ^` | PASS |
| 33_break_continue | 58 | 428 | 13.2 | 5 | 36 | 446 | 8 | `         ^` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         ^` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `       * ^` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | ` _._ _-_ v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `     __. ^` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `_    ___` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | `         v` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 49 | 1.6 | 1 | 4 | 18 | 5 | `__.__-~~` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 4 | ` __ ----` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 5 | `     _._ v` | PASS |
| 47_try_operator | 32 | 288 | 10.7 | 4 | 23 | 279 | 7 | `         ^` | PASS |
| 48_match_nested_exhaustive | 23 | 337 | 13.6 | 3 | 32 | 309 | 7 | `        ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 7 | `___- _-* ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 9 | `       * ^` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 5 | `__    ..` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.2 | 1 | 34 | 899 | 7 | `___  -_- ^` | PASS |
| 51_match_guards_and_or | 17 | 0 | 0.0 | 0 | 0 | 0 | 3 | `_ __ _ - ^` | FAIL |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 6 | `_     _* ^` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.6 | 1 | 42 | 750 | 7 | `-______* ^` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 6 | `-__ __-* ^` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 4 | `. _  __- ^` | PASS |
| 55_async_basic | 12 | 134 | 4.9 | 2 | 11 | 41 | 7 | `       * ^` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 6 | `       * ^` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 7 | `__-_-__- ^` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 5 | `____. _. ^` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 5 | `.. .*  . ^` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 6 | ` _  _  * ^` | PASS |
| 62_list_output | 35 | 295 | 14.1 | 2 | 20 | 289 | 7 | `         ^` | PASS |
| 63_else_sino | 40 | 259 | 8.6 | 3 | 20 | 250 | 6 | `______--` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 7 | `__.__..* ^` | PASS |
| 65_list_int_indexing | 31 | 261 | 10.2 | 1 | 14 | 317 | 5 | `         ^` | PASS |
| **Total** | **1315** | **12528** | **471.2** | **109** | **991** | **10682** | **951** | | **64/65** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 125 | 7.7 | 1 | 73 | YES | PASS |
| 02_arithmetic | 130 | 7.8 | 1 | 88 | YES | PASS |
| 03_function | 140 | 8.0 | 2 | 117 | YES | PASS |
| 04_if_else | 142 | 8.3 | 1 | 111 | YES | PASS |
| 05_for_loop | 153 | 8.6 | 1 | 114 | YES | PASS |
| 06_struct | 135 | 8.0 | 1 | 102 | YES | PASS |
| 07_enum_match | 148 | 8.5 | 1 | 131 | YES | PASS |
| 08_list | 157 | 9.1 | 1 | 93 | YES | PASS |
| 09_string_methods | 138 | 8.4 | 1 | 80 | YES | PASS |
| 10_result | 183 | 9.9 | 2 | 100 | YES | PASS |
| 11_closure | 143 | 8.1 | 1 | 103 | YES | PASS |
| 12_while | 139 | 8.0 | 1 | 106 | YES | PASS |
| 13_fib | 0 | 0.0 | 0 | 100 | - | FAIL |
| 14_nested_struct | 135 | 8.0 | 1 | 72 | YES | PASS |
| 15_multifunction | 148 | 8.2 | 3 | 82 | YES | PASS |
| 16_string_escape | 144 | 8.7 | 1 | 71 | YES | PASS |
| 17_option | 210 | 10.7 | 2 | 115 | YES | PASS |
| 18_method_chain | 155 | 9.2 | 1 | 95 | YES | PASS |
| 19_nested_match | 0 | 0.0 | 0 | 96 | - | FAIL |
| 20_recursion | 0 | 0.0 | 0 | 84 | - | FAIL |
| 21_list_ops | 0 | 0.0 | 0 | 66 | - | FAIL |
| 22_string_builder | 0 | 0.0 | 0 | 97 | - | FAIL |
| 23_multi_return | 159 | 8.9 | 2 | 87 | YES | PASS |
| 24_enum_methods | 171 | 9.4 | 2 | 85 | YES | PASS |
| 25_fizzbuzz | 200 | 10.1 | 2 | 97 | YES | PASS |
| 26_generics | 197 | 10.0 | 5 | 93 | YES | PASS |
| 27_impl | 158 | 8.7 | 3 | 95 | YES | PASS |
| 28_traits | 163 | 8.8 | 3 | 116 | YES | PASS |
| 29_generic_impl | 0 | 0.0 | 0 | 92 | - | FAIL |
| 30_nested_generics | 165 | 9.8 | 1 | 74 | YES | PASS |
| 31_generic_multi | 0 | 0.0 | 0 | 101 | - | FAIL |
| 32_generic_enum | 142 | 8.3 | 1 | 87 | YES | PASS |
| 33_break_continue | 0 | 0.0 | 0 | 81 | - | FAIL |
| 34_file_io | 193 | 11.4 | 1 | 69 | YES | PASS |
| 35_stdin | 135 | 8.3 | 1 | 66 | YES | PASS |
| 36_crypto | 154 | 9.3 | 1 | 83 | YES | PASS |
| 37_regex | 175 | 10.4 | 1 | 76 | YES | PASS |
| 38_http | 131 | 8.0 | 1 | 74 | YES | PASS |
| 39_gpu_detect | 148 | 8.8 | 1 | 83 | YES | PASS |
| 40_gpu_tensor | 0 | 0.0 | 0 | 52 | - | FAIL |
| 41_module_let | 130 | 7.7 | 2 | 73 | YES | PASS |
| 42_module_let_string | 133 | 8.0 | 2 | 84 | YES | PASS |
| 43_module_let_math | 135 | 8.0 | 2 | 79 | YES | PASS |
| 45_ffi_bind | 162 | 8.5 | 3 | 72 | YES | PASS |
| 47_try_operator | 0 | 0.0 | 0 | 81 | - | FAIL |
| 48_match_nested_exhaustive | 0 | 0.0 | 0 | 88 | - | FAIL |
| 49_match_guards | 0 | 0.0 | 0 | 100 | - | FAIL |
| 49_tensor_literal | 0 | 0.0 | 0 | 35 | - | FAIL |
| 50_match_or_patterns | 189 | 10.4 | 2 | 103 | YES | PASS |
| 50_tensor_indexing | 0 | 0.0 | 0 | 25 | - | FAIL |
| 51_tensor_broadcast | 0 | 0.0 | 0 | 29 | - | FAIL |
| 52_tensor_slicing | 0 | 0.0 | 0 | 29 | - | FAIL |
| 53_linear_regression | 0 | 0.0 | 0 | 25 | - | FAIL |
| 54_const_basic | 131 | 8.0 | 1 | 77 | YES | PASS |
| 55_async_basic | 0 | 0.0 | 0 | 45 | - | FAIL |
| 56_async_await | 0 | 0.0 | 0 | 46 | - | FAIL |
| 57_real_await | 0 | 0.0 | 0 | 40 | - | FAIL |
| 58_async_file_io | 0 | 0.0 | 0 | 38 | - | FAIL |
| 58_const_scope | 166 | 9.1 | 2 | 80 | YES | PASS |
| 59_async_fanout | 0 | 0.0 | 0 | 31 | - | FAIL |
| 62_list_output | 0 | 0.0 | 0 | 106 | - | FAIL |
| 63_else_sino | 0 | 0.0 | 0 | 83 | - | FAIL |
| 64_closure_typed | 0 | 0.0 | 0 | 34 | - | FAIL |
| 65_list_int_indexing | 219 | 12.2 | 1 | 90 | YES | PASS |
| **Total** | | | | **5100** | **39/65** | **39/65** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 581 | 73 | 7.9x |
| 02_arithmetic | 7 | 88 | 0.1x |
| 03_function | 7 | 117 | 0.1x |
| 04_if_else | 6 | 111 | 0.1x |
| 05_for_loop | 5 | 114 | 0.0x |
| 06_struct | 6 | 102 | 0.1x |
| 07_enum_match | 16 | 131 | 0.1x |
| 08_list | 8 | 93 | 0.1x |
| 09_string_methods | 4 | 80 | 0.1x |
| 10_result | 6 | 100 | 0.1x |
| 11_closure | 4 | 103 | 0.0x |
| 12_while | 5 | 106 | 0.1x |
| 14_nested_struct | 4 | 72 | 0.1x |
| 15_multifunction | 5 | 82 | 0.1x |
| 16_string_escape | 4 | 71 | 0.1x |
| 17_option | 7 | 115 | 0.1x |
| 18_method_chain | 4 | 95 | 0.0x |
| 23_multi_return | 5 | 87 | 0.1x |
| 24_enum_methods | 5 | 85 | 0.1x |
| 25_fizzbuzz | 5 | 97 | 0.1x |
| 26_generics | 7 | 93 | 0.1x |
| 27_impl | 5 | 95 | 0.1x |
| 28_traits | 5 | 116 | 0.0x |
| 30_nested_generics | 5 | 74 | 0.1x |
| 32_generic_enum | 4 | 87 | 0.0x |
| 34_file_io | 5 | 69 | 0.1x |
| 35_stdin | 4 | 66 | 0.1x |
| 36_crypto | 4 | 83 | 0.1x |
| 37_regex | 4 | 76 | 0.1x |
| 38_http | 4 | 74 | 0.1x |
| 39_gpu_detect | 4 | 83 | 0.1x |
| 41_module_let | 4 | 73 | 0.1x |
| 42_module_let_string | 5 | 84 | 0.1x |
| 43_module_let_math | 4 | 79 | 0.1x |
| 45_ffi_bind | 5 | 72 | 0.1x |
| 50_match_or_patterns | 5 | 103 | 0.1x |
| 54_const_basic | 4 | 77 | 0.1x |
| 58_const_scope | 5 | 80 | 0.1x |
| 65_list_int_indexing | 5 | 90 | 0.1x |

