# Mapanare Benchmarks - Linux

Generated: 2026-03-21 08:04 UTC  
Version: 1.0.11 (`b6df42f`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.5s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 11_closure | 5 | 80 | 2.6 | 1 | 4 | 73 | 437 | `        ` | PASS |
| **Total** | **5** | **80** | **2.6** | **1** | **4** | **73** | **437** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 11_closure | 75 | 3.0 | 1 | 95 | DIFF | PASS |
| **Total** | | | | **95** | **0/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 11_closure | 437 | 95 | 4.6x |

