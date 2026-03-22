# Mapanare Benchmarks - Windows

Generated: 2026-03-22 22:05 UTC  
Version: 1.0.11 (`d1a91c0`)  
Platform: Windows AMD64, Python 3.11.7  
Total time: 1.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 433 | `-*------ v` | PASS |
| **Total** | **3** | **30** | **0.9** | **1** | **2** | **9** | **433** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 0 | 0.0 | 0 | 1075 | - | FAIL |
| **Total** | | | | **1075** | **0/1** | **0/1** |

