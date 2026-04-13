"""v4.55.0: Parser tests for ``const`` keyword.

The file that v4.26.0's CHANGELOG claimed existed — now it does for real.
"""

from __future__ import annotations

from mapanare.ast_nodes import ConstDef, IntLiteral, FloatLiteral, StringLiteral, NamedType
from mapanare.parser import parse


class TestConstParsing:
    def test_const_int_parses(self):
        prog = parse("const N: Int = 100\nfn main() {}\n", filename="test.mn")
        const_defs = [d for d in prog.definitions if isinstance(d, ConstDef)]
        assert len(const_defs) == 1
        assert const_defs[0].name == "N"
        assert isinstance(const_defs[0].value, IntLiteral)
        assert const_defs[0].value.value == 100

    def test_const_float_parses(self):
        prog = parse("const PI: Float = 3.14\nfn main() {}\n", filename="test.mn")
        const_defs = [d for d in prog.definitions if isinstance(d, ConstDef)]
        assert len(const_defs) == 1
        assert const_defs[0].name == "PI"
        assert isinstance(const_defs[0].value, FloatLiteral)

    def test_const_string_parses(self):
        prog = parse('const GREETING: String = "hello"\nfn main() {}\n', filename="test.mn")
        const_defs = [d for d in prog.definitions if isinstance(d, ConstDef)]
        assert len(const_defs) == 1
        assert const_defs[0].name == "GREETING"
        assert isinstance(const_defs[0].value, StringLiteral)

    def test_const_type_expr_preserved(self):
        """v4.26.0 bug: parser collapsed TypeExpr to .name string. Verify full TypeExpr."""
        prog = parse("const N: Int = 42\nfn main() {}\n", filename="test.mn")
        const_defs = [d for d in prog.definitions if isinstance(d, ConstDef)]
        assert len(const_defs) == 1
        assert const_defs[0].type_expr is not None
        assert isinstance(const_defs[0].type_expr, NamedType)
        assert const_defs[0].type_expr.name == "Int"

    def test_const_with_expression_initializer(self):
        src = "const N: Int = 10\nconst D: Int = N * 2\nfn main() {}\n"
        prog = parse(src, filename="test.mn")
        const_defs = [d for d in prog.definitions if isinstance(d, ConstDef)]
        assert len(const_defs) == 2
        assert const_defs[1].name == "D"

    def test_const_without_type_annotation_is_parse_error(self):
        """v4.55.0: const requires explicit type annotation."""
        from mapanare.parser import ParseError
        import pytest

        with pytest.raises(ParseError):
            parse("const N = 100\nfn main() {}\n", filename="test.mn")
