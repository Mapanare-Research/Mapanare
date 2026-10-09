"""Closed map aliases may survive replacement without leaks or dangling handles."""

from pathlib import Path

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run

pytest_plugins = ["tests.integration.test_map_return_ownership"]

FACTORY = "fn make(n: Int) -> Map<Int, Int>:\n    return #{1: n}\n"
CASES = {
    "retain-first": (
        FACTORY + """
fn main():
    let mut saved = make(-1)
    for i in 0..100:
        let current = make(i)
        if i == 0: saved = current
        assert(saved[1] == 0)
    print(saved[1])
""",
        "0\n",
    ),
    "rolling": (
        FACTORY + """
fn main():
    let mut saved = make(-1)
    let mut total = 0
    for i in 0..100:
        let current = make(i)
        if i % 10 == 0: saved = current
        total = total + saved[1]
    print(total)
""",
        "4500\n",
    ),
    "rotating-aliases": (
        FACTORY + """
fn main():
    let mut left = make(1)
    let mut right = make(2)
    let mut total = 0
    for i in 0..100:
        let current = make(i)
        let temp = left
        left = right
        right = current
        total = total + temp[1]
    print(left[1])
    print(right[1])
    print(total)
""",
        "98\n99\n4756\n",
    ),
    "self-assignment": (
        FACTORY + """
fn main():
    let mut saved = make(-1)
    for i in 0..100:
        saved = make(i)
        saved = saved
    print(saved[1])
""",
        "99\n",
    ),
    "literal-replacement": (
        """
fn main():
    let mut saved = #{1: -1}
    let mut total = 0
    for i in 0..100:
        let current = #{1: i}
        if i % 10 == 0: saved = current
        total = total + saved[1]
    print(total)
""",
        "4500\n",
    ),
    "heap-keys": (
        """
fn make(n: Int) -> Map<String, Int>:
    let key = "key-" + str(n)
    return #{key: n}
fn main():
    let mut saved = #{"initial": -1}
    for i in 0..100:
        let current = make(i)
        if i == 0: saved = current
        assert(saved["key-0"] == 0)
    print(saved["key-0"])
""",
        "0\n",
    ),
    "branch-factories": (
        FACTORY + """
fn make_b(n: Int) -> Map<Int, Int>:
    return #{1: n + 1000}
fn main():
    let mut saved = make(-1)
    let mut total = 0
    for i in 0..100:
        if i % 2 == 0:
            saved = make(i)
        else:
            saved = make_b(i)
        total = total + saved[1]
    print(total)
""",
        "54950\n",
    ),
    "early-return": (
        FACTORY + """
fn score(stop: Int) -> Int:
    let mut saved = make(-1)
    let mut i = 0
    while i < 100:
        saved = make(i)
        if i == stop: return saved[1]
        i = i + 1
    return 0
fn main():
    let mut total = 0
    for i in 0..100:
        total = total + score(i)
    print(total)
""",
        "4950\n",
    ),
    "skipped-loop": (
        FACTORY + """
fn main():
    let mut saved = make(5)
    for i in 0..0:
        saved = make(i)
    print(saved[1])
""",
        "5\n",
    ),
    "nested-loops": (
        FACTORY + """
fn main():
    let mut saved = make(-1)
    for i in 0..10:
        for j in 0..10:
            let current = make(i * 10 + j)
            if j == 0: saved = current
    print(saved[1])
""",
        "90\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_retained_map_ownership(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)
