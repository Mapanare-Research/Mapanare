"""Parser tests for match guards (v4.35.0)."""

from __future__ import annotations

from mapanare.ast_nodes import BinaryExpr, IdentPattern, MatchArm, MatchExpr
from mapanare.parser import parse


def _match_arms(source: str) -> list[MatchArm]:
    prog = parse(source, filename="test.mn")
    stmts = prog.definitions[0].body.stmts
    for s in stmts:
        if hasattr(s, "expr") and isinstance(s.expr, MatchExpr):
            return s.expr.arms
    raise AssertionError("No match expression found")


class TestMatchGuards:
    def test_simple_guard_parses(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        y if y > 0 => print("pos"),
        _ => print("neg")
    }
}
""")
        assert arms[0].guard is not None
        assert isinstance(arms[0].pattern, IdentPattern)
        assert arms[1].guard is None

    def test_guard_with_complex_expression(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        y if y > 0 && y < 100 => print("range"),
        _ => print("other")
    }
}
""")
        assert arms[0].guard is not None
        assert isinstance(arms[0].guard, BinaryExpr)

    def test_guard_with_function_call(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        y if is_valid(y) => print("valid"),
        _ => print("invalid")
    }
}
""")
        assert arms[0].guard is not None

    def test_no_guard_gives_none(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 => print("one"),
        _ => print("other")
    }
}
""")
        assert arms[0].guard is None
        assert arms[1].guard is None

    def test_guard_before_arrow(self) -> None:
        """Guard must appear between pattern and => (not after)."""
        arms = _match_arms("""
fn main() {
    match x {
        Some(v) if v > 0 => print("pos"),
        None => print("none")
    }
}
""")
        assert arms[0].guard is not None
        assert arms[1].guard is None
