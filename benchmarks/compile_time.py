"""Repeatable native compiler latency measurements with optional regression gates.

Times IR emission, a development build, a release build, and compile-and-run.
Every command must succeed. Use the same source, machine and toolchain when
comparing --baseline files; program runtime is included only in the run case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def measure(command: list[str], runs: int) -> dict:
    samples = []
    output = None
    for iteration in range(runs + 1):
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=True)
        elapsed = (time.perf_counter() - start) * 1000
        if output is not None and result.stdout != output:
            raise RuntimeError(f"Output changed between runs: {command}")
        output = result.stdout
        if iteration:
            samples.append(elapsed)
    return {"median_ms": statistics.median(samples), "samples_ms": samples}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mnc", type=Path, default=ROOT / "mapanare/self/mnc-stage1")
    parser.add_argument("--source", type=Path, default=ROOT / "tests/golden/01_hello.mn")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--max-regression", type=float, default=0.10)
    parser.add_argument("--max-ms", type=float, help="absolute latency limit for every case")
    parser.add_argument(
        "--include-uncached", action="store_true", help="also measure --no-cache builds"
    )
    args = parser.parse_args()
    if args.runs < 1 or args.max_regression < 0:
        parser.error("runs must be positive and max-regression must be nonnegative")
    mnc, source = str(args.mnc.resolve()), str(args.source.resolve())
    with tempfile.TemporaryDirectory(prefix="mnc-bench-") as tmp:
        output = str(Path(tmp) / "program")
        commands = {
            "emit": [mnc, "emit-llvm", source, "-o", str(Path(tmp) / "program.ll")],
            "build": [mnc, "build", source, "-o", output],
            "release": [mnc, "build", source, "--release", "-o", output],
            "run": [mnc, "run", source],
        }
        # Same compiler, same flags: these cases isolate the object-cache benefit.
        if args.include_uncached:
            commands["build_cold"] = [mnc, "build", source, "--no-cache", "-o", output]
            commands["release_cold"] = [
                mnc,
                "build",
                source,
                "--release",
                "--no-cache",
                "-o",
                output,
            ]
        results = {name: measure(command, args.runs) for name, command in commands.items()}
    report = {
        "platform": platform.platform(),
        "compiler": mnc,
        "source": source,
        "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "compiler_sha256": hashlib.sha256(Path(mnc).read_bytes()).hexdigest(),
        "runs": args.runs,
        "results": results,
    }
    baseline = json.loads(args.baseline.read_text()) if args.baseline else None
    if baseline and (
        baseline["platform"] != report["platform"]
        or baseline["source"] != source
        or baseline.get("source_sha256", report["source_sha256"]) != report["source_sha256"]
    ):
        parser.error("baseline must use the same platform and source")
    failed = False
    for name, result in results.items():
        median = result["median_ms"]
        print(f"{name:8s} {median:10.3f} ms")
        if args.max_ms is not None and median > args.max_ms:
            failed = True
        if baseline and name in baseline["results"]:
            previous = baseline["results"][name]["median_ms"]
            print(f"         change: {(median / previous - 1) * 100:+.1f}%")
            if median > previous * (1 + args.max_regression):
                failed = True
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    if failed:
        raise SystemExit("compile-time regression gate failed")


if __name__ == "__main__":
    main()
