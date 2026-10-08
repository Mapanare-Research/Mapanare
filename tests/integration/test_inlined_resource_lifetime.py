"""Inlining must not widen allocation lifetimes into a caller's loop."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("backend", ["O2", "O3", "native"])
@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "scalar-wrapper"])
@pytest.mark.parametrize("case", ["string", "list", "combined"])
def test_loop_allocations_keep_function_cleanup(
    backend: str, wrapped: bool, case: str, tmp_path: Path
) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    if backend == "native" and not compiler.exists():
        pytest.skip("requires native compiler")
    source = (ROOT / "tests/native/fixtures/inlined_resource_lifetime.mn").read_text()
    if case != "combined":
        body = (
            "    let text: String = str(n)\n    return len(text)\n"
            if case == "string"
            else "    let values: List<Int> = [n, 1]\n    return values[0]\n"
        )
        source = (
            "fn score(n: Int) -> Int:\n" + body + "\nfn main():" + source.split("fn main():")[1]
        )
    if wrapped:
        source = source.replace("total + score(i)", "total + wrapper(i)")
        # A forward-defined scalar wrapper can inline, but its allocating
        # callee must keep a call boundary even across optimizer fixpoints.
        source += "\nfn wrapper(n: Int) -> Int:\n    return score(n)\n"
    path = tmp_path / "lifetime.mn"
    path.write_text(source)
    ir = path.with_suffix(".ll")
    if backend == "native":
        emitted = subprocess.run(
            [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
        )
        assert emitted.returncode == 0, emitted.stderr
        llvm = emitted.stdout
    else:
        llvm = _compile_to_llvm_ir(source, str(path), opt_level=MIROptLevel[backend])
    ir.write_text(llvm)
    # Ensure this test exercises the required call boundary, even when the
    # allocating function happens to exceed the backend's inlining budget.
    assert "call i64 @score(" in llvm
    executable = tmp_path / "probe"
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
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    expected = {"string": 2890, "list": 499500, "combined": 1514280}[case]
    assert run.stdout == f"{expected}\n"


@pytest.mark.parametrize("backend", ["O2", "O3", "native"])
def test_scalar_inline_keeps_caller_allocation_in_loop(backend: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if backend == "native" and not compiler.exists():
        pytest.skip("requires native compiler")
    source = """
fn increment(n: Int) -> Int:
    return n + 1
fn main():
    let mut total: Int = 0
    for i in 0..1000:
        let n: Int = increment(i)
        let text: String = str(n)
        total = total + len(text)
    print(total)
"""
    ir = tmp_path / "caller.ll"
    path = ir.with_suffix(".mn")
    path.write_text(source)
    if backend == "native":
        emitted = subprocess.run(
            [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
        )
        assert emitted.returncode == 0, emitted.stderr
        ir.write_text(emitted.stdout)
    else:
        ir.write_text(_compile_to_llvm_ir(source, str(path), opt_level=MIROptLevel[backend]))
    executable = tmp_path / "caller"
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
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == "2893\n"


def test_native_scalar_arithmetic_still_inlines(tmp_path: Path) -> None:
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if sys.platform != "linux" or not compiler.exists():
        pytest.skip("requires Linux/WSL and native compiler")
    path = tmp_path / "scalar.mn"
    path.write_text(
        "fn increment(n: Int) -> Int:\n    return n + 1\n" "fn main():\n    print(increment(41))\n"
    )
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
    )
    assert emitted.returncode == 0, emitted.stderr
    assert "call i64 @increment(" not in emitted.stdout
    assert "_inl" in emitted.stdout
