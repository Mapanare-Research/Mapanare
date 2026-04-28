"""Tests for In.1: inline_small_functions SSA rename correctness (v5.1.2).

After inlining a call, no SSA register should be defined twice in the
resulting function. The inliner must produce unique destination names
for the inlined result — reusing the caller's original destination can
collide with definitions in other blocks.
"""

from __future__ import annotations

from mapanare.mir import (
    BasicBlock,
    BinOp,
    BinOpKind,
    Call,
    Const,
    Copy,
    EnumPayload,
    EnumTag,
    FieldGet,
    IndexGet,
    Jump,
    MIRFunction,
    MIRParam,
    MIRType,
    Return,
    StructInit,
    Value,
    mir_int,
)
from mapanare.mir_opt import MIRPassStats, inline_small_functions


def _v(name: str, ty: MIRType | None = None) -> Value:
    return Value(name=name, ty=ty or mir_int())


def _make_small_fn(name: str) -> MIRFunction:
    """A one-block function that returns its argument + 1."""
    return MIRFunction(
        name=name,
        params=[MIRParam(name="x", ty=mir_int())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    BinOp(dest=_v("%t0"), op=BinOpKind.ADD, lhs=_v("%x"), rhs=_v("1")),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )


def _collect_dests(fn: MIRFunction) -> list[str]:
    """Collect all destination names across all blocks."""
    dests: list[str] = []
    for bb in fn.blocks:
        for inst in bb.instructions:
            d = getattr(inst, "dest", None)
            if d and d.name:
                dests.append(d.name)
    return dests


def test_no_duplicate_defs_after_inline():
    """After inlining, no SSA name should appear as dest more than once."""
    callee = _make_small_fn("add_one")
    caller = MIRFunction(
        name="main",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%t0"), ty=mir_int(), value="5"),
                    Call(dest=_v("%t1"), fn_name="add_one", args=[_v("%t0")]),
                    # Post-call: use the call result
                    BinOp(
                        dest=_v("%t2"),
                        op=BinOpKind.ADD,
                        lhs=_v("%t1"),
                        rhs=_v("10"),
                    ),
                    Return(val=_v("%t2")),
                ],
            )
        ],
    )

    fn_lookup = {"add_one": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed, "Expected inlining to occur"
    assert stats.functions_inlined == 1

    # Check no duplicate dests
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert d not in seen, f"SSA name {d!r} defined twice after inlining. " f"All dests: {dests}"
        seen.add(d)


def test_inlined_result_used_correctly():
    """Post-call instructions should correctly reference the inlined result.

    After inlining, the merge block should contain a Copy from the inlined
    retval to the original call destination, and the post-call BinOp should
    reference that destination (or a renamed version of it).
    """
    callee = _make_small_fn("add_one")
    caller = MIRFunction(
        name="test_fn",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%t0"), ty=mir_int(), value="5"),
                    Call(dest=_v("%t1"), fn_name="add_one", args=[_v("%t0")]),
                    BinOp(
                        dest=_v("%t2"),
                        op=BinOpKind.ADD,
                        lhs=_v("%t1"),
                        rhs=_v("10"),
                    ),
                    Return(val=_v("%t2")),
                ],
            )
        ],
    )

    fn_lookup = {"add_one": callee}
    stats = MIRPassStats()
    inline_small_functions(caller, fn_lookup, stats)

    # Find the merge block — the one whose label contains "ret" (inline merge)
    merge_block = None
    for bb in caller.blocks:
        if "ret" in bb.label and "_inl" in bb.label:
            merge_block = bb
            break

    assert (
        merge_block is not None
    ), f"No merge block found. Blocks: {[bb.label for bb in caller.blocks]}"

    # The merge block should start with a Copy from the retval
    copy_inst = merge_block.instructions[0]
    assert isinstance(
        copy_inst, Copy
    ), f"Expected Copy as first merge instruction, got {type(copy_inst).__name__}"
    assert "retval" in copy_inst.src.name, f"Expected retval source, got {copy_inst.src.name}"

    # The post-call BinOp should reference the Copy's destination
    binop_inst = merge_block.instructions[1]
    assert isinstance(binop_inst, BinOp)
    assert binop_inst.lhs.name == copy_inst.dest.name, (
        f"BinOp lhs {binop_inst.lhs.name!r} should reference " f"Copy dest {copy_inst.dest.name!r}"
    )


def test_multi_block_caller_no_collision():
    """Inlining in a caller with multiple blocks should not produce collisions."""
    callee = _make_small_fn("inc")
    # Caller has two blocks, both using %t-style names
    caller = MIRFunction(
        name="multi_block",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%t0"), ty=mir_int(), value="1"),
                    Call(dest=_v("%t1"), fn_name="inc", args=[_v("%t0")]),
                    Jump(target="next"),
                ],
            ),
            BasicBlock(
                label="next",
                instructions=[
                    # This block uses %t1 from the call above
                    BinOp(
                        dest=_v("%t2"),
                        op=BinOpKind.ADD,
                        lhs=_v("%t1"),
                        rhs=_v("100"),
                    ),
                    Return(val=_v("%t2")),
                ],
            ),
        ],
    )

    fn_lookup = {"inc": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed

    # No duplicate dests across the entire function
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert d not in seen, (
            f"SSA name {d!r} defined twice in multi-block caller. " f"All dests: {dests}"
        )
        seen.add(d)


def test_inlining_cap():
    """Inline cap prevents cascading — at most 5 inline sites per function."""
    callee = _make_small_fn("tiny")
    # Caller with 7 call sites
    insts = []
    for i in range(7):
        insts.append(Const(dest=_v(f"%a{i}"), ty=mir_int(), value=str(i)))
        insts.append(Call(dest=_v(f"%r{i}"), fn_name="tiny", args=[_v(f"%a{i}")]))
    insts.append(Return(val=_v("%r0")))

    caller = MIRFunction(
        name="many_calls",
        params=[],
        return_type=mir_int(),
        blocks=[BasicBlock(label="entry", instructions=insts)],
    )

    fn_lookup = {"tiny": callee}
    stats = MIRPassStats()
    # Run multiple times (the pass inlines one site per call)
    total_inlined = 0
    for _ in range(10):
        changed = inline_small_functions(caller, fn_lookup, stats)
        if changed:
            total_inlined += 1
        else:
            break

    assert total_inlined <= 5, f"Expected at most 5 inlines, got {total_inlined}"


# --- v5.3.2 tests: previously-unhandled instruction variants ---


def _struct_ty() -> MIRType:
    return mir_int()  # Type details don't matter for inline rename tests


def _make_fieldget_fn(name: str) -> MIRFunction:
    """A one-block function that reads a struct field and returns it."""
    return MIRFunction(
        name=name,
        params=[MIRParam(name="s", ty=_struct_ty())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    FieldGet(dest=_v("%t0"), obj=_v("%s"), field_name="line"),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )


def test_fieldget_no_duplicate_defs():
    """v5.3.2: FieldGet destination must be renamed during inlining."""
    callee = _make_fieldget_fn("get_line")
    caller = MIRFunction(
        name="caller",
        params=[MIRParam(name="span", ty=_struct_ty())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Call(dest=_v("%t0"), fn_name="get_line", args=[_v("%span")]),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    fn_lookup = {"get_line": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert (
            d not in seen
        ), f"SSA name {d!r} defined twice after FieldGet inlining. All dests: {dests}"
        seen.add(d)


def test_structinit_no_duplicate_defs():
    """v5.3.2: StructInit destination must be renamed during inlining."""
    callee = MIRFunction(
        name="make_point",
        params=[MIRParam(name="x", ty=mir_int()), MIRParam(name="y", ty=mir_int())],
        return_type=_struct_ty(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    StructInit(
                        dest=_v("%t0"),
                        struct_type=_struct_ty(),
                        fields=[("x", _v("%x")), ("y", _v("%y"))],
                    ),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    caller = MIRFunction(
        name="caller",
        params=[],
        return_type=_struct_ty(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%a"), ty=mir_int(), value="1"),
                    Const(dest=_v("%b"), ty=mir_int(), value="2"),
                    Call(dest=_v("%t0"), fn_name="make_point", args=[_v("%a"), _v("%b")]),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    fn_lookup = {"make_point": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert (
            d not in seen
        ), f"SSA name {d!r} defined twice after StructInit inlining. All dests: {dests}"
        seen.add(d)


def test_indexget_no_duplicate_defs():
    """v5.3.2: IndexGet destination must be renamed during inlining."""
    callee = MIRFunction(
        name="first_elem",
        params=[MIRParam(name="arr", ty=mir_int())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%idx"), ty=mir_int(), value="0"),
                    IndexGet(dest=_v("%t0"), obj=_v("%arr"), index=_v("%idx")),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    caller = MIRFunction(
        name="caller",
        params=[MIRParam(name="list", ty=mir_int())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Call(dest=_v("%t0"), fn_name="first_elem", args=[_v("%list")]),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    fn_lookup = {"first_elem": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert (
            d not in seen
        ), f"SSA name {d!r} defined twice after IndexGet inlining. All dests: {dests}"
        seen.add(d)


def test_enumtag_payload_no_duplicate_defs():
    """v5.3.2: EnumTag/EnumPayload destinations must be renamed during inlining."""
    callee = MIRFunction(
        name="get_tag",
        params=[MIRParam(name="e", ty=mir_int())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    EnumTag(dest=_v("%t0"), enum_val=_v("%e")),
                    EnumPayload(dest=_v("%t1"), enum_val=_v("%e"), variant="Some"),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    caller = MIRFunction(
        name="caller",
        params=[MIRParam(name="val", ty=mir_int())],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Call(dest=_v("%t0"), fn_name="get_tag", args=[_v("%val")]),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    fn_lookup = {"get_tag": callee}
    stats = MIRPassStats()
    changed = inline_small_functions(caller, fn_lookup, stats)
    assert changed
    dests = _collect_dests(caller)
    seen: set[str] = set()
    for d in dests:
        assert (
            d not in seen
        ), f"SSA name {d!r} defined twice after EnumTag/Payload inlining. All dests: {dests}"
        seen.add(d)


def test_param_count_mismatch_does_not_crash():
    """v5.3.2: Calls where arg count != param count must not crash.

    The self-hosted inliner (mir_opt.mn) skips these; the Python inliner
    may still inline them but must not crash. This tests robustness.
    """
    # Callee has 1 param, but call passes 2 args (simulates name collision)
    callee = _make_small_fn("overloaded")
    caller = MIRFunction(
        name="caller",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%a"), ty=mir_int(), value="1"),
                    Const(dest=_v("%b"), ty=mir_int(), value="2"),
                    Call(dest=_v("%t0"), fn_name="overloaded", args=[_v("%a"), _v("%b")]),
                    Return(val=_v("%t0")),
                ],
            )
        ],
    )
    fn_lookup = {"overloaded": callee}
    stats = MIRPassStats()
    # Must not raise — whether it inlines or skips is implementation-defined
    inline_small_functions(caller, fn_lookup, stats)
