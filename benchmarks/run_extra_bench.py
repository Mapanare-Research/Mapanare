"""Measure Mapanare O2 for matmul_naive + agent_fanout (not in cross_language harness).

Uses same compile pipeline + timing approach as run_benchmarks.py so results
are directly comparable. Writes to benchmarks/v4.110.0-extra.json.
"""

from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Harness is called from the repo root.
ROOT = Path("/mnt/c/Users/Juan/Documents/GitHub/Mapanare")
RUNTIME_LIB = ROOT / "runtime" / "native" / "libmapanare_rt.a"
TIME_BIN = "/usr/bin/time"

BENCH = [
    ("matmul_naive", ROOT / "benchmarks" / "optimizer" / "matmul_naive.mn", "checksum"),
    ("agent_fanout", ROOT / "benchmarks" / "optimizer" / "agent_fanout.mn", "total"),
]


def find_tool(name):
    for c in [name, f"{name}-18", f"{name}-17"]:
        p = shutil.which(c)
        if p:
            return p
    return None


def parse_gnu_time(stderr):
    peak = 0.0
    for raw in stderr.splitlines():
        s = raw.strip()
        if s.startswith("Maximum resident set size"):
            peak = float(s.split(":")[-1].strip())
    return peak


def run_binary(binary):
    t0 = time.perf_counter()
    r = subprocess.run(
        [TIME_BIN, "-v", "--", str(binary)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    t1 = time.perf_counter()
    if r.returncode != 0:
        return None
    return {
        "wall_s": t1 - t0,
        "mem_kb": parse_gnu_time(r.stderr),
        "output": r.stdout.strip(),
    }


def compile_mn(mn_path, outbin):
    tools = {t: find_tool(t) for t in ["llvm-as", "opt", "llc", "clang"]}
    if not all(tools.values()):
        return f"missing tools: {[k for k, v in tools.items() if not v]}"
    name = mn_path.stem
    td = outbin.parent
    ll = td / f"{name}.ll"
    bc = td / f"{name}.bc"
    opt_bc = td / f"{name}.opt.bc"
    obj = td / f"{name}.o"

    emit = [sys.executable, "-m", "mapanare", "emit-llvm", str(mn_path), "-o", str(ll)]
    llc = [tools["llc"], "-filetype=obj", "-relocation-model=pic", str(opt_bc), "-o", str(obj)]
    link = [
        tools["clang"],
        str(obj),
        str(RUNTIME_LIB),
        "-lm",
        "-lpthread",
        "-ldl",
        "-o",
        str(outbin),
    ]
    steps = [
        (emit, "emit"),
        ([tools["llvm-as"], str(ll), "-o", str(bc)], "llvm-as"),
        ([tools["opt"], "-O2", str(bc), "-o", str(opt_bc)], "opt"),
        (llc, "llc"),
        (link, "link"),
    ]
    for cmd, stage in steps:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=ROOT)
        if r.returncode != 0:
            return f"compile_fail @ {stage}: {r.stderr[:200]}"
    return None


def measure(name, mn_path, expected, n_runs=10):
    result = {
        "benchmark": name,
        "language": "Mapanare O2",
        "lines_of_code": 0,
        "binary_size_bytes": 0,
        "runs": [],
        "wall_median_ms": 0.0,
        "mem_peak_kb": 0.0,
        "correct": False,
        "error": "",
    }
    try:
        result["lines_of_code"] = sum(
            1
            for line in mn_path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("//")
        )
    except Exception:
        pass
    with tempfile.TemporaryDirectory() as td:
        binary = Path(td) / name
        err = compile_mn(mn_path, binary)
        if err:
            result["error"] = err
            return result
        result["binary_size_bytes"] = binary.stat().st_size
        # warmup
        run_binary(binary)
        walls = []
        mems = []
        outs = []
        for _ in range(n_runs):
            r = run_binary(binary)
            if not r:
                continue
            walls.append(r["wall_s"])
            mems.append(r["mem_kb"])
            outs.append(r["output"])
        if walls:
            walls_sorted = sorted(walls)
            if len(walls_sorted) >= 4:
                walls_sorted = walls_sorted[1:-1]
            result["wall_median_ms"] = statistics.median(walls_sorted) * 1000.0
            result["mem_peak_kb"] = max(mems) if mems else 0.0
            result["correct"] = all(expected in o for o in outs)
            result["output_sample"] = outs[0] if outs else ""
    return result


def main():
    results = []
    for name, path, expected in BENCH:
        print(f"[{name}]")
        r = measure(name, path, expected, n_runs=10)
        results.append(r)
        if r["error"]:
            print(f"  ERR: {r['error']}")
        else:
            line = f"  wall={r['wall_median_ms']:.3f}ms"
            line += f"  mem={r['mem_peak_kb']:.0f}KB"
            line += f"  bin={r['binary_size_bytes']}B"
            line += f"  correct={r['correct']}"
            line += f"  output={r.get('output_sample', '')[:40]}"
            print(line)
    outpath = ROOT / "benchmarks" / "v4.110.0-extra.json"
    outpath.write_text(
        json.dumps(
            {
                "version": "4.110.0",
                "date": time.strftime("%Y-%m-%d"),
                "note": "matmul_naive + agent_fanout (needed for v4.82.0 cumulative delta)",
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nSaved to {outpath}")


if __name__ == "__main__":
    main()
