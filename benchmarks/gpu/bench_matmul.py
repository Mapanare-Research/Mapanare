"""GPU Benchmark: Matrix Multiply — CPU (numpy) vs CUDA (Driver API).

Tests square matrix multiplication at increasing sizes to measure
compute-bound GPU throughput vs CPU baseline.

Sizes: 256x256, 512x512, 1024x1024, 2048x2048, 4096x4096
Metric: GFLOPS (2*N^3 / time for matmul)
Warmup: 5 runs, Timed: 10 runs, Median with IQR outlier removal
"""

from __future__ import annotations

import ctypes

import numpy as np

from benchmarks.gpu._bench_utils import BenchResult, compile_ptx, timed_runs
from benchmarks.gpu._cuda_helpers import (
    CUDAContext,
    cuda_free,
    cuda_init,
    cuda_launch_kernel,
    cuda_malloc,
    cuda_memcpy_htod,
    cuda_shutdown,
    cuda_synchronize,
)

# ---------------------------------------------------------------------------
# PTX for naive matmul kernel (matches mapanare_gpu.h's built-in kernel)
# ---------------------------------------------------------------------------

# We compile this PTX from the CUDA C source at runtime using nvrtc or
# use a pre-compiled PTX. For the benchmark, we use nvcc --ptx via subprocess
# or fall back to numpy-only if nvcc is unavailable.

MATMUL_CUDA_SOURCE = """\
extern "C" __global__
void matmul_f64(const double* __restrict__ a,
                const double* __restrict__ b,
                double* __restrict__ c,
                int N)
{
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < N && col < N) {
        double sum = 0.0;
        for (int k = 0; k < N; k++) {
            sum += a[row * N + k] * b[k * N + col];
        }
        c[row * N + col] = sum;
    }
}
"""

SIZES = [256, 512, 1024, 2048, 4096]


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------


def _bench_cpu_matmul(n: int) -> tuple[float, float]:
    """Benchmark CPU matmul using numpy. Returns (median_s, cv)."""
    a = np.random.randn(n, n)
    b = np.random.randn(n, n)

    def run() -> None:
        np.dot(a, b)

    return timed_runs(run, warmup=3, runs=10)


def _bench_gpu_matmul(
    ctx: CUDAContext,
    ptx: str,
    n: int,
) -> tuple[float, float]:
    """Benchmark GPU matmul using CUDA Driver API. Returns (median_s, cv)."""
    from benchmarks.gpu._cuda_helpers import cuda_get_function, cuda_load_module

    module = cuda_load_module(ctx, ptx)
    func = cuda_get_function(ctx, module, "matmul_f64")

    # Prepare host data
    a = np.random.randn(n, n).astype(np.float64)
    b = np.random.randn(n, n).astype(np.float64)
    size_bytes = n * n * 8  # float64 = 8 bytes

    # Allocate device memory
    d_a = cuda_malloc(ctx, size_bytes)
    d_b = cuda_malloc(ctx, size_bytes)
    d_c = cuda_malloc(ctx, size_bytes)

    # Upload input data
    cuda_memcpy_htod(ctx, d_a, a.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_memcpy_htod(ctx, d_b, b.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_synchronize(ctx)

    # Kernel launch config
    block = (16, 16, 1)
    grid = ((n + 15) // 16, (n + 15) // 16, 1)

    # Prepare kernel params: pointers to each argument
    p_a = ctypes.c_uint64(d_a.value)
    p_b = ctypes.c_uint64(d_b.value)
    p_c = ctypes.c_uint64(d_c.value)
    p_n = ctypes.c_int(n)

    params = [
        ctypes.cast(ctypes.pointer(p_a), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_b), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_c), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_n), ctypes.c_void_p),
    ]

    def run() -> None:
        cuda_launch_kernel(ctx, func, grid, block, params)
        cuda_synchronize(ctx)

    median, cv = timed_runs(run, warmup=5, runs=10)

    # Cleanup
    cuda_free(ctx, d_a)
    cuda_free(ctx, d_b)
    cuda_free(ctx, d_c)
    ctx.lib.cuModuleUnload(module)

    return median, cv


def run_matmul_benchmarks() -> list[BenchResult]:
    """Run all matmul benchmarks (CPU + GPU if available).

    Returns a list of BenchResult, one per size.
    """
    print("\n=== Matrix Multiply Benchmark ===")
    print(f"  Sizes: {', '.join(f'{n}x{n}' for n in SIZES)}")
    print("  Metric: GFLOPS (2*N^3 / time)")

    # Try to initialize CUDA
    ctx = cuda_init()
    ptx: str | None = None
    if ctx is not None:
        print(f"  CUDA device: {ctx.device_name}")
        print(f"  Compute capability: sm_{ctx.compute_cap[0]}{ctx.compute_cap[1]}")
        print(f"  Memory: {ctx.total_mem / (1024**3):.1f} GB")
        ptx = compile_ptx(MATMUL_CUDA_SOURCE)
        if ptx is None:
            print("  WARNING: nvcc not found or PTX compilation failed — GPU tests skipped")
    else:
        print("  CUDA not available — GPU tests skipped")

    gpu_available = ctx is not None and ptx is not None
    results: list[BenchResult] = []

    for n in SIZES:
        label = f"{n}x{n}"
        flops = 2.0 * n * n * n  # 2*N^3 for matmul

        print(f"\n  [{label}]")

        # CPU benchmark
        print("    CPU (numpy)...", end="", flush=True)
        cpu_time, cpu_cv = _bench_cpu_matmul(n)
        cpu_gflops = flops / cpu_time / 1e9
        print(f" {cpu_time*1000:.1f}ms ({cpu_gflops:.1f} GFLOPS, CV={cpu_cv:.1%})")

        result = BenchResult(
            name="matmul",
            size_label=label,
            cpu_time_s=cpu_time,
            cpu_metric=cpu_gflops,
            metric_unit="GFLOPS",
            cv_cpu=cpu_cv,
            gpu_available=gpu_available,
        )

        # GPU benchmark
        if gpu_available:
            assert ctx is not None and ptx is not None
            print("    GPU (CUDA)...", end="", flush=True)
            try:
                gpu_time, gpu_cv = _bench_gpu_matmul(ctx, ptx, n)
                gpu_gflops = flops / gpu_time / 1e9
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                print(
                    f" {gpu_time*1000:.1f}ms ({gpu_gflops:.1f} GFLOPS, "
                    f"speedup={speedup:.1f}x, CV={gpu_cv:.1%})"
                )
                result.gpu_time_s = gpu_time
                result.gpu_metric = gpu_gflops
                result.cv_gpu = gpu_cv
                result.speedup = speedup
            except RuntimeError as e:
                print(f" FAILED: {e}")
                result.gpu_available = False

        results.append(result)

    if ctx is not None:
        cuda_shutdown(ctx)

    return results


if __name__ == "__main__":
    results = run_matmul_benchmarks()
    print("\n--- Summary ---")
    for r in results:
        line = f"  {r.size_label}: CPU={r.cpu_metric:.1f} GFLOPS"
        if r.gpu_available:
            line += f", GPU={r.gpu_metric:.1f} GFLOPS, speedup={r.speedup:.1f}x"
        print(line)
