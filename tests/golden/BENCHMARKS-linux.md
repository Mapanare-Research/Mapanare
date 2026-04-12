# Mapanare Benchmarks - Linux

Generated: 2026-04-12 05:49 UTC  
Version: 4.34.0 (`d6b58d9`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 585 | `_____... v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 6 | `         ^` | PASS |
| 03_function | 8 | 73 | 2.2 | 2 | 6 | 65 | 6 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 4 | `        ` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 11 | `         v` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 88 | 3.3 | 1 | 6 | 51 | 4 | `        ` | PASS |
| 10_result | 14 | 142 | 5.0 | 2 | 10 | 147 | 6 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.4 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 5 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 4 | `         v` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 118 | 3.6 | 3 | 10 | 114 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 4 | `___ ____` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 6 | `.______. ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 5 | `______._ v` | PASS |
| 19_nested_match | 18 | 199 | 6.8 | 2 | 15 | 186 | 7 | `.__ _.__` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 230 | 8.5 | 2 | 13 | 277 | 5 | `.__ .___` | PASS |
| 22_string_builder | 14 | 132 | 4.7 | 2 | 7 | 124 | 5 | `..-_-_..` | PASS |
| 23_multi_return | 15 | 119 | 4.2 | 2 | 8 | 114 | 6 | ` _  _ .  v` | PASS |
| 24_enum_methods | 20 | 109 | 3.8 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 186 | 5.9 | 2 | 16 | 166 | 5 | `__  _ __` | PASS |
| 26_generics | 29 | 167 | 5.3 | 5 | 12 | 129 | 7 | `         ^` | PASS |
| 27_impl | 21 | 99 | 2.8 | 3 | 6 | 106 | 6 | `    _ _  v` | PASS |
| 28_traits | 25 | 98 | 2.8 | 3 | 6 | 98 | 5 | `__._____` | PASS |
| 29_generic_impl | 24 | 101 | 3.1 | 3 | 6 | 99 | 5 | `        ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | `___ _ __` | PASS |
| 31_generic_multi | 35 | 145 | 4.7 | 4 | 8 | 141 | 5 | `         v` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 428 | 13.1 | 5 | 36 | 446 | 9 | `        ` | PASS |
| 34_file_io | 19 | 236 | 10.1 | 1 | 12 | 185 | 5 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `_ ______` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 5 | `._...-._ v` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 4 | `.  .    ` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 4 | `   _ __  v` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 4 | `        ` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | `        ` | PASS |
| 41_module_let | 13 | 53 | 1.5 | 2 | 4 | 26 | 5 | `        ` | PASS |
| 42_module_let_string | 19 | 57 | 1.7 | 2 | 4 | 26 | 4 | `........` | PASS |
| 43_module_let_math | 19 | 57 | 1.7 | 2 | 4 | 26 | 5 | `   .    ` | PASS |
| 45_ffi_bind | 15 | 121 | 3.3 | 3 | 9 | 123 | 5 | ` ....**. v` | PASS |
| 47_try_operator | 32 | 288 | 10.6 | 4 | 23 | 279 | 7 | `        ` | PASS |
| 48_match_nested_exhaustive | 23 | 261 | 10.4 | 3 | 12 | 309 | 7 | `        ` | PASS |
| **Total** | **692** | **5961** | **209.1** | **86** | **413** | **5402** | **822** | | **46/46** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 120 | 7.5 | 1 | 54 | YES | PASS |
| 02_arithmetic | 125 | 7.5 | 1 | 54 | YES | PASS |
| 03_function | 135 | 7.8 | 2 | 57 | YES | PASS |
| 04_if_else | 137 | 8.1 | 1 | 57 | YES | PASS |
| 05_for_loop | 148 | 8.4 | 1 | 59 | YES | PASS |
| 06_struct | 130 | 7.8 | 1 | 59 | YES | PASS |
| 07_enum_match | 142 | 8.3 | 1 | 58 | YES | PASS |
| 08_list | 152 | 8.8 | 1 | 59 | YES | PASS |
| 09_string_methods | 133 | 8.2 | 1 | 55 | YES | PASS |
| 10_result | 177 | 9.7 | 2 | 63 | YES | PASS |
| 11_closure | 138 | 7.9 | 1 | 57 | YES | PASS |
| 12_while | 134 | 7.8 | 1 | 59 | YES | PASS |
| 13_fib | 145 | 8.0 | 2 | 57 | YES | PASS |
| 14_nested_struct | 130 | 7.8 | 1 | 59 | YES | PASS |
| 15_multifunction | 143 | 7.9 | 3 | 57 | YES | PASS |
| 16_string_escape | 139 | 8.5 | 1 | 53 | YES | PASS |
| 17_option | 203 | 10.4 | 2 | 63 | YES | PASS |
| 18_method_chain | 150 | 9.0 | 1 | 62 | YES | PASS |
| 19_nested_match | 185 | 9.6 | 2 | 63 | YES | PASS |
| 20_recursion | 146 | 8.1 | 2 | 68 | YES | PASS |
| 21_list_ops | 211 | 11.2 | 2 | 63 | YES | PASS |
| 22_string_builder | 178 | 9.8 | 2 | 66 | YES | PASS |
| 23_multi_return | 161 | 8.9 | 2 | 77 | YES | PASS |
| 24_enum_methods | 166 | 9.2 | 2 | 61 | YES | PASS |
| 25_fizzbuzz | 195 | 9.8 | 2 | 75 | YES | PASS |
| 26_generics | 192 | 9.7 | 5 | 67 | YES | PASS |
| 27_impl | 159 | 8.7 | 3 | 57 | YES | PASS |
| 28_traits | 161 | 8.7 | 3 | 59 | YES | PASS |
| 29_generic_impl | 168 | 9.1 | 3 | 61 | YES | PASS |
| 30_nested_generics | 160 | 9.6 | 1 | 57 | YES | PASS |
| 31_generic_multi | 186 | 10.0 | 4 | 58 | YES | PASS |
| 32_generic_enum | 137 | 8.1 | 1 | 56 | YES | PASS |
| 33_break_continue | 329 | 13.7 | 5 | 65 | YES | PASS |
| 34_file_io | 188 | 11.2 | 1 | 56 | YES | PASS |
| 35_stdin | 130 | 8.1 | 1 | 59 | YES | PASS |
| 36_crypto | 149 | 9.0 | 1 | 59 | YES | PASS |
| 37_regex | 170 | 10.1 | 1 | 56 | YES | PASS |
| 38_http | 126 | 7.8 | 1 | 56 | YES | PASS |
| 39_gpu_detect | 143 | 8.6 | 1 | 66 | YES | PASS |
| 40_gpu_tensor | 250 | 13.6 | 1 | 65 | YES | PASS |
| 41_module_let | 125 | 7.5 | 2 | 57 | YES | PASS |
| 42_module_let_string | 128 | 7.7 | 2 | 60 | YES | PASS |
| 43_module_let_math | 130 | 7.8 | 2 | 57 | YES | PASS |
| 45_ffi_bind | 157 | 8.2 | 3 | 54 | YES | PASS |
| 47_try_operator | 242 | 12.4 | 4 | 62 | YES | PASS |
| 48_match_nested_exhaustive | 213 | 11.6 | 3 | 60 | YES | PASS |
| **Total** | | | | **2763** | **46/46** | **46/46** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 585 | 54 | 10.9x |
| 02_arithmetic | 6 | 54 | 0.1x |
| 03_function | 6 | 57 | 0.1x |
| 04_if_else | 5 | 57 | 0.1x |
| 05_for_loop | 4 | 59 | 0.1x |
| 06_struct | 5 | 59 | 0.1x |
| 07_enum_match | 11 | 58 | 0.2x |
| 08_list | 5 | 59 | 0.1x |
| 09_string_methods | 4 | 55 | 0.1x |
| 10_result | 6 | 63 | 0.1x |
| 11_closure | 4 | 57 | 0.1x |
| 12_while | 5 | 59 | 0.1x |
| 13_fib | 4 | 57 | 0.1x |
| 14_nested_struct | 4 | 59 | 0.1x |
| 15_multifunction | 4 | 57 | 0.1x |
| 16_string_escape | 4 | 53 | 0.1x |
| 17_option | 6 | 63 | 0.1x |
| 18_method_chain | 5 | 62 | 0.1x |
| 19_nested_match | 7 | 63 | 0.1x |
| 20_recursion | 5 | 68 | 0.1x |
| 21_list_ops | 5 | 63 | 0.1x |
| 22_string_builder | 5 | 66 | 0.1x |
| 23_multi_return | 6 | 77 | 0.1x |
| 24_enum_methods | 5 | 61 | 0.1x |
| 25_fizzbuzz | 5 | 75 | 0.1x |
| 26_generics | 7 | 67 | 0.1x |
| 27_impl | 6 | 57 | 0.1x |
| 28_traits | 5 | 59 | 0.1x |
| 29_generic_impl | 5 | 61 | 0.1x |
| 30_nested_generics | 5 | 57 | 0.1x |
| 31_generic_multi | 5 | 58 | 0.1x |
| 32_generic_enum | 4 | 56 | 0.1x |
| 33_break_continue | 9 | 65 | 0.1x |
| 34_file_io | 5 | 56 | 0.1x |
| 35_stdin | 4 | 59 | 0.1x |
| 36_crypto | 5 | 59 | 0.1x |
| 37_regex | 4 | 56 | 0.1x |
| 38_http | 4 | 56 | 0.1x |
| 39_gpu_detect | 4 | 66 | 0.1x |
| 40_gpu_tensor | 6 | 65 | 0.1x |
| 41_module_let | 5 | 57 | 0.1x |
| 42_module_let_string | 4 | 60 | 0.1x |
| 43_module_let_math | 5 | 57 | 0.1x |
| 45_ffi_bind | 5 | 54 | 0.1x |
| 47_try_operator | 7 | 62 | 0.1x |
| 48_match_nested_exhaustive | 7 | 60 | 0.1x |

