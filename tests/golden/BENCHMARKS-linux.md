# Mapanare Benchmarks - Linux

Generated: 2026-03-21 04:20 UTC  
Version: 1.0.11 (`b082360`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 2.0s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 28 | 1.0 | 1 | 2 | 9 | 442 | ` _  __   ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 5 | `_*-__-_* ^` | PASS |
| 03_function | 8 | 63 | 1.7 | 2 | 4 | 57 | 4 | `_     _- ^` | PASS |
| 04_if_else | 8 | 32 | 1.0 | 1 | 4 | 9 | 4 | `__-_--__` | PASS |
| 05_for_loop | 7 | 77 | 2.4 | 1 | 5 | 58 | 4 | `.  . ..  v` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `- __  __` | PASS |
| 07_enum_match | 13 | 65 | 2.4 | 1 | 5 | 42 | 6 | `        ` | PASS |
| 08_list | 5 | 89 | 3.6 | 1 | 2 | 121 | 5 | `        ` | PASS |
| 09_string_methods | 5 | 62 | 2.5 | 1 | 2 | 35 | 5 | `         v` | PASS |
| 10_result | 14 | 141 | 5.7 | 2 | 10 | 132 | 6 | `        ` | PASS |
| 11_closure | 5 | 54 | 2.0 | 1 | 2 | 33 | 4 | `__-_____` | PASS |
| 12_while | 7 | 59 | 1.7 | 1 | 5 | 42 | 4 | `-_--___  v` | PASS |
| 13_fib | 10 | 100 | 2.8 | 2 | 7 | 98 | 4 | `--_-_-__` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `..*. ...` | PASS |
| 15_multifunction | 12 | 99 | 2.8 | 3 | 6 | 98 | 4 | `-_____-_ v` | PASS |
| **Total** | **119** | **992** | **33.6** | **20** | **60** | **833** | **506** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 90 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 94 | YES | PASS |
| 03_function | 74 | 3.0 | 2 | 86 | YES | PASS |
| 04_if_else | 75 | 3.1 | 1 | 90 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 85 | YES | PASS |
| 06_struct | 67 | 2.9 | 1 | 93 | YES | PASS |
| 07_enum_match | 67 | 2.8 | 1 | 83 | YES | PASS |
| 08_list | 85 | 3.7 | 1 | 140 | YES | PASS |
| 09_string_methods | 75 | 3.4 | 1 | 100 | YES | PASS |
| 10_result | 88 | 3.4 | 2 | 100 | YES | PASS |
| 11_closure | 75 | 3.0 | 1 | 89 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 85 | YES | PASS |
| 13_fib | 80 | 3.1 | 2 | 87 | YES | PASS |
| 14_nested_struct | 67 | 2.9 | 1 | 97 | YES | PASS |
| 15_multifunction | 85 | 3.4 | 3 | 84 | YES | PASS |
| **Total** | | | | **1401** | **15/15** | **15/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 442 | 90 | 4.9x |
| 02_arithmetic | 5 | 94 | 0.1x |
| 03_function | 4 | 86 | 0.0x |
| 04_if_else | 4 | 90 | 0.0x |
| 05_for_loop | 4 | 85 | 0.1x |
| 06_struct | 4 | 93 | 0.0x |
| 07_enum_match | 6 | 83 | 0.1x |
| 08_list | 5 | 140 | 0.0x |
| 09_string_methods | 5 | 100 | 0.1x |
| 10_result | 6 | 100 | 0.1x |
| 11_closure | 4 | 89 | 0.0x |
| 12_while | 4 | 85 | 0.0x |
| 13_fib | 4 | 87 | 0.1x |
| 14_nested_struct | 4 | 97 | 0.0x |
| 15_multifunction | 4 | 84 | 0.0x |

