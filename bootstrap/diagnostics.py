"""Structured diagnostics with spans, labels, suggestions, and colorized output."""

from __future__ import annotations

import enum
import os
import sys
from dataclasses import dataclass, field

from mapanare.ast_nodes import Span

# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------


class Severity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    HELP = "help"


# ---------------------------------------------------------------------------
# Label — annotates a span within the source
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Label:
    """A labeled source span (primary or secondary)."""

    span: Span
    message: str = ""
    primary: bool = True


# ---------------------------------------------------------------------------
# Suggestion — a concrete fix the user can apply
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Suggestion:
    """A suggested code fix."""

    message: str
    replacement: str = ""
    span: Span | None = None


# ---------------------------------------------------------------------------
# Diagnostic — a single compiler diagnostic
# ---------------------------------------------------------------------------


@dataclass
class Diagnostic:
    """A structured compiler diagnostic with source location, labels, and suggestions."""

    severity: Severity
    message: str
    filename: str = "<input>"
    labels: list[Label] = field(default_factory=list)
    suggestions: list[Suggestion] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def line(self) -> int:
        for lbl in self.labels:
            if lbl.primary:
                return lbl.span.line
        return 0

    @property
    def column(self) -> int:
        for lbl in self.labels:
            if lbl.primary:
                return lbl.span.column
        return 0

    @property
    def span(self) -> Span | None:
        for lbl in self.labels:
            if lbl.primary:
                return lbl.span
        return None

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.column}: {self.severity.value}: {self.message}"


# ---------------------------------------------------------------------------
# DiagnosticBag — collects diagnostics from multiple phases
# ---------------------------------------------------------------------------


class DiagnosticBag:
    """Collects diagnostics from parsing and semantic analysis."""

    def __init__(self) -> None:
        self.diagnostics: list[Diagnostic] = []

    def add(self, diag: Diagnostic) -> None:
        self.diagnostics.append(diag)

    def error(
        self,
        message: str,
        span: Span,
        filename: str = "<input>",
        label: str = "",
        suggestions: list[Suggestion] | None = None,
        notes: list[str] | None = None,
    ) -> None:
        labels = [Label(span=span, message=label, primary=True)]
        self.diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message=message,
                filename=filename,
                labels=labels,
                suggestions=suggestions or [],
                notes=notes or [],
            )
        )

    def warning(
        self,
        message: str,
        span: Span,
        filename: str = "<input>",
        label: str = "",
    ) -> None:
        labels = [Label(span=span, message=label, primary=True)]
        self.diagnostics.append(
            Diagnostic(
                severity=Severity.WARNING,
                message=message,
                filename=filename,
                labels=labels,
            )
        )

    @property
    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.WARNING)


# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------


def _supports_color(stream: object = None) -> bool:
    """Check if the output stream supports ANSI colors."""
    if stream is None:
        stream = sys.stderr
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    return bool(isatty())


class _Colors:
    """ANSI escape codes for terminal colors."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    BOLD_RED = "\033[1;31m"
    YELLOW = "\033[33m"
    BOLD_YELLOW = "\033[1;33m"
    BLUE = "\033[34m"
    BOLD_BLUE = "\033[1;34m"
    CYAN = "\033[36m"
    BOLD_CYAN = "\033[1;36m"
    GREEN = "\033[32m"
    BOLD_GREEN = "\033[1;32m"
    DIM = "\033[2m"


class _NoColors:
    """No-op colors for non-TTY output."""

    RESET = ""
    BOLD = ""
    RED = ""
    BOLD_RED = ""
    YELLOW = ""
    BOLD_YELLOW = ""
    BLUE = ""
    BOLD_BLUE = ""
    CYAN = ""
    BOLD_CYAN = ""
    GREEN = ""
    BOLD_GREEN = ""
    DIM = ""


# ---------------------------------------------------------------------------
# Format a single diagnostic
# ---------------------------------------------------------------------------

_SEVERITY_STYLE = {
    Severity.ERROR: ("BOLD_RED", "error"),
    Severity.WARNING: ("BOLD_YELLOW", "warning"),
    Severity.NOTE: ("BOLD_CYAN", "note"),
    Severity.HELP: ("BOLD_GREEN", "help"),
}


def format_diagnostic(
    diag: Diagnostic,
    source: str | None = None,
    *,
    color: bool | None = None,
) -> str:
    """Format a single diagnostic into a human-readable string.

    If *source* is provided, underline spans are rendered in context.
    """
    if color is None:
        color = _supports_color()
    c = _Colors if color else _NoColors

    style_attr, severity_text = _SEVERITY_STYLE[diag.severity]
    sev_color = getattr(c, style_attr)

    parts: list[str] = []

    # Header: filename:line:col: severity: message
    loc = f"{diag.filename}:{diag.line}:{diag.column}"
    parts.append(
        f"{c.BOLD}{loc}: {sev_color}{severity_text}{c.RESET}{c.BOLD}: {diag.message}{c.RESET}"
    )

    # Source context with underline spans
    if source is not None and diag.labels:
        source_lines = source.splitlines()
        for label in diag.labels:
            span = label.span
            if span.line < 1 or span.line > len(source_lines):
                continue

            line_text = source_lines[span.line - 1]
            line_num = str(span.line)
            gutter_width = len(line_num) + 1

            # Line number + source line
            parts.append(f"{c.BOLD_BLUE}{' ' * gutter_width}|{c.RESET}")
            parts.append(f"{c.BOLD_BLUE}{line_num} | {c.RESET}{line_text}")

            # Underline span
            col_start = max(span.column - 1, 0)
            if span.end_line == span.line and span.end_column > span.column:
                underline_len = span.end_column - span.column
            else:
                underline_len = max(len(line_text) - col_start, 1)

            underline_color = sev_color if label.primary else getattr(c, "BOLD_BLUE")
            caret = "^" * max(underline_len, 1)
            padding = " " * col_start
            label_suffix = f" {label.message}" if label.message else ""
            parts.append(
                f"{c.BOLD_BLUE}{' ' * gutter_width}| {c.RESET}"
                f"{padding}{underline_color}{caret}{label_suffix}{c.RESET}"
            )

    # Suggestions
    for suggestion in diag.suggestions:
        parts.append(f"{c.BOLD_GREEN}help{c.RESET}{c.BOLD}: {suggestion.message}{c.RESET}")
        if suggestion.replacement:
            parts.append(f"  {c.GREEN}{suggestion.replacement}{c.RESET}")

    # Notes
    for note in diag.notes:
        parts.append(f"{c.BOLD_CYAN}note{c.RESET}{c.BOLD}: {note}{c.RESET}")

    return "\n".join(parts)


def format_diagnostics(
    diagnostics: list[Diagnostic],
    source: str | None = None,
    *,
    color: bool | None = None,
) -> str:
    """Format multiple diagnostics, separated by blank lines."""
    if not diagnostics:
        return ""
    blocks = [format_diagnostic(d, source, color=color) for d in diagnostics]
    return "\n\n".join(blocks) + "\n"


def format_summary(
    diagnostics: list[Diagnostic],
    *,
    color: bool | None = None,
) -> str:
    """Format an error/warning count summary line."""
    if color is None:
        color = _supports_color()
    c = _Colors if color else _NoColors

    errors = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
    warnings = sum(1 for d in diagnostics if d.severity == Severity.WARNING)

    parts: list[str] = []
    if errors:
        parts.append(f"{c.BOLD_RED}{errors} error{'s' if errors != 1 else ''}{c.RESET}")
    if warnings:
        parts.append(f"{c.BOLD_YELLOW}{warnings} warning{'s' if warnings != 1 else ''}{c.RESET}")
    if not parts:
        return ""
    return f"{c.BOLD}aborting due to {' and '.join(parts)}{c.RESET}"
