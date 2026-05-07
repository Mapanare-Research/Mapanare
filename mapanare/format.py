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
``examples/terseness/chained_cmp.mn``.
"""

from __future__ import annotations

__all__ = [
    "format_source",
    "check_formatted",
    "to_terse",
    "to_braces",
    "to_terse_markdown",
    "find_long_lines",
    "sort_imports",
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


# v5.48.0 Te.3.D.3: stmt keywords accepted as match-arm bodies in
# the new colon shorthand (``Pat => return x``, ``Pat => break``).
# Mirrors the parser's ``_ARM_STMT_KEYWORDS``.
_ARM_STMT_KEYWORDS_FMT = (
    "return",
    "da",
    "break",
    "sal",
    "continue",
    "sigue",
    "pass",
)


def _mask_strings(line: str) -> str:
    """Return a shadow copy of ``line`` with string / char literals and
    line comments masked to spaces, so brace / colon scanners ignore
    content inside them. Used by the v5.48.0 one-line migration
    helpers.
    """
    out = list(line)
    in_str = False
    in_char = False
    n = len(line)
    i = 0
    while i < n:
        ch = line[i]
        if in_str:
            out[i] = " "
            if ch == "\\" and i + 1 < n:
                out[i + 1] = " "
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if in_char:
            out[i] = " "
            if ch == "\\" and i + 1 < n:
                out[i + 1] = " "
                i += 2
                continue
            if ch == "'":
                in_char = False
            i += 1
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            for j in range(i, n):
                out[j] = " "
            break
        if ch == '"':
            out[i] = " "
            in_str = True
            i += 1
            continue
        if ch == "'":
            out[i] = " "
            in_char = True
            i += 1
            continue
        i += 1
    return "".join(out)


def _find_matching_close(shadow: str, open_idx: int) -> int:
    """Given an opening ``{`` at ``shadow[open_idx]``, return the index
    of the matching ``}`` at the same depth, or ``-1`` if none on the
    same string. ``shadow`` must be string-masked (see ``_mask_strings``).
    """
    depth = 1
    n = len(shadow)
    i = open_idx + 1
    while i < n:
        c = shadow[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _migrate_one_line_arm_body(content: str) -> str:
    """Rewrite ``Pat => { body }`` arm bodies to compact form.

    v5.48.0 Te.3.D.3. Operates on a single line of brace-form source.
    Produces:

    - ``Pat => { return x }`` -> ``Pat => return x``
    - ``Pat => { da x }`` -> ``Pat => da x``
    - ``Pat => { break }`` -> ``Pat => break``
    - ``Pat => { print(x) }`` -> ``Pat => print(x)``
    - ``Pat => { k = 1 }`` -> ``Pat => k = 1``

    Skips when:

    - body contains a top-level ``;`` (multi-stmt, no shorthand)
    - body itself contains a nested ``{`` block (would break parse)
    - body is empty (``Pat => {}`` — no shorthand exists)

    Trailing ``,`` (sibling separator) is preserved. Leading whitespace
    is preserved. Idempotent: a line already in shorthand form is
    returned unchanged.
    """
    if "=>" not in content or "{" not in content:
        return content
    shadow = _mask_strings(content)

    # Walk left-to-right to find ``=> { body }`` segments. Each match
    # is replaced from the position of ``{`` through the matching ``}``
    # (and the leading space before ``{``).
    edits: list[tuple[int, int, str]] = []
    pos = 0
    n = len(shadow)
    while True:
        arrow = shadow.find("=>", pos)
        if arrow < 0:
            break
        # advance past `=>`
        body_pos = arrow + 2
        # skip whitespace
        while body_pos < n and shadow[body_pos] in (" ", "\t"):
            body_pos += 1
        if body_pos >= n or shadow[body_pos] != "{":
            pos = arrow + 2
            continue
        close = _find_matching_close(shadow, body_pos)
        if close < 0:
            pos = arrow + 2
            continue
        # Body is content[body_pos+1 : close], stripped.
        body = content[body_pos + 1 : close].strip()
        # Skip empty body — keep brace form.
        if not body:
            pos = close + 1
            continue
        # Skip nested brace (a sub-block inside the arm body — too
        # risky to flatten textually).
        body_shadow = shadow[body_pos + 1 : close]
        if "{" in body_shadow or "}" in body_shadow:
            pos = close + 1
            continue
        # v5.50.0 Te.3.E.1: ``;``-bearing multi-stmt bodies are
        # accepted. The parser's ``_rewrite_arm_stmt_shorthand``
        # re-wraps them in ``{ }`` on round-trip via the depth-0
        # ``;`` detection. Pre-v5.50.0 this branch rejected ``;``
        # bodies because the parser didn't accept the colon form.
        # Build replacement: from arrow+2 (after `=>`) through close+1
        # (after `}`). Replace ``{ body }`` with `` body``.
        replacement = " " + body
        edits.append((arrow + 2, close + 1, replacement))
        pos = close + 1

    if not edits:
        return content
    result = content
    for s, e, r in reversed(edits):
        result = result[:s] + r + result[e:]
    return result


def _migrate_one_line_stmt_block(leading: str, content: str) -> str | None:
    """Rewrite a single-line statement-block brace to colon form.

    v5.48.0 Te.3.D.3. Returns the rewritten line (with ``leading``
    re-applied) if migration succeeds, or ``None`` if the content
    does not match the single-line pattern or is unsafe to migrate.

    Pattern: ``<head> { <body> }`` where ``<head>`` is a stmt-block
    opener (``if x``, ``fn name()``, ``while x``, ``for x in xs``,
    Spanish forms, continuations like ``} else``, ``} else if x``).
    Body must be a single statement (no top-level ``;``) and must not
    contain nested ``{...}``.

    Special-case: ``} else { body }`` and ``} else if X { body }``
    continuation forms are also accepted; they require the previous
    line to be the ``}`` closer of an if-block, which the formatter's
    line-by-line architecture has already produced as a separate
    line (the ``content == "}"`` branch).
    """
    if "{" not in content or not content.endswith("}"):
        return None
    shadow = _mask_strings(content)
    open_idx = shadow.find("{")
    if open_idx < 0:
        return None
    close_idx = _find_matching_close(shadow, open_idx)
    if close_idx < 0:
        return None
    # Anything after the matching close (other than trailing whitespace)?
    # If yes, this is not a clean single-line brace (e.g. inline if-else
    # ``if x { 1 } else { 2 }`` or arm with trailing comma).
    tail = content[close_idx + 1 :]
    if tail.strip():
        return None
    head = content[:open_idx].rstrip()
    body = content[open_idx + 1 : close_idx].strip()
    if not body:
        return None
    body_shadow = shadow[open_idx + 1 : close_idx]
    if "{" in body_shadow or "}" in body_shadow:
        return None
    # v5.50.0 Te.3.E.1: ``;``-bearing multi-stmt bodies migrate
    # symmetrically with arm bodies. ``if X { a = 1; b = 2 }`` →
    # ``if X: a = 1; b = 2`` round-trips through
    # ``_indent_to_braces`` + grammar BLOCK rule (which accepts
    # ``;``-separated statements).
    # Reject match-arm shape (``Pat =>``); arm migration is handled
    # separately by ``_migrate_one_line_arm_body``.
    if head.endswith("=>"):
        return None
    if not _looks_like_stmt_block_opener(head):
        return None
    # Reject comma-body openers — their bodies need multi-line grammar.
    if any(head.startswith(p) for p in _COMMA_BODY_OPENERS):
        return None
    # v5.48.1 Te.3.D.5.1: reject implicit-return shapes like
    # ``fn make() -> Point = Point { x }`` — that's an expression-binding
    # whose `{...}` is a struct literal, not a stmt block. Mirrors the
    # `=` filter in count_user_brace_block_openers Rule (b). Without
    # this, the formatter migrates ``fn new_token(...) -> Token = new
    # Token { ... }`` to ``fn new_token(...) -> Token: new Token: ...``,
    # which collapses two distinct semantic levels and is unparseable.
    head_shadow = _mask_strings(head)
    if _has_standalone_eq(head_shadow):
        return None
    # Reject ``} else { body }`` chained with a trailing continuation
    # (we already filtered ``tail.strip()`` so we know nothing follows).
    return f"{leading}{head}: {body}"


def _has_standalone_eq(s: str) -> bool:
    """Return True if ``s`` contains a ``=`` that is NOT part of any of
    ``==``, ``!=``, ``<=``, ``>=``, ``=>``, ``+=``, ``-=``, ``*=``,
    ``/=``, ``%=``. Used to detect implicit-return / assignment shapes
    that disqualify single-line stmt-block migration. Mirrors
    ``count_user_brace_block_openers`` Rule (b)'s filter.
    """
    n = len(s)
    i = 0
    while i < n:
        if s[i] == "=":
            prev_ch = s[i - 1] if i > 0 else " "
            next_ch = s[i + 1] if i + 1 < n else " "
            if next_ch in ("=", ">"):
                i += 2
                continue
            if prev_ch in ("=", "!", "<", ">", "+", "-", "*", "/", "%"):
                i += 1
                continue
            return True
        i += 1
    return False


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
    """Return line indices inside expression-context brace blocks that
    must stay verbatim under ``to_terse``.

    v5.50.0 Te.3.E.3 rescoped: the only verbatim case left is
    expression-position openers like ``let x = if cond {`` or
    ``let m: Map<K,V> = #{`` — the grammar requires braces in those
    positions. The previous match-with-multiline-arm verbatim mark
    was a workaround for the missing multi-line arm-body grammar;
    Te.3.E.2 added ``Pat =>:`` colon form, so match blocks (statement
    or expression context) and their arm bodies now rewrite cleanly
    via the main ``to_terse`` loop.

    Detection is line-based and trusts canonical formatting (4-space
    indent, no inline ``{``/``}`` in unusual positions). For an
    expression-context opener at column ``k``, the verbatim range
    runs from the opener line through the matching ``}`` closer
    inclusive.
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

        # Expression-context opener (e.g. ``let x = if cond {``,
        # ``let m: Map<K,V> = #{``). The grammar requires braces here,
        # so mark the entire ``{ ... }`` range as verbatim. ``=>``
        # arm bodies are NOT expression-context openers — they are
        # statement-or-expression contexts handled by the colon-form
        # rewrite (Te.3.E.2).
        if not _looks_like_stmt_block_opener(body_text) and not body_text.endswith("=>"):
            end_idx = _find_brace_close(lines, i, leading_len)
            if end_idx >= 0:
                for k in range(i, end_idx + 1):
                    verbatim.add(k)
                i = end_idx + 1
                continue
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

        # v5.50.0 Te.3.E.3: ``}`` followed by a trailing line comment
        # (``} // end of foo``) is a closer with a trailing comment.
        # Pre-Te.3.E.3 this case was hidden by the
        # ``_find_match_verbatim_lines`` workaround (which kept the
        # whole match block in brace form). After Te.3.E.3 the surrounding
        # match migrates, leaving the closer's comment as an orphan ``}``
        # in colon-form output. Strip the brace, preserve the comment.
        if content.startswith("}") and len(content) >= 2:
            after = content[1:].lstrip()
            if after.startswith(("//", "#")):
                if popped_verbatim:
                    out.append(f"{leading}{content}")
                else:
                    # Drop the leading ``}``, keep the comment indented
                    # at the parent block's level.
                    out.append(f"{leading}{after}")
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
            # v5.50.0 Te.3.E.2 + Te.3.E.3: multi-line arm body
            # (``Pat => {``) becomes colon form (``Pat =>:``). Pre-
            # v5.50.0 this branch kept the brace and pushed a verbatim
            # block; the verbatim mark was a workaround for the
            # missing multi-line arm-body grammar, now obsolete.
            if opener.endswith("=>"):
                out.append(f"{leading}{opener}:")
                block_stack.append((leading, False, "colon"))
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
            # v5.27.0 Tk.1: expression-context empty literals (``#{}`` empty
            # map, ``Foo {}`` empty struct, ``[]``-equivalent etc.) are NOT
            # block openers. Apply the same statement-block-opener filter the
            # ``endswith(" {")`` branch relies on (via the verbatim pre-pass)
            # so ``let m: Map<K, V> = #{}`` survives ``to_terse`` unchanged
            # rather than collapsing to ``let m: Map<K, V> = #:`` + ``pass``.
            if not _looks_like_stmt_block_opener(opener):
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

        # v5.48.0 Te.3.D.3: rewrite single-line match-arm brace bodies
        # to compact form (``Pat => { return x }`` -> ``Pat => return x``).
        # Runs before comma-stripping so the comma logic still sees the
        # final shape.
        content = _migrate_one_line_arm_body(content)

        # Inside a comma-body block, strip trailing comma from members.
        # Snapshot whether the line carried a trailing comma so the
        # single-line stmt-block migration below can reattach it.
        had_trailing_comma = (
            block_stack
            and block_stack[-1][1]
            and content.endswith(",")
            and len(leading) > len(block_stack[-1][0])
        )
        if had_trailing_comma:
            content = content[:-1].rstrip()

        # v5.48.0 Te.3.D.3: rewrite single-line statement-block braces
        # to colon form (``if x { return y }`` -> ``if x: return y``).
        # Runs after comma-strip so we operate on the bare content.
        migrated = _migrate_one_line_stmt_block(leading, content)
        if migrated is not None:
            if had_trailing_comma:
                migrated = migrated + ","
            out.append(migrated)
            continue

        out.append(f"{leading}{content}")

    rewritten = "\n".join(out) + ("\n" if out else "")
    # Final pass through ``format_source`` to collapse any extra blank
    # lines that resulted from dropped ``}`` lines.
    return format_source(rewritten)


def to_braces(source: str) -> str:
    """Rewrite colon-block syntax to brace-block syntax.

    Thin wrapper around the parser's ``_indent_to_braces`` +
    ``_rewrite_arm_stmt_shorthand`` preprocessors, then
    ``format_source`` for canonical whitespace. Idempotent on
    already-brace-style source (the preprocessors' fast paths
    return unchanged input).

    v5.50.0 Te.3.E.3: also runs ``_rewrite_arm_stmt_shorthand`` so
    arm-body sugar (``Pat => return X``, ``Pat => let X = []; return X``)
    is restored to brace form on round-trip.
    """
    from mapanare.parser import _indent_to_braces, _rewrite_arm_stmt_shorthand

    return format_source(_rewrite_arm_stmt_shorthand(_indent_to_braces(source)))


# ---------------------------------------------------------------------------
# v5.24.1 Wd.2 — markdown-aware brace-to-colon rewriter for SPEC / guide docs.
#
# ``to_terse_markdown`` walks a markdown source line by line, locates
# fenced `````mn ... ````` code blocks, and
# runs ``to_terse`` on each fence body. Other code-block languages
# (`````bash``, `````toml``, etc.) and prose
# are passed through verbatim. A ``<!-- preserve-brace -->`` HTML comment
# on the line immediately before an ``mn`` fence (skipping blank lines)
# opts that fence out — the brace shape is kept verbatim, useful for
# historical-artifact examples (e.g. a section that intentionally
# demonstrates the brace shape).
#
# The rewriter is conservative: any fence body that round-trips
# unchanged through ``to_terse`` (already colon-style, or shapes
# ``to_terse`` cannot prove safe to rewrite) lands in the output
# unchanged. The function is idempotent.
# ---------------------------------------------------------------------------

_MD_PRESERVE_MARKER = "<!-- preserve-brace -->"


def to_terse_markdown(source: str) -> str:
    """Rewrite `````mn`` fences in a markdown document to
    colon-block syntax.

    Honors a ``<!-- preserve-brace -->`` HTML comment immediately above
    the opening fence (blank lines between the marker and the fence are
    allowed) as an opt-out marker — the marked fence's body is kept
    verbatim. Other code-block languages and prose pass through
    unchanged. Idempotent.
    """
    if not source:
        return source

    lines = source.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped == "```mn":
            # Look back to detect a preserve-brace marker, allowing
            # any number of blank lines between the marker and the fence.
            preserve = False
            j = len(out) - 1
            while j >= 0 and out[j].strip() == "":
                j -= 1
            if j >= 0 and out[j].strip() == _MD_PRESERVE_MARKER:
                preserve = True

            # Capture fence body until the closing fence.
            body: list[str] = []
            i += 1
            while i < n and lines[i].strip() != "```":
                body.append(lines[i])
                i += 1
            # Closing fence (if present)
            closer = lines[i] if i < n else "```"
            if i < n:
                i += 1

            out.append(line)
            if preserve or not body:
                out.extend(body)
            else:
                rewritten = to_terse("\n".join(body))
                # ``to_terse`` always appends a trailing newline; split
                # produces a trailing empty element we must drop.
                pieces = rewritten.split("\n")
                if pieces and pieces[-1] == "":
                    pieces.pop()
                out.extend(pieces)
            out.append(closer)
            continue

        # Non-mn fences: pass the body through unchanged so we don't
        # mistake their content for nested `````mn``
        # markers. Detect any `````<lang>`` opener.
        if stripped.startswith("```") and stripped != "```":
            out.append(line)
            i += 1
            while i < n and lines[i].strip() != "```":
                out.append(lines[i])
                i += 1
            if i < n:
                out.append(lines[i])
                i += 1
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


# ---------------------------------------------------------------------------
# v5.27.0 Mc.8 — long-line detection (detect-only).
#
# Mapanare's grammar is strictly single-line for all expressions: newlines
# are not implicit continuations inside parens / brackets / braces. The
# parser rejects every wrap shape — split arg lists, multi-line method
# chains, multi-line operator chains. ``wrap_lines``-style automatic
# rewriting therefore cannot satisfy ``Mc.2``'s AST-preservation
# invariant under the v5.27.0 grammar.
#
# v5.27.0 closes Mc.8 honestly by shipping a *detector* — ``find_long_lines``
# reports overlong lines without modifying source. The CLI surfaces them
# as warnings (or failures under ``--check``); users can then refactor
# manually. A future release that also adds newline-tolerant grammar
# inside grouping delimiters can revisit auto-wrapping.
# ---------------------------------------------------------------------------


def find_long_lines(source: str, max_length: int = 100) -> list[tuple[int, int]]:
    """Return ``[(line_no, length), ...]`` for lines exceeding ``max_length``.

    Line numbers are 1-based. Trailing newline is excluded from the
    length count. Strict inequality: a line of exactly ``max_length``
    visible characters is NOT flagged.

    Pure function. No I/O. Source-modification-free, so trivially
    AST-preserving.
    """
    if max_length <= 0:
        return []
    out: list[tuple[int, int]] = []
    for i, line in enumerate(source.split("\n"), start=1):
        # ``split("\n")`` drops the trailing newline already; what
        # remains is the visible content. Tabs are counted as one
        # character — ``format_source`` normalizes leading tabs to
        # 4 spaces, so by the time the detector runs (after fmt),
        # the count is canonical.
        if len(line) > max_length:
            out.append((i, len(line)))
    return out


# ---------------------------------------------------------------------------
# v5.27.0 Mc.9 — import sort.
#
# Sorts contiguous ``import ...`` blocks alphabetically. The block
# boundary is any non-import / non-comment line — including a blank
# line — so the user's existing grouping (e.g. stdlib / third-party /
# local separated by blanks) is preserved as the de-facto group
# structure: each group sorts independently.
#
# Comments inside an import block (``// keep this first``) split the
# block into sub-blocks; each sub-block sorts independently. This is
# the conservative choice — a free-floating comment adjacent to a
# specific import would otherwise drift to a different import after
# sorting, which is a silent semantics change for human readers.
#
# AST preservation: Mapanare's import resolution is order-insensitive
# for the shapes the corpus uses (``import path::sub``). The sort
# preserves the multiset of imports; ``parse(src)`` and
# ``parse(sort_imports(src))`` produce ASTs that differ only in
# ``ImportDecl`` declaration order — verified by
# ``tests/test_format_imports.py`` over the corpus.
# ---------------------------------------------------------------------------


def _is_import_line(line: str) -> bool:
    """Return True iff ``line`` is a top-level ``import`` statement.

    Recognizes the ``KW_IMPORT NAME (DOUBLE_COLON NAME)*`` shape and the
    optional ``{ items }`` selector tail. Whitespace-tolerant: a line
    with leading spaces/tabs is NOT an import (only top-level imports
    are sorted; nested ``import`` inside a block is not a thing in
    Mapanare today, but the indentation guard makes the check robust
    if the grammar grows there).
    """
    stripped = line.lstrip()
    if stripped != line:
        return False  # indented — not a top-level import
    return stripped.startswith("import ")


def sort_imports(source: str) -> str:
    """Sort contiguous top-level ``import`` blocks alphabetically.

    Block boundaries are any non-import line (blank, comment, or other
    statement). Each contiguous run of imports is sorted in place;
    blank-line groupings between runs are preserved. Idempotent.

    AST-preserving up to ``ImportDecl`` declaration order — Mapanare's
    import resolution does not depend on source order for the shapes
    the corpus uses.
    """
    if not source:
        return source

    lines = source.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        if _is_import_line(lines[i]):
            # Collect contiguous imports — stop at any non-import line.
            block_start = i
            while i < n and _is_import_line(lines[i]):
                i += 1
            # Stable sort by full line text (case-sensitive ASCII order
            # — matches how the corpus is already grouped).
            block = sorted(lines[block_start:i])
            out.extend(block)
        else:
            out.append(lines[i])
            i += 1

    return "\n".join(out)
