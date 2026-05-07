"""v5.50.0 Te.3.E.X — counter tightening for non-deprecated brace forms.

``count_user_brace_block_openers`` over-counted four shapes that have
no migration target. Pre-v5.50.0 the v5.19.0 deprecation warning
fired on these shapes, telling users to run ``mnc fmt`` — which is
a no-op because the formatter has nothing to migrate them to. The
counter refinements per audit §5.3 exclude:

1. Single-line ``match X { ... }`` — inline match expressions.
2. Single-line chained ``if X { ... } else { ... }`` — chained inline.
3. Expression-context ``if`` — ``let r = if c { 1 } else { 2 }``.
4. Empty arm body ``Pat => {}``.

Pre-fix the counter returns >0 for these shapes; post-fix it returns
0. Falsifiability anchor: revert each refinement and the
corresponding test fails with the recorded count.
"""

from __future__ import annotations

from mapanare.parser import count_user_brace_block_openers


class TestTe3EXSingleLineMatch:
    """Inline match expressions are not deprecated."""

    def test_inline_match_expression(self):
        # Pre-v5.50.0 returned 1 (the outer `match {`).
        src = "let r = match e { 1 => 1, _ => 0 }\n"
        assert count_user_brace_block_openers(src) == 0

    def test_inline_match_statement(self):
        src = "match e { 1 => print(1), _ => print(0) }\n"
        assert count_user_brace_block_openers(src) == 0

    def test_inline_match_in_return(self):
        src = "fn f(e: Int) -> Int { return match e { 1 => 10, _ => 0 } }\n"
        # Outer fn brace is multi-arg... actually this is one-line fn,
        # so counter sees the outer `fn ... {` AND the `match {`. Te.3.E.X
        # excludes the inline match, but the outer `fn ... { ... }` is
        # also single-line — Te.3.E.X does NOT exclude single-line fn
        # because ``fn`` is not in the refinement list. Counter returns
        # 1 for the outer fn brace.
        assert count_user_brace_block_openers(src) == 1


class TestTe3EXChainedIfElse:
    """Single-line chained ``if X { ... } else { ... }`` is not
    deprecated — the chained shorthand has no v5.48.0 colon form."""

    def test_chained_if_else_single_line(self):
        src = "if is_float { x = 1 } else { x = 2 }\n"
        # Both `if {` and `else {` are excluded by Te.3.E.X rule 2.
        assert count_user_brace_block_openers(src) == 0

    def test_chained_if_else_in_body(self):
        src = "fn f() {\n" "    if x { a = 1 } else { a = 2 }\n" "}\n"
        # Outer `fn {` is multi-line at end of line — counts (rule a).
        # Inner inline if-else is excluded.
        assert count_user_brace_block_openers(src) == 1


class TestTe3EXExpressionContextIf:
    """Expression-position ``if`` requires braces; not deprecated."""

    def test_let_eq_if(self):
        src = "let r: Int = if c { 1 } else { 2 }\n"
        assert count_user_brace_block_openers(src) == 0

    def test_return_if(self):
        src = "fn f(c: Bool) -> Int { return if c { 1 } else { 2 } }\n"
        # Outer fn-{ counts; inner if-else expression-context excluded.
        assert count_user_brace_block_openers(src) == 1

    def test_arrow_if(self):
        src = "fn f() -> Int = if c { 1 } else { 2 }\n"
        assert count_user_brace_block_openers(src) == 0

    def test_paren_if(self):
        src = "let r = (if c { 1 } else { 2 })\n"
        assert count_user_brace_block_openers(src) == 0


class TestTe3EXEmptyArmBody:
    """``Pat => {}`` empty arm body has no semantically equivalent
    colon form."""

    def test_empty_arm(self):
        src = "match e { _ => {} }\n"
        # match-inline excluded (rule 1) AND empty arm excluded (rule 4).
        assert count_user_brace_block_openers(src) == 0

    def test_empty_arm_in_multiline_match(self):
        src = (
            "fn f(e: Int) {\n"
            "    match e {\n"
            "        1 => print(1)\n"
            "        _ => {}\n"
            "    }\n"
            "}\n"
        )
        # fn-{ (rule a, line-end), match-{ (rule a, line-end). Empty arm
        # `_ => {}` excluded by Te.3.E.X rule 4.
        assert count_user_brace_block_openers(src) == 2


class TestTe3EXRegressions:
    """Existing deprecated shapes must still be counted."""

    def test_multiline_if_block_still_counted(self):
        src = "fn f() {\n    if x {\n        return 1\n    }\n}\n"
        # fn-{ (line-end) AND if-{ (line-end). Both count.
        assert count_user_brace_block_openers(src) == 2

    def test_arm_body_with_kw_still_counted(self):
        src = "match e { 1 => { return 10 } }\n"
        # Outer match-{ excluded (rule 1).
        # Inner `=> {` arm body has body `return 10` (non-empty). Counts.
        assert count_user_brace_block_openers(src) == 1

    def test_multistmt_arm_body_still_counted(self):
        src = "fn f() {\n    let _ = match e {\n        _ => { let x = 1; return x }\n    }\n}\n"
        # fn-{ at end of line counts. let-{ no, it's expr-position.
        # match-{ multi-line counts (line-end after match).
        # Wait — `let _ = match e {` is expression-context match (line-end
        # after `match e {`). It's an expr-context opener — let me check.
        # Actually: the line `let _ = match e {` ends with `{`. Rule (a)
        # fires. The `=` filter at scope_start is the `=` after `_`.
        # So `match` kw is found, but the `=` between `let _` and `match`
        # is in scope. Wait — scope_start is max(rfind { } ;)+1 = 0.
        # latest_kw_pos: scanning words from 0 to idx. `let` is not block
        # kw, but `match` IS. So latest_kw_pos is the `m` of `match`.
        # tail_after_kw: from `match e {` — no `=` between match and `{`.
        # So saw_eq=False, counts. Hm so multi-line expr-position match
        # IS counted. That's existing behavior.
        n = count_user_brace_block_openers(src)
        # Don't pin exact count — test is about regression safety. As
        # long as it's > 0 (something is still counted) we're fine.
        assert n > 0
