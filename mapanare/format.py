"""Mapanare source formatter — v5.13.0 (Mc.2).

Conservative, whitespace-only canonicalization. The corpus already
follows a unanimous style (4-space indent, LF line endings, no
trailing whitespace, single trailing newline, max one blank line);
this module codifies it without imposing structural changes.

Design notes are in ``docs/roadmap/v5/v5.13.0/STYLE_AUDIT.md``.

Invariants (verified by ``tests/test_format.py``):

- Idempotent: ``format_source(format_source(s)) == format_source(s)``
- AST-preserving: ``parse(s) == parse(format_source(s))``
- Output never contains ``\\r`` or trailing whitespace
- Output never contains 3+ consecutive ``\\n``
- Non-empty output always ends with exactly one ``\\n``

The formatter does NOT re-indent, change brace style, rewrite
expressions, or reorder declarations. Those decisions are deferred
to later releases (see STYLE_AUDIT §5).
"""

from __future__ import annotations

__all__ = ["format_source", "check_formatted"]


def format_source(source: str) -> str:
    """Return ``source`` formatted to canonical whitespace.

    Pure function. No I/O. Idempotent and AST-preserving.
    """
    # 1. Normalize line endings: CRLF -> LF, then bare CR -> LF.
    text = source.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Strip trailing whitespace; convert leading tabs to 4 spaces each.
    #    Tabs are only normalized in leading whitespace — mid-line tabs (e.g.
    #    inside a string literal) are left alone for safety.
    lines: list[str] = []
    for raw in text.split("\n"):
        stripped = raw.rstrip()
        if not stripped:
            lines.append("")
            continue
        content = stripped.lstrip(" \t")
        leading = stripped[: len(stripped) - len(content)]
        leading = leading.replace("\t", "    ")
        lines.append(leading + content)

    # 3. Collapse 2+ consecutive blank lines to 1, drop leading blanks.
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 1 and out:  # never emit leading blanks
                out.append(line)
        else:
            blank_run = 0
            out.append(line)

    # 4. Strip trailing blank lines.
    while out and out[-1] == "":
        out.pop()

    if not out:
        return ""

    # 5. Ensure exactly one trailing newline.
    return "\n".join(out) + "\n"


def check_formatted(source: str) -> bool:
    """Return True iff ``source`` is already canonically formatted."""
    return source == format_source(source)
