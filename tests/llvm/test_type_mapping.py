"""Tests for Phase 4.1 — LLVM type mapping.

Each test class corresponds to a roadmap task in Phase 4.1.
"""

from __future__ import annotations

import pytest
from llvmlite import ir

from mapa.ast_nodes import (
    GenericType,
    IntLiteral,
    NamedType,
    TensorType,
)
from mapa.emit_llvm import (
    LLVM_BOOL,
    LLVM_FLOAT,
    LLVM_INT,
    LLVM_STRING,
    TypeMapper,
    option_type,
    result_type,
    tensor_type,
)

# ---------------------------------------------------------------------------
# Task 1: Int → i64, Float → double, Bool → i1
# ---------------------------------------------------------------------------


class TestPrimitiveTypes:
    """Task 4.1.1 — primitive type mappings."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_int_is_i64(self) -> None:
        ty = self.mapper.resolve(NamedType(name="Int"))
        assert ty == ir.IntType(64)

    def test_float_is_double(self) -> None:
        ty = self.mapper.resolve(NamedType(name="Float"))
        assert ty == ir.DoubleType()

    def test_bool_is_i1(self) -> None:
        ty = self.mapper.resolve(NamedType(name="Bool"))
        assert ty == ir.IntType(1)

    def test_char_is_i8(self) -> None:
        ty = self.mapper.resolve(NamedType(name="Char"))
        assert ty == ir.IntType(8)

    def test_void(self) -> None:
        ty = self.mapper.resolve(NamedType(name="Void"))
        assert isinstance(ty, ir.VoidType)

    def test_int_constant(self) -> None:
        assert LLVM_INT == ir.IntType(64)

    def test_float_constant(self) -> None:
        assert LLVM_FLOAT == ir.DoubleType()

    def test_bool_constant(self) -> None:
        assert LLVM_BOOL == ir.IntType(1)

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(TypeError, match="Unknown Mapanare type"):
            self.mapper.resolve(NamedType(name="FooBar"))


# ---------------------------------------------------------------------------
# Task 2: String → { i8*, i64 } struct
# ---------------------------------------------------------------------------


class TestStringType:
    """Task 4.1.2 — String → { i8*, i64 } struct."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_string_is_struct(self) -> None:
        ty = self.mapper.resolve(NamedType(name="String"))
        assert isinstance(ty, ir.LiteralStructType)

    def test_string_has_two_fields(self) -> None:
        ty = self.mapper.resolve(NamedType(name="String"))
        assert len(ty.elements) == 2

    def test_string_data_ptr(self) -> None:
        """First field: i8* pointer to character data."""
        ty = self.mapper.resolve(NamedType(name="String"))
        data_ptr = ty.elements[0]
        assert isinstance(data_ptr, ir.PointerType)
        assert data_ptr.pointee == ir.IntType(8)

    def test_string_length(self) -> None:
        """Second field: i64 length."""
        ty = self.mapper.resolve(NamedType(name="String"))
        length = ty.elements[1]
        assert length == ir.IntType(64)

    def test_string_constant_matches(self) -> None:
        assert LLVM_STRING == self.mapper.resolve(NamedType(name="String"))


# ---------------------------------------------------------------------------
# Task 3: Option<T> → { i1, T } tagged union
# ---------------------------------------------------------------------------


class TestOptionType:
    """Task 4.1.3 — Option<T> → { i1, T } tagged union."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_option_int(self) -> None:
        ty = self.mapper.resolve(GenericType(name="Option", args=[NamedType(name="Int")]))
        assert isinstance(ty, ir.LiteralStructType)
        assert len(ty.elements) == 2
        assert ty.elements[0] == LLVM_BOOL  # tag
        assert ty.elements[1] == LLVM_INT  # value

    def test_option_float(self) -> None:
        ty = self.mapper.resolve(GenericType(name="Option", args=[NamedType(name="Float")]))
        assert ty.elements[1] == LLVM_FLOAT

    def test_option_string(self) -> None:
        ty = self.mapper.resolve(GenericType(name="Option", args=[NamedType(name="String")]))
        assert ty.elements[0] == LLVM_BOOL
        assert ty.elements[1] == LLVM_STRING

    def test_option_bool(self) -> None:
        ty = self.mapper.resolve(GenericType(name="Option", args=[NamedType(name="Bool")]))
        assert ty.elements[1] == LLVM_BOOL

    def test_nested_option(self) -> None:
        """Option<Option<Int>> should nest properly."""
        inner = GenericType(name="Option", args=[NamedType(name="Int")])
        ty = self.mapper.resolve(GenericType(name="Option", args=[inner]))
        assert isinstance(ty, ir.LiteralStructType)
        inner_ty = ty.elements[1]
        assert isinstance(inner_ty, ir.LiteralStructType)
        assert inner_ty.elements[1] == LLVM_INT

    def test_option_wrong_arg_count(self) -> None:
        with pytest.raises(TypeError, match="Option expects exactly 1"):
            self.mapper.resolve(
                GenericType(name="Option", args=[NamedType(name="Int"), NamedType(name="Float")])
            )

    def test_option_helper_function(self) -> None:
        ty = option_type(LLVM_INT)
        assert ty.elements[0] == LLVM_BOOL
        assert ty.elements[1] == LLVM_INT


# ---------------------------------------------------------------------------
# Task 4: Result<T, E> → { i1, { T, E } } tagged union
# ---------------------------------------------------------------------------


class TestResultType:
    """Task 4.1.4 — Result<T, E> → { i1, { T, E } } tagged union."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_result_int_string(self) -> None:
        ty = self.mapper.resolve(
            GenericType(name="Result", args=[NamedType(name="Int"), NamedType(name="String")])
        )
        assert isinstance(ty, ir.LiteralStructType)
        assert len(ty.elements) == 2
        assert ty.elements[0] == LLVM_BOOL  # tag: 1=Ok, 0=Err
        payload = ty.elements[1]
        assert isinstance(payload, ir.LiteralStructType)
        assert payload.elements[0] == LLVM_INT  # ok type
        assert payload.elements[1] == LLVM_STRING  # err type

    def test_result_float_int(self) -> None:
        ty = self.mapper.resolve(
            GenericType(name="Result", args=[NamedType(name="Float"), NamedType(name="Int")])
        )
        payload = ty.elements[1]
        assert payload.elements[0] == LLVM_FLOAT
        assert payload.elements[1] == LLVM_INT

    def test_result_nested_option(self) -> None:
        """Result<Option<Int>, String>."""
        opt = GenericType(name="Option", args=[NamedType(name="Int")])
        ty = self.mapper.resolve(GenericType(name="Result", args=[opt, NamedType(name="String")]))
        payload = ty.elements[1]
        ok_ty = payload.elements[0]
        assert isinstance(ok_ty, ir.LiteralStructType)
        assert ok_ty.elements[1] == LLVM_INT

    def test_result_wrong_arg_count(self) -> None:
        with pytest.raises(TypeError, match="Result expects exactly 2"):
            self.mapper.resolve(GenericType(name="Result", args=[NamedType(name="Int")]))

    def test_result_helper_function(self) -> None:
        ty = result_type(LLVM_FLOAT, LLVM_STRING)
        assert ty.elements[0] == LLVM_BOOL
        assert ty.elements[1].elements[0] == LLVM_FLOAT
        assert ty.elements[1].elements[1] == LLVM_STRING


# ---------------------------------------------------------------------------
# Task 5: Tensor<T>[...] → contiguous heap allocation
# ---------------------------------------------------------------------------


class TestTensorType:
    """Task 4.1.5 — Tensor<T>[...] → { T*, i64, i64*, i64 } heap struct."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_tensor_float_struct(self) -> None:
        ty = self.mapper.resolve(
            TensorType(
                element_type=NamedType(name="Float"),
                shape=[IntLiteral(value=3), IntLiteral(value=3)],
            )
        )
        assert isinstance(ty, ir.LiteralStructType)
        assert len(ty.elements) == 4

    def test_tensor_data_pointer(self) -> None:
        """First field: T* — pointer to element buffer."""
        ty = self.mapper.resolve(TensorType(element_type=NamedType(name="Float")))
        data = ty.elements[0]
        assert isinstance(data, ir.PointerType)
        assert data.pointee == LLVM_FLOAT

    def test_tensor_ndim(self) -> None:
        """Second field: i64 — number of dimensions."""
        ty = self.mapper.resolve(TensorType(element_type=NamedType(name="Float")))
        assert ty.elements[1] == LLVM_INT

    def test_tensor_shape_pointer(self) -> None:
        """Third field: i64* — pointer to shape array."""
        ty = self.mapper.resolve(TensorType(element_type=NamedType(name="Float")))
        shape = ty.elements[2]
        assert isinstance(shape, ir.PointerType)
        assert shape.pointee == LLVM_INT

    def test_tensor_size(self) -> None:
        """Fourth field: i64 — total element count."""
        ty = self.mapper.resolve(TensorType(element_type=NamedType(name="Float")))
        assert ty.elements[3] == LLVM_INT

    def test_tensor_int_elements(self) -> None:
        ty = self.mapper.resolve(TensorType(element_type=NamedType(name="Int")))
        assert ty.elements[0].pointee == LLVM_INT

    def test_tensor_helper_function(self) -> None:
        ty = tensor_type(LLVM_FLOAT)
        assert len(ty.elements) == 4
        assert ty.elements[0].pointee == LLVM_FLOAT

    def test_tensor_with_shape_ignored_at_type_level(self) -> None:
        """Shape is compile-time metadata; the LLVM struct is the same regardless."""
        ty1 = self.mapper.resolve(TensorType(element_type=NamedType(name="Float"), shape=[]))
        ty2 = self.mapper.resolve(
            TensorType(
                element_type=NamedType(name="Float"),
                shape=[IntLiteral(value=3), IntLiteral(value=3)],
            )
        )
        assert str(ty1) == str(ty2)


# ---------------------------------------------------------------------------
# Additional integration tests
# ---------------------------------------------------------------------------


class TestTypeMapperIntegration:
    """Cross-cutting tests for the TypeMapper."""

    def setup_method(self) -> None:
        self.mapper = TypeMapper()

    def test_register_and_resolve_struct(self) -> None:
        point_ty = ir.LiteralStructType([LLVM_FLOAT, LLVM_FLOAT])
        self.mapper.register_struct("Point", point_ty)
        assert self.mapper.resolve(NamedType(name="Point")) == point_ty

    def test_option_of_user_struct(self) -> None:
        point_ty = ir.LiteralStructType([LLVM_FLOAT, LLVM_FLOAT])
        self.mapper.register_struct("Point", point_ty)
        ty = self.mapper.resolve(GenericType(name="Option", args=[NamedType(name="Point")]))
        assert ty.elements[1] == point_ty

    def test_list_type(self) -> None:
        ty = self.mapper.resolve(GenericType(name="List", args=[NamedType(name="Int")]))
        assert isinstance(ty, ir.LiteralStructType)
        assert len(ty.elements) == 3
        assert ty.elements[0].pointee == LLVM_INT

    def test_map_type(self) -> None:
        ty = self.mapper.resolve(
            GenericType(name="Map", args=[NamedType(name="String"), NamedType(name="Int")])
        )
        assert isinstance(ty, ir.LiteralStructType)
        assert len(ty.elements) == 2

    def test_unsupported_type_expr(self) -> None:
        from mapa.ast_nodes import FnType

        with pytest.raises(TypeError, match="Unsupported Mapanare type expression"):
            self.mapper.resolve(FnType())

    def test_unknown_generic_raises(self) -> None:
        with pytest.raises(TypeError, match="Unknown generic Mapanare type"):
            self.mapper.resolve(GenericType(name="Weird", args=[NamedType(name="Int")]))
