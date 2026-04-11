# Mapanare Benchmarks - Linux

Generated: 2026-04-11 08:03 UTC  
Version: 4.28.0 (`fe0d56e`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 606 | `.._..-._ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 7 | `         v` | PASS |
| 03_function | 8 | 73 | 2.2 | 2 | 6 | 65 | 6 | `        ` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 4 | `         ^` | PASS |
| 06_struct | 9 | 61 | 2.0 | 1 | 4 | 49 | 5 | `         v` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 6 | `        ` | PASS |
| 08_list | 5 | 103 | 3.9 | 1 | 6 | 121 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 88 | 3.3 | 1 | 6 | 51 | 3 | `         v` | PASS |
| 10_result | 14 | 142 | 5.0 | 2 | 10 | 147 | 5 | `         v` | PASS |
| 11_closure | 5 | 102 | 3.4 | 1 | 8 | 89 | 4 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 4 | `        ` | PASS |
| 13_fib | 10 | 112 | 3.3 | 2 | 9 | 106 | 4 | `        ` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 118 | 3.6 | 3 | 10 | 114 | 4 | `         v` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 5 | `  ._____` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 5 | `_._._-._ v` | PASS |
| 18_method_chain | 9 | 124 | 4.8 | 1 | 8 | 84 | 4 | `___._.__` | PASS |
| 19_nested_match | 18 | 199 | 6.8 | 2 | 15 | 186 | 6 | `__..._._ v` | PASS |
| 20_recursion | 11 | 130 | 4.0 | 2 | 11 | 123 | 5 | `        ` | PASS |
| 21_list_ops | 15 | 230 | 8.4 | 2 | 13 | 277 | 5 | `________` | PASS |
| 22_string_builder | 14 | 132 | 4.7 | 2 | 7 | 124 | 5 | `-._.....` | PASS |
| 23_multi_return | 15 | 119 | 4.2 | 2 | 8 | 114 | 4 | `     __  v` | PASS |
| 24_enum_methods | 20 | 109 | 3.8 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 186 | 5.9 | 2 | 16 | 166 | 5 | `___.__._ v` | PASS |
| 26_generics | 29 | 167 | 5.3 | 5 | 12 | 129 | 6 | `        ` | PASS |
| 27_impl | 21 | 99 | 2.8 | 3 | 6 | 106 | 5 | `      _  v` | PASS |
| 28_traits | 25 | 98 | 2.8 | 3 | 6 | 98 | 4 | ` _  ___  v` | PASS |
| 29_generic_impl | 24 | 101 | 3.1 | 3 | 6 | 99 | 4 | ` _    _  v` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 5 | ` _ _____` | PASS |
| 31_generic_multi | 35 | 145 | 4.7 | 4 | 8 | 141 | 6 | `        ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 4 | `        ` | PASS |
| 33_break_continue | 58 | 428 | 13.0 | 5 | 36 | 446 | 7 | `        ` | PASS |
| 34_file_io | 19 | 236 | 10.0 | 1 | 12 | 185 | 5 | `         v` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 4 | `__*_____` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 4 | `________` | PASS |
| 37_regex | 10 | 163 | 6.8 | 1 | 8 | 109 | 4 | `    . .  v` | PASS |
| 38_http | 5 | 74 | 2.7 | 1 | 6 | 49 | 4 | `_.  _ __` | PASS |
| 39_gpu_detect | 8 | 144 | 5.5 | 1 | 13 | 100 | 4 | `         ^` | PASS |
| 40_gpu_tensor | 18 | 389 | 16.7 | 1 | 25 | 478 | 6 | `         v` | PASS |
| 41_module_let | 13 | 53 | 1.5 | 2 | 4 | 26 | 4 | `        ` | PASS |
| 42_module_let_string | 19 | 57 | 1.7 | 2 | 4 | 26 | 4 | `     *  ` | PASS |
| 43_module_let_math | 19 | 57 | 1.7 | 2 | 4 | 26 | 5 | `        ` | PASS |
| 44_async_basic | 13 | 55 | 1.6 | 2 | 4 | 26 | 4 | `......**` | PASS |
| 45_ffi_bind | 15 | 121 | 3.3 | 3 | 9 | 123 | 4 | `  *   *  v` | PASS |
| 46_async_stream | 19 | 139 | 5.0 | 3 | 6 | 132 | 6 | `         v` | PASS |
| **Total** | **669** | **5606** | **194.0** | **84** | **388** | **4972** | **817** | | **46/46** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 120 | 5.7 | 1 | 54 | YES | PASS |
| 02_arithmetic | 125 | 5.8 | 1 | 58 | YES | PASS |
| 03_function | 135 | 6.0 | 2 | 58 | YES | PASS |
| 04_if_else | 137 | 6.3 | 1 | 60 | YES | PASS |
| 05_for_loop | 148 | 6.6 | 1 | 69 | YES | PASS |
| 06_struct | 130 | 6.0 | 1 | 59 | YES | PASS |
| 07_enum_match | 142 | 6.6 | 1 | 74 | YES | PASS |
| 08_list | 152 | 7.1 | 1 | 78 | YES | PASS |
| 09_string_methods | 133 | 6.4 | 1 | 61 | YES | PASS |
| 10_result | 177 | 8.0 | 2 | 68 | YES | PASS |
| 11_closure | 138 | 6.1 | 1 | 57 | YES | PASS |
| 12_while | 134 | 6.0 | 1 | 68 | YES | PASS |
| 13_fib | 145 | 6.2 | 2 | 55 | YES | PASS |
| 14_nested_struct | 130 | 6.0 | 1 | 57 | YES | PASS |
| 15_multifunction | 143 | 6.1 | 3 | 54 | YES | PASS |
| 16_string_escape | 139 | 6.7 | 1 | 51 | YES | PASS |
| 17_option | 203 | 8.6 | 2 | 59 | YES | PASS |
| 18_method_chain | 150 | 7.2 | 1 | 54 | YES | PASS |
| 19_nested_match | 185 | 7.8 | 2 | 72 | YES | PASS |
| 20_recursion | 146 | 6.3 | 2 | 61 | YES | PASS |
| 21_list_ops | 211 | 9.4 | 2 | 67 | YES | PASS |
| 22_string_builder | 178 | 8.1 | 2 | 68 | YES | PASS |
| 23_multi_return | 161 | 7.2 | 2 | 59 | YES | PASS |
| 24_enum_methods | 166 | 7.4 | 2 | 62 | YES | PASS |
| 25_fizzbuzz | 195 | 8.0 | 2 | 65 | YES | PASS |
| 26_generics | 192 | 7.9 | 5 | 59 | YES | PASS |
| 27_impl | 159 | 6.9 | 3 | 55 | YES | PASS |
| 28_traits | 161 | 6.9 | 3 | 55 | YES | PASS |
| 29_generic_impl | 168 | 7.4 | 3 | 55 | YES | PASS |
| 30_nested_generics | 160 | 7.8 | 1 | 55 | YES | PASS |
| 31_generic_multi | 186 | 8.3 | 4 | 57 | YES | PASS |
| 32_generic_enum | 137 | 6.3 | 1 | 53 | YES | PASS |
| 33_break_continue | 329 | 11.9 | 5 | 65 | YES | PASS |
| 34_file_io | 188 | 9.4 | 1 | 54 | YES | PASS |
| 35_stdin | 130 | 6.3 | 1 | 51 | YES | PASS |
| 36_crypto | 149 | 7.3 | 1 | 50 | YES | PASS |
| 37_regex | 170 | 8.4 | 1 | 53 | YES | PASS |
| 38_http | 126 | 6.0 | 1 | 57 | YES | PASS |
| 39_gpu_detect | 143 | 6.8 | 1 | 56 | YES | PASS |
| 40_gpu_tensor | 250 | 11.8 | 1 | 63 | YES | PASS |
| 41_module_let | 125 | 5.7 | 2 | 50 | YES | PASS |
| 42_module_let_string | 128 | 6.0 | 2 | 65 | YES | PASS |
| 43_module_let_math | 130 | 6.0 | 2 | 51 | YES | PASS |
| 44_async_basic | 131 | 6.0 | 2 | 53 | YES | PASS |
| 45_ffi_bind | 157 | 6.5 | 3 | 57 | YES | PASS |
| 46_async_stream | 168 | 7.7 | 3 | 50 | YES | PASS |
| **Total** | | | | **2711** | **46/46** | **46/46** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 606 | 54 | 11.2x |
| 02_arithmetic | 7 | 58 | 0.1x |
| 03_function | 6 | 58 | 0.1x |
| 04_if_else | 5 | 60 | 0.1x |
| 05_for_loop | 4 | 69 | 0.1x |
| 06_struct | 5 | 59 | 0.1x |
| 07_enum_match | 6 | 74 | 0.1x |
| 08_list | 6 | 78 | 0.1x |
| 09_string_methods | 3 | 61 | 0.1x |
| 10_result | 5 | 68 | 0.1x |
| 11_closure | 4 | 57 | 0.1x |
| 12_while | 4 | 68 | 0.1x |
| 13_fib | 4 | 55 | 0.1x |
| 14_nested_struct | 4 | 57 | 0.1x |
| 15_multifunction | 4 | 54 | 0.1x |
| 16_string_escape | 5 | 51 | 0.1x |
| 17_option | 5 | 59 | 0.1x |
| 18_method_chain | 4 | 54 | 0.1x |
| 19_nested_match | 6 | 72 | 0.1x |
| 20_recursion | 5 | 61 | 0.1x |
| 21_list_ops | 5 | 67 | 0.1x |
| 22_string_builder | 5 | 68 | 0.1x |
| 23_multi_return | 4 | 59 | 0.1x |
| 24_enum_methods | 5 | 62 | 0.1x |
| 25_fizzbuzz | 5 | 65 | 0.1x |
| 26_generics | 6 | 59 | 0.1x |
| 27_impl | 5 | 55 | 0.1x |
| 28_traits | 4 | 55 | 0.1x |
| 29_generic_impl | 4 | 55 | 0.1x |
| 30_nested_generics | 5 | 55 | 0.1x |
| 31_generic_multi | 6 | 57 | 0.1x |
| 32_generic_enum | 4 | 53 | 0.1x |
| 33_break_continue | 7 | 65 | 0.1x |
| 34_file_io | 5 | 54 | 0.1x |
| 35_stdin | 4 | 51 | 0.1x |
| 36_crypto | 4 | 50 | 0.1x |
| 37_regex | 4 | 53 | 0.1x |
| 38_http | 4 | 57 | 0.1x |
| 39_gpu_detect | 4 | 56 | 0.1x |
| 40_gpu_tensor | 6 | 63 | 0.1x |
| 41_module_let | 4 | 50 | 0.1x |
| 42_module_let_string | 4 | 65 | 0.1x |
| 43_module_let_math | 5 | 51 | 0.1x |
| 44_async_basic | 4 | 53 | 0.1x |
| 45_ffi_bind | 4 | 57 | 0.1x |
| 46_async_stream | 6 | 50 | 0.1x |

