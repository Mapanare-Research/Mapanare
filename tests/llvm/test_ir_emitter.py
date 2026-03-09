"""Tests for Phase 4.2 — LLVM IR Emitter.

Each test class corresponds to a roadmap task in Phase 4.2.
Tests verify the emitted LLVM IR contains correct instructions.
"""

from __future__ import annotations

import pytest
from llvmlite import ir

from mapanare.ast_nodes import (
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    ExprStmt,
    FloatLiteral,
    FnDef,
    ForLoop,
    Identifier,
    IfExpr,
    IntLiteral,
    LetBinding,
    LiteralPattern,
    MatchArm,
    MatchExpr,
    NamedType,
    Param,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    StringLiteral,
    UnaryExpr,
    WildcardPattern,
)
from mapanare.emit_llvm import LLVM_FLOAT, LLVM_INT, LLVMEmitter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fn(
    name: str = "test_fn",
    params: list[Param] | None = None,
    ret: NamedType | None = None,
    body: list[object] | None = None,
) -> FnDef:
    """Helper to build an FnDef AST node."""
    return FnDef(
        name=name,
        params=params or [],
        return_type=ret,
        body=Block(stmts=body or []),
    )


def _emit_single_fn(fn: FnDef) -> tuple[LLVMEmitter, ir.Function]:
    """Emit a single function and return the emitter + LLVM function."""
    emitter = LLVMEmitter()
    func = emitter.emit_fn(fn)
    return emitter, func


def _ir_str(emitter: LLVMEmitter) -> str:
    """Get the full module IR as a string."""
    return str(emitter.module)


# ===========================================================================
# Task 1: fn → LLVM function declarations
# ===========================================================================


class TestFnDeclarations:
    """Task 4.2.1 — fn → LLVM function declarations."""

    def test_void_fn_no_params(self) -> None:
        fn = _make_fn(name="hello")
        emitter, func = _emit_single_fn(fn)
        assert func.name == "hello"
        assert isinstance(func.function_type.return_type, ir.VoidType)
        assert len(func.function_type.args) == 0

    def test_fn_with_int_params(self) -> None:
        fn = _make_fn(
            name="add",
            params=[
                Param(name="a", type_annotation=NamedType(name="Int")),
                Param(name="b", type_annotation=NamedType(name="Int")),
            ],
            ret=NamedType(name="Int"),
        )
        _emitter, func = _emit_single_fn(fn)
        assert func.function_type.return_type == LLVM_INT
        assert len(func.function_type.args) == 2
        assert all(a == LLVM_INT for a in func.function_type.args)

    def test_fn_param_names(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
        )
        _emitter, func = _emit_single_fn(fn)
        assert func.args[0].name == "x"

    def test_fn_with_float_return(self) -> None:
        fn = _make_fn(ret=NamedType(name="Float"))
        _emitter, func = _emit_single_fn(fn)
        assert func.function_type.return_type == LLVM_FLOAT

    def test_fn_appears_in_module(self) -> None:
        fn = _make_fn(name="my_func")
        emitter, _func = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert 'define void @"my_func"()' in ir_str

    def test_fn_with_return_value(self) -> None:
        fn = _make_fn(
            name="get42",
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=IntLiteral(value=42))],
        )
        emitter, _func = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "ret i64 42" in ir_str

    def test_void_fn_implicit_ret_void(self) -> None:
        fn = _make_fn(name="noop")
        emitter, _func = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "ret void" in ir_str

    def test_multiple_fns_in_program(self) -> None:
        prog = Program(
            definitions=[
                _make_fn(name="foo"),
                _make_fn(name="bar"),
            ]
        )
        emitter = LLVMEmitter()
        emitter.emit_program(prog)
        ir_str = _ir_str(emitter)
        assert '@"foo"' in ir_str
        assert '@"bar"' in ir_str


# ===========================================================================
# Task 2: Arithmetic expressions → LLVM arithmetic instructions
# ===========================================================================


class TestArithmeticExpressions:
    """Task 4.2.2 — Arithmetic → LLVM instructions."""

    def _arith_fn(self, op: str, is_float: bool = False) -> tuple[LLVMEmitter, str]:
        """Build fn(a, b) -> a <op> b and return the emitter + IR."""
        ty_name = "Float" if is_float else "Int"
        fn = _make_fn(
            name="arith",
            params=[
                Param(name="a", type_annotation=NamedType(name=ty_name)),
                Param(name="b", type_annotation=NamedType(name=ty_name)),
            ],
            ret=NamedType(name=ty_name),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op=op,
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter, _func = _emit_single_fn(fn)
        return emitter, _ir_str(emitter)

    def test_int_add(self) -> None:
        _, ir_str = self._arith_fn("+")
        assert "add i64" in ir_str

    def test_int_sub(self) -> None:
        _, ir_str = self._arith_fn("-")
        assert "sub i64" in ir_str

    def test_int_mul(self) -> None:
        _, ir_str = self._arith_fn("*")
        assert "mul i64" in ir_str

    def test_int_div(self) -> None:
        _, ir_str = self._arith_fn("/")
        assert "sdiv i64" in ir_str

    def test_int_mod(self) -> None:
        _, ir_str = self._arith_fn("%")
        assert "srem i64" in ir_str

    def test_float_add(self) -> None:
        _, ir_str = self._arith_fn("+", is_float=True)
        assert "fadd double" in ir_str

    def test_float_sub(self) -> None:
        _, ir_str = self._arith_fn("-", is_float=True)
        assert "fsub double" in ir_str

    def test_float_mul(self) -> None:
        _, ir_str = self._arith_fn("*", is_float=True)
        assert "fmul double" in ir_str

    def test_float_div(self) -> None:
        _, ir_str = self._arith_fn("/", is_float=True)
        assert "fdiv double" in ir_str

    def test_float_mod(self) -> None:
        _, ir_str = self._arith_fn("%", is_float=True)
        assert "frem double" in ir_str

    def test_unary_neg_int(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=UnaryExpr(op="-", operand=Identifier(name="x")))],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "sub i64 0," in ir_str

    def test_unary_neg_float(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Float"))],
            ret=NamedType(name="Float"),
            body=[ReturnStmt(value=UnaryExpr(op="-", operand=Identifier(name="x")))],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "fneg double" in ir_str

    def test_nested_arithmetic(self) -> None:
        """Test (a + b) * c."""
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="Int")),
                Param(name="b", type_annotation=NamedType(name="Int")),
                Param(name="c", type_annotation=NamedType(name="Int")),
            ],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=BinaryExpr(
                            left=Identifier(name="a"),
                            op="+",
                            right=Identifier(name="b"),
                        ),
                        op="*",
                        right=Identifier(name="c"),
                    )
                )
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "add i64" in ir_str
        assert "mul i64" in ir_str


# ===========================================================================
# Task 3: Boolean expressions → LLVM comparison instructions
# ===========================================================================


class TestBooleanExpressions:
    """Task 4.2.3 — Boolean → LLVM comparison instructions."""

    def _cmp_fn(self, op: str, is_float: bool = False) -> str:
        ty_name = "Float" if is_float else "Int"
        fn = _make_fn(
            name="cmp",
            params=[
                Param(name="a", type_annotation=NamedType(name=ty_name)),
                Param(name="b", type_annotation=NamedType(name=ty_name)),
            ],
            ret=NamedType(name="Bool"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op=op,
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        return _ir_str(emitter)

    def test_int_eq(self) -> None:
        assert "icmp eq" in self._cmp_fn("==")

    def test_int_ne(self) -> None:
        assert "icmp ne" in self._cmp_fn("!=")

    def test_int_lt(self) -> None:
        assert "icmp slt" in self._cmp_fn("<")

    def test_int_le(self) -> None:
        assert "icmp sle" in self._cmp_fn("<=")

    def test_int_gt(self) -> None:
        assert "icmp sgt" in self._cmp_fn(">")

    def test_int_ge(self) -> None:
        assert "icmp sge" in self._cmp_fn(">=")

    def test_float_eq(self) -> None:
        assert "fcmp oeq" in self._cmp_fn("==", is_float=True)

    def test_float_lt(self) -> None:
        assert "fcmp olt" in self._cmp_fn("<", is_float=True)

    def test_float_gt(self) -> None:
        assert "fcmp ogt" in self._cmp_fn(">", is_float=True)

    def test_logical_and(self) -> None:
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="Bool")),
                Param(name="b", type_annotation=NamedType(name="Bool")),
            ],
            ret=NamedType(name="Bool"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op="&&",
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        assert "and i1" in _ir_str(emitter)

    def test_logical_or(self) -> None:
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="Bool")),
                Param(name="b", type_annotation=NamedType(name="Bool")),
            ],
            ret=NamedType(name="Bool"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op="||",
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        assert "or i1" in _ir_str(emitter)

    def test_logical_not(self) -> None:
        fn = _make_fn(
            params=[Param(name="a", type_annotation=NamedType(name="Bool"))],
            ret=NamedType(name="Bool"),
            body=[ReturnStmt(value=UnaryExpr(op="!", operand=Identifier(name="a")))],
        )
        emitter, _ = _emit_single_fn(fn)
        assert "xor i1" in _ir_str(emitter)


# ===========================================================================
# Task 4: if/else → basic blocks + branch instructions
# ===========================================================================


class TestIfElse:
    """Task 4.2.4 — if/else → basic blocks + branch."""

    def test_if_then_else_blocks(self) -> None:
        fn = _make_fn(
            params=[
                Param(name="x", type_annotation=NamedType(name="Bool")),
            ],
            ret=NamedType(name="Int"),
            body=[
                ExprStmt(
                    expr=IfExpr(
                        condition=Identifier(name="x"),
                        then_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=1))]),
                        else_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=0))]),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "if.then" in ir_str
        assert "if.else" in ir_str
        assert "if.merge" in ir_str

    def test_if_cbranch(self) -> None:
        fn = _make_fn(
            params=[Param(name="cond", type_annotation=NamedType(name="Bool"))],
            ret=NamedType(name="Int"),
            body=[
                ExprStmt(
                    expr=IfExpr(
                        condition=Identifier(name="cond"),
                        then_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=1))]),
                        else_block=Block(stmts=[ReturnStmt(value=IntLiteral(value=2))]),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "br i1" in ir_str

    def test_if_phi_node(self) -> None:
        """If both branches return values, a phi node should merge them."""
        fn = _make_fn(
            params=[Param(name="flag", type_annotation=NamedType(name="Bool"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=IfExpr(
                        condition=Identifier(name="flag"),
                        then_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=10))]),
                        else_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=20))]),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "phi" in ir_str and "i64" in ir_str

    def test_if_without_else(self) -> None:
        fn = _make_fn(
            params=[Param(name="flag", type_annotation=NamedType(name="Bool"))],
            body=[
                ExprStmt(
                    expr=IfExpr(
                        condition=Identifier(name="flag"),
                        then_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=1))]),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "br i1" in ir_str
        assert "if.then" in ir_str

    def test_if_else_if_chain(self) -> None:
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="Bool")),
                Param(name="b", type_annotation=NamedType(name="Bool")),
            ],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=IfExpr(
                        condition=Identifier(name="a"),
                        then_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=1))]),
                        else_block=IfExpr(
                            condition=Identifier(name="b"),
                            then_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=2))]),
                            else_block=Block(stmts=[ExprStmt(expr=IntLiteral(value=3))]),
                        ),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        # Should have multiple br i1 (two conditions)
        assert ir_str.count("br i1") >= 2


# ===========================================================================
# Task 5: for/in → LLVM loop with phi nodes
# ===========================================================================


class TestForLoop:
    """Task 4.2.5 — for/in → LLVM loop with phi nodes."""

    def test_for_range_has_phi(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                    ),
                    body=Block(stmts=[ExprStmt(expr=Identifier(name="i"))]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "phi" in ir_str and "i64" in ir_str

    def test_for_loop_blocks(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=5),
                    ),
                    body=Block(stmts=[]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "for.header" in ir_str
        assert "for.body" in ir_str
        assert "for.exit" in ir_str

    def test_for_loop_condition(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                        inclusive=False,
                    ),
                    body=Block(stmts=[]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        # Exclusive range: i < end → icmp slt
        assert "icmp slt" in ir_str

    def test_for_loop_inclusive(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                        inclusive=True,
                    ),
                    body=Block(stmts=[]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        # Inclusive range: i <= end → icmp sle
        assert "icmp sle" in ir_str

    def test_for_loop_increment(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=5),
                    ),
                    body=Block(stmts=[]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        # Should have an add for the counter increment
        assert "for.next" in ir_str

    def test_for_loop_back_edge(self) -> None:
        """The body should branch back to the header."""
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=3),
                    ),
                    body=Block(stmts=[]),
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        # The for.body block should branch to for.header
        assert 'br label %"for.header"' in ir_str

    def test_for_non_range_raises(self) -> None:
        fn = _make_fn(
            body=[
                ForLoop(
                    var_name="i",
                    iterable=Identifier(name="items"),
                    body=Block(stmts=[]),
                ),
            ],
        )
        with pytest.raises(NotImplementedError, match="range"):
            _emit_single_fn(fn)


# ===========================================================================
# Task 6: Function calls → LLVM call instructions
# ===========================================================================


class TestFunctionCalls:
    """Task 4.2.6 — function calls → LLVM call instructions."""

    def test_simple_call(self) -> None:
        """Call a previously defined function."""
        emitter = LLVMEmitter()
        # Define callee first
        callee = _make_fn(
            name="double_it",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="x"),
                        op="*",
                        right=IntLiteral(value=2),
                    )
                )
            ],
        )
        emitter.emit_fn(callee)

        # Define caller
        caller = _make_fn(
            name="main",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=CallExpr(
                        callee=Identifier(name="double_it"),
                        args=[IntLiteral(value=21)],
                    )
                )
            ],
        )
        emitter.emit_fn(caller)
        ir_str = str(emitter.module)
        assert 'call i64 @"double_it"(i64 21)' in ir_str

    def test_call_with_multiple_args(self) -> None:
        emitter = LLVMEmitter()
        add_fn = _make_fn(
            name="add",
            params=[
                Param(name="a", type_annotation=NamedType(name="Int")),
                Param(name="b", type_annotation=NamedType(name="Int")),
            ],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op="+",
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter.emit_fn(add_fn)

        caller = _make_fn(
            name="use_add",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=CallExpr(
                        callee=Identifier(name="add"),
                        args=[IntLiteral(value=3), IntLiteral(value=4)],
                    )
                )
            ],
        )
        emitter.emit_fn(caller)
        ir_str = str(emitter.module)
        assert 'call i64 @"add"(i64 3, i64 4)' in ir_str

    def test_call_undefined_fn_raises(self) -> None:
        fn = _make_fn(
            body=[
                ExprStmt(
                    expr=CallExpr(
                        callee=Identifier(name="nonexistent"),
                        args=[],
                    )
                )
            ],
        )
        with pytest.raises(NameError, match="Undefined function"):
            _emit_single_fn(fn)

    def test_nested_calls(self) -> None:
        """f(g(x))"""
        emitter = LLVMEmitter()
        g_fn = _make_fn(
            name="g",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=Identifier(name="x"))],
        )
        emitter.emit_fn(g_fn)

        f_fn = _make_fn(
            name="f",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=Identifier(name="x"))],
        )
        emitter.emit_fn(f_fn)

        main_fn = _make_fn(
            name="main",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=CallExpr(
                        callee=Identifier(name="f"),
                        args=[
                            CallExpr(
                                callee=Identifier(name="g"),
                                args=[IntLiteral(value=5)],
                            )
                        ],
                    )
                )
            ],
        )
        emitter.emit_fn(main_fn)
        ir_str = str(emitter.module)
        assert 'call i64 @"g"(i64 5)' in ir_str
        assert 'call i64 @"f"' in ir_str


# ===========================================================================
# Task 7: let → stack alloca + store/load
# ===========================================================================


class TestLetBindings:
    """Task 4.2.7 — let → alloca + store/load."""

    def test_let_alloca(self) -> None:
        fn = _make_fn(
            ret=NamedType(name="Int"),
            body=[
                LetBinding(name="x", value=IntLiteral(value=42)),
                ReturnStmt(value=Identifier(name="x")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "alloca i64" in ir_str
        assert "store i64 42" in ir_str
        assert "load i64" in ir_str

    def test_let_multiple_vars(self) -> None:
        fn = _make_fn(
            ret=NamedType(name="Int"),
            body=[
                LetBinding(name="a", value=IntLiteral(value=1)),
                LetBinding(name="b", value=IntLiteral(value=2)),
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op="+",
                        right=Identifier(name="b"),
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "store i64 1" in ir_str
        assert "store i64 2" in ir_str
        assert "add i64" in ir_str

    def test_let_float(self) -> None:
        fn = _make_fn(
            ret=NamedType(name="Float"),
            body=[
                LetBinding(name="pi", value=FloatLiteral(value=3.14)),
                ReturnStmt(value=Identifier(name="pi")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "alloca double" in ir_str

    def test_let_bool(self) -> None:
        fn = _make_fn(
            ret=NamedType(name="Bool"),
            body=[
                LetBinding(name="flag", value=BoolLiteral(value=True)),
                ReturnStmt(value=Identifier(name="flag")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "alloca i1" in ir_str
        assert "store i1 1" in ir_str

    def test_mut_assign(self) -> None:
        """Mutable variable with reassignment."""
        fn = _make_fn(
            ret=NamedType(name="Int"),
            body=[
                LetBinding(name="x", mutable=True, value=IntLiteral(value=0)),
                ExprStmt(
                    expr=AssignExpr(
                        target=Identifier(name="x"),
                        op="=",
                        value=IntLiteral(value=10),
                    )
                ),
                ReturnStmt(value=Identifier(name="x")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "store i64 0" in ir_str
        assert "store i64 10" in ir_str

    def test_compound_assign(self) -> None:
        fn = _make_fn(
            ret=NamedType(name="Int"),
            body=[
                LetBinding(name="x", mutable=True, value=IntLiteral(value=5)),
                ExprStmt(
                    expr=AssignExpr(
                        target=Identifier(name="x"),
                        op="+=",
                        value=IntLiteral(value=3),
                    )
                ),
                ReturnStmt(value=Identifier(name="x")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "add i64" in ir_str

    def test_undefined_var_raises(self) -> None:
        fn = _make_fn(
            body=[
                ReturnStmt(value=Identifier(name="undefined_var")),
            ],
        )
        with pytest.raises(NameError, match="Undefined variable"):
            _emit_single_fn(fn)


# ===========================================================================
# Task 8: match → LLVM switch + conditional branches
# ===========================================================================


class TestMatch:
    """Task 4.2.8 — match → LLVM switch + conditional branches."""

    def test_match_switch_instruction(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=1)),
                                body=IntLiteral(value=10),
                            ),
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=2)),
                                body=IntLiteral(value=20),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=IntLiteral(value=0),
                            ),
                        ],
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "switch i64" in ir_str

    def test_match_arm_blocks(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=1)),
                                body=IntLiteral(value=100),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=IntLiteral(value=0),
                            ),
                        ],
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "match.arm" in ir_str
        assert "match.default" in ir_str
        assert "match.merge" in ir_str

    def test_match_phi_node(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=0)),
                                body=IntLiteral(value=42),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=IntLiteral(value=99),
                            ),
                        ],
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "phi" in ir_str and "i64" in ir_str

    def test_match_case_values(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=5)),
                                body=IntLiteral(value=50),
                            ),
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=10)),
                                body=IntLiteral(value=100),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=IntLiteral(value=0),
                            ),
                        ],
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "i64 5" in ir_str
        assert "i64 10" in ir_str

    def test_match_with_block_body(self) -> None:
        fn = _make_fn(
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=1)),
                                body=Block(
                                    stmts=[
                                        LetBinding(name="y", value=IntLiteral(value=10)),
                                        ExprStmt(expr=Identifier(name="y")),
                                    ]
                                ),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=IntLiteral(value=0),
                            ),
                        ],
                    )
                ),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "switch i64" in ir_str
        assert "match.arm" in ir_str


# ===========================================================================
# Task 9: |> → inlined LLVM call chain
# ===========================================================================


class TestPipeOperator:
    """Task 4.2.9 — |> → inlined LLVM call chain."""

    def test_simple_pipe(self) -> None:
        """x |> f → f(x)"""
        emitter = LLVMEmitter()
        f_fn = _make_fn(
            name="f",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=Identifier(name="x"))],
        )
        emitter.emit_fn(f_fn)

        main = _make_fn(
            name="main",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=PipeExpr(
                        left=IntLiteral(value=42),
                        right=Identifier(name="f"),
                    )
                ),
            ],
        )
        emitter.emit_fn(main)
        ir_str = str(emitter.module)
        assert 'call i64 @"f"(i64 42)' in ir_str

    def test_chained_pipe(self) -> None:
        """x |> f |> g → g(f(x))"""
        emitter = LLVMEmitter()
        f_fn = _make_fn(
            name="f",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=Identifier(name="x"))],
        )
        emitter.emit_fn(f_fn)

        g_fn = _make_fn(
            name="g",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            ret=NamedType(name="Int"),
            body=[ReturnStmt(value=Identifier(name="x"))],
        )
        emitter.emit_fn(g_fn)

        main = _make_fn(
            name="main",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=PipeExpr(
                        left=PipeExpr(
                            left=IntLiteral(value=5),
                            right=Identifier(name="f"),
                        ),
                        right=Identifier(name="g"),
                    )
                ),
            ],
        )
        emitter.emit_fn(main)
        ir_str = str(emitter.module)
        assert 'call i64 @"f"(i64 5)' in ir_str
        assert 'call i64 @"g"' in ir_str

    def test_pipe_with_extra_args(self) -> None:
        """x |> f(y) → f(x, y)"""
        emitter = LLVMEmitter()
        add_fn = _make_fn(
            name="add",
            params=[
                Param(name="a", type_annotation=NamedType(name="Int")),
                Param(name="b", type_annotation=NamedType(name="Int")),
            ],
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        left=Identifier(name="a"),
                        op="+",
                        right=Identifier(name="b"),
                    )
                )
            ],
        )
        emitter.emit_fn(add_fn)

        main = _make_fn(
            name="main",
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(
                    value=PipeExpr(
                        left=IntLiteral(value=10),
                        right=CallExpr(
                            callee=Identifier(name="add"),
                            args=[IntLiteral(value=5)],
                        ),
                    )
                ),
            ],
        )
        emitter.emit_fn(main)
        ir_str = str(emitter.module)
        assert 'call i64 @"add"(i64 10, i64 5)' in ir_str

    def test_pipe_undefined_fn_raises(self) -> None:
        fn = _make_fn(
            body=[
                ExprStmt(
                    expr=PipeExpr(
                        left=IntLiteral(value=1),
                        right=Identifier(name="missing"),
                    )
                ),
            ],
        )
        with pytest.raises(NameError, match="Undefined function"):
            _emit_single_fn(fn)


# ===========================================================================
# Integration tests
# ===========================================================================


class TestIREmitterIntegration:
    """Cross-cutting integration tests."""

    def test_string_literal_struct(self) -> None:
        fn = _make_fn(
            name="get_str",
            body=[
                LetBinding(name="s", value=StringLiteral(value="hello")),
                ExprStmt(expr=Identifier(name="s")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "private constant" in ir_str or "@str" in ir_str
        assert "insertvalue" in ir_str

    def test_full_program_add(self) -> None:
        prog = Program(
            definitions=[
                _make_fn(
                    name="add",
                    params=[
                        Param(name="a", type_annotation=NamedType(name="Int")),
                        Param(name="b", type_annotation=NamedType(name="Int")),
                    ],
                    ret=NamedType(name="Int"),
                    body=[
                        ReturnStmt(
                            value=BinaryExpr(
                                left=Identifier(name="a"),
                                op="+",
                                right=Identifier(name="b"),
                            )
                        )
                    ],
                ),
                _make_fn(
                    name="main",
                    ret=NamedType(name="Int"),
                    body=[
                        ReturnStmt(
                            value=CallExpr(
                                callee=Identifier(name="add"),
                                args=[IntLiteral(value=3), IntLiteral(value=4)],
                            )
                        )
                    ],
                ),
            ]
        )
        emitter = LLVMEmitter()
        module = emitter.emit_program(prog)
        ir_str = str(module)
        assert 'define i64 @"add"(i64 %"a", i64 %"b")' in ir_str
        assert 'define i64 @"main"()' in ir_str
        assert 'call i64 @"add"(i64 3, i64 4)' in ir_str

    def test_loop_with_accumulator(self) -> None:
        """Sum 0..5 using a mutable accumulator."""
        fn = _make_fn(
            name="sum5",
            ret=NamedType(name="Int"),
            body=[
                LetBinding(name="total", mutable=True, value=IntLiteral(value=0)),
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=5),
                    ),
                    body=Block(
                        stmts=[
                            ExprStmt(
                                expr=AssignExpr(
                                    target=Identifier(name="total"),
                                    op="+=",
                                    value=Identifier(name="i"),
                                )
                            ),
                        ]
                    ),
                ),
                ReturnStmt(value=Identifier(name="total")),
            ],
        )
        emitter, _ = _emit_single_fn(fn)
        ir_str = _ir_str(emitter)
        assert "phi" in ir_str and "i64" in ir_str
        assert "for.header" in ir_str
        assert "add i64" in ir_str


# =====================================================================
# Phase 5.1: Tensor operations — LLVM IR emission
# =====================================================================


class TestTensorOpsIR:
    """Test LLVM IR emission for tensor operations."""

    def test_matmul_declares_runtime_fn(self) -> None:
        """@ operator declares __mapanare_matmul in the module."""
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        emitter._declare_tensor_runtime("__mapanare_matmul")
        ir_str = str(emitter.module)
        assert "__mapanare_matmul" in ir_str
        assert "i8*" in ir_str  # opaque pointer args

    def test_tensor_runtime_declarations(self) -> None:
        """Tensor runtime functions are correctly declared."""
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        # Manually declare some tensor runtime functions
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_add")
        assert fn.name == "__mapanare_tensor_add"
        # Second call should return the same function
        fn2 = emitter._declare_tensor_runtime("__mapanare_tensor_add")
        assert fn is fn2

    def test_tensor_alloc_declaration(self) -> None:
        """__mapanare_tensor_alloc is declared with correct signature."""
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_alloc")
        assert fn.name == "__mapanare_tensor_alloc"
        assert len(fn.args) == 3  # ndim, shape_ptr, elem_size

    def test_tensor_free_declaration(self) -> None:
        """__mapanare_tensor_free is declared with void return."""
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_free")
        assert fn.name == "__mapanare_tensor_free"
        assert isinstance(fn.function_type.return_type, ir.VoidType)

    def test_tensor_shape_eq_declaration(self) -> None:
        """__mapanare_tensor_shape_eq returns i1."""
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_shape_eq")
        assert fn.name == "__mapanare_tensor_shape_eq"
        assert fn.function_type.return_type == ir.IntType(1)
