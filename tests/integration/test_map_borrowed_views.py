"""Parent map lifetimes include cursors and borrowed String keys/values."""

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run
from tests.integration.test_map_return_ownership import FACTORY

pytest_plugins = ["tests.integration.test_map_return_ownership"]

KEY_FACTORY = """
fn make(n: Int) -> Map<String, Int>:
    let key: String = "key-" + str(n)
    return #{key: n}
"""
TEXT_FACTORY = """
fn make(n: Int) -> Map<Int, String>:
    let text: String = "value-" + str(n)
    return #{1: text}
"""
NUMBER_FACTORY = """
fn make(n: Int) -> Map<Int, Int>:
    return #{1: n}
"""
CASES = {
    "heap-keys": (
        KEY_FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        let values = make(i)
        for key in values:
            let alias = key
            total = total + len(alias)
    print(total)
""",
        "590\n",
    ),
    "scalar-lookup": (
        NUMBER_FACTORY + """
fn main():
    let mut total: Int = 0
    let mut last: Int = 0
    for i in 0..100:
        let values = make(i)
        last = values[1]
        total = total + last
    print(total)
    print(last)
""",
        "4950\n99\n",
    ),
    "heap-values": (
        TEXT_FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        let values = make(i)
        let text = values[1]
        total = total + len(text)
    print(total)
""",
        "790\n",
    ),
    "print-values": (
        TEXT_FACTORY + """
fn main():
    for i in 0..3:
        let values = make(i)
        print(values[1])
""",
        "value-0\nvalue-1\nvalue-2\n",
    ),
    "nested-iterators": (
        KEY_FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..10:
        let values = make(i)
        for first in values:
            for second in values:
                total = total + len(first) + len(second)
    print(total)
""",
        "100\n",
    ),
    "continue": (
        FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        let values = make_values()
        for key in values:
            if key == "bb": continue
            total = total + len(key)
    print(total)
""",
        "400\n",
    ),
    "break": (
        KEY_FACTORY + """
fn main():
    let mut total: Int = 0
    for i in 0..100:
        let values = make(i)
        for key in values:
            total = total + len(key)
            break
    print(total)
""",
        "590\n",
    ),
    "early-return": (
        KEY_FACTORY + """
fn score(stop: Int) -> Int:
    let mut i: Int = 0
    while i < 100:
        let values = make(i)
        for key in values:
            if i == stop: return len(key)
        i = i + 1
    return 0
fn main():
    let mut total: Int = 0
    for i in 0..100:
        total = total + score(i)
    print(total)
""",
        "590\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_borrowed_map_views(case, opt, instrumented_core, tmp_path):
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)


@pytest.mark.parametrize("kind", ["key", "value"])
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_retained_view_prevents_recycling(kind, opt, instrumented_core, tmp_path):
    body = (
        "        for key in values:\n            if i == 0: saved = key\n"
        if kind == "key"
        else "        if i == 0: saved = values[1]\n"
    )
    source = (KEY_FACTORY if kind == "key" else TEXT_FACTORY) + """
fn main():
    let mut saved: String = ""
    for i in 0..100:
        let values = make(i)
""" + body + "        print(saved)\n    print(saved)\n"
    expected = ("key-0\n" if kind == "key" else "value-0\n") * 101
    # The fallback still retains maps; verify it never reclaims a live view.
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=False)
