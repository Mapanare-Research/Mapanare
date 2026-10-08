"""A scalar-returning mutator can capture an argument in an existing list."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir

ROOT = Path(__file__).resolve().parents[2]
SOURCE = """
fn capture(values: List<String>, text: String) -> Int:
    values[0] = text
    return len(values)
fn make_values(n: Int) -> List<String>:
    let values: List<String> = ["old"]
    let text: String = "captured-" + str(n)
    capture(values, text)
    return values
fn main():
    let values: List<String> = make_values(42)
    print(values[0])
    print(len(values[0]))
"""


@pytest.mark.parametrize("backend", ["bootstrap", "native"])
def test_mutator_keeps_captured_argument_alive(backend: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    source = tmp_path / "capture.mn"
    source.write_text(SOURCE)
    if backend == "bootstrap":
        llvm = _compile_to_llvm_ir(SOURCE, str(source))
    else:
        if not compiler.exists():
            pytest.skip("requires native compiler")
        result = subprocess.run(
            [str(compiler), "emit-llvm", str(source)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        llvm = result.stdout
    ir = source.with_suffix(".ll")
    ir.write_text(llvm)
    binary = tmp_path / "capture"
    linked = subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address",
            "-no-pie",
            str(ir),
            str(runtime),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(binary)],
        capture_output=True,
        text=True,
        timeout=30,
        # This is an invalid-access guard. Legacy lists still lack recursive
        # element cleanup; those known retention gaps have separate probes.
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == "captured-42\n11\n"
