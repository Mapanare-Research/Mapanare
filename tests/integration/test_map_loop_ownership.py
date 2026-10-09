"""Recycling a map result requires every alias of its previous value to be dead."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_return_ownership import FACTORY

pytest_plugins = ["tests.integration.test_map_return_ownership"]

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "original": (
        (ROOT / "tests/native/fixtures/map_return_loop_lifetime.mn").read_text(),
        "3000\n",
    ),
    "alias": (
        FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..1000:
        let values = make_values()
        let alias = values
        total = total + len(alias)
    print(total)
""",
        "3000\n",
    ),
    "conditional": (
        FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        if i % 2 == 0:
            let values = make_values()
            total = total + len(values)
    print(total)
""",
        "150\n",
    ),
    "nested": (
        FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..10:
        for j in 0..20:
            let first = make_values()
            let second = make_values()
            total = total + len(first) + len(second)
    print(total)
""",
        "1200\n",
    ),
    "break-continue": (
        FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        let values = make_values()
        if i == 20: break
        if i % 2 == 1: continue
        total = total + len(values)
    print(total)
""",
        "30\n",
    ),
    "early-return": (
        FACTORY + """
fn score(stop: Int) -> Int:
    let mut i: Int = 0
    while i < 100:
        let values = make_values()
        if i == stop: return len(values)
        i = i + 1
    return 0
fn main():
    let mut total: Int = 0
    for i in 0..100:
        total = total + score(i)
    print(total + score(-1))
""",
        "300\n",
    ),
    "skipped": (
        FACTORY + """
fn score(run: Bool) -> Int:
    let mut total: Int = 0
    if run:
        for i in 0..100:
            let values = make_values()
            total = total + len(values)
    return total
fn main():
    print(score(false))
    print(score(true))
""",
        "0\n300\n",
    ),
    "discarded": (
        FACTORY + """
fn main():
    for i in 0..1000:
        make_values()
    print(42)
""",
        "42\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_loop_map_results(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)


def _run(
    source: str, expected: str, opt: MIROptLevel, core: Path, tmp: Path, *, leaks: bool
) -> None:
    ir = tmp / "loop.ll"
    llvm = _compile_to_llvm_ir(source, "loop.mn", opt_level=opt)
    ir.write_text(llvm)
    assert ("map_owner" in llvm) is leaks
    exe = tmp / "loop"
    linked = subprocess.run(
        [
            "clang",
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            str(ir),
            str(core),
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
        timeout=15,
        env={**os.environ, "ASAN_OPTIONS": f"detect_leaks={int(leaks)}:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected


@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_retained_alias_is_not_recycled(
    opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source = FACTORY + """
fn main():
    let mut saved: Map<String, Int> = #{"initial": 0}
    for i in 0..100:
        let values = make_values()
        if i == 0: saved = values
        print(len(saved))
    print(len(saved))
"""
    # This group cannot recycle a sole owner, but explicit retained references
    # now keep the saved map alive and release every obsolete result.
    _run(source, "3\n" * 101, opt, instrumented_core, tmp_path, leaks=True)
