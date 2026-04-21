"""Tests for exhaustiveness checking in match expressions (v4.34.0).

Uses the Maranget decision-tree algorithm to detect non-exhaustive
matches and unreachable arms. See DESIGN.md for the algorithm.
"""

from __future__ import annotations

from mapanare.parser import parse
from mapanare.semantic import SemanticError, check


def _check(source: str) -> list[SemanticError]:
    """Parse + semantic check, return errors."""
    program = parse(source, filename="test.mn")
    return check(program, filename="test.mn")


def _check_ok(source: str) -> None:
    """Assert no semantic errors."""
    errors = _check(source)
    assert errors == [], f"Expected no errors, got: {errors}"


def _check_err(source: str, expected_fragment: str) -> list[SemanticError]:
    """Assert at least one error contains the expected fragment."""
    errors = _check(source)
    assert errors, f"Expected errors but got none for:\n{source}"
    msgs = [e.message for e in errors]
    assert any(
        expected_fragment in m for m in msgs
    ), f"Expected error containing '{expected_fragment}', got: {msgs}"
    return errors


# ======================================================================
# Positive cases: exhaustive matches (should pass)
# ======================================================================


class TestExhaustiveMatches:
    """Matches that cover all variants should pass without errors."""

    def test_option_some_none_exhaustive(self) -> None:
        _check_ok("""
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) => { return v },
        None => { return 0 }
    }
}
fn main() { print(str(foo(Some(1)))) }
""")

    def test_result_ok_err_exhaustive(self) -> None:
        _check_ok("""
fn foo(x: Result<Int, String>) -> Int {
    match x {
        Ok(v) => { return v },
        Err(e) => { return 0 }
    }
}
fn main() { print(str(foo(Ok(1)))) }
""")

    def test_enum_all_variants_exhaustive(self) -> None:
        _check_ok("""
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red => { return "red" },
        Green => { return "green" },
        Blue => { return "blue" }
    }
}
fn main() { print(name(Color::Red)) }
""")

    def test_enum_wildcard_catchall_exhaustive(self) -> None:
        _check_ok("""
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red => { return "red" },
        _ => { return "other" }
    }
}
fn main() { print(name(Color::Red)) }
""")

    def test_enum_ident_catchall_exhaustive(self) -> None:
        _check_ok("""
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red => { return "red" },
        other => { return "other" }
    }
}
fn main() { print(name(Color::Red)) }
""")

    def test_int_with_default_exhaustive(self) -> None:
        _check_ok("""
fn classify(x: Int) -> String {
    match x {
        0 => { return "zero" },
        1 => { return "one" },
        _ => { return "other" }
    }
}
fn main() { print(classify(0)) }
""")


# ======================================================================
# Negative cases: non-exhaustive matches (should produce errors)
# ======================================================================


class TestNonExhaustiveMatches:
    """Matches missing variants should produce errors with witness patterns."""

    def test_option_only_some_is_error(self) -> None:
        _check_err(
            """
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) => { return v }
    }
}
fn main() { print(str(foo(Some(1)))) }
""",
            "None",
        )

    def test_result_only_ok_is_error(self) -> None:
        _check_err(
            """
fn foo(x: Result<Int, String>) -> Int {
    match x {
        Ok(v) => { return v }
    }
}
fn main() { print(str(foo(Ok(1)))) }
""",
            "Err",
        )

    def test_enum_missing_variant_is_error(self) -> None:
        _check_err(
            """
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red => { return "red" },
        Green => { return "green" }
    }
}
fn main() { print(name(Color::Red)) }
""",
            "Blue",
        )


# ======================================================================
# Witness and diagnostic quality
# ======================================================================


class TestDiagnosticQuality:
    """Verify error messages contain witness patterns and are actionable."""

    def test_exhaustive_message_names_witness(self) -> None:
        """The error message should name the specific missing pattern."""
        errors = _check("""
enum Dir { Up, Down, Left, Right }
fn go(d: Dir) -> Int {
    match d {
        Up => { return 1 },
        Down => { return 2 }
    }
}
fn main() { print(str(go(Dir::Up))) }
""")
        assert errors
        msg = errors[0].message
        # Should mention at least one of the missing variants
        assert "Left" in msg or "Right" in msg, f"Expected witness in: {msg}"

    def test_non_exhaustive_message_format(self) -> None:
        """Check that the error message uses the 'not covered' format."""
        errors = _check("""
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) => { return v }
    }
}
fn main() { print(str(foo(Some(1)))) }
""")
        assert errors
        msg = errors[0].message
        assert "not covered" in msg, f"Expected 'not covered' in: {msg}"
