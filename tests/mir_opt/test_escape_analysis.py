"""Tests for Ea.1: escape_analysis_promotion heap-to-stack (v5.1.2).

Verifies that non-escaping allocations get alloc_kind=STACK and escaping
ones stay HEAP. The Python escape analysis (mir_opt.py) is tested here
because it actually sets alloc_kind on MIR instructions. The self-hosted
version (mir_opt.mn) computes the same analysis but cannot annotate
instructions (the Instruction enum lacks alloc_kind — v5.2+ scope).
"""

from __future__ import annotations

from mapanare.mir import (
    AllocKind,
    BasicBlock,
    BinOp,
    BinOpKind,
    Call,
    FieldSet,
    MIRFunction,
    MIRType,
    Return,
    StructInit,
    Value,
    WrapSome,
    mir_int,
    mir_void,
)
from mapanare.mir_opt import (
    MIRPassStats,
    analyze_escapes,
    escape_analysis_promotion,
)
from mapanare.types import TypeInfo, TypeKind


def _v(name: str, ty: MIRType | None = None) -> Value:
    return Value(name=name, ty=ty or mir_int())


def _struct_ty(name: str = "Point") -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=name))


def test_non_escaping_struct_promoted():
    """A struct that never escapes should get alloc_kind=STACK."""
    si = StructInit(
        dest=_v("%pt"),
        struct_type=_struct_ty(),
        fields=[("x", _v("1")), ("y", _v("2"))],
    )
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    si,
                    # Uses the struct but doesn't escape it
                    BinOp(
                        dest=_v("%sum"),
                        op=BinOpKind.ADD,
                        lhs=_v("1"),
                        rhs=_v("2"),
                    ),
                    Return(val=_v("%sum")),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert changed, "Expected promotion"
    assert stats.allocations_promoted == 1
    assert si.alloc_kind == AllocKind.STACK


def test_returned_struct_not_promoted():
    """A struct that is returned from the function must stay HEAP."""
    si = StructInit(
        dest=_v("%pt"),
        struct_type=_struct_ty(),
        fields=[("x", _v("1"))],
    )
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=_struct_ty(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    si,
                    Return(val=_v("%pt")),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert not changed
    assert si.alloc_kind == AllocKind.HEAP


def test_struct_stored_in_field_escapes():
    """A struct stored into another struct's field escapes."""
    inner = StructInit(
        dest=_v("%inner"),
        struct_type=_struct_ty("Inner"),
        fields=[("a", _v("1"))],
    )
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_void(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    inner,
                    FieldSet(obj=_v("%outer"), field_name="child", val=_v("%inner")),
                    Return(val=None),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert not changed
    assert inner.alloc_kind == AllocKind.HEAP


def test_struct_passed_to_unknown_call_escapes():
    """A struct passed to an unknown function escapes (conservative)."""
    si = StructInit(
        dest=_v("%pt"),
        struct_type=_struct_ty(),
        fields=[("x", _v("1"))],
    )
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_void(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    si,
                    Call(dest=_v("%r"), fn_name="unknown_fn", args=[_v("%pt")]),
                    Return(val=None),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert not changed
    assert si.alloc_kind == AllocKind.HEAP


def test_struct_passed_to_print_does_not_escape():
    """A struct passed to print (known non-capturing) should be promoted."""
    si = StructInit(
        dest=_v("%pt"),
        struct_type=_struct_ty(),
        fields=[("x", _v("1"))],
    )
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_void(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    si,
                    Call(dest=_v("%r"), fn_name="print", args=[_v("%pt")]),
                    Return(val=None),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert changed
    assert si.alloc_kind == AllocKind.STACK


def test_analyze_escapes_returns_escaped_set():
    """analyze_escapes correctly identifies escaping allocations."""
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    StructInit(
                        dest=_v("%escapes"),
                        struct_type=_struct_ty(),
                        fields=[("x", _v("1"))],
                    ),
                    StructInit(
                        dest=_v("%stays"),
                        struct_type=_struct_ty(),
                        fields=[("y", _v("2"))],
                    ),
                    # %escapes is returned, %stays is not
                    Return(val=_v("%escapes")),
                ],
            )
        ],
    )

    escaped = analyze_escapes(fn)
    assert "%escapes" in escaped
    assert "%stays" not in escaped


def test_wrap_some_non_escaping_promoted():
    """A WrapSome that doesn't escape should get alloc_kind=STACK."""
    ws = WrapSome(dest=_v("%opt"), val=_v("42"))
    fn = MIRFunction(
        name="test",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    ws,
                    Return(val=_v("0")),
                ],
            )
        ],
    )

    stats = MIRPassStats()
    changed = escape_analysis_promotion(fn, stats)
    assert changed
    assert ws.alloc_kind == AllocKind.STACK
