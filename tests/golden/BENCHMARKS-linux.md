# Mapanare Benchmarks - Linux

Generated: 2026-04-08 16:37 UTC  
Version: 3.43.0 (`446e62b`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 507 | `_.______ ^` | PASS |
| 02_arithmetic | 4 | 44 | 1.4 | 1 | 4 | 25 | 5 | `        ` | PASS |
| 03_function | 8 | 71 | 2.1 | 2 | 6 | 65 | 5 | `         ^` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 4 | `         ^` | PASS |
| 05_for_loop | 7 | 90 | 2.9 | 1 | 7 | 67 | 4 | `         v` | PASS |
| 06_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 4 | `         ^` | PASS |
| 07_enum_match | 13 | 65 | 2.1 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 101 | 3.8 | 1 | 6 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 85 | 3.2 | 1 | 6 | 51 | 4 | `         ^` | PASS |
| 10_result | 14 | 140 | 4.9 | 2 | 10 | 147 | 5 | `         v` | PASS |
| 11_closure | 5 | 100 | 3.3 | 1 | 8 | 89 | 4 | `         v` | PASS |
| 12_while | 7 | 71 | 2.2 | 1 | 7 | 50 | 3 | `         v` | PASS |
| 13_fib | 10 | 110 | 3.2 | 2 | 9 | 106 | 3 | `        ` | PASS |
| 14_nested_struct | 9 | 59 | 2.0 | 1 | 4 | 49 | 4 | `         v` | PASS |
| 15_multifunction | 12 | 116 | 3.5 | 3 | 10 | 114 | 4 | `        ` | PASS |
| 16_string_escape | 8 | 54 | 1.9 | 1 | 2 | 27 | 3 | `.___.__  v` | PASS |
| 17_option | 19 | 186 | 6.2 | 2 | 15 | 173 | 5 | `.__-.___` | PASS |
| 18_method_chain | 9 | 121 | 4.7 | 1 | 8 | 84 | 4 | `__._____` | PASS |
| 19_nested_match | 18 | 197 | 6.7 | 2 | 15 | 186 | 5 | `.*- __  ` | PASS |
| 20_recursion | 11 | 128 | 4.0 | 2 | 11 | 123 | 4 | `        ` | PASS |
| 21_list_ops | 15 | 224 | 8.2 | 2 | 13 | 269 | 6 | `_~-__._  v` | PASS |
| 22_string_builder | 14 | 126 | 4.4 | 2 | 7 | 116 | 6 | `_.-_..__` | PASS |
| 23_multi_return | 15 | 117 | 4.1 | 2 | 8 | 114 | 6 | `.___ _.  v` | PASS |
| 24_enum_methods | 20 | 107 | 3.8 | 2 | 8 | 82 | 5 | `         v` | PASS |
| 25_fizzbuzz | 18 | 184 | 5.8 | 2 | 16 | 166 | 5 | `_..   _  v` | PASS |
| 26_generics | 29 | 164 | 5.2 | 5 | 12 | 129 | 6 | `         v` | PASS |
| 27_impl | 21 | 97 | 2.7 | 3 | 6 | 106 | 4 | `        ` | PASS |
| 28_traits | 25 | 96 | 2.8 | 3 | 6 | 98 | 4 | `.__     ` | PASS |
| 29_generic_impl | 24 | 99 | 3.0 | 3 | 6 | 99 | 5 | `        ` | PASS |
| 30_nested_generics | 20 | 113 | 4.2 | 1 | 2 | 117 | 4 | `.       ` | PASS |
| 31_generic_multi | 35 | 143 | 4.6 | 4 | 8 | 141 | 5 | `         v` | PASS |
| 32_generic_enum | 16 | 37 | 1.1 | 1 | 2 | 18 | 4 | `______-_ v` | PASS |
| 33_break_continue | 58 | 402 | 12.2 | 5 | 36 | 398 | 7 | ` __   _  v` | PASS |
| 34_file_io | 19 | 232 | 9.9 | 1 | 12 | 185 | 5 | `  *    v` | PASS |
| 35_stdin | 4 | 90 | 3.5 | 1 | 8 | 65 | 4 | `  **  v` | PASS |
| 36_crypto | 13 | 145 | 5.8 | 1 | 12 | 108 | 4 | ` *  v` | PASS |
| 37_regex | 10 | 159 | 6.7 | 1 | 8 | 109 | 5 | `   ` | PASS |
| 38_http | 5 | 72 | 2.7 | 1 | 6 | 49 | 4 | ` *  v` | PASS |
| **Total** | **545** | **4468** | **152.9** | **68** | **319** | **3955** | **674** | | **38/38** |

