"""GPU Benchmark: Host <-> Device Transfer Bandwidth.

Measures PCIe transfer throughput for host-to-device (H2D) and
device-to-host (D2H) memory copies at various buffer sizes.

Sizes: 1MB, 4MB, 16MB, 64MB, 256MB
Metric: GB/s
Warmup: 5 runs, Timed: 10 runs, Median with IQR outlier removal
"""

from __future__ import annotations

import ctypes
import sys

import numpy as np

from benchmarks.gpu._bench_utils import BenchResult, format_size, timed_runs
from benchmarks.gpu._cuda_helpers import (
    CUDAContext,
    cuda_free,
    cuda_init,
    cuda_malloc,
    cuda_memcpy_dtoh,
    cuda_memcpy_htod,
    cuda_shutdown,
    cuda_synchronize,
)

SIZES_BYTES = [
    1 * 1024 * 1024,       # 1 MB
    4 * 1024 * 1024,       # 4 MB
    16 * 1024 * 1024,      # 16 MB
    64 * 1024 * 1024,      # 64 MB
    256 * 1024 * 1024,     # 256 MB
]


def _bench_h2d(ctx: CUDAContext, size_bytes: int) -> tuple[float, float]:
    """Benchmark host-to-device transfer. Returns (median_s, cv)."""
    host_buf = np.ones(size_bytes // 8, dtype=np.float64)  # Align to 8 bytes
    actual_bytes = host_buf.nbytes

    d_ptr = cuda_malloc(ctx, actual_bytes)
    host_ptr = host_buf.ctypes.data_as(ctypes.c_void_p)

    def run() -> None:
        cuda_memcpy_htod(ctx, d_ptr, host_ptr, actual_bytes)
        cuda_synchronize(ctx)

    median, cv = timed_runs(run, warmup=5, runs=10)

    cuda_free(ctx, d_ptr)
    return median, cv


def _bench_d2h(ctx: CUDAContext, size_bytes: int) -> tuple[float, float]:
    """Benchmark device-to-host transfer. Returns (median_s, cv)."""
    host_buf = np.empty(size_bytes // 8, dtype=np.float64)
    actual_bytes = host_buf.nbytes

    d_ptr = cuda_malloc(ctx, actual_bytes)
    # Fill device memory with something (upload first)
    src = np.ones(size_bytes // 8, dtype=np.float64)
    cuda_memcpy_htod(ctx, d_ptr, src.ctypes.data_as(ctypes.c_void_p), actual_bytes)
    cuda_synchronize(ctx)

    host_ptr = host_buf.ctypes.data_as(ctypes.c_void_p)

    def run() -> None:
        cuda_memcpy_dtoh(ctx, host_ptr, d_ptr, actual_bytes)
        cuda_synchronize(ctx)

    median, cv = timed_runs(run, warmup=5, runs=10)

    cuda_free(ctx, d_ptr)
    return median, cv


def run_transfer_benchmarks() -> list[BenchResult]:
    """Run all host<->device transfer benchmarks.

    Returns list of BenchResult (one per size per direction).
    If CUDA is not available, returns an empty list.
    """
    print("\n=== Host <-> Device Transfer Benchmark ===")
    print(f"  Sizes: {', '.join(format_size(s) for s in SIZES_BYTES)}")
    print(f"  Metric: GB/s")

    ctx = cuda_init()
    if ctx is None:
        print("  CUDA not available — skipping transfer benchmarks")
        return []

    print(f"  CUDA device: {ctx.device_name}")
    print(f"  Memory: {ctx.total_mem / (1024**3):.1f} GB")

    results: list[BenchResult] = []

    for size_bytes in SIZES_BYTES:
        label = format_size(size_bytes)

        print(f"\n  [{label}]")

        # Host -> Device
        print(f"    H2D...", end="", flush=True)
        try:
            h2d_time, h2d_cv = _bench_h2d(ctx, size_bytes)
            h2d_gbps = size_bytes / h2d_time / 1e9
            print(f" {h2d_time*1000:.2f}ms ({h2d_gbps:.2f} GB/s, CV={h2d_cv:.1%})")
            results.append(
                BenchResult(
                    name="transfer_h2d",
                    size_label=label,
                    gpu_time_s=h2d_time,
                    gpu_metric=h2d_gbps,
                    metric_unit="GB/s",
                    cv_gpu=h2d_cv,
                    gpu_available=True,
                )
            )
        except RuntimeError as e:
            print(f" FAILED: {e}")

        # Device -> Host
        print(f"    D2H...", end="", flush=True)
        try:
            d2h_time, d2h_cv = _bench_d2h(ctx, size_bytes)
            d2h_gbps = size_bytes / d2h_time / 1e9
            print(f" {d2h_time*1000:.2f}ms ({d2h_gbps:.2f} GB/s, CV={d2h_cv:.1%})")
            results.append(
                BenchResult(
                    name="transfer_d2h",
                    size_label=label,
                    gpu_time_s=d2h_time,
                    gpu_metric=d2h_gbps,
                    metric_unit="GB/s",
                    cv_gpu=d2h_cv,
                    gpu_available=True,
                )
            )
        except RuntimeError as e:
            print(f" FAILED: {e}")

    cuda_shutdown(ctx)
    return results


if __name__ == "__main__":
    results = run_transfer_benchmarks()
    if results:
        print("\n--- Summary ---")
        for r in results:
            print(f"  {r.size_label} {r.name}: {r.gpu_metric:.2f} GB/s")
    else:
        print("\nNo results (CUDA not available).")
