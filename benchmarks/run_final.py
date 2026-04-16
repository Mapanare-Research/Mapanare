#!/usr/bin/env python3
"""v4.98.0 Final Benchmark Suite — 10 Mapanare programs + cross-language comparison.

Usage:
    python benchmarks/run_final.py
    python benchmarks/run_final.py --runs 5
    python benchmarks/run_final.py --cross-language
    python benchmarks/run_final.py --only fib_recursive
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

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_LIB = ROOT / "runtime" / "native" / "libmapanare_rt.a"
RESULTS_FILE = ROOT / "benchmarks" / "v4.98.0-final.json"

BENCHMARKS = {
    "optimizer": [
        ("fib_recursive", ROOT / "benchmarks" / "optimizer" / "fib_recursive.mn"),
        ("quicksort", ROOT / "benchmarks" / "optimizer" / "quicksort.mn"),
        ("matmul_naive", ROOT / "benchmarks" / "optimizer" / "matmul_naive.mn"),
        ("string_concat", ROOT / "benchmarks" / "optimizer" / "string_concat.mn"),
        ("agent_fanout", ROOT / "benchmarks" / "optimizer" / "agent_fanout.mn"),
    ],
    "system": [
        ("struct_alloc", ROOT / "benchmarks" / "system" / "struct_alloc.mn"),
        ("enum_match", ROOT / "benchmarks" / "system" / "enum_match.mn"),
        ("closure_capture", ROOT / "benchmarks" / "system" / "closure_capture.mn"),
        ("prime_sieve", ROOT / "benchmarks" / "system" / "list_ops.mn"),
        ("compile_self", ROOT / "benchmarks" / "system" / "compile_self.mn"),
    ],
}

# Expected outputs for correctness verification
EXPECTED = {
    "fib_recursive": "fib(35) = 9227465",
    "quicksort": "checksum = ",  # prefix match
    "matmul_naive": "checksum = ",
    "string_concat": "",  # any output
    "agent_fanout": "",
    "struct_alloc": "checksum = 29999700000",
    "enum_match": "checksum = 52818168",
    "closure_capture": "checksum = 349965000",
    "prime_sieve": "primes = 9592",
    "compile_self": "checksum = 3067267",
}

# Cross-language equivalents
CROSS_LANG = {
    "fib_recursive": {
        "python": ROOT / "benchmarks" / "optimizer" / "fib_recursive.py",
        "rust": ROOT / "benchmarks" / "optimizer" / "fib_recursive.rs",
    },
    "quicksort": {
        "python": ROOT / "benchmarks" / "optimizer" / "quicksort.py",
        "rust": ROOT / "benchmarks" / "optimizer" / "quicksort.rs",
    },
    "matmul_naive": {
        "python": ROOT / "benchmarks" / "optimizer" / "matmul_naive.py",
        "rust": ROOT / "benchmarks" / "optimizer" / "matmul_naive.rs",
    },
    "string_concat": {
        "python": ROOT / "benchmarks" / "optimizer" / "string_concat.py",
        "rust": ROOT / "benchmarks" / "optimizer" / "string_concat.rs",
    },
    "struct_alloc": {
        "python": ROOT / "benchmarks" / "system" / "struct_alloc.py",
        "rust": ROOT / "benchmarks" / "system" / "struct_alloc.rs",
    },
    "enum_match": {
        "python": ROOT / "benchmarks" / "system" / "enum_match.py",
        "rust": ROOT / "benchmarks" / "system" / "enum_match.rs",
    },
    "closure_capture": {
        "python": ROOT / "benchmarks" / "system" / "closure_capture.py",
        "rust": ROOT / "benchmarks" / "system" / "closure_capture.rs",
    },
    "prime_sieve": {
        "python": ROOT / "benchmarks" / "system" / "list_ops.py",
        "rust": ROOT / "benchmarks" / "system" / "list_ops.rs",
    },
    "compile_self": {
        "python": ROOT / "benchmarks" / "system" / "compile_self.py",
        "rust": ROOT / "benchmarks" / "system" / "compile_self.rs",
    },
}


def find_tool(name: str) -> str | None:
    for c in [name, f"{name}-18", f"{name}-17"]:
        p = shutil.which(c)
        if p:
            return p
    return None


def run_timed(cmd: list[str], timeout: int = 120) -> tuple[float, str, int]:
    start = time.monotonic()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
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

    tools = {t: find_tool(t) for t in ["llvm-as", "opt", "llc", "clang"]}
    if not all(tools.values()):
        print(f"  SKIP: missing tools {[k for k, v in tools.items() if not v]}")
        return None

    steps = [
        (["python3", "-m", "mapanare", "emit-llvm", str(mn_path), "-o", str(ll)], "emit"),
        ([tools["llvm-as"], str(ll), "-o", str(bc)], "llvm-as"),
        ([tools["opt"], "-O2", str(bc), "-o", str(opt_bc)], "opt"),
        (
            [tools["llc"], "-filetype=obj", "-relocation-model=pic", str(opt_bc), "-o", str(obj)],
            "llc",
        ),
        (
            [
                tools["clang"],
                str(obj),
                str(RUNTIME_LIB),
                "-lm",
                "-lpthread",
                "-ldl",
                "-o",
                str(binary),
            ],
            "link",
        ),
    ]
    for cmd, stage in steps:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  FAIL {stage}: {r.stderr[:120]}")
            return None
    return binary


def compile_rust(rs_path: Path, out_dir: Path) -> Path | None:
    binary = out_dir / rs_path.stem
    rustc = find_tool("rustc")
    if not rustc:
        return None
    r = subprocess.run(
        [rustc, "-O", str(rs_path), "-o", str(binary)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        print(f"  FAIL rustc: {r.stderr[:120]}")
        return None
    return binary


def bench_runs(cmd: list[str], num_runs: int) -> tuple[float, str, bool]:
    """Run a binary num_runs times, return (median_ms, output, ran_ok)."""
    # Warmup
    run_timed(cmd, timeout=60)

    times = []
    output = ""
    for _ in range(num_runs):
        elapsed, stdout, rc = run_timed(cmd, timeout=60)
        if rc != 0:
            return -1.0, stdout, False
        times.append(elapsed * 1000)
        output = stdout

    if len(times) >= 5:
        times.sort()
        times = times[1:-1]

    return round(statistics.median(times), 2), output, True


def check_correct(name: str, output: str) -> bool:
    expected = EXPECTED.get(name, "")
    if not expected:
        return bool(output)
    return output.startswith(expected) or expected in output


def get_binary_size(binary: Path) -> int:
    return binary.stat().st_size if binary.exists() else 0


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--only", type=str, default=None)
    parser.add_argument("--cross-language", action="store_true")
    args = parser.parse_args()

    print(f"=== Mapanare v4.98.0 Final Benchmark ({args.runs} runs, O2) ===\n")

    all_results: list[dict] = []

    for category, benches in BENCHMARKS.items():
        print(f"[{category}]")
        for name, mn_path in benches:
            if args.only and args.only != name:
                continue
            if not mn_path.exists():
                print(f"  {name}: SKIP (file not found)")
                continue

            with tempfile.TemporaryDirectory() as tmpdir:
                td = Path(tmpdir)
                binary = compile_mn(mn_path, td)
                if binary is None:
                    all_results.append(
                        {
                            "benchmark": name,
                            "category": category,
                            "status": "compile_fail",
                            "median_ms": -1,
                        }
                    )
                    continue

                median_ms, output, ok = bench_runs([str(binary)], args.runs)
                correct = check_correct(name, output)
                bin_size = get_binary_size(binary)
                src_lines = sum(1 for _ in mn_path.open())

                status = "ok" if ok and correct else "fail"
                print(f"  {name}: {median_ms:.1f}ms ({status}) [{output[:60]}]")

                all_results.append(
                    {
                        "benchmark": name,
                        "category": category,
                        "median_ms": median_ms,
                        "output": output,
                        "correct": correct,
                        "status": status,
                        "binary_size_bytes": bin_size,
                        "source_lines": src_lines,
                    }
                )
        print()

    # Cross-language
    cross_results: list[dict] = []
    if args.cross_language:
        print("[cross-language]")
        for name, langs in CROSS_LANG.items():
            if args.only and args.only != name:
                continue

            # Python
            py_path = langs.get("python")
            if py_path and py_path.exists():
                median_ms, output, ok = bench_runs(["python3", str(py_path)], args.runs)
                print(f"  {name} (python): {median_ms:.1f}ms")
                cross_results.append(
                    {
                        "benchmark": name,
                        "language": "python",
                        "median_ms": median_ms,
                        "output": output,
                    }
                )

            # Rust
            rs_path = langs.get("rust")
            if rs_path and rs_path.exists():
                with tempfile.TemporaryDirectory() as tmpdir:
                    td = Path(tmpdir)
                    binary = compile_rust(rs_path, td)
                    if binary:
                        median_ms, output, ok = bench_runs([str(binary)], args.runs)
                        print(f"  {name} (rust): {median_ms:.1f}ms")
                        cross_results.append(
                            {
                                "benchmark": name,
                                "language": "rust",
                                "median_ms": median_ms,
                                "output": output,
                            }
                        )
        print()

    # Save results
    data = {
        "version": "4.98.0",
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "os": "WSL2 (Ubuntu on Windows)",
            "cpu": "AMD Ryzen 9 7950X",
            "ram_gb": 62,
            "llvm_version": "18.1.3",
            "python_version": sys.version.split()[0],
            "runs_per_benchmark": args.runs,
            "opt_level": "O2",
        },
        "mapanare": all_results,
        "cross_language": cross_results,
    }

    RESULTS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
