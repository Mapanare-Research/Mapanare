"""Borrowed view dependencies may not be lost by map recycling analysis."""

import pytest

from mapanare.lower import lower
from mapanare.map_liveness import recyclable_map_results
from mapanare.map_ownership import owned_map_factories
from mapanare.mir import (
    BasicBlock,
    Branch,
    Call,
    Copy,
    IndexGet,
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
from tests.integration.test_map_borrowed_views import KEY_FACTORY, TEXT_FACTORY


@pytest.mark.parametrize(
    "body,expected",
    [
        ("        for key in m:\n            print(key)\n", True),
        ('        for key in m:\n            if key != "skip": print(len(key))\n', True),
        ("        for key in m:\n            capture(key)\n", False),
        (
            "        for key in m:\n            let captured = [key]\n            sink(captured)\n",
            False,
        ),
        ("        for key in m:\n            return key\n", False),
    ],
)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_iterator_borrow_proof(body, expected, opt):
    module = lower(
        parse(KEY_FACTORY + "fn main():\n    for i in 0..10:\n        let m = make(i)\n" + body)
    )
    optimize_module(module, opt)
    fn = next(fn for fn in module.functions if fn.name == "main")
    assert bool(recyclable_map_results(fn, owned_map_factories(module.functions))) is expected


@pytest.mark.parametrize(
    "body,expected",
    [
        ("        let text = m[1]\n        print(len(text))\n", True),
        ("        let text = m[1]\n        capture(text)\n", False),
        ("        let text = m[1]\n        let captured = [text]\n        sink(captured)\n", False),
    ],
)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_index_borrow_proof(body, expected, opt):
    module = lower(
        parse(TEXT_FACTORY + "fn main():\n    for i in 0..10:\n        let m = make(i)\n" + body)
    )
    optimize_module(module, opt)
    fn = next(fn for fn in module.functions if fn.name == "main")
    assert bool(recyclable_map_results(fn, owned_map_factories(module.functions))) is expected


@pytest.mark.parametrize("kind", ["cursor", "string", "scalar"])
@pytest.mark.parametrize("skip_copy", [False, True])
def test_single_origin_view_liveness(kind: str, skip_copy: bool) -> None:
    # Unlike the source-level retained-view guards, this has no second origin:
    # declining recycling must come from liveness, not mixed-origin rejection.
    map_ty = MIRType(TypeInfo(kind=TypeKind.MAP))
    view_ty = MIRType(
        TypeInfo(
            kind={
                "cursor": TypeKind.ANY,
                "string": TypeKind.STRING,
                "scalar": TypeKind.INT,
            }[kind]
        )
    )
    made = Value("%made", map_ty)
    view, saved = Value("%view", view_ty), Value("%saved", view_ty)
    read = (
        Call(dest=view, fn_name="__mn_map_iter_new", args=[made])
        if kind == "cursor"
        else IndexGet(dest=view, obj=made, index=Value("%key", mir_int()))
    )
    use = Call(
        dest=Value("%used", mir_bool() if kind == "cursor" else mir_int()),
        fn_name={"cursor": "__map_iter_has_next", "string": "len", "scalar": "capture"}[kind],
        args=[saved],
    )
    fn = MIRFunction(
        name="probe",
        blocks=[
            BasicBlock(
                label="header",
                instructions=[
                    Call(dest=made, fn_name="make"),
                    read,
                    (
                        Branch(
                            cond=Value("%condition", mir_bool()),
                            true_block="save",
                            false_block="use",
                        )
                        if skip_copy
                        else Jump(target="save")
                    ),
                ],
            ),
            BasicBlock(label="save", instructions=[Copy(dest=saved, src=view), Jump(target="use")]),
            BasicBlock(label="use", instructions=[use, Jump(target="header")]),
        ],
    )
    assert recyclable_map_results(fn, {"make"}) == (
        set() if skip_copy and kind != "scalar" else {"%made"}
    )
