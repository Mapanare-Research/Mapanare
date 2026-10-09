"""Map merge ownership requires complete, typed control-flow inputs."""

import pytest

from mapanare.map_shared import shared_map_aliases
from mapanare.mir import (
    BasicBlock,
    Branch,
    Call,
    Jump,
    MIRFunction,
    MIRParam,
    MIRType,
    Phi,
    Return,
    Value,
    mir_bool,
    mir_int,
)
from mapanare.types import TypeInfo, TypeKind


def _merge() -> tuple[MIRFunction, Phi]:
    ty = MIRType(TypeInfo(kind=TypeKind.MAP))
    a, b, result = (Value(name, ty) for name in ("%a", "%b", "%result"))
    phi = Phi(dest=result, incoming=[("entry", a), ("right", b)])
    fn = MIRFunction(
        name="merge",
        return_type=ty,
        params=[MIRParam(name="%flag", ty=mir_bool())],
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Call(dest=a, fn_name="make"),
                    Branch(
                        cond=Value("%flag", mir_bool()), true_block="merge", false_block="right"
                    ),
                ],
            ),
            BasicBlock(
                label="right", instructions=[Call(dest=b, fn_name="make"), Jump(target="merge")]
            ),
            BasicBlock(label="merge", instructions=[phi, Return(val=result)]),
        ],
    )
    return fn, phi


def test_consumed_phi_joins_all_owners_on_critical_edge() -> None:
    fn, _ = _merge()
    assert shared_map_aliases(fn, {"make"}, set()) == {"%a", "%b", "%result"}


@pytest.mark.parametrize(
    "invalid", ["missing", "duplicate", "unknown", "scalar", "late", "borrowed"]
)
def test_incomplete_phi_groups_are_rejected(invalid: str) -> None:
    fn, phi = _merge()
    if invalid == "missing":
        phi.incoming.pop()
    elif invalid == "duplicate":
        phi.incoming.append(phi.incoming[0])
    elif invalid == "unknown":
        phi.incoming[0] = ("absent", phi.incoming[0][1])
    elif invalid == "scalar":
        phi.incoming[0] = ("entry", Value("%a", mir_int()))
    elif invalid == "late":
        fn.blocks[-1].instructions.insert(
            0, Call(dest=Value("%n", mir_int()), fn_name="len", args=[phi.incoming[0][1]])
        )
    else:
        fn.params.append(MIRParam(name="%a", ty=phi.dest.ty))
    owners = shared_map_aliases(fn, {"make"}, set())
    assert not owners & {"%a", "%result"}
    if invalid == "missing":
        # The omitted, unused allocation forms a separate valid local group.
        assert owners == {"%b"}


def test_match_factories_are_owned_but_borrowed_returns_are_not() -> None:
    from mapanare.lower import lower
    from mapanare.map_ownership import owned_map_factories
    from mapanare.parser import parse

    module = lower(parse("""
fn choose(n: Int) -> Map<Int, Int>:
    let result: Map<Int, Int> = match n {
        0 => #{1: 2},
        _ => #{1: 3}
    }
    return result
fn borrowed(n: Int, input: Map<Int, Int>) -> Map<Int, Int>:
    let result: Map<Int, Int> = match n {
        0 => input,
        _ => #{1: 3}
    }
    return result
"""))
    assert owned_map_factories(module.functions) == {"choose"}
