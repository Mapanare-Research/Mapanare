# Mapanare Benchmarks - Linux

Generated: 2026-04-06 01:21 UTC  
Version: 3.9.0 (`e5ffb05`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 517 | `__-____. ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `        ` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 6 | `         v` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 6 | `        ` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 5 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 7 | `         v` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 5 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `         ^` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `__._. __` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 5 | `__._-___` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 5 | `_...____` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `_.._____` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 5 | `_.-___-_ v` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 5 | `__-. _._ v` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `..-..-_. ^` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 4 | `-__ ..  ` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 4 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 4 | `*_. _. _ ^` | PASS |
| 26_generics | 29 | 153 | 4.7 | 5 | 10 | 143 | 5 | `     ~   v` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 5 | `_* -___- ^` | PASS |
| 28_traits | 25 | 96 | 2.7 | 3 | 6 | 98 | 5 | `*. * ^` | PASS |
| **Total** | **341** | **2568** | **81.5** | **49** | **157** | **2412** | **654** | | **28/28** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 49 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 47 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 51 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 56 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 62 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 71 | YES | PASS |
| 07_enum_match | 109 | 4.6 | 1 | 75 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 74 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 58 | YES | PASS |
| 10_result | 144 | 6.0 | 2 | 62 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 59 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 57 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 61 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 83 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 68 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 46 | YES | PASS |
| 17_option | 170 | 6.7 | 2 | 69 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 55 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 61 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 60 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 74 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 71 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 51 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 60 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 57 | YES | PASS |
| 26_generics | 158 | 5.9 | 5 | 53 | YES | PASS |
| 27_impl | 126 | 5.0 | 3 | 72 | YES | PASS |
| 28_traits | 128 | 4.9 | 3 | 66 | YES | PASS |
| **Total** | | | | **1728** | **28/28** | **28/28** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 517 | 49 | 10.6x |
| 02_arithmetic | 6 | 47 | 0.1x |
| 03_function | 5 | 51 | 0.1x |
| 04_if_else | 5 | 56 | 0.1x |
| 05_for_loop | 4 | 62 | 0.1x |
| 06_struct | 5 | 71 | 0.1x |
| 07_enum_match | 6 | 75 | 0.1x |
| 08_list | 6 | 74 | 0.1x |
| 09_string_methods | 5 | 58 | 0.1x |
| 10_result | 7 | 62 | 0.1x |
| 11_closure | 5 | 59 | 0.1x |
| 12_while | 4 | 57 | 0.1x |
| 13_fib | 5 | 61 | 0.1x |
| 14_nested_struct | 5 | 83 | 0.1x |
| 15_multifunction | 5 | 68 | 0.1x |
| 16_string_escape | 4 | 46 | 0.1x |
| 17_option | 5 | 69 | 0.1x |
| 18_method_chain | 5 | 55 | 0.1x |
| 19_nested_match | 6 | 61 | 0.1x |
| 20_recursion | 5 | 60 | 0.1x |
| 21_list_ops | 5 | 74 | 0.1x |
| 22_string_builder | 5 | 71 | 0.1x |
| 23_multi_return | 4 | 51 | 0.1x |
| 24_enum_methods | 4 | 60 | 0.1x |
| 25_fizzbuzz | 4 | 57 | 0.1x |
| 26_generics | 5 | 53 | 0.1x |
| 27_impl | 5 | 72 | 0.1x |
| 28_traits | 5 | 66 | 0.1x |

