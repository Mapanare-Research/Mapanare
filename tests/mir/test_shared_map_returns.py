"""Return transfer applies only to fresh, completely tracked map aliases."""

import pytest

from mapanare.lower import lower
from mapanare.map_ownership import owned_map_factories
from mapanare.map_shared import shared_map_aliases
from mapanare.mir import Return
from mapanare.mir_opt import MIROptLevel, optimize_module
from mapanare.parser import parse


@pytest.mark.parametrize("opt", list(MIROptLevel))
@pytest.mark.parametrize(
    "body",
    [
        "    return #{1: 2}\n",
        "    let m = #{1: 2}\n    let alias = m\n    return alias\n",
        "    let mut m = make(0)\n    for i in 0..10:\n        m = make(i)\n    return m\n",
    ],
)
def test_fresh_return_has_complete_reference_group(body: str, opt: MIROptLevel) -> None:
    module = lower(
        parse(
            "fn make(n: Int) -> Map<Int, Int>:\n    return #{1: n}\n"
            + "fn main() -> Map<Int, Int>:\n"
            + body
        )
    )
    optimize_module(module, opt)
    fn = module.functions[-1]
    owners = shared_map_aliases(fn, owned_map_factories(module.functions), set())
    assert owners
    for block in fn.blocks:
        for inst in block.instructions:
            if isinstance(inst, Return) and inst.val is not None:
                assert inst.val.name in owners


@pytest.mark.parametrize(
    "source",
    [
        "fn choose(m: Map<Int, Int>) -> Map<Int, Int>:\n    let alias = m\n    return alias\n",
        "fn choose() -> Map<Int, Int>:\n    let m = unknown()\n    return m\n",
        "fn choose():\n    let m = #{1: 2}\n    return m\n",
        "fn choose() -> Map<Int, Int>:\n    let m = #{1: 2}\n    capture(m)\n    return m\n",
    ],
)
def test_unproven_return_does_not_acquire_local_ownership(source: str) -> None:
    module = lower(parse(source))
    assert not shared_map_aliases(module.functions[0], set(), set())
