"""Tests for the Python emitter -- Phase 2.4."""

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
    CharLiteral,
    ConstructExpr,
    ConstructorPattern,
    EnumDef,
    EnumVariant,
    ErrExpr,
    ErrorPropExpr,
    ExportDef,
    ExprStmt,
    FieldAccessExpr,
    FieldInit,
    FloatLiteral,
    FnDef,
    ForLoop,
    GenericType,
    Identifier,
    IdentPattern,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    LiteralPattern,
    MatchArm,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    OkExpr,
    Param,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalDecl,
    SignalExpr,
    SomeExpr,
    SpawnExpr,
    StreamDecl,
    StringLiteral,
    StructDef,
    StructField,
    SyncExpr,
    TypeAlias,
    UnaryExpr,
    WildcardPattern,
)
from mapanare.emit_python import PythonEmitter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def emit(program: Program) -> str:
    return PythonEmitter().emit(program)


def emit_with(defns: list) -> str:
    return emit(Program(definitions=defns))


def _fn(
    name: str = "test_fn",
    params: list | None = None,
    body_stmts: list | None = None,
    return_type: NamedType | None = None,
) -> FnDef:
    return FnDef(
        name=name,
        params=params or [],
        return_type=return_type,
        body=Block(stmts=body_stmts or []),
    )


# ---------------------------------------------------------------------------
# Task 1: agent → async class with asyncio task
# ---------------------------------------------------------------------------


class TestAgentEmission:
    def test_basic_agent_class(self) -> None:
        agent = AgentDef(
            name="Greeter",
            inputs=[AgentInput(name="name", type_annotation=NamedType(name="String"))],
            outputs=[AgentOutput(name="greeting", type_annotation=NamedType(name="String"))],
            state=[],
            methods=[
                FnDef(
                    name="handle",
                    params=[
                        Param(
                            name="name",
                            type_annotation=NamedType(name="String"),
                        )
                    ],
                    return_type=NamedType(name="String"),
                    body=Block(
                        stmts=[
                            ReturnStmt(
                                value=BinaryExpr(
                                    left=StringLiteral(value="Hello, "),
                                    op="+",
                                    right=Identifier(name="name"),
                                )
                            )
                        ]
                    ),
                )
            ],
        )
        code = emit_with([agent])
        assert "class Greeter(AgentBase):" in code
        assert "def __init__(self)" in code
        assert 'self._register_input("name")' in code
        assert 'self._register_output("greeting")' in code
        assert "async def handle(self, name: str)" in code

    def test_agent_with_state(self) -> None:
        agent = AgentDef(
            name="Counter",
            inputs=[AgentInput(name="increment", type_annotation=NamedType(name="Int"))],
            outputs=[AgentOutput(name="count", type_annotation=NamedType(name="Int"))],
            state=[LetBinding(name="state", mutable=True, value=IntLiteral(value=0))],
            methods=[],
        )
        code = emit_with([agent])
        assert "self.state = 0" in code

    def test_agent_imports_asyncio(self) -> None:
        agent = AgentDef(
            name="Simple",
            inputs=[AgentInput(name="x", type_annotation=NamedType(name="Int"))],
            outputs=[],
            state=[],
            methods=[],
        )
        code = emit_with([agent])
        assert "import asyncio" in code
        assert "from runtime.agent import AgentBase" in code


# ---------------------------------------------------------------------------
# Task 2: signal → Signal wrapper class
# ---------------------------------------------------------------------------


class TestSignalEmission:
    def test_signal_value(self) -> None:
        fn = _fn(
            body_stmts=[
                SignalDecl(name="count", value=IntLiteral(value=0)),
            ]
        )
        code = emit_with([fn])
        assert "count = Signal(0)" in code
        assert "from runtime.signal import Signal" in code

    def test_signal_computed(self) -> None:
        fn = _fn(
            body_stmts=[
                SignalDecl(
                    name="doubled",
                    value=BinaryExpr(
                        left=FieldAccessExpr(
                            object=Identifier(name="count"),
                            field_name="value",
                        ),
                        op="*",
                        right=IntLiteral(value=2),
                    ),
                    is_computed=True,
                ),
            ]
        )
        code = emit_with([fn])
        assert "doubled = Signal(computed=lambda: " in code

    def test_signal_expr_inline(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="s",
                    value=SignalExpr(value=IntLiteral(value=42)),
                ),
            ]
        )
        code = emit_with([fn])
        assert "s = Signal(42)" in code

    def test_signal_computed_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="c",
                    value=SignalExpr(
                        value=Identifier(name="x"),
                        is_computed=True,
                    ),
                ),
            ]
        )
        code = emit_with([fn])
        assert "c = Signal(computed=lambda: x)" in code


# ---------------------------------------------------------------------------
# Task 3: stream → Python AsyncGenerator
# ---------------------------------------------------------------------------


class TestStreamEmission:
    def test_stream_decl(self) -> None:
        fn = _fn(
            body_stmts=[
                StreamDecl(
                    name="nums",
                    value=ListLiteral(elements=[IntLiteral(value=1), IntLiteral(value=2)]),
                ),
            ]
        )
        code = emit_with([fn])
        assert "nums = Stream.from_iter([1, 2])" in code
        assert "from runtime.stream import Stream" in code


# ---------------------------------------------------------------------------
# Task 4: pipe → async function composing agents
# ---------------------------------------------------------------------------


class TestPipeEmission:
    def test_pipe_definition(self) -> None:
        pipe = PipeDef(
            name="MyPipeline",
            stages=[Identifier(name="AgentA"), Identifier(name="AgentB")],
        )
        # Need a dummy agent to trigger agent imports
        agent = AgentDef(
            name="AgentA",
            inputs=[AgentInput(name="x", type_annotation=NamedType(name="Int"))],
            outputs=[AgentOutput(name="y", type_annotation=NamedType(name="Int"))],
        )
        code = emit_with([agent, pipe])
        assert "async def MyPipeline(input_value):" in code
        assert "AgentA.spawn()" in code
        assert "AgentB.spawn()" in code
        assert "return _val" in code

    def test_empty_pipe(self) -> None:
        pipe = PipeDef(name="Empty", stages=[])
        code = emit_with([pipe])
        assert "return input_value" in code


# ---------------------------------------------------------------------------
# Task 5: spawn → asyncio.create_task()
# ---------------------------------------------------------------------------


class TestSpawnEmission:
    def test_spawn_expr(self) -> None:
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    LetBinding(
                        name="handle",
                        value=SpawnExpr(callee=Identifier(name="Greeter"), args=[]),
                    ),
                ]
            ),
        )
        code = emit_with([fn])
        assert "handle = await Greeter.spawn()" in code

    def test_spawn_makes_fn_async(self) -> None:
        fn = FnDef(
            name="run",
            params=[],
            body=Block(
                stmts=[
                    LetBinding(
                        name="h",
                        value=SpawnExpr(callee=Identifier(name="Agent"), args=[]),
                    ),
                ]
            ),
        )
        code = emit_with([fn])
        assert "async def run" in code


# ---------------------------------------------------------------------------
# Task 6: sync → await
# ---------------------------------------------------------------------------


class TestSyncEmission:
    def test_sync_expr(self) -> None:
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    LetBinding(
                        name="result",
                        value=SyncExpr(
                            expr=FieldAccessExpr(
                                object=Identifier(name="agent"),
                                field_name="output",
                            )
                        ),
                    ),
                ]
            ),
        )
        code = emit_with([fn])
        assert "result = await agent.output.receive()" in code

    def test_sync_as_statement(self) -> None:
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    ExprStmt(expr=SyncExpr(expr=Identifier(name="future"))),
                ]
            ),
        )
        code = emit_with([fn])
        assert "await future" in code


# ---------------------------------------------------------------------------
# Task 7: |> operator → chained function calls
# ---------------------------------------------------------------------------


class TestPipeExprEmission:
    def test_simple_pipe(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="result",
                    value=PipeExpr(
                        left=Identifier(name="data"),
                        right=Identifier(name="process"),
                    ),
                ),
            ]
        )
        code = emit_with([fn])
        assert "result = process(data)" in code

    def test_pipe_chain(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="result",
                    value=PipeExpr(
                        left=PipeExpr(
                            left=Identifier(name="data"),
                            right=Identifier(name="tokenize"),
                        ),
                        right=Identifier(name="classify"),
                    ),
                ),
            ]
        )
        code = emit_with([fn])
        assert "result = classify(tokenize(data))" in code

    def test_pipe_with_args(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="result",
                    value=PipeExpr(
                        left=Identifier(name="x"),
                        right=CallExpr(
                            callee=Identifier(name="add"),
                            args=[IntLiteral(value=1)],
                        ),
                    ),
                ),
            ]
        )
        code = emit_with([fn])
        assert "result = add(x, 1)" in code


# ---------------------------------------------------------------------------
# Task 8: Option<T> → Python Optional[T]
# ---------------------------------------------------------------------------


class TestOptionEmission:
    def test_option_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="x",
                    type_annotation=GenericType(name="Option", args=[NamedType(name="Int")]),
                    value=NoneLiteral(),
                ),
            ]
        )
        code = emit_with([fn])
        assert "x: int | None = None" in code

    def test_some_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="x",
                    value=SomeExpr(value=IntLiteral(value=42)),
                ),
            ]
        )
        code = emit_with([fn])
        assert "x = Some(42)" in code
        assert "from runtime.result import Some" in code

    def test_none_literal(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(name="x", value=NoneLiteral()),
            ]
        )
        code = emit_with([fn])
        assert "x = None" in code


# ---------------------------------------------------------------------------
# Task 9: Result<T, E> → Result class in runtime
# ---------------------------------------------------------------------------


class TestResultEmission:
    def test_ok_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                ReturnStmt(value=OkExpr(value=IntLiteral(value=42))),
            ]
        )
        code = emit_with([fn])
        assert "return Ok(42)" in code
        assert "from runtime.result import Ok, Err" in code

    def test_err_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                ReturnStmt(
                    value=ErrExpr(value=StringLiteral(value="fail")),
                ),
            ]
        )
        code = emit_with([fn])
        assert "return Err('fail')" in code

    def test_error_propagation(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="val",
                    value=ErrorPropExpr(
                        expr=CallExpr(
                            callee=Identifier(name="parse"),
                            args=[Identifier(name="s")],
                        )
                    ),
                ),
            ]
        )
        code = emit_with([fn])
        assert "unwrap_or_return(parse(s))" in code
        assert "try:" in code
        assert "except _EarlyReturn" in code

    def test_result_type_annotation(self) -> None:
        fn = FnDef(
            name="parse",
            params=[Param(name="s", type_annotation=NamedType(name="String"))],
            return_type=GenericType(
                name="Result",
                args=[NamedType(name="Int"), NamedType(name="String")],
            ),
            body=Block(stmts=[ReturnStmt(value=OkExpr(value=IntLiteral(value=0)))]),
        )
        code = emit_with([fn])
        assert "Ok[int] | Err[str]" in code


# ---------------------------------------------------------------------------
# Task 10: Emitter unit tests for every AST node type
# ---------------------------------------------------------------------------


class TestLiteralEmission:
    def test_int_literal(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=IntLiteral(value=42))])
        code = emit_with([fn])
        assert "42" in code

    def test_float_literal(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=FloatLiteral(value=3.14))])
        code = emit_with([fn])
        assert "3.14" in code

    def test_string_literal(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=StringLiteral(value="hello"))])
        code = emit_with([fn])
        assert "'hello'" in code

    def test_char_literal(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=CharLiteral(value="a"))])
        code = emit_with([fn])
        assert "'a'" in code

    def test_bool_literal_true(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=BoolLiteral(value=True))])
        code = emit_with([fn])
        assert "True" in code

    def test_bool_literal_false(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=BoolLiteral(value=False))])
        code = emit_with([fn])
        assert "False" in code

    def test_none_literal(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=NoneLiteral())])
        code = emit_with([fn])
        assert "None" in code

    def test_list_literal(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(expr=ListLiteral(elements=[IntLiteral(value=1), IntLiteral(value=2)]))
            ]
        )
        code = emit_with([fn])
        assert "[1, 2]" in code


class TestExpressionEmission:
    def test_binary_add(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=BinaryExpr(
                        left=IntLiteral(value=1),
                        op="+",
                        right=IntLiteral(value=2),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "(1 + 2)" in code

    def test_binary_logical_and(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=BinaryExpr(
                        left=BoolLiteral(value=True),
                        op="&&",
                        right=BoolLiteral(value=False),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "(True and False)" in code

    def test_binary_logical_or(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=BinaryExpr(
                        left=BoolLiteral(value=True),
                        op="||",
                        right=BoolLiteral(value=False),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "(True or False)" in code

    def test_unary_negation(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=UnaryExpr(op="-", operand=IntLiteral(value=5)))])
        code = emit_with([fn])
        assert "(-5)" in code

    def test_unary_not(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=UnaryExpr(op="!", operand=BoolLiteral(value=True)))])
        code = emit_with([fn])
        assert "(not True)" in code

    def test_function_call(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=CallExpr(
                        callee=Identifier(name="print"),
                        args=[StringLiteral(value="hi")],
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "print('hi')" in code

    def test_method_call(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=MethodCallExpr(
                        object=Identifier(name="list"),
                        method="append",
                        args=[IntLiteral(value=1)],
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "list.append(1)" in code

    def test_field_access(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(expr=FieldAccessExpr(object=Identifier(name="point"), field_name="x"))
            ]
        )
        code = emit_with([fn])
        assert "point.x" in code

    def test_namespace_access(self) -> None:
        fn = _fn(body_stmts=[ExprStmt(expr=NamespaceAccessExpr(namespace="Math", member="sqrt"))])
        code = emit_with([fn])
        assert "Math.sqrt" in code

    def test_index_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=IndexExpr(
                        object=Identifier(name="arr"),
                        index=IntLiteral(value=0),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "arr[0]" in code

    def test_range_exclusive(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                        inclusive=False,
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "range(0, 10)" in code

    def test_range_inclusive(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                        inclusive=True,
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "range(0, 10 + 1)" in code

    def test_lambda_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="f",
                    value=LambdaExpr(
                        params=[Param(name="x")],
                        body=BinaryExpr(
                            left=Identifier(name="x"),
                            op="+",
                            right=IntLiteral(value=1),
                        ),
                    ),
                )
            ]
        )
        code = emit_with([fn])
        assert "f = lambda x: (x + 1)" in code

    def test_construct_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="p",
                    value=ConstructExpr(
                        name="Point",
                        fields=[
                            FieldInit(name="x", value=FloatLiteral(value=1.0)),
                            FieldInit(name="y", value=FloatLiteral(value=2.0)),
                        ],
                    ),
                )
            ]
        )
        code = emit_with([fn])
        assert "p = Point(x=1.0, y=2.0)" in code

    def test_assign_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=AssignExpr(
                        target=Identifier(name="x"),
                        op="=",
                        value=IntLiteral(value=5),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "x = 5" in code

    def test_assign_compound(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=AssignExpr(
                        target=Identifier(name="x"),
                        op="+=",
                        value=IntLiteral(value=1),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "x += 1" in code

    def test_send_expr(self) -> None:
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    ExprStmt(
                        expr=SendExpr(
                            target=FieldAccessExpr(
                                object=Identifier(name="agent"),
                                field_name="input",
                            ),
                            value=StringLiteral(value="hello"),
                        )
                    )
                ]
            ),
        )
        code = emit_with([fn])
        assert "await agent.input.send('hello')" in code


class TestStatementEmission:
    def test_let_binding(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(name="x", value=IntLiteral(value=42)),
            ]
        )
        code = emit_with([fn])
        assert "x = 42" in code

    def test_let_with_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="x",
                    type_annotation=NamedType(name="Int"),
                    value=IntLiteral(value=42),
                ),
            ]
        )
        code = emit_with([fn])
        assert "x: int = 42" in code

    def test_return_stmt(self) -> None:
        fn = _fn(
            body_stmts=[
                ReturnStmt(value=IntLiteral(value=0)),
            ]
        )
        code = emit_with([fn])
        assert "return 0" in code

    def test_return_void(self) -> None:
        fn = _fn(body_stmts=[ReturnStmt()])
        code = emit_with([fn])
        assert "return" in code

    def test_for_loop(self) -> None:
        fn = _fn(
            body_stmts=[
                ForLoop(
                    var_name="i",
                    iterable=RangeExpr(
                        start=IntLiteral(value=0),
                        end=IntLiteral(value=10),
                    ),
                    body=Block(
                        stmts=[
                            ExprStmt(
                                expr=CallExpr(
                                    callee=Identifier(name="print"),
                                    args=[Identifier(name="i")],
                                )
                            )
                        ]
                    ),
                )
            ]
        )
        code = emit_with([fn])
        assert "for i in range(0, 10):" in code
        assert "print(i)" in code

    def test_if_else(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=IfExpr(
                        condition=BinaryExpr(
                            left=Identifier(name="x"),
                            op=">",
                            right=IntLiteral(value=0),
                        ),
                        then_block=Block(
                            stmts=[
                                ExprStmt(
                                    expr=CallExpr(
                                        callee=Identifier(name="print"),
                                        args=[StringLiteral(value="pos")],
                                    )
                                )
                            ]
                        ),
                        else_block=Block(
                            stmts=[
                                ExprStmt(
                                    expr=CallExpr(
                                        callee=Identifier(name="print"),
                                        args=[StringLiteral(value="neg")],
                                    )
                                )
                            ]
                        ),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "if (x > 0):" in code
        assert "print('pos')" in code
        assert "else:" in code
        assert "print('neg')" in code

    def test_if_elif(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=IfExpr(
                        condition=BinaryExpr(
                            left=Identifier(name="x"),
                            op=">",
                            right=IntLiteral(value=0),
                        ),
                        then_block=Block(stmts=[ExprStmt(expr=StringLiteral(value="pos"))]),
                        else_block=IfExpr(
                            condition=BinaryExpr(
                                left=Identifier(name="x"),
                                op="==",
                                right=IntLiteral(value=0),
                            ),
                            then_block=Block(stmts=[ExprStmt(expr=StringLiteral(value="zero"))]),
                            else_block=Block(stmts=[ExprStmt(expr=StringLiteral(value="neg"))]),
                        ),
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "if (x > 0):" in code
        assert "elif (x == 0):" in code
        assert "else:" in code

    def test_match_expr(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=MatchExpr(
                        subject=Identifier(name="shape"),
                        arms=[
                            MatchArm(
                                pattern=ConstructorPattern(
                                    name="Circle",
                                    args=[IdentPattern(name="r")],
                                ),
                                body=Block(
                                    stmts=[
                                        ExprStmt(
                                            expr=BinaryExpr(
                                                left=FloatLiteral(value=3.14),
                                                op="*",
                                                right=Identifier(name="r"),
                                            )
                                        )
                                    ]
                                ),
                            ),
                            MatchArm(
                                pattern=WildcardPattern(),
                                body=Block(stmts=[ExprStmt(expr=IntLiteral(value=0))]),
                            ),
                        ],
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "match shape:" in code
        assert "case Circle(r):" in code
        assert "case _:" in code

    def test_match_literal_pattern(self) -> None:
        fn = _fn(
            body_stmts=[
                ExprStmt(
                    expr=MatchExpr(
                        subject=Identifier(name="x"),
                        arms=[
                            MatchArm(
                                pattern=LiteralPattern(value=IntLiteral(value=1)),
                                body=Block(stmts=[ExprStmt(expr=StringLiteral(value="one"))]),
                            ),
                        ],
                    )
                )
            ]
        )
        code = emit_with([fn])
        assert "case 1:" in code


class TestDefinitionEmission:
    def test_fn_def(self) -> None:
        fn = FnDef(
            name="add",
            params=[
                Param(name="a", type_annotation=NamedType(name="Int")),
                Param(name="b", type_annotation=NamedType(name="Int")),
            ],
            return_type=NamedType(name="Int"),
            body=Block(
                stmts=[
                    ReturnStmt(
                        value=BinaryExpr(
                            left=Identifier(name="a"),
                            op="+",
                            right=Identifier(name="b"),
                        )
                    )
                ]
            ),
        )
        code = emit_with([fn])
        assert "def add(a: int, b: int) -> int:" in code
        assert "return (a + b)" in code

    def test_main_sync_when_no_agents(self) -> None:
        """main() without async features is emitted as a regular function."""
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    ExprStmt(
                        expr=CallExpr(
                            callee=Identifier(name="print"),
                            args=[StringLiteral(value="hello")],
                        )
                    )
                ]
            ),
        )
        code = emit_with([fn])
        assert "def main():" in code
        assert "async def main():" not in code
        assert 'if __name__ == "__main__":' in code
        assert "main()" in code
        assert "asyncio.run" not in code

    def test_main_async_with_spawn(self) -> None:
        """main() with spawn is emitted as async def."""
        fn = FnDef(
            name="main",
            params=[],
            body=Block(
                stmts=[
                    ExprStmt(
                        expr=SpawnExpr(
                            callee=Identifier(name="worker"),
                            args=[],
                        )
                    )
                ]
            ),
        )
        code = emit_with([fn])
        assert "async def main():" in code
        assert 'if __name__ == "__main__":' in code
        assert "asyncio.run(main())" in code

    def test_struct_def(self) -> None:
        struct = StructDef(
            name="Point",
            fields=[
                StructField(name="x", type_annotation=NamedType(name="Float")),
                StructField(name="y", type_annotation=NamedType(name="Float")),
            ],
        )
        code = emit_with([struct])
        assert "class Point:" in code
        assert "def __init__(self, x: float, y: float)" in code
        assert "self.x = x" in code
        assert "self.y = y" in code

    def test_enum_def(self) -> None:
        enum = EnumDef(
            name="Shape",
            variants=[
                EnumVariant(name="Circle", fields=[NamedType(name="Float")]),
                EnumVariant(
                    name="Rect",
                    fields=[
                        NamedType(name="Float"),
                        NamedType(name="Float"),
                    ],
                ),
            ],
        )
        code = emit_with([enum])
        assert "class Shape_Circle:" in code
        assert "class Shape_Rect:" in code
        assert "Shape = Shape_Circle | Shape_Rect" in code

    def test_type_alias(self) -> None:
        alias = TypeAlias(name="Name", type_expr=NamedType(name="String"))
        code = emit_with([alias])
        assert "Name = str" in code

    def test_impl_methods_merged(self) -> None:
        struct = StructDef(
            name="Point",
            fields=[
                StructField(name="x", type_annotation=NamedType(name="Float")),
            ],
        )
        impl = ImplDef(
            target="Point",
            methods=[
                FnDef(
                    name="magnitude",
                    params=[],
                    return_type=NamedType(name="Float"),
                    body=Block(
                        stmts=[
                            ReturnStmt(
                                value=FieldAccessExpr(
                                    object=Identifier(name="self"),
                                    field_name="x",
                                )
                            )
                        ]
                    ),
                )
            ],
        )
        code = emit_with([struct, impl])
        assert "def magnitude(self)" in code

    def test_import_def(self) -> None:
        imp = ImportDef(path=["math", "trig"], items=["sin", "cos"])
        code = emit_with([imp])
        assert "from math.trig import sin, cos" in code

    def test_import_module(self) -> None:
        imp = ImportDef(path=["utils"], items=[])
        code = emit_with([imp])
        assert "import utils" in code

    def test_export_def(self) -> None:
        exp = ExportDef(
            definition=FnDef(
                name="helper",
                params=[],
                body=Block(stmts=[ReturnStmt(value=IntLiteral(value=1))]),
            )
        )
        code = emit_with([exp])
        assert "def helper():" in code

    def test_empty_block(self) -> None:
        fn = _fn(body_stmts=[])
        code = emit_with([fn])
        assert "pass" in code


class TestTypeEmission:
    def test_named_types(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="x",
                    type_annotation=NamedType(name="Int"),
                    value=IntLiteral(value=0),
                ),
            ]
        )
        code = emit_with([fn])
        assert "x: int" in code

    def test_list_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="xs",
                    type_annotation=GenericType(name="List", args=[NamedType(name="Int")]),
                    value=ListLiteral(elements=[]),
                ),
            ]
        )
        code = emit_with([fn])
        assert "xs: list[int]" in code

    def test_map_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="m",
                    type_annotation=GenericType(
                        name="Map",
                        args=[NamedType(name="String"), NamedType(name="Int")],
                    ),
                    value=ListLiteral(elements=[]),
                ),
            ]
        )
        code = emit_with([fn])
        assert "m: dict[str, int]" in code

    def test_signal_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="s",
                    type_annotation=GenericType(name="Signal", args=[NamedType(name="Int")]),
                    value=SignalExpr(value=IntLiteral(value=0)),
                ),
            ]
        )
        code = emit_with([fn])
        assert "s: Signal[int]" in code

    def test_channel_type(self) -> None:
        fn = _fn(
            body_stmts=[
                LetBinding(
                    name="ch",
                    type_annotation=GenericType(name="Channel", args=[NamedType(name="String")]),
                    value=Identifier(name="channel"),
                ),
            ]
        )
        code = emit_with([fn])
        assert "ch: Channel[str]" in code


# ---------------------------------------------------------------------------
# Runtime unit tests
# ---------------------------------------------------------------------------


class TestRuntimeSignal:
    def test_signal_value(self) -> None:
        from runtime.signal import Signal

        s: Signal[int] = Signal(10)
        assert s.value == 10

    def test_signal_set(self) -> None:
        from runtime.signal import Signal

        s: Signal[int] = Signal(0)
        s.value = 42
        assert s.value == 42

    def test_signal_computed(self) -> None:
        from runtime.signal import Signal

        a: Signal[int] = Signal(3)
        b: Signal[int] = Signal(computed=lambda: a.value * 2)
        a.subscribe(b)
        assert b.value == 6
        a.value = 5
        assert b.value == 10

    def test_computed_cannot_set(self) -> None:
        from runtime.signal import Signal

        s: Signal[int] = Signal(computed=lambda: 42)
        with pytest.raises(AttributeError):
            s.value = 10


class TestRuntimeResult:
    def test_ok(self) -> None:
        from runtime.result import Ok

        r = Ok(42)
        assert r.is_ok()
        assert not r.is_err()
        assert r.unwrap() == 42

    def test_err(self) -> None:
        from runtime.result import Err

        r = Err("oops")
        assert r.is_err()
        assert not r.is_ok()
        with pytest.raises(RuntimeError):
            r.unwrap()

    def test_unwrap_or_return(self) -> None:
        from runtime.result import Err, Ok, _EarlyReturn, unwrap_or_return

        assert unwrap_or_return(Ok(5)) == 5
        with pytest.raises(_EarlyReturn):
            unwrap_or_return(Err("bad"))

    def test_some(self) -> None:
        from runtime.result import Some

        s = Some(42)
        assert s.value == 42
        assert repr(s) == "Some(42)"

    def test_ok_equality(self) -> None:
        from runtime.result import Ok

        assert Ok(1) == Ok(1)
        assert Ok(1) != Ok(2)

    def test_err_equality(self) -> None:
        from runtime.result import Err

        assert Err("a") == Err("a")
        assert Err("a") != Err("b")


class TestRuntimeStream:
    @pytest.mark.asyncio
    async def test_stream_from_iter(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3])
        result = await s.collect()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_stream_map(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3]).map(lambda x: x * 2)
        result = await s.collect()
        assert result == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_stream_filter(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3, 4]).filter(lambda x: x % 2 == 0)
        result = await s.collect()
        assert result == [2, 4]

    @pytest.mark.asyncio
    async def test_stream_take(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3, 4, 5]).take(3)
        result = await s.collect()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_stream_skip(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3, 4, 5]).skip(2)
        result = await s.collect()
        assert result == [3, 4, 5]

    @pytest.mark.asyncio
    async def test_stream_chunk(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3, 4, 5]).chunk(2)
        result = await s.collect()
        assert result == [[1, 2], [3, 4], [5]]

    @pytest.mark.asyncio
    async def test_stream_fold(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([1, 2, 3])
        result = await s.fold(0, lambda acc, x: acc + x)
        assert result == 6

    @pytest.mark.asyncio
    async def test_stream_first(self) -> None:
        from runtime.stream import Stream

        s = Stream.from_iter([10, 20, 30])
        result = await s.first()
        assert result == 10


class TestRuntimeAgent:
    @pytest.mark.asyncio
    async def test_agent_spawn_and_communicate(self) -> None:
        from runtime.agent import AgentBase

        class Echo(AgentBase):
            def __init__(self) -> None:
                super().__init__()
                self._register_input("msg")
                self._register_output("reply")

            async def handle(self, value: str) -> str:
                return f"echo: {value}"

        handle = await Echo.spawn()
        await handle.msg.send("hello")
        result = await handle.reply.receive()
        assert result == "echo: hello"
        await handle.stop()
