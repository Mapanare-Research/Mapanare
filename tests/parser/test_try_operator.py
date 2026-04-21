"""v4.33.0 Phase 3.2 — Parser tests for the ``?`` operator.

Positive: the parser produces an ``ErrorPropExpr`` node for valid ``expr?``
usage. Negative: ``?`` without an operand or in invalid positions is rejected.
"""

from __future__ import annotations

import textwrap

import pytest

from mapanare.ast_nodes import ErrorPropExpr, FnDef
from mapanare.parser import parse


def _parse_fn_body_expr(source: str) -> object:
    """Parse source, return the first expression in the first function's body."""
    tree = parse(source)
    for defn in tree.definitions:
        if isinstance(defn, FnDef):
            body = defn.body
            if body and body.stmts:
                stmt = body.stmts[0]
                # LetBinding → value, ExprStmt → expr, ReturnStmt → value
                if hasattr(stmt, "value") and stmt.value is not None:
                    return stmt.value
                if hasattr(stmt, "expr"):
                    return stmt.expr
    return None


class TestTryOperatorParses:
    def test_simple_try_on_call(self) -> None:
        source = textwrap.dedent("""\
            fn f(x: Result<Int, String>) -> Result<Int, String> {
                let v = x?
                return Ok(v)
            }
        """)
        tree = parse(source)
        fn = [d for d in tree.definitions if isinstance(d, FnDef)][0]
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt.value, ErrorPropExpr)

    def test_try_on_function_call(self) -> None:
        source = textwrap.dedent("""\
            fn might_fail() -> Result<Int, String> { return Ok(1) }
            fn f() -> Result<Int, String> {
                let v = might_fail()?
                return Ok(v)
            }
        """)
        tree = parse(source)
        fns = [d for d in tree.definitions if isinstance(d, FnDef)]
        f = [fn for fn in fns if fn.name == "f"][0]
        let_stmt = f.body.stmts[0]
        assert isinstance(let_stmt.value, ErrorPropExpr)

    def test_try_preserves_inner_expr(self) -> None:
        source = textwrap.dedent("""\
            fn f(x: Result<Int, String>) -> Result<Int, String> {
                let v = x?
                return Ok(v)
            }
        """)
        tree = parse(source)
        fn = [d for d in tree.definitions if isinstance(d, FnDef)][0]
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt.value, ErrorPropExpr)
        # The inner expression should be an identifier 'x'
        inner = let_stmt.value.expr
        assert hasattr(inner, "name") and inner.name == "x"


class TestTryOperatorRejects:
    def test_standalone_question_mark_is_error(self) -> None:
        source = textwrap.dedent("""\
            fn f() -> Int {
                ?
                return 0
            }
        """)
        with pytest.raises(Exception):
            parse(source)

    def test_question_mark_as_binary_op_is_error(self) -> None:
        source = textwrap.dedent("""\
            fn f(x: Int, y: Int) -> Int {
                return x ? y
            }
        """)
        with pytest.raises(Exception):
            parse(source)
