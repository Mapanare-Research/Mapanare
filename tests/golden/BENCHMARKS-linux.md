# Mapanare Benchmarks - Linux

Generated: 2026-04-09 13:37 UTC  
Version: 4.13.0 (`13aaedc`)  
Platform: Linux x86_64, Python 3.12.3  
Total time: 0.7s  

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 33_break_continue | 58 | 428 | 13.0 | 5 | 36 | 446 | 581 | ` -  _  _ ^` | PASS |
| **Total** | **58** | **428** | **13.0** | **5** | **36** | **446** | **581** | | **1/1** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 33_break_continue | 329 | 11.9 | 5 | 75 | YES | PASS |
| **Total** | | | | **75** | **1/1** | **1/1** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 33_break_continue | 581 | 75 | 7.7x |

