"""Proven read-only callees leave String cleanup with their callers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CASES = [
    (
        "loop",
        """
fn measure(text: String) -> Int:
    let mut total: Int = 0
    for i in 0..3:
        total = total + len(text)
    return total
""",
        "measure(text)",
        3,
    ),
    (
        "alias-branch",
        """
fn measure(text: String) -> Int:
    let mut alias: String = text
    if len(text) > 3:
        alias = text
        return len(alias)
    return 0
""",
        "measure(text)",
        1,
    ),
    (
        "two-arguments",
        """
fn measure(left: String, right: String) -> Int:
    return len(left) + len(right)
""",
        "measure(text, text)",
        2,
    ),
]


@pytest.mark.parametrize("name,callee,call,factor", CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("iterations", [100, 10000])
@pytest.mark.parametrize("forward", [False, True], ids=["defined-first", "forward-call"])
def test_borrowed_string_argument_is_leak_free(
    name: str,
    callee: str,
    call: str,
    factor: int,
    iterations: int,
    forward: bool,
    tmp_path: Path,
) -> None:
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not compiler.exists() or not runtime.exists():
        pytest.skip("requires Linux native compiler/runtime and LeakSanitizer")
    main = f"""
fn main():
    let mut total: Int = 0
    for i in 0..{iterations}:
        let text: String = "item-" + str(i)
        let alias: String = text
        total = total + {call}
        total = total + {call}
        total = total + len(alias)
    print(total)
"""
    source = tmp_path / f"{name}.mn"
    source.write_text(main + callee if forward else callee + main)
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(source)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert emitted.returncode == 0, emitted.stderr
    ir = source.with_suffix(".ll")
    ir.write_text(emitted.stdout)
    executable = tmp_path / name
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
    expected = sum(len(f"item-{i}") for i in range(iterations)) * (2 * factor + 1)
    assert run.stdout == f"{expected}\n"
