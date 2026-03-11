"""Tests for Phase 3: Error Recovery & Structured Diagnostics."""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import Span
from mapanare.diagnostics import (
    Diagnostic,
    DiagnosticBag,
    Label,
    Severity,
    Suggestion,
    format_diagnostic,
    format_diagnostics,
    format_summary,
)
from mapanare.parser import ParseError, ParseErrors, parse, parse_recovering

# ---------------------------------------------------------------------------
# Task 1: Source locations on AST nodes
# ---------------------------------------------------------------------------


class TestASTSpans:
    """All AST nodes produced by the parser should have non-zero spans."""

    def test_int_literal_span(self) -> None:
        prog = parse("let x: Int = 42")
        let_stmt = prog.definitions[0].body.stmts[0]  # type: ignore[union-attr]
        assert let_stmt.span.line >= 1
        assert let_stmt.value.span.line >= 1

    def test_fn_def_span(self) -> None:
        prog = parse("fn add(a: Int, b: Int) -> Int { return a + b }")
        fn = prog.definitions[0]
        assert fn.span.line == 1
        assert fn.span.column >= 1

    def test_binary_expr_span(self) -> None:
        prog = parse("let x: Int = 1 + 2")
        let_stmt = prog.definitions[0].body.stmts[0]  # type: ignore[union-attr]
        binop = let_stmt.value
        assert binop.span.line >= 1

    def test_if_expr_span(self) -> None:
        prog = parse("let x: Int = if true { 1 } else { 2 }")
        let_stmt = prog.definitions[0].body.stmts[0]  # type: ignore[union-attr]
        if_expr = let_stmt.value
        assert if_expr.span.line >= 1

    def test_struct_def_span(self) -> None:
        prog = parse("struct Point { x: Int, y: Int }")
        struct = prog.definitions[0]
        assert struct.span.line == 1

    def test_enum_def_span(self) -> None:
        prog = parse("enum Color { Red, Green, Blue }")
        enum = prog.definitions[0]
        assert enum.span.line == 1

    def test_bool_literal_span(self) -> None:
        prog = parse("let x: Bool = true")
        let_stmt = prog.definitions[0].body.stmts[0]  # type: ignore[union-attr]
        assert let_stmt.value.span.line >= 1

    def test_string_literal_span(self) -> None:
        prog = parse('let x: String = "hello"')
        let_stmt = prog.definitions[0].body.stmts[0]  # type: ignore[union-attr]
        assert let_stmt.value.span.line >= 1

    def test_call_expr_span(self) -> None:
        prog = parse("println(42)")
        main_fn = prog.definitions[0]
        call = main_fn.body.stmts[0].expr
        assert call.span.line >= 1

    def test_for_loop_span(self) -> None:
        prog = parse("for i in 0..10 { println(i) }")
        main_fn = prog.definitions[0]
        for_loop = main_fn.body.stmts[0]
        assert for_loop.span.line >= 1

    def test_while_loop_span(self) -> None:
        prog = parse("while true { println(1) }")
        main_fn = prog.definitions[0]
        while_loop = main_fn.body.stmts[0]
        assert while_loop.span.line >= 1

    def test_match_expr_span(self) -> None:
        src = "fn test(x: Int) -> Int { match x { 1 => 10, _ => 0 } }"
        prog = parse(src)
        fn = prog.definitions[0]
        # The match is in the last expression of the block
        match_stmt = fn.body.stmts[0]
        assert match_stmt.span.line >= 1

    def test_multiline_spans(self) -> None:
        src = """fn foo() -> Int {
    let x: Int = 1
    let y: Int = 2
    return x + y
}"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert fn.span.line == 1
        # Body statements should have increasing line numbers
        stmts = fn.body.stmts
        assert len(stmts) == 3
        assert stmts[0].span.line == 2
        assert stmts[1].span.line == 3
        assert stmts[2].span.line == 4

    def test_program_span(self) -> None:
        prog = parse("fn main() { println(1) }")
        assert prog.span.line >= 1


# ---------------------------------------------------------------------------
# Task 2: Structured error types
# ---------------------------------------------------------------------------


class TestDiagnosticTypes:
    def test_diagnostic_creation(self) -> None:
        span = Span(line=1, column=5, end_line=1, end_column=10)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="type mismatch",
            filename="test.mn",
            labels=[Label(span=span, message="expected Int", primary=True)],
        )
        assert diag.severity == Severity.ERROR
        assert diag.message == "type mismatch"
        assert diag.line == 1
        assert diag.column == 5
        assert str(diag) == "test.mn:1:5: error: type mismatch"

    def test_diagnostic_with_suggestion(self) -> None:
        span = Span(line=3, column=1, end_line=3, end_column=4)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="unknown variable 'fob'",
            filename="test.mn",
            labels=[Label(span=span, message="not found", primary=True)],
            suggestions=[Suggestion(message="did you mean 'foo'?", replacement="foo")],
        )
        assert len(diag.suggestions) == 1
        assert diag.suggestions[0].message == "did you mean 'foo'?"

    def test_diagnostic_with_notes(self) -> None:
        span = Span(line=1, column=1, end_line=1, end_column=5)
        diag = Diagnostic(
            severity=Severity.WARNING,
            message="unused variable",
            filename="test.mn",
            labels=[Label(span=span, primary=True)],
            notes=["prefix with _ to silence this warning"],
        )
        assert diag.severity == Severity.WARNING
        assert len(diag.notes) == 1

    def test_diagnostic_bag(self) -> None:
        bag = DiagnosticBag()
        span = Span(line=1, column=1, end_line=1, end_column=5)
        bag.error("bad thing", span, filename="test.mn")
        bag.warning("suspicious", span, filename="test.mn")
        assert bag.has_errors
        assert bag.error_count == 1
        assert bag.warning_count == 1
        assert len(bag.diagnostics) == 2

    def test_empty_bag(self) -> None:
        bag = DiagnosticBag()
        assert not bag.has_errors
        assert bag.error_count == 0


# ---------------------------------------------------------------------------
# Task 2 continued: Colorized output formatting
# ---------------------------------------------------------------------------


class TestFormatDiagnostic:
    def test_format_no_color(self) -> None:
        span = Span(line=1, column=5, end_line=1, end_column=10)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="type mismatch",
            filename="test.mn",
            labels=[Label(span=span, message="expected Int", primary=True)],
        )
        out = format_diagnostic(diag, "let x: Int = true", color=False)
        assert "test.mn:1:5" in out
        assert "error" in out
        assert "type mismatch" in out

    def test_format_with_source_underline(self) -> None:
        source = 'let x: Int = "hello"'
        span = Span(line=1, column=14, end_line=1, end_column=21)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="type mismatch: expected Int, got String",
            filename="test.mn",
            labels=[Label(span=span, message="this is a String", primary=True)],
        )
        out = format_diagnostic(diag, source, color=False)
        assert "^" in out
        assert "this is a String" in out

    def test_format_with_suggestion(self) -> None:
        source = "let x: Int = fob"
        span = Span(line=1, column=14, end_line=1, end_column=17)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="unknown variable 'fob'",
            filename="test.mn",
            labels=[Label(span=span, primary=True)],
            suggestions=[Suggestion(message="did you mean 'foo'?", replacement="foo")],
        )
        out = format_diagnostic(diag, source, color=False)
        assert "help" in out
        assert "did you mean 'foo'?" in out
        assert "foo" in out

    def test_format_with_notes(self) -> None:
        span = Span(line=1, column=1, end_line=1, end_column=5)
        diag = Diagnostic(
            severity=Severity.WARNING,
            message="unused variable",
            filename="test.mn",
            labels=[Label(span=span, primary=True)],
            notes=["prefix with _ to silence"],
        )
        out = format_diagnostic(diag, "let _x: Int = 5", color=False)
        assert "note" in out
        assert "prefix with _ to silence" in out

    def test_format_color_output(self) -> None:
        span = Span(line=1, column=1, end_line=1, end_column=5)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="test error",
            filename="test.mn",
            labels=[Label(span=span, primary=True)],
        )
        out = format_diagnostic(diag, "test code", color=True)
        # Should contain ANSI escape codes
        assert "\033[" in out

    def test_format_multiple_diagnostics(self) -> None:
        span1 = Span(line=1, column=1, end_line=1, end_column=5)
        span2 = Span(line=2, column=1, end_line=2, end_column=5)
        diags = [
            Diagnostic(
                severity=Severity.ERROR,
                message="first error",
                filename="test.mn",
                labels=[Label(span=span1, primary=True)],
            ),
            Diagnostic(
                severity=Severity.ERROR,
                message="second error",
                filename="test.mn",
                labels=[Label(span=span2, primary=True)],
            ),
        ]
        out = format_diagnostics(diags, "line one\nline two", color=False)
        assert "first error" in out
        assert "second error" in out

    def test_format_summary(self) -> None:
        span = Span(line=1, column=1, end_line=1, end_column=5)
        lbl = Label(span=span, primary=True)
        diags = [
            Diagnostic(severity=Severity.ERROR, message="e1", labels=[lbl]),
            Diagnostic(severity=Severity.ERROR, message="e2", labels=[lbl]),
            Diagnostic(severity=Severity.WARNING, message="w1", labels=[lbl]),
        ]
        out = format_summary(diags, color=False)
        assert "2 errors" in out
        assert "1 warning" in out

    def test_format_summary_empty(self) -> None:
        out = format_summary([], color=False)
        assert out == ""


# ---------------------------------------------------------------------------
# Task 3: Error recovery in parser
# ---------------------------------------------------------------------------


class TestParserErrorRecovery:
    def test_single_error_recovery(self) -> None:
        """A file with one bad definition should still report the error."""
        src = "fn foo( { }"
        program, errors = parse_recovering(src, filename="test.mn")
        assert len(errors) >= 1
        assert errors[0].filename == "test.mn"

    def test_multiple_errors_recovery(self) -> None:
        """Multiple bad definitions should produce multiple errors."""
        src = """fn good() -> Int { return 1 }

fn bad1( { }

fn also_good() -> Int { return 2 }

fn bad2( -> {
"""
        program, errors = parse_recovering(src, filename="test.mn")
        # Should recover some good definitions
        good_fns = [d for d in program.definitions if hasattr(d, "name") and "good" in d.name]
        assert len(good_fns) >= 1, "Should recover at least one good definition"
        # Should have at least 2 errors (bad1 and bad2)
        assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}"

    def test_recovery_preserves_good_definitions(self) -> None:
        """Good definitions around bad ones should be preserved."""
        src = """struct Point {
    x: Int,
    y: Int
}

fn bad( { }

fn add(a: Int, b: Int) -> Int {
    return a + b
}
"""
        program, errors = parse_recovering(src, filename="test.mn")
        names = [d.name for d in program.definitions if hasattr(d, "name")]
        assert "Point" in names, "Struct should be recovered"
        assert "add" in names, "Good fn should be recovered"
        assert len(errors) >= 1

    def test_no_errors_fast_path(self) -> None:
        """When there are no errors, parse_recovering should work like parse."""
        src = "fn main() { println(42) }"
        program, errors = parse_recovering(src, filename="test.mn")
        assert errors == []
        assert len(program.definitions) == 1

    def test_error_has_line_info(self) -> None:
        """Recovered errors should have correct line numbers."""
        src = """fn good() -> Int { return 1 }

fn bad( { }
"""
        _, errors = parse_recovering(src, filename="test.mn")
        assert len(errors) >= 1
        # The bad fn starts on line 3
        assert errors[0].line >= 3


# ---------------------------------------------------------------------------
# Task 4: Multiple errors per compilation
# ---------------------------------------------------------------------------


class TestMultipleErrors:
    def test_semantic_multiple_errors(self) -> None:
        """Semantic checker already collects multiple errors."""
        from mapanare.semantic import check

        src = """fn main() {
    let x: Int = "hello"
    let y: String = 42
}
"""
        prog = parse(src)
        errors = check(prog, filename="test.mn")
        assert len(errors) >= 2, "Should detect multiple type errors"

    def test_parse_errors_exception(self) -> None:
        """ParseErrors can carry multiple errors."""
        errs = [
            ParseError("err1", line=1, column=1, filename="a.mn"),
            ParseError("err2", line=5, column=3, filename="a.mn"),
        ]
        exc = ParseErrors(errs)
        assert len(exc.errors) == 2
        assert "2" in str(exc)

    def test_combined_parse_and_semantic_errors(self) -> None:
        """parse_recovering + semantic check collects both kinds of errors."""
        from mapanare.semantic import check

        src = """fn good() -> Int {
    let x: Int = "wrong"
    return x
}

fn bad( { }
"""
        program, parse_errs = parse_recovering(src, filename="test.mn")
        sem_errs = check(program, filename="test.mn")
        total = len(parse_errs) + len(sem_errs)
        assert total >= 2, f"Expected at least 2 total errors, got {total}"


# ---------------------------------------------------------------------------
# Task 5: Colorized output (verified via formatting)
# ---------------------------------------------------------------------------


class TestColorizedOutput:
    def test_severity_colors(self) -> None:
        """Each severity should produce different colored output."""
        span = Span(line=1, column=1, end_line=1, end_column=5)
        for severity in Severity:
            diag = Diagnostic(
                severity=severity,
                message=f"test {severity.value}",
                filename="test.mn",
                labels=[Label(span=span, primary=True)],
            )
            out = format_diagnostic(diag, "test code", color=True)
            assert severity.value in out

    def test_no_color_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """NO_COLOR env var should suppress ANSI codes."""
        monkeypatch.setenv("NO_COLOR", "1")
        from mapanare.diagnostics import _supports_color

        assert not _supports_color()

    def test_force_color_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FORCE_COLOR env var should enable ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)
        from mapanare.diagnostics import _supports_color

        assert _supports_color()

    def test_underline_span_rendering(self) -> None:
        """Underline carets should appear under the correct columns."""
        source = "let x: Int = true"
        span = Span(line=1, column=14, end_line=1, end_column=18)
        diag = Diagnostic(
            severity=Severity.ERROR,
            message="type mismatch",
            filename="test.mn",
            labels=[Label(span=span, message="not an Int", primary=True)],
        )
        out = format_diagnostic(diag, source, color=False)
        lines = out.split("\n")
        # Find the line with carets
        caret_lines = [line for line in lines if "^^^^" in line]
        assert len(caret_lines) >= 1, f"Expected underline carets in output:\n{out}"
        assert "not an Int" in caret_lines[0]
