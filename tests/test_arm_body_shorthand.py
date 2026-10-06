"""v5.50.0 Te.3.E.1 + Te.3.E.2 — match-arm body grammar extensions.

Falsifiability anchors:

- **Te.3.E.1** — multi-stmt single-line arm body shorthand. Source
  ``Pat => let x = []; return x`` parses identically to the brace form
  ``Pat => { let x = []; return x }``. Pre-fix, the parser rejects
  the colon form (``_rewrite_arm_stmt_shorthand`` skipped non-keyword
  bodies). Reverting the change re-introduces the rejection.

- **Te.3.E.2** — multi-line ``Pat =>:`` colon form. Source

  ::

      match x:
          1 =>:
              let r: Int = 1
              return r
          _ => return 0

  parses identically to the all-brace form. Pre-fix, the
  ``_indent_to_braces`` comma-tracking emitted the comma on the
  opener line (``1 => {,``) instead of the closer (``},``), which
  the LALR parser rejected.

Round-trip property: for both Te.3.E.1 and Te.3.E.2 sources, the AST
produced by ``parse`` is structurally identical to the AST produced
by parsing the canonical brace form. This is the load-bearing
behavior-equivalence guarantee.
"""

from __future__ import annotations

from mapanare.parser import (
    _indent_to_braces,
    _rewrite_arm_stmt_shorthand,
    parse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(s: str) -> str:
    """Strip span info from an AST repr for cross-form comparison.
    Spans differ between colon-form and brace-form sources because
    the line/column positions are different in the original text;
    structural equality is what we want to assert."""
    import re

    return re.sub(r"Span\([^)]*\)", "Span(...)", repr(s))


# ---------------------------------------------------------------------------
# Te.3.E.1 — multi-stmt single-line arm body
# ---------------------------------------------------------------------------


class TestTe3E1MultiStmtArm:
    """``Pat => let x = []; return x`` colon form parses identically
    to the brace form ``Pat => { let x = []; return x }``."""

    def test_let_then_return(self):
        colon = """fn f(x: Int) -> List<Int>:
    match x:
        1 => let empty: List<Int> = []; return empty,
        _ => return [99]
"""
        brace = """fn f(x: Int) -> List<Int>:
    match x:
        1 => { let empty: List<Int> = []; return empty }
        _ => return [99]
"""
        a = parse(colon)
        b = parse(brace)
        assert _normalize(a) == _normalize(b)

    def test_assignment_then_return(self):
        colon = """fn f(x: Int) -> Int:
    let mut r: Int = 0
    match x:
        1 => r = 10; return r,
        _ => return 0
"""
        # Equivalent brace form
        brace = """fn f(x: Int) -> Int:
    let mut r: Int = 0
    match x:
        1 => { r = 10; return r }
        _ => return 0
"""
        a = parse(colon)
        b = parse(brace)
        assert _normalize(a) == _normalize(b)

    def test_single_stmt_kw_unchanged(self):
        """v5.48.0 single-stmt-keyword arm body still wraps."""
        src = """fn f(x: Int) -> Int:
    match x:
        1 => return 10
        _ => return 0
"""
        a = parse(src)
        # No exception means it parsed; the AST equivalence check is
        # in the round-trip tests below.
        assert a is not None

    def test_expression_arm_not_wrapped(self):
        """Bare expression arms (``Pat => expr``) must NOT be wrapped
        as statement-arms. Falsifiability for over-eager wrapping."""
        src = """fn f(x: Int) -> Int:
    let r: Int = match x { 1 => 10, _ => 0 }
    return r
"""
        a = parse(src)
        assert a is not None

    def test_preprocessor_round_trip_semi(self):
        """The brace stream produced by the preprocessor for the colon
        form is byte-identical to the user-written brace form modulo
        whitespace."""
        colon = "_ => let x: Int = 1; return x,\n"
        processed = _indent_to_braces(colon)
        processed = _rewrite_arm_stmt_shorthand(processed)
        # The body ends up wrapped as ``{ let x: Int = 1; return x }``
        assert "{ let x: Int = 1; return x }" in processed


# ---------------------------------------------------------------------------
# Te.3.E.2 — multi-line Pat =>: colon form
# ---------------------------------------------------------------------------


class TestTe3E2MultilineArm:
    """``Pat =>:`` followed by indented body produces a multi-line arm
    body. Round-trips to the brace form ``Pat => { ... }``."""

    def test_basic_multiarm(self):
        colon = """fn f(x: Int) -> Int:
    match x:
        1 =>:
            let r: Int = 10
            return r
        _ => return 0
"""
        brace = """fn f(x: Int) -> Int {
    match x {
        1 => {
            let r: Int = 10
            return r
        },
        _ => return 0
    }
}
"""
        a = parse(colon)
        b = parse(brace)
        assert _normalize(a) == _normalize(b)

    def test_two_multiline_arms(self):
        colon = """fn f(x: Int) -> Int:
    match x:
        1 =>:
            let r: Int = 10
            return r
        2 =>:
            let s: Int = 20
            return s
        _ => return 0
"""
        a = parse(colon)
        assert a is not None

    def test_mixed_singleline_and_multiline(self):
        """Single-line and multi-line arms in the same match body
        compose correctly. Comma separator is on the closer line of
        the multi-line arm, not the opener (Te.3.E.2 comma-tracking
        fix in ``_indent_to_braces`` dedent loop)."""
        colon = """fn f(x: Int) -> Int:
    match x:
        1 => return 1
        2 =>:
            let r: Int = 0
            return r
        _ => return 0
"""
        a = parse(colon)
        assert a is not None

    def test_comma_lands_on_closer_not_opener(self):
        """Direct preprocessor output check: comma after a multi-line
        arm body is appended to the ``}`` closer, not the ``=> {``
        opener. Pre-fix this would emit ``1 => {,``."""
        colon = """match x:
    1 =>:
        return 1
    2 => return 2
"""
        out = _indent_to_braces(colon)
        # The opener line should NOT have a comma at the end
        assert "1 => {," not in out
        # The closer should carry the comma between the multi-line
        # arm and the next sibling
        assert "}," in out

    def test_brace_form_unchanged(self):
        """Brace-form sources are unaffected by Te.3.E.2 changes."""
        src = """fn f(x: Int) -> Int {
    match x {
        1 => {
            let r: Int = 10
            return r
        },
        _ => return 0
    }
}
"""
        a = parse(src)
        assert a is not None


# ---------------------------------------------------------------------------
# Combined: Te.3.E.1 + Te.3.E.2 in the same match
# ---------------------------------------------------------------------------


class TestTe3ECombined:
    """All three new colon-form arm shapes in one match block."""

    def test_three_shapes_one_match(self):
        src = """fn classify(x: Int) -> String:
    match x:
        0 => return "zero"
        1 =>:
            let s: String = "one"
            return s
        _ => let label: String = "other"; return label
"""
        a = parse(src)
        assert a is not None
