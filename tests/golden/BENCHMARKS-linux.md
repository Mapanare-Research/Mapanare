# Mapanare Benchmarks - Linux

Generated: 2026-04-07 13:15 UTC  
Version: 3.25.0 (`f33c2e5`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.9s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 607 | `....__._ v` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 7 | `         v` | PASS |
| 03_function | 8 | 78 | 2.4 | 2 | 6 | 73 | 6 | `         v` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 5 | `        ` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 5 | `        ` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `        ` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 7 | `        ` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 6 | `         v` | PASS |
| 09_string_methods | 5 | 85 | 3.2 | 1 | 6 | 51 | 5 | `         ^` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 6 | `         ^` | PASS |
| 11_closure | 5 | 108 | 3.7 | 1 | 8 | 97 | 6 | `        ` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 7 | `         ^` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 6 | `        ` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 5 | `         ^` | PASS |
| 15_multifunction | 12 | 128 | 4.0 | 3 | 10 | 130 | 5 | `         ^` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 4 | `_*-.- _. ^` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 6 | `_-... _- ^` | PASS |
| 18_method_chain | 9 | 121 | 4.7 | 1 | 8 | 84 | 5 | `_-.-.__. ^` | PASS |
| 19_nested_match | 18 | 206 | 7.1 | 2 | 15 | 194 | 6 | `_-.-.___` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 4 | `.--..__- ^` | PASS |
| 21_list_ops | 15 | 233 | 8.6 | 2 | 15 | 269 | 5 | `_.._.__. ^` | PASS |
| 22_string_builder | 14 | 140 | 5.0 | 2 | 10 | 116 | 4 | `.--.-__. ^` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 5 | ` .__-_ . ^` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 5 | `         ^` | PASS |
| 25_fizzbuzz | 18 | 198 | 6.4 | 2 | 19 | 166 | 5 | ` ___- _* ^` | PASS |
| 26_generics | 29 | 180 | 5.8 | 5 | 12 | 153 | 5 | `         ^` | PASS |
| 27_impl | 21 | 109 | 3.3 | 3 | 6 | 122 | 5 | `*---*__- ^` | PASS |
| 28_traits | 25 | 108 | 3.3 | 3 | 6 | 114 | 6 | `*.*** ..` | PASS |
| 29_generic_impl | 24 | 111 | 3.5 | 3 | 6 | 115 | 5 | `*  **  * ^` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 5 | `***.* ..` | PASS |
| 31_generic_multi | 35 | 160 | 5.3 | 4 | 8 | 165 | 6 | `         ^` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 4 | `.* ..` | PASS |
| **Total** | **436** | **3510** | **117.6** | **58** | **245** | **3177** | **773** | | **32/32** |

