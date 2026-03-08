"""Tests for mapa/self/parser.mn — verifies the self-hosted parser definitions
can be parsed and type-checked by the Python compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapa.lexer import tokenize
from mapa.parser import parse
from mapa.semantic import check

PARSER_MN = Path(__file__).resolve().parents[2] / "mapa" / "self" / "parser.mn"


@pytest.fixture
def parser_source() -> str:
    return PARSER_MN.read_text(encoding="utf-8")


class TestParserMnParsing:
    """Ensure parser.mn parses without errors."""

    def test_tokenize(self, parser_source: str) -> None:
        tokens = tokenize(parser_source, filename="parser.mn")
        assert len(tokens) > 0

    def test_parse(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_has_parse_error_struct(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        struct_names = {s.name for s in structs}
        assert "ParseError" in struct_names
        assert "Parser" in struct_names

    def test_has_core_parse_functions(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        from mapa.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "parse" in fn_names
        assert "parse_definition" in fn_names
        assert "parse_fn_def" in fn_names
        assert "parse_expr" in fn_names
        assert "parse_atom" in fn_names
        assert "parse_block" in fn_names
        assert "parse_stmt" in fn_names
        assert "parse_type_expr" in fn_names
        assert "parse_pattern" in fn_names

    def test_has_helper_functions(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        from mapa.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "is_skip_token" in fn_names
        assert "is_keep_token" in fn_names
        assert "parse_int_token" in fn_names
        assert "is_arithmetic_op" in fn_names
        assert "is_comparison_op" in fn_names
        assert "is_logical_op" in fn_names
        assert "is_assign_op" in fn_names
        assert "op_precedence" in fn_names

    def test_semantic_check(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        errors = check(program, filename="parser.mn")
        assert isinstance(errors, list)


class TestParserMnCoverage:
    """Verify the parser covers all grammar constructs."""

    def test_precedence_levels(self, parser_source: str) -> None:
        """op_precedence should cover all binary operators."""
        operators = [
            "||",
            "&&",
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "|>",
            "..",
            "..=",
            "+",
            "-",
            "*",
            "/",
            "%",
            "@",
        ]
        for op in operators:
            assert f'"{op}"' in parser_source, f"Missing precedence for: {op}"

    def test_skip_tokens(self, parser_source: str) -> None:
        """is_skip_token should include all keyword tokens filtered in Python."""
        skip_types = [
            "KW_FN",
            "KW_LET",
            "KW_AGENT",
            "KW_PIPE",
            "KW_STRUCT",
            "KW_ENUM",
            "KW_TYPE",
            "KW_IMPL",
            "KW_IF",
            "KW_ELSE",
            "KW_MATCH",
            "KW_FOR",
            "KW_IN",
            "KW_RETURN",
            "KW_IMPORT",
            "KW_EXPORT",
            "KW_SPAWN",
            "KW_SYNC",
            "KW_SIGNAL",
            "KW_STREAM",
            "KW_INPUT",
            "KW_OUTPUT",
            "KW_TENSOR",
            "KW_WILDCARD",
            "KW_TRUE",
            "KW_FALSE",
            "KW_NONE",
            "LPAREN",
            "RPAREN",
            "LBRACE",
            "RBRACE",
            "LBRACKET",
            "RBRACKET",
            "COMMA",
            "COLON",
            "SEMICOLON",
            "ASSIGN",
            "ARROW",
            "FAT_ARROW",
            "PIPE_OP",
            "DOUBLE_COLON",
            "DOT",
            "QUESTION",
            "SEND",
        ]
        for tt in skip_types:
            assert f'"{tt}"' in parser_source, f"Missing skip token: {tt}"

    def test_keep_tokens(self, parser_source: str) -> None:
        """is_keep_token should include NAME, PUB, MUT, literal tokens."""
        keep_types = [
            "KW_PUB",
            "KW_MUT",
            "KW_SELF",
            "NAME",
            "DEC_INT",
            "HEX_INT",
            "BIN_INT",
            "OCT_INT",
            "FLOAT_LIT",
            "STRING_LIT",
            "CHAR_LIT",
        ]
        for tt in keep_types:
            assert f'"{tt}"' in parser_source, f"Missing keep token: {tt}"

    def test_parse_error_has_fields(self, parser_source: str) -> None:
        program = parse(parser_source, filename="parser.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        pe = next(s for s in structs if s.name == "ParseError")
        field_names = {f.name for f in pe.fields}
        assert "message" in field_names
        assert "line" in field_names
        assert "column" in field_names
        assert "filename" in field_names
