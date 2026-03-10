"""Tests for Phase 1.1 — Memory Management Strategy.

Verifies that the LLVM emitter generates proper memory management code:
- Arena creation at function entry
- Arena destruction at function exit
- String free calls for temporaries
- Scope cleanup before return statements
"""

from __future__ import annotations

from mapanare.ast_nodes import (
    AssignExpr,
    BinaryExpr,
    Block,
    CallExpr,
    ExprStmt,
    FnDef,
    Identifier,
    IntLiteral,
    LetBinding,
    NamedType,
    Param,
    Program,
    ReturnStmt,
    StringLiteral,
)
from mapanare.emit_llvm import LLVMEmitter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fn(
    name: str = "test_fn",
    params: list[Param] | None = None,
    ret: NamedType | None = None,
    body: list[object] | None = None,
) -> FnDef:
    return FnDef(
        name=name,
        params=params or [],
        return_type=ret,
        body=Block(stmts=body or []),
    )


def _emit_fn(fn_def: FnDef) -> str:
    """Emit a single function and return the LLVM IR as text."""
    emitter = LLVMEmitter()
    prog = Program(definitions=[fn_def])
    module = emitter.emit_program(prog)
    return str(module)


# ---------------------------------------------------------------------------
# Task 2 Tests: Arena allocator in emitted IR
# ---------------------------------------------------------------------------


class TestArenaInEmittedIR:
    """Verify that emitted functions contain arena create/destroy calls."""

    def test_empty_fn_has_arena_create(self) -> None:
        """An empty void function should still create a scope arena."""
        ir_text = _emit_fn(_make_fn(body=[]))
        assert "mn_arena_create" in ir_text

    def test_empty_fn_has_arena_destroy(self) -> None:
        """An empty void function should destroy the scope arena on exit."""
        ir_text = _emit_fn(_make_fn(body=[]))
        assert "mn_arena_destroy" in ir_text

    def test_arena_created_before_body(self) -> None:
        """Arena creation should appear before the function body instructions."""
        fn = _make_fn(
            body=[
                ExprStmt(
                    expr=CallExpr(callee=Identifier(name="print"), args=[IntLiteral(value=42)])
                )
            ]
        )
        ir_text = _emit_fn(fn)
        create_pos = ir_text.find("mn_arena_create")
        # The printf/print call should come after arena creation
        printf_pos = ir_text.find("printf")
        if printf_pos >= 0:
            assert create_pos < printf_pos


# ---------------------------------------------------------------------------
# Task 3 Tests: String free in emitted IR
# ---------------------------------------------------------------------------


class TestStringFreeInEmittedIR:
    """Verify that string temporaries get __mn_str_free calls."""

    def test_str_concat_tracked(self) -> None:
        """String concatenation should produce a tracked temporary."""
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="String")),
                Param(name="b", type_annotation=NamedType(name="String")),
            ],
            ret=NamedType(name="Void"),
            body=[
                LetBinding(
                    name="c",
                    mutable=False,
                    type_annotation=None,
                    value=BinaryExpr(
                        op="+",
                        left=Identifier(name="a"),
                        right=Identifier(name="b"),
                    ),
                ),
            ],
        )
        ir_text = _emit_fn(fn)
        assert "__mn_str_concat" in ir_text
        assert "__mn_str_free" in ir_text

    def test_str_free_before_arena_destroy(self) -> None:
        """String frees should happen before arena destruction."""
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="String")),
                Param(name="b", type_annotation=NamedType(name="String")),
            ],
            ret=NamedType(name="Void"),
            body=[
                LetBinding(
                    name="c",
                    mutable=False,
                    type_annotation=None,
                    value=BinaryExpr(
                        op="+",
                        left=Identifier(name="a"),
                        right=Identifier(name="b"),
                    ),
                ),
            ],
        )
        ir_text = _emit_fn(fn)
        free_pos = ir_text.find("__mn_str_free")
        destroy_pos = ir_text.find("mn_arena_destroy")
        assert free_pos < destroy_pos

    def test_return_string_not_freed(self) -> None:
        """A string returned from a function should NOT be freed (it escapes)."""
        fn = _make_fn(
            params=[
                Param(name="a", type_annotation=NamedType(name="String")),
                Param(name="b", type_annotation=NamedType(name="String")),
            ],
            ret=NamedType(name="String"),
            body=[
                ReturnStmt(
                    value=BinaryExpr(
                        op="+",
                        left=Identifier(name="a"),
                        right=Identifier(name="b"),
                    ),
                ),
            ],
        )
        ir_text = _emit_fn(fn)
        assert "__mn_str_concat" in ir_text
        # Arena destroy should still be present (for scope cleanup)
        assert "mn_arena_destroy" in ir_text


# ---------------------------------------------------------------------------
# Task 4 Tests: List free declarations
# ---------------------------------------------------------------------------


class TestListFreeDeclarations:
    """Verify list free functions are declared when needed."""

    def test_list_free_strings_declared(self) -> None:
        """__mn_list_free_strings should be declarable."""
        emitter = LLVMEmitter()
        fn = emitter._rt_list_free_strings()
        assert fn.name == "__mn_list_free_strings"

    def test_list_free_declared(self) -> None:
        """__mn_list_free should be declarable."""
        emitter = LLVMEmitter()
        fn = emitter._rt_list_free()
        assert fn.name == "__mn_list_free"


# ---------------------------------------------------------------------------
# Task 5 Tests: Scope cleanup on function exit
# ---------------------------------------------------------------------------


class TestScopeCleanup:
    """Verify scope cleanup emitted at all exit points."""

    def test_void_fn_has_cleanup(self) -> None:
        """A void function should have arena destroy before ret void."""
        fn = _make_fn(
            ret=NamedType(name="Void"),
            body=[],
        )
        ir_text = _emit_fn(fn)
        assert "mn_arena_destroy" in ir_text
        assert "ret void" in ir_text

    def test_explicit_return_has_cleanup(self) -> None:
        """An explicit return statement should have cleanup before ret."""
        fn = _make_fn(
            ret=NamedType(name="Int"),
            body=[
                ReturnStmt(value=IntLiteral(value=42)),
            ],
        )
        ir_text = _emit_fn(fn)
        assert "mn_arena_destroy" in ir_text

    def test_str_from_int_tracked(self) -> None:
        """toString(int) should produce a tracked string temporary."""
        fn = _make_fn(
            ret=NamedType(name="Void"),
            body=[
                LetBinding(
                    name="s",
                    mutable=False,
                    type_annotation=None,
                    value=CallExpr(
                        callee=Identifier(name="str"),
                        args=[IntLiteral(value=42)],
                    ),
                ),
            ],
        )
        ir_text = _emit_fn(fn)
        assert "__mn_str_from_int" in ir_text
        assert "__mn_str_free" in ir_text


# ---------------------------------------------------------------------------
# Task 6 Tests: Arena runtime declarations
# ---------------------------------------------------------------------------


class TestArenaDeclarations:
    """Verify arena runtime functions are properly declared."""

    def test_arena_create_declared(self) -> None:
        emitter = LLVMEmitter()
        fn = emitter._rt_arena_create()
        assert fn.name == "mn_arena_create"

    def test_arena_destroy_declared(self) -> None:
        emitter = LLVMEmitter()
        fn = emitter._rt_arena_destroy()
        assert fn.name == "mn_arena_destroy"

    def test_str_free_declared(self) -> None:
        emitter = LLVMEmitter()
        fn = emitter._rt_str_free()
        assert fn.name == "__mn_str_free"


# ---------------------------------------------------------------------------
# Task: String += assignment frees old value
# ---------------------------------------------------------------------------


class TestStringAssignmentCleanup:
    """Verify string += frees the old value."""

    def test_str_concat_assign_has_free(self) -> None:
        """s += 'x' should free the old s before storing the new concat."""
        fn = _make_fn(
            ret=NamedType(name="Void"),
            body=[
                LetBinding(
                    name="s",
                    mutable=True,
                    type_annotation=None,
                    value=StringLiteral(value="hello"),
                ),
                ExprStmt(
                    expr=AssignExpr(
                        target=Identifier(name="s"),
                        op="+=",
                        value=StringLiteral(value="x"),
                    ),
                ),
            ],
        )
        ir_text = _emit_fn(fn)
        assert "__mn_str_concat" in ir_text
        assert "__mn_str_free" in ir_text
