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
    Jump,
    MIRFunction,
    MIRParam,
    MIRType,
    Return,
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
