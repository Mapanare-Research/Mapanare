"""LSP diagnostic conversion and streaming (v4.40.0).

Converts Mapanare SemanticError and parse errors to LSP Diagnostic format
with proper range mapping (1-based to 0-based) and relatedInformation for
suggestions.
"""

from __future__ import annotations

from typing import Optional

from lsprotocol import types as lsp


def semantic_error_to_diagnostic(
    err: object,
    uri: str,
) -> lsp.Diagnostic:
    """Convert a SemanticError to an LSP Diagnostic.

    Handles the 1-based to 0-based line/column conversion at the boundary.
    Attaches suggestions as relatedInformation entries.
    """
    line = max(0, getattr(err, "line", 1) - 1)
    col = max(0, getattr(err, "column", 1) - 1)
    end_line = getattr(err, "end_line", 0)
    end_col = getattr(err, "end_column", 0)
    end_line = max(0, end_line - 1) if end_line else line
    end_col = max(0, end_col - 1) if end_col else col + 1

    severity = getattr(err, "severity", "error")
    severity_map = {
        "error": lsp.DiagnosticSeverity.Error,
        "warning": lsp.DiagnosticSeverity.Warning,
        "info": lsp.DiagnosticSeverity.Information,
        "hint": lsp.DiagnosticSeverity.Hint,
    }

    message = getattr(err, "message", str(err))

    # v4.40.0: attach suggestions as relatedInformation
    related: Optional[list[lsp.DiagnosticRelatedInformation]] = None
    suggestion = getattr(err, "suggestion", None)
    if suggestion:
        related = [
            lsp.DiagnosticRelatedInformation(
                location=lsp.Location(
                    uri=uri,
                    range=lsp.Range(
                        start=lsp.Position(line=line, character=col),
                        end=lsp.Position(line=end_line, character=end_col),
                    ),
                ),
                message=suggestion if isinstance(suggestion, str) else str(suggestion),
            )
        ]

    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=line, character=col),
            end=lsp.Position(line=end_line, character=end_col),
        ),
        message=message,
        severity=severity_map.get(severity, lsp.DiagnosticSeverity.Error),
        source="mapanare",
        related_information=related,
    )


def parse_error_to_diagnostic(
    message: str,
    line: int = 1,
    column: int = 1,
) -> lsp.Diagnostic:
    """Convert a parse error to an LSP Diagnostic."""
    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=max(0, line - 1), character=max(0, column - 1)),
            end=lsp.Position(line=max(0, line - 1), character=max(0, column)),
        ),
        message=message,
        severity=lsp.DiagnosticSeverity.Error,
        source="mapanare",
    )


def run_semantic_check(source: str, uri: str) -> list[lsp.Diagnostic]:
    """Parse + semantic check a source string, return LSP diagnostics.

    Returns parse error diagnostics if parsing fails, or semantic error
    diagnostics if semantic check finds issues. Returns empty list if clean.
    """
    diagnostics: list[lsp.Diagnostic] = []

    try:
        from mapanare.parser import ParseError, parse

        program = parse(source, filename=uri)
    except Exception as e:
        line = getattr(e, "line", 1) or 1
        col = getattr(e, "column", 1) or 1
        diagnostics.append(parse_error_to_diagnostic(str(e), line, col))
        return diagnostics

    try:
        from mapanare.semantic import check

        errors = check(program, filename=uri)
        for err in errors:
            diagnostics.append(semantic_error_to_diagnostic(err, uri))
    except Exception:
        pass  # Semantic check crash should not block diagnostic delivery

    return diagnostics
