"""GPU Benchmark: Element-wise Operations — CPU (numpy) vs CUDA (Driver API).

Measures throughput of element-wise tensor operations (add, mul, scale)
on 1D tensors of increasing size.

Sizes: 1M, 4M, 16M, 64M elements (float64)
Operations: add (a+b), mul (a*b), scale (a*scalar)
Metric: GB/s effective memory bandwidth
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
# CUDA kernels for element-wise ops
# ---------------------------------------------------------------------------

ELEMENTWISE_CUDA_SOURCE = """\
extern "C" __global__
void tensor_add_f64(const double* __restrict__ a,
                    const double* __restrict__ b,
                    double* __restrict__ c,
                    long long n)
{
    long long idx = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

extern "C" __global__
void tensor_mul_f64(const double* __restrict__ a,
                    const double* __restrict__ b,
                    double* __restrict__ c,
                    long long n)
{
    long long idx = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] * b[idx];
    }
}

extern "C" __global__
void tensor_scale_f64(const double* __restrict__ a,
                      double scalar,
                      double* __restrict__ c,
                      long long n)
{
    long long idx = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] * scalar;
    }
}
"""

SIZES = [1_000_000, 4_000_000, 16_000_000, 64_000_000]
OPS = ["add", "mul", "scale"]


def _bytes_accessed_binary(n: int) -> int:
    """Bytes accessed for a binary op: read 2 inputs + write 1 output."""
    return 3 * n * 8  # 3 tensors, float64


def _bytes_accessed_scale(n: int) -> int:
    """Bytes accessed for scale: read 1 input + write 1 output."""
    return 2 * n * 8


# ---------------------------------------------------------------------------
# CPU benchmarks
# ---------------------------------------------------------------------------


def _bench_cpu_add(n: int) -> tuple[float, float]:
    a = np.random.randn(n)
    b = np.random.randn(n)

    def run() -> None:
        np.add(a, b, out=np.empty(n))

    return timed_runs(run, warmup=5, runs=10)


def _bench_cpu_mul(n: int) -> tuple[float, float]:
    a = np.random.randn(n)
    b = np.random.randn(n)

    def run() -> None:
        np.multiply(a, b, out=np.empty(n))

    return timed_runs(run, warmup=5, runs=10)


def _bench_cpu_scale(n: int) -> tuple[float, float]:
    a = np.random.randn(n)
    scalar = 2.5

    def run() -> None:
        np.multiply(a, scalar, out=np.empty(n))

    return timed_runs(run, warmup=5, runs=10)


# ---------------------------------------------------------------------------
# GPU benchmarks
# ---------------------------------------------------------------------------


def _bench_gpu_binary_op(
    ctx: CUDAContext,
    func_name: str,
    ptx: str,
    n: int,
) -> tuple[float, float]:
    """Benchmark a binary element-wise GPU op (add or mul)."""
    from benchmarks.gpu._cuda_helpers import cuda_get_function, cuda_load_module

    module = cuda_load_module(ctx, ptx)
    func = cuda_get_function(ctx, module, func_name)

    a = np.random.randn(n).astype(np.float64)
    b = np.random.randn(n).astype(np.float64)
    size_bytes = n * 8

    d_a = cuda_malloc(ctx, size_bytes)
    d_b = cuda_malloc(ctx, size_bytes)
    d_c = cuda_malloc(ctx, size_bytes)

    cuda_memcpy_htod(ctx, d_a, a.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_memcpy_htod(ctx, d_b, b.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_synchronize(ctx)

    block = (256, 1, 1)
    grid = ((n + 255) // 256, 1, 1)

    p_a = ctypes.c_uint64(d_a.value)
    p_b = ctypes.c_uint64(d_b.value)
    p_c = ctypes.c_uint64(d_c.value)
    p_n = ctypes.c_longlong(n)

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

    cuda_free(ctx, d_a)
    cuda_free(ctx, d_b)
    cuda_free(ctx, d_c)
    ctx.lib.cuModuleUnload(module)

    return median, cv


def _bench_gpu_scale(
    ctx: CUDAContext,
    ptx: str,
    n: int,
) -> tuple[float, float]:
    """Benchmark GPU scale operation."""
    from benchmarks.gpu._cuda_helpers import cuda_get_function, cuda_load_module

    module = cuda_load_module(ctx, ptx)
    func = cuda_get_function(ctx, module, "tensor_scale_f64")

    a = np.random.randn(n).astype(np.float64)
    size_bytes = n * 8

    d_a = cuda_malloc(ctx, size_bytes)
    d_c = cuda_malloc(ctx, size_bytes)

    cuda_memcpy_htod(ctx, d_a, a.ctypes.data_as(ctypes.c_void_p), size_bytes)
    cuda_synchronize(ctx)

    block = (256, 1, 1)
    grid = ((n + 255) // 256, 1, 1)

    p_a = ctypes.c_uint64(d_a.value)
    p_scalar = ctypes.c_double(2.5)
    p_c = ctypes.c_uint64(d_c.value)
    p_n = ctypes.c_longlong(n)

    params = [
        ctypes.cast(ctypes.pointer(p_a), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_scalar), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_c), ctypes.c_void_p),
        ctypes.cast(ctypes.pointer(p_n), ctypes.c_void_p),
    ]

    def run() -> None:
        cuda_launch_kernel(ctx, func, grid, block, params)
        cuda_synchronize(ctx)

    median, cv = timed_runs(run, warmup=5, runs=10)

    cuda_free(ctx, d_a)
    cuda_free(ctx, d_c)
    ctx.lib.cuModuleUnload(module)

    return median, cv


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_elementwise_benchmarks() -> list[BenchResult]:
    """Run all element-wise benchmarks. Returns list of BenchResult."""
    print("\n=== Element-wise Operations Benchmark ===")
    print(f"  Sizes: {', '.join(format_count(n) for n in SIZES)} elements")
    print(f"  Ops: {', '.join(OPS)}")
    print("  Metric: GB/s effective bandwidth")

    ctx = cuda_init()
    ptx: str | None = None
    if ctx is not None:
        print(f"  CUDA device: {ctx.device_name}")
        ptx = compile_ptx(ELEMENTWISE_CUDA_SOURCE)
        if ptx is None:
            print("  WARNING: PTX compilation failed — GPU tests skipped")
    else:
        print("  CUDA not available — GPU tests skipped")

    gpu_available = ctx is not None and ptx is not None
    results: list[BenchResult] = []

    cpu_fns = {"add": _bench_cpu_add, "mul": _bench_cpu_mul, "scale": _bench_cpu_scale}
    gpu_fns = {
        "add": lambda c, p, n: _bench_gpu_binary_op(c, "tensor_add_f64", p, n),
        "mul": lambda c, p, n: _bench_gpu_binary_op(c, "tensor_mul_f64", p, n),
        "scale": lambda c, p, n: _bench_gpu_scale(c, p, n),
    }
    bytes_fn = {
        "add": _bytes_accessed_binary,
        "mul": _bytes_accessed_binary,
        "scale": _bytes_accessed_scale,
    }

    for n in SIZES:
        size_label = format_count(n)
        for op in OPS:
            name = f"elementwise_{op}"
            total_bytes = bytes_fn[op](n)

            print(f"\n  [{size_label} / {op}]")

            # CPU
            print("    CPU (numpy)...", end="", flush=True)
            cpu_time, cpu_cv = cpu_fns[op](n)
            cpu_gbps = total_bytes / cpu_time / 1e9
            print(f" {cpu_time*1000:.2f}ms ({cpu_gbps:.1f} GB/s, CV={cpu_cv:.1%})")

            result = BenchResult(
                name=name,
                size_label=size_label,
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
                    gpu_time, gpu_cv = gpu_fns[op](ctx, ptx, n)
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
    results = run_elementwise_benchmarks()
    print("\n--- Summary ---")
    for r in results:
        line = f"  {r.size_label}/{r.name}: CPU={r.cpu_metric:.1f} GB/s"
        if r.gpu_available:
            line += f", GPU={r.gpu_metric:.1f} GB/s, speedup={r.speedup:.1f}x"
        print(line)
