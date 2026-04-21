"""Semantic tests for tensor literal type checking (v4.42.0)."""

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _check(src: str) -> SemanticChecker:
    ast = parse(f"fn main() {{ {src} }}")
    checker = SemanticChecker()
    checker.check(ast)
    return checker


class TestTensorLiteralSemantics:
    def test_float_tensor_no_errors(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0, 3.0]")
        assert len(c.errors) == 0

    def test_int_tensor_no_errors(self):
        c = _check("let a = Tensor<Int>[10, 20, 30]")
        assert len(c.errors) == 0

    def test_int_to_float_promotion(self):
        c = _check("let a = Tensor<Float>[1, 2, 3]")
        assert len(c.errors) == 0

    def test_2d_tensor_no_errors(self):
        c = _check("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]")
        assert len(c.errors) == 0

    def test_3d_tensor_no_errors(self):
        c = _check("let a = Tensor<Int>[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]")
        assert len(c.errors) == 0

    def test_tensor_with_type_annotation(self):
        c = _check("let a: Tensor<Float>[2, 3] = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]")
        assert len(c.errors) == 0

    def test_negated_elements(self):
        c = _check("let a = Tensor<Float>[-1.0, 2.0]")
        assert len(c.errors) == 0
