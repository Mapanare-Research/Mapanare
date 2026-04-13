"""v4.74.0 — Parser and semantic tests for `for await` syntax."""

from __future__ import annotations

import textwrap

import pytest

from mapanare.ast_nodes import ForAwaitLoop, AsyncFnDef
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


class TestForAwaitParsing:
    def test_basic_for_await(self) -> None:
        """for await parses to ForAwaitLoop."""
        source = textwrap.dedent("""\
            async fn consume(items: List<Int>) -> Int {
                let mut sum = 0
                for await x in items {
                    sum = sum + x
                }
                return sum
            }
        """)
        tree = parse(source)
        fn = [d for d in tree.definitions if isinstance(d, AsyncFnDef)][0]
        # Find the ForAwaitLoop in the body
        for_await = None
        for stmt in fn.body.stmts:
            if isinstance(stmt, ForAwaitLoop):
                for_await = stmt
        assert for_await is not None
        assert for_await.var_name == "x"

    def test_for_await_var_name(self) -> None:
        """for await captures the variable name correctly."""
        source = textwrap.dedent("""\
            async fn f(s: List<Int>) -> Int {
                for await chunk in s {
                    let y = chunk
                }
                return 0
            }
        """)
        tree = parse(source)
        fn = [d for d in tree.definitions if isinstance(d, AsyncFnDef)][0]
        for_await = [s for s in fn.body.stmts if isinstance(s, ForAwaitLoop)][0]
        assert for_await.var_name == "chunk"


class TestForAwaitSemantic:
    def test_for_await_outside_async_is_error(self) -> None:
        """for await in a non-async fn produces an error."""
        source = textwrap.dedent("""\
            fn f(items: List<Int>) -> Int {
                for await x in items {
                    let y = x
                }
                return 0
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        errors = [e.message for e in checker.errors]
        assert any("async" in e for e in errors), f"Expected async error, got: {errors}"

    def test_for_await_inside_async_is_ok(self) -> None:
        """for await in an async fn produces no async-context error."""
        source = textwrap.dedent("""\
            async fn f(items: List<Int>) -> Int {
                for await x in items {
                    let y = x
                }
                return 0
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        errors = [e.message for e in checker.errors]
        async_errors = [e for e in errors if "async" in e.lower()]
        assert len(async_errors) == 0, f"Unexpected async error: {async_errors}"


class TestForAwaitLowering:
    def test_for_await_lowers_without_error(self) -> None:
        """for await should lower without crashing."""
        from mapanare.lower import lower

        source = textwrap.dedent("""\
            async fn consume(items: List<Int>) -> Int {
                let mut sum = 0
                for await x in items {
                    sum = sum + x
                }
                return sum
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        module = lower(tree)
        fn = module.get_function("consume")
        assert fn is not None
        assert fn.is_async is True
