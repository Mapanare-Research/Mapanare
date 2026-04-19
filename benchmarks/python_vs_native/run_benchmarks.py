#!/usr/bin/env python3
"""Benchmark harness: Python 3 vs Mapanare-compiled native binaries.

For each script, runs it under Python and as a compiled native binary,
measures wall-clock time (median of N runs), verifies output matches,
and reports the speedup factor.

Usage:
    python3 benchmarks/python_vs_native/run_benchmarks.py
    python3 benchmarks/python_vs_native/run_benchmarks.py --runs 5
"""

from __future__ import annotations

import argparse
import os
import statistics
import subprocess
import sys
import tempfile
import time

SCRIPTS = [
    # (display name, path relative to repo root)
    ("numerical_compute", "examples/python_to_native/numerical_compute.py"),
    ("collatz_explorer", "examples/python_to_native/collatz_explorer.py"),
    ("prime_sieve", "examples/python_to_native/prime_sieve.py"),
    ("fibonacci(40)", "examples/transpile/fibonacci_bench.py"),
    ("primes(500K)", "examples/transpile/primes.py"),
]


def run_python(script: str, timeout: int = 600) -> tuple[float, str]:
    """Run a script with python3 and return (elapsed_seconds, stdout)."""
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.perf_counter() - t0
    if result.returncode != 0:
        raise RuntimeError(f"Python failed on {script}: {result.stderr[:200]}")
    return elapsed, result.stdout.strip()


def build_native(script: str, out_path: str) -> None:
    """Compile a .py script to a native binary via mapanare build."""
    result = subprocess.run(
        [sys.executable, "-m", "mapanare", "build", script, "-o", out_path],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Build failed for {script}: {result.stderr[:300]}")


def run_native(binary: str, timeout: int = 600) -> tuple[float, str]:
    """Run a native binary and return (elapsed_seconds, stdout)."""
    t0 = time.perf_counter()
    result = subprocess.run(
        [binary],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.perf_counter() - t0
    if result.returncode != 0:
        raise RuntimeError(f"Binary failed: {result.stderr[:200]}")
    return elapsed, result.stdout.strip()


def fmt_ms(seconds: float) -> str:
    """Format seconds as milliseconds with comma separators."""
    ms = seconds * 1000
    if ms >= 1000:
        return f"{ms:,.0f} ms"
    return f"{ms:.1f} ms"


def main() -> None:
    parser = argparse.ArgumentParser(description="Python vs Mapanare benchmark")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs per script")
    args = parser.parse_args()
    n_runs = args.runs

    # Find repo root (this script is at benchmarks/python_vs_native/)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(repo_root)

    print(f"Python vs Mapanare-Compiled (median of {n_runs} runs)")
    print()
    header = (
        f"  {'Script':<22} {'Python':>12} {'Mapanare':>12} {'Speedup':>10} {'Output Match':>14}"
    )
    print(header)
    sep = f"  {'─' * 22} {'─' * 12} {'─' * 12} {'─' * 10} {'─' * 14}"
    print(sep)

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for name, script in SCRIPTS:
            if not os.path.isfile(script):
                print(f"  {name:<22} {'SKIP':>12} (file not found)")
                continue

            # Build native binary
            binary = os.path.join(tmpdir, name)
            try:
                build_native(script, binary)
            except RuntimeError as e:
                print(f"  {name:<22} {'BUILD FAIL':>12} {str(e)[:60]}")
                continue

            # Benchmark Python
            py_times = []
            py_output = ""
            for r in range(n_runs):
                try:
                    t, out = run_python(script)
                    py_times.append(t)
                    if r == 0:
                        py_output = out
                except Exception as e:
                    print(f"  {name:<22} Python run {r} failed: {e}")
                    break

            if not py_times:
                continue

            # Benchmark Mapanare
            mn_times = []
            mn_output = ""
            for r in range(n_runs):
                try:
                    t, out = run_native(binary)
                    mn_times.append(t)
                    if r == 0:
                        mn_output = out
                except Exception as e:
                    print(f"  {name:<22} Mapanare run {r} failed: {e}")
                    break

            if not mn_times:
                continue

            py_median = statistics.median(py_times)
            mn_median = statistics.median(mn_times)
            speedup = py_median / mn_median if mn_median > 0 else float("inf")
            match = py_output == mn_output

            match_str = "yes" if match else "MISMATCH"
            print(
                f"  {name:<22} {fmt_ms(py_median):>12} {fmt_ms(mn_median):>12}"
                f" {speedup:>9.0f}x {match_str:>14}"
            )

            results.append(
                {
                    "name": name,
                    "python_ms": py_median * 1000,
                    "mapanare_ms": mn_median * 1000,
                    "speedup": speedup,
                    "match": match,
                }
            )

    print()

    # Write RESULTS.md
    results_path = os.path.join("benchmarks", "python_vs_native", "RESULTS.md")
    with open(results_path, "w") as f:
        f.write("# Python vs Mapanare-Compiled — Benchmark Results\n\n")
        f.write(f"Median of {n_runs} runs per script.\n\n")
        f.write("| Script | Python 3 | Mapanare (native) | Speedup | Output Match |\n")
        f.write("|--------|----------|-------------------|---------|-------------|\n")
        for r in results:
            match_str = "yes" if r["match"] else "MISMATCH"
            f.write(
                f"| {r['name']} | {r['python_ms']:.0f} ms "
                f"| {r['mapanare_ms']:.1f} ms "
                f"| {r['speedup']:.0f}x "
                f"| {match_str} |\n"
            )
        f.write("\n")
    print(f"Results written to {results_path}")


if __name__ == "__main__":
    main()
