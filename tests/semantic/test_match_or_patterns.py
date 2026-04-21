"""Semantic tests for or-patterns (v4.35.0)."""

from __future__ import annotations

from mapanare.parser import parse
from mapanare.semantic import SemanticError, check


def _check(source: str) -> list[SemanticError]:
    program = parse(source, filename="test.mn")
    return [e for e in check(program, filename="test.mn") if e.severity != "warning"]


def _check_ok(source: str) -> None:
    errors = _check(source)
    assert errors == [], f"Expected no errors, got: {errors}"


def _check_err(source: str, expected_fragment: str) -> list[SemanticError]:
    errors = _check(source)
    assert errors, f"Expected errors but got none for:\n{source}"
    msgs = [e.message for e in errors]
    assert any(
        expected_fragment in m for m in msgs
    ), f"Expected error containing '{expected_fragment}', got: {msgs}"
    return errors


class TestOrPatternBindings:
    def test_or_no_bindings_accepted(self) -> None:
        """Or-pattern with no bindings in any alternative is trivially valid."""
        _check_ok("""
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red | Green => { return "warm" },
        Blue => { return "cool" }
    }
}
fn main() { print(name(Color::Red)) }
""")

    def test_or_different_bindings_rejected(self) -> None:
        """Or-pattern where one alternative binds a name and the other doesn't."""
        _check_err(
            """
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) | None => { return 0 }
    }
}
fn main() { print(str(foo(Some(1)))) }
""",
            "or-pattern alternatives must bind the same names",
        )


class TestOrPatternExhaustiveness:
    def test_or_exhaustive_coverage(self) -> None:
        """Or-pattern covering all variants is exhaustive."""
        _check_ok("""
enum Color { Red, Green, Blue }
fn name(c: Color) -> String {
    match c {
        Red | Green => { return "warm" },
        Blue => { return "cool" }
    }
}
fn main() { print(name(Color::Red)) }
""")

    def test_or_with_literal_and_default(self) -> None:
        _check_ok("""
fn classify(x: Int) -> String {
    match x {
        1 | 2 | 3 => { return "small" },
        _ => { return "other" }
    }
}
fn main() { print(classify(1)) }
""")
