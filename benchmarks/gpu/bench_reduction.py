"""GPU Benchmark: Sum Reduction — CPU (numpy) vs CUDA (Driver API).

Measures reduction throughput for summing large 1D tensors.
Uses a two-pass parallel reduction kernel on GPU.

Sizes: 1M, 4M, 16M, 64M elements (float64)
Operation: sum
Metric: GB/s effective bandwidth, speedup vs CPU
Warmup: 5 runs, Timed: 10 runs, Median with IQR outlier removal
"""

from __future__ import annotations

import ctypes

import numpy as np

from benchmarks.gpu._bench_utils import BenchResult, compile_ptx, format_count, timed_runs
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
# CUDA reduction kernel
# ---------------------------------------------------------------------------

REDUCTION_CUDA_SOURCE = """\
extern "C" __global__
void reduce_sum_f64(const double* __restrict__ input,
                    double* __restrict__ output,
                    long long n)
{
    extern __shared__ double sdata[];

    long long tid = threadIdx.x;
    long long idx = (long long)blockIdx.x * blockDim.x * 2 + threadIdx.x;

    // Load and add first reduction step
    double val = 0.0;
    if (idx < n) val += input[idx];
    if (idx + blockDim.x < n) val += input[idx + blockDim.x];
    sdata[tid] = val;
    __syncthreads();

    // Reduction in shared memory
    for (unsigned int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }

    // Write result for this block
    if (tid == 0) {
        output[blockIdx.x] = sdata[0];
    }
}
"""

SIZES = [1_000_000, 4_000_000, 16_000_000, 64_000_000]


# ---------------------------------------------------------------------------
# CPU benchmark
# ---------------------------------------------------------------------------


def _bench_cpu_sum(n: int) -> tuple[float, float]:
    """Benchmark numpy sum. Returns (median_s, cv)."""
    a = np.random.randn(n)

    def run() -> None:
        np.sum(a)

    return timed_runs(run, warmup=5, runs=10)


# ---------------------------------------------------------------------------
# GPU benchmark
# ---------------------------------------------------------------------------


def _bench_gpu_sum(ctx: CUDAContext, ptx: str, n: int) -> tuple[float, float]:
    """Benchmark GPU parallel sum reduction. Returns (median_s, cv).

    Uses a two-pass approach:
      Pass 1: reduce N elements to num_blocks partial sums
      Pass 2: reduce num_blocks partial sums to 1 final sum
    """
    from benchmarks.gpu._cuda_helpers import cuda_get_function, cuda_load_module

    module = cuda_load_module(ctx, ptx)
    func = cuda_get_function(ctx, module, "reduce_sum_f64")

    a = np.random.randn(n).astype(np.float64)
    size_bytes = n * 8

    # Kernel config
    block_size = 256
    # Each block processes 2*block_size elements
    num_blocks = (n + 2 * block_size - 1) // (2 * block_size)
    shared_mem = block_size * 8  # float64

    # Allocate device memory
    d_input = cuda_malloc(ctx, size_bytes)
    d_partial = cuda_malloc(ctx, num_blocks * 8)
    d_output = cuda_malloc(ctx, 8)

    # Upload input
    cuda_memcpy_htod(ctx, d_input, a.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_synchronize(ctx)

    # Prepare params for pass 1
    p_input = ctypes.c_uint64(d_input.value)
    p_partial = ctypes.c_uint64(d_partial.value)
    p_output = ctypes.c_uint64(d_output.value)
    p_n = ctypes.c_longlong(n)
    p_nb = ctypes.c_longlong(num_blocks)

    params_pass1 = [
        ctypes.cast(ctypes.pointer(p_input), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_partial), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_n), ctypes.c_void_p),
    ]

    # Pass 2 config: reduce num_blocks -> 1
    num_blocks_2 = (num_blocks + 2 * block_size - 1) // (2 * block_size)
    if num_blocks_2 < 1:
        num_blocks_2 = 1

    params_pass2 = [
        ctypes.cast(ctypes.pointer(p_partial), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_output), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_nb), ctypes.c_void_p),
    ]

    def run() -> None:
        # Pass 1: N -> num_blocks partial sums
        cuda_launch_kernel(
            ctx,
            func,
            (num_blocks, 1, 1),
            (block_size, 1, 1),
            params_pass1,
            shared_mem=shared_mem,
        )
        # Pass 2: num_blocks -> 1
        cuda_launch_kernel(
            ctx,
            func,
            (num_blocks_2, 1, 1),
            (block_size, 1, 1),
            params_pass2,
            shared_mem=shared_mem,
        )
        cuda_synchronize(ctx)

    median, cv = timed_runs(run, warmup=5, runs=10)

    # Cleanup
    cuda_free(ctx, d_input)
    cuda_free(ctx, d_partial)
    cuda_free(ctx, d_output)
    ctx.lib.cuModuleUnload(module)

    return median, cv


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_reduction_benchmarks() -> list[BenchResult]:
    """Run all reduction benchmarks. Returns list of BenchResult."""
    print("\n=== Sum Reduction Benchmark ===")
    print(f"  Sizes: {', '.join(format_count(n) for n in SIZES)} elements")
    print("  Metric: GB/s, speedup")

    ctx = cuda_init()
    ptx: str | None = None
    if ctx is not None:
        print(f"  CUDA device: {ctx.device_name}")
        ptx = compile_ptx(REDUCTION_CUDA_SOURCE)
        if ptx is None:
            print("  WARNING: PTX compilation failed — GPU tests skipped")
    else:
        print("  CUDA not available — GPU tests skipped")

    gpu_available = ctx is not None and ptx is not None
    results: list[BenchResult] = []

    for n in SIZES:
        label = format_count(n)
        # Reduction reads N elements (8 bytes each)
        total_bytes = n * 8

        print(f"\n  [{label} elements]")

        # CPU
        print("    CPU (numpy)...", end="", flush=True)
        cpu_time, cpu_cv = _bench_cpu_sum(n)
        cpu_gbps = total_bytes / cpu_time / 1e9
        print(f" {cpu_time*1000:.2f}ms ({cpu_gbps:.1f} GB/s, CV={cpu_cv:.1%})")

        result = BenchResult(
            name="reduction_sum",
            size_label=label,
            cpu_time_s=cpu_time,
            cpu_metric=cpu_gbps,
            metric_unit="GB/s",
            cv_cpu=cpu_cv,
            gpu_available=gpu_available,
        )

        # GPU
        if gpu_available:
            assert ctx is not None and ptx is not None
            print("    GPU (CUDA)...", end="", flush=True)
            try:
                gpu_time, gpu_cv = _bench_gpu_sum(ctx, ptx, n)
                gpu_gbps = total_bytes / gpu_time / 1e9
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                print(
                    f" {gpu_time*1000:.2f}ms ({gpu_gbps:.1f} GB/s, "
                    f"speedup={speedup:.1f}x, CV={gpu_cv:.1%})"
                )
                result.gpu_time_s = gpu_time
                result.gpu_metric = gpu_gbps
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
    results = run_reduction_benchmarks()
    print("\n--- Summary ---")
    for r in results:
        line = f"  {r.size_label}: CPU={r.cpu_metric:.1f} GB/s"
        if r.gpu_available:
            line += f", GPU={r.gpu_metric:.1f} GB/s, speedup={r.speedup:.1f}x"
        print(line)
