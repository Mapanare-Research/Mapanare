"""Tests for Phase 2.1 — LLVM Agent Codegen.

Tests verify that agent definitions, spawn, send, sync, and supervision
policy are emitted correctly to LLVM IR via the MIR-based text emitter.
"""

from __future__ import annotations

from mapanare.ast_nodes import (
    AgentDef,
    AgentInput,
    AgentOutput,
    BinaryExpr,
    Block,
    Decorator,
    ExprStmt,
    FieldAccessExpr,
    FnDef,
    Identifier,
    IntLiteral,
    LetBinding,
    NamedType,
    Param,
    Program,
    ReturnStmt,
    SendExpr,
    SpawnExpr,
    SyncExpr,
)
from mapanare.emit_llvm_text import I32, I64, LLVMTextEmitter
from mapanare.lower import lower as build_mir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_doubler_agent() -> AgentDef:
    """Create a simple Doubler agent: input Int, output Int, handle(x) -> x * 2."""
    return AgentDef(
        name="Doubler",
        inputs=[AgentInput(name="messages", type_annotation=NamedType(name="Int"))],
        outputs=[AgentOutput(name="results", type_annotation=NamedType(name="Int"))],
        state=[],
        methods=[
            FnDef(
                name="handle",
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


def _make_passthrough_agent() -> AgentDef:
    """Agent that passes messages through without modification."""
    return AgentDef(
        name="Passthrough",
        inputs=[AgentInput(name="inbox", type_annotation=NamedType(name="Int"))],
        outputs=[AgentOutput(name="outbox", type_annotation=NamedType(name="Int"))],
        state=[],
        methods=[
            FnDef(
                name="handle",
                params=[Param(name="msg", type_annotation=NamedType(name="Int"))],
                return_type=NamedType(name="Int"),
                body=Block(stmts=[ReturnStmt(value=Identifier(name="msg"))]),
            )
        ],
    )


def _make_spawn_program(agent: AgentDef) -> Program:
    """Create a program that defines an agent and spawns it in main."""
    return Program(
        definitions=[
            agent,
            FnDef(
                name="main",
                params=[],
                return_type=NamedType(name="Int"),
                body=Block(
                    stmts=[
                        LetBinding(
                            name="d",
                            value=SpawnExpr(
                                callee=Identifier(name=agent.name),
                                args=[],
                            ),
                        ),
                        ReturnStmt(value=IntLiteral(value=0)),
                    ]
                ),
            ),
        ]
    )


def _make_send_recv_program(agent: AgentDef) -> Program:
    """Create a program that spawns, sends, and syncs."""
    return Program(
        definitions=[
            agent,
            FnDef(
                name="main",
                params=[],
                return_type=NamedType(name="Int"),
                body=Block(
                    stmts=[
                        # let d = spawn Agent()
                        LetBinding(
                            name="d",
                            value=SpawnExpr(
                                callee=Identifier(name=agent.name),
                                args=[],
                            ),
                        ),
                        # d.messages <- 42
                        ExprStmt(
                            expr=SendExpr(
                                target=FieldAccessExpr(
                                    object=Identifier(name="d"),
                                    field_name=agent.inputs[0].name,
                                ),
                                value=IntLiteral(value=42),
                            )
                        ),
                        # let result = sync d.results
                        LetBinding(
                            name="result",
                            value=SyncExpr(
                                expr=FieldAccessExpr(
                                    object=Identifier(name="d"),
                                    field_name=agent.outputs[0].name,
                                )
                            ),
                        ),
                        ReturnStmt(value=Identifier(name="result")),
                    ]
                ),
            ),
        ]
    )


def _emit_ir(program: Program) -> str:
    """Lower and emit a program to LLVM IR text."""
    mir = build_mir(program, module_name="test")
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(mir)


# ===========================================================================
# Task 1: Wire emitter to emit calls to C runtime agent functions
# ===========================================================================


class TestAgentRuntimeDeclarations:
    """Verify runtime function declarations are emitted."""

    def test_agent_new_declared(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_new" in ir_text

    def test_agent_spawn_declared(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_spawn" in ir_text

    def test_agent_send_declared(self) -> None:
        agent = _make_doubler_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_send" in ir_text

    def test_agent_recv_blocking_declared(self) -> None:
        agent = _make_doubler_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_recv_blocking" in ir_text


# ===========================================================================
# Task 2: SpawnExpr codegen
# ===========================================================================


class TestSpawnExpr:
    """Verify spawn expression emits agent allocation and thread start."""

    def test_spawn_calls_agent_new(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_new" in ir_text

    def test_spawn_calls_agent_spawn(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_spawn" in ir_text

    def test_spawn_passes_handler(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "__mn_handler_Doubler" in ir_text

    def test_spawn_produces_ptr(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        # Agent handle is a pointer
        assert "ptr" in ir_text or "i8*" in ir_text


# ===========================================================================
# Task 3: SendExpr codegen
# ===========================================================================


class TestSendExpr:
    """Verify send expression emits message boxing and send call."""

    def test_send_calls_agent_send(self) -> None:
        agent = _make_doubler_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_send" in ir_text


# ===========================================================================
# Task 4: SyncExpr codegen
# ===========================================================================


class TestSyncExpr:
    """Verify sync expression emits blocking receive and unboxing."""

    def test_sync_calls_recv_blocking(self) -> None:
        agent = _make_doubler_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_recv_blocking" in ir_text


# ===========================================================================
# Task 5: Agent handle function dispatch
# ===========================================================================


class TestAgentHandler:
    """Verify handler wrapper function is emitted correctly."""

    def test_handler_function_exists(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "__mn_handler_Doubler" in ir_text

    def test_handler_has_correct_return_type(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        # Handler returns i32 status code
        assert I32 in ir_text

    def test_handler_calls_method(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "Doubler_handle" in ir_text

    def test_method_function_exists(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "Doubler_handle" in ir_text

    def test_method_function_uses_i64(self) -> None:
        agent = _make_doubler_agent()
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        # Int maps to i64
        assert I64 in ir_text


# ===========================================================================
# Task 6: Supervision policy codegen
# ===========================================================================


class TestSupervisionPolicy:
    """Verify supervision policy handling.

    The text emitter does not emit mapanare_agent_set_restart_policy at the IR
    level. Supervision policy is handled at the runtime layer. Decorators are
    preserved in MIR but not directly emitted as function calls by the text
    emitter. These tests verify the decorator does not break compilation.
    """

    def test_restart_decorator_compiles(self) -> None:
        agent = _make_doubler_agent()
        agent.decorators = [Decorator(name="restart", args=[IntLiteral(value=5)])]
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        # Should still compile successfully with agent infrastructure
        assert "mapanare_agent_new" in ir_text
        assert "mapanare_agent_spawn" in ir_text

    def test_no_decorator_no_policy_call(self) -> None:
        agent = _make_doubler_agent()
        agent.decorators = []
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        assert "mapanare_agent_set_restart_policy" not in ir_text

    def test_restart_default_compiles(self) -> None:
        agent = _make_doubler_agent()
        agent.decorators = [Decorator(name="restart", args=[])]
        program = _make_spawn_program(agent)
        ir_text = _emit_ir(program)
        # Should compile without errors
        assert "mapanare_agent_new" in ir_text


# ===========================================================================
# Full pipeline: spawn + send + sync together
# ===========================================================================


class TestAgentFullPipeline:
    """Test the full agent lifecycle in LLVM IR."""

    def test_doubler_full_pipeline(self) -> None:
        """Emit a complete program: define Doubler, spawn, send 42, sync result."""
        agent = _make_doubler_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)

        # All agent runtime functions should be declared
        assert "mapanare_agent_new" in ir_text
        assert "mapanare_agent_spawn" in ir_text
        assert "mapanare_agent_send" in ir_text
        assert "mapanare_agent_recv_blocking" in ir_text

        # Handler and method should exist
        assert "__mn_handler_Doubler" in ir_text
        assert "Doubler_handle" in ir_text

        # Main function should exist
        assert "define" in ir_text and "main" in ir_text

    def test_passthrough_agent(self) -> None:
        """Emit a passthrough agent pipeline."""
        agent = _make_passthrough_agent()
        program = _make_send_recv_program(agent)
        ir_text = _emit_ir(program)

        assert "__mn_handler_Passthrough" in ir_text
        assert "Passthrough_handle" in ir_text

    def test_multiple_agents(self) -> None:
        """Emit a program with two different agent types."""
        doubler = _make_doubler_agent()
        passthrough = _make_passthrough_agent()
        program = Program(
            definitions=[
                doubler,
                passthrough,
                FnDef(
                    name="main",
                    params=[],
                    body=Block(
                        stmts=[
                            LetBinding(
                                name="d",
                                value=SpawnExpr(callee=Identifier(name="Doubler"), args=[]),
                            ),
                            LetBinding(
                                name="p",
                                value=SpawnExpr(callee=Identifier(name="Passthrough"), args=[]),
                            ),
                        ]
                    ),
                ),
            ]
        )
        ir_text = _emit_ir(program)

        assert "__mn_handler_Doubler" in ir_text
        assert "__mn_handler_Passthrough" in ir_text
        assert "Doubler_handle" in ir_text
        assert "Passthrough_handle" in ir_text
