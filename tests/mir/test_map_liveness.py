"""The recycling proof must reject aliases that escape a loop iteration."""

import pytest

from mapanare.lower import lower
from mapanare.map_liveness import recyclable_map_results
from mapanare.map_ownership import owned_map_factories
from mapanare.mir import (
    BasicBlock,
    Branch,
    Call,
    Copy,
    Jump,
    MIRFunction,
    MIRType,
    Value,
    mir_bool,
    mir_int,
)
from mapanare.mir_opt import MIROptLevel, optimize_module
from mapanare.parser import parse
from mapanare.types import TypeInfo, TypeKind

FACTORY = "fn make() -> Map<Int, Int>:\n    return #{1: 2}\n"


@pytest.mark.parametrize(
    "body,expected",
    [
        ("        let m = make()\n        print(len(m))\n", True),
        ("        let m = make()\n        let alias = m\n        print(len(alias))\n", True),
        ("        let m = make()\n        capture(m)\n", False),
        ("        let m = make()\n        let captured = [m]\n        sink(captured)\n", False),
        ("        let m = make()\n        for key in m:\n            print(key)\n", True),
    ],
)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_recycling_eligibility(body: str, expected: bool, opt: MIROptLevel) -> None:
    module = lower(parse(FACTORY + "fn main():\n    for i in 0..10:\n" + body))
    optimize_module(module, opt)
    fn = next(fn for fn in module.functions if fn.name == "main")
    assert bool(recyclable_map_results(fn, owned_map_factories(module.functions))) is expected


def test_loop_carried_alias_is_live() -> None:
    module = lower(parse(FACTORY + """
fn main():
    let mut saved = make()
    for i in 0..10:
        let current = make()
        if i == 0: saved = current
        print(len(saved))
"""))
    fn = next(fn for fn in module.functions if fn.name == "main")
    assert not recyclable_map_results(fn, owned_map_factories(module.functions))


@pytest.mark.parametrize("skip_copy", [False, True])
def test_single_origin_branch_liveness(skip_copy: bool) -> None:
    # One allocation origin in both cases: only the branch that can skip
    # overwriting saved makes its previous map live across the next call.
    ty = MIRType(TypeInfo(kind=TypeKind.MAP))
    made, saved = Value("%made", ty), Value("%saved", ty)
    branch = Branch(cond=Value("%condition", mir_bool()), true_block="save", false_block="use")
    fn = MIRFunction(
        name="probe",
        blocks=[
            BasicBlock(
                label="header",
                instructions=[
                    Call(dest=made, fn_name="make"),
                    branch if skip_copy else Jump(target="save"),
                ],
            ),
            BasicBlock(label="save", instructions=[Copy(dest=saved, src=made), Jump(target="use")]),
            BasicBlock(
                label="use",
                instructions=[
                    Call(dest=Value("%length", mir_int()), fn_name="len", args=[saved]),
                    Jump(target="header"),
                ],
            ),
        ],
    )
    assert recyclable_map_results(fn, {"make"}) == (set() if skip_copy else {"%made"})
