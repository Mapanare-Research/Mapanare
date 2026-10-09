"""A consumed String merge carries its selected borrowed map parent."""

from pathlib import Path

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run

pytest_plugins = ["tests.integration.test_map_return_ownership"]

FACTORY = """
fn make(n: Int) -> Map<Int, String>:
    return #{1: "left-" + str(n), 2: "right-" + str(n)}
"""
CASES = {
    "selected-views": (
        FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        let selected: String = match i % 2 {
            0 => values[1],
            _ => values[2]
        }
        if i % 10 == 0: saved = selected
    print(saved)
""",
        "left-90\n",
    ),
    "literal-alternative": (
        FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        let selected: String = match i % 2 {
            0 => values[1],
            _ => "literal"
        }
        saved = selected
    print(saved)
""",
        "literal\n",
    ),
    "nested-merges": (
        FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        let first: String = match i % 2 { 0 => values[1], _ => values[2] }
        let second: String = match i % 3 { 0 => first, _ => "fallback" }
        saved = second
    print(saved)
""",
        "right-99\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_retained_view_phi(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)
