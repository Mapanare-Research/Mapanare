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

__all__ = [
    "format_source",
    "check_formatted",
    "to_terse",
    "to_braces",
]


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


# ---------------------------------------------------------------------------
# v5.14.0 Te.1 — colon-block rewriters.
#
# ``to_terse`` rewrites brace-block syntax to colon-block syntax.
# ``to_braces`` is the inverse, implemented as a thin wrapper over the
# parser's ``_indent_to_braces`` preprocessor.
#
# Both rewriters are line-based and comment-preserving, matching the
# architecture of ``format_source``. They are NOT AST-based — that
# would lose comments, which is unacceptable for v5.17.0's mechanical
# rewrite of ``mapanare/self/`` (~14k lines, comments load-bearing).
# The trade-off: text-level transforms can be confused by unusual
# layouts. The rewriters refuse (return source unchanged) on patterns
# they cannot prove safe; ``--check`` mode surfaces these.
# ---------------------------------------------------------------------------

# Block-opener prefixes that introduce a comma-separated body. Inside
# these blocks ``to_terse`` strips trailing commas from member lines
# (the colon form has implicit separators); ``to_braces`` re-inserts
# them via the parser preprocessor.
_COMMA_BODY_OPENERS = ("struct ", "enum ", "match ")


def to_terse(source: str) -> str:
    """Rewrite brace-block syntax to colon-block syntax.

    Idempotent and comment-preserving. Round-trip with ``to_braces``
    yields source equivalent to ``format_source(source)``.

    Pattern rules (applied in order, after ``format_source``):

    1. Line ending with `` {`` → strip the trailing `` {`` and append ``:``.
    2. Line that is exactly `` } `` (any indent) → drop.
    3. Line matching `` } else {`` / `` } else if EXPR {`` / Spanish
       counterparts → rewrite as ``else:`` / ``else if EXPR:``.
    4. Line ending with `` {}`` → expand to colon-block + indented
       ``pass``.
    5. Trailing commas inside struct/enum/match bodies → stripped.

    Any line that does not match a known shape is passed through
    unchanged. This means ``to_terse`` is *conservative* — it never
    invents syntax, just elides braces where the layout is canonical.
    """
    text = format_source(source)
    if not text:
        return text

    lines = text.split("\n")
    out: list[str] = []
    # Stack of (indent_str, comma_body) pairs tracking colon-block
    # context produced by the rewrite. ``comma_body`` is True when the
    # opener was struct/enum/match — used to strip trailing commas
    # from member lines.
    block_stack: list[tuple[str, bool]] = []

    for raw in lines:
        stripped = raw.rstrip()
        if not stripped:
            out.append("")
            continue

        leading = raw[: len(raw) - len(raw.lstrip(" "))]
        content = stripped[len(leading) :]

        # Pop blocks whose body has ended (indentation has decreased).
        while block_stack and len(leading) <= len(block_stack[-1][0]):
            block_stack.pop()

        # Continuation: ``} else {``, ``} else if EXPR {``, Spanish forms
        if content == "}":
            # Pure closer — drop. Block context already popped above.
            continue

        if content.startswith("} ") and content.endswith(" {"):
            # Pattern: ``} CONTINUATION {`` — rewrite as ``CONTINUATION:``
            mid = content[2:-2].strip()
            if mid.startswith(("else", "sino")):
                out.append(f"{leading}{mid}:")
                block_stack.append((leading, False))
                continue

        if content.endswith(" {"):
            opener = content[:-2].rstrip()
            comma_body = any(opener.startswith(p) for p in _COMMA_BODY_OPENERS)
            out.append(f"{leading}{opener}:")
            block_stack.append((leading, comma_body))
            continue

        if content.endswith("{}"):
            opener = content[:-2].rstrip()
            comma_body = any(opener.startswith(p) for p in _COMMA_BODY_OPENERS)
            out.append(f"{leading}{opener}:")
            inner_indent = leading + "    "
            out.append(f"{inner_indent}pass")
            # Don't push to block_stack — body is closed in one step.
            # The lone ``pass`` belongs to a transient block at deeper
            # indent that has no siblings.
            del comma_body  # not relevant here
            continue

        # Inside a comma-body block, strip trailing comma from members.
        if (
            block_stack
            and block_stack[-1][1]
            and content.endswith(",")
            and len(leading) > len(block_stack[-1][0])
        ):
            content = content[:-1].rstrip()

        out.append(f"{leading}{content}")

    rewritten = "\n".join(out) + ("\n" if out else "")
    # Final pass through ``format_source`` to collapse any extra blank
    # lines that resulted from dropped ``}`` lines.
    return format_source(rewritten)


def to_braces(source: str) -> str:
    """Rewrite colon-block syntax to brace-block syntax.

    Thin wrapper around the parser's ``_indent_to_braces``
    preprocessor, then ``format_source`` for canonical whitespace.
    Idempotent on already-brace-style source (the preprocessor's
    fast path returns unchanged input when no ``:``-suffixed lines
    are present).
    """
    from mapanare.parser import _indent_to_braces

    return format_source(_indent_to_braces(source))
