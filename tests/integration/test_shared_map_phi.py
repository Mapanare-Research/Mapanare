"""Consumed map merges retain only the selected control-flow edge."""

from pathlib import Path

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run

pytest_plugins = ["tests.integration.test_map_return_ownership"]

MAKE = "fn make(n: Int) -> Map<Int, Int>:\n    return #{1: n}\n"
CASES = {
    "factory-arms": (
        MAKE + """
fn main():
    let mut saved = make(-1)
    let mut total = 0
    for i in 0..100:
        let selected: Map<Int, Int> = match i % 2 {
            0 => make(i),
            _ => make(i + 100)
        }
        saved = selected
        total = total + saved[1]
    print(total)
""",
        "9950\n",
    ),
    "existing-aliases": (
        MAKE + """
fn main():
    let mut saved = make(-1)
    let mut total = 0
    for i in 0..100:
        let left = make(i)
        let right = make(i + 100)
        let selected: Map<Int, Int> = match i % 2 {
            0 => left,
            _ => right
        }
        if i % 10 == 0: saved = selected
        total = total + saved[1]
    print(total)
""",
        "4500\n",
    ),
    "returned-merge": (
        MAKE + """
fn choose(n: Int) -> Map<Int, Int>:
    let mut saved = make(-1)
    for i in 0..n:
        let selected: Map<Int, Int> = match i % 2 {
            0 => make(i),
            _ => make(i + 100)
        }
        saved = selected
    return saved
fn main():
    let mut total = 0
    for i in 0..100:
        let result = choose(100)
        total = total + result[1]
    print(total)
""",
        "19900\n",
    ),
    "three-arms": (
        MAKE + """
fn main():
    let mut total = 0
    for i in 0..99:
        let selected: Map<Int, Int> = match i % 3 {
            0 => make(1),
            1 => make(2),
            _ => make(3)
        }
        total = total + selected[1]
    print(total)
""",
        "198\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_shared_map_phi(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)
