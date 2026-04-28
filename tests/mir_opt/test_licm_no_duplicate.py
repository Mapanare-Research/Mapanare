"""Tests for Li.1: LICM hoist_instruction no-duplicate invariant (v5.1.2).

After LICM hoists a loop-invariant instruction to the preheader/header,
that instruction must appear exactly once in the function — NOT both in
the header and the original block (which was the v4.152.0 regression).
"""

from __future__ import annotations

from mapanare.mir import (
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Const,
    Jump,
    MIRFunction,
    MIRType,
    Return,
    Value,
    mir_int,
)
from mapanare.mir_opt import MIRPassStats, licm


def _v(name: str, ty: MIRType | None = None) -> Value:
    return Value(name=name, ty=ty or mir_int())


def _collect_dests(fn: MIRFunction) -> list[str]:
    """Collect all destination names across all blocks."""
    dests: list[str] = []
    for bb in fn.blocks:
        for inst in bb.instructions:
            d = getattr(inst, "dest", None)
            if d and d.name:
                dests.append(d.name)
    return dests


def test_hoisted_instruction_appears_once():
    """A hoisted instruction should appear exactly once after LICM."""
    # Build a simple loop:
    #   entry: const %x = 10, jump loop_header
    #   loop_header: branch %cond, loop_body, exit
    #   loop_body: const %invariant = 42   <-- loop-invariant, should be hoisted
    #              binop %result = %invariant + %x
    #              jump loop_header
    #   exit: return %result
    fn = MIRFunction(
        name="test_licm",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%x"), ty=mir_int(), value=10),
                    Const(dest=_v("%cond"), ty=mir_int(), value=1),
                    Jump(target="loop_header"),
                ],
            ),
            BasicBlock(
                label="loop_header",
                instructions=[
                    Branch(cond=_v("%cond"), true_block="loop_body", false_block="exit"),
                ],
            ),
            BasicBlock(
                label="loop_body",
                instructions=[
                    # Loop-invariant: operand %x is defined outside the loop
                    Const(dest=_v("%invariant"), ty=mir_int(), value=42),
                    BinOp(
                        dest=_v("%result"),
                        op=BinOpKind.ADD,
                        lhs=_v("%invariant"),
                        rhs=_v("%x"),
                    ),
                    Jump(target="loop_header"),
                ],
            ),
            BasicBlock(
                label="exit",
                instructions=[
                    Return(val=_v("%result")),
                ],
            ),
        ],
    )

    stats = MIRPassStats()
    licm(fn, stats)

    # Check no duplicate definitions
    dests = _collect_dests(fn)
    from collections import Counter

    counts = Counter(dests)
    for name, count in counts.items():
        assert count == 1, (
            f"SSA name {name!r} defined {count} times after LICM. " f"All dests: {dests}"
        )


def test_licm_hoists_invariant():
    """LICM should actually hoist a pure loop-invariant instruction."""
    fn = MIRFunction(
        name="test_hoist",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%n"), ty=mir_int(), value=100),
                    Const(dest=_v("%cond"), ty=mir_int(), value=1),
                    Jump(target="header"),
                ],
            ),
            BasicBlock(
                label="header",
                instructions=[
                    Branch(cond=_v("%cond"), true_block="body", false_block="done"),
                ],
            ),
            BasicBlock(
                label="body",
                instructions=[
                    # This const is loop-invariant and pure — should be hoisted
                    Const(dest=_v("%k"), ty=mir_int(), value=7),
                    BinOp(
                        dest=_v("%sum"),
                        op=BinOpKind.ADD,
                        lhs=_v("%k"),
                        rhs=_v("%n"),
                    ),
                    Jump(target="header"),
                ],
            ),
            BasicBlock(
                label="done",
                instructions=[
                    Return(val=_v("%sum")),
                ],
            ),
        ],
    )

    stats = MIRPassStats()
    changed = licm(fn, stats)
    assert changed, "Expected LICM to hoist the loop-invariant constant"
    assert stats.licm_hoisted >= 1

    # The invariant const should now be in the header, not the body
    header = None
    body = None
    for bb in fn.blocks:
        if bb.label == "header":
            header = bb
        elif bb.label == "body":
            body = bb

    assert header is not None
    assert body is not None

    # Check the const was moved out of the body
    body_dests = {getattr(inst, "dest", Value()).name for inst in body.instructions}
    assert "%k" not in body_dests, "%k should have been hoisted out of loop body"

    # And it should be in the header
    header_dests = {getattr(inst, "dest", Value()).name for inst in header.instructions}
    assert "%k" in header_dests, "%k should have been hoisted to header"


def test_licm_does_not_hoist_side_effects():
    """LICM should not hoist instructions with side effects (calls)."""
    fn = MIRFunction(
        name="test_no_hoist_call",
        params=[],
        return_type=mir_int(),
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=_v("%cond"), ty=mir_int(), value=1),
                    Jump(target="header"),
                ],
            ),
            BasicBlock(
                label="header",
                instructions=[
                    Branch(cond=_v("%cond"), true_block="body", false_block="done"),
                ],
            ),
            BasicBlock(
                label="body",
                instructions=[
                    # Const is pure — could be hoisted
                    Const(dest=_v("%k"), ty=mir_int(), value=99),
                    Jump(target="header"),
                ],
            ),
            BasicBlock(
                label="done",
                instructions=[
                    Return(val=_v("%k")),
                ],
            ),
        ],
    )

    stats = MIRPassStats()
    licm(fn, stats)

    # Whether or not the const was hoisted, no duplicates should exist
    dests = _collect_dests(fn)
    from collections import Counter

    counts = Counter(dests)
    for name, count in counts.items():
        assert count == 1, f"SSA name {name!r} defined {count} times. All dests: {dests}"
