"""Retained String views keep their original map alive across replacement."""

from pathlib import Path

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run

pytest_plugins = ["tests.integration.test_map_return_ownership"]

TEXT_FACTORY = """
fn make(n: Int) -> Map<Int, String>:
    return #{1: "value-" + str(n)}
"""
KEY_FACTORY = """
fn make(n: Int) -> Map<String, Int>:
    return #{"key-" + str(n): n}
"""
CASES = {
    "saved-value": (
        TEXT_FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        if i == 0: saved = values[1]
        assert(saved == "value-0")
    print(saved)
""",
        "value-0\n",
    ),
    "saved-key": (
        KEY_FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        for key in values:
            if i == 0: saved = key
        assert(saved == "key-0")
    print(saved)
""",
        "key-0\n",
    ),
    "copy-snapshot": (
        TEXT_FACTORY + """
fn main():
    let mut saved = ""
    let mut previous = ""
    for i in 0..100:
        let values = make(i)
        previous = saved
        saved = values[1]
        saved = saved
    print(previous)
    print(saved)
""",
        "value-98\nvalue-99\n",
    ),
    "clear-view": (
        TEXT_FACTORY + """
fn main():
    let mut saved = ""
    for i in 0..100:
        let values = make(i)
        saved = values[1]
        saved = ""
    print(len(saved))
""",
        "0\n",
    ),
    "replace-during-cursor": (
        KEY_FACTORY + """
fn main():
    let mut values = make(0)
    let mut saved = ""
    for key in values:
        values = make(100)
        saved = key
    print(saved)
    print(values["key-100"])
""",
        "key-0\n100\n",
    ),
    "early-scalar-return": (
        TEXT_FACTORY + """
fn score(n: Int) -> Int:
    let mut saved = ""
    let mut i = 0
    while i < 100:
        let values = make(i)
        if i == 0: saved = values[1]
        if i == n: return len(saved)
        i = i + 1
    return len(saved)
fn main():
    let mut total = 0
    for i in 0..100:
        total = total + score(i)
    print(total)
""",
        "700\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_retained_map_view(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)
