"""Shared benchmark measurement utilities for GPU benchmarks.

Provides timing harness with warmup, multiple runs, median, CV calculation.
Follows the same isolation philosophy as benchmarks/isolate.py but adapted
for synchronous GPU workloads (no asyncio needed).
"""

from __future__ import annotations

import gc
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class BenchResult:
    """Result of a single benchmark scenario."""

    name: str
    size_label: str
    cpu_time_s: float = 0.0
    gpu_time_s: float = 0.0
    cpu_metric: float = 0.0  # GFLOPS, GB/s, etc. depending on benchmark
    gpu_metric: float = 0.0
    metric_unit: str = ""
    speedup: float = 0.0
    cv_cpu: float = 0.0
    cv_gpu: float = 0.0
    gpu_available: bool = False
    extra: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        d = {
            "name": self.name,
            "size_label": self.size_label,
            "cpu_time_s": round(self.cpu_time_s, 6),
            "cpu_metric": round(self.cpu_metric, 2),
            "metric_unit": self.metric_unit,
            "cv_cpu": round(self.cv_cpu, 4),
            "gpu_available": self.gpu_available,
        }
        if self.gpu_available:
            d["gpu_time_s"] = round(self.gpu_time_s, 6)
            d["gpu_metric"] = round(self.gpu_metric, 2)
            d["speedup"] = round(self.speedup, 2)
            d["cv_gpu"] = round(self.cv_gpu, 4)
        if self.extra:
            d["extra"] = {k: round(v, 4) for k, v in self.extra.items()}
        return d


def _iqr_clean(raw: list[float]) -> list[float]:
    """Remove outliers using IQR method."""
    if len(raw) < 4:
        return raw
    q1, _, q3 = statistics.quantiles(raw, n=4)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [t for t in raw if lo <= t <= hi]


def timed_runs(
    fn: Callable[[], None],
    warmup: int = 5,
    runs: int = 10,
) -> tuple[float, float]:
    """Run a function with warmup and return (median_seconds, cv).

    GC is disabled during timed runs. IQR outlier removal applied.
    """
    # Warmup
    for _ in range(warmup):
        fn()

    # Timed runs
    times: list[float] = []
    for _ in range(runs):
        gc.collect()
        gc.disable()
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        gc.enable()
        times.append(t1 - t0)

    cleaned = _iqr_clean(times)
    median = statistics.median(cleaned)
    cv = statistics.stdev(cleaned) / median if len(cleaned) > 1 and median > 0 else 0.0
    return median, cv


def format_size(n_bytes: int) -> str:
    """Format byte count as human-readable string."""
    if n_bytes >= 1024 * 1024 * 1024:
        return f"{n_bytes / (1024**3):.0f}GB"
    if n_bytes >= 1024 * 1024:
        return f"{n_bytes / (1024**2):.0f}MB"
    if n_bytes >= 1024:
        return f"{n_bytes / 1024:.0f}KB"
    return f"{n_bytes}B"


def format_count(n: int) -> str:
    """Format element count as human-readable string (e.g., 1M, 64M)."""
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


def _find_msvc_cl() -> str | None:
    """Find cl.exe from Visual Studio on Windows (nvcc needs it as host compiler)."""
    import glob

    for base in [
        r"C:\Program Files\Microsoft Visual Studio",
        r"C:\Program Files (x86)\Microsoft Visual Studio",
    ]:
        matches = glob.glob(base + r"\*\*\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe")
        if matches:
            matches.sort()
            return os.path.dirname(matches[-1])
    return None


def compile_ptx(cuda_source: str, arch: str = "sm_89") -> str | None:
    """Compile CUDA C source to PTX using nvcc.

    On Windows, automatically locates cl.exe (MSVC) and passes -ccbin to nvcc.
    Returns the PTX source string, or None if compilation fails.
    """
    import os
    import platform
    import shutil
    import subprocess
    import sys
    import tempfile

    nvcc = shutil.which("nvcc")
    if nvcc is None:
        return None

    extra_args: list[str] = []
    if platform.system() == "Windows" and shutil.which("cl") is None:
        cl_dir = _find_msvc_cl()
        if cl_dir:
            extra_args = [f"-ccbin={cl_dir}"]
        else:
            print(
                "  WARNING: cl.exe not found — nvcc requires MSVC on Windows",
                file=sys.stderr,
            )
            return None

    with tempfile.TemporaryDirectory() as tmpdir:
        cu_path = os.path.join(tmpdir, "kernel.cu")
        ptx_path = os.path.join(tmpdir, "kernel.ptx")
        with open(cu_path, "w") as f:
            f.write(cuda_source)
        try:
            cmd = [nvcc, "--ptx", "-o", ptx_path, cu_path, f"-arch={arch}"] + extra_args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  nvcc PTX compilation failed: {result.stderr.strip()}", file=sys.stderr)
                return None
            with open(ptx_path) as f:
                return f.read()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
