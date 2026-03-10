"""Tests for the Mapanare type system (mapanare/types.py).

Verifies TypeKind enum, TypeInfo equality, display names, and builtin registries.
"""

from __future__ import annotations

import pytest

from mapanare.types import (
    BOOL_TYPE,
    BUILTIN_CALL_MAP,
    BUILTIN_FUNCTIONS,
    BUILTIN_GENERIC_KINDS,
    BUILTIN_GENERIC_TYPES,
    CHAR_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    PRIMITIVE_KINDS,
    PRIMITIVE_TYPES,
    PYTHON_TYPE_MAP,
    RANGE_TYPE,
    STRING_TYPE,
    TypeInfo,
    TypeKind,
    UNKNOWN_TYPE,
    VOID_TYPE,
    _type_display,
    kind_from_name,
    make_type,
)

# ======================================================================
# TypeKind enum
# ======================================================================


class TestTypeKind:
    """Tests for the TypeKind enum."""

    def test_primitive_kinds_exist(self) -> None:
        assert TypeKind.INT is not None
        assert TypeKind.FLOAT is not None
        assert TypeKind.BOOL is not None
        assert TypeKind.STRING is not None
        assert TypeKind.CHAR is not None
        assert TypeKind.VOID is not None

    def test_generic_kinds_exist(self) -> None:
        assert TypeKind.LIST is not None
        assert TypeKind.MAP is not None
        assert TypeKind.OPTION is not None
        assert TypeKind.RESULT is not None
        assert TypeKind.TENSOR is not None

    def test_compound_kinds_exist(self) -> None:
        assert TypeKind.FN is not None
        assert TypeKind.STRUCT is not None
        assert TypeKind.ENUM is not None
        assert TypeKind.AGENT is not None

    def test_special_kinds_exist(self) -> None:
        assert TypeKind.UNKNOWN is not None
        assert TypeKind.TYPE_VAR is not None
        assert TypeKind.RANGE is not None


# ======================================================================
# kind_from_name
# ======================================================================


class TestKindFromName:
    """Tests for kind_from_name resolver."""

    def test_primitives(self) -> None:
        assert kind_from_name("Int") == TypeKind.INT
        assert kind_from_name("Float") == TypeKind.FLOAT
        assert kind_from_name("Bool") == TypeKind.BOOL
        assert kind_from_name("String") == TypeKind.STRING
        assert kind_from_name("Char") == TypeKind.CHAR
        assert kind_from_name("Void") == TypeKind.VOID

    def test_generics(self) -> None:
        assert kind_from_name("List") == TypeKind.LIST
        assert kind_from_name("Map") == TypeKind.MAP
        assert kind_from_name("Option") == TypeKind.OPTION
        assert kind_from_name("Result") == TypeKind.RESULT
        assert kind_from_name("Tensor") == TypeKind.TENSOR

    def test_unknown_name(self) -> None:
        assert kind_from_name("MyStruct") == TypeKind.UNKNOWN
        assert kind_from_name("") == TypeKind.UNKNOWN


# ======================================================================
# TypeInfo equality
# ======================================================================


class TestTypeInfoEquality:
    """Tests for TypeInfo.__eq__."""

    def test_same_primitive(self) -> None:
        assert INT_TYPE == INT_TYPE
        assert TypeInfo(kind=TypeKind.INT) == TypeInfo(kind=TypeKind.INT)

    def test_different_primitives(self) -> None:
        assert INT_TYPE != STRING_TYPE
        assert not (INT_TYPE == STRING_TYPE)

    def test_unknown_matches_anything(self) -> None:
        assert UNKNOWN_TYPE == INT_TYPE
        assert INT_TYPE == UNKNOWN_TYPE
        assert UNKNOWN_TYPE == STRING_TYPE

    def test_user_defined_same_name(self) -> None:
        a = TypeInfo(kind=TypeKind.STRUCT, name="Point")
        b = TypeInfo(kind=TypeKind.STRUCT, name="Point")
        assert a == b

    def test_user_defined_different_name(self) -> None:
        a = TypeInfo(kind=TypeKind.STRUCT, name="Point")
        b = TypeInfo(kind=TypeKind.STRUCT, name="Vec2")
        assert a != b

    def test_generic_with_args(self) -> None:
        a = TypeInfo(kind=TypeKind.LIST, args=[INT_TYPE])
        b = TypeInfo(kind=TypeKind.LIST, args=[INT_TYPE])
        assert a == b

    def test_generic_different_args(self) -> None:
        a = TypeInfo(kind=TypeKind.LIST, args=[INT_TYPE])
        b = TypeInfo(kind=TypeKind.LIST, args=[STRING_TYPE])
        assert a != b

    def test_function_types(self) -> None:
        a = TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=[INT_TYPE],
            return_type=BOOL_TYPE,
        )
        b = TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=[INT_TYPE],
            return_type=BOOL_TYPE,
        )
        assert a == b

    def test_function_different_return(self) -> None:
        a = TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=[INT_TYPE],
            return_type=BOOL_TYPE,
        )
        b = TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=[INT_TYPE],
            return_type=STRING_TYPE,
        )
        assert a != b


# ======================================================================
# TypeInfo display
# ======================================================================


class TestTypeInfoDisplay:
    """Tests for TypeInfo.__repr__ and display_name."""

    def test_primitive_display(self) -> None:
        assert repr(INT_TYPE) == "Int"
        assert repr(FLOAT_TYPE) == "Float"
        assert repr(BOOL_TYPE) == "Bool"
        assert repr(STRING_TYPE) == "String"
        assert repr(VOID_TYPE) == "Void"

    def test_unknown_display(self) -> None:
        assert repr(UNKNOWN_TYPE) == "<unknown>"

    def test_user_defined_display(self) -> None:
        t = TypeInfo(kind=TypeKind.STRUCT, name="Point")
        assert repr(t) == "Point"

    def test_generic_display(self) -> None:
        t = TypeInfo(kind=TypeKind.LIST, args=[INT_TYPE])
        assert repr(t) == "List<Int>"

    def test_tensor_display(self) -> None:
        t = TypeInfo(
            kind=TypeKind.TENSOR,
            args=[FLOAT_TYPE],
            tensor_shape=(3, 3),
        )
        assert repr(t) == "Tensor<Float>[3, 3]"

    def test_function_display(self) -> None:
        t = TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=[INT_TYPE, INT_TYPE],
            return_type=BOOL_TYPE,
        )
        assert repr(t) == "fn(Int, Int) -> Bool"


# ======================================================================
# TypeInfo methods
# ======================================================================


class TestTypeInfoMethods:
    """Tests for TypeInfo utility methods."""

    def test_is_numeric(self) -> None:
        assert INT_TYPE.is_numeric()
        assert FLOAT_TYPE.is_numeric()
        assert not STRING_TYPE.is_numeric()
        assert not BOOL_TYPE.is_numeric()

    def test_is_primitive(self) -> None:
        assert INT_TYPE.is_primitive()
        assert STRING_TYPE.is_primitive()
        assert not TypeInfo(kind=TypeKind.LIST).is_primitive()
        assert not TypeInfo(kind=TypeKind.STRUCT, name="Foo").is_primitive()


# ======================================================================
# Builtin registries
# ======================================================================


class TestBuiltinRegistries:
    """Tests for builtin registries (single source of truth)."""

    def test_primitive_types_set(self) -> None:
        assert "Int" in PRIMITIVE_TYPES
        assert "Float" in PRIMITIVE_TYPES
        assert "Bool" in PRIMITIVE_TYPES
        assert "String" in PRIMITIVE_TYPES
        assert "List" not in PRIMITIVE_TYPES

    def test_primitive_kinds_set(self) -> None:
        assert TypeKind.INT in PRIMITIVE_KINDS
        assert TypeKind.LIST not in PRIMITIVE_KINDS

    def test_builtin_generic_types(self) -> None:
        assert "List" in BUILTIN_GENERIC_TYPES
        assert "Map" in BUILTIN_GENERIC_TYPES
        assert "Option" in BUILTIN_GENERIC_TYPES
        assert "Result" in BUILTIN_GENERIC_TYPES
        assert "Int" not in BUILTIN_GENERIC_TYPES

    def test_builtin_generic_kinds(self) -> None:
        assert TypeKind.LIST in BUILTIN_GENERIC_KINDS
        assert TypeKind.INT not in BUILTIN_GENERIC_KINDS

    def test_builtin_functions(self) -> None:
        assert "print" in BUILTIN_FUNCTIONS
        assert "println" in BUILTIN_FUNCTIONS
        assert "len" in BUILTIN_FUNCTIONS
        assert "str" in BUILTIN_FUNCTIONS
        assert BUILTIN_FUNCTIONS["print"].kind == TypeKind.VOID

    def test_python_type_map(self) -> None:
        assert PYTHON_TYPE_MAP["Int"] == "int"
        assert PYTHON_TYPE_MAP["String"] == "str"

    def test_builtin_call_map(self) -> None:
        assert BUILTIN_CALL_MAP["str"] == "str"
        assert BUILTIN_CALL_MAP["int"] == "int"


# ======================================================================
# make_type factory
# ======================================================================


class TestMakeType:
    """Tests for the make_type convenience factory."""

    def test_primitive(self) -> None:
        t = make_type("Int")
        assert t.kind == TypeKind.INT

    def test_generic(self) -> None:
        t = make_type("List")
        assert t.kind == TypeKind.LIST

    def test_user_defined(self) -> None:
        t = make_type("MyStruct")
        assert t.kind == TypeKind.STRUCT
        assert t.name == "MyStruct"

    def test_unknown(self) -> None:
        t = make_type("<unknown>")
        assert t.kind == TypeKind.UNKNOWN


# ======================================================================
# Integration with semantic checker
# ======================================================================


class TestSemanticIntegration:
    """Verify that semantic.py re-exports work and type checking uses TypeKind."""

    def test_reimports(self) -> None:
        from mapanare.semantic import (
            BUILTIN_FUNCTIONS,
            BUILTIN_GENERIC_TYPES,
            PRIMITIVE_TYPES,
            TypeInfo,
            TypeKind,
        )

        assert TypeKind.INT is not None
        assert "Int" in PRIMITIVE_TYPES
        assert "print" in BUILTIN_FUNCTIONS

    def test_no_string_type_comparisons_in_semantic(self) -> None:
        """Verify that semantic.py no longer uses .name for type comparisons."""
        import inspect

        from mapanare import semantic

        source = inspect.getsource(semantic.SemanticChecker)
        # These patterns indicate old-style string comparisons
        # .name == "Int" or .name == "Float" etc. should not appear
        for prim in ("Int", "Float", "Bool", "String", "Char", "Void"):
            pattern = f'.name == "{prim}"'
            assert (
                pattern not in source
            ), f"Found old-style string comparison {pattern} in SemanticChecker"
        # Also check .name != patterns
        for prim in ("Int", "Float", "Bool", "String", "Char", "Void"):
            pattern = f'.name != "{prim}"'
            assert (
                pattern not in source
            ), f"Found old-style string comparison {pattern} in SemanticChecker"
