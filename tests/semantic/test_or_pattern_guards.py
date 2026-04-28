"""v5.7.0: or-pattern binding-set check correctly handles built-in
Option/Result variants. Previously `Some(0) | None` was rejected as
"extra ['None']" because `_is_enum_variant_name` only checked
user-defined enums and treated `None` (an IdentPattern) as a fresh
binding name.
"""

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


class TestOrPatternBuiltinVariants:
    def test_some_literal_or_none_accepted(self) -> None:
        """Some(literal) | None — both bind nothing, must accept."""
        _check_ok("""
fn describe(opt: Option<Int>) -> String {
    match opt {
        Some(0) | None => "zero or absent",
        _ => "other"
    }
}
fn main() { print(describe(Some(0))) }
""")

    def test_none_or_some_literal_accepted(self) -> None:
        """Symmetry: None | Some(literal) also accepted."""
        _check_ok("""
fn describe(opt: Option<Int>) -> String {
    match opt {
        None | Some(0) => "zero or absent",
        _ => "other"
    }
}
fn main() { print(describe(None)) }
""")

    def test_ok_literal_or_err_literal_accepted(self) -> None:
        """Result variants with literal payloads — both bind nothing."""
        _check_ok("""
fn describe(r: Result<Int, Int>) -> String {
    match r {
        Ok(0) | Err(0) => "zero",
        _ => "other"
    }
}
fn main() { print(describe(Ok(0))) }
""")

    def test_some_binding_or_none_still_rejected(self) -> None:
        """Some(v) | None still rejected — binds {v} vs {}."""
        _check_err(
            """
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) | None => 0
    }
}
fn main() { print(str(foo(Some(1)))) }
""",
            "or-pattern alternatives must bind the same names",
        )

    def test_none_as_expression_resolves_to_option(self) -> None:
        """`None` as an identifier expression compiles (lower.py + semantic.py).
        Required because KW_NONE only matches lowercase `none`/`nada`;
        capital `None` tokenizes as NAME.
        """
        _check_ok("""
fn pick() -> Option<Int> { None }
fn main() {
    let opt: Option<Int> = None
    let other: Option<Int> = pick()
    match opt {
        Some(_) => print("some"),
        None => print("none")
    }
}
""")
