"""v4.30.0 Phase 3.1: the MIR optimizer fixpoint loop must raise on
non-convergence.

Prior to v4.30.0 this site emitted ``logging.warning`` and shipped the
half-optimized MIR — silent failure, nobody read the log. The v4.26.0
seven-reviewer panel (Anaconda HIGH) flagged it. v4.30.0 replaces the
warning with ``MIROptimizerNonConvergence``.

These tests pin the exception path so any future regression that
silently reintroduces the warning gets caught at PR time. They also
verify that ``dead_code_elimination`` converges internally — the chain
of dead instructions that used to force the outer loop past its cap
(``emit_llvm__emit_binop`` with >10 layers of dependent dead code)
now drains in a single DCE call.
"""

from __future__ import annotations

import pytest

from mapanare.mir import (
    BasicBlock,
    BinOp,
    BinOpKind,
    Const,
    MIRFunction,
    Return,
    Value,
    mir_int,
)
from mapanare.mir_opt import (
    MIROptimizerNonConvergence,
    MIROptLevel,
    MIRPassStats,
    dead_code_elimination,
    optimize_function,
)


def _build_dead_chain(n: int) -> MIRFunction:
    """Build a function whose entry block is N dead ``let`` bindings
    followed by ``return 0``.

    Each binding depends on the previous one, so DCE can only remove
    them one layer at a time unless it iterates internally. Pre-v4.30.0
    this meant ``N`` outer fixpoint iterations; with the internal
    convergence fix it drains in a single DCE call.
    """
    insts: list = []
    prev = Value(name="x0", ty=mir_int())
    insts.append(Const(dest=prev, ty=mir_int(), value=0))
    for i in range(1, n + 1):
        nxt = Value(name=f"x{i}", ty=mir_int())
        insts.append(
            BinOp(
                dest=nxt,
                op=BinOpKind.ADD,
                lhs=prev,
                rhs=prev,
            )
        )
        prev = nxt
    # ``return 0`` — no use of x1..xN, so every binding is dead.
    ret_val = Value(name="ret", ty=mir_int())
    insts.append(Const(dest=ret_val, ty=mir_int(), value=0))
    insts.append(Return(val=ret_val))
    bb = BasicBlock(label="entry", instructions=insts)
    return MIRFunction(
        name="test_dead_chain",
        params=[],
        return_type=mir_int(),
        blocks=[bb],
    )


class TestDeadCodeConvergesInternally:
    """DCE must drain a chain of N dependent dead instructions in one call."""

    def test_dce_removes_20_layers_in_one_call(self) -> None:
        fn = _build_dead_chain(20)
        stats = MIRPassStats()
        # One call to DCE must return True (work was done) and leave
        # only the return instructions (the two that are actually live).
        changed = dead_code_elimination(fn, stats)
        assert changed is True
        live = [
            i
            for bb in fn.blocks
            for i in bb.instructions
            if not isinstance(i, Return) and not (isinstance(i, Const) and i.dest.name == "ret")
        ]
        assert live == [], (
            f"DCE left {len(live)} dead instructions after one call; "
            f"the v4.30.0 fix was supposed to drain the full chain"
        )

    def test_second_call_is_noop(self) -> None:
        fn = _build_dead_chain(10)
        stats = MIRPassStats()
        dead_code_elimination(fn, stats)  # drain
        assert (
            dead_code_elimination(fn, stats) is False
        ), "DCE should report no change on a fully-drained function"


class TestOptimizerICEsOnNonConvergence:
    """If the fixpoint loop exhausts its cap, optimize_function must raise."""

    def test_ice_type_is_exported(self) -> None:
        from mapanare import mir_opt

        assert hasattr(mir_opt, "MIROptimizerNonConvergence")
        assert issubclass(mir_opt.MIROptimizerNonConvergence, Exception)

    def test_non_convergent_pass_triggers_ice(self) -> None:
        """Synthesize a rogue pass that always returns True, patch it
        into the optimizer, and verify the ICE fires.

        We patch ``dead_code_elimination`` because it is called at O2+
        and the fixture avoids needing to construct a module with all
        possible instruction types. The patch is reverted in
        ``finally`` so other tests are unaffected.
        """
        from mapanare import mir_opt

        orig = mir_opt.dead_code_elimination

        def rogue(fn: MIRFunction, stats: MIRPassStats) -> bool:
            # Always report "changed" without actually changing anything.
            # This is exactly the pattern the fixpoint cap is supposed
            # to catch.
            return True

        mir_opt.dead_code_elimination = rogue
        try:
            fn = _build_dead_chain(3)
            stats = MIRPassStats()
            with pytest.raises(MIROptimizerNonConvergence) as exc_info:
                optimize_function(fn, MIROptLevel.O2, stats)
            # The message must mention the function name and the word
            # ``converge`` so the fix location is obvious from the
            # traceback alone.
            msg = str(exc_info.value)
            assert "test_dead_chain" in msg
            assert "converge" in msg
        finally:
            mir_opt.dead_code_elimination = orig

    def test_golden_corpus_converges(self) -> None:
        """The default O2 optimizer must converge on our dead-chain
        fixture — i.e. the real (non-rogue) DCE is enough to drain
        the outer fixpoint loop. If this test regresses, a new pass
        has been added that fights with an existing one.
        """
        fn = _build_dead_chain(15)
        stats = MIRPassStats()
        optimize_function(fn, MIROptLevel.O2, stats)
