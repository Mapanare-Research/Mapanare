# Mapanare Benchmarks - Linux

Generated: 2026-04-06 23:08 UTC  
Version: 3.9.0 (`dc63a23`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 3.1s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 582 | `-_____.. v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 6 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         v` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 5 | `         v` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 3 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 5 | `         ^` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `         ^` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 4 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 5 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `_-.___ _ ^` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | `_-______` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | ` __.____` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `-._...__` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 5 | `___.____` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `..___ __` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `.-__..__` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 4 | ` _    _. ^` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 4 | `         v` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | `. ___ __` | PASS |
| 26_generics | 29 | 150 | 4.6 | 5 | 10 | 121 | 6 | `        ` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 7 | ` _-_*___` | PASS |
| 28_traits | 25 | 96 | 2.7 | 3 | 6 | 98 | 6 | `.......* ^` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 6 | `   **` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 6 | `  ` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 6 | ` *  v` | PASS |
| **Total** | **420** | **2920** | **93.3** | **57** | **173** | **2747** | **733** | | **31/31** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 47 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 53 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 54 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 53 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 68 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 63 | YES | PASS |
| 07_enum_match | 109 | 4.6 | 1 | 70 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 59 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 52 | YES | PASS |
| 10_result | 144 | 6.0 | 2 | 51 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 56 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 71 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 62 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 83 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 62 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 61 | YES | PASS |
| 17_option | 170 | 6.7 | 2 | 72 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 58 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 91 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 84 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 81 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 66 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 53 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 63 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 71 | YES | PASS |
| 26_generics | 158 | 5.9 | 5 | 80 | YES | PASS |
| 27_impl | 126 | 5.0 | 3 | 97 | YES | PASS |
| 28_traits | 128 | 4.9 | 3 | 95 | YES | PASS |
| 29_generic_impl | 135 | 5.4 | 3 | 75 | YES | PASS |
| 30_nested_generics | 127 | 5.9 | 1 | 63 | YES | PASS |
| 31_generic_multi | 153 | 6.3 | 4 | 87 | YES | PASS |
| **Total** | | | | **2100** | **31/31** | **31/31** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 582 | 47 | 12.3x |
| 02_arithmetic | 6 | 53 | 0.1x |
| 03_function | 6 | 54 | 0.1x |
| 04_if_else | 4 | 53 | 0.1x |
| 05_for_loop | 5 | 68 | 0.1x |
| 06_struct | 5 | 63 | 0.1x |
| 07_enum_match | 5 | 70 | 0.1x |
| 08_list | 6 | 59 | 0.1x |
| 09_string_methods | 3 | 52 | 0.1x |
| 10_result | 5 | 51 | 0.1x |
| 11_closure | 4 | 56 | 0.1x |
| 12_while | 4 | 71 | 0.1x |
| 13_fib | 4 | 62 | 0.1x |
| 14_nested_struct | 4 | 83 | 0.0x |
| 15_multifunction | 5 | 62 | 0.1x |
| 16_string_escape | 4 | 61 | 0.1x |
| 17_option | 5 | 72 | 0.1x |
| 18_method_chain | 4 | 58 | 0.1x |
| 19_nested_match | 6 | 91 | 0.1x |
| 20_recursion | 5 | 84 | 0.1x |
| 21_list_ops | 5 | 81 | 0.1x |
| 22_string_builder | 5 | 66 | 0.1x |
| 23_multi_return | 4 | 53 | 0.1x |
| 24_enum_methods | 4 | 63 | 0.1x |
| 25_fizzbuzz | 4 | 71 | 0.1x |
| 26_generics | 6 | 80 | 0.1x |
| 27_impl | 7 | 97 | 0.1x |
| 28_traits | 6 | 95 | 0.1x |
| 29_generic_impl | 6 | 75 | 0.1x |
| 30_nested_generics | 6 | 63 | 0.1x |
| 31_generic_multi | 6 | 87 | 0.1x |

