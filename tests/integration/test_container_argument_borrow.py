"""Read-only calls retain caller cleanup for String and list arguments."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("string", "", "", "return len(text)", "len(text)", 1, 0),
    (
        "list-length",
        ", values: List<Int>",
        "let values: List<Int> = [n, 1]",
        "return len(text) + len(values)",
        "len(values)",
        1,
        2,
    ),
    (
        "list-index-alias",
        ", values: List<Int>",
        "let values: List<Int> = [n, 1]",
        "let alias: List<Int> = values\n    if len(alias) > 0:\n"
        "        return len(text) + alias[0]\n    return 0",
        "values[0]",
        1,
        -1,
    ),
    (
        "string-element-loop",
        ", values: List<String>",
        'let values: List<String> = ["left", "right"]',
        "let mut total: Int = 0\n    for i in 0..3:\n"
        "        let alias: String = values[0]\n"
        "        total = total + len(text) + len(alias)\n    return total",
        "len(values[0])",
        3,
        4,
    ),
]


@pytest.mark.parametrize("backend", ["bootstrap", "native"])
@pytest.mark.parametrize("forward", [False, True], ids=["defined-first", "forward-call"])
@pytest.mark.parametrize(
    "name,params,setup,body,after,factor,extra", CASES, ids=[c[0] for c in CASES]
)
def test_read_only_arguments_are_leak_free(
    backend: str,
    forward: bool,
    name: str,
    params: str,
    setup: str,
    body: str,
    after: str,
    factor: int,
    extra: int,
    tmp_path: Path,
) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    if backend == "native" and not compiler.exists():
        pytest.skip("requires native compiler")
    callee = f"fn measure(text: String{params}) -> Int:\n    {body}\n"
    args = "text, values" if params else "text"
    caller = f"""
fn score(n: Int) -> Int:
    if n < 0: return 0
    let text: String = "item-" + str(n)
    {setup}
    let first: Int = measure({args})
    let second: Int = measure({args})
    return first + second + {after}
fn main():
    let mut total: Int = 0
    for i in 0..1000:
        total = total + score(i)
    print(total)
"""
    source = caller + callee if forward else callee + caller
    path = tmp_path / f"{name}.mn"
    path.write_text(source)
    if backend == "bootstrap":
        llvm = _compile_to_llvm_ir(source, str(path))
    else:
        emitted = subprocess.run(
            [str(compiler), "emit-llvm", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert emitted.returncode == 0, emitted.stderr
        llvm = emitted.stdout
    ir = path.with_suffix(".ll")
    ir.write_text(llvm)
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
    expected = 0
    for n in range(1000):
        addition = n if extra == -1 else extra
        tail = len(f"item-{n}") if not params else addition
        expected += 2 * factor * (len(f"item-{n}") + addition) + tail
    assert run.stdout == f"{expected}\n"
