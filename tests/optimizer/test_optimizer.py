"""Tests for Phase 4.4 — Optimization Passes.

Each test class corresponds to a roadmap task in Phase 4.4.
"""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import (
    AgentDef,
    AgentInput,
    AgentOutput,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    ExprStmt,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    ForLoop,
    Identifier,
    IfExpr,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    MethodCallExpr,
    NamedType,
    Param,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    StringLiteral,
    UnaryExpr,
)
from mapanare.optimizer import (
    AgentInliner,
    ConstantFolder,
    DeadCodeEliminator,
    OptLevel,
    PassStats,
    StreamFuser,
    optimize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fn(
    name: str = "test_fn",
    params: list[Param] | None = None,
    ret: NamedType | None = None,
    body: list[object] | None = None,
    public: bool = False,
) -> FnDef:
    return FnDef(
        name=name,
        public=public,
        params=params or [],
        return_type=ret,
        body=Block(stmts=body or []),
    )


def _make_program(*defs: object) -> Program:
    return Program(definitions=list(defs))


# ===========================================================================
# Task 1: Constant Folding and Propagation
# ===========================================================================


class TestConstantFolding:
    """Task 4.4.1 — Constant folding and propagation."""

    # -- Arithmetic folding --

    def test_fold_int_addition(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=3), op="+", right=IntLiteral(value=4))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret, ReturnStmt)
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 7
        assert folder.stats.constants_folded == 1

    def test_fold_int_subtraction(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=10), op="-", right=IntLiteral(value=3))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 7

    def test_fold_int_multiplication(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=5), op="*", right=IntLiteral(value=6))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 30

    def test_fold_int_division(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=15), op="/", right=IntLiteral(value=3))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 5

    def test_fold_int_modulo(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=17), op="%", right=IntLiteral(value=5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 2

    def test_no_fold_division_by_zero(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=10), op="/", right=IntLiteral(value=0))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BinaryExpr)

    def test_fold_float_arithmetic(self) -> None:
        expr = BinaryExpr(left=FloatLiteral(value=2.5), op="*", right=FloatLiteral(value=4.0))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, FloatLiteral)
        assert ret.value.value == 10.0

    def test_fold_mixed_int_float(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=3), op="+", right=FloatLiteral(value=1.5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, FloatLiteral)
        assert ret.value.value == 4.5

    # -- Comparison folding --

    def test_fold_equality(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=5), op="==", right=IntLiteral(value=5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is True

    def test_fold_inequality(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=3), op="!=", right=IntLiteral(value=5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is True

    def test_fold_less_than(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=3), op="<", right=IntLiteral(value=5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is True

    def test_fold_greater_equal(self) -> None:
        expr = BinaryExpr(left=IntLiteral(value=5), op=">=", right=IntLiteral(value=5))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is True

    # -- Logical folding --

    def test_fold_logical_and(self) -> None:
        expr = BinaryExpr(left=BoolLiteral(value=True), op="&&", right=BoolLiteral(value=False))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is False

    def test_fold_logical_or(self) -> None:
        expr = BinaryExpr(left=BoolLiteral(value=False), op="||", right=BoolLiteral(value=True))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is True

    # -- Unary folding --

    def test_fold_negation(self) -> None:
        expr = UnaryExpr(op="-", operand=IntLiteral(value=42))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == -42

    def test_fold_not(self) -> None:
        expr = UnaryExpr(op="!", operand=BoolLiteral(value=True))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BoolLiteral)
        assert ret.value.value is False

    # -- String folding --

    def test_fold_string_concat(self) -> None:
        expr = BinaryExpr(
            left=StringLiteral(value="hello "),
            op="+",
            right=StringLiteral(value="world"),
        )
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, StringLiteral)
        assert ret.value.value == "hello world"

    # -- Nested/cascading folds --

    def test_fold_nested_expression(self) -> None:
        """(2 + 3) * 4 → 20"""
        inner = BinaryExpr(left=IntLiteral(value=2), op="+", right=IntLiteral(value=3))
        outer = BinaryExpr(left=inner, op="*", right=IntLiteral(value=4))
        fn = _make_fn(body=[ReturnStmt(value=outer)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 20

    def test_no_fold_with_variable(self) -> None:
        """x + 3 cannot be folded."""
        expr = BinaryExpr(left=Identifier(name="x"), op="+", right=IntLiteral(value=3))
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            body=[ReturnStmt(value=expr)],
        )
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BinaryExpr)

    # -- Constant propagation --

    def test_propagate_constant(self) -> None:
        """let x = 5; return x + 1 → return 6"""
        let = LetBinding(name="x", mutable=False, value=IntLiteral(value=5))
        ret = ReturnStmt(
            value=BinaryExpr(left=Identifier(name="x"), op="+", right=IntLiteral(value=1))
        )
        fn = _make_fn(body=[let, ret])
        prog = _make_program(fn)
        optimize(prog, OptLevel.O1)
        # The let binding may still exist but the return should be folded
        # Find the return statement
        for s in prog.definitions[0].body.stmts:
            if isinstance(s, ReturnStmt):
                assert isinstance(s.value, IntLiteral)
                assert s.value.value == 6
                return
        pytest.fail("No return statement found")

    def test_no_propagate_mutable(self) -> None:
        """let mut x = 5; x = 10; return x → NOT propagated."""
        let = LetBinding(name="x", mutable=True, value=IntLiteral(value=5))
        assign = ExprStmt(
            expr=AssignExpr(target=Identifier(name="x"), op="=", value=IntLiteral(value=10))
        )
        ret = ReturnStmt(value=Identifier(name="x"))
        fn = _make_fn(body=[let, assign, ret])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        ret_stmt = prog.definitions[0].body.stmts[2]
        assert isinstance(ret_stmt, ReturnStmt)
        assert isinstance(ret_stmt.value, Identifier)

    def test_fold_in_let_binding(self) -> None:
        """let y = 2 + 3 → let y = 5"""
        let = LetBinding(
            name="y",
            mutable=False,
            value=BinaryExpr(left=IntLiteral(value=2), op="+", right=IntLiteral(value=3)),
        )
        fn = _make_fn(body=[let, ReturnStmt(value=Identifier(name="y"))])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        let_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, IntLiteral)
        assert let_stmt.value.value == 5

    def test_fold_in_call_args(self) -> None:
        """foo(1 + 2) → foo(3)"""
        call = CallExpr(
            callee=Identifier(name="foo"),
            args=[BinaryExpr(left=IntLiteral(value=1), op="+", right=IntLiteral(value=2))],
        )
        fn = _make_fn(body=[ExprStmt(expr=call)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        call_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(call_stmt, ExprStmt)
        assert isinstance(call_stmt.expr, CallExpr)
        assert isinstance(call_stmt.expr.args[0], IntLiteral)
        assert call_stmt.expr.args[0].value == 3

    def test_fold_in_if_condition(self) -> None:
        """if (1 < 2) { ... } → if (true) { ... }"""
        if_expr = IfExpr(
            condition=BinaryExpr(left=IntLiteral(value=1), op="<", right=IntLiteral(value=2)),
            then_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=1))]),
        )
        fn = _make_fn(body=[ExprStmt(expr=if_expr)])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(stmt.expr, IfExpr)
        assert isinstance(stmt.expr.condition, BoolLiteral)
        assert stmt.expr.condition.value is True

    def test_fold_in_range(self) -> None:
        """for i in (1+1)..(3+2) → for i in 2..5"""
        loop = ForLoop(
            var_name="i",
            iterable=RangeExpr(
                start=BinaryExpr(left=IntLiteral(value=1), op="+", right=IntLiteral(value=1)),
                end=BinaryExpr(left=IntLiteral(value=3), op="+", right=IntLiteral(value=2)),
            ),
            body=Block(stmts=[]),
        )
        fn = _make_fn(body=[loop])
        prog = _make_program(fn)
        folder = ConstantFolder()
        folder.run(prog)
        stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(stmt, ForLoop)
        assert isinstance(stmt.iterable, RangeExpr)
        assert isinstance(stmt.iterable.start, IntLiteral)
        assert stmt.iterable.start.value == 2
        assert isinstance(stmt.iterable.end, IntLiteral)
        assert stmt.iterable.end.value == 5


# ===========================================================================
# Task 2: Dead Code Elimination
# ===========================================================================


class TestDeadCodeElimination:
    """Task 4.4.2 — Dead code elimination."""

    def test_remove_after_return(self) -> None:
        """Statements after return are removed."""
        fn = _make_fn(
            name="main",
            body=[
                ReturnStmt(value=IntLiteral(value=42)),
                ExprStmt(
                    expr=CallExpr(
                        callee=Identifier(name="println"),
                        args=[StringLiteral(value="unreachable")],
                    )
                ),
            ],
        )
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions[0].body.stmts) == 1
        assert isinstance(prog.definitions[0].body.stmts[0], ReturnStmt)
        assert dce.stats.dead_stmts_removed == 1

    def test_remove_multiple_after_return(self) -> None:
        """All statements after return are removed."""
        fn = _make_fn(
            name="main",
            body=[
                ReturnStmt(value=IntLiteral(value=1)),
                LetBinding(name="x", value=IntLiteral(value=2)),
                LetBinding(name="y", value=IntLiteral(value=3)),
                ReturnStmt(value=IntLiteral(value=4)),
            ],
        )
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions[0].body.stmts) == 1
        assert dce.stats.dead_stmts_removed == 3

    def test_keep_code_before_return(self) -> None:
        """Code before return is preserved."""
        fn = _make_fn(
            name="main",
            body=[
                LetBinding(name="x", value=IntLiteral(value=5)),
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="x"),
                        op="+",
                        right=IntLiteral(value=1),
                    )
                ),
            ],
        )
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions[0].body.stmts) == 2

    def test_remove_unused_let(self) -> None:
        """Unused let bindings with pure literal values are removed."""
        fn = _make_fn(
            name="main",
            body=[
                LetBinding(name="unused", value=IntLiteral(value=99)),
                ReturnStmt(value=IntLiteral(value=1)),
            ],
        )
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions[0].body.stmts) == 1
        assert isinstance(prog.definitions[0].body.stmts[0], ReturnStmt)
        assert dce.stats.dead_stmts_removed == 1

    def test_keep_used_let(self) -> None:
        """Used let bindings are preserved."""
        fn = _make_fn(
            name="main",
            body=[
                LetBinding(name="x", value=IntLiteral(value=5)),
                ReturnStmt(value=Identifier(name="x")),
            ],
        )
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions[0].body.stmts) == 2

    def test_remove_dead_private_function(self) -> None:
        """Unreferenced private functions are removed."""
        main_fn = _make_fn(name="main", body=[ReturnStmt(value=IntLiteral(value=0))])
        dead_fn = _make_fn(
            name="never_called",
            public=False,
            body=[ReturnStmt(value=IntLiteral(value=42))],
        )
        prog = _make_program(main_fn, dead_fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions) == 1
        assert prog.definitions[0].name == "main"
        assert dce.stats.dead_fns_removed == 1

    def test_keep_referenced_function(self) -> None:
        """Functions referenced by other functions are kept."""
        helper_fn = _make_fn(name="helper", body=[ReturnStmt(value=IntLiteral(value=42))])
        main_fn = _make_fn(
            name="main",
            body=[ReturnStmt(value=CallExpr(callee=Identifier(name="helper"), args=[]))],
        )
        prog = _make_program(helper_fn, main_fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions) == 2

    def test_keep_public_function(self) -> None:
        """Public functions are never removed even if unreferenced."""
        main_fn = _make_fn(name="main", body=[ReturnStmt(value=IntLiteral(value=0))])
        pub_fn = _make_fn(
            name="api_handler",
            public=True,
            body=[ReturnStmt(value=IntLiteral(value=200))],
        )
        prog = _make_program(main_fn, pub_fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert len(prog.definitions) == 2

    def test_dce_in_for_body(self) -> None:
        """Dead code after return inside a for loop body is removed."""
        loop = ForLoop(
            var_name="i",
            iterable=RangeExpr(start=IntLiteral(value=0), end=IntLiteral(value=10)),
            body=Block(
                stmts=[
                    ReturnStmt(value=Identifier(name="i")),
                    ExprStmt(
                        expr=CallExpr(
                            callee=Identifier(name="println"),
                            args=[StringLiteral(value="dead")],
                        )
                    ),
                ]
            ),
        )
        fn = _make_fn(name="main", body=[loop])
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        loop_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(loop_stmt, ForLoop)
        assert len(loop_stmt.body.stmts) == 1

    def test_constant_condition_detection(self) -> None:
        """If with constant true/false condition is detected."""
        if_expr = IfExpr(
            condition=BoolLiteral(value=True),
            then_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=1))]),
            else_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=2))]),
        )
        fn = _make_fn(name="main", body=[ExprStmt(expr=if_expr)])
        prog = _make_program(fn)
        dce = DeadCodeEliminator()
        dce.run(prog)
        assert dce.stats.dead_branches_removed == 1


# ===========================================================================
# Task 3: Agent Communication Inlining
# ===========================================================================


class TestAgentInlining:
    """Task 4.4.3 — Agent communication inlining."""

    def test_identify_simple_agent(self) -> None:
        """Simple agents (one method, no state, no effects) are identified."""
        agent = AgentDef(
            name="Doubler",
            inputs=[AgentInput(name="input", type_annotation=NamedType(name="Int"))],
            outputs=[AgentOutput(name="output", type_annotation=NamedType(name="Int"))],
            state=[],
            methods=[
                FnDef(
                    name="on_message",
                    params=[Param(name="x", type_annotation=NamedType(name="Int"))],
                    return_type=NamedType(name="Int"),
                    body=Block(
                        stmts=[
                            ReturnStmt(
                                value=BinaryExpr(
                                    left=Identifier(name="x"),
                                    op="*",
                                    right=IntLiteral(value=2),
                                )
                            )
                        ]
                    ),
                )
            ],
        )
        prog = _make_program(agent)
        inliner = AgentInliner()
        inliner.run(prog)
        assert "Doubler" in inliner._simple_agents

    def test_agent_with_state_not_simple(self) -> None:
        """Agents with state are not considered simple."""
        agent = AgentDef(
            name="Counter",
            inputs=[AgentInput(name="input", type_annotation=NamedType(name="Int"))],
            outputs=[AgentOutput(name="output", type_annotation=NamedType(name="Int"))],
            state=[LetBinding(name="count", mutable=True, value=IntLiteral(value=0))],
            methods=[
                FnDef(
                    name="on_message",
                    params=[],
                    body=Block(stmts=[ReturnStmt(value=IntLiteral(value=0))]),
                )
            ],
        )
        prog = _make_program(agent)
        inliner = AgentInliner()
        inliner.run(prog)
        assert "Counter" not in inliner._simple_agents

    def test_agent_with_effects_not_simple(self) -> None:
        """Agents with side effects are not considered simple."""
        agent = AgentDef(
            name="Printer",
            inputs=[AgentInput(name="input", type_annotation=NamedType(name="String"))],
            outputs=[],
            state=[],
            methods=[
                FnDef(
                    name="on_message",
                    params=[Param(name="msg", type_annotation=NamedType(name="String"))],
                    body=Block(
                        stmts=[
                            ExprStmt(
                                expr=CallExpr(
                                    callee=Identifier(name="println"),
                                    args=[Identifier(name="msg")],
                                )
                            )
                        ]
                    ),
                )
            ],
        )
        prog = _make_program(agent)
        inliner = AgentInliner()
        inliner.run(prog)
        assert "Printer" not in inliner._simple_agents

    def test_inline_single_stage_pipe(self) -> None:
        """Single-stage pipes with unknown agents are NOT inlined (preserved as PipeDef)."""
        pipe = PipeDef(
            name="SimplePipe",
            stages=[CallExpr(callee=Identifier(name="transform"), args=[])],
        )
        prog = _make_program(pipe)
        inliner = AgentInliner()
        inliner.run(prog)
        # Not inlined because 'transform' is not a known simple agent
        assert isinstance(prog.definitions[0], PipeDef)
        assert prog.definitions[0].name == "SimplePipe"

    def test_no_inline_multi_stage_pipe(self) -> None:
        """Multi-stage pipes are not inlined."""
        pipe = PipeDef(
            name="MultiPipe",
            stages=[
                CallExpr(callee=Identifier(name="a"), args=[]),
                CallExpr(callee=Identifier(name="b"), args=[]),
            ],
        )
        prog = _make_program(pipe)
        inliner = AgentInliner()
        inliner.run(prog)
        assert isinstance(prog.definitions[0], PipeDef)

    def test_inline_send_to_simple_agent(self) -> None:
        """Send to simple agent is replaced with direct call."""
        agent = AgentDef(
            name="Doubler",
            inputs=[AgentInput(name="input", type_annotation=NamedType(name="Int"))],
            outputs=[AgentOutput(name="output", type_annotation=NamedType(name="Int"))],
            state=[],
            methods=[
                FnDef(
                    name="process",
                    params=[Param(name="x", type_annotation=NamedType(name="Int"))],
                    return_type=NamedType(name="Int"),
                    body=Block(
                        stmts=[
                            ReturnStmt(
                                value=BinaryExpr(
                                    left=Identifier(name="x"),
                                    op="*",
                                    right=IntLiteral(value=2),
                                )
                            )
                        ]
                    ),
                )
            ],
        )
        send_fn = _make_fn(
            name="main",
            body=[
                ExprStmt(
                    expr=SendExpr(
                        target=FieldAccessExpr(
                            object=Identifier(name="Doubler"),
                            field_name="input",
                        ),
                        value=IntLiteral(value=21),
                    )
                )
            ],
        )
        prog = _make_program(agent, send_fn)
        inliner = AgentInliner()
        inliner.run(prog)
        stmt = prog.definitions[1].body.stmts[0]
        assert isinstance(stmt, ExprStmt)
        assert isinstance(stmt.expr, CallExpr)
        assert inliner.stats.agents_inlined == 1


# ===========================================================================
# Task 4: Stream Fusion
# ===========================================================================


class TestStreamFusion:
    """Task 4.4.4 — Stream fusion."""

    def test_fuse_pipe_map_map(self) -> None:
        """stream |> map(f) |> map(g) → stream |> map(compose(f, g))"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=BinaryExpr(left=Identifier(name="x"), op="*", right=IntLiteral(value=2)),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BinaryExpr(left=Identifier(name="y"), op="+", right=IntLiteral(value=1)),
        )

        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(callee=Identifier(name="map"), args=[f_lambda]),
            ),
            right=CallExpr(callee=Identifier(name="map"), args=[g_lambda]),
        )
        fn = _make_fn(body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret, ReturnStmt)
        # Should be fused into single pipe with composed map
        assert isinstance(ret.value, PipeExpr)
        assert isinstance(ret.value.left, Identifier)
        assert ret.value.left.name == "stream"
        assert isinstance(ret.value.right, CallExpr)
        assert ret.value.right.callee.name == "map"
        assert fuser.stats.streams_fused == 1

    def test_fuse_pipe_map_filter(self) -> None:
        """stream |> map(f) |> filter(g) → stream |> map_filter(f, g)"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=BinaryExpr(left=Identifier(name="x"), op="*", right=IntLiteral(value=2)),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BinaryExpr(left=Identifier(name="y"), op=">", right=IntLiteral(value=5)),
        )

        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(callee=Identifier(name="map"), args=[f_lambda]),
            ),
            right=CallExpr(callee=Identifier(name="filter"), args=[g_lambda]),
        )
        fn = _make_fn(body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, PipeExpr)
        assert isinstance(ret.value.right, CallExpr)
        assert ret.value.right.callee.name == "map_filter"
        assert len(ret.value.right.args) == 2
        assert fuser.stats.streams_fused == 1

    def test_fuse_pipe_filter_filter(self) -> None:
        """stream |> filter(f) |> filter(g) → stream |> filter(compose_and(f, g))"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=BinaryExpr(left=Identifier(name="x"), op=">", right=IntLiteral(value=0)),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BinaryExpr(left=Identifier(name="y"), op="<", right=IntLiteral(value=100)),
        )

        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(callee=Identifier(name="filter"), args=[f_lambda]),
            ),
            right=CallExpr(callee=Identifier(name="filter"), args=[g_lambda]),
        )
        fn = _make_fn(body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, PipeExpr)
        assert isinstance(ret.value.right, CallExpr)
        assert ret.value.right.callee.name == "filter"
        assert fuser.stats.streams_fused == 1

    def test_no_fuse_non_fusable_ops(self) -> None:
        """stream |> map(f) |> take(5) is not fused."""
        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(
                    callee=Identifier(name="map"),
                    args=[LambdaExpr(params=[Param(name="x")], body=Identifier(name="x"))],
                ),
            ),
            right=CallExpr(callee=Identifier(name="take"), args=[IntLiteral(value=5)]),
        )
        fn = _make_fn(body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        assert fuser.stats.streams_fused == 0

    def test_fuse_method_chain_map_map(self) -> None:
        """stream.map(f).map(g) → stream.map(compose(f, g))"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=BinaryExpr(left=Identifier(name="x"), op="*", right=IntLiteral(value=2)),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BinaryExpr(left=Identifier(name="y"), op="+", right=IntLiteral(value=1)),
        )

        chain = MethodCallExpr(
            object=MethodCallExpr(
                object=Identifier(name="stream"),
                method="map",
                args=[f_lambda],
            ),
            method="map",
            args=[g_lambda],
        )
        fn = _make_fn(body=[ReturnStmt(value=chain)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, MethodCallExpr)
        assert ret.value.method == "map"
        assert isinstance(ret.value.object, Identifier)
        assert ret.value.object.name == "stream"
        assert fuser.stats.streams_fused == 1

    def test_fuse_method_chain_map_filter(self) -> None:
        """stream.map(f).filter(g) → stream.map_filter(f, g)"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=Identifier(name="x"),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BoolLiteral(value=True),
        )

        chain = MethodCallExpr(
            object=MethodCallExpr(
                object=Identifier(name="stream"),
                method="map",
                args=[f_lambda],
            ),
            method="filter",
            args=[g_lambda],
        )
        fn = _make_fn(body=[ReturnStmt(value=chain)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, MethodCallExpr)
        assert ret.value.method == "map_filter"
        assert fuser.stats.streams_fused == 1

    def test_fuse_method_chain_filter_filter(self) -> None:
        """stream.filter(f).filter(g) → stream.filter(compose_and(f, g))"""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=BoolLiteral(value=True),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=BoolLiteral(value=False),
        )

        chain = MethodCallExpr(
            object=MethodCallExpr(
                object=Identifier(name="stream"),
                method="filter",
                args=[f_lambda],
            ),
            method="filter",
            args=[g_lambda],
        )
        fn = _make_fn(body=[ReturnStmt(value=chain)])
        prog = _make_program(fn)
        fuser = StreamFuser()
        fuser.run(prog)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, MethodCallExpr)
        assert ret.value.method == "filter"
        assert isinstance(ret.value.args[0], CallExpr)
        assert ret.value.args[0].callee.name == "__compose_and"
        assert fuser.stats.streams_fused == 1


# ===========================================================================
# Task 5: Optimization Levels (-O0 through -O3)
# ===========================================================================


class TestOptimizationLevels:
    """Task 4.4.5 — Expose -O0 through -O3 in mapa."""

    def test_o0_no_optimization(self) -> None:
        """O0: No changes to the program."""
        expr = BinaryExpr(left=IntLiteral(value=3), op="+", right=IntLiteral(value=4))
        fn = _make_fn(body=[ReturnStmt(value=expr)])
        prog = _make_program(fn)
        prog, stats = optimize(prog, OptLevel.O0)
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, BinaryExpr)
        assert stats.total_changes == 0

    def test_o1_constant_folding_only(self) -> None:
        """O1: Constant folding runs, DCE does not."""
        dead_fn = _make_fn(name="dead", body=[ReturnStmt(value=IntLiteral(value=0))])
        main_fn = _make_fn(
            name="main",
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=IntLiteral(value=1),
                        op="+",
                        right=IntLiteral(value=2),
                    )
                )
            ],
        )
        prog = _make_program(dead_fn, main_fn)
        prog, stats = optimize(prog, OptLevel.O1)
        # Constant folding happened
        ret = prog.definitions[1].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        assert ret.value.value == 3
        # Dead function NOT removed at O1
        assert len(prog.definitions) == 2

    def test_o2_includes_dce(self) -> None:
        """O2: Both constant folding and DCE run."""
        dead_fn = _make_fn(name="dead", body=[ReturnStmt(value=IntLiteral(value=0))])
        main_fn = _make_fn(
            name="main",
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=IntLiteral(value=1),
                        op="+",
                        right=IntLiteral(value=2),
                    )
                )
            ],
        )
        prog = _make_program(dead_fn, main_fn)
        prog, stats = optimize(prog, OptLevel.O2)
        # Constant folding happened
        ret = prog.definitions[0].body.stmts[0]
        assert isinstance(ret.value, IntLiteral)
        # Dead function removed
        assert len(prog.definitions) == 1

    def test_o3_includes_stream_fusion(self) -> None:
        """O3: All optimizations including stream fusion."""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=Identifier(name="x"),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=Identifier(name="y"),
        )
        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(callee=Identifier(name="map"), args=[f_lambda]),
            ),
            right=CallExpr(callee=Identifier(name="filter"), args=[g_lambda]),
        )
        fn = _make_fn(name="main", body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        prog, stats = optimize(prog, OptLevel.O3)
        assert stats.streams_fused >= 1

    def test_o2_no_stream_fusion(self) -> None:
        """O2 does NOT run stream fusion."""
        f_lambda = LambdaExpr(
            params=[Param(name="x")],
            body=Identifier(name="x"),
        )
        g_lambda = LambdaExpr(
            params=[Param(name="y")],
            body=Identifier(name="y"),
        )
        pipe = PipeExpr(
            left=PipeExpr(
                left=Identifier(name="stream"),
                right=CallExpr(callee=Identifier(name="map"), args=[f_lambda]),
            ),
            right=CallExpr(callee=Identifier(name="filter"), args=[g_lambda]),
        )
        fn = _make_fn(name="main", body=[ReturnStmt(value=pipe)])
        prog = _make_program(fn)
        prog, stats = optimize(prog, OptLevel.O2)
        assert stats.streams_fused == 0

    def test_pass_stats_aggregate(self) -> None:
        """Stats are properly aggregated across passes."""
        stats = PassStats()
        stats.constants_folded = 5
        stats.dead_stmts_removed = 3
        stats.agents_inlined = 1
        stats.streams_fused = 2
        assert stats.total_changes == 11

    def test_opt_level_ordering(self) -> None:
        """Optimization levels are properly ordered."""
        assert OptLevel.O0 < OptLevel.O1 < OptLevel.O2 < OptLevel.O3
        assert OptLevel.O0 == 0
        assert OptLevel.O3 == 3
