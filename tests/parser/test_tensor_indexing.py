"""Parser tests for tensor multi-index syntax (v4.43.0)."""

import pytest

from mapanare.ast_nodes import IndexExpr, IntLiteral, Identifier
from mapanare.parser import parse


def _idx(src: str) -> IndexExpr:
    ast = parse(f"fn main() {{ {src} }}")
    return ast.definitions[0].body.stmts[-1].value


class TestMultiIndexParsing:
    def test_single_index(self):
        e = _idx("let a = [1]; let x = a[0]")
        assert isinstance(e, IndexExpr)
        assert len(e.indices) == 1

    def test_two_indices(self):
        e = _idx("let t = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let x = t[1, 0]")
        assert isinstance(e, IndexExpr)
        assert len(e.indices) == 2

    def test_three_indices(self):
        e = _idx("let t = Tensor<Int>[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]; let x = t[0, 1, 0]")
        assert isinstance(e, IndexExpr)
        assert len(e.indices) == 3

    def test_variable_indices(self):
        ast = parse("fn main() { let t = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let i = 0; let j = 1; let x = t[i, j] }")
        idx = ast.definitions[0].body.stmts[3].value
        assert isinstance(idx, IndexExpr)
        assert len(idx.indices) == 2
        assert isinstance(idx.indices[0], Identifier)

    def test_list_single_index_preserved(self):
        e = _idx("let a = [1, 2, 3]; let x = a[1]")
        assert isinstance(e, IndexExpr)
        assert len(e.indices) == 1
