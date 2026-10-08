"""Borrowing requires a body proof, not just a scalar return or purity."""

from __future__ import annotations

import pytest

from mapanare.borrow import function_borrows_arguments
from mapanare.lower import lower
from mapanare.mir import BasicBlock, Call, IndexSet, MIRFunction, MIRParam, MIRType, Return, Value
from mapanare.parser import parse
from mapanare.types import TypeInfo, TypeKind


@pytest.mark.parametrize(
    "source,expected",
    [
        ("fn target(s: String) -> Int:\n    return len(s)\n", True),
        ("fn target(v: List<Int>) -> Int:\n    return v[0] + len(v)\n", True),
        ("fn target(v: List<String>) -> Int:\n    return len(v[0])\n", True),
        ("fn target(v: List<List<Int>>) -> Int:\n    return v[0][0]\n", True),
        (
            "fn target(v: List<Int>) -> Int:\n    let mut n: Int = 0\n"
            "    for i in 0..3:\n        n = n + v[0]\n    return n\n",
            True,
        ),
        ("fn target(s: String) -> String:\n    return s\n", False),
        ("fn target(v: List<Int>) -> List<Int>:\n    return v\n", False),
        (
            "fn target(v: List<String>, s: String) -> Int:\n" "    v.push(s)\n    return len(v)\n",
            False,
        ),
        (
            "fn target(v: List<String>, s: String) -> Int:\n" "    v[0] = s\n    return len(v)\n",
            False,
        ),
        ("fn target(s: String) -> Int:\n    return len(s + s)\n", False),
        ("fn target(s: String) -> Int:\n    return len(s[0])\n", False),
        (
            "fn other(s: String) -> Int:\n    return len(s)\n"
            "fn target(s: String) -> Int:\n    return other(s)\n",
            False,
        ),
        ("fn target(s: String) -> Int:\n    let values = [s]\n    return len(values)\n", False),
        (
            "fn target(s: String) -> Int:\n" "    let run = || len(s)\n    return run()\n",
            False,
        ),
        (
            "fn target(v: Map<String, String>) -> Int:\n    return len(v)\n",
            False,
        ),
    ],
)
def test_source_borrow_contract(source: str, expected: bool) -> None:
    module = lower(parse(source))
    target = next(fn for fn in module.functions if fn.name == "target")
    assert function_borrows_arguments(target) is expected


@pytest.mark.parametrize("failure", ["extern", "async", "unreachable-mutation", "unknown-call"])
def test_fail_closed_borrow_contract(failure: str) -> None:
    integer = MIRType(TypeInfo(kind=TypeKind.INT))
    values = MIRType(TypeInfo(kind=TypeKind.LIST, args=[integer.type_info]))
    fn = MIRFunction(
        name="target",
        params=[MIRParam("items", values)],
        return_type=integer,
        blocks=[BasicBlock("entry", [Return(val=Value("zero", integer))])],
    )
    if failure == "extern":
        fn.blocks = []
    elif failure == "async":
        fn.is_async = True
    elif failure == "unknown-call":
        fn.blocks[0].instructions.insert(0, Call(fn_name="unknown", args=[Value("items", values)]))
    else:
        fn.blocks.append(BasicBlock("unreachable", [IndexSet(obj=Value("items", values))]))
    assert not function_borrows_arguments(fn)


def test_recursive_type_bound_fails_closed() -> None:
    cycle = TypeInfo(kind=TypeKind.LIST)
    cycle.args.append(cycle)
    fn = MIRFunction(params=[MIRParam("items", MIRType(cycle))], blocks=[BasicBlock("entry")])
    assert not function_borrows_arguments(fn)
