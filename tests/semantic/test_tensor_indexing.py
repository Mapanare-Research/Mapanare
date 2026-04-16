"""Semantic tests for tensor indexing (v4.43.0)."""

import pytest

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _check(src: str) -> SemanticChecker:
    ast = parse(f"fn main() {{ {src} }}")
    checker = SemanticChecker()
    checker.check(ast)
    return checker


class TestTensorIndexingSemantics:
    def test_2d_index_no_error(self):
        c = _check("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let x = a[0, 1]")
        assert len(c.errors) == 0

    def test_1d_index_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0, 3.0]; let x = a[0]")
        assert len(c.errors) == 0

    def test_3d_index_no_error(self):
        c = _check(
            "let a = Tensor<Float>[[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]; let x = a[0, 1, 0]"
        )
        assert len(c.errors) == 0

    def test_under_rank_is_error(self):
        c = _check("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let x = a[0]")
        assert any("rank mismatch" in str(e) for e in c.errors)

    def test_over_rank_is_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let x = a[0, 1]")
        assert any("rank mismatch" in str(e) for e in c.errors)

    def test_list_single_index_still_works(self):
        c = _check("let a = [1, 2, 3]; let x = a[0]")
        assert len(c.errors) == 0

    def test_list_multi_index_is_error(self):
        c = _check("let a = [1, 2, 3]; let x = a[0, 1]")
        assert any("multi-index not supported" in str(e) for e in c.errors)

    def test_tensor_assignment(self):
        c = _check("let mut a = Tensor<Float>[[0.0, 0.0], [0.0, 0.0]]; a[0, 1] = 42.0")
        assert len(c.errors) == 0
