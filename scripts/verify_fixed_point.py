#!/usr/bin/env python3
"""Strict Linux/WSL self-host validation; build stage1 first.

Regenerates concatenated source and runtime, checks both compilers, and retains
isolated artifacts plus a manifest under build/fixed-point-* even on failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE_GOLDENS = (
    "01_hello",
    "02_arithmetic",
    "07_enum_match",
    "14_nested_struct",
    "26_generics",
    "29_generic_impl",
    "30_nested_generics",
    "31_generic_multi",
    "104_for_continue",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checked(command: list[str], output: Path, timeout: int = 300) -> None:
    """Reject nonzero exit even when a crashing compiler wrote valid output."""
    with output.open("wb") as stdout, Path(str(output) + ".stderr").open("wb") as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {command!r}; see {output}.stderr")


def validate_ir(path: Path) -> None:
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError(f"empty or missing LLVM IR: {path}")
    run_checked(["llvm-as", str(path), "-o", os.devnull], path.with_suffix(".validation.log"))


def require_fixed_point(stage2: Path, stage3: Path) -> None:
    if not stage2.read_bytes() or stage2.read_bytes() != stage3.read_bytes():
        raise RuntimeError(f"strict fixed point failed: {stage2} != {stage3}")


def check_goldens(compiler: Path, directory: Path, runtime: Path) -> dict[str, int]:
    directory.mkdir()
    sources = sorted((ROOT / "tests/golden").glob("*.mn"))
    if not sources:
        raise RuntimeError("golden corpus is empty")
    executed = 0
    for source in sources:
        ir = directory / (source.stem + ".ll")
        run_checked([str(compiler), "emit-llvm", str(source)], ir, timeout=60)
        validate_ir(ir)
        if source.stem in EXECUTABLE_GOLDENS:
            executable = directory / source.stem
            run_checked(
                [
                    "clang",
                    "-O2",
                    str(ir),
                    str(runtime),
                    "-lm",
                    "-lpthread",
                    "-ldl",
                    "-o",
                    str(executable),
                ],
                directory / (source.stem + ".link.log"),
            )
            output = directory / (source.stem + ".stdout")
            run_checked([str(executable)], output, timeout=30)
            expected = ROOT / "tests/integration/expected" / (source.stem + ".expected")
            if output.read_text().strip() != expected.read_text().strip():
                raise RuntimeError(f"wrong executable output: {source.stem} via {compiler}")
            executed += 1
    if executed != len(EXECUTABLE_GOLDENS):
        raise RuntimeError("one or more executable golden fixtures are missing")
    return {"llvm_valid": len(sources), "executed": executed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage1", type=Path, default=ROOT / "mapanare/self/mnc-stage1")
    parser.add_argument("--keep", action="store_true", help="artifacts are always retained")
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("requires Linux/WSL and clang/llvm-as")
    (ROOT / "build").mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="fixed-point-", dir=ROOT / "build"))
    print(f"Validation artifacts: {work}", flush=True)
    manifest: dict[str, object] = {"status": "running", "work_dir": str(work)}
    try:
        compiler = args.stage1.resolve()
        if not compiler.is_file():
            raise RuntimeError(f"build stage1 first: {compiler}")
        manifest["source_revision"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
        manifest["working_tree"] = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=ROOT,
            text=True,
        )
        manifest["stage1_sha256"] = sha256(compiler)
        manifest["clang"] = subprocess.check_output(["clang", "--version"], text=True).splitlines()[
            0
        ]
        source = work / "mnc_all.mn"
        run_checked([sys.executable, "scripts/concat_self.py", str(source)], work / "concat.log")
        manifest["source_sha256"] = sha256(source)
        run_checked(["make", "build-rt"], work / "runtime.log")
        runtime = ROOT / "runtime/native/libmapanare_rt.a"
        manifest["runtime_sha256"] = sha256(runtime)
        print("Checking stage1 goldens and outputs...", flush=True)
        manifest["stage1_goldens"] = check_goldens(compiler, work / "stage1-goldens", runtime)
        stage2 = work / "stage2.ll"
        print("Emitting and compiling stage2...", flush=True)
        run_checked([str(compiler), "emit-llvm", str(source)], stage2)
        validate_ir(stage2)
        stage2_object = work / "stage2.o"
        run_checked(
            ["clang", "-O2", "-c", str(stage2), "-o", str(stage2_object)], work / "compile.log", 1800
        )
        successor = work / "mnc-stage2"
        # The compiler exports void mn_main(), whereas the application wrapper
        # expects i32. The compiler wrapper also provisions a larger stack.
        run_checked(
            [
                "clang",
                "-O2",
                "mapanare/self/mnc_main.c",
                str(stage2_object),
                str(runtime),
                "-no-pie",
                "-rdynamic",
                "-lm",
                "-lpthread",
                "-ldl",
                "-o",
                str(successor),
            ],
            work / "link.log",
        )
        manifest["stage2_sha256"] = sha256(successor)
        print("Checking stage2 goldens and outputs...", flush=True)
        manifest["stage2_goldens"] = check_goldens(successor, work / "stage2-goldens", runtime)
        stage3 = work / "stage3.ll"
        print("Emitting stage3 and requiring exact equality...", flush=True)
        run_checked([str(successor), "emit-llvm", str(source)], stage3)
        validate_ir(stage3)
        require_fixed_point(stage2, stage3)
        manifest["stage2_ir_sha256"] = sha256(stage2)
        manifest["stage3_ir_sha256"] = sha256(stage3)
        manifest["status"] = "passed"
        print("PASS: both compilers pass goldens; stage2.ll == stage3.ll", flush=True)
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        print(f"FAIL: {error}", file=sys.stderr, flush=True)
        return 1
    finally:
        (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
