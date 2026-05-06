"""v5.45.0 Ts.3.A — `[start..end:step]` grammar + AST + parser tests.

Covers:
- bare stepped range `a..b:s` produces RangeExpr with step set
- inclusive stepped range `a..=b:s` produces RangeExpr(inclusive=True)
- non-stepped range still parses unchanged (regression gate)
- step propagates from RangeExpr → IndexItem inside `arr[a..b:s]`
- step accepts arbitrary expressions, not just int literals

Falsifiability — revert mapanare/mapanare.lark::range_step_op (delete
the new productions) and every test fails with a parse error;
revert mapanare/parser.py::range_step_op constructor and the AST
shape tests fail (RangeExpr.step stays None).
"""
from __future__ import annotations

import pytest

from mapanare.ast_nodes import IndexExpr, IntLiteral, RangeExpr
from mapanare.parser import parse


def _first_let_value(src: str):
    """Extract the first `let X = EXPR` value from a single-fn program."""
    ast = parse(src)
    fn = ast.definitions[0]
    return fn.body.stmts[0].value


def _let_at(src: str, idx: int):
    ast = parse(src)
    fn = ast.definitions[0]
    return fn.body.stmts[idx].value


def test_bare_stepped_range() -> None:
    val = _first_let_value("fn main():\n    let r = 0..10:2\n")
    assert isinstance(val, RangeExpr)
    assert val.inclusive is False
    assert isinstance(val.start, IntLiteral) and val.start.value == 0
    assert isinstance(val.end, IntLiteral) and val.end.value == 10
    assert isinstance(val.step, IntLiteral) and val.step.value == 2


def test_inclusive_stepped_range() -> None:
    val = _first_let_value("fn main():\n    let r = 0..=9:3\n")
    assert isinstance(val, RangeExpr)
    assert val.inclusive is True
    assert isinstance(val.step, IntLiteral) and val.step.value == 3


def test_non_stepped_range_still_parses() -> None:
    """Regression: existing v4.x range_op surface unchanged."""
    val = _first_let_value("fn main():\n    let r = 0..10\n")
    assert isinstance(val, RangeExpr)
    assert val.inclusive is False
    assert val.step is None


def test_inclusive_non_stepped_range_still_parses() -> None:
    """Regression: existing v4.x range_incl_op surface unchanged."""
    val = _first_let_value("fn main():\n    let r = 0..=10\n")
    assert isinstance(val, RangeExpr)
    assert val.inclusive is True
    assert val.step is None


def test_step_propagates_through_index() -> None:
    """`arr[a..b:s]` — step survives the RangeExpr→IndexItem translation."""
    src = (
        "fn main():\n"
        "    let t = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]\n"
        "    let s = t[0..6:2]\n"
        "    print(str(tensor_size(s)))\n"
    )
    val = _let_at(src, 1)
    assert isinstance(val, IndexExpr)
    assert len(val.indices) == 1
    idx = val.indices[0]
    assert idx.kind == "range"
    assert idx.start is not None and isinstance(idx.start, IntLiteral)
    assert idx.start.value == 0
    assert idx.end is not None and isinstance(idx.end, IntLiteral)
    assert idx.end.value == 6
    assert idx.step is not None and isinstance(idx.step, IntLiteral)
    assert idx.step.value == 2


def test_index_without_step_has_step_none() -> None:
    """`arr[a..b]` — IndexItem.step stays None on non-stepped index."""
    src = (
        "fn main():\n"
        "    let t = Tensor<Float>[1.0, 2.0, 3.0, 4.0]\n"
        "    let s = t[0..4]\n"
    )
    val = _let_at(src, 1)
    assert isinstance(val, IndexExpr)
    idx = val.indices[0]
    assert idx.kind == "range"
    assert idx.step is None


@pytest.mark.parametrize(
    "step_expr,expected_step_kind",
    [
        ("2", IntLiteral),
        ("step", None),  # bare identifier — non-IntLiteral expression
        ("(step + 1)", None),
    ],
)
def test_step_accepts_expressions(step_expr: str, expected_step_kind: type | None) -> None:
    """The grammar accepts any `add_expr` for step; lower-time check
    handles literal-vs-non-literal step validation."""
    src = (
        "fn main():\n"
        "    let step = 2\n"
        f"    let r = 0..10:{step_expr}\n"
    )
    val = _let_at(src, 1)
    assert isinstance(val, RangeExpr)
    assert val.step is not None
    if expected_step_kind is not None:
        assert isinstance(val.step, expected_step_kind)


def test_multi_index_with_stepped_range() -> None:
    """2D tensor index with one stepped axis + one scalar axis."""
    src = (
        "fn main():\n"
        "    let t = Tensor<Float>[[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]\n"
        "    let s = t[0..2, 0..4:2]\n"
    )
    val = _let_at(src, 1)
    assert isinstance(val, IndexExpr)
    assert len(val.indices) == 2
    assert val.indices[0].kind == "range" and val.indices[0].step is None
    assert val.indices[1].kind == "range" and val.indices[1].step is not None
    assert isinstance(val.indices[1].step, IntLiteral)
    assert val.indices[1].step.value == 2
