"""v4.68.0 Phase 7 — Parser tests for ``async fn`` and ``await`` expressions.

Positive: the parser produces ``AsyncFnDef`` and ``AwaitExpr`` nodes for valid
source. Negative: malformed async/await is rejected. Precedence: ``await``
binds at unary level (tighter than binary, looser than postfix).
"""

from __future__ import annotations

import textwrap

import pytest

from mapanare.ast_nodes import (
    AsyncFnDef,
    AwaitExpr,
    BinaryExpr,
    CallExpr,
    FieldAccessExpr,
    FnDef,
    Identifier,
    LetBinding,
    ReturnStmt,
)
from mapanare.parser import parse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_first_async_fn(source: str) -> AsyncFnDef:
    """Parse source and return the first AsyncFnDef."""
    tree = parse(source)
    for defn in tree.definitions:
        if isinstance(defn, AsyncFnDef):
            return defn
    raise AssertionError("No AsyncFnDef found in parsed source")


def _get_first_fn_body_expr(source: str) -> object:
    """Parse source, return the first expression in the first function's body."""
    tree = parse(source)
    for defn in tree.definitions:
        if isinstance(defn, (FnDef, AsyncFnDef)):
            body = defn.body
            if body and body.stmts:
                stmt = body.stmts[0]
                if hasattr(stmt, "value") and stmt.value is not None:
                    return stmt.value
                if hasattr(stmt, "expr"):
                    return stmt.expr
    return None


# ---------------------------------------------------------------------------
# async fn definition tests
# ---------------------------------------------------------------------------


class TestAsyncFnDef:
    def test_basic_async_fn(self) -> None:
        source = textwrap.dedent("""\
            async fn fetch() -> String {
                return "hello"
            }
        """)
        fn = _get_first_async_fn(source)
        assert fn.name == "fetch"
        assert fn.params == []

    def test_async_fn_with_params(self) -> None:
        source = textwrap.dedent("""\
            async fn fetch(url: String, timeout: Int) -> String {
                return url
            }
        """)
        fn = _get_first_async_fn(source)
        assert fn.name == "fetch"
        assert len(fn.params) == 2
        assert fn.params[0].name == "url"
        assert fn.params[1].name == "timeout"

    def test_async_fn_no_return_type(self) -> None:
        source = textwrap.dedent("""\
            async fn do_work() {
                let x = 1
            }
        """)
        fn = _get_first_async_fn(source)
        assert fn.name == "do_work"
        assert fn.return_type is None

    def test_pub_async_fn(self) -> None:
        source = textwrap.dedent("""\
            pub async fn public_fetch(url: String) -> String {
                return url
            }
        """)
        fn = _get_first_async_fn(source)
        assert fn.name == "public_fetch"
        assert fn.public is True

    def test_async_fn_with_type_params(self) -> None:
        source = textwrap.dedent("""\
            async fn transform<T>(x: T) -> T {
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        assert fn.name == "transform"
        assert fn.type_params == ["T"]

    def test_async_fn_is_not_fn_def(self) -> None:
        """AsyncFnDef is a separate AST node from FnDef."""
        source = textwrap.dedent("""\
            async fn a() -> Int { return 1 }
            fn b() -> Int { return 2 }
        """)
        tree = parse(source)
        defns = tree.definitions
        assert isinstance(defns[0], AsyncFnDef)
        assert isinstance(defns[1], FnDef)
        assert defns[0].name == "a"
        assert defns[1].name == "b"


# ---------------------------------------------------------------------------
# await expression tests
# ---------------------------------------------------------------------------


class TestAwaitExpr:
    def test_basic_await(self) -> None:
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await get_value()
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, AwaitExpr)
        assert isinstance(let_stmt.value.expr, CallExpr)

    def test_await_identifier(self) -> None:
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await future_val
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt.value, AwaitExpr)
        assert isinstance(let_stmt.value.expr, Identifier)

    def test_return_await(self) -> None:
        source = textwrap.dedent("""\
            async fn f() -> Int {
                return await get_value()
            }
        """)
        fn = _get_first_async_fn(source)
        ret = fn.body.stmts[0]
        assert isinstance(ret, ReturnStmt)
        assert isinstance(ret.value, AwaitExpr)


# ---------------------------------------------------------------------------
# Precedence tests
# ---------------------------------------------------------------------------


class TestAwaitPrecedence:
    def test_await_binds_tighter_than_addition(self) -> None:
        """``await foo + 1`` should parse as ``(await foo) + 1``."""
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await foo + 1
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        let_stmt = fn.body.stmts[0]
        # Should be BinaryExpr(AwaitExpr(foo), +, 1)
        assert isinstance(let_stmt.value, BinaryExpr)
        assert isinstance(let_stmt.value.left, AwaitExpr)
        assert let_stmt.value.op == "+"

    def test_await_binds_looser_than_field_access(self) -> None:
        """``await foo.bar`` should parse as ``await (foo.bar)``."""
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await foo.bar
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        let_stmt = fn.body.stmts[0]
        # Should be AwaitExpr(FieldAccessExpr(foo, bar))
        assert isinstance(let_stmt.value, AwaitExpr)
        assert isinstance(let_stmt.value.expr, FieldAccessExpr)

    def test_await_binds_looser_than_call(self) -> None:
        """``await foo()`` should parse as ``await (foo())``."""
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await foo()
                return x
            }
        """)
        fn = _get_first_async_fn(source)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt.value, AwaitExpr)
        assert isinstance(let_stmt.value.expr, CallExpr)


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------


class TestAsyncAwaitNegative:
    def test_await_is_reserved_keyword(self) -> None:
        """``await`` cannot be used as a variable name."""
        source = textwrap.dedent("""\
            fn f() -> Int {
                let await = 1
                return await
            }
        """)
        with pytest.raises(Exception):
            parse(source)

    def test_async_is_reserved_keyword(self) -> None:
        """``async`` cannot be used as a variable name."""
        source = textwrap.dedent("""\
            fn f() -> Int {
                let async = 1
                return async
            }
        """)
        with pytest.raises(Exception):
            parse(source)
