"""v5.7.0 Sh.7: closure type annotations resolved through Python
bootstrap. Mirrors the v4.103.0 fix at mapanare/lower.py docket #5
(closure-typed parameter calls lower to ClosureCall instead of
direct-call-by-name) plus the Python preconditions that already
existed: `_resolve_type_expr(FnType)` returns FN type and lambdas
emit ClosureCreate.
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


class TestClosureTypedParams:
    def test_simple_closure_param(self) -> None:
        """Closure passed as a typed function parameter."""
        _check_ok("""
fn apply(f: fn(Int) -> Int, x: Int) -> Int {
    return f(x)
}
fn main() {
    let double: fn(Int) -> Int = (x) => x * 2
    print(str(apply(double, 5)))
}
""")

    def test_multi_param_closure(self) -> None:
        """Multi-parameter closure: both params resolve in lambda body."""
        _check_ok("""
fn combine(f: fn(Int, Int) -> Int, a: Int, b: Int) -> Int {
    return f(a, b)
}
fn main() {
    let sum: fn(Int, Int) -> Int = (a, b) => a + b
    print(str(combine(sum, 7, 8)))
}
""")

    def test_closure_invoked_directly(self) -> None:
        """Closure stored in a typed binding can be called directly."""
        _check_ok("""
fn main() {
    let double: fn(Int) -> Int = (x) => x * 2
    print(str(double(10)))
}
""")
