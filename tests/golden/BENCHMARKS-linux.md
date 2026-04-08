# Mapanare Benchmarks - Linux

Generated: 2026-04-08 15:41 UTC  
Version: 3.40.0 (`45bd3e4`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 34_file_io | 19 | 232 | 9.9 | 1 | 12 | 185 | 515 | `  ` | PASS |
| **Total** | **19** | **232** | **9.9** | **1** | **12** | **185** | **515** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 34_file_io | 152 | 7.5 | 1 | 68 | YES | PASS |
| **Total** | | | | **68** | **1/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 34_file_io | 515 | 68 | 7.6x |

