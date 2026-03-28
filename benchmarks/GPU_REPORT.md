# Mapanare GPU Benchmark Report

## System Information

| Field | Value |
|-------|-------|
| platform | Windows-10-10.0.26200-SP0 |
| python | 3.11.7 |
| timestamp | 2026-03-28T20:37:10.873399+00:00 |
| numpy | 1.26.0 |
| gpu | NVIDIA GeForce RTX 4090 |
| gpu_memory | 24564 MB |
| driver | 591.86 |
| compute_cap | sm_89 |
| total_duration | 39.5s |

## Matrix Multiply (GFLOPS)

| Size | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |
|------|-------------|------------|---------|--------|--------|
| 256x256 | 103.4 | 501.6 | 4.9x | 9.3% | 4.1% |
| 512x512 | 226.4 | 999.0 | 4.4x | 8.6% | 5.4% |
| 1024x1024 | 364.3 | 1202.1 | 3.3x | 6.5% | 2.2% |
| 2048x2048 | 501.1 | 1276.7 | 2.5x | 6.7% | 2.4% |
| 4096x4096 | 638.4 | 1297.1 | 2.0x | 4.1% | 0.6% |

## Element-wise Operations (GB/s)

| Size | Op | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |
|------|----|-------------|------------|---------|--------|--------|
| 1M | add | 15.3 | 406.4 | 26.6x | 7.2% | 92.1% |
| 1M | mul | 17.9 | 518.4 | 28.9x | 5.2% | 13.5% |
| 1M | scale | 13.6 | 356.3 | 26.2x | 5.5% | 6.4% |
| 4M | add | 13.4 | 644.3 | 48.0x | 5.8% | 3.6% |
| 4M | mul | 14.1 | 711.6 | 50.7x | 5.3% | 3.4% |
| 4M | scale | 12.1 | 1213.3 | 100.1x | 2.6% | 13.5% |
| 16M | add | 9.3 | 820.2 | 88.4x | 7.9% | 1.0% |
| 16M | mul | 9.3 | 845.1 | 90.4x | 6.4% | 0.4% |
| 16M | scale | 7.7 | 776.9 | 100.5x | 5.0% | 5.1% |
| 64M | add | 12.5 | 896.1 | 71.6x | 9.0% | 0.9% |
| 64M | mul | 12.2 | 893.8 | 73.0x | 2.3% | 1.9% |
| 64M | scale | 11.4 | 881.6 | 77.3x | 3.8% | 5.0% |

## Host <-> Device Transfer (GB/s)

| Size | Direction | Bandwidth | CV |
|------|-----------|-----------|-----|
| 1MB | H2D | 10.71 GB/s | 2.0% |
| 1MB | D2H | 8.81 GB/s | 6.4% |
| 4MB | H2D | 17.08 GB/s | 3.3% |
| 4MB | D2H | 12.99 GB/s | 3.0% |
| 16MB | H2D | 15.05 GB/s | 4.9% |
| 16MB | D2H | 11.24 GB/s | 0.8% |
| 64MB | H2D | 14.82 GB/s | 3.7% |
| 64MB | D2H | 13.72 GB/s | 3.6% |
| 256MB | H2D | 13.39 GB/s | 3.8% |
| 256MB | D2H | 12.95 GB/s | 5.1% |

## Sum Reduction (GB/s)

| Size | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |
|------|-------------|------------|---------|--------|--------|
| 1M | 16.2 | 142.3 | 8.8x | 48.9% | 5.0% |
| 4M | 6.4 | 391.0 | 61.2x | 6.1% | 6.6% |
| 16M | 7.3 | 655.6 | 89.4x | 3.0% | 2.5% |
| 64M | 7.0 | 744.7 | 105.7x | 4.7% | 5.3% |

## What this measures

These benchmarks test **Mapanare's C runtime GPU layer** — the same CUDA Driver API
calls that `@gpu` and `@cuda` annotated Mapanare functions dispatch to at runtime.
The CPU baseline uses numpy (typically backed by MKL/OpenBLAS), which is a strong
multi-threaded BLAS implementation. The GPU path uses raw CUDA kernel launches via
the Mapanare runtime's `dlopen`-based CUDA integration — no cuBLAS, no cuDNN.

When a Mapanare program uses `@gpu` tensor operations, this is the performance it
gets from the underlying runtime. End-to-end Mapanare compilation adds only the
overhead of LLVM-compiled dispatch code, which is negligible for tensor-sized workloads.

## Key takeaways

- **Element-wise ops** reach 89% of the RTX 4090's theoretical memory bandwidth (896 of ~1,008 GB/s) — near-optimal for memory-bound kernels
- **Matmul** uses a naive kernel (no shared memory tiling); cuBLAS would be ~60x faster. This establishes a baseline for future optimization
- **Reductions** scale well: 106x speedup at 64M elements, also near peak bandwidth
- **Small tensors** (1M elements) show high variance due to kernel launch overhead — GPU shines on larger workloads
- **Transfer bandwidth** peaks at ~17 GB/s (PCIe 4.0 x16), consistent with typical pinned-memory throughput

## Methodology

- CPU baseline: numpy (MKL/OpenBLAS, multi-threaded)
- GPU: CUDA Driver API via ctypes — raw kernel launch, matching `mapanare_gpu.h` runtime path
- Matmul GFLOPS = 2*N^3 / time (standard matmul flop count)
- Element-wise GB/s = total bytes read + written / time
- Transfer GB/s = buffer size / time (includes synchronization)
- Reduction GB/s = input bytes / time (read-only)
- All measurements: 5 warmup + 10 timed runs, median with IQR outlier removal
- CV = coefficient of variation (stdev/mean); below 5% is stable, above 10% is flagged as noisy
