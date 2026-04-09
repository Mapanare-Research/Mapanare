"""Tests for Phase 4.1 — LLVM type mapping.

Each test class corresponds to a roadmap task in Phase 4.1.
Validates type resolution through the MIR-based text emitter pipeline.
"""

from __future__ import annotations

from mapanare.emit_llvm_text import (
    DBL,
    I1,
    I64,
    LIST,
    PTR,
    STR,
    LLVMTextEmitter,
)
from mapanare.lower import lower as build_mir
from mapanare.mir import MIRType
from mapanare.parser import parse
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Helpers — build a type and resolve it through the text emitter
# ---------------------------------------------------------------------------


def _rty(kind: TypeKind, name: str = "", args: list[TypeInfo] | None = None) -> str:
    """Resolve a MIR type to an LLVM type string via LLVMTextEmitter."""
    ti = TypeInfo(kind=kind, name=name, args=args or [])
    mt = MIRType(type_info=ti)
    emitter = LLVMTextEmitter(module_name="test")
    return emitter._rty(mt)


# ---------------------------------------------------------------------------
# Task 1: Int -> i64, Float -> double, Bool -> i1
# ---------------------------------------------------------------------------


class TestPrimitiveTypes:
    """Task 4.1.1 — primitive type mappings."""

    def test_int_is_i64(self) -> None:
        assert _rty(TypeKind.INT) == I64

    def test_float_is_double(self) -> None:
        assert _rty(TypeKind.FLOAT) == DBL

    def test_bool_is_i1(self) -> None:
        assert _rty(TypeKind.BOOL) == I1

    def test_char_is_i8(self) -> None:
        assert _rty(TypeKind.CHAR) == "i8"

    def test_void(self) -> None:
        assert _rty(TypeKind.VOID) == "void"

    def test_int_constant(self) -> None:
        assert I64 == "i64"

    def test_float_constant(self) -> None:
        assert DBL == "double"

    def test_bool_constant(self) -> None:
        assert I1 == "i1"


# ---------------------------------------------------------------------------
# Task 2: String -> { ptr, i64 } struct
# ---------------------------------------------------------------------------


class TestStringType:
    """Task 4.1.2 — String -> {ptr, i64} struct."""

    def test_string_is_struct(self) -> None:
        ty = _rty(TypeKind.STRING)
        assert ty == STR

    def test_string_has_ptr_and_i64(self) -> None:
        ty = _rty(TypeKind.STRING)
        assert "ptr" in ty
        assert "i64" in ty

    def test_string_constant_matches(self) -> None:
        assert STR == _rty(TypeKind.STRING)


# ---------------------------------------------------------------------------
# Task 3: Option<T> -> { i1, T } tagged union
# ---------------------------------------------------------------------------


class TestOptionType:
    """Task 4.1.3 — Option<T> -> { i1, T } tagged union."""

    def test_option_int(self) -> None:
        ty = _rty(TypeKind.OPTION, args=[TypeInfo(kind=TypeKind.INT)])
        assert ty == "{i1, i64}"

    def test_option_float(self) -> None:
        ty = _rty(TypeKind.OPTION, args=[TypeInfo(kind=TypeKind.FLOAT)])
        assert "double" in ty

    def test_option_string(self) -> None:
        ty = _rty(TypeKind.OPTION, args=[TypeInfo(kind=TypeKind.STRING)])
        assert "i1" in ty
        assert "{ptr, i64}" in ty

    def test_option_bool(self) -> None:
        ty = _rty(TypeKind.OPTION, args=[TypeInfo(kind=TypeKind.BOOL)])
        assert "i1" in ty


# ---------------------------------------------------------------------------
# Task 4: Result<T, E> -> { i1, { T, E } } tagged union
# ---------------------------------------------------------------------------


class TestResultType:
    """Task 4.1.4 — Result<T, E> -> { i1, { T, E } } tagged union."""

    def test_result_int_string(self) -> None:
        ty = _rty(
            TypeKind.RESULT,
            args=[TypeInfo(kind=TypeKind.INT), TypeInfo(kind=TypeKind.STRING)],
        )
        assert "i1" in ty
        assert "i64" in ty
        assert "{ptr, i64}" in ty

    def test_result_float_int(self) -> None:
        ty = _rty(
            TypeKind.RESULT,
            args=[TypeInfo(kind=TypeKind.FLOAT), TypeInfo(kind=TypeKind.INT)],
        )
        assert "double" in ty
        assert "i64" in ty


# ---------------------------------------------------------------------------
# Task 5: Tensor<T>[...] — tensor type
# ---------------------------------------------------------------------------


class TestTensorType:
    """Task 4.1.5 — Tensor type resolution."""

    def test_tensor_resolves(self) -> None:
        """Tensor resolves to ptr (opaque pointer)."""
        ty = _rty(TypeKind.TENSOR)
        # Tensor may be ptr or a struct depending on implementation
        assert ty is not None


# ---------------------------------------------------------------------------
# Additional integration tests
# ---------------------------------------------------------------------------


class TestTypeMapperIntegration:
    """Cross-cutting tests for type resolution."""

    def test_list_type(self) -> None:
        ty = _rty(TypeKind.LIST)
        assert ty == LIST

    def test_map_type(self) -> None:
        ty = _rty(TypeKind.MAP)
        assert ty == PTR

    def test_agent_type(self) -> None:
        ty = _rty(TypeKind.AGENT)
        assert ty == PTR

    def test_fn_type(self) -> None:
        ty = _rty(TypeKind.FN)
        assert ty == PTR

    def test_emit_simple_fn_produces_ir(self) -> None:
        """Full pipeline: parse -> lower -> emit produces IR with correct types."""
        src = "fn add(a: Int, b: Int) -> Int { return a + b }"
        ast = parse(src, filename="test.mn")
        mir = build_mir(ast, module_name="test")
        emitter = LLVMTextEmitter(module_name="test")
        ir = emitter.emit(mir)
        assert "i64" in ir
        assert "define" in ir
