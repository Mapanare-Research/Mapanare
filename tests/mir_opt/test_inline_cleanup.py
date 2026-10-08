"""Inlining eligibility must preserve cleanup, including through wrappers."""

import pytest

from mapanare.lower import lower
from mapanare.mir import BasicBlock, Call, Instruction, MIRFunction, Return, Value, mir_int
from mapanare.mir_opt import _inline_preserves_cleanup, _should_inline
from mapanare.parser import parse


@pytest.mark.parametrize(
    "source,expected",
    [
        ("fn target(n: Int) -> Int:\n    return n + 1\n", True),
        ("fn target(n: Float) -> Float:\n    return -n\n", True),
        ("fn target(b: Bool) -> Bool:\n    return !b\n", True),
        ("fn target(n: Int) -> Int:\n    return len(str(n))\n", False),
        ("fn target(n: Int) -> Int:\n    let xs = [n]\n    return xs[0]\n", False),
        ("fn target(s: String) -> Int:\n    return len(s)\n", False),
        ("fn target(n: Int) -> String:\n    return str(n)\n", False),
        ("fn target(s: String) -> String:\n    return s\n", False),
        ("fn target(xs: List<Int>) -> Int:\n    return xs[0]\n", False),
        ("fn target(s: String) -> Int:\n    return len(s[0])\n", False),
        ("fn target(n: Int) -> Int:\n    let f = || n\n    return f()\n", False),
        (
            "fn allocate(n: Int) -> Int:\n    return len(str(n))\n"
            "fn target(n: Int) -> Int:\n    return allocate(n)\n",
            True,
        ),
    ],
)
def test_cleanup_eligibility(source: str, expected: bool) -> None:
    module = lower(parse(source))
    fn = next(fn for fn in module.functions if fn.name == "target")
    assert _inline_preserves_cleanup(fn) is expected
    assert _should_inline(fn, 1) is expected


def test_unknown_instruction_fails_closed() -> None:
    fn = MIRFunction(
        name="future_instruction",
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry", instructions=[Instruction(), Return(val=Value("0", mir_int()))]
            )
        ],
    )
    assert not _should_inline(fn, 1)


def test_resource_callee_remains_in_scalar_wrapper() -> None:
    from mapanare.mir_opt import MIROptLevel, optimize_module

    module = lower(
        parse(
            "fn allocate(n: Int) -> Int:\n    return len(str(n))\n"
            "fn wrapper(n: Int) -> Int:\n    return allocate(n)\n"
            "fn main():\n    print(wrapper(42))\n"
        )
    )
    optimize_module(module, MIROptLevel.O2)
    main = next(fn for fn in module.functions if fn.name == "main")
    calls = [
        inst.fn_name for bb in main.blocks for inst in bb.instructions if isinstance(inst, Call)
    ]
    assert "wrapper" not in calls
    assert "allocate" in calls
