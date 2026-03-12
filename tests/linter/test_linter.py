"""Tests for the Mapanare linter — one test per rule + auto-fix tests."""

from __future__ import annotations

from mapanare.diagnostics import Diagnostic, Severity
from mapanare.linter import LintRule, lint, lint_and_fix
from mapanare.parser import parse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lint(source: str, filename: str = "test.mn") -> list[Diagnostic]:
    """Parse + lint, return diagnostics."""
    program = parse(source, filename=filename)
    return lint(program, filename=filename)


def _lint_codes(source: str) -> list[str]:
    """Return just the rule codes from lint diagnostics."""
    diags = _lint(source)
    codes: list[str] = []
    for d in diags:
        for rule in LintRule:
            if f"[{rule.name}]" in d.message:
                codes.append(rule.name)
                break
    return codes


def _has_warning(diags: list[Diagnostic], rule: LintRule) -> bool:
    """Check if a specific rule fired."""
    return any(f"[{rule.name}]" in d.message for d in diags)


def _no_warnings(source: str) -> None:
    """Assert the source produces no lint warnings."""
    diags = _lint(source)
    assert diags == [], f"Expected no warnings, got: {[d.message for d in diags]}"


# ======================================================================
# W001: Unused variable
# ======================================================================


class TestW001UnusedVariable:
    def test_unused_let_warns(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 42
            }
        """)
        assert _has_warning(diags, LintRule.W001)

    def test_used_variable_no_warning(self) -> None:
        _no_warnings("""
            fn main() {
                let x: Int = 42
                println(str(x))
            }
        """)

    def test_underscore_prefix_suppresses(self) -> None:
        _no_warnings("""
            fn main() {
                let _x: Int = 42
            }
        """)

    def test_unused_in_nested_scope(self) -> None:
        diags = _lint("""
            fn main() {
                if true {
                    let y: Int = 10
                }
            }
        """)
        assert _has_warning(diags, LintRule.W001)

    def test_for_loop_var_used(self) -> None:
        _no_warnings("""
            fn main() {
                let items: List<Int> = [1, 2, 3]
                for x in items {
                    println(str(x))
                }
            }
        """)

    def test_multiple_unused(self) -> None:
        diags = _lint("""
            fn main() {
                let a: Int = 1
                let b: Int = 2
                let c: Int = 3
            }
        """)
        w001_count = sum(1 for d in diags if "[W001]" in d.message)
        assert w001_count == 3


# ======================================================================
# W002: Unused import
# ======================================================================


class TestW002UnusedImport:
    def test_unused_import_warns(self) -> None:
        diags = _lint("""
            import math { sqrt }
            fn main() {
                let x: Int = 42
                println(str(x))
            }
        """)
        assert _has_warning(diags, LintRule.W002)

    def test_used_import_no_warning(self) -> None:
        diags = _lint("""
            import math { sqrt }
            fn main() {
                let x: Float = sqrt(4.0)
            }
        """)
        assert not _has_warning(diags, LintRule.W002)

    def test_whole_module_import_unused(self) -> None:
        diags = _lint("""
            import math
            fn main() {
                let x: Int = 42
                println(str(x))
            }
        """)
        assert _has_warning(diags, LintRule.W002)

    def test_whole_module_import_used_via_namespace(self) -> None:
        diags = _lint("""
            import math
            fn main() {
                let x: Float = math::sqrt(4.0)
            }
        """)
        assert not _has_warning(diags, LintRule.W002)


# ======================================================================
# W003: Variable shadowing
# ======================================================================


class TestW003VariableShadowing:
    def test_shadow_in_inner_scope(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 1
                if true {
                    let x: Int = 2
                    println(str(x))
                }
                println(str(x))
            }
        """)
        assert _has_warning(diags, LintRule.W003)

    def test_no_shadow_different_names(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 1
                if true {
                    let y: Int = 2
                    println(str(y))
                }
                println(str(x))
            }
        """)
        assert not _has_warning(diags, LintRule.W003)

    def test_shadow_in_for_body(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 1
                let items: List<Int> = [1, 2]
                for i in items {
                    let x: Int = i
                    println(str(x))
                }
                println(str(x))
            }
        """)
        assert _has_warning(diags, LintRule.W003)


# ======================================================================
# W004: Unreachable code after return
# ======================================================================


class TestW004UnreachableCode:
    def test_code_after_return(self) -> None:
        diags = _lint("""
            fn foo() -> Int {
                return 42
                let x: Int = 1
            }
        """)
        assert _has_warning(diags, LintRule.W004)

    def test_return_at_end_no_warning(self) -> None:
        _no_warnings("""
            fn foo() -> Int {
                let x: Int = 42
                return x
            }
        """)

    def test_nested_block_return(self) -> None:
        """Return in nested if block should not flag sibling code."""
        _no_warnings("""
            fn foo(flag: Bool) -> Int {
                if flag {
                    return 1
                }
                return 0
            }
        """)


# ======================================================================
# W005: Mutable variable never mutated
# ======================================================================


class TestW005UnnecessaryMut:
    def test_mut_never_mutated_warns(self) -> None:
        diags = _lint("""
            fn main() {
                let mut x: Int = 1
                println(str(x))
            }
        """)
        assert _has_warning(diags, LintRule.W005)

    def test_mut_actually_mutated_no_warning(self) -> None:
        _no_warnings("""
            fn main() {
                let mut x: Int = 1
                x = 2
                println(str(x))
            }
        """)

    def test_mut_mutated_via_compound_assign(self) -> None:
        _no_warnings("""
            fn main() {
                let mut x: Int = 1
                x += 1
                println(str(x))
            }
        """)


# ======================================================================
# W006: Empty match arm body
# ======================================================================


class TestW006EmptyMatchArm:
    def test_empty_arm_warns(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 1
                match x {
                    1 => {
                    },
                    _ => {
                        println("other")
                    }
                }
            }
        """)
        assert _has_warning(diags, LintRule.W006)

    def test_non_empty_arm_no_warning(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 1
                match x {
                    1 => {
                        println("one")
                    },
                    _ => {
                        println("other")
                    }
                }
            }
        """)
        assert not _has_warning(diags, LintRule.W006)


# ======================================================================
# W007: Agent handle without send
# ======================================================================


class TestW007AgentHandleNoSend:
    def test_handle_without_send_warns(self) -> None:
        diags = _lint("""
            agent Logger {
                input msg: String
                output result: String

                fn handle(msg: String) {
                    println(msg)
                }
            }
        """)
        assert _has_warning(diags, LintRule.W007)

    def test_handle_with_send_no_warning(self) -> None:
        diags = _lint("""
            agent Logger {
                input msg: String
                output result: String

                fn handle(msg: String) {
                    self.result <- msg
                }
            }
        """)
        assert not _has_warning(diags, LintRule.W007)

    def test_agent_no_output_no_warning(self) -> None:
        diags = _lint("""
            agent Logger {
                input msg: String

                fn handle(msg: String) {
                    println(msg)
                }
            }
        """)
        assert not _has_warning(diags, LintRule.W007)


# ======================================================================
# W008: Result not checked
# ======================================================================


class TestW008UncheckedResult:
    def test_bare_try_call_warns(self) -> None:
        diags = _lint("""
            fn try_connect() -> Int {
                return 1
            }
            fn main() {
                try_connect()
            }
        """)
        assert _has_warning(diags, LintRule.W008)

    def test_try_call_with_let_no_warning(self) -> None:
        _no_warnings("""
            fn try_connect() -> Int {
                return 1
            }
            fn main() {
                let r: Int = try_connect()
                println(str(r))
            }
        """)

    def test_regular_fn_no_warning(self) -> None:
        _no_warnings("""
            fn do_thing() -> Int {
                return 1
            }
            fn main() {
                do_thing()
            }
        """)


# ======================================================================
# Auto-fix tests
# ======================================================================


class TestAutoFix:
    def test_fix_removes_unused_import(self) -> None:
        source = """import math { sqrt }
fn main() {
    let x: Int = 42
    println(str(x))
}
"""
        program = parse(source, filename="test.mn")
        diags, fixed = lint_and_fix(source, program, filename="test.mn")
        assert _has_warning(diags, LintRule.W002)
        assert "import math" not in fixed

    def test_fix_removes_mut(self) -> None:
        source = """fn main() {
    let mut x: Int = 1
    println(str(x))
}
"""
        program = parse(source, filename="test.mn")
        diags, fixed = lint_and_fix(source, program, filename="test.mn")
        assert _has_warning(diags, LintRule.W005)
        assert "let mut " not in fixed
        assert "let x: Int" in fixed


# ======================================================================
# Suppression tests
# ======================================================================


class TestSuppression:
    def test_underscore_prefix_suppresses_w001(self) -> None:
        _no_warnings("""
            fn main() {
                let _unused: Int = 42
            }
        """)

    def test_all_warnings_are_severity_warning(self) -> None:
        diags = _lint("""
            fn main() {
                let x: Int = 42
            }
        """)
        for d in diags:
            assert d.severity == Severity.WARNING


# ======================================================================
# Edge cases
# ======================================================================


class TestEdgeCases:
    def test_empty_program_no_warnings(self) -> None:
        _no_warnings("")

    def test_single_fn_no_body_issues(self) -> None:
        _no_warnings("""
            fn main() {
                println("hello")
            }
        """)

    def test_lambda_scope_isolation(self) -> None:
        """Lambda params should not trigger unused warnings for outer scope."""
        _no_warnings("""
            fn main() {
                let f: fn(Int) -> Int = (x) => x + 1
                println(str(f(1)))
            }
        """)

    def test_match_arm_variable_binding(self) -> None:
        """Variables bound in match patterns should track usage."""
        diags = _lint("""
            fn main() {
                let x: Int = 1
                match x {
                    y => { println(str(y)) }
                }
            }
        """)
        assert not _has_warning(diags, LintRule.W001) or all(
            "'x'" not in d.message and "'y'" not in d.message
            for d in diags
            if "[W001]" in d.message
        )
