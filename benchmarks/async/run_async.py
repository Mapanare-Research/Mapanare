#!/usr/bin/env python3
"""Async benchmark harness — compile .mn at O2, run at varying thread counts, compare.

v4.94.0: measures the work-stealing scheduler built in v4.93.0.

Usage:
    python benchmarks/async/run_async.py
    python benchmarks/async/run_async.py --runs 5
    python benchmarks/async/run_async.py --only 02_fanout
    python benchmarks/async/run_async.py --cross-language
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BENCH_DIR = Path(__file__).resolve().parent
RUNTIME_LIB = ROOT / "runtime" / "native" / "libmapanare_rt.a"

BENCHMARKS = [
    "01_sequential_chain",
    "02_fanout",
    "03_io_bound",
    "04_mixed_cpu_io",
    "05_backpressure",
]

EXPECTED_CHECKSUMS = {
    "01_sequential_chain": "checksum = 5050",
    "02_fanout": "checksum = 171700",
    "03_io_bound": "checksum = 1000",
    "04_mixed_cpu_io": "checksum = 12000",
    "05_backpressure": "checksum = 2500",
}

DEFAULT_RUNS = 5


def _find_tool(name: str) -> str | None:
    for c in [name, f"{name}-18", f"{name}-17"]:
        p = shutil.which(c)
        if p:
            return p
    return None


def _run_timed(
    cmd: list[str], timeout: int = 120, env: dict | None = None
) -> tuple[float, str, int]:
    """Run a command, return (wall_seconds, stdout, returncode)."""
    start = time.monotonic()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        elapsed = time.monotonic() - start
        return elapsed, r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return timeout, "", -1


def compile_mn(mn_path: Path, out_dir: Path) -> Path | None:
    """Compile .mn -> native binary at O2."""
    name = mn_path.stem
    ll = out_dir / f"{name}.ll"
    bc = out_dir / f"{name}.bc"
    opt_bc = out_dir / f"{name}.opt.bc"
    obj = out_dir / f"{name}.o"
    binary = out_dir / name

    tools = {t: _find_tool(t) for t in ["llvm-as", "opt", "llc", "clang"]}
    if not all(tools.values()):
        print(f"  SKIP: missing tools {[k for k, v in tools.items() if not v]}")
        return None

    # emit-llvm
    r = subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(mn_path), "-o", str(ll)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        print(f"  FAIL emit: {r.stderr[:200]}")
        return None

    # llvm-as
    r = subprocess.run([tools["llvm-as"], str(ll), "-o", str(bc)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAIL llvm-as: {r.stderr[:200]}")
        return None

    # opt -O2
    r = subprocess.run(
        [tools["opt"], "-O2", str(bc), "-o", str(opt_bc)], capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"  FAIL opt: {r.stderr[:200]}")
        return None

    # llc
    r = subprocess.run(
        [tools["llc"], "-filetype=obj", "-relocation-model=pic", str(opt_bc), "-o", str(obj)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"  FAIL llc: {r.stderr[:200]}")
        return None

    # link
    r = subprocess.run(
        [tools["clang"], str(obj), str(RUNTIME_LIB), "-lm", "-lpthread", "-ldl", "-o", str(binary)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"  FAIL link: {r.stderr[:200]}")
        return None

    return binary


def bench_mapanare(name: str, num_runs: int) -> list[dict]:
    """Benchmark one .mn program (compile at O2, run num_runs times)."""
    mn_path = BENCH_DIR / f"{name}.mn"
    if not mn_path.exists():
        print(f"  SKIP: {mn_path} not found")
        return []

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        binary = compile_mn(mn_path, td)
        if binary is None:
            results.append(
                {
                    "benchmark": name,
                    "language": "mapanare",
                    "status": "compile_fail",
                    "median_ms": -1,
                }
            )
            return results

        # Warmup
        _run_timed([str(binary)], timeout=60)

        # Timed runs
        times = []
        output = ""
        correct = True
        for _ in range(num_runs):
            elapsed, stdout, rc = _run_timed([str(binary)], timeout=60)
            if rc != 0:
                correct = False
            times.append(elapsed * 1000)
            output = stdout

        # Check correctness
        expected = EXPECTED_CHECKSUMS.get(name, "")
        if expected and expected not in output:
            correct = False

        if len(times) >= 5:
            times.sort()
            times = times[1:-1]

        median_ms = statistics.median(times) if times else -1
        min_ms = min(times) if times else -1
        max_ms = max(times) if times else -1

        results.append(
            {
                "benchmark": name,
                "language": "mapanare",
                "median_ms": round(median_ms, 2),
                "min_ms": round(min_ms, 2),
                "max_ms": round(max_ms, 2),
                "runs": num_runs,
                "output": output,
                "correct": correct,
                "status": "ok" if correct else "wrong_checksum",
            }
        )
        status = "OK" if correct else "FAIL"
        print(f"  {name} Mapanare: {median_ms:.1f}ms ({status})")

    return results


def bench_python(name: str, num_runs: int) -> list[dict]:
    """Benchmark Python asyncio equivalent."""
    py_path = BENCH_DIR / f"{name}.py"
    if not py_path.exists():
        return []

    times = []
    output = ""
    for _ in range(num_runs):
        elapsed, stdout, rc = _run_timed(["python3", str(py_path)], timeout=120)
        times.append(elapsed * 1000)
        output = stdout

    if len(times) >= 5:
        times.sort()
        times = times[1:-1]

    median = statistics.median(times) if times else -1
    print(f"  {name} Python: {median:.1f}ms")
    return [
        {
            "benchmark": name,
            "language": "python",
            "median_ms": round(median, 2),
            "output": output,
        }
    ]


def bench_go(name: str, num_runs: int) -> list[dict]:
    """Benchmark Go goroutine equivalent."""
    go_path = BENCH_DIR / f"{name}.go"
    if not go_path.exists() or not shutil.which("go"):
        if go_path.exists():
            return [
                {"benchmark": name, "language": "go", "median_ms": -1, "note": "go not installed"}
            ]
        return []

    with tempfile.TemporaryDirectory() as td:
        binary = Path(td) / name
        r = subprocess.run(
            ["go", "build", "-o", str(binary), str(go_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode != 0:
            return [
                {
                    "benchmark": name,
                    "language": "go",
                    "median_ms": -1,
                    "note": f"build fail: {r.stderr[:100]}",
                }
            ]

        times = []
        output = ""
        for _ in range(num_runs):
            elapsed, stdout, rc = _run_timed([str(binary)], timeout=60)
            times.append(elapsed * 1000)
            output = stdout

        if len(times) >= 5:
            times.sort()
            times = times[1:-1]

        median = statistics.median(times) if times else -1
        print(f"  {name} Go: {median:.1f}ms")
        return [
            {"benchmark": name, "language": "go", "median_ms": round(median, 2), "output": output}
        ]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Async benchmark harness")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--only", type=str, default=None)
    parser.add_argument("--cross-language", action="store_true")
    parser.add_argument("--output", type=str, default=str(BENCH_DIR / "v4.94.0-baseline.json"))
    args = parser.parse_args()

    benchmarks = [args.only] if args.only else BENCHMARKS

    print(f"=== Mapanare Async Benchmark Suite ({args.runs} runs per benchmark) ===\n")

    all_results: dict = {"mapanare": [], "cross_language": []}

    for name in benchmarks:
        print(f"[{name}]")
        results = bench_mapanare(name, args.runs)
        all_results["mapanare"].extend(results)

    if args.cross_language:
        print(f"\n=== Cross-Language Comparison ===\n")
        for name in benchmarks:
            print(f"[{name}]")
            all_results["cross_language"].extend(bench_python(name, args.runs))
            all_results["cross_language"].extend(bench_go(name, args.runs))

    out_path = Path(args.output)
    out_path.write_text(json.dumps(all_results, indent=2) + "\n")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
