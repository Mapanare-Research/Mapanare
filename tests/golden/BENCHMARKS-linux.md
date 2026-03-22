# Mapanare Benchmarks - Linux

Generated: 2026-03-22 23:31 UTC  
Version: 1.0.11 (`f57aa01`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 451 | `  .___   v` | PASS |
| **Total** | **3** | **30** | **0.9** | **1** | **2** | **9** | **451** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 19 | - | FAIL |
| **Total** | | | | **19** | **0/1** | **0/1** |

