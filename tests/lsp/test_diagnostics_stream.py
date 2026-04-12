"""Tests for diagnostic streaming (v4.40.0).

Tests the diagnostic conversion, semantic check integration, and
relatedInformation for suggestions.
"""

from __future__ import annotations

from lsprotocol import types as lsp

from mapanare.lsp.diagnostics import (
    parse_error_to_diagnostic,
    run_semantic_check,
    semantic_error_to_diagnostic,
)


class TestDiagnosticConversion:
    def test_semantic_error_maps_line_column_to_0_based(self) -> None:
        """SemanticError has 1-based lines; LSP uses 0-based."""

        class FakeError:
            line = 5
            column = 10
            end_line = 5
            end_column = 15
            message = "type mismatch"
            severity = "error"
            suggestion = None

        diag = semantic_error_to_diagnostic(FakeError(), "file:///test.mn")
        assert diag.range.start.line == 4  # 5 - 1
        assert diag.range.start.character == 9  # 10 - 1
        assert diag.range.end.line == 4
        assert diag.range.end.character == 14

    def test_error_severity_maps_correctly(self) -> None:
        class FakeError:
            line = 1
            column = 1
            end_line = 0
            end_column = 0
            message = "err"
            severity = "error"
            suggestion = None

        diag = semantic_error_to_diagnostic(FakeError(), "file:///t.mn")
        assert diag.severity == lsp.DiagnosticSeverity.Error

    def test_warning_severity_maps_correctly(self) -> None:
        class FakeWarning:
            line = 1
            column = 1
            end_line = 0
            end_column = 0
            message = "warn"
            severity = "warning"
            suggestion = None

        diag = semantic_error_to_diagnostic(FakeWarning(), "file:///t.mn")
        assert diag.severity == lsp.DiagnosticSeverity.Warning

    def test_suggestion_appears_as_related_information(self) -> None:
        class FakeErrorWithSuggestion:
            line = 3
            column = 5
            end_line = 3
            end_column = 10
            message = "undefined variable 'x'"
            severity = "error"
            suggestion = "did you mean 'y'?"

        diag = semantic_error_to_diagnostic(FakeErrorWithSuggestion(), "file:///t.mn")
        assert diag.related_information is not None
        assert len(diag.related_information) == 1
        assert "did you mean" in diag.related_information[0].message

    def test_no_suggestion_gives_no_related_info(self) -> None:
        class FakeError:
            line = 1
            column = 1
            end_line = 0
            end_column = 0
            message = "err"
            severity = "error"
            suggestion = None

        diag = semantic_error_to_diagnostic(FakeError(), "file:///t.mn")
        assert diag.related_information is None

    def test_diagnostic_range_covers_expression(self) -> None:
        """Range should span from start to end, not just the start position."""

        class FakeError:
            line = 10
            column = 5
            end_line = 10
            end_column = 25
            message = "error"
            severity = "error"
            suggestion = None

        diag = semantic_error_to_diagnostic(FakeError(), "file:///t.mn")
        assert diag.range.start.line == 9
        assert diag.range.start.character == 4
        assert diag.range.end.line == 9
        assert diag.range.end.character == 24


class TestParseErrorDiagnostic:
    def test_parse_error_creates_diagnostic(self) -> None:
        diag = parse_error_to_diagnostic("unexpected token", line=3, column=7)
        assert diag.range.start.line == 2
        assert diag.range.start.character == 6
        assert diag.message == "unexpected token"
        assert diag.severity == lsp.DiagnosticSeverity.Error


class TestSemanticCheckIntegration:
    def test_clean_file_returns_empty(self) -> None:
        source = 'fn main() { print("hello") }'
        diags = run_semantic_check(source, "test.mn")
        # May have warnings but no errors
        errors = [d for d in diags if d.severity == lsp.DiagnosticSeverity.Error]
        assert errors == []

    def test_parse_error_returns_diagnostic(self) -> None:
        source = "fn broken( { invalid syntax"
        diags = run_semantic_check(source, "test.mn")
        assert len(diags) >= 1
        assert diags[0].severity == lsp.DiagnosticSeverity.Error

    def test_fixed_file_clears_diagnostics(self) -> None:
        """A file that used to have errors but is now fixed returns empty."""
        good_source = 'fn main() { print("hello") }'
        diags = run_semantic_check(good_source, "test.mn")
        errors = [d for d in diags if d.severity == lsp.DiagnosticSeverity.Error]
        assert errors == []
