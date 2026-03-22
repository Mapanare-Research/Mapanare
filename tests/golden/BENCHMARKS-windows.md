# Mapanare Benchmarks - Windows

Generated: 2026-03-22 22:58 UTC  
Version: 1.0.11 (`e7b0dd9`)  
Platform: Windows AMD64, Python 3.11.7  
Total time: 18.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 446 | `*------- v` | PASS |
| 02_arithmetic | 4 | 31 | 0.9 | 1 | 2 | 17 | 4 | ` --* ^` | PASS |
| 03_function | 8 | 58 | 1.6 | 2 | 4 | 57 | 2 | ` ***` | PASS |
| 04_if_else | 8 | 34 | 0.9 | 1 | 4 | 9 | 1 | ` ***` | PASS |
| 05_for_loop | 7 | 72 | 2.2 | 1 | 5 | 58 | 1 | `    ` | PASS |
| 06_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 2 | ` ***` | PASS |
| 07_enum_match | 13 | 65 | 2.2 | 1 | 5 | 42 | 3 | ` ***` | PASS |
| 08_list | 5 | 81 | 3.1 | 1 | 2 | 113 | 2 | `  *  v` | PASS |
| 09_string_methods | 5 | 61 | 2.3 | 1 | 2 | 35 | 1 | `    ` | PASS |
| 10_result | 14 | 139 | 5.4 | 2 | 10 | 139 | 3 | `* **` | PASS |
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 1 | `    ` | PASS |
| 12_while | 7 | 58 | 1.7 | 1 | 5 | 42 | 1 | ` *  ` | PASS |
| 13_fib | 10 | 97 | 2.7 | 2 | 7 | 98 | 1 | `**  ` | PASS |
| 14_nested_struct | 9 | 46 | 1.5 | 1 | 2 | 41 | 2 | `    ` | PASS |
| 15_multifunction | 12 | 92 | 2.6 | 3 | 6 | 98 | 1 | `*   ` | PASS |
| **Total** | **119** | **990** | **32.0** | **20** | **62** | **872** | **472** | | **15/15** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 1400 | - | FAIL |
| 02_arithmetic | 0 | 0.0 | 0 | 1305 | - | FAIL |
| 03_function | 0 | 0.0 | 0 | 1264 | - | FAIL |
| 04_if_else | 0 | 0.0 | 0 | 1276 | - | FAIL |
| 05_for_loop | 0 | 0.0 | 0 | 1282 | - | FAIL |
| 06_struct | 0 | 0.0 | 0 | 1302 | - | FAIL |
| 07_enum_match | 0 | 0.0 | 0 | 1262 | - | FAIL |
| 08_list | 0 | 0.0 | 0 | 1259 | - | FAIL |
| 09_string_methods | 0 | 0.0 | 0 | 1280 | - | FAIL |
| 10_result | 0 | 0.0 | 0 | 1047 | - | FAIL |
| 11_closure | 0 | 0.0 | 0 | 1065 | - | FAIL |
| 12_while | 0 | 0.0 | 0 | 1023 | - | FAIL |
| 13_fib | 0 | 0.0 | 0 | 1059 | - | FAIL |
| 14_nested_struct | 0 | 0.0 | 0 | 966 | - | FAIL |
| 15_multifunction | 0 | 0.0 | 0 | 1063 | - | FAIL |
| **Total** | | | | **17853** | **0/15** | **0/15** |

