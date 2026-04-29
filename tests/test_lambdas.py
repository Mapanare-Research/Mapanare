"""v5.15.0 Te.2.F — terse lambda syntax.

``|x| body``, ``|x, y| body``, ``|| body`` lower to the same
``LambdaExpr`` AST node as the legacy ``(x) => body`` form.
"""

from __future__ import annotations

from mapanare.ast_nodes import FnDef, LambdaExpr, LetBinding, Param, Program
from mapanare.parser import parse


def _first_let_value(program: Program, fn_name: str) -> object:
    for d in program.definitions:
        if isinstance(d, FnDef) and d.name == fn_name:
            for stmt in d.body.stmts:
                if isinstance(stmt, LetBinding):
                    return stmt.value
    raise AssertionError("no let in fn")


def test_terse_lambda_one_param() -> None:
    program = parse("fn main() { let f = |x| x * 2 }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    assert [p.name for p in val.params] == ["x"]


def test_terse_lambda_two_params() -> None:
    program = parse("fn main() { let f = |a, b| a + b }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    assert [p.name for p in val.params] == ["a", "b"]


def test_terse_lambda_zero_params() -> None:
    program = parse("fn main() { let f = || 42 }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    assert val.params == []


def test_terse_lambda_three_params() -> None:
    program = parse("fn main() { let f = |a, b, c| a + b + c }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    assert [p.name for p in val.params] == ["a", "b", "c"]


def test_terse_lambda_params_are_untyped() -> None:
    """Terse-lambda parameters carry no type annotation — types flow in
    via call-site inference / closure capture."""
    program = parse("fn main() { let f = |x, y| x + y }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    for p in val.params:
        assert isinstance(p, Param)
        assert p.type_annotation is None


def test_legacy_long_form_still_parses() -> None:
    program = parse("fn main() { let f = (x) => x * 2 }")
    val = _first_let_value(program, "main")
    assert isinstance(val, LambdaExpr)
    assert [p.name for p in val.params] == ["x"]
