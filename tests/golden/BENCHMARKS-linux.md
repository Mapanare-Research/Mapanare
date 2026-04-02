# Mapanare Benchmarks - Linux

Generated: 2026-04-01 05:24 UTC  
Version: 2.1.0 (`e553c4f`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.6s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 30 | 0.9 | 1 | 2 | 9 | 536 | `. .-_.__ ^` | PASS |
| **Total** | **3** | **30** | **0.9** | **1** | **2** | **9** | **536** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 69 | 3.0 | 1 | 67 | YES | PASS |
| **Total** | | | | **67** | **1/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 536 | 67 | 8.0x |

