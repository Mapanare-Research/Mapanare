#!/usr/bin/env python3
"""Golden test harness for the Mapanare compiler.

One command to answer: "does the compiler work, and how fast?"

Usage:
    python scripts/test_native.py                                    # Bootstrap only
    python scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # Compare with native
    python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run  # Also run via lli
    python scripts/test_native.py --bless                            # Update reference files
    python scripts/test_native.py --filter fib -v                    # One test, verbose
    python scripts/test_native.py --bench                            # Write BENCHMARKS.md

Golden files: tests/golden/*.mn
Reference IR: tests/golden/*.ref.ll
Benchmark table: tests/golden/BENCHMARKS.md
"""

from __future__ import annotations

import argparse
import os
import pathlib
import platform
import re
try:
    import resource
except ImportError:
    resource = None  # type: ignore[assignment]
import shutil
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
BENCH_FILE = GOLDEN_DIR / "BENCHMARKS.md"


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

class C:
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def off():
        C.GREEN = C.RED = C.YELLOW = C.DIM = C.BOLD = C.RESET = ""


# ---------------------------------------------------------------------------
# Resource measurement
# ---------------------------------------------------------------------------

def _get_rusage():
    """Get resource usage (Unix only)."""
    try:
        return resource.getrusage(resource.RUSAGE_CHILDREN)
    except Exception:
        return None


def _rss_mb() -> float:
    """Current process RSS in MB."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    # Fallback: /proc on Linux
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return 0.0


class Metrics:
    """Timing and resource metrics for a compilation."""
    def __init__(self):
        self.time_ms: float = 0.0
        self.peak_rss_mb: float = 0.0
        self.ir_lines: int = 0
        self.ir_bytes: int = 0
        self.defines: int = 0
        self.source_lines: int = 0

    def __repr__(self):
        return f"{self.time_ms:.0f}ms, {self.peak_rss_mb:.0f}MB, {self.ir_lines}L"


def measure_compile(fn, *args) -> tuple[any, Metrics]:
    """Run a compile function and measure time + memory."""
    m = Metrics()
    rss_before = _rss_mb()
    t0 = time.perf_counter()
    result = fn(*args)
    t1 = time.perf_counter()
    rss_after = _rss_mb()
    m.time_ms = (t1 - t0) * 1000
    m.peak_rss_mb = max(rss_after - rss_before, 0)
    return result, m


# ---------------------------------------------------------------------------
# IR analysis
# ---------------------------------------------------------------------------

def count_defines(ir: str) -> int:
    return len(re.findall(r"^define\s", ir, re.MULTILINE))


def count_declares(ir: str) -> int:
    return len(re.findall(r"^declare\s", ir, re.MULTILINE))


def has_main(ir: str) -> bool:
    return bool(re.search(r'define\s.*@"?main"?', ir))


def extract_function_names(ir: str) -> list[str]:
    return re.findall(r'define\s+(?:internal\s+)?[^@]*@"?([^"(]+)"?', ir)


def ir_fingerprint(ir: str) -> dict:
    return {
        "defines": count_defines(ir),
        "declares": count_declares(ir),
        "has_main": has_main(ir),
        "functions": sorted(extract_function_names(ir)),
        "lines": ir.count("\n"),
        "has_strings": "@.str" in ir or "private constant" in ir,
    }


# ---------------------------------------------------------------------------
# Compilers
# ---------------------------------------------------------------------------

def compile_bootstrap(mn_file: pathlib.Path) -> tuple[str, str]:
    try:
        from mapanare.cli import _compile_to_llvm_ir
        ir = _compile_to_llvm_ir(mn_file.read_text(encoding="utf-8"), str(mn_file))
        return ir, ""
    except Exception as e:
        return "", str(e)


def compile_stage1(mn_file: pathlib.Path, stage1: pathlib.Path) -> tuple[str, str]:
    try:
        result = subprocess.run(
            [str(stage1), str(mn_file)],
            capture_output=True, timeout=30,
        )
        stdout = result.stdout.decode(errors="replace")
        stderr = result.stderr.decode(errors="replace")
        if result.returncode != 0:
            return "", stderr or f"exit code {result.returncode}"
        return stdout, ""
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT (30s)"
    except FileNotFoundError:
        return "", f"binary not found: {stage1}"


def run_ir(ir: str, test_name: str) -> tuple[str, str]:
    ir_path = pathlib.Path(f"/tmp/mn_golden_{test_name}.ll")
    ir_path.write_text(ir, encoding="utf-8")
    lli = shutil.which("lli")
    if not lli:
        return "", "lli not found"
    try:
        result = subprocess.run(
            [lli, str(ir_path)], capture_output=True, timeout=10,
        )
        stdout = result.stdout.decode(errors="replace")
        stderr = result.stderr.decode(errors="replace")
        if result.returncode != 0:
            return "", f"lli exit {result.returncode}: {stderr[:200]}"
        return stdout, ""
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    finally:
        ir_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test result
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.source_lines = 0
        self.bootstrap_ok = False
        self.bootstrap_err = ""
        self.bootstrap_ir = ""
        self.bootstrap_metrics = Metrics()
        self.stage1_ok: bool | None = None
        self.stage1_err = ""
        self.stage1_ir = ""
        self.stage1_metrics = Metrics()
        self.run_ok: bool | None = None
        self.run_err = ""
        self.run_output = ""
        self.compare_ok: bool | None = None
        self.compare_diff = ""

    @property
    def passed(self) -> bool:
        if not self.bootstrap_ok:
            return False
        if self.stage1_ok is not None and not self.stage1_ok:
            return False
        if self.compare_ok is not None and not self.compare_ok:
            return False
        return True

    @property
    def status_str(self) -> str:
        return f"{C.GREEN}PASS{C.RESET}" if self.passed else f"{C.RED}FAIL{C.RESET}"


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_test(
    mn_file: pathlib.Path,
    stage1: pathlib.Path | None,
    do_run: bool,
) -> TestResult:
    name = mn_file.stem
    r = TestResult(name)
    r.source_lines = mn_file.read_text(encoding="utf-8").count("\n")

    # Bootstrap
    (r.bootstrap_ir, r.bootstrap_err), r.bootstrap_metrics = measure_compile(
        compile_bootstrap, mn_file,
    )
    if r.bootstrap_err:
        return r

    fp = ir_fingerprint(r.bootstrap_ir)
    r.bootstrap_ok = fp["defines"] > 0
    r.bootstrap_metrics.ir_lines = fp["lines"]
    r.bootstrap_metrics.ir_bytes = len(r.bootstrap_ir.encode())
    r.bootstrap_metrics.defines = fp["defines"]
    r.bootstrap_metrics.source_lines = r.source_lines

    if not r.bootstrap_ok:
        r.bootstrap_err = f"0 defines, {fp['lines']} lines"
        return r

    # Stage 1
    if stage1:
        (r.stage1_ir, r.stage1_err), r.stage1_metrics = measure_compile(
            compile_stage1, mn_file, stage1,
        )
        if r.stage1_err:
            r.stage1_ok = False
        else:
            sfp = ir_fingerprint(r.stage1_ir)
            r.stage1_ok = sfp["defines"] > 0
            r.stage1_metrics.ir_lines = sfp["lines"]
            r.stage1_metrics.ir_bytes = len(r.stage1_ir.encode())
            r.stage1_metrics.defines = sfp["defines"]
            if not r.stage1_ok:
                r.stage1_err = f"0 defines, {sfp['lines']} lines"

            if r.stage1_ok:
                r.compare_ok = True
                diffs = []
                if sfp["defines"] != fp["defines"]:
                    diffs.append(f"defines: {fp['defines']} vs {sfp['defines']}")
                    r.compare_ok = False
                if sfp["has_main"] != fp["has_main"]:
                    diffs.append(f"main: {fp['has_main']} vs {sfp['has_main']}")
                    r.compare_ok = False
                missing = set(fp["functions"]) - set(sfp["functions"])
                if missing:
                    diffs.append(f"missing: {missing}")
                    r.compare_ok = False
                r.compare_diff = "; ".join(diffs)

    # Run
    if do_run and r.bootstrap_ok:
        r.run_output, r.run_err = run_ir(r.bootstrap_ir, name)
        r.run_ok = r.run_err == ""

    return r


# ---------------------------------------------------------------------------
# Benchmark table
# ---------------------------------------------------------------------------

def write_benchmarks(results: list[TestResult], stage1: pathlib.Path | None, elapsed: float):
    """Write tests/golden/BENCHMARKS.md with metrics table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    py_ver = platform.python_version()
    os_name = platform.system()
    arch = platform.machine()

    # Get compiler version
    version = "unknown"
    vf = ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()

    # Get git commit
    commit = "unknown"
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, cwd=ROOT, timeout=5,
        )
        if r.returncode == 0:
            commit = r.stdout.decode().strip()
    except Exception:
        pass

    lines = []
    lines.append("# Mapanare Compiler Benchmarks")
    lines.append("")
    lines.append(f"Generated: {now}  ")
    lines.append(f"Version: {version} (`{commit}`)  ")
    lines.append(f"Platform: {os_name} {arch}, Python {py_ver}  ")
    lines.append(f"Total time: {elapsed:.1f}s  ")
    lines.append("")

    # Bootstrap table
    lines.append("## Bootstrap Compiler (Python)")
    lines.append("")
    lines.append("| Test | Source | IR Lines | IR KB | Fns | Time (ms) | Status |")
    lines.append("|------|-------:|---------:|------:|----:|----------:|--------|")

    total_src = 0
    total_ir = 0
    total_kb = 0
    total_fns = 0
    total_ms = 0.0
    passed = 0

    for r in results:
        m = r.bootstrap_metrics
        status = "PASS" if r.bootstrap_ok else "FAIL"
        kb = m.ir_bytes / 1024
        lines.append(
            f"| {r.name} | {r.source_lines} | {m.ir_lines} | {kb:.1f} | "
            f"{m.defines} | {m.time_ms:.0f} | {status} |"
        )
        total_src += r.source_lines
        total_ir += m.ir_lines
        total_kb += kb
        total_fns += m.defines
        total_ms += m.time_ms
        if r.bootstrap_ok:
            passed += 1

    lines.append(
        f"| **Total** | **{total_src}** | **{total_ir}** | **{total_kb:.1f}** | "
        f"**{total_fns}** | **{total_ms:.0f}** | **{passed}/{len(results)}** |"
    )
    lines.append("")

    # Stage 1 table (if available)
    if stage1 and any(r.stage1_ok is not None for r in results):
        lines.append("## Native Compiler (mnc-stage1)")
        lines.append("")
        lines.append("| Test | IR Lines | IR KB | Fns | Time (ms) | Match | Status |")
        lines.append("|------|---------:|------:|----:|----------:|-------|--------|")

        s1_passed = 0
        s1_matched = 0
        s1_total_ms = 0.0

        for r in results:
            if r.stage1_ok is None:
                continue
            m = r.stage1_metrics
            status = "PASS" if r.stage1_ok else "FAIL"
            match = "YES" if r.compare_ok else ("DIFF" if r.compare_ok is False else "-")
            kb = m.ir_bytes / 1024
            lines.append(
                f"| {r.name} | {m.ir_lines} | {kb:.1f} | "
                f"{m.defines} | {m.time_ms:.0f} | {match} | {status} |"
            )
            if r.stage1_ok:
                s1_passed += 1
            if r.compare_ok:
                s1_matched += 1
            s1_total_ms += m.time_ms

        lines.append(
            f"| **Total** | | | | **{s1_total_ms:.0f}** | "
            f"**{s1_matched}/{len(results)}** | **{s1_passed}/{len(results)}** |"
        )
        lines.append("")

    # Speed comparison (if both compilers ran)
    if stage1 and any(r.stage1_ok for r in results):
        lines.append("## Speed Comparison")
        lines.append("")
        lines.append("| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |")
        lines.append("|------|---------------:|------------:|--------:|")
        for r in results:
            if not r.stage1_ok:
                continue
            bms = r.bootstrap_metrics.time_ms
            sms = r.stage1_metrics.time_ms
            speedup = bms / sms if sms > 0 else 0
            lines.append(f"| {r.name} | {bms:.0f} | {sms:.0f} | {speedup:.1f}x |")
        lines.append("")

    BENCH_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(BENCH_FILE.relative_to(ROOT))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Golden test harness for Mapanare compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python scripts/test_native.py                        # bootstrap only
              python scripts/test_native.py --stage1 mnc-stage1    # compare
              python scripts/test_native.py --run                  # run via lli
              python scripts/test_native.py --bless                # update refs
              python scripts/test_native.py --bench                # write BENCHMARKS.md
              python scripts/test_native.py --filter fib -v        # one test
        """),
    )
    parser.add_argument("--stage1", type=pathlib.Path, help="Path to mnc-stage1")
    parser.add_argument("--run", action="store_true", help="Run IR through lli")
    parser.add_argument("--bless", action="store_true", help="Generate .ref.ll files")
    parser.add_argument("--bench", action="store_true", help="Write BENCHMARKS.md")
    parser.add_argument("--filter", help="Filter tests by name")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        C.off()

    mn_files = sorted(GOLDEN_DIR.glob("*.mn"))
    if args.filter:
        mn_files = [f for f in mn_files if args.filter in f.stem]

    if not mn_files:
        print(f"{C.RED}No test files in {GOLDEN_DIR}{C.RESET}")
        return 1

    mode = "bootstrap"
    if args.stage1:
        mode = "compare"
    if args.run:
        mode += "+run"
    if args.bench:
        mode += "+bench"

    print(f"{C.BOLD}Mapanare Golden Tests{C.RESET} ({len(mn_files)} tests, mode: {mode})")
    print()

    # Bless mode
    if args.bless:
        print("Generating reference files...")
        blessed = 0
        for mn_file in mn_files:
            ir, err = compile_bootstrap(mn_file)
            if err:
                print(f"  {C.RED}FAIL{C.RESET} {mn_file.stem}: {err}")
                continue
            mn_file.with_suffix(".ref.ll").write_text(ir, encoding="utf-8")
            fp = ir_fingerprint(ir)
            print(f"  {C.GREEN}OK{C.RESET}   {mn_file.stem} ({fp['defines']} fns, {fp['lines']}L)")
            blessed += 1
        print(f"\nBlessed {blessed}/{len(mn_files)} files.")
        return 0

    # Run tests
    results: list[TestResult] = []
    t0 = time.perf_counter()

    for mn_file in mn_files:
        r = run_test(mn_file, args.stage1, args.run)
        results.append(r)

        # Print result
        m = r.bootstrap_metrics
        parts = [r.status_str, f" {r.name}"]
        parts.append(f" {C.DIM}{r.source_lines}L->{m.ir_lines}L {m.time_ms:.0f}ms{C.RESET}")

        if r.bootstrap_ok:
            parts.append(f" {C.DIM}({m.defines} fns){C.RESET}")

        if r.stage1_ok is not None:
            sm = r.stage1_metrics
            if r.stage1_ok:
                parts.append(f" stg1:{C.GREEN}{sm.defines}fns {sm.time_ms:.0f}ms{C.RESET}")
            else:
                parts.append(f" stg1:{C.RED}FAIL{C.RESET}")

        if r.compare_ok is not None and not r.compare_ok:
            parts.append(f" {C.YELLOW}{r.compare_diff}{C.RESET}")

        if r.run_ok is not None:
            out = r.run_output.strip()[:30]
            if r.run_ok:
                parts.append(f" run:{C.GREEN}\"{out}\"{C.RESET}")
            else:
                parts.append(f" run:{C.RED}{r.run_err[:30]}{C.RESET}")

        print("".join(parts))

        if args.verbose and not r.passed:
            if r.bootstrap_err:
                print(f"    bootstrap: {r.bootstrap_err[:200]}")
            if r.stage1_err:
                print(f"    stage1: {r.stage1_err[:200]}")
            if r.compare_diff:
                print(f"    diff: {r.compare_diff}")

    elapsed = time.perf_counter() - t0
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print()
    if failed == 0:
        print(f"{C.GREEN}{C.BOLD}All {passed} tests passed{C.RESET} in {elapsed:.1f}s")
    else:
        print(f"{C.RED}{C.BOLD}{failed} failed{C.RESET}, {C.GREEN}{passed} passed{C.RESET} in {elapsed:.1f}s")

    # Write benchmark table
    if args.bench or True:  # Always write — it's cheap and useful
        bench_path = write_benchmarks(results, args.stage1, elapsed)
        print(f"{C.DIM}Benchmarks: {bench_path}{C.RESET}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
