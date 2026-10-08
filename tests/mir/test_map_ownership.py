"""Borrowed and uncertain map origins must never become caller-owned."""

import pytest

from mapanare.lower import lower
from mapanare.map_ownership import owned_map_factories
from mapanare.mir import Instruction
from mapanare.parser import parse


@pytest.mark.parametrize(
    "source,expected",
    [
        ("fn f() -> Map<Int, Int>:\n    return #{1: 2}\n", {"f"}),
        ("fn f(m: Map<Int, Int>) -> Map<Int, Int>:\n    return m\n", set()),
        (
            "fn f(m: Map<Int, Int>, b: Bool) -> Map<Int, Int>:\n"
            "    if b: return m\n    return #{1: 2}\n",
            set(),
        ),
        (
            "fn f() -> Map<Int, Int>:\n    return g()\n"
            "fn g() -> Map<Int, Int>:\n    return #{1: 2}\n",
            {"f", "g"},
        ),
        (
            "fn f() -> Map<Int, Int>:\n    return g()\n"
            "fn g() -> Map<Int, Int>:\n    return f()\n",
            set(),
        ),
        ("fn f() -> Map<Int, Int>:\n    return unknown()\n", set()),
        ("fn f() -> Map<Int, List<Int>>:\n    return #{1: [2]}\n", set()),
        (
            "fn f(m: Map<Int, Int>, b: Bool) -> Map<Int, Int>:\n"
            "    let mut result = #{1: 2}\n    if b: result = m\n    return result\n",
            set(),
        ),
        (
            "fn f() -> Map<Int, Int>:\n    let result = #{1: 2}\n"
            "    capture(result)\n    return result\n",
            set(),
        ),
        (
            "fn f() -> Map<Int, Int>:\n    let result = #{1: 2}\n"
            "    let captured = [result]\n    return result\n",
            set(),
        ),
        (
            "fn f() -> Map<Int, Int>:\n    let result = #{1: 2}\n"
            "    let captured = #{3: result}\n    return result\n",
            set(),
        ),
    ],
)
def test_factory_proof(source: str, expected: set[str]) -> None:
    assert owned_map_factories(lower(parse(source)).functions) == expected


def test_future_instruction_fails_closed() -> None:
    module = lower(parse("fn f() -> Map<Int, Int>:\n    return #{1: 2}\n"))
    module.functions[0].blocks[0].instructions.insert(0, Instruction())
    assert owned_map_factories(module.functions) == set()


def test_long_alias_chain_fails_closed() -> None:
    source = "fn f() -> Map<Int, Int>:\n    let m0 = #{1: 2}\n"
    source += "".join(f"    let m{i} = m{i - 1}\n" for i in range(1, 100))
    source += "    return m99\n"
    assert owned_map_factories(lower(parse(source)).functions) == set()
