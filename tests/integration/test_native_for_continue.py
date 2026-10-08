"""Loop control must make progress and target the innermost native loop."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "simple": ((ROOT / "tests/native/fixtures/range_continue_progress.mn").read_text(), "8\n"),
    "golden": (
        (ROOT / "tests/golden/104_for_continue.mn").read_text(),
        (ROOT / "tests/integration/expected/104_for_continue.expected").read_text(),
    ),
    "all-continue": (
        """
fn main():
    let mut visits: Int = 0
    for i in 0..5:
        visits = visits + 1
        continue
    print(visits)
""",
        "5\n",
    ),
    "empty-ranges": (
        """
fn main():
    let mut total: Int = 42
    for i in 2..2:
        total = 0
        continue
    for i in 5..3:
        total = 0
        continue
    print(total)
""",
        "42\n",
    ),
    "for-in-while": (
        """
fn main():
    let mut total: Int = 0
    let mut i: Int = 0
    while i < 3:
        i = i + 1
        for j in 0..3:
            if j == 1: continue
            total = total + j
        if i == 2: continue
        total = total + 10
    print(total)
""",
        "26\n",
    ),
    "while-in-for": (
        """
fn main():
    let mut total: Int = 0
    for i in 0..3:
        let mut j: Int = 0
        while j < 3:
            j = j + 1
            if j == 2: continue
            total = total + i * 10 + j
        if i == 1: continue
        total = total + 100
    print(total)
""",
        "272\n",
    ),
    "map-break": (
        """
fn main():
    let values: Map<String, Int> = #{"a": 1, "b": 2, "c": 3}
    let mut total: Int = 0
    for key in values:
        total = total + 1
        break
    print(total)
""",
        "1\n",
    ),
    "map-in-for": (
        """
fn main():
    let values: Map<String, Int> = #{"a": 1, "b": 2, "c": 3}
    let mut total: Int = 0
    for i in 0..3:
        for key in values:
            if key == "b": continue
            total = total + 1
        if i == 1: continue
        total = total + 10
    print(total)
""",
        "26\n",
    ),
    "for-in-map": (
        """
fn main():
    let values: Map<String, Int> = #{"a": 1, "b": 2, "c": 3}
    let mut total: Int = 0
    for key in values:
        for i in 0..3:
            if i == 1: continue
            total = total + 1
        if key == "b": continue
        total = total + 10
    print(total)
""",
        "26\n",
    ),
}


@pytest.mark.parametrize(
    "case,backend",
    [(case, backend) for backend in ("bootstrap", "native") for case in CASES],
)
@pytest.mark.parametrize("clang_level", ["-O0", "-O2"])
def test_for_control_flow(case: str, backend: str, clang_level: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    if backend == "native" and not compiler.exists():
        pytest.skip("requires native compiler")
    source, expected = CASES[case]
    path = tmp_path / "loop.mn"
    path.write_text(source)
    if backend == "native":
        emitted = subprocess.run(
            [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
        )
        assert emitted.returncode == 0, emitted.stderr
        llvm = emitted.stdout
    else:
        llvm = _compile_to_llvm_ir(source, str(path))
    ir = path.with_suffix(".ll")
    ir.write_text(llvm)
    executable = tmp_path / "loop"
    linked = subprocess.run(
        [
            clang,
            clang_level,
            "-Wno-override-module",
            str(ir),
            str(runtime),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    # IR validity alone misses nonprogress and jumps into an outer loop.
    run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=3)
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
