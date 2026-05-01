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

v5.21.1 — Chained comparisons (v5.21.0 Te.6, e.g. ``0 < x < 10``)
are token-shaped just like ordinary binary comparisons; the
line-based whitespace canonicalization preserves them with single
spaces around each operator without any expression-level pass.
The formatter therefore needs no ``ChainedCompare`` arm —
``format_source`` already round-trips chains stable, and
``to_terse`` / ``to_braces`` (which act only on block openers and
trailing commas) leave chain lines verbatim. This is verified by
the corpus invariants over goldens 92–95 and
``examples/chained_cmp.mn``.
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
# v5.19.0 Te.3.B: include Spanish aliases ``tipo`` (struct) and
# ``modo`` / ``way`` (trait).
_COMMA_BODY_OPENERS = (
    "struct ",
    "enum ",
    "match ",
    "tipo ",
    "modo ",
    "way ",
)

# v5.17.0 Sh.A.1: keywords that begin a statement-level block which
# is safe to convert from `... {` to `... :`. Anything else (e.g.
# ``let x = if cond {``, struct literals, lambdas inlined as
# arguments) opens an *expression*-context block whose grammar
# requires braces — those must be left verbatim.
# v5.19.0 Te.3.B: extended with Spanish keyword aliases so the
# formatter can migrate downstream user code that mixes English and
# Spanish surface (the v3.0.0 bilingual feature).
_STMT_BLOCK_KEYWORDS = (
    "fn",
    "if",
    "si",
    "while",
    "mien",
    "for",
    "cada",
    "loop",
    "struct",
    "tipo",
    "enum",
    "trait",
    "modo",
    "way",
    "agent",
    "impl",
    "match",
    "do",
)
_STMT_BLOCK_PREFIXES = ("pub ", "async ", "extern ")
_CONTINUATION_PREFIXES = ("else", "sino")


def _looks_like_stmt_block_opener(opener_body: str) -> bool:
    """Return True if ``opener_body`` (line content with the trailing
    `` {`` already stripped) is a statement-level block opener that can
    safely be converted to colon form. Continuations like ``} else {``
    and ``} else if EXPR {`` also return True since they are
    statement-level. Returns False for expression-context openers
    like ``let x = if cond {`` or ``Foo {`` (struct literal)."""
    s = opener_body
    # Strip continuation prefix (`} `): handles `} else {`, `} sino si X {`.
    if s.startswith("} "):
        s = s[2:]
    # Strip visibility / async / extern modifiers.
    while True:
        for prefix in _STMT_BLOCK_PREFIXES:
            if s.startswith(prefix):
                s = s[len(prefix) :]
                break
        else:
            break
    # Statement keyword: `fn name(...)`, `if cond`, `loop`, ...
    # v5.19.0 Te.3.B: also recognize generic-prefixed openers like
    # `impl<T> Box<T>`, `fn<T>(...)`, `struct Foo<T>` (the last two
    # already match via the space form, but `impl<T>` needs the
    # ``<`` suffix).
    for kw in _STMT_BLOCK_KEYWORDS:
        if s == kw or s.startswith(kw + " ") or s.startswith(kw + "(") or s.startswith(kw + "<"):
            return True
    # Continuations after `} ` strip: `else`, `else if`, `else{`, ...
    # v5.19.0 Te.3.B: include Spanish ``si`` for ``} else si X {`` and
    # ``} sino si X {`` shapes.
    for kw in _CONTINUATION_PREFIXES:
        if s == kw or s.startswith(kw + " ") or s.startswith(kw + "{"):
            return True
    return False


def _find_brace_close(lines: list[str], start_idx: int, opener_indent: int) -> int:
    """Find the index of the line containing the matching ``}`` for the
    brace opener at ``lines[start_idx]``. The closer is expected to sit
    at column ``opener_indent``. Returns -1 if not found.

    Counts ``{`` / ``}`` characters across lines, skipping content
    inside ``"`` / ``'`` string literals (with backslash escapes) and
    ``//`` line comments. Trusts the source not to embed unbalanced
    braces in unusual places. Used by ``_find_match_verbatim_lines``
    to bracket non-statement-block openers.
    """
    depth = 0
    # Count the opener line's net braces too — usually exactly 1 for
    # a clean `... {` opener, but the line may contain inline pairs.
    # Check depth only at end-of-line so that ``} else {`` (which
    # transiently hits 0 mid-line but reopens) is not mistaken for
    # the final closer.
    for line_no in range(start_idx, len(lines)):
        s = lines[line_no]
        in_str = False
        in_char = False
        j = 0
        while j < len(s):
            ch = s[j]
            if in_str:
                if ch == "\\" and j + 1 < len(s):
                    j += 2
                    continue
                if ch == '"':
                    in_str = False
            elif in_char:
                if ch == "\\" and j + 1 < len(s):
                    j += 2
                    continue
                if ch == "'":
                    in_char = False
            else:
                # Line comment terminates the line for brace-counting
                if ch == "/" and j + 1 < len(s) and s[j + 1] == "/":
                    break
                if ch == '"':
                    in_str = True
                elif ch == "'":
                    in_char = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
            j += 1
        if depth == 0 and line_no > start_idx:
            return line_no
    return -1


def _find_match_verbatim_lines(lines: list[str]) -> set[int]:
    """Return line indices that lie within ``match`` blocks containing
    at least one multi-line arm body.

    Such matches must be preserved verbatim by ``to_terse`` because
    ``_indent_to_braces`` does not track brace nesting inside match
    bodies — converting the outer ``match X {`` to ``match X:`` while
    keeping the inner multi-line arm in brace form would cause the
    preprocessor to insert a spurious ``,`` after every nested colon
    opener, producing ``match X { ... { Pat => {, ... }`` (invalid).

    Detection is line-based and trusts canonical formatting (4-space
    indent, no inline ``{``/``}`` in unusual positions). For a
    ``match X {`` opener at column ``k``, the match body lives at
    column ``k+4``. A multi-line arm opener is any body-level line
    ending with `` {`` whose stripped content (minus the trailing
    `` {``) ends with ``=>``. The match block ends at the first line
    at column ``k`` or less whose content begins with ``}``.

    The returned set covers every line from the ``match`` opener
    through its closing ``}`` inclusive.
    """
    verbatim: set[int] = set()
    n = len(lines)
    i = 0
    while i < n:
        s = lines[i].rstrip()
        if not s.endswith(" {"):
            i += 1
            continue
        opener_body = s[:-2].rstrip()
        # Find indent of the opener line
        leading_len = len(s) - len(s.lstrip(" "))
        # Strip the leading indent off the opener body to test prefix
        body_text = opener_body[leading_len:] if len(opener_body) >= leading_len else opener_body

        # Non-statement-block opener (e.g. ``let x = if cond {`` —
        # an expression-context if). The grammar requires braces here,
        # so mark the entire ``{ ... }`` range as verbatim. ``=>``
        # arm bodies and continuation lines (``} else {``) inside the
        # range are also kept verbatim by the main loop's verbatim
        # propagation.
        if not _looks_like_stmt_block_opener(body_text) and not body_text.endswith("=>"):
            end_idx = _find_brace_close(lines, i, leading_len)
            if end_idx >= 0:
                for k in range(i, end_idx + 1):
                    verbatim.add(k)
                i = end_idx + 1
                continue
            i += 1
            continue

        if not body_text.startswith("match "):
            i += 1
            continue
        # Scan the match body. Body lines start at leading_len + 4.
        # The match closes at a line whose content starts with `}` at
        # column leading_len.
        body_indent = leading_len + 4
        has_multiline_arm = False
        end_idx = -1
        for j in range(i + 1, n):
            t = lines[j].rstrip()
            if not t:
                continue
            t_lstripped = t.lstrip()
            t_indent = len(t) - len(t_lstripped)
            if t_lstripped.startswith(("//", "#")):
                continue
            # Closer of the match block?
            if t_indent <= leading_len and t_lstripped.startswith("}"):
                end_idx = j
                break
            # Multi-line arm opener at body level?
            if t_indent == body_indent and t.endswith(" {"):
                arm_opener = t[:-2].rstrip()
                if arm_opener.endswith("=>"):
                    has_multiline_arm = True
            # Don't break on multi-line arm; keep scanning to find
            # the close so we can mark the entire range.
        if has_multiline_arm and end_idx >= 0:
            for k in range(i, end_idx + 1):
                verbatim.add(k)
            i = end_idx + 1
        else:
            i += 1
    return verbatim


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

    # v5.17.0 Sh.A.1: pre-pass — identify line indices belonging to
    # ``match X { ... }`` blocks that contain at least one multi-line
    # arm body (``Pat => {`` opener). Such matches must stay fully in
    # brace form: ``_indent_to_braces`` does not track brace nesting
    # inside match bodies, so any colon-block inside a multi-line arm
    # would be mistaken for a match sibling and trigger a spurious
    # comma insertion. Matches with only single-line arms (or only
    # ``=> {}`` empties) are still safely converted.
    verbatim_lines = _find_match_verbatim_lines(lines)

    out: list[str] = []
    # Stack of (indent_str, comma_body, kind) triples tracking
    # colon-block context produced by the rewrite. ``comma_body`` is
    # True when the opener was struct/enum/match — used to strip
    # trailing commas from member lines. ``kind`` is "colon" for a
    # rewritten colon-block, or "verbatim" for a match-arm body
    # (``Pat => {``) which keeps its braces because the grammar
    # rejects ``=>:`` (v5.17.0 Sh.A.1).
    block_stack: list[tuple[str, bool, str]] = []

    for line_idx, raw in enumerate(lines):
        if line_idx in verbatim_lines:
            # Inside a match block with multi-line arms — pass through
            # unchanged so the brace form is preserved.
            out.append(raw)
            continue

        stripped = raw.rstrip()
        if not stripped:
            out.append("")
            continue

        leading = raw[: len(raw) - len(raw.lstrip(" "))]
        content = stripped[len(leading) :]

        # Pop blocks whose body has ended (indentation has decreased).
        # Track whether any popped block was a verbatim arm-body so we
        # can drop the closer ``},`` (otherwise comma-stripping leaves
        # an orphan ``}``).
        popped_verbatim = False
        while block_stack and len(leading) <= len(block_stack[-1][0]):
            popped = block_stack.pop()
            if popped[2] == "verbatim":
                popped_verbatim = True

        # Inside a verbatim arm body (``Pat => { ... }``), keep ALL
        # lines unchanged. Rewriting inner colon-blocks inside the arm
        # body would confuse ``_indent_to_braces``'s match-sibling
        # comma-insertion logic, which doesn't track brace-form arm
        # body nesting and would treat nested colon-openers as match
        # siblings of the arm opener.
        if (
            block_stack
            and block_stack[-1][2] == "verbatim"
            and len(leading) > len(block_stack[-1][0])
        ):
            out.append(f"{leading}{content}")
            continue

        # Continuation: ``} else {``, ``} else if EXPR {``, Spanish forms
        if content == "}":
            # Colon blocks have no closer in terse form — drop the
            # brace. Verbatim arm bodies (``Pat => { ... }``) keep
            # the brace because the grammar requires it.
            if popped_verbatim:
                out.append(f"{leading}}}")
            continue

        if content == "},":
            # ``},`` only appears as a match-arm closer. Keep the
            # brace (verbatim arm needs it) and drop the comma —
            # ``_indent_to_braces`` re-inserts the sibling separator
            # automatically when round-tripping.
            if popped_verbatim:
                out.append(f"{leading}}}")
            continue

        if content.startswith("} ") and content.endswith(" {"):
            # Pattern: ``} CONTINUATION {`` — rewrite as ``CONTINUATION:``
            mid = content[2:-2].strip()
            if mid.startswith(("else", "sino")):
                out.append(f"{leading}{mid}:")
                block_stack.append((leading, False, "colon"))
                continue

        if content.endswith(" {"):
            opener = content[:-2].rstrip()
            # Match-arm body (``Pat => {``): grammar requires brace or
            # single-expr arm, so leave the line alone and track the
            # block as verbatim. Inner content (e.g. ``if x {`` inside
            # the arm) still gets the normal colon-block rewrite.
            if opener.endswith("=>"):
                out.append(f"{leading}{content}")
                block_stack.append((leading, False, "verbatim"))
                continue
            comma_body = any(opener.startswith(p) for p in _COMMA_BODY_OPENERS)
            out.append(f"{leading}{opener}:")
            block_stack.append((leading, comma_body, "colon"))
            continue

        if content.endswith("{}"):
            opener = content[:-2].rstrip()
            # Match-arm empty body (``Pat => {}``): keep as-is. Grammar
            # rejects ``=>:`` and ``pass`` is a stmt, not an expression
            # — there is no terse equivalent.
            if opener.endswith("=>"):
                out.append(f"{leading}{content}")
                continue
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
