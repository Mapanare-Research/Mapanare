"""v4.68.0 Phase 8 — Interim error tests for async fn lowering.

The lowerer must produce a rustc-quality "under construction" error when it
encounters an ``AsyncFnDef``, pointing the user at v4.70.0. This is the
honest interim state — grammar real, lowering not yet. See DESIGN.md §4.
"""

from __future__ import annotations

import textwrap

from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


class TestAsyncFnInterimError:
    def test_async_fn_lowering_succeeds(self) -> None:
        """v4.70.0: async fn lowering works (coroutine prelude emitted)."""
        source = textwrap.dedent("""\
            async fn fetch() -> Int {
                return 42
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        module = lower(tree)
        fn = module.get_function("fetch")
        assert fn is not None
        assert fn.is_async is True

    def test_async_fn_is_async_flag(self) -> None:
        """v4.70.0: MIRFunction has is_async=True for async fn."""
        source = textwrap.dedent("""\
            async fn work(x: Int) -> Int {
                return x + 1
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        module = lower(tree)
        fn = module.get_function("work")
        assert fn is not None
        assert fn.is_async is True

    def test_regular_fn_still_lowers(self) -> None:
        """Non-async functions are unaffected by the async interim."""
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        checker.check(tree)
        module = lower(tree)
        assert module.get_function("add") is not None

    def test_semantic_checker_accepts_async_fn(self) -> None:
        """The semantic checker must not reject async fn at v4.68.0 (stub)."""
        source = textwrap.dedent("""\
            async fn fetch(url: String) -> String {
                return url
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        # Should not raise — semantic accepts async fn as a stub
        checker.check(tree)

    def test_semantic_checker_accepts_await_expr(self) -> None:
        """The semantic checker must not reject await at v4.68.0 (stub)."""
        source = textwrap.dedent("""\
            async fn f() -> Int {
                let x = await get_value()
                return x
            }
            fn get_value() -> Int {
                return 42
            }
        """)
        tree = parse(source)
        checker = SemanticChecker()
        # Should not raise — await checking is a stub until v4.69.0
        checker.check(tree)
