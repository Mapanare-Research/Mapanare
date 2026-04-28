"""Cross-language benchmark suite.

Compares Mapanare against 5 other languages across 6 workloads:

  Languages (6)           Workloads (6)
  --------------          --------------
  C (gcc -O2)             fib_recursive
  C (clang -O2)           quicksort
  Rust -O                 struct_alloc
  Go (go build)           enum_match
  Mapanare (mnc opt -O2)  prime_sieve
  Python 3.12             string_concat

Each configuration is run `--runs N` times; the highest and lowest are
dropped and the median of the middle runs is reported (10 runs -> median
of middle 8 by default).

Programs that emit a `__BENCH_METRICS__` block (Go, C, Python-wrapped)
report internal wall time (excludes subprocess spawn). Mapanare and
Rust binaries are timed externally via `time.perf_counter()` wrapped
around `subprocess.run()`, which includes ~1-3 ms of spawn overhead.
This is documented in the methodology section of FULL_COMPARISON.md.

Usage:
    python benchmarks/cross_language/run_benchmarks.py
    python benchmarks/cross_language/run_benchmarks.py --runs 10
    python benchmarks/cross_language/run_benchmarks.py --only fib_recursive
    python benchmarks/cross_language/run_benchmarks.py --only fib --runs 3
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BENCH_DIR = Path(__file__).resolve().parent
RUNTIME_LIB = ROOT / "runtime" / "native" / "libmapanare_rt.a"

# v5.0.6 Bn.3: read live VERSION file instead of hardcoding.
# Prior to this fix, every benchmark JSON claimed version "4.125.0"
# regardless of the tree state — three cycles of Mamba review flagged it.
MAPANARE_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RESULTS_FILE = BENCH_DIR / f"v{MAPANARE_VERSION}-results.json"


def geomean(ratios: list[float]) -> float:
    """Geometric mean of positive ratios.

    Returns ``math.nan`` for empty input or any non-positive ratio —
    the geometric mean is undefined for those cases, and a 0.0
    sentinel would silently read as "infinitely fast" in benchmark
    summaries.

    >>> geomean([1.0, 4.0])
    2.0
    >>> round(geomean([0.5, 2.0, 8.0]), 6)
    2.0
    """
    if not ratios or any(r <= 0 for r in ratios):
        return math.nan
    return math.exp(sum(math.log(r) for r in ratios) / len(ratios))


# ---------------------------------------------------------------------------
# Benchmark registry
# ---------------------------------------------------------------------------


@dataclass
class BenchSpec:
    """Where each language's source for this workload lives + expected output."""

    name: str
    expected: str  # Prefix match against stdout first line.
    mn_path: Path
    py_path: Path
    rs_path: Path
    go_path: Path
    c_path: Path


BENCHMARKS: list[BenchSpec] = [
    BenchSpec(
        name="fib_recursive",
        expected="fib(35) = 9227465",
        mn_path=ROOT / "benchmarks" / "optimizer" / "fib_recursive.mn",
        py_path=ROOT / "benchmarks" / "optimizer" / "fib_recursive.py",
        rs_path=ROOT / "benchmarks" / "optimizer" / "fib_recursive.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "fib_recursive.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "fib_recursive.c",
    ),
    BenchSpec(
        name="quicksort",
        expected="checksum = 485",
        mn_path=ROOT / "benchmarks" / "optimizer" / "quicksort.mn",
        py_path=ROOT / "benchmarks" / "optimizer" / "quicksort.py",
        rs_path=ROOT / "benchmarks" / "optimizer" / "quicksort.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "quicksort.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "quicksort.c",
    ),
    BenchSpec(
        name="struct_alloc",
        expected="checksum = 29999700000",
        mn_path=ROOT / "benchmarks" / "system" / "struct_alloc.mn",
        py_path=ROOT / "benchmarks" / "system" / "struct_alloc.py",
        rs_path=ROOT / "benchmarks" / "system" / "struct_alloc.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "struct_alloc.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "struct_alloc.c",
    ),
    BenchSpec(
        name="enum_match",
        expected="checksum = 52818168",
        mn_path=ROOT / "benchmarks" / "system" / "enum_match.mn",
        py_path=ROOT / "benchmarks" / "system" / "enum_match.py",
        rs_path=ROOT / "benchmarks" / "system" / "enum_match.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "enum_match.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "enum_match.c",
    ),
    BenchSpec(
        name="prime_sieve",
        expected="primes = 9592",
        # list_ops.mn is the Mapanare prime sieve; file is named list_ops
        # for historical reasons but implements trial-division prime counting.
        mn_path=ROOT / "benchmarks" / "system" / "list_ops.mn",
        py_path=ROOT / "benchmarks" / "system" / "list_ops.py",
        rs_path=ROOT / "benchmarks" / "system" / "list_ops.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "prime_sieve.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "prime_sieve.c",
    ),
    BenchSpec(
        name="string_concat",
        expected="len = 50000",
        mn_path=ROOT / "benchmarks" / "optimizer" / "string_concat.mn",
        py_path=ROOT / "benchmarks" / "optimizer" / "string_concat.py",
        rs_path=ROOT / "benchmarks" / "optimizer" / "string_concat.rs",
        go_path=ROOT / "benchmarks" / "cross_language" / "go" / "string_concat.go",
        c_path=ROOT / "benchmarks" / "cross_language" / "c" / "string_concat.c",
    ),
]


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class SingleRun:
    wall_time_s: float = -1.0
    cpu_time_s: float = -1.0
    peak_memory_kb: float = 0.0
    output: str = ""


@dataclass
class LangResult:
    benchmark: str
    language: str
    lines_of_code: int = 0
    binary_size_bytes: int = 0
    runs: list[SingleRun] = field(default_factory=list)
    wall_median_ms: float = 0.0
    wall_min_ms: float = 0.0
    cpu_median_ms: float = 0.0
    mem_peak_kb: float = 0.0
    correct: bool = False
    error: str = ""

    def aggregate(self, expected: str) -> None:
        valid = [r for r in self.runs if r.wall_time_s >= 0]
        if not valid:
            return
        # Drop highest and lowest if we have at least 4 runs; otherwise keep all.
        walls = sorted(r.wall_time_s for r in valid)
        if len(walls) >= 4:
            walls = walls[1:-1]
        self.wall_median_ms = statistics.median(walls) * 1000.0
        self.wall_min_ms = min(walls) * 1000.0
        self.cpu_median_ms = statistics.median(r.cpu_time_s for r in valid) * 1000.0
        self.mem_peak_kb = max(r.peak_memory_kb for r in valid)
        # Correctness: all runs must have produced the expected output.
        self.correct = all(r.output.startswith(expected) or expected in r.output for r in valid)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_tool(name: str) -> str | None:
    """Find a tool binary, trying plain name then -18, -17 suffixes."""
    for candidate in [name, f"{name}-18", f"{name}-17"]:
        p = shutil.which(candidate)
        if p:
            return p
    # Special cases for per-user installs
    if name == "go" and not shutil.which("go"):
        home_go = Path.home() / "go" / "bin" / "go"
        if home_go.exists():
            return str(home_go)
    return None


def _count_lines(path: Path) -> int:
    """Count non-empty, non-comment lines, excluding instrumentation code."""
    if not path.exists():
        return 0
    SKIP_KWS = [
        "__BENCH_METRICS__",
        "wall_time_s=",
        "peak_memory_kb=",
        "cpu_time_s=",
        "runtime.GC",
        "runtime.ReadMemStats",
        "getrusage",
        "clock_gettime",
        "syscall.Getrusage",
        "tv_to_sec",
        "ts_to_sec",
        "timevalSub",
        "RUSAGE_SELF",
        "CLOCK_MONOTONIC",
        "sys/resource.h",
        "sys/time.h",
        "struct rusage",
        "struct timespec",
        "tracemalloc",
        "perf_counter",
    ]
    count = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("//", "#", "/*", "*")):
            continue
        if any(kw in line for kw in SKIP_KWS):
            continue
        count += 1
    return count


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


def _strip_metrics(output: str) -> str:
    """Remove __BENCH_METRICS__ block from output, leaving only program stdout."""
    lines: list[str] = []
    for line in output.splitlines():
        s = line.strip()
        if s == "__BENCH_METRICS__":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _run_with_metrics(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> SingleRun:
    """Run a binary that emits __BENCH_METRICS__, parse internal timing.

    Wall time and CPU time come from the program's own __BENCH_METRICS__
    block (excludes subprocess spawn). Peak memory comes from
    /usr/bin/time -v wrapping around the child, because the program's own
    getrusage(RUSAGE_SELF).ru_maxrss is inflated by Python's RSS at fork
    time (pre-exec COW pages count toward the child's peak RSS).
    """
    use_gnu_time = Path(_TIME_BIN).is_file()
    wrapped = [_TIME_BIN, "-v", "--"] + cmd if use_gnu_time else cmd
    try:
        t0 = time.perf_counter()
        r = subprocess.run(wrapped, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        t1 = time.perf_counter()
    except subprocess.TimeoutExpired:
        return SingleRun(output="TIMEOUT")

    if r.returncode != 0:
        return SingleRun(output=f"ERROR rc={r.returncode}: {r.stderr[:200]}")

    metrics = _parse_metrics(r.stdout)
    clean = _strip_metrics(r.stdout)
    wall = metrics.get("wall_time_s", t1 - t0)
    if use_gnu_time:
        peak_kb, _ = _parse_gnu_time(r.stderr)
    else:
        peak_kb = metrics.get("peak_memory_kb", 0.0)
    return SingleRun(
        wall_time_s=wall,
        cpu_time_s=metrics.get("cpu_time_s", wall),
        peak_memory_kb=peak_kb,
        output=clean,
    )


_TIME_BIN = "/usr/bin/time"


def _parse_gnu_time(stderr: str) -> tuple[float, float]:
    """Parse /usr/bin/time -v output; return (peak_kb, cpu_seconds)."""
    peak_kb = 0.0
    user_s = 0.0
    sys_s = 0.0
    for raw in stderr.splitlines():
        line = raw.strip()
        if line.startswith("Maximum resident set size"):
            peak_kb = float(line.split(":")[-1].strip())
        elif line.startswith("User time"):
            user_s = float(line.split(":")[-1].strip())
        elif line.startswith("System time"):
            sys_s = float(line.split(":")[-1].strip())
    return peak_kb, user_s + sys_s


def _run_external(cmd: list[str], timeout: int = 120) -> SingleRun:
    """Run a binary that doesn't emit metrics; measure via /usr/bin/time -v.

    Wall time uses perf_counter (includes ~1-3 ms /usr/bin/time overhead plus
    subprocess spawn). Peak memory and CPU time come from GNU time's
    structured output, which gives accurate per-process rusage.
    """
    use_gnu_time = Path(_TIME_BIN).is_file()
    wrapped = [_TIME_BIN, "-v", "--"] + cmd if use_gnu_time else cmd
    try:
        t0 = time.perf_counter()
        r = subprocess.run(wrapped, capture_output=True, text=True, timeout=timeout)
        t1 = time.perf_counter()
    except subprocess.TimeoutExpired:
        return SingleRun(output="TIMEOUT")

    if r.returncode != 0:
        return SingleRun(output=f"ERROR rc={r.returncode}: {r.stderr[:200]}")

    if use_gnu_time:
        peak_kb, cpu = _parse_gnu_time(r.stderr)
    else:
        peak_kb, cpu = 0.0, t1 - t0
    return SingleRun(
        wall_time_s=t1 - t0,
        cpu_time_s=cpu,
        peak_memory_kb=peak_kb,
        output=r.stdout.strip(),
    )


# ---------------------------------------------------------------------------
# Language runners
# ---------------------------------------------------------------------------


def run_mapanare_o2(spec: BenchSpec, n_runs: int) -> LangResult:
    """Compile .mn to native via LLVM -O2 pipeline, run, parse __BENCH_METRICS__.

    v4.148.0 (E4): Links against mn_bench_main.c instead of mn_user_main.c so
    the binary emits __BENCH_METRICS__ with internal wall time (clock_gettime).
    This matches the Rust/Go/C methodology: timing excludes subprocess spawn.
    Prior to v4.148.0, Mapanare used _run_external (perf_counter around
    subprocess.run), which included ~1.2 ms of spawn overhead — pinning the
    reported wall time at >= 1.2 ms regardless of actual compute and producing
    a spurious 30x+ gap vs Rust on sub-millisecond workloads.
    """
    result = LangResult(
        benchmark=spec.name,
        language="Mapanare O2",
        lines_of_code=_count_lines(spec.mn_path),
    )

    tools = {t: _find_tool(t) for t in ["llvm-as", "opt", "llc", "clang"]}
    if not all(tools.values()):
        missing = [k for k, v in tools.items() if not v]
        result.error = f"missing tools: {missing}"
        return result

    if not RUNTIME_LIB.exists():
        result.error = f"missing runtime library: {RUNTIME_LIB}"
        return result

    bench_main_c = BENCH_DIR / "mn_bench_main.c"
    if not bench_main_c.exists():
        result.error = f"missing benchmark wrapper: {bench_main_c}"
        return result
    objcopy = _find_tool("objcopy")
    if not objcopy:
        result.error = "objcopy not installed (needed for benchmark timing wrapper)"
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        name = spec.mn_path.stem
        ll = td / f"{name}.ll"
        bc = td / f"{name}.bc"
        opt_bc = td / f"{name}.opt.bc"
        obj = td / f"{name}.o"
        obj_renamed = td / f"{name}.renamed.o"
        bench_main_obj = td / "mn_bench_main.o"
        binary = td / name

        emit_cmd = [sys.executable, "-m", "mapanare", "emit-llvm", str(spec.mn_path), "-o", str(ll)]
        # Compile the benchmark timing wrapper
        bench_main_cmd = [
            tools["clang"],
            "-O2",
            "-c",
            str(bench_main_c),
            "-o",
            str(bench_main_obj),
        ]
        llc_cmd = [
            tools["llc"],
            "-filetype=obj",
            "-relocation-model=pic",
            str(opt_bc),
            "-o",
            str(obj),
        ]
        # The Python bootstrap emitter generates main(), not mn_main().
        # Rename main -> mn_main so mn_bench_main.c can wrap it with timing.
        rename_cmd = [objcopy, "--redefine-sym", "main=mn_main", str(obj), str(obj_renamed)]
        link_cmd = [
            tools["clang"],
            str(obj_renamed),
            str(bench_main_obj),
            str(RUNTIME_LIB),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(binary),
        ]
        steps = [
            (emit_cmd, "emit"),
            (bench_main_cmd, "bench_main"),
            ([tools["llvm-as"], str(ll), "-o", str(bc)], "llvm-as"),
            ([tools["opt"], "-O2", str(bc), "-o", str(opt_bc)], "opt"),
            (llc_cmd, "llc"),
            (rename_cmd, "rename_main"),
            (link_cmd, "link"),
        ]
        for cmd, stage in steps:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                result.error = f"compile_fail at {stage}: {r.stderr[:200]}"
                return result

        result.binary_size_bytes = binary.stat().st_size
        # Warmup
        _run_with_metrics([str(binary)], timeout=60)
        for _ in range(n_runs):
            result.runs.append(_run_with_metrics([str(binary)], timeout=60))

    result.aggregate(spec.expected)
    return result


def run_python(spec: BenchSpec, n_runs: int) -> LangResult:
    """Wrap Python source with tracemalloc + timing, emit __BENCH_METRICS__."""
    result = LangResult(
        benchmark=spec.name,
        language="Python 3.12",
        lines_of_code=_count_lines(spec.py_path),
    )
    if not spec.py_path.exists():
        result.error = f"missing: {spec.py_path}"
        return result

    source = spec.py_path.read_text(encoding="utf-8")
    wrapped = (
        "import time, tracemalloc, sys\n"
        "tracemalloc.start()\n"
        "_cpu0 = time.process_time()\n"
        "_wall0 = time.perf_counter()\n"
        "try:\n"
    )
    for line in source.splitlines():
        if line.strip() == "":
            wrapped += "\n"
        else:
            wrapped += "    " + line + "\n"
    wrapped += (
        "finally:\n"
        "    _wall1 = time.perf_counter() - _wall0\n"
        "    _cpu1 = time.process_time() - _cpu0\n"
        "    _mem = tracemalloc.get_traced_memory()[1]\n"
        "    tracemalloc.stop()\n"
        "    print('__BENCH_METRICS__')\n"
        "    print('wall_time_s=' + str(round(_wall1, 6)))\n"
        "    print('cpu_time_s=' + str(round(_cpu1, 6)))\n"
        "    print('peak_memory_kb=' + str(round(_mem / 1024, 1)))\n"
    )

    # Warmup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(wrapped)
        tmp_path = tmp.name

    try:
        _run_with_metrics([sys.executable, tmp_path])
        for _ in range(n_runs):
            result.runs.append(_run_with_metrics([sys.executable, tmp_path]))
    finally:
        os.unlink(tmp_path)

    result.aggregate(spec.expected)
    return result


def run_rust(spec: BenchSpec, n_runs: int) -> LangResult:
    """Compile .rs with rustc -O, run the pre-built binary, parse
    ``__BENCH_METRICS__`` for internal wall time.

    **v4.143.0 (Bn.1):** Rust benchmarks emit ``__BENCH_METRICS__`` the same
    way Go/C/Python do (``std::time::Instant::now().elapsed()`` around
    ``main``'s body), so timing excludes subprocess spawn — matches
    Go/C/Python methodology. Prior to v4.143.0 the Rust path was timed
    externally via ``perf_counter()`` and accumulated a ~10 ms subprocess-
    spawn + GNU-time floor, which pinned Rust medians at 9.5–11 ms on
    short workloads and corrupted the v4.142.0 benchmark pack (Mamba's
    Bn.1 finding at the v4.143.0 panel).
    """
    result = LangResult(
        benchmark=spec.name,
        language="Rust -O",
        lines_of_code=_count_lines(spec.rs_path),
    )
    if not spec.rs_path.exists():
        result.error = f"missing: {spec.rs_path}"
        return result
    rustc = _find_tool("rustc")
    if not rustc:
        result.error = "rustc not installed"
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        binary = Path(tmpdir) / spec.rs_path.stem
        r = subprocess.run(
            [rustc, "-O", str(spec.rs_path), "-o", str(binary)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            result.error = f"compile_fail: {r.stderr[:200]}"
            return result

        result.binary_size_bytes = binary.stat().st_size
        # Warmup: populates file caches and pre-resolves any dynamic
        # linking cost. Not included in reported runs.
        _run_with_metrics([str(binary)], timeout=60)
        for _ in range(n_runs):
            result.runs.append(_run_with_metrics([str(binary)], timeout=60))

    result.aggregate(spec.expected)
    return result


def run_go_compiled(spec: BenchSpec, n_runs: int) -> LangResult:
    """Compile .go with `go build -o bin`, run bin, parse __BENCH_METRICS__."""
    result = LangResult(
        benchmark=spec.name,
        language="Go",
        lines_of_code=_count_lines(spec.go_path),
    )
    if not spec.go_path.exists():
        result.error = f"missing: {spec.go_path}"
        return result
    go = _find_tool("go")
    if not go:
        result.error = "go not installed"
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        binary = Path(tmpdir) / spec.name
        # Suppress GOPATH warning noise with explicit GOPATH env.
        env = os.environ.copy()
        env["GOPATH"] = env.get("GOPATH") or str(Path.home() / "gopath")
        r = subprocess.run(
            [go, "build", "-o", str(binary), str(spec.go_path)],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if r.returncode != 0:
            result.error = f"compile_fail: {r.stderr[:200]}"
            return result

        result.binary_size_bytes = binary.stat().st_size
        _run_with_metrics([str(binary)], timeout=60)
        for _ in range(n_runs):
            result.runs.append(_run_with_metrics([str(binary)], timeout=60))

    result.aggregate(spec.expected)
    return result


def _run_c_variant(
    spec: BenchSpec,
    n_runs: int,
    compiler_tool: str,
    language_label: str,
) -> LangResult:
    """Shared runner for C (gcc) and C (clang) variants."""
    result = LangResult(
        benchmark=spec.name,
        language=language_label,
        lines_of_code=_count_lines(spec.c_path),
    )
    if not spec.c_path.exists():
        result.error = f"missing: {spec.c_path}"
        return result
    cc = _find_tool(compiler_tool)
    if not cc:
        result.error = f"{compiler_tool} not installed"
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        binary = Path(tmpdir) / spec.name
        r = subprocess.run(
            [cc, "-O2", "-Wall", "-Wextra", str(spec.c_path), "-o", str(binary)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            result.error = f"compile_fail: {r.stderr[:200]}"
            return result

        result.binary_size_bytes = binary.stat().st_size
        _run_with_metrics([str(binary)], timeout=60)
        for _ in range(n_runs):
            result.runs.append(_run_with_metrics([str(binary)], timeout=60))

    result.aggregate(spec.expected)
    return result


def run_c_gcc(spec: BenchSpec, n_runs: int) -> LangResult:
    return _run_c_variant(spec, n_runs, "gcc", "C (gcc -O2)")


def run_c_clang(spec: BenchSpec, n_runs: int) -> LangResult:
    return _run_c_variant(spec, n_runs, "clang", "C (clang -O2)")


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

LANG_ORDER = [
    ("C (gcc -O2)", run_c_gcc),
    ("C (clang -O2)", run_c_clang),
    ("Rust -O", run_rust),
    ("Go", run_go_compiled),
    ("Mapanare O2", run_mapanare_o2),
    ("Python 3.12", run_python),
]


def run_all(only: str | None, n_runs: int) -> dict:
    print("=" * 78)
    print(f"  CROSS-LANGUAGE BENCHMARK SUITE (v{MAPANARE_VERSION}) -- {n_runs} runs per config")
    print("=" * 78)

    tool_report = {
        "gcc": _find_tool("gcc"),
        "clang": _find_tool("clang"),
        "rustc": _find_tool("rustc"),
        "go": _find_tool("go"),
        "python": sys.executable,
    }
    print()
    for name, path in tool_report.items():
        print(f"  {name:<8s} {path or 'NOT FOUND'}")
    print()

    all_results: list[LangResult] = []
    for spec in BENCHMARKS:
        if only and only not in spec.name:
            continue
        print(f"[{spec.name}]")
        for label, runner in LANG_ORDER:
            _ = label  # display label comes from runner
            res = runner(spec, n_runs)
            all_results.append(res)
            if res.error:
                print(f"  {res.language:<16s} ERR: {res.error[:80]}")
            else:
                status = "ok" if res.correct else "WRONG CHECKSUM"
                mem = f"mem={res.mem_peak_kb:>7.0f}KB" if res.mem_peak_kb > 0 else "mem=N/A"
                bin_kb = (
                    f"bin={res.binary_size_bytes / 1024:>6.1f}KB"
                    if res.binary_size_bytes
                    else "bin=N/A"
                )
                print(
                    f"  {res.language:<16s} "
                    f"wall={res.wall_median_ms:>8.3f}ms  "
                    f"{mem}  "
                    f"{bin_kb}  "
                    f"loc={res.lines_of_code:>3d}  "
                    f"[{status}]"
                )
        print()

    out: dict = {
        "version": MAPANARE_VERSION,
        "date": time.strftime("%Y-%m-%d"),
        "runs_per_config": n_runs,
        "environment": {
            "os": "WSL2 (Ubuntu on Windows)",
            "llvm_version": "18.1.3",
            "python_version": sys.version.split()[0],
            "tools": {k: v for k, v in tool_report.items()},
        },
        "results": [asdict(r) for r in all_results],
    }
    # v5.1.2 Bn.2: compute and embed geomean ratios in the JSON so downstream
    # reports can cite them without recomputing. Mamba v4.154.0 flagged the
    # prior approach (external recomputation diverging from reported numbers).
    gm = _compute_geomean_ratios(out)
    if gm:
        out["geomean_ratios"] = {k: round(v, 4) for k, v in gm.items()}
    return out


def _compute_geomean_ratios(data: dict) -> dict[str, float]:
    """Compute Mn/Lang geomean ratios from raw results.

    v5.1.2 Bn.2: independent geomean computation from per-benchmark medians.
    Returns {lang_name: geomean_ratio} where ratio = Mn_time / Lang_time.
    """
    by_bench: dict[str, dict[str, float]] = {}
    for entry in data["results"]:
        wm = entry.get("wall_median_ms", 0)
        if wm > 0:
            by_bench.setdefault(entry["benchmark"], {})[entry["language"]] = wm

    ratios_per_lang: dict[str, list[float]] = {}
    for bench_name, lang_times in by_bench.items():
        mn_time = lang_times.get("Mapanare")
        if mn_time is None or mn_time <= 0:
            continue
        for lang, lt in lang_times.items():
            if lang == "Mapanare" or lt <= 0:
                continue
            ratios_per_lang.setdefault(lang, []).append(mn_time / lt)

    return {lang: geomean(rs) for lang, rs in ratios_per_lang.items() if rs}


def _format_summary_table(data: dict) -> str:
    """Format the 6-column comparison table as Markdown."""
    lines: list[str] = []
    by_bench: dict[str, dict[str, LangResult]] = {}
    for entry in data["results"]:
        by_bench.setdefault(entry["benchmark"], {})[entry["language"]] = entry

    langs = [ln for ln, _ in LANG_ORDER]
    header = "| Benchmark       | " + " | ".join(f"{ln}" for ln in langs) + " |"
    sep = "|" + "---|" * (len(langs) + 1)
    lines.append(header)
    lines.append(sep)
    for spec in BENCHMARKS:
        row = [f"{spec.name:<15s}"]
        for ln in langs:
            r = by_bench.get(spec.name, {}).get(ln)
            if r and r.get("wall_median_ms", 0) > 0:
                row.append(f"{r['wall_median_ms']:.3f} ms")
            elif r and r.get("error"):
                row.append("ERR")
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    # v5.1.2 Bn.2: append geomean ratios
    gm = _compute_geomean_ratios(data)
    if gm:
        lines.append("")
        lines.append("**Mn/Lang geomean ratios** (lower = faster than Lang):")
        for lang, ratio in sorted(gm.items()):
            lines.append(f"  Mn/{lang}: {ratio:.3f}x")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"v{MAPANARE_VERSION} cross-language benchmark suite"
    )
    parser.add_argument("--runs", type=int, default=10, help="runs per config (default: 10)")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="substring match against benchmark name",
    )
    parser.add_argument("--output", type=str, default=str(RESULTS_FILE))
    args = parser.parse_args()

    data = run_all(only=args.only, n_runs=args.runs)

    out_path = Path(args.output)
    out_path.write_text(json.dumps(data, indent=2, default=str) + "\n")

    print("=" * 78)
    print("  SUMMARY TABLE (median wall time, ms)")
    print("=" * 78)
    print()
    print(_format_summary_table(data))
    print()
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
