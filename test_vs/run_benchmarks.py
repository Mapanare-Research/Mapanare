"""Mapanare vs Python vs Go vs Rust -- Benchmark Runner.

Measures: wall time, peak memory (RSS), CPU time.
Runs each benchmark multiple times for stability.
Process isolation per run.

Usage:
    python -m test_vs.run_benchmarks          # run all
    python -m test_vs.run_benchmarks --only 01 # run only fibonacci
    python -m test_vs.run_benchmarks --runs 5  # 5 iterations per benchmark
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VS_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(_ROOT))


@dataclass
class SingleRun:
    wall_time_s: float
    cpu_time_s: float
    peak_memory_kb: float
    output: str = ""


@dataclass
class BenchResult:
    benchmark: str
    language: str
    lines_of_code: int
    runs: list[SingleRun] = field(default_factory=list)
    wall_median: float = 0.0
    wall_min: float = 0.0
    cpu_median: float = 0.0
    mem_peak_kb: float = 0.0
    error: str = ""

    def aggregate(self) -> None:
        valid = [r for r in self.runs if r.wall_time_s >= 0]
        if not valid:
            return
        self.wall_median = statistics.median(r.wall_time_s for r in valid)
        self.wall_min = min(r.wall_time_s for r in valid)
        self.cpu_median = statistics.median(r.cpu_time_s for r in valid)
        self.mem_peak_kb = max(r.peak_memory_kb for r in valid)


@dataclass
class BenchComparison:
    benchmark: str
    results: list[BenchResult] = field(default_factory=list)


def _count_lines(path: Path) -> int:
    """Count non-empty, non-comment lines, excluding benchmark instrumentation."""
    count = 0
    skip_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        # Skip Rust tracking allocator boilerplate
        if "struct TrackingAlloc" in stripped or "static ALLOCATED" in stripped:
            skip_block = True
            continue
        if skip_block:
            if stripped.startswith("#[global_allocator]") or stripped.startswith("static A:"):
                continue
            if stripped == "}" and not any(
                kw in stripped for kw in ["fn main", "fn fib", "fn mat"]
            ):
                skip_block = False
                continue
            continue
        # Skip Go/Rust memory stats boilerplate
        if any(
            kw in stripped
            for kw in [
                "runtime.ReadMemStats",
                "runtime.MemStats",
                "runtime.GC",
                "memBefore",
                "memAfter",
                "__BENCH_METRICS__",
                "wall_time_s=",
                "peak_memory_kb=",
                "cpu_time_s=",
                "PEAK.store",
                "PEAK.load",
                "ALLOCATED.store",
            ]
        ):
            continue
        # Skip benchmark metric print lines
        if "Println" in stripped and "METRICS" in stripped:
            continue
        if "Printf" in stripped and ("wall_time_s" in stripped or "peak_memory_kb" in stripped):
            continue
        if "println!" in stripped and (
            "METRICS" in stripped or "wall_time_s" in stripped or "peak_memory_kb" in stripped
        ):
            continue
        if stripped and not stripped.startswith("//") and not stripped.startswith("#"):
            count += 1
    return count


def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def _parse_metrics(output: str) -> dict[str, float]:
    """Parse __BENCH_METRICS__ block from process output."""
    metrics: dict[str, float] = {}
    capture = False
    for line in output.splitlines():
        if line.strip() == "__BENCH_METRICS__":
            capture = True
            continue
        if capture and "=" in line:
            key, val = line.strip().split("=", 1)
            try:
                metrics[key] = float(val)
            except ValueError:
                pass
    return metrics


def _make_measured_script(bench_code: str) -> str:
    """Wrap benchmark code with measurement instrumentation."""
    return (
        "import time, tracemalloc, sys\n"
        "tracemalloc.start()\n"
        "_cpu0 = time.process_time()\n"
        "_wall0 = time.perf_counter()\n"
        "\n" + bench_code + "\n\n"
        "_wall1 = time.perf_counter() - _wall0\n"
        "_cpu1 = time.process_time() - _cpu0\n"
        "_mem = tracemalloc.get_traced_memory()[1]\n"
        "tracemalloc.stop()\n"
        "print('__BENCH_METRICS__')\n"
        "print('wall_time_s=' + str(round(_wall1, 6)))\n"
        "print('cpu_time_s=' + str(round(_cpu1, 6)))\n"
        "print('peak_memory_kb=' + str(round(_mem / 1024, 1)))\n"
    )


def _run_script(script: str, cwd: str = str(_ROOT)) -> SingleRun:
    """Write script to temp file, execute in isolated process, parse metrics."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8", dir=cwd
    ) as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd,
        )
        if result.returncode != 0:
            return SingleRun(
                wall_time_s=-1,
                cpu_time_s=-1,
                peak_memory_kb=0,
                output=f"ERROR: {result.stderr[:500]}",
            )
        metrics = _parse_metrics(result.stdout)
        clean = "\n".join(
            l
            for l in result.stdout.splitlines()
            if l.strip() != "__BENCH_METRICS__" and "=" not in l
        ).strip()
        return SingleRun(
            wall_time_s=metrics.get("wall_time_s", -1),
            cpu_time_s=metrics.get("cpu_time_s", -1),
            peak_memory_kb=metrics.get("peak_memory_kb", 0),
            output=clean,
        )
    except subprocess.TimeoutExpired:
        return SingleRun(wall_time_s=-1, cpu_time_s=-1, peak_memory_kb=0, output="TIMEOUT")
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Language runners
# ---------------------------------------------------------------------------


def run_mapanare(mn_file: Path, n_runs: int) -> BenchResult:
    """Compile .mn to Python, wrap with measurement, run isolated."""
    from mapanare.cli import _compile_source

    source = mn_file.read_text(encoding="utf-8")
    compiled = _compile_source(source, str(mn_file))

    # The compiled code has:
    #   async def main(): ...
    #   if __name__ == "__main__":
    #       import asyncio
    #       asyncio.run(main())
    #
    # We replace the bottom block to inject measurement around asyncio.run
    measured = compiled.replace(
        'if __name__ == "__main__":\n    import asyncio\n\n    asyncio.run(main())',
        (
            'if __name__ == "__main__":\n'
            "    import asyncio, time, tracemalloc\n"
            "    tracemalloc.start()\n"
            "    _cpu0 = time.process_time()\n"
            "    _wall0 = time.perf_counter()\n"
            "    asyncio.run(main())\n"
            "    _wall1 = time.perf_counter() - _wall0\n"
            "    _cpu1 = time.process_time() - _cpu0\n"
            "    _mem = tracemalloc.get_traced_memory()[1]\n"
            "    tracemalloc.stop()\n"
            '    print("__BENCH_METRICS__")\n'
            '    print("wall_time_s=" + str(round(_wall1, 6)))\n'
            '    print("cpu_time_s=" + str(round(_cpu1, 6)))\n'
            '    print("peak_memory_kb=" + str(round(_mem / 1024, 1)))\n'
        ),
    )

    result = BenchResult(
        benchmark=mn_file.stem,
        language="Mapanare",
        lines_of_code=_count_lines(mn_file),
    )
    for _ in range(n_runs):
        run = _run_script(measured)
        result.runs.append(run)
    result.aggregate()
    return result


def run_mapanare_native(mn_file: Path, n_runs: int) -> BenchResult:
    """Compile .mn to LLVM IR, JIT-compile via MCJIT, run natively."""
    result = BenchResult(
        benchmark=mn_file.stem,
        language="Mapanare (native)",
        lines_of_code=_count_lines(mn_file),
    )

    # Use subprocess to call mapa jit --bench for process isolation
    for _ in range(n_runs):
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.path.insert(0, r'{_ROOT}'); "
                    f"from mapanare.cli import _compile_to_llvm_ir; "
                    f"from mapanare.jit import jit_compile_and_run; "
                    f"import time; "
                    f"source = open(r'{mn_file}', encoding='utf-8').read(); "
                    f"ir_code = _compile_to_llvm_ir(source, '{mn_file.name}'); "
                    f"t0 = time.perf_counter(); c0 = time.process_time(); "
                    f"jit_compile_and_run(ir_code); "
                    f"w = time.perf_counter() - t0; c = time.process_time() - c0; "
                    f"print('__BENCH_METRICS__'); "
                    f"print('wall_time_s=' + str(round(w, 6))); "
                    f"print('cpu_time_s=' + str(round(c, 6))); "
                    f"print('peak_memory_kb=0')",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            run = _parse_native_run(proc.stdout)
            result.runs.append(run)
        except subprocess.TimeoutExpired:
            result.runs.append(
                SingleRun(wall_time_s=-1, cpu_time_s=-1, peak_memory_kb=0, output="TIMEOUT")
            )
        except Exception as e:
            result.runs.append(
                SingleRun(wall_time_s=-1, cpu_time_s=-1, peak_memory_kb=0, output=str(e))
            )

    result.aggregate()
    return result


def run_python(py_file: Path, n_runs: int) -> BenchResult:
    """Extract benchmark code from Python file, wrap with measurement."""
    source = py_file.read_text(encoding="utf-8")

    # Extract: functions + main block body (dedented)
    lines = source.splitlines()
    func_lines: list[str] = []
    main_lines: list[str] = []
    in_main = False
    for line in lines:
        # Skip time import and timing code
        if line.strip().startswith("import time"):
            continue
        if line.strip().startswith("if __name__"):
            in_main = True
            continue
        if in_main:
            if line.startswith("    "):
                stripped = line[4:]
                # Skip timing-related lines
                if any(kw in stripped for kw in ["perf_counter", "elapsed", 'print(f"Time:']):
                    continue
                main_lines.append(stripped)
            elif line.strip() == "":
                main_lines.append("")
            else:
                in_main = False
                func_lines.append(line)
        else:
            func_lines.append(line)

    bench_code = "\n".join(func_lines) + "\n" + "\n".join(main_lines)
    script = _make_measured_script(bench_code)

    result = BenchResult(
        benchmark=py_file.stem,
        language="Python",
        lines_of_code=_count_lines(py_file),
    )
    for _ in range(n_runs):
        run = _run_script(script)
        result.runs.append(run)
    result.aggregate()
    return result


def _parse_native_run(output: str) -> SingleRun:
    """Parse __BENCH_METRICS__ from Go/Rust output."""
    metrics = _parse_metrics(output)
    clean = "\n".join(
        l
        for l in output.splitlines()
        if l.strip() != "__BENCH_METRICS__"
        and not l.strip().startswith("wall_time_s=")
        and not l.strip().startswith("cpu_time_s=")
        and not l.strip().startswith("peak_memory_kb=")
    ).strip()
    wall = metrics.get("wall_time_s", -1)
    return SingleRun(
        wall_time_s=wall,
        cpu_time_s=metrics.get("cpu_time_s", wall),  # fallback to wall
        peak_memory_kb=metrics.get("peak_memory_kb", 0),
        output=clean,
    )


def run_go(go_file: Path, n_runs: int) -> BenchResult | None:
    if not _has_tool("go"):
        return None
    result = BenchResult(
        benchmark=go_file.stem,
        language="Go",
        lines_of_code=_count_lines(go_file),
    )
    for _ in range(n_runs):
        try:
            proc = subprocess.run(
                ["go", "run", str(go_file)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            run = _parse_native_run(proc.stdout)
            result.runs.append(run)
        except subprocess.TimeoutExpired:
            result.runs.append(
                SingleRun(wall_time_s=-1, cpu_time_s=-1, peak_memory_kb=0, output="TIMEOUT")
            )
    result.aggregate()
    return result


def run_rust(rs_file: Path, n_runs: int) -> BenchResult | None:
    if not _has_tool("rustc"):
        return None
    result = BenchResult(
        benchmark=rs_file.stem,
        language="Rust",
        lines_of_code=_count_lines(rs_file),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        binary = os.path.join(tmpdir, "bench.exe" if os.name == "nt" else "bench")
        comp = subprocess.run(
            ["rustc", "-O", str(rs_file), "-o", binary],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if comp.returncode != 0:
            result.error = f"COMPILE ERROR: {comp.stderr[:300]}"
            return result

        for _ in range(n_runs):
            try:
                proc = subprocess.run(
                    [binary],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                run = _parse_native_run(proc.stdout)
                result.runs.append(run)
            except subprocess.TimeoutExpired:
                result.runs.append(
                    SingleRun(wall_time_s=-1, cpu_time_s=-1, peak_memory_kb=0, output="TIMEOUT")
                )
    result.aggregate()
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

BENCHMARKS = [
    ("01_fibonacci", "Fibonacci (recursive, n=35)"),
    ("02_concurrency", "Message Passing (10K msgs)"),
    ("03_stream_pipeline", "Stream Pipeline (1M items)"),
    ("04_matrix_mul", "Matrix Multiply (100x100)"),
]


def run_all(only: str | None = None, n_runs: int = 3) -> list[BenchComparison]:
    comparisons: list[BenchComparison] = []

    print("=" * 78)
    print("  MAPANARE vs PYTHON vs GO vs RUST -- Benchmark Suite")
    print("=" * 78)

    tools = []
    if _has_tool("go"):
        tools.append("Go")
    if _has_tool("rustc"):
        tools.append("Rust")
    print("\n  Toolchains: Python, Mapanare" + (f", {', '.join(tools)}" if tools else ""))
    print(f"  Runs per benchmark: {n_runs} (median reported)")
    print("  Metrics: wall time, CPU time, peak memory")
    print()

    for bench_id, bench_name in BENCHMARKS:
        if only and only not in bench_id:
            continue

        print(f"  [{bench_id}] {bench_name}")
        print(f"  {'-' * 60}")

        comp = BenchComparison(benchmark=bench_name)

        # Mapanare (interpreted via Python transpiler)
        mn_file = _VS_DIR / f"{bench_id}.mn"
        if mn_file.exists():
            print("    Mapanare  ... ", end="", flush=True)
            try:
                r = run_mapanare(mn_file, n_runs)
                comp.results.append(r)
                if r.error:
                    print(f"ERROR: {r.error}")
                else:
                    print(
                        f"{r.wall_median:.4f}s  "
                        f"CPU:{r.cpu_median:.4f}s  "
                        f"Mem:{r.mem_peak_kb:.0f}KB  "
                        f"({r.lines_of_code} LOC)"
                    )
            except Exception as e:
                print(f"ERROR: {e}")

        # Mapanare Native (LLVM JIT)
        if mn_file.exists() and bench_id != "02_concurrency":
            print("    MN Native ... ", end="", flush=True)
            try:
                r = run_mapanare_native(mn_file, n_runs)
                comp.results.append(r)
                if r.error:
                    print(f"ERROR: {r.error}")
                else:
                    print(
                        f"{r.wall_median:.4f}s  "
                        f"CPU:{r.cpu_median:.4f}s  "
                        f"({r.lines_of_code} LOC)"
                    )
            except Exception as e:
                print(f"ERROR: {e}")

        # Python
        py_file = _VS_DIR / f"{bench_id}.py"
        if py_file.exists():
            print("    Python    ... ", end="", flush=True)
            r = run_python(py_file, n_runs)
            comp.results.append(r)
            print(
                f"{r.wall_median:.4f}s  "
                f"CPU:{r.cpu_median:.4f}s  "
                f"Mem:{r.mem_peak_kb:.0f}KB  "
                f"({r.lines_of_code} LOC)"
            )

        # Go
        go_file = _VS_DIR / f"{bench_id}.go"
        if go_file.exists():
            r = run_go(go_file, n_runs)
            if r:
                comp.results.append(r)
                mem_s = f"Mem:{r.mem_peak_kb:.0f}KB  " if r.mem_peak_kb > 0 else ""
                print(f"    Go        ... {r.wall_median:.4f}s  {mem_s}({r.lines_of_code} LOC)")
            else:
                print("    Go        ... skipped")

        # Rust
        rs_file = _VS_DIR / f"{bench_id}.rs"
        if rs_file.exists():
            r = run_rust(rs_file, n_runs)
            if r:
                comp.results.append(r)
                mem_s = f"Mem:{r.mem_peak_kb:.0f}KB  " if r.mem_peak_kb > 0 else ""
                print(f"    Rust      ... {r.wall_median:.4f}s  {mem_s}({r.lines_of_code} LOC)")
            else:
                print("    Rust      ... skipped")

        comparisons.append(comp)
        print()

    _print_summary(comparisons)

    out_path = _VS_DIR / "results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in comparisons], f, indent=2)
    print(f"\n  Results saved to {out_path}")

    return comparisons


def _print_summary(comparisons: list[BenchComparison]) -> None:
    print("\n" + "=" * 78)
    print("  SUMMARY (median of all runs)")
    print("=" * 78)

    # Performance table
    print("\n  >> PERFORMANCE")
    hdr = (
        f"  {'Benchmark':<28s} {'Lang':<10s} "
        f"{'Wall(s)':>9s} {'CPU(s)':>9s} {'Mem(KB)':>9s} {'vs Py':>8s}"
    )
    print(hdr)
    print("  " + "-" * 73)

    for comp in comparisons:
        py_time = next(
            (r.wall_median for r in comp.results if r.language == "Python" and r.wall_median > 0),
            None,
        )
        for r in comp.results:
            if r.wall_median <= 0 and not r.error:
                print(f"  {comp.benchmark:<28s} {r.language:<10s} {'ERR':>9s}")
                continue
            if r.error:
                print(f"  {comp.benchmark:<28s} {r.language:<10s} {'ERR':>9s}  {r.error[:40]}")
                continue
            vs_py = ""
            if py_time and py_time > 0 and r.wall_median > 0:
                speedup = py_time / r.wall_median
                vs_py = f"{speedup:.1f}x"
            mem_str = f"{r.mem_peak_kb:.0f}" if r.mem_peak_kb > 0 else "N/A"
            cpu_str = f"{r.cpu_median:.4f}" if r.cpu_median > 0 else "N/A"
            print(
                f"  {comp.benchmark:<28s} {r.language:<10s} "
                f"{r.wall_median:>9.4f} {cpu_str:>9s} {mem_str:>9s} {vs_py:>8s}"
            )
        print()

    # Expressiveness table (use Mapanare LOC — same for both interpreted and native)
    print("  >> EXPRESSIVENESS (lines of code -- lower is better)")
    hdr2 = f"  {'Benchmark':<28s} {'Mapanare':>10s} {'Python':>10s} {'Go':>10s} {'Rust':>10s}"
    print(hdr2)
    print("  " + "-" * 68)

    for comp in comparisons:

        def _loc(lang: str) -> str:
            return next((str(r.lines_of_code) for r in comp.results if r.language == lang), "-")

        mn_loc = _loc("Mapanare") if _loc("Mapanare") != "-" else _loc("Mapanare (native)")
        print(
            f"  {comp.benchmark:<28s} "
            f"{mn_loc:>10s} {_loc('Python'):>10s} "
            f"{_loc('Go'):>10s} {_loc('Rust'):>10s}"
        )
    print()


def main() -> None:
    only = None
    n_runs = 3
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--only" and i + 1 < len(args):
            only = args[i + 1]
            i += 2
        elif args[i] == "--runs" and i + 1 < len(args):
            n_runs = int(args[i + 1])
            i += 2
        else:
            i += 1
    run_all(only=only, n_runs=n_runs)


if __name__ == "__main__":
    main()
