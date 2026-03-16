#!/usr/bin/env python3
"""Golden test harness + benchmark system for the Mapanare compiler.

One command to answer: "does the compiler work, and how fast?"

Usage:
    python scripts/test_native.py                                    # Bootstrap only
    python scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # Compare with native
    python scripts/test_native.py --arch                             # Cross-arch object sizes
    python scripts/test_native.py --self-hosted                      # Benchmark full compiler
    python scripts/test_native.py --profile                          # perf stat (Linux)
    python scripts/test_native.py --bless                            # Update reference files

Golden files: tests/golden/*.mn
Benchmarks:   tests/golden/BENCHMARKS-{platform}.md
History:      tests/golden/HISTORY.jsonl
"""

from __future__ import annotations

import argparse
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from datetime import datetime, timezone

try:
    import resource as _resource
except ImportError:
    _resource = None  # type: ignore[assignment]

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
HISTORY_FILE = GOLDEN_DIR / "HISTORY.jsonl"
PLATFORM_TAG = "linux" if sys.platform == "linux" else "windows"
BENCH_PLATFORM_FILE = GOLDEN_DIR / f"BENCHMARKS-{PLATFORM_TAG}.md"
BENCH_FILE = GOLDEN_DIR / "BENCHMARKS.md"

ARCH_TRIPLES = {
    "x86_64": "x86_64-unknown-linux-gnu",
    "i686": "i686-unknown-linux-gnu",
    "aarch64": "aarch64-unknown-linux-gnu",
}

# Unicode sparkline chars (safe subset)
SPARK_CHARS = " _.-~*"


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
# Helpers
# ---------------------------------------------------------------------------


def _rss_mb() -> float:
    try:
        import psutil

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return 0.0


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo if hi != lo else 1.0
    n = len(SPARK_CHARS) - 1
    chars = []
    for v in values[-8:]:
        idx = int((v - lo) / span * n)
        chars.append(SPARK_CHARS[min(idx, n)])
    trend = ""
    if len(values) >= 2:
        d = values[-1] - values[-2]
        if d > 0:
            trend = " ^"
        elif d < 0:
            trend = " v"
    return "".join(chars) + trend


def _delta_str(current: float, previous: float) -> str:
    if previous == 0:
        return ""
    d = current - previous
    pct = d / previous * 100
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.0f} ({sign}{pct:.0f}%)"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class Metrics:
    def __init__(self):
        self.time_ms: float = 0.0
        self.peak_rss_mb: float = 0.0
        self.ir_lines: int = 0
        self.ir_bytes: int = 0
        self.defines: int = 0
        self.declares: int = 0
        self.source_lines: int = 0
        self.basic_blocks: int = 0
        self.phi_nodes: int = 0
        self.alloca_bytes: int = 0
        self.arch_obj_sizes: dict[str, int] = {}  # arch -> .o bytes
        self.arch_insn_counts: dict[str, int] = {}  # arch -> instruction count

    def to_dict(self) -> dict:
        return {
            "time_ms": round(self.time_ms),
            "ir_lines": self.ir_lines,
            "ir_bytes": self.ir_bytes,
            "defines": self.defines,
            "declares": self.declares,
            "basic_blocks": self.basic_blocks,
            "phi_nodes": self.phi_nodes,
            "alloca_bytes": self.alloca_bytes,
            "arch_obj_sizes": self.arch_obj_sizes,
            "arch_insn_counts": self.arch_insn_counts,
        }


def measure_compile(fn, *args):
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
    return len(
        [
            m
            for m in re.findall(r'^define\s+.*?@"?([^"(\s]+)', ir, re.MULTILINE)
            if not m.startswith("%lambda") and not m.startswith("lambda")
        ]
    )


def count_declares(ir: str) -> int:
    return len(re.findall(r"^declare\s", ir, re.MULTILINE))


def has_main(ir: str) -> bool:
    return bool(re.search(r'define\s.*@"?main"?', ir))


def extract_function_names(ir: str) -> list[str]:
    return re.findall(r'define\s+(?:internal\s+)?[^@]*@"?([^"(]+)"?', ir)


def ir_complexity(ir: str) -> dict:
    """Analyze IR structural complexity."""
    blocks = len(re.findall(r"^\w[\w.]*:", ir, re.MULTILINE))
    phis = ir.count(" phi ")
    # Sum alloca sizes: alloca {type} patterns
    alloca_bytes = 0
    for m in re.finditer(r"%\S+\s*=\s*alloca\s+(.+?)(?:\s*,|\s*$)", ir, re.MULTILINE):
        ty = m.group(1).strip()
        alloca_bytes += _estimate_type_size(ty)
    return {"basic_blocks": blocks, "phi_nodes": phis, "alloca_bytes": alloca_bytes}


def _estimate_type_size(ty: str) -> int:
    """Rough size estimate from LLVM type string."""
    if ty.startswith("i1"):
        return 1
    if ty.startswith("i8") and not ty.startswith("i8*"):
        return 1
    if ty.startswith("i32"):
        return 4
    if ty.startswith("i64"):
        return 8
    if ty == "double":
        return 8
    if ty == "float":
        return 4
    if ty.endswith("*"):
        return 8
    # Struct: count nested elements roughly
    if ty.startswith("{"):
        # Count commas + 1 for element count, assume 8 bytes each
        return (ty.count(",") + 1) * 8
    # Array: [N x type]
    arr = re.match(r"\[(\d+)\s*x\s*(.+)\]", ty)
    if arr:
        return int(arr.group(1)) * _estimate_type_size(arr.group(2).strip())
    return 8  # fallback


def ir_fingerprint(ir: str) -> dict:
    cx = ir_complexity(ir)
    return {
        "defines": count_defines(ir),
        "declares": count_declares(ir),
        "has_main": has_main(ir),
        "functions": sorted(extract_function_names(ir)),
        "lines": ir.count("\n"),
        "has_strings": "@.str" in ir or "private constant" in ir,
        **cx,
    }


# ---------------------------------------------------------------------------
# Cross-architecture compilation
# ---------------------------------------------------------------------------


def compile_arch(ir: str, test_name: str, triples: dict[str, str]) -> dict[str, dict]:
    """Compile IR for multiple architectures via llc. Returns {arch: {obj_bytes, insn_count}}."""
    llc = shutil.which("llc")
    if not llc:
        return {}

    results = {}
    with tempfile.TemporaryDirectory(prefix="mn_arch_") as tmpdir:
        ir_path = pathlib.Path(tmpdir) / f"{test_name}.ll"
        ir_path.write_text(ir, encoding="utf-8")

        for arch, triple in triples.items():
            obj_path = pathlib.Path(tmpdir) / f"{test_name}_{arch}.o"
            asm_path = pathlib.Path(tmpdir) / f"{test_name}_{arch}.s"

            # Object file
            try:
                r = subprocess.run(
                    [
                        llc,
                        "-mtriple",
                        triple,
                        "-filetype=obj",
                        "-O0",
                        "-o",
                        str(obj_path),
                        str(ir_path),
                    ],
                    capture_output=True,
                    timeout=30,
                )
                obj_bytes = obj_path.stat().st_size if r.returncode == 0 else 0
            except Exception:
                obj_bytes = 0

            # Assembly for instruction count
            insn_count = 0
            try:
                r = subprocess.run(
                    [
                        llc,
                        "-mtriple",
                        triple,
                        "-filetype=asm",
                        "-O0",
                        "-o",
                        str(asm_path),
                        str(ir_path),
                    ],
                    capture_output=True,
                    timeout=30,
                )
                if r.returncode == 0:
                    asm = asm_path.read_text(encoding="utf-8", errors="replace")
                    # Count lines that look like instructions (indented, not labels/directives)
                    for line in asm.splitlines():
                        stripped = line.strip()
                        if (
                            stripped
                            and not stripped.startswith(".")
                            and not stripped.startswith("#")
                            and not stripped.startswith("@")
                            and not stripped.endswith(":")
                            and "\t" in line
                            and not line.startswith("\t.")
                        ):
                            insn_count += 1
            except Exception:
                pass

            results[arch] = {"obj_bytes": obj_bytes, "insn_count": insn_count}

    return results


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
            capture_output=True,
            timeout=30,
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


def compile_self_hosted() -> tuple[Metrics, str]:
    """Benchmark compiling all self-hosted .mn files."""
    m = Metrics()
    self_dir = ROOT / "mapanare" / "self"
    main_mn = self_dir / "main.mn"
    if not main_mn.exists():
        return m, "main.mn not found"
    source = main_mn.read_text(encoding="utf-8")
    total_lines = sum(f.read_text(encoding="utf-8").count("\n") for f in self_dir.glob("*.mn"))
    m.source_lines = total_lines

    try:
        from mapanare.multi_module import compile_multi_module_mir

        t0 = time.perf_counter()
        ir = compile_multi_module_mir(
            root_source=source,
            root_file=str(main_mn),
            opt_level=2,
        )
        t1 = time.perf_counter()
        m.time_ms = (t1 - t0) * 1000
        m.ir_lines = ir.count("\n")
        m.ir_bytes = len(ir.encode())
        m.defines = count_defines(ir)
        m.declares = count_declares(ir)
        cx = ir_complexity(ir)
        m.basic_blocks = cx["basic_blocks"]
        m.alloca_bytes = cx["alloca_bytes"]
        return m, ""
    except Exception as e:
        return m, str(e)


def run_ir(ir: str, test_name: str) -> tuple[str, str]:
    lli = shutil.which("lli")
    if not lli:
        return "", "lli not found"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ll", prefix=f"mn_{test_name}_", delete=False, encoding="utf-8"
    ) as f:
        f.write(ir)
        ir_path = f.name
    try:
        result = subprocess.run(
            [lli, ir_path],
            capture_output=True,
            timeout=10,
        )
        stdout = result.stdout.decode(errors="replace")
        stderr = result.stderr.decode(errors="replace")
        if result.returncode != 0:
            return "", f"lli exit {result.returncode}: {stderr[:200]}"
        return stdout, ""
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    finally:
        pathlib.Path(ir_path).unlink(missing_ok=True)


def run_perf(mn_file: pathlib.Path) -> dict:
    """Run perf stat on bootstrap compilation (Linux only)."""
    if sys.platform != "linux" or not shutil.which("perf"):
        return {}
    script = (
        f"from mapanare.cli import _compile_to_llvm_ir; "
        f"_compile_to_llvm_ir(open('{mn_file}').read(), '{mn_file}')"
    )
    try:
        result = subprocess.run(
            [
                "perf",
                "stat",
                "-e",
                "instructions,cycles,cache-misses,branch-misses",
                sys.executable,
                "-c",
                script,
            ],
            capture_output=True,
            timeout=60,
        )
        stats = {}
        for line in result.stderr.decode().splitlines():
            line = line.strip()
            for key in ("instructions", "cycles", "cache-misses", "branch-misses"):
                if key in line:
                    num = line.split()[0].replace(",", "")
                    try:
                        stats[key] = int(num)
                    except ValueError:
                        pass
        return stats
    except Exception:
        return {}


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
        self.perf_stats: dict = {}

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
    do_arch: bool,
    do_profile: bool,
) -> TestResult:
    name = mn_file.stem
    r = TestResult(name)
    r.source_lines = mn_file.read_text(encoding="utf-8").count("\n")

    # Bootstrap
    (r.bootstrap_ir, r.bootstrap_err), r.bootstrap_metrics = measure_compile(
        compile_bootstrap,
        mn_file,
    )
    if r.bootstrap_err:
        return r

    fp = ir_fingerprint(r.bootstrap_ir)
    r.bootstrap_ok = fp["defines"] > 0
    m = r.bootstrap_metrics
    m.ir_lines = fp["lines"]
    m.ir_bytes = len(r.bootstrap_ir.encode())
    m.defines = fp["defines"]
    m.declares = fp["declares"]
    m.source_lines = r.source_lines
    m.basic_blocks = fp["basic_blocks"]
    m.phi_nodes = fp["phi_nodes"]
    m.alloca_bytes = fp["alloca_bytes"]

    if not r.bootstrap_ok:
        r.bootstrap_err = f"0 defines, {fp['lines']} lines"
        return r

    # Cross-architecture
    if do_arch:
        arch_results = compile_arch(r.bootstrap_ir, name, ARCH_TRIPLES)
        for arch, data in arch_results.items():
            m.arch_obj_sizes[arch] = data["obj_bytes"]
            m.arch_insn_counts[arch] = data["insn_count"]

    # Stage 1
    if stage1:
        (r.stage1_ir, r.stage1_err), r.stage1_metrics = measure_compile(
            compile_stage1,
            mn_file,
            stage1,
        )
        if r.stage1_err:
            r.stage1_ok = False
        else:
            sfp = ir_fingerprint(r.stage1_ir)
            r.stage1_ok = sfp["defines"] > 0
            sm = r.stage1_metrics
            sm.ir_lines = sfp["lines"]
            sm.ir_bytes = len(r.stage1_ir.encode())
            sm.defines = sfp["defines"]
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

    # Profile
    if do_profile:
        r.perf_stats = run_perf(mn_file)

    return r


# ---------------------------------------------------------------------------
# History (JSONL)
# ---------------------------------------------------------------------------


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    entries = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def append_history(results: list[TestResult], self_hosted: Metrics | None, env: dict):
    entry = {
        "timestamp": env["now"],
        "commit": env["commit"],
        "version": env["version"],
        "platform": env["tag"],
        "tests": {},
    }
    for r in results:
        entry["tests"][r.name] = r.bootstrap_metrics.to_dict()
    if self_hosted:
        entry["self_hosted"] = self_hosted.to_dict()
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def get_trends(test_name: str, metric: str, history: list[dict]) -> list[float]:
    """Get last N values of a metric for a test from history."""
    values = []
    for entry in history:
        if entry.get("platform") != PLATFORM_TAG:
            continue
        t = entry.get("tests", {}).get(test_name, {})
        v = t.get(metric)
        if v is not None:
            values.append(float(v))
    return values


# ---------------------------------------------------------------------------
# Benchmark output
# ---------------------------------------------------------------------------


def _get_env_info() -> dict:
    version = "unknown"
    vf = ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()
    commit = "unknown"
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            cwd=ROOT,
            timeout=5,
        )
        if r.returncode == 0:
            commit = r.stdout.decode().strip()
    except Exception:
        pass
    return {
        "now": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "version": version,
        "commit": commit,
        "os": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "tag": PLATFORM_TAG,
    }


def _build_platform_md(
    results: list[TestResult],
    stage1: pathlib.Path | None,
    self_hosted: Metrics | None,
    self_hosted_err: str,
    elapsed: float,
    env: dict,
    history: list[dict],
) -> str:
    tag = env["tag"].capitalize()
    L = [
        f"# Mapanare Benchmarks - {tag}",
        "",
        f"Generated: {env['now']}  ",
        f"Version: {env['version']} (`{env['commit']}`)  ",
        f"Platform: {env['os']} {env['arch']}, Python {env['python']}  ",
        f"Total time: {elapsed:.1f}s  ",
        "",
    ]

    # --- Self-hosted compiler benchmark ---
    if self_hosted and not self_hosted_err:
        lps = self_hosted.source_lines / (self_hosted.time_ms / 1000) if self_hosted.time_ms else 0
        L += [
            "## Self-Hosted Compiler (full pipeline)",
            "",
            "| Metric | Value |",
            "|--------|------:|",
            f"| Source lines | {self_hosted.source_lines} |",
            f"| IR lines | {self_hosted.ir_lines} |",
            f"| IR size | {self_hosted.ir_bytes / 1024:.0f} KB |",
            f"| Functions | {self_hosted.defines} |",
            f"| Basic blocks | {self_hosted.basic_blocks} |",
            f"| Compile time | {self_hosted.time_ms:.0f} ms |",
            f"| Throughput | {lps:.0f} lines/s |",
            "",
        ]

    # --- Bootstrap table ---
    L += [
        "## Bootstrap Compiler (Python)",
        "",
        "| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |",
        "|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|",
    ]

    ts = ts_ir = ts_fns = ts_bbs = ts_stk = tp = 0
    ts_kb = ts_ms = 0.0
    for r in results:
        m = r.bootstrap_metrics
        status = "PASS" if r.bootstrap_ok else "FAIL"
        kb = m.ir_bytes / 1024
        trend_vals = get_trends(r.name, "time_ms", history)
        trend = _sparkline(trend_vals)
        L.append(
            f"| {r.name} | {r.source_lines} | {m.ir_lines} | {kb:.1f} | "
            f"{m.defines} | {m.basic_blocks} | {m.alloca_bytes} | "
            f"{m.time_ms:.0f} | `{trend}` | {status} |"
        )
        ts += r.source_lines
        ts_ir += m.ir_lines
        ts_kb += kb
        ts_fns += m.defines
        ts_bbs += m.basic_blocks
        ts_stk += m.alloca_bytes
        ts_ms += m.time_ms
        if r.bootstrap_ok:
            tp += 1

    L.append(
        f"| **Total** | **{ts}** | **{ts_ir}** | **{ts_kb:.1f}** | "
        f"**{ts_fns}** | **{ts_bbs}** | **{ts_stk}** | "
        f"**{ts_ms:.0f}** | | **{tp}/{len(results)}** |"
    )
    L.append("")

    # --- Cross-architecture table ---
    has_arch = any(r.bootstrap_metrics.arch_obj_sizes for r in results)
    if has_arch:
        archs = sorted({a for r in results for a in r.bootstrap_metrics.arch_obj_sizes})
        hdr = "| Test |" + "|".join(f" {a} .o |" for a in archs)
        hdr += "|".join(f" {a} insns |" for a in archs) + "|"
        sep = "|------|" + "|".join("------:|" for _ in archs)
        sep += "|".join("--------:|" for _ in archs) + "|"
        L += ["## Cross-Architecture", "", hdr, sep]
        for r in results:
            m = r.bootstrap_metrics
            row = f"| {r.name} |"
            for a in archs:
                sz = m.arch_obj_sizes.get(a, 0)
                row += f" {sz} |" if sz else " - |"
            for a in archs:
                ic = m.arch_insn_counts.get(a, 0)
                row += f" {ic} |" if ic else " - |"
            L.append(row)
        L.append("")

    # --- Stage 1 table ---
    if stage1 and any(r.stage1_ok is not None for r in results):
        L += [
            "## Native Compiler (mnc-stage1)",
            "",
            "| Test | IR | KB | Fns | ms | Match | Status |",
            "|------|---:|---:|----:|---:|-------|--------|",
        ]
        s1p = s1m = 0
        s1ms = 0.0
        for r in results:
            if r.stage1_ok is None:
                continue
            sm = r.stage1_metrics
            st = "PASS" if r.stage1_ok else "FAIL"
            mt = "YES" if r.compare_ok else ("DIFF" if r.compare_ok is False else "-")
            kb = sm.ir_bytes / 1024
            L.append(
                f"| {r.name} | {sm.ir_lines} | {kb:.1f} | "
                f"{sm.defines} | {sm.time_ms:.0f} | {mt} | {st} |"
            )
            if r.stage1_ok:
                s1p += 1
            if r.compare_ok:
                s1m += 1
            s1ms += sm.time_ms
        L.append(
            f"| **Total** | | | | **{s1ms:.0f}** | "
            f"**{s1m}/{len(results)}** | **{s1p}/{len(results)}** |"
        )
        L.append("")

        # Speed comparison
        if any(r.stage1_ok for r in results):
            L += [
                "## Speed Comparison",
                "",
                "| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |",
                "|------|---------------:|------------:|--------:|",
            ]
            for r in results:
                if not r.stage1_ok:
                    continue
                bms = r.bootstrap_metrics.time_ms
                sms = r.stage1_metrics.time_ms
                sp = bms / sms if sms > 0 else 0
                L.append(f"| {r.name} | {bms:.0f} | {sms:.0f} | {sp:.1f}x |")
            L.append("")

    # --- Perf stats ---
    if any(r.perf_stats for r in results):
        L += [
            "## Hardware Counters (perf stat)",
            "",
            "| Test | Instructions | Cycles | IPC | Cache Miss | Branch Miss |",
            "|------|------------:|-------:|----:|-----------:|------------:|",
        ]
        for r in results:
            p = r.perf_stats
            if not p:
                continue
            insns = p.get("instructions", 0)
            cyc = p.get("cycles", 0)
            ipc = insns / cyc if cyc else 0
            cm = p.get("cache-misses", 0)
            bm = p.get("branch-misses", 0)
            L.append(f"| {r.name} | {insns:,} | {cyc:,} | {ipc:.2f} | {cm:,} | {bm:,} |")
        L.append("")

    return "\n".join(L) + "\n"


def _merge_benchmarks():
    win_file = GOLDEN_DIR / "BENCHMARKS-windows.md"
    lin_file = GOLDEN_DIR / "BENCHMARKS-linux.md"
    if not win_file.exists() and not lin_file.exists():
        return
    L = [
        "# Mapanare Compiler Benchmarks",
        "",
        "Cross-platform results. Auto-generated by `python scripts/test_native.py`.",
        "Commit to track regressions.",
        "",
        "---",
        "",
    ]
    for label, path in [("Windows", win_file), ("Linux", lin_file)]:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"^# .+\n", "", content)
        L += [f"## {label}", "", content.strip(), "", "---", ""]
    BENCH_FILE.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_benchmarks(
    results: list[TestResult],
    stage1: pathlib.Path | None,
    self_hosted: Metrics | None,
    self_hosted_err: str,
    elapsed: float,
):
    env = _get_env_info()
    history = load_history()

    md = _build_platform_md(results, stage1, self_hosted, self_hosted_err, elapsed, env, history)
    BENCH_PLATFORM_FILE.write_text(md, encoding="utf-8")
    _merge_benchmarks()

    # Append history
    append_history(results, self_hosted, env)

    return str(BENCH_PLATFORM_FILE.relative_to(ROOT))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Golden test harness + benchmarks for Mapanare",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python scripts/test_native.py                        # bootstrap only
              python scripts/test_native.py --arch                 # + cross-arch .o sizes
              python scripts/test_native.py --self-hosted          # + full compiler bench
              python scripts/test_native.py --stage1 mnc-stage1    # compare with native
              python scripts/test_native.py --profile              # + perf stat (Linux)
              python scripts/test_native.py --run                  # run IR via lli
              python scripts/test_native.py --bless                # update .ref.ll files
              python scripts/test_native.py --filter fib -v        # one test, verbose
        """),
    )
    parser.add_argument("--stage1", type=pathlib.Path, help="Path to mnc-stage1")
    parser.add_argument("--run", action="store_true", help="Run IR through lli")
    parser.add_argument("--arch", action="store_true", help="Cross-arch object sizes via llc")
    parser.add_argument("--self-hosted", action="store_true", help="Benchmark full compiler")
    parser.add_argument("--profile", action="store_true", help="perf stat (Linux only)")
    parser.add_argument("--bless", action="store_true", help="Generate .ref.ll files")
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

    flags = []
    if args.stage1:
        flags.append("compare")
    if args.arch:
        flags.append("arch")
    if args.self_hosted:
        flags.append("self-hosted")
    if args.run:
        flags.append("run")
    if args.profile:
        flags.append("profile")
    mode = "+".join(flags) if flags else "bootstrap"

    print(f"{C.BOLD}Mapanare Golden Tests{C.RESET} ({len(mn_files)} tests, mode: {mode})")
    print()

    # Bless
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

    # Self-hosted benchmark
    self_hosted = None
    self_hosted_err = ""
    if args.self_hosted:
        print(f"{C.DIM}Compiling self-hosted compiler (7 modules)...{C.RESET}")
        self_hosted, self_hosted_err = compile_self_hosted()
        if self_hosted_err:
            print(f"  {C.RED}FAIL{C.RESET}: {self_hosted_err[:100]}")
        else:
            lps = (
                self_hosted.source_lines / (self_hosted.time_ms / 1000)
                if self_hosted.time_ms
                else 0
            )
            sl = self_hosted.source_lines
            il = self_hosted.ir_lines
            df = self_hosted.defines
            tm = self_hosted.time_ms
            print(
                f"  {C.GREEN}OK{C.RESET} {sl}L -> "
                f"{il}L IR, {df} fns, "
                f"{tm:.0f}ms ({lps:.0f} L/s)"
            )
        print()

    # Run tests
    results: list[TestResult] = []
    t0 = time.perf_counter()

    for mn_file in mn_files:
        r = run_test(mn_file, args.stage1, args.run, args.arch, args.profile)
        results.append(r)

        m = r.bootstrap_metrics
        parts = [r.status_str, f" {r.name}"]
        parts.append(
            f" {C.DIM}{r.source_lines}L->{m.ir_lines}L "
            f"{m.basic_blocks}bb {m.alloca_bytes}stk "
            f"{m.time_ms:.0f}ms{C.RESET}"
        )

        if r.bootstrap_ok:
            parts.append(f" {C.DIM}({m.defines} fns){C.RESET}")

        if m.arch_obj_sizes:
            sizes = " ".join(f"{a}:{s}" for a, s in sorted(m.arch_obj_sizes.items()))
            parts.append(f" {C.DIM}[{sizes}]{C.RESET}")

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
                parts.append(f' run:{C.GREEN}"{out}"{C.RESET}')
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
        print(
            f"{C.RED}{C.BOLD}{failed} failed{C.RESET}, "
            f"{C.GREEN}{passed} passed{C.RESET} in {elapsed:.1f}s"
        )

    # Write benchmarks + history
    bench_path = write_benchmarks(results, args.stage1, self_hosted, self_hosted_err, elapsed)
    print(f"{C.DIM}Benchmarks: {bench_path}{C.RESET}")
    print(f"{C.DIM}History: {HISTORY_FILE.relative_to(ROOT)}{C.RESET}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
