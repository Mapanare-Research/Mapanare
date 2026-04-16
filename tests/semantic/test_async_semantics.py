"""v4.69.0 — Semantic analysis tests for async fn and await.

Tests Future<T> type wrapping, await-outside-async errors, await-on-non-Future
errors, and "forgot to await" arithmetic errors.
"""

from __future__ import annotations

import textwrap

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker
from mapanare.types import TypeKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check(source: str) -> SemanticChecker:
    """Parse and semantic-check source, return the checker."""
    tree = parse(source)
    checker = SemanticChecker()
    checker.check(tree)
    return checker


def _check_errors(source: str) -> list[str]:
    """Parse and check, return error messages."""
    checker = _check(source)
    return [e.message for e in checker.errors]


def _get_fn_return_type(source: str, fn_name: str) -> object:
    """Get the registered return type for a function."""
    checker = _check(source)
    sym = checker.global_scope.lookup(fn_name)
    if sym and sym.type_info and sym.type_info.return_type:
        return sym.type_info.return_type
    return None


# ---------------------------------------------------------------------------
# Future<T> type wrapping
# ---------------------------------------------------------------------------


class TestAsyncFnReturnTypeWrapping:
    def test_async_fn_returns_future(self) -> None:
        """async fn foo() -> Int registers as fn returning Future<Int>."""
        source = textwrap.dedent("""\
            async fn foo() -> Int {
                return 42
            }
        """)
        ret = _get_fn_return_type(source, "foo")
        assert ret is not None
        assert ret.kind == TypeKind.FUTURE
        assert ret.args
        assert ret.args[0].kind == TypeKind.INT

    def test_async_fn_void_returns_future_void(self) -> None:
        """async fn with no return type registers as Future<Void> (or similar)."""
        source = textwrap.dedent("""\
            async fn do_work() {
                let x = 1
            }
        """)
        ret = _get_fn_return_type(source, "do_work")
        assert ret is not None
        assert ret.kind == TypeKind.FUTURE

    def test_sync_fn_returns_raw_type(self) -> None:
        """Regular fn foo() -> Int returns Int (not Future<Int>)."""
        source = textwrap.dedent("""\
            fn foo() -> Int {
                return 42
            }
        """)
        ret = _get_fn_return_type(source, "foo")
        assert ret is not None
        assert ret.kind == TypeKind.INT


# ---------------------------------------------------------------------------
# await outside async fn
# ---------------------------------------------------------------------------


class TestAwaitOutsideAsync:
    def test_await_in_sync_fn_is_error(self) -> None:
        """await in a regular fn produces an error."""
        source = textwrap.dedent("""\
            fn f() -> Int {
                let x = await some_future()
                return x
            }
            async fn some_future() -> Int { return 1 }
        """)
        errors = _check_errors(source)
        assert any(
            "only be used inside" in e for e in errors
        ), f"Expected await-outside-async error, got: {errors}"

    def test_await_in_async_fn_is_ok(self) -> None:
        """await in an async fn produces no error (for the await itself)."""
        source = textwrap.dedent("""\
            async fn get_value() -> Int { return 42 }
            async fn f() -> Int {
                let x = await get_value()
                return x
            }
        """)
        errors = _check_errors(source)
        # No "await outside async" error
        assert not any("only be used inside" in e for e in errors), f"Unexpected error: {errors}"


# ---------------------------------------------------------------------------
# await on non-Future type
# ---------------------------------------------------------------------------


class TestAwaitOnNonFuture:
    def test_await_on_int_is_error(self) -> None:
        """await on a plain Int value (not Future) produces an error."""
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let y = 42
                let x = await y
                return x
            }
        """)
        errors = _check_errors(source)
        assert any(
            "requires a Future" in e for e in errors
        ), f"Expected Future error, got: {errors}"

    def test_await_on_future_is_ok(self) -> None:
        """await on Future<Int> (from async fn call) produces no type error."""
        source = textwrap.dedent("""\
            async fn get_value() -> Int { return 42 }
            async fn f() -> Int {
                let x = await get_value()
                return x
            }
        """)
        errors = _check_errors(source)
        # Filter out non-await errors (there may be return type mismatches etc.)
        await_errors = [e for e in errors if "await" in e.lower() or "future" in e.lower()]
        assert len(await_errors) == 0, f"Unexpected await/future error: {await_errors}"


# ---------------------------------------------------------------------------
# "Forgot to await" errors
# ---------------------------------------------------------------------------


class TestForgotToAwait:
    def test_future_in_arithmetic_is_error(self) -> None:
        """Using a Future<Int> in arithmetic produces "forgot to await" error."""
        source = textwrap.dedent("""\
            async fn get_value() -> Int { return 42 }
            fn f() {
                let future_val = get_value()
                let x = future_val + 1
            }
        """)
        errors = _check_errors(source)
        future_errors = [e for e in errors if "future" in e.lower() or "await" in e.lower()]
        assert len(future_errors) > 0, f"Expected 'forgot to await' error, got: {errors}"

    def test_future_in_comparison_is_error(self) -> None:
        """Using a Future<Int> in comparison produces "forgot to await" error."""
        source = textwrap.dedent("""\
            async fn get_value() -> Int { return 42 }
            fn f() {
                let future_val = get_value()
                let x = future_val == 1
            }
        """)
        errors = _check_errors(source)
        future_errors = [e for e in errors if "future" in e.lower() or "await" in e.lower()]
        assert len(future_errors) > 0, f"Expected 'forgot to await' error, got: {errors}"


# ---------------------------------------------------------------------------
# Regression: existing features still work
# ---------------------------------------------------------------------------


class TestAsyncDoesNotBreakExisting:
    def test_sync_fn_still_checks(self) -> None:
        """Regular functions are unaffected by async additions."""
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """)
        errors = _check_errors(source)
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_multiple_fns_work(self) -> None:
        """Multiple sync functions are unaffected."""
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int { return a + b }
            fn sub(a: Int, b: Int) -> Int { return a - b }
            fn main() -> Int { return add(1, sub(3, 1)) }
        """)
        errors = _check_errors(source)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
