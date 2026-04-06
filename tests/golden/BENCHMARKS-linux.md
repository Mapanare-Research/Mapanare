# Mapanare Benchmarks - Linux

Generated: 2026-04-06 00:32 UTC  
Version: 3.9.0 (`d8f9f13`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 527 | `._..__-_ v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `         v` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 5 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         v` | PASS |
| 05_for_loop | 7 | 71 | 2.1 | 1 | 5 | 58 | 4 | `        ` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 4 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `        ` | PASS |
| 08_list | 5 | 79 | 2.7 | 1 | 2 | 113 | 5 | `         ^` | PASS |
| 09_string_methods | 5 | 61 | 2.2 | 1 | 2 | 35 | 3 | `        ` | PASS |
| 10_result | 14 | 137 | 4.8 | 2 | 10 | 139 | 5 | `        ` | PASS |
| 11_closure | 5 | 77 | 2.4 | 1 | 4 | 73 | 4 | `        ` | PASS |
| 12_while | 7 | 58 | 1.6 | 1 | 5 | 42 | 4 | `        ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 5 | `         ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `        ` | PASS |
| 15_multifunction | 12 | 92 | 2.5 | 3 | 6 | 98 | 7 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 5 | `__.___._ v` | PASS |
| 17_option | 19 | 170 | 5.5 | 2 | 13 | 157 | 7 | `_._.__._ v` | PASS |
| 18_method_chain | 9 | 86 | 3.3 | 1 | 2 | 60 | 4 | `_-_._...` | PASS |
| 19_nested_match | 18 | 151 | 4.9 | 2 | 7 | 154 | 6 | `_____.._ v` | PASS |
| 20_recursion | 11 | 104 | 3.0 | 2 | 7 | 107 | 4 | `_____.-_ v` | PASS |
| 21_list_ops | 15 | 183 | 6.3 | 2 | 7 | 244 | 4 | `______-. v` | PASS |
| 22_string_builder | 14 | 117 | 4.0 | 2 | 7 | 107 | 5 | `_.__..-. v` | PASS |
| 23_multi_return | 15 | 93 | 3.1 | 2 | 4 | 98 | 6 | ` ___-__  v` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 6 | `        ` | PASS |
| 25_fizzbuzz | 18 | 175 | 5.4 | 2 | 16 | 157 | 5 | `  _.*_.  v` | PASS |
| 26_generics | 29 | 153 | 4.7 | 5 | 10 | 143 | 6 | ` *      ` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 5 | `__* - ^` | PASS |
| 28_traits | 24 | 96 | 2.7 | 3 | 6 | 98 | 6 | `` | PASS |
| **Total** | **340** | **2568** | **81.5** | **49** | **157** | **2412** | **662** | | **28/28** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 87 | 3.8 | 1 | 50 | YES | PASS |
| 02_arithmetic | 92 | 3.8 | 1 | 48 | YES | PASS |
| 03_function | 102 | 4.0 | 2 | 52 | YES | PASS |
| 04_if_else | 104 | 4.3 | 1 | 51 | YES | PASS |
| 05_for_loop | 115 | 4.7 | 1 | 56 | YES | PASS |
| 06_struct | 97 | 4.1 | 1 | 57 | YES | PASS |
| 07_enum_match | 109 | 4.6 | 1 | 55 | YES | PASS |
| 08_list | 119 | 5.1 | 1 | 58 | YES | PASS |
| 09_string_methods | 99 | 4.4 | 1 | 53 | YES | PASS |
| 10_result | 144 | 6.0 | 2 | 60 | YES | PASS |
| 11_closure | 105 | 4.2 | 1 | 53 | YES | PASS |
| 12_while | 125 | 4.9 | 1 | 59 | YES | PASS |
| 13_fib | 112 | 4.2 | 2 | 81 | YES | PASS |
| 14_nested_struct | 97 | 4.1 | 1 | 101 | YES | PASS |
| 15_multifunction | 110 | 4.2 | 3 | 89 | YES | PASS |
| 16_string_escape | 106 | 4.8 | 1 | 71 | YES | PASS |
| 17_option | 170 | 6.7 | 2 | 81 | YES | PASS |
| 18_method_chain | 116 | 5.2 | 1 | 46 | YES | PASS |
| 19_nested_match | 152 | 5.8 | 2 | 57 | YES | PASS |
| 20_recursion | 113 | 4.3 | 2 | 47 | YES | PASS |
| 21_list_ops | 178 | 7.3 | 2 | 58 | YES | PASS |
| 22_string_builder | 145 | 6.1 | 2 | 62 | YES | PASS |
| 23_multi_return | 128 | 5.2 | 2 | 73 | YES | PASS |
| 24_enum_methods | 133 | 5.5 | 2 | 63 | YES | PASS |
| 25_fizzbuzz | 162 | 6.1 | 2 | 49 | YES | PASS |
| 26_generics | 153 | 5.7 | 5 | 55 | YES | PASS |
| 27_impl | 126 | 5.0 | 3 | 56 | YES | PASS |
| 28_traits | 125 | 4.8 | 3 | 58 | YES | PASS |
| **Total** | | | | **1699** | **28/28** | **28/28** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 527 | 50 | 10.5x |
| 02_arithmetic | 6 | 48 | 0.1x |
| 03_function | 5 | 52 | 0.1x |
| 04_if_else | 4 | 51 | 0.1x |
| 05_for_loop | 4 | 56 | 0.1x |
| 06_struct | 4 | 57 | 0.1x |
| 07_enum_match | 5 | 55 | 0.1x |
| 08_list | 5 | 58 | 0.1x |
| 09_string_methods | 3 | 53 | 0.1x |
| 10_result | 5 | 60 | 0.1x |
| 11_closure | 4 | 53 | 0.1x |
| 12_while | 4 | 59 | 0.1x |
| 13_fib | 5 | 81 | 0.1x |
| 14_nested_struct | 5 | 101 | 0.1x |
| 15_multifunction | 7 | 89 | 0.1x |
| 16_string_escape | 5 | 71 | 0.1x |
| 17_option | 7 | 81 | 0.1x |
| 18_method_chain | 4 | 46 | 0.1x |
| 19_nested_match | 6 | 57 | 0.1x |
| 20_recursion | 4 | 47 | 0.1x |
| 21_list_ops | 4 | 58 | 0.1x |
| 22_string_builder | 5 | 62 | 0.1x |
| 23_multi_return | 6 | 73 | 0.1x |
| 24_enum_methods | 6 | 63 | 0.1x |
| 25_fizzbuzz | 5 | 49 | 0.1x |
| 26_generics | 6 | 55 | 0.1x |
| 27_impl | 5 | 56 | 0.1x |
| 28_traits | 6 | 58 | 0.1x |

