"""Reference-count eligibility is limited to complete, closed map groups."""

import pytest

from mapanare.lower import lower
from mapanare.map_liveness import recyclable_map_results
from mapanare.map_ownership import owned_map_factories
from mapanare.map_shared import shared_map_aliases
from mapanare.mir import BasicBlock, Call, MIRFunction, MIRType, Phi, Return, Value
from mapanare.mir_opt import MIROptLevel, optimize_module
from mapanare.parser import parse
from mapanare.types import TypeInfo, TypeKind

FACTORY = "fn make(n: Int) -> Map<Int, Int>:\n    return #{1: n}\n"


@pytest.mark.parametrize(
    "body,expected",
    [
        ("        if i == 0: saved = current\n        print(len(saved))\n", True),
        ("        saved = current\n        saved = saved\n        print(saved[1])\n", True),
        ("        saved = current\n        capture(saved)\n", False),
        ("        saved = current\n        let box = [saved]\n        capture(box)\n", False),
        ("        saved = current\n        return saved\n", False),
        ("        saved = current\n        saved[1] = i\n        print(saved[1])\n", False),
        ("        saved = current\n        for key in saved: print(key)\n", True),
    ],
)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_shared_map_consumers(body: str, expected: bool, opt: MIROptLevel) -> None:
    source = FACTORY + """
fn main():
    let mut saved = make(-1)
    for i in 0..10:
        let current = make(i)
""" + body
    module = lower(parse(source))
    optimize_module(module, opt)
    fn = next(fn for fn in module.functions if fn.name == "main")
    factories = owned_map_factories(module.functions)
    assert bool(shared_map_aliases(fn, factories, set())) is expected


@pytest.mark.parametrize(
    "initial,expected",
    [
        ('#{"initial": 0}', True),
        ('#{"initial": 0, "second": 1}', True),
        ('#{"initial-" + str(n): 0}', False),
        ("#{input: 0}", False),
        ('#{"initial": [1]}', False),
    ],
)
def test_literal_map_origins(initial: str, expected: bool) -> None:
    module = lower(
        parse("fn main(n: Int, input: String):\n    let m = " + initial + "\n    print(len(m))\n")
    )
    assert bool(shared_map_aliases(module.functions[0], set(), set())) is expected


def test_parameter_alias_stays_borrowed() -> None:
    fn = lower(
        parse("fn main(m: Map<Int, Int>):\n    let alias = m\n    print(len(alias))\n")
    ).functions[0]
    assert shared_map_aliases(fn, set(), set()) == set()


def test_string_lookup_prevents_shared_cleanup() -> None:
    source = """
fn make(n: Int) -> Map<Int, String>:
    return #{1: "value-" + str(n)}
fn main():
    let mut m = make(0)
    let saved = m[1]
    m = make(1)
    print(saved)
"""
    module = lower(parse(source))
    # The original map-only proof rejected this lookup. Retained parent slots
    # now preserve the String even when its source map handle is replaced.
    assert shared_map_aliases(module.functions[-1], owned_map_factories(module.functions), set())


def test_resource_factory_argument_rejected() -> None:
    module = lower(parse("""
fn make(s: String) -> Map<Int, String>:
    return #{1: s}
fn main(s: String):
    let m = make(s)
    print(len(m))
"""))
    assert not shared_map_aliases(module.functions[-1], {"make"}, set())


def test_existing_recycling_takes_precedence() -> None:
    module = lower(parse(FACTORY + """
fn main():
    for i in 0..10:
        let m = make(i)
        print(len(m))
"""))
    fn = module.functions[-1]
    factories = owned_map_factories(module.functions)
    recycled = recyclable_map_results(fn, factories)
    assert recycled
    assert not shared_map_aliases(fn, factories, recycled)


def test_phi_groups_fail_closed() -> None:
    ty = MIRType(TypeInfo(kind=TypeKind.MAP))
    a, b, merged = (Value(name, ty) for name in ("%a", "%b", "%merged"))
    fn = MIRFunction(
        name="phi",
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Call(dest=a, fn_name="make"),
                    Call(dest=b, fn_name="make"),
                    Phi(dest=merged, incoming=[("left", a), ("right", b)]),
                    Return(val=merged),
                ],
            )
        ],
    )
    assert not shared_map_aliases(fn, {"make"}, set())
