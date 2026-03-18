# Mapanare Benchmarks - Linux

Generated: 2026-03-18 05:36 UTC  
Version: 1.0.10 (`c17bbb5`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 1.2s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 28 | 1.0 | 1 | 2 | 9 | 586 | `_. .___* ^` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 6 | `_______* ^` | PASS |
| 03_function | 8 | 63 | 1.7 | 2 | 4 | 57 | 5 | `    .  . ^` | PASS |
| 04_if_else | 8 | 32 | 1.0 | 1 | 4 | 9 | 4 | `.......* ^` | PASS |
| 05_for_loop | 7 | 77 | 2.3 | 1 | 5 | 58 | 5 | `* **   * ^` | PASS |
| 06_struct | 9 | 46 | 1.4 | 1 | 2 | 41 | 5 | `. .....* ^` | PASS |
| 07_enum_match | 13 | 65 | 2.3 | 1 | 5 | 42 | 5 | `         ^` | PASS |
| 08_list | 5 | 89 | 3.4 | 1 | 2 | 121 | 5 | `         ^` | PASS |
| 09_string_methods | 5 | 62 | 2.5 | 1 | 2 | 35 | 4 | `         ^` | PASS |
| 10_result | 14 | 141 | 5.5 | 2 | 10 | 132 | 6 | `.. . ..* ^` | PASS |
| 11_closure | 5 | 54 | 2.0 | 1 | 2 | 33 | 4 | `*.......` | PASS |
| 12_while | 7 | 59 | 1.7 | 1 | 5 | 42 | 5 | `.......* ^` | PASS |
| 13_fib | 10 | 100 | 2.6 | 2 | 7 | 98 | 4 | `.*.....* ^` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 4 | `.......* ^` | PASS |
| 15_multifunction | 12 | 99 | 2.6 | 3 | 6 | 98 | 4 | `_______- ^` | PASS |
| **Total** | **119** | **992** | **32.4** | **20** | **60** | **833** | **652** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 64 | 2.8 | 1 | 31 | YES | PASS |
| 02_arithmetic | 67 | 2.8 | 1 | 30 | YES | PASS |
| 03_function | 71 | 2.9 | 2 | 29 | YES | PASS |
| 04_if_else | 80 | 3.4 | 1 | 33 | YES | PASS |
| 05_for_loop | 73 | 3.0 | 1 | 33 | YES | PASS |
| 06_struct | 71 | 3.0 | 1 | 29 | YES | PASS |
| 07_enum_match | 0 | 0.0 | 0 | 27 | - | FAIL |
| 08_list | 65 | 2.8 | 1 | 26 | YES | PASS |
| 09_string_methods | 0 | 0.0 | 0 | 28 | - | FAIL |
| 10_result | 61 | 2.7 | 1 | 24 | DIFF | PASS |
| 11_closure | 74 | 3.0 | 1 | 32 | YES | PASS |
| 12_while | 67 | 2.8 | 1 | 32 | YES | PASS |
| 13_fib | 83 | 3.1 | 2 | 31 | YES | PASS |
| 14_nested_struct | 71 | 3.0 | 1 | 29 | YES | PASS |
| 15_multifunction | 81 | 3.1 | 3 | 31 | YES | PASS |
| **Total** | | | | **445** | **12/15** | **13/15** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 586 | 31 | 18.9x |
| 02_arithmetic | 6 | 30 | 0.2x |
| 03_function | 5 | 29 | 0.2x |
| 04_if_else | 4 | 33 | 0.1x |
| 05_for_loop | 5 | 33 | 0.1x |
| 06_struct | 5 | 29 | 0.2x |
| 08_list | 5 | 26 | 0.2x |
| 10_result | 6 | 24 | 0.2x |
| 11_closure | 4 | 32 | 0.1x |
| 12_while | 5 | 32 | 0.1x |
| 13_fib | 4 | 31 | 0.1x |
| 14_nested_struct | 4 | 29 | 0.1x |
| 15_multifunction | 4 | 31 | 0.1x |

