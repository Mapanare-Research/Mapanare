# Mapanare Benchmarks - Linux

Generated: 2026-04-09 22:23 UTC  
Version: 4.23.0 (`db400df`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 46_async_stream | 19 | 139 | 5.0 | 3 | 6 | 132 | 591 | `` | PASS |
| **Total** | **19** | **139** | **5.0** | **3** | **6** | **132** | **591** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 46_async_stream | 168 | 7.7 | 3 | 59 | YES | PASS |
| **Total** | | | | **59** | **1/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 46_async_stream | 591 | 59 | 10.1x |

