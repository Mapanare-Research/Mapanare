"""A returned retained map transfers one reference after releasing local aliases."""

from pathlib import Path

import pytest

from mapanare.mir_opt import MIROptLevel
from tests.integration.test_map_loop_ownership import _run

pytest_plugins = ["tests.integration.test_map_return_ownership"]

MAKE = "fn make(n: Int) -> Map<Int, Int>:\n    return #{1: n}\n"
CASES = {
    "retained-first": (
        MAKE + """
fn choose(n: Int) -> Map<Int, Int>:
    let mut saved = make(-1)
    for i in 0..n:
        let current = make(i)
        if i == 0: saved = current
    let alias = saved
    return alias
fn main():
    let mut total = 0
    for i in 0..100:
        let result = choose(100)
        total = total + result[1] + len(result)
    print(total)
""",
        "100\n",
    ),
    "skipped-loop": (
        MAKE + """
fn choose(n: Int) -> Map<Int, Int>:
    let mut saved = make(5)
    for i in 0..n:
        saved = make(i)
    return saved
fn main():
    let result = choose(0)
    print(result[1])
""",
        "5\n",
    ),
    "early-return": (
        MAKE + """
fn choose(n: Int) -> Map<Int, Int>:
    let mut saved = make(-1)
    let mut i = 0
    while i < 100:
        let current = make(i)
        saved = current
        let alias = saved
        if i == n: return alias
        i = i + 1
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
    "multiple-groups": (
        MAKE + """
fn choose(left: Bool) -> Map<Int, Int>:
    let mut first = make(1)
    let mut second = make(2)
    for i in 0..100:
        first = make(i)
        second = make(i + 100)
    let a = first
    let b = second
    if left: return a
    return b
fn main():
    let a = choose(true)
    let b = choose(false)
    print(a[1])
    print(b[1])
""",
        "99\n199\n",
    ),
    "forward-wrapper": (
        MAKE + """
fn choose() -> Map<Int, Int>:
    let mut saved = make(-1)
    for i in 0..100:
        saved = make(i)
    return saved
fn wrap() -> Map<Int, Int>:
    let original = choose()
    let alias = original
    return alias
fn main():
    let result = wrap()
    print(result[1])
""",
        "99\n",
    ),
    "heap-keys": (
        """
fn make(n: Int) -> Map<String, Int>:
    return #{"key-" + str(n): n}
fn choose() -> Map<String, Int>:
    let mut saved = make(-1)
    for i in 0..100:
        let current = make(i)
        if i == 0: saved = current
    return saved
fn main():
    let result = choose()
    print(result["key-0"])
""",
        "0\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_shared_map_return(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = CASES[case]
    _run(source, expected, opt, instrumented_core, tmp_path, leaks=True)
