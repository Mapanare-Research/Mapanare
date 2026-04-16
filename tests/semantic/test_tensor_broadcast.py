"""Semantic tests for tensor broadcasting (v4.44.0)."""

import pytest

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker
from mapanare.types import broadcast_shape


def _check(src: str) -> SemanticChecker:
    ast = parse(f"fn main() {{ {src} }}")
    checker = SemanticChecker()
    checker.check(ast)
    return checker


class TestBroadcastShapeHelper:
    def test_same_shape(self):
        assert broadcast_shape((3, 4), (3, 4)) == (3, 4)

    def test_row_column(self):
        assert broadcast_shape((3, 1), (1, 4)) == (3, 4)

    def test_rank_extension(self):
        assert broadcast_shape((3, 4), (4,)) == (3, 4)

    def test_scalar_like(self):
        assert broadcast_shape((1,), (5,)) == (5,)

    def test_3d_1d(self):
        assert broadcast_shape((2, 3, 4), (4,)) == (2, 3, 4)

    def test_complex_broadcast(self):
        assert broadcast_shape((5, 1, 4), (1, 3, 1)) == (5, 3, 4)

    def test_incompatible(self):
        assert broadcast_shape((3, 4), (3, 5)) is None

    def test_incompatible_1d(self):
        assert broadcast_shape((2,), (3,)) is None

    def test_empty_shapes(self):
        assert broadcast_shape((), ()) == ()

    def test_0d_broadcast(self):
        assert broadcast_shape((), (3,)) == (3,)


class TestTensorBroadcastSemantics:
    def test_same_shape_no_error(self):
        c = _check(
            "let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let b = Tensor<Float>[[5.0, 6.0], [7.0, 8.0]]; let c = a + b"
        )
        assert len(c.errors) == 0

    def test_incompatible_shapes_error(self):
        c = _check(
            "let a = Tensor<Float>[[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0], [9.0, 10.0, 11.0, 12.0]]; "
            "let b = Tensor<Float>[[1.0, 2.0, 3.0, 4.0, 5.0], [6.0, 7.0, 8.0, 9.0, 10.0], [11.0, 12.0, 13.0, 14.0, 15.0]]; "
            "let c = a + b"
        )
        assert any("not broadcast-compatible" in str(e) for e in c.errors)

    def test_error_names_dimension(self):
        c = _check(
            "let a = Tensor<Float>[[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0], [9.0, 10.0, 11.0, 12.0]]; "
            "let b = Tensor<Float>[[1.0, 2.0, 3.0, 4.0, 5.0], [6.0, 7.0, 8.0, 9.0, 10.0], [11.0, 12.0, 13.0, 14.0, 15.0]]; "
            "let c = a + b"
        )
        assert any("dimension" in str(e) for e in c.errors)

    def test_scalar_tensor_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let c = a + 5.0")
        assert len(c.errors) == 0

    def test_tensor_scalar_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let c = 5.0 + a")
        assert len(c.errors) == 0

    def test_all_four_ops(self):
        for op in ["+", "-", "*", "/"]:
            c = _check(
                f"let a = Tensor<Float>[1.0, 2.0]; let b = Tensor<Float>[3.0, 4.0]; let c = a {op} b"
            )
            assert len(c.errors) == 0, f"op {op} failed: {c.errors}"

    def test_broadcast_compatible_rank_extension(self):
        c = _check(
            "let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; "
            "let b = Tensor<Float>[10.0, 20.0]; "
            "let c = a + b"
        )
        assert len(c.errors) == 0
