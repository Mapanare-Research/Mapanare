"""Semantic tests for match guards (v4.35.0)."""

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


class TestGuardTypeChecks:
    def test_guard_bool_accepted(self) -> None:
        _check_ok("""
fn main() {
    let x: Int = 5
    match x {
        y if y > 0 => print("pos"),
        _ => print("other")
    }
}
""")

    def test_guard_non_bool_rejected(self) -> None:
        _check_err(
            """
fn main() {
    let x: Int = 5
    match x {
        y if y => print("truthy"),
        _ => print("other")
    }
}
""",
            "Bool",
        )

    def test_guard_sees_pattern_bindings(self) -> None:
        _check_ok("""
fn foo(x: Option<Int>) -> String {
    match x {
        Some(v) if v > 0 => { return "pos" },
        Some(v) => { return "nonpos" },
        None => { return "none" }
    }
}
fn main() { print(foo(Some(1))) }
""")


class TestGuardExhaustiveness:
    def test_guarded_arms_count_for_coverage(self) -> None:
        """Guarded arms count toward coverage (Rust semantics)."""
        _check_ok("""
fn foo(x: Option<Int>) -> String {
    match x {
        Some(v) if v > 0 => { return "pos" },
        Some(_) => { return "other" },
        None => { return "none" }
    }
}
fn main() { print(foo(Some(1))) }
""")

    def test_only_guarded_arms_still_exhaustive(self) -> None:
        """Even if all arms have guards, the pattern coverage is what matters."""
        _check_ok("""
fn foo(x: Option<Int>) -> Int {
    match x {
        Some(v) if v > 0 => { return v },
        None if true => { return 0 },
        _ => { return -1 }
    }
}
fn main() { print(str(foo(Some(1)))) }
""")
