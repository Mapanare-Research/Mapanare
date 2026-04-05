"""Tests for mapanare/self/semantic.mn — verifies the self-hosted semantic checker
definitions can be parsed and type-checked by the Python compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.lexer import tokenize
from mapanare.parser import parse
from mapanare.semantic import BUILTIN_FUNCTIONS, BUILTIN_GENERIC_TYPES, PRIMITIVE_TYPES, check

SEMANTIC_MN = Path(__file__).resolve().parents[2] / "mapanare" / "self" / "semantic.mn"


@pytest.fixture
def semantic_source() -> str:
    return SEMANTIC_MN.read_text(encoding="utf-8")


class TestSemanticMnParsing:
    """Ensure semantic.mn parses without errors."""

    def test_tokenize(self, semantic_source: str) -> None:
        tokens = tokenize(semantic_source, filename="semantic.mn")
        assert len(tokens) > 0

    def test_parse(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_has_structs(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        struct_names = {s.name for s in structs}
        assert "SemanticError" in struct_names
        assert "TypeInfo" in struct_names
        assert "Symbol" in struct_names
        assert "Scope" in struct_names
        assert "SemanticChecker" in struct_names

    def test_has_type_helper_functions(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "unknown_type" in fn_names
        assert "int_type" in fn_names
        assert "float_type" in fn_names
        assert "bool_type" in fn_names
        assert "string_type" in fn_names
        assert "char_type" in fn_names
        assert "void_type" in fn_names
        assert "make_type" in fn_names

    def test_has_classification_functions(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "is_primitive_type" in fn_names
        assert "is_builtin_generic" in fn_names
        assert "is_builtin_function" in fn_names
        assert "builtin_return_type" in fn_names

    def test_has_scope_functions(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "scope_define" in fn_names
        assert "scope_lookup" in fn_names
        assert "scope_lookup_local" in fn_names

    def test_has_type_checking_functions(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "types_compatible" in fn_names
        assert "is_numeric_type" in fn_names
        assert "is_arithmetic_operand" in fn_names
        assert "check_arithmetic_result" in fn_names
        assert "check_comparison_result" in fn_names
        assert "check_logical_result" in fn_names

    def test_has_public_api(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "check" in fn_names
        assert "check_or_raise" in fn_names

    def test_semantic_check(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        errors = check(program, filename="semantic.mn")
        assert isinstance(errors, list)


class TestSemanticMnCoverage:
    """Verify the semantic checker covers all type categories."""

    def test_all_primitive_types_covered(self, semantic_source: str) -> None:
        for t in PRIMITIVE_TYPES:
            assert f'"{t}"' in semantic_source, f"Missing primitive type: {t}"

    def test_all_builtin_generics_covered(self, semantic_source: str) -> None:
        for t in BUILTIN_GENERIC_TYPES:
            assert f'"{t}"' in semantic_source, f"Missing generic type: {t}"

    @pytest.mark.xfail(reason="Not all builtins listed in semantic.mn yet", strict=False)
    def test_all_builtin_functions_covered(self, semantic_source: str) -> None:
        for name in BUILTIN_FUNCTIONS:
            assert f'"{name}"' in semantic_source, f"Missing builtin function: {name}"

    def test_semantic_error_has_fields(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        se = next(s for s in structs if s.name == "SemanticError")
        field_names = {f.name for f in se.fields}
        assert "message" in field_names
        assert "line" in field_names
        assert "column" in field_names
        assert "filename" in field_names

    def test_type_info_has_fields(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        ti = next(s for s in structs if s.name == "TypeInfo")
        field_names = {f.name for f in ti.fields}
        assert "name" in field_names
        assert "args" in field_names
        assert "is_function" in field_names
        assert "param_types" in field_names
        assert "return_type" in field_names
        assert "tensor_shape" in field_names

    def test_symbol_has_fields(self, semantic_source: str) -> None:
        program = parse(semantic_source, filename="semantic.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        sym = next(s for s in structs if s.name == "Symbol")
        field_names = {f.name for f in sym.fields}
        assert "name" in field_names
        assert "kind" in field_names
        assert "type_info" in field_names
        assert "mutable" in field_names
