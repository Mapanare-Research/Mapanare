"""Private range cleanup must not assume ownership of escaping aliases."""

import pytest

from mapanare.mir import (
    BasicBlock,
    Call,
    Copy,
    MIRFunction,
    MIRParam,
    MIRType,
    Return,
    Value,
    mir_bool,
    mir_int,
    mir_string,
)
from mapanare.range_ownership import private_range_results
from mapanare.types import TypeInfo, TypeKind


@pytest.mark.parametrize(
    "kind,accepted",
    [
        ("exclusive", True),
        ("inclusive", True),
        ("unused", True),
        ("copy", False),
        ("return", False),
        ("capture", False),
        ("two-frees", False),
        ("redefined", False),
        ("parameter", False),
        ("async", False),
        ("bad-bound", False),
        ("wrong-type", False),
    ],
)
def test_private_range_proof(kind: str, accepted: bool) -> None:
    ty = MIRType(TypeInfo(kind=TypeKind.RANGE))
    iterator = Value("%range", ty)
    root = Call(
        dest=iterator,
        fn_name="__mn_range",
        args=[Value("%start", mir_int()), Value("%end", mir_int())],
    )
    release = Call(dest=Value("%freed", mir_bool()), fn_name="__mn_range_free", args=[iterator])
    body = [
        root,
        Call(dest=Value("%more", mir_bool()), fn_name="__iter_has_next", args=[iterator]),
        release,
        Return(),
    ]
    fn = MIRFunction(name="main", blocks=[BasicBlock(label="entry", instructions=body)])
    if kind == "inclusive":
        root.fn_name = "__mn_range_inclusive"
    elif kind == "unused":
        body[:] = [root, Return()]
    elif kind == "copy":
        body.insert(1, Copy(dest=Value("%alias", ty), src=iterator))
    elif kind == "return":
        body[-1] = Return(val=iterator)
    elif kind == "capture":
        body.insert(1, Call(dest=Value("%out", mir_int()), fn_name="capture", args=[iterator]))
    elif kind == "two-frees":
        body.insert(-1, release)
    elif kind == "redefined":
        body.insert(1, root)
    elif kind == "parameter":
        fn.params.append(MIRParam(name=iterator.name, ty=ty))
    elif kind == "async":
        fn.is_async = True
    elif kind == "bad-bound":
        root.args[0] = Value("%start", mir_string())
    elif kind == "wrong-type":
        root.dest = Value(iterator.name, mir_int())
    assert (iterator.name in private_range_results(fn)) is accepted
