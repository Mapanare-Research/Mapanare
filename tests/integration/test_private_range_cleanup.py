"""Private range iterators are released on normal and early function exits."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel

pytest_plugins = ["tests.integration.test_map_return_ownership"]

CASES = {
    "scalar-return": (
        """
fn score(n: Int) -> Int:
    for i in 0..10:
        if i == n: return i
    return -1
fn main():
    let mut total = 0
    for i in 0..10:
        total = total + score(i)
    print(total)
""",
        "45\n",
    ),
    "inclusive-return": (
        """
fn score(n: Int) -> Int:
    for i in 0..=9:
        if i == n: return i
    return -1
fn main():
    let mut total = 0
    for i in 0..10:
        total = total + score(i)
    print(total)
""",
        "45\n",
    ),
    "nested-return": (
        """
fn score(n: Int) -> Int:
    for i in 0..10:
        for j in 0..10:
            if i * 10 + j == n: return n
    return -1
fn main():
    let mut total = 0
    for i in 0..100:
        total = total + score(i)
    print(total)
""",
        "4950\n",
    ),
    "map-return": (
        """
fn make(n: Int) -> Map<Int, Int>:
    return #{1: n}
fn choose(n: Int) -> Map<Int, Int>:
    let mut saved = make(-1)
    for i in 0..100:
        let current = make(i)
        saved = current
        let alias = saved
        if i == n: return alias
    return saved
fn main():
    let mut total = 0
    for i in 0..100:
        let result = choose(i)
        total = total + result[1]
    print(total)
""",
        "4950\n",
    ),
    "retained-view-return": (
        """
fn make(n: Int) -> Map<Int, String>:
    return #{1: "value-" + str(n)}
fn score(n: Int) -> Int:
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        if i == 0: saved = values[1]
        if i == n: return len(saved)
    return len(saved)
fn main():
    let mut total = 0
    for i in 0..100:
        total = total + score(i)
    print(total)
""",
        "700\n",
    ),
    "normal-break-skipped": (
        """
fn score(early: Bool) -> Int:
    if early: return 7
    let mut total = 0
    for i in 0..0: total = total + i
    for i in 0..100:
        if i % 2 == 0: continue
        total = total + i
        if i == 5: break
    return total
fn main():
    print(score(true) + score(false))
""",
        "16\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_private_range_cleanup(case, opt, instrumented_core: Path, tmp_path: Path):
    source, expected = CASES[case]
    ir = tmp_path / "range.ll"
    ir.write_text(_compile_to_llvm_ir(source, "range.mn", opt_level=opt))
    exe = tmp_path / "range"
    link = subprocess.run(
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
    assert link.returncode == 0, link.stderr
    run = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
