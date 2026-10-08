"""Direct map returns preserve the handle and release proven owned results."""

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
FACTORY = """
fn make_values() -> Map<String, Int>:
    let result: Map<String, Int> = #{"a": 1, "bb": 2, "ccc": 3}
    return result
"""
CASES = {
    "original": ((ROOT / "tests/native/fixtures/map_return_lifetime.mn").read_text(), "3\n"),
    "alias": (
        FACTORY.replace("return result", "let alias = result\n    return alias") + """
fn main():
    let values = make_values()
    let alias = values
    print(len(alias))
    print(len(values))
""",
        "3\n3\n",
    ),
    "forward-wrapper": (
        """
fn wrap() -> Map<String, Int>:
    return make_values()
fn main():
    let values = wrap()
    print(len(values))
""" + FACTORY,
        "3\n",
    ),
    "discarded": (FACTORY + "\nfn main():\n    make_values()\n    print(42)\n", "42\n"),
    "early-return": (
        """
fn choose(b: Bool) -> Map<String, Int>:
    let first = #{"a": 1, "bb": 2}
    let second = #{"ccc": 3}
    for key in first:
        if b: return first
    return second
fn score(b: Bool) -> Int:
    let values = choose(b)
    let mut total: Int = 0
    for key in values:
        total = total + len(key)
    return total
fn main():
    let mut total: Int = 0
    for i in 0..100:
        total = total + score(true) + score(false)
    print(total)
""",
        "600\n",
    ),
    "borrowed": (
        """
fn identity(values: Map<String, Int>) -> Map<String, Int>:
    let alias = values
    return alias
fn score(values: Map<String, Int>) -> Int:
    let alias = identity(values)
    return len(alias)
fn main():
    let values = #{"a": 1, "b": 2}
    let mut total: Int = 0
    for i in 0..100:
        total = total + score(values)
    print(total)
    print(len(values))
""",
        "200\n2\n",
    ),
    "repeated-calls": (
        FACTORY + """
fn score() -> Int:
    let first = make_values()
    let second = make_values()
    return len(first) + len(second)
fn main():
    let mut total: Int = 0
    for i in 0..100:
        total = total + score()
    print(total)
""",
        "600\n",
    ),
}


@pytest.fixture(scope="module")
def instrumented_core(tmp_path_factory: pytest.TempPathFactory) -> Path:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux/WSL and clang sanitizers")
    obj = tmp_path_factory.mktemp("map-return-runtime") / "core.o"
    run = subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-c",
            str(ROOT / "runtime/native/mapanare_core.c"),
            "-o",
            str(obj),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert run.returncode == 0, run.stderr
    return obj


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_map_return_lifetime(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    ir = tmp_path / "map.ll"
    ir.write_text(_compile_to_llvm_ir(source, "map.mn", opt_level=opt))
    exe = tmp_path / "map"
    linked = subprocess.run(
        [
            "clang",
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            str(ir),
            str(instrumented_core),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
