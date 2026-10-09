"""Copy propagation must preserve snapshots of changing MIR variables."""

import pytest

from mapanare.mir import (
    BasicBlock,
    Branch,
    Call,
    Const,
    Copy,
    Jump,
    MIRFunction,
    Return,
    Value,
    mir_bool,
    mir_int,
)
from mapanare.mir_opt import MIRPassStats, copy_propagation


@pytest.mark.parametrize("parameter", [False, True])
def test_copy_of_reassigned_source_keeps_snapshot(parameter: bool) -> None:
    source, saved = Value("%source", mir_int()), Value("%saved", mir_int())
    instructions = [] if parameter else [Const(dest=source, ty=mir_int(), value=1)]
    instructions += [
        Copy(dest=saved, src=source),
        Const(dest=source, ty=mir_int(), value=2),
        Return(val=saved),
    ]
    fn = MIRFunction(
        name="snapshot",
        params=[source] if parameter else [],
        blocks=[BasicBlock(label="entry", instructions=instructions)],
    )
    copy_propagation(fn, MIRPassStats())
    assert instructions[-1].val.name == "%saved"


def test_copy_of_loop_redefined_source_keeps_snapshot() -> None:
    source, saved = Value("%source", mir_int()), Value("%saved", mir_int())
    use = Call(dest=Value("%out", mir_int()), fn_name="observe", args=[saved])
    fn = MIRFunction(
        name="loop",
        blocks=[
            BasicBlock(
                label="body",
                instructions=[
                    Call(dest=source, fn_name="next"),
                    Branch(cond=Value("%save", mir_bool()), true_block="save", false_block="use"),
                ],
            ),
            BasicBlock(
                label="save", instructions=[Copy(dest=saved, src=source), Jump(target="use")]
            ),
            BasicBlock(label="use", instructions=[use, Jump(target="body")]),
        ],
    )
    copy_propagation(fn, MIRPassStats())
    assert use.args[0].name == "%saved"


def test_stable_parameter_copy_still_propagates() -> None:
    source, saved = Value("%source", mir_int()), Value("%saved", mir_int())
    ret = Return(val=saved)
    fn = MIRFunction(
        name="stable",
        params=[source],
        blocks=[BasicBlock(label="entry", instructions=[Copy(dest=saved, src=source), ret])],
    )
    assert copy_propagation(fn, MIRPassStats())
    assert ret.val.name == "%source"
