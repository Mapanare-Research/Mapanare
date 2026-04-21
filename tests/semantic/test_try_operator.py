"""v4.33.0 Phase 3.3 — Semantic tests for the ``?`` operator.

Tests the strengthened type-checking that v4.33.0 phase 1.5 added:
``?`` requires ``Result<T, E>`` or ``Option<T>`` as the inner type,
and the enclosing function's return type must be compatible.
"""

from __future__ import annotations

import textwrap

from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _check(source: str) -> list[object]:
    """Parse and semantic-check source; return the list of errors."""
    tree = parse(source)
    checker = SemanticChecker(filename="<test>")
    checker.check(tree)
    return checker.errors


class TestTryOnResultValid:
    def test_try_on_result_in_result_fn_ok(self) -> None:
        source = textwrap.dedent("""\
            fn might_fail() -> Result<Int, String> { return Ok(1) }
            fn f() -> Result<Int, String> {
                let v = might_fail()?
                return Ok(v)
            }
        """)
        errors = _check(source)
        # Should have zero errors related to ?
        try_errors = [e for e in errors if "?" in str(e) or "Result" in str(e)]
        assert len(try_errors) == 0, f"Unexpected errors: {try_errors}"


class TestTryOnOptionValid:
    def test_try_on_option_in_option_fn_ok(self) -> None:
        source = textwrap.dedent("""\
            fn find(x: Int) -> Option<Int> {
                if x > 0 { return Some(x) }
                return None
            }
            fn f(x: Int) -> Option<Int> {
                let v = find(x)?
                return Some(v + 1)
            }
        """)
        errors = _check(source)
        option_errors = [e for e in errors if "?" in str(e) or "Option" in str(e)]
        assert len(option_errors) == 0, f"Unexpected errors: {option_errors}"


class TestTryTypeErrors:
    def test_try_on_int_errors(self) -> None:
        source = textwrap.dedent("""\
            fn f(x: Int) -> Int {
                let v = x?
                return v
            }
        """)
        errors = _check(source)
        msgs = [str(e) for e in errors]
        found = any("Result" in m or "Option" in m for m in msgs)
        assert found, f"Expected type error for ? on Int, got: {msgs}"

    def test_try_on_result_in_non_result_fn_errors(self) -> None:
        source = textwrap.dedent("""\
            fn might_fail() -> Result<Int, String> { return Ok(1) }
            fn f() -> Int {
                let v = might_fail()?
                return v
            }
        """)
        errors = _check(source)
        msgs = [str(e) for e in errors]
        found = any("Result" in m for m in msgs)
        assert found, f"Expected return-type mismatch error, got: {msgs}"

    def test_try_on_option_in_result_fn_errors(self) -> None:
        source = textwrap.dedent("""\
            fn find(x: Int) -> Option<Int> {
                if x > 0 { return Some(x) }
                return None
            }
            fn f() -> Result<Int, String> {
                let v = find(1)?
                return Ok(v)
            }
        """)
        errors = _check(source)
        msgs = [str(e) for e in errors]
        found = any("Option" in m for m in msgs)
        assert found, f"Expected Option-in-Result error, got: {msgs}"
