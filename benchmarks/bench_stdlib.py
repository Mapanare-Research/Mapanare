"""v0.9.0 Stdlib compilation benchmarks.

Measures compilation time (parse → semantic → MIR → LLVM IR) for each stdlib
module. These are compilation benchmarks, not runtime benchmarks — runtime
performance requires full binary linking which is not yet automated.

Metrics:
  - Lines of .mn source
  - Time to compile to LLVM IR (median of N runs)
  - LLVM IR output size (characters)
  - Lines per second (source lines / compilation time)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from statistics import median

try:
    from mapanare.cli import _compile_to_llvm_ir

    HAS_COMPILER = True
except ImportError:
    HAS_COMPILER = False

_STDLIB = Path(__file__).resolve().parent.parent / "stdlib"

_MODULES: dict[str, Path] = {
    "encoding/json": _STDLIB / "encoding" / "json.mn",
    "encoding/csv": _STDLIB / "encoding" / "csv.mn",
    "net/http": _STDLIB / "net" / "http.mn",
    "net/http/server": _STDLIB / "net" / "http" / "server.mn",
    "net/websocket": _STDLIB / "net" / "websocket.mn",
    "crypto": _STDLIB / "crypto.mn",
    "text/regex": _STDLIB / "text" / "regex.mn",
}


@dataclass
class StdlibBenchResult:
    module: str
    source_lines: int
    compile_time_ms: float
    ir_size_chars: int
    lines_per_second: float


def _compile_module(source: str, name: str) -> tuple[str, float]:
    """Compile a module source and return (IR output, elapsed_ms)."""
    # Add a main function so the compiler has an entry point
    full_source = source + '\n\nfn main() {\n    println("ok")\n}\n'
    start = time.perf_counter()
    ir_out = _compile_to_llvm_ir(full_source, f"{name}.mn", use_mir=True)
    elapsed = (time.perf_counter() - start) * 1000
    return ir_out, elapsed


def run_stdlib_benchmarks(n_runs: int = 5) -> list[StdlibBenchResult]:
    """Benchmark each stdlib module compilation."""
    if not HAS_COMPILER:
        print("Compiler not available — skipping stdlib benchmarks")
        return []

    results: list[StdlibBenchResult] = []

    for name, path in _MODULES.items():
        if not path.exists():
            print(f"  SKIP {name} — file not found: {path}")
            continue

        source = path.read_text(encoding="utf-8")
        source_lines = len(source.splitlines())

        # Warmup
        try:
            _compile_module(source, name)
        except Exception as e:
            print(f"  SKIP {name} — compilation error: {e}")
            continue

        # Timed runs
        times: list[float] = []
        ir_out = ""
        for _ in range(n_runs):
            ir_out, elapsed = _compile_module(source, name)
            times.append(elapsed)

        med_time = median(times)
        lps = (source_lines / med_time) * 1000 if med_time > 0 else 0

        results.append(
            StdlibBenchResult(
                module=name,
                source_lines=source_lines,
                compile_time_ms=round(med_time, 2),
                ir_size_chars=len(ir_out),
                lines_per_second=round(lps, 0),
            )
        )

    return results


def print_report(results: list[StdlibBenchResult]) -> None:
    """Print a formatted benchmark report."""
    print("\n" + "=" * 78)
    print("v0.9.0 Stdlib Compilation Benchmarks")
    print("=" * 78)
    print(f"{'Module':<22} {'Lines':>6} {'Time (ms)':>10} {'IR Size':>10} {'Lines/s':>10}")
    print("-" * 78)

    total_lines = 0
    total_time = 0.0

    for r in results:
        print(
            f"{r.module:<22} {r.source_lines:>6} {r.compile_time_ms:>10.2f} "
            f"{r.ir_size_chars:>10,} {r.lines_per_second:>10,.0f}"
        )
        total_lines += r.source_lines
        total_time += r.compile_time_ms

    print("-" * 78)
    total_lps = (total_lines / total_time) * 1000 if total_time > 0 else 0
    print(f"{'TOTAL':<22} {total_lines:>6} {total_time:>10.2f} " f"{'':>10} {total_lps:>10,.0f}")
    print("=" * 78)


def main() -> None:
    """Entry point for stdlib benchmarks."""
    results = run_stdlib_benchmarks(n_runs=5)
    if results:
        print_report(results)


if __name__ == "__main__":
    main()
