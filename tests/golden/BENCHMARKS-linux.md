# Mapanare Benchmarks - Linux

Generated: 2026-04-07 20:53 UTC  
Version: 3.32.0 (`010ce2c`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 811 | `_._..... v` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 7 | `         v` | PASS |
| 03_function | 8 | 71 | 2.1 | 2 | 6 | 65 | 8 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 6 | `         v` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 6 | `      _  v` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 8 | `         v` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 7 | `         v` | PASS |
| 09_string_methods | 5 | 85 | 3.2 | 1 | 6 | 51 | 6 | `         v` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 8 | `         v` | PASS |
| 11_closure | 5 | 101 | 3.4 | 1 | 8 | 89 | 6 | `         v` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 5 | `         v` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 5 | `         v` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 6 | `         v` | PASS |
| 15_multifunction | 12 | 116 | 3.5 | 3 | 10 | 114 | 5 | `         v` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 5 | ` _.___._ v` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 6 | ` _-. _-_ v` | PASS |
| 18_method_chain | 9 | 121 | 4.7 | 1 | 8 | 84 | 5 | `__.. _-_ v` | PASS |
| 19_nested_match | 18 | 195 | 6.7 | 2 | 15 | 186 | 7 | `______*_ v` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 5 | `__-___-_ v` | PASS |
| 21_list_ops | 15 | 233 | 8.6 | 2 | 15 | 269 | 6 | `__.___.  v` | PASS |
| 22_string_builder | 14 | 140 | 5.0 | 2 | 10 | 116 | 6 | `__.___*_ v` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 5 | `_ ._  _  v` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 198 | 6.4 | 2 | 19 | 166 | 5 | ` _*_._  ` | PASS |
| 26_generics | 29 | 163 | 5.1 | 5 | 12 | 129 | 7 | `         v` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 6 | `__-_*__  v` | PASS |
| 28_traits | 25 | 96 | 2.8 | 3 | 6 | 98 | 5 | ` ..** .  v` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 5 | `..*.* .  v` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 5 | ` ......  v` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 5 | `        ` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 4 | `_--____  v` | PASS |
| **Total** | **436** | **3403** | **113.6** | **58** | **245** | **3041** | **989** | | **32/32** |

