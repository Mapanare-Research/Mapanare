# Mapanare Benchmarks - Linux

Generated: 2026-04-14 22:16 UTC  
Version: 4.122.0 (`b635435`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.8s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 65_list_int_indexing | 31 | 270 | 10.4 | 1 | 14 | 317 | 607 | ` ` | PASS |
| **Total** | **31** | **270** | **10.4** | **1** | **14** | **317** | **607** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 65_list_int_indexing | 226 | 12.2 | 1 | 194 | YES | PASS |
| **Total** | | | | **194** | **1/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 65_list_int_indexing | 607 | 194 | 3.1x |

