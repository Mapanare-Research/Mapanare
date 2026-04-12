"""Semantic tests for tensor slicing and reductions (v4.45.0)."""

import pytest

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _check(src: str) -> SemanticChecker:
    ast = parse(f"fn main() {{ {src} }}")
    checker = SemanticChecker()
    checker.check(ast)
    return checker


class TestTensorReductionSemantics:
    def test_sum_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let x = a.sum()")
        assert len(c.errors) == 0

    def test_mean_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let x = a.mean()")
        assert len(c.errors) == 0

    def test_max_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let x = a.max()")
        assert len(c.errors) == 0

    def test_argmax_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0]; let x = a.argmax()")
        assert len(c.errors) == 0


class TestTensorSlicingSemantics:
    def test_range_slice_no_error(self):
        c = _check("let a = Tensor<Float>[1.0, 2.0, 3.0]; let s = a[0..2]")
        assert len(c.errors) == 0

    def test_wildcard_slice_no_error(self):
        c = _check("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let s = a[0, _]")
        assert len(c.errors) == 0

    def test_range_and_wildcard_no_error(self):
        c = _check("let a = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]; let s = a[0..1, _]")
        assert len(c.errors) == 0
