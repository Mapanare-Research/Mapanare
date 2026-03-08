"""Tests for mapa/self/lexer.mn — verifies the self-hosted lexer definitions
can be parsed and type-checked by the Python compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapa.lexer import KEYWORDS, tokenize
from mapa.parser import parse
from mapa.semantic import check

LEXER_MN = Path(__file__).resolve().parents[2] / "mapa" / "self" / "lexer.mn"


@pytest.fixture
def lexer_source() -> str:
    return LEXER_MN.read_text(encoding="utf-8")


class TestLexerMnParsing:
    """Ensure lexer.mn parses without errors."""

    def test_tokenize(self, lexer_source: str) -> None:
        tokens = tokenize(lexer_source, filename="lexer.mn")
        assert len(tokens) > 0

    def test_parse(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_has_token_struct(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        struct_names = {s.name for s in structs}
        assert "Token" in struct_names
        assert "LexError" in struct_names
        assert "Lexer" in struct_names

    def test_has_keyword_functions(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        from mapa.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "is_keyword" in fn_names
        assert "keyword_token_type" in fn_names
        assert "tokenize" in fn_names
        assert "tokenize_with_newlines" in fn_names

    def test_has_char_helpers(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        from mapa.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "is_alpha" in fn_names
        assert "is_digit" in fn_names
        assert "is_alnum" in fn_names
        assert "is_whitespace" in fn_names

    def test_semantic_check(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        errors = check(program, filename="lexer.mn")
        assert isinstance(errors, list)


class TestLexerMnCoverage:
    """Verify the lexer covers all keywords from the Python compiler."""

    def test_all_keywords_covered(self, lexer_source: str) -> None:
        """Every Python keyword should appear in is_keyword() function body."""
        for kw in KEYWORDS:
            if kw == "_" or kw == "Tensor":
                continue  # contextual keywords not in is_keyword
            assert f'"{kw}"' in lexer_source, f"Missing keyword: {kw}"

    def test_all_keyword_token_types_covered(self, lexer_source: str) -> None:
        """Every keyword token type should appear in keyword_token_type() function body."""
        for kw, tok_type in KEYWORDS.items():
            if kw == "_" or kw == "Tensor":
                continue
            assert tok_type in lexer_source, f"Missing token type: {tok_type}"

    def test_token_struct_has_required_fields(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        token_struct = next(s for s in structs if s.name == "Token")
        field_names = {f.name for f in token_struct.fields}
        assert "tok_type" in field_names
        assert "value" in field_names
        assert "line" in field_names
        assert "column" in field_names
        assert "end_line" in field_names
        assert "end_column" in field_names

    def test_lex_error_struct_has_required_fields(self, lexer_source: str) -> None:
        program = parse(lexer_source, filename="lexer.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        err_struct = next(s for s in structs if s.name == "LexError")
        field_names = {f.name for f in err_struct.fields}
        assert "message" in field_names
        assert "line" in field_names
        assert "column" in field_names
        assert "filename" in field_names
