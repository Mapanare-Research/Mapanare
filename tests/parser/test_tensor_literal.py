"""Parser tests for tensor literal syntax (v4.42.0)."""

import pytest

from mapanare.ast_nodes import TensorLiteral, UnaryExpr
from mapanare.parser import ParseError, parse


def _tensor(src: str) -> TensorLiteral:
    """Parse a single tensor literal from a let statement."""
    ast = parse(f"fn main() {{ {src} }}")
    return ast.definitions[0].body.stmts[0].value


class TestTensorLiteralParsing:
    def test_1d_float(self):
        t = _tensor("let a = Tensor<Float>[1.0, 2.0, 3.0]")
        assert isinstance(t, TensorLiteral)
        assert t.shape == [3]
        assert len(t.elements) == 3
        assert t.element_type.name == "Float"

    def test_2d_float(self):
        t = _tensor("let a = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]")
        assert t.shape == [2, 3]
        assert len(t.elements) == 6

    def test_3d_int(self):
        t = _tensor("let a = Tensor<Int>[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]")
        assert t.shape == [2, 2, 2]
        assert len(t.elements) == 8
        assert t.element_type.name == "Int"

    def test_row_major_flattening(self):
        t = _tensor("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]")
        vals = [e.value for e in t.elements]
        assert vals == [1.0, 2.0, 3.0, 4.0]

    def test_trailing_comma(self):
        t = _tensor("let a = Tensor<Float>[1.0, 2.0,]")
        assert t.shape == [2]
        assert len(t.elements) == 2

    def test_negated_elements(self):
        t = _tensor("let a = Tensor<Float>[-1.0, 2.0]")
        assert t.shape == [2]
        assert len(t.elements) == 2
        assert isinstance(t.elements[0], UnaryExpr)
        assert t.elements[0].op == "-"

    def test_variable_elements(self):
        ast = parse("fn main() { let x = 1.0; let a = Tensor<Float>[x, 2.0] }")
        t = ast.definitions[0].body.stmts[1].value
        assert isinstance(t, TensorLiteral)
        assert t.shape == [2]

    def test_paren_expr_elements(self):
        t = _tensor("let a = Tensor<Float>[(1.0), (2.0)]")
        assert t.shape == [2]
        assert len(t.elements) == 2

    def test_single_element(self):
        t = _tensor("let a = Tensor<Float>[42.0]")
        assert t.shape == [1]
        assert len(t.elements) == 1


class TestTensorLiteralJaggedDetection:
    def test_jagged_is_parse_error(self):
        with pytest.raises(ParseError, match="shape mismatch"):
            parse("fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0]] }")

    def test_jagged_3d(self):
        with pytest.raises(ParseError, match="shape mismatch"):
            parse("fn main() { let a = Tensor<Float>[[[1.0], [2.0, 3.0]], [[4.0], [5.0]]] }")

    def test_empty_body_is_parse_error(self):
        with pytest.raises(Exception):
            parse("fn main() { let a = Tensor<Float>[] }")


class TestTensorLiteralWithTypeAnnotation:
    def test_type_and_literal_coexist(self):
        src = (
            "fn main() { let a: Tensor<Float>[2, 3] = "
            "Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]] }"
        )
        ast = parse(src)
        t = ast.definitions[0].body.stmts[0].value
        assert isinstance(t, TensorLiteral)
        assert t.shape == [2, 3]
