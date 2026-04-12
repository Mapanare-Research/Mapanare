"""Parser tests for or-patterns (v4.35.0)."""

from __future__ import annotations

from mapanare.ast_nodes import (
    ConstructorPattern,
    IdentPattern,
    LiteralPattern,
    MatchArm,
    MatchExpr,
    OrPattern,
    WildcardPattern,
)
from mapanare.parser import parse


def _match_arms(source: str) -> list[MatchArm]:
    prog = parse(source, filename="test.mn")
    stmts = prog.definitions[0].body.stmts
    for s in stmts:
        if hasattr(s, "expr") and isinstance(s.expr, MatchExpr):
            return s.expr.arms
    raise AssertionError("No match expression found")


class TestOrPatterns:
    def test_simple_or_pattern(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 | 2 => print("small"),
        _ => print("other")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, OrPattern)
        assert len(pat.alternatives) == 2
        assert isinstance(pat.alternatives[0], LiteralPattern)
        assert isinstance(pat.alternatives[1], LiteralPattern)

    def test_triple_or_pattern(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 | 2 | 3 => print("small"),
        _ => print("other")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, OrPattern)
        assert len(pat.alternatives) == 3

    def test_or_with_constructors(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        Red | Green => print("warm"),
        Blue => print("cool")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, OrPattern)
        assert len(pat.alternatives) == 2

    def test_or_with_wildcard(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 | _ => print("any")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, OrPattern)
        assert isinstance(pat.alternatives[0], LiteralPattern)
        assert isinstance(pat.alternatives[1], WildcardPattern)

    def test_single_pattern_not_wrapped(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 => print("one"),
        _ => print("other")
    }
}
""")
        assert not isinstance(arms[0].pattern, OrPattern)
        assert isinstance(arms[0].pattern, LiteralPattern)

    def test_or_with_guard(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        1 | 2 | 3 if true => print("small"),
        _ => print("other")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, OrPattern)
        assert len(pat.alternatives) == 3
        assert arms[0].guard is not None

    def test_nested_or_in_constructor(self) -> None:
        arms = _match_arms("""
fn main() {
    match x {
        Some(1 | 2) => print("small"),
        _ => print("other")
    }
}
""")
        pat = arms[0].pattern
        assert isinstance(pat, ConstructorPattern)
        assert len(pat.args) == 1
        assert isinstance(pat.args[0], OrPattern)
        assert len(pat.args[0].alternatives) == 2
