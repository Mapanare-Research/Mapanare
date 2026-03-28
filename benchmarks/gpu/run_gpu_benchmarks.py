"""GPU Benchmark Suite Runner for Mapanare.

Runs all GPU benchmark modules, aggregates results into a single JSON file,
and generates a GPU_REPORT.md with formatted tables.

Usage:
    python -m benchmarks.gpu.run_gpu_benchmarks
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.gpu._bench_utils import BenchResult
from benchmarks.gpu.bench_elementwise import run_elementwise_benchmarks
from benchmarks.gpu.bench_matmul import run_matmul_benchmarks
from benchmarks.gpu.bench_reduction import run_reduction_benchmarks
from benchmarks.gpu.bench_transfer import run_transfer_benchmarks

# Try to detect GPU info for report header
from experimental.gpu import detect_gpus


def _detect_system_info() -> dict[str, str]:
    """Gather system info for the report header."""
    import platform

    info: dict[str, str] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        import numpy as np

        info["numpy"] = np.__version__
    except ImportError:
        info["numpy"] = "not installed"

    detection = detect_gpus()
    if detection.cuda_available and detection.devices:
        dev = detection.devices[0]
        info["gpu"] = dev.name
        if dev.memory_bytes:
            info["gpu_memory"] = f"{dev.memory_bytes // (1024**2)} MB"
        if dev.driver_version:
            info["driver"] = dev.driver_version
        if dev.compute_capability:
            info["compute_cap"] = f"sm_{dev.compute_capability[0]}{dev.compute_capability[1]}"
    else:
        info["gpu"] = "none detected"

    return info


def _generate_report(
    results: dict[str, list[BenchResult]],
    system_info: dict[str, str],
    duration_s: float,
) -> str:
    """Generate GPU_REPORT.md content."""
    lines: list[str] = []

    lines.append("# Mapanare GPU Benchmark Report")
    lines.append("")
    lines.append("## System Information")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    for key, val in system_info.items():
        lines.append(f"| {key} | {val} |")
    lines.append(f"| total_duration | {duration_s:.1f}s |")
    lines.append("")

    # --- Matrix Multiply ---
    matmul = results.get("matmul", [])
    if matmul:
        lines.append("## Matrix Multiply (GFLOPS)")
        lines.append("")
        has_gpu = any(r.gpu_available for r in matmul)
        if has_gpu:
            lines.append("| Size | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |")
            lines.append("|------|-------------|------------|---------|--------|--------|")
            for r in matmul:
                if r.gpu_available:
                    lines.append(
                        f"| {r.size_label} | {r.cpu_metric:.1f} | {r.gpu_metric:.1f} | "
                        f"{r.speedup:.1f}x | {r.cv_cpu:.1%} | {r.cv_gpu:.1%} |"
                    )
                else:
                    lines.append(
                        f"| {r.size_label} | {r.cpu_metric:.1f} | N/A | - | {r.cv_cpu:.1%} | - |"
                    )
        else:
            lines.append("| Size | CPU (numpy) | CV |")
            lines.append("|------|-------------|----|")
            for r in matmul:
                lines.append(f"| {r.size_label} | {r.cpu_metric:.1f} GFLOPS | {r.cv_cpu:.1%} |")
        lines.append("")

    # --- Element-wise Operations ---
    elemwise = results.get("elementwise", [])
    if elemwise:
        lines.append("## Element-wise Operations (GB/s)")
        lines.append("")
        has_gpu = any(r.gpu_available for r in elemwise)
        if has_gpu:
            lines.append("| Size | Op | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |")
            lines.append("|------|----|-------------|------------|---------|--------|--------|")
            for r in elemwise:
                op = r.name.replace("elementwise_", "")
                if r.gpu_available:
                    lines.append(
                        f"| {r.size_label} | {op} | {r.cpu_metric:.1f} | {r.gpu_metric:.1f} | "
                        f"{r.speedup:.1f}x | {r.cv_cpu:.1%} | {r.cv_gpu:.1%} |"
                    )
                else:
                    lines.append(
                        f"| {r.size_label} | {op} | {r.cpu_metric:.1f} | N/A | "
                        f"- | {r.cv_cpu:.1%} | - |"
                    )
        else:
            lines.append("| Size | Op | CPU (numpy) | CV |")
            lines.append("|------|----|-------------|----|")
            for r in elemwise:
                op = r.name.replace("elementwise_", "")
                lines.append(
                    f"| {r.size_label} | {op} | {r.cpu_metric:.1f} GB/s | {r.cv_cpu:.1%} |"
                )
        lines.append("")

    # --- Transfer Bandwidth ---
    transfer = results.get("transfer", [])
    if transfer:
        lines.append("## Host <-> Device Transfer (GB/s)")
        lines.append("")
        lines.append("| Size | Direction | Bandwidth | CV |")
        lines.append("|------|-----------|-----------|-----|")
        for r in transfer:
            direction = "H2D" if "h2d" in r.name else "D2H"
            lines.append(
                f"| {r.size_label} | {direction} | {r.gpu_metric:.2f} GB/s | {r.cv_gpu:.1%} |"
            )
        lines.append("")

    # --- Reduction ---
    reduction = results.get("reduction", [])
    if reduction:
        lines.append("## Sum Reduction (GB/s)")
        lines.append("")
        has_gpu = any(r.gpu_available for r in reduction)
        if has_gpu:
            lines.append("| Size | CPU (numpy) | GPU (CUDA) | Speedup | CPU CV | GPU CV |")
            lines.append("|------|-------------|------------|---------|--------|--------|")
            for r in reduction:
                if r.gpu_available:
                    lines.append(
                        f"| {r.size_label} | {r.cpu_metric:.1f} | {r.gpu_metric:.1f} | "
                        f"{r.speedup:.1f}x | {r.cv_cpu:.1%} | {r.cv_gpu:.1%} |"
                    )
                else:
                    lines.append(
                        f"| {r.size_label} | {r.cpu_metric:.1f} | N/A | - | {r.cv_cpu:.1%} | - |"
                    )
        else:
            lines.append("| Size | CPU (numpy) | CV |")
            lines.append("|------|-------------|----|")
            for r in reduction:
                lines.append(f"| {r.size_label} | {r.cpu_metric:.1f} GB/s | {r.cv_cpu:.1%} |")
        lines.append("")

    # --- What this measures ---
    lines.append("## What this measures")
    lines.append("")
    lines.append(
        "These benchmarks test **Mapanare's C runtime GPU layer** — the same CUDA Driver API"
    )
    lines.append(
        "calls that `@gpu` and `@cuda` annotated Mapanare functions dispatch to at runtime."
    )
    lines.append(
        "The CPU baseline uses numpy (typically backed by MKL/OpenBLAS), which is a strong"
    )
    lines.append(
        "multi-threaded BLAS implementation. The GPU path uses raw CUDA kernel launches via"
    )
    lines.append("the Mapanare runtime's `dlopen`-based CUDA integration — no cuBLAS, no cuDNN.")
    lines.append("")
    lines.append(
        "When a Mapanare program uses `@gpu` tensor operations, this is the performance it"
    )
    lines.append("gets from the underlying runtime. End-to-end Mapanare compilation adds only the")
    lines.append(
        "overhead of LLVM-compiled dispatch code, which is negligible for tensor-sized workloads."
    )
    lines.append("")

    # --- Methodology ---
    lines.append("## Methodology")
    lines.append("")
    lines.append("- CPU baseline: numpy (MKL/OpenBLAS, multi-threaded)")
    lines.append(
        "- GPU: CUDA Driver API via ctypes — raw kernel launch, "
        "matching `mapanare_gpu.h` runtime path"
    )
    lines.append("- Matmul GFLOPS = 2*N^3 / time (standard matmul flop count)")
    lines.append("- Element-wise GB/s = total bytes read + written / time")
    lines.append("- Transfer GB/s = buffer size / time (includes synchronization)")
    lines.append("- Reduction GB/s = input bytes / time (read-only)")
    lines.append("- All measurements: 5 warmup + 10 timed runs, median with IQR outlier removal")
    lines.append(
        "- CV = coefficient of variation (stdev/mean); "
        "below 5% is stable, above 10% is flagged as noisy"
    )
    lines.append("")

    return "\n".join(lines)


def run_all_gpu_benchmarks() -> dict[str, list[BenchResult]]:
    """Run all GPU benchmark suites. Returns dict of category -> results."""
    results: dict[str, list[BenchResult]] = {}

    print("=" * 60)
    print("  Mapanare GPU Benchmark Suite")
    print("=" * 60)

    # 1. Matrix multiply
    try:
        results["matmul"] = run_matmul_benchmarks()
    except Exception as e:
        print(f"\nERROR in matmul benchmark: {e}", file=sys.stderr)
        results["matmul"] = []

    # 2. Element-wise operations
    try:
        results["elementwise"] = run_elementwise_benchmarks()
    except Exception as e:
        print(f"\nERROR in elementwise benchmark: {e}", file=sys.stderr)
        results["elementwise"] = []

    # 3. Transfer bandwidth
    try:
        results["transfer"] = run_transfer_benchmarks()
    except Exception as e:
        print(f"\nERROR in transfer benchmark: {e}", file=sys.stderr)
        results["transfer"] = []

    # 4. Reduction
    try:
        results["reduction"] = run_reduction_benchmarks()
    except Exception as e:
        print(f"\nERROR in reduction benchmark: {e}", file=sys.stderr)
        results["reduction"] = []

    return results


def main() -> None:
    """Entry point: run all benchmarks, write JSON and markdown report."""
    t_start = time.perf_counter()

    system_info = _detect_system_info()
    results = run_all_gpu_benchmarks()

    t_end = time.perf_counter()
    duration = t_end - t_start

    # Serialize to JSON
    json_data: dict[str, list[dict]] = {}
    for category, bench_results in results.items():
        json_data[category] = [r.to_dict() for r in bench_results]
    json_data["_meta"] = [{"system_info": system_info, "duration_s": round(duration, 1)}]  # type: ignore[assignment]

    benchmarks_dir = Path(__file__).resolve().parent.parent
    json_path = benchmarks_dir / "results_gpu.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"\nJSON results written to {json_path}")

    # Generate markdown report
    report = _generate_report(results, system_info, duration)
    report_path = benchmarks_dir / "GPU_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Markdown report written to {report_path}")

    # Summary
    total_benchmarks = sum(len(v) for v in results.values())
    gpu_benchmarks = sum(1 for v in results.values() for r in v if r.gpu_available)
    print(f"\nDone: {total_benchmarks} benchmarks ({gpu_benchmarks} with GPU) in {duration:.1f}s")

    # Warn about noisy results
    noisy = [
        r
        for v in results.values()
        for r in v
        if r.cv_cpu > 0.05 or (r.gpu_available and r.cv_gpu > 0.05)
    ]
    if noisy:
        print(f"\nWarning: {len(noisy)} noisy results (CV > 5%) — consider re-running")


if __name__ == "__main__":
    main()
