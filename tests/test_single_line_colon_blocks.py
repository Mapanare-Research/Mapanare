"""v5.48.0 Te.3.D — single-line colon block + match-arm shorthand tests.

Covers:

- ``if x: stmt`` / ``si x: da y`` / ``while`` / ``for`` / ``loop`` /
  ``do`` / ``fn name(): stmt`` / ``else: stmt`` / ``else if x: stmt``
  parse to the same AST as the equivalent ``<head> { stmt }`` brace
  form.
- ``Pat => return x`` / ``Pat => da y`` / ``Pat => break`` /
  ``Pat => sal`` / ``Pat => continue`` / ``Pat => sigue`` /
  ``Pat => pass`` parse to the same AST as ``Pat => { return x }``.
- Negative cases: ``struct Point: x: Int`` / ``enum Color: Red`` /
  ``match e: Pat => 1`` / ``let x: Int = 5`` are NOT misclassified.
- Expression-context braces (``let x = if cond { 1 } else { 2 }``,
  struct literals ``Foo {}``, empty maps ``#{}``) are not migrated.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

import pytest

from mapanare.ast_nodes import Block, PassStmt, Span
from mapanare.parser import (
    ParseError,
    _is_single_line_stmt_head,
    _rewrite_arm_stmt_shorthand,
    _split_inline_colon_body,
    parse,
)


def _norm(node: Any) -> Any:
    """Recursively strip ``span`` and treat a single-PassStmt body as
    an empty body (the brace-form can be empty; ``pass`` is the
    zero-statement filler)."""
    if isinstance(node, Span):
        return None
    if isinstance(node, list):
        return [_norm(x) for x in node]
    if isinstance(node, tuple):
        return tuple(_norm(x) for x in node)
    if isinstance(node, Block):
        stmts = [s for s in node.stmts if not isinstance(s, PassStmt)]
        return ("Block", _norm(stmts))
    if is_dataclass(node):
        out: dict[str, Any] = {}
        for f in fields(node):
            if f.name == "span":
                continue
            out[f.name] = _norm(getattr(node, f.name))
        return (type(node).__name__, out)
    return node


# ---------------------------------------------------------------------------
# Phase 1 — single-line colon blocks
# ---------------------------------------------------------------------------


class TestSplitInlineColonBody:
    def test_basic_split(self) -> None:
        assert _split_inline_colon_body("if x: return y") == ("if x", "return y")

    def test_strips_around(self) -> None:
        # ``_split_inline_colon_body`` only trims whitespace internal to
        # the split; the caller is responsible for the line's leading
        # indent. We pass already-stripped content here.
        assert _split_inline_colon_body("if  x  :   return  y  ") == ("if  x", "return  y  ")

    def test_skip_paren_colon(self) -> None:
        # `Map<String, Int>` doesn't have `:` but a generic with `:`?
        # Use a function call with annotation in it.
        assert _split_inline_colon_body("if call(a: 1): return y") == (
            "if call(a: 1)",
            "return y",
        )

    def test_skip_string_colon(self) -> None:
        assert _split_inline_colon_body('if x == "a:b": return y') == (
            'if x == "a:b"',
            "return y",
        )

    def test_skip_char_colon(self) -> None:
        assert _split_inline_colon_body("if x == ':': return y") == (
            "if x == ':'",
            "return y",
        )

    def test_no_top_colon(self) -> None:
        assert _split_inline_colon_body("return x") is None

    def test_empty_body_returns_none(self) -> None:
        # A line ending with `:` is a multi-line block opener, not a
        # single-line shape — caller never invokes us on these, but
        # double-check.
        assert _split_inline_colon_body("if x:") is None

    def test_line_comment_in_middle_bails(self) -> None:
        assert _split_inline_colon_body("if x // note : return y") is None


class TestIsSingleLineStmtHead:
    @pytest.mark.parametrize(
        "head",
        [
            "if x",
            "si x",
            "while ready()",
            "mien ready()",
            "for x in xs",
            "cada x in xs",
            "fn main()",
            "fn name() -> Int",
            "fn name<T>(x: T) -> T",
            "pub fn helper()",
            "async fn handler()",
            "extern fn foo()",
            "else",
            "else if x",
            "sino",
            "sino si x",
            "} else if x",
            "} sino si y",
        ],
    )
    def test_accepts_stmt_block_heads(self, head: str) -> None:
        assert _is_single_line_stmt_head(head)

    @pytest.mark.parametrize(
        "head",
        [
            "struct Point",
            "enum Color",
            "match e",
            "tipo Point",
            "modo Display",
            "way Display",
            "trait Display",
            "agent Worker",
            "impl Display",
            "let x",
            "x = 1",
            "print(x)",
            "Foo",
        ],
    )
    def test_rejects_non_stmt_heads(self, head: str) -> None:
        assert not _is_single_line_stmt_head(head)


class TestSingleLineColonBlocks:
    def _ast_eq(self, a: str, b: str) -> None:
        assert _norm(parse(a)) == _norm(parse(b))

    def test_if_return(self) -> None:
        self._ast_eq(
            "fn f() -> Int:\n    if x() <= 1: return 0\n    return 1\n",
            "fn f() -> Int:\n    if x() <= 1:\n        return 0\n    return 1\n",
        )

    def test_if_da_spanish(self) -> None:
        self._ast_eq(
            "fn f() -> Int:\n    si x() <= 1: da 0\n    da 1\n",
            "fn f() -> Int:\n    si x() <= 1:\n        da 0\n    da 1\n",
        )

    def test_while_break(self) -> None:
        self._ast_eq(
            "fn f():\n    while ready(): break\n",
            "fn f():\n    while ready():\n        break\n",
        )

    def test_for_print(self) -> None:
        self._ast_eq(
            "fn f():\n    for x in xs: print(x)\n",
            "fn f():\n    for x in xs:\n        print(x)\n",
        )

    def test_fn_zero_arg(self) -> None:
        self._ast_eq(
            'fn main(): print("hi")\n',
            'fn main():\n    print("hi")\n',
        )

    def test_fn_with_args(self) -> None:
        self._ast_eq(
            "fn double(x: Int) -> Int: return x + x\n",
            "fn double(x: Int) -> Int:\n    return x + x\n",
        )

    def test_else_single_line(self) -> None:
        self._ast_eq(
            "fn f() -> Int:\n    if x() > 0:\n        return 1\n    else: return 0\n",
            "fn f() -> Int:\n    if x() > 0:\n        return 1\n    else:\n        return 0\n",
        )

    def test_else_if_single_line_terminating(self) -> None:
        # Single-line `else if x: stmt` is supported as the terminator
        # of an if-chain. Further continuations (a trailing `else`) on
        # subsequent lines do NOT attach because the brace stream emits
        # the single-line as a fully-closed inline block. This is
        # documented in PRE_PHASE_AUDIT Decision A.
        self._ast_eq(
            "fn f() -> Int:\n    if x() > 0:\n        return 1\n    else if x() < 0: return -1\n    return 0\n",  # noqa: E501
            "fn f() -> Int:\n    if x() > 0:\n        return 1\n    else if x() < 0:\n        return -1\n    return 0\n",  # noqa: E501
        )

    def test_sino_single_line(self) -> None:
        self._ast_eq(
            "fn f() -> Int:\n    si x() > 0:\n        da 1\n    sino: da 0\n",
            "fn f() -> Int:\n    si x() > 0:\n        da 1\n    sino:\n        da 0\n",
        )


class TestSingleLineColonNegatives:
    """Shapes that must NOT migrate to single-line colon."""

    def test_let_with_type_annotation(self) -> None:
        # `let x: Int = 5` is a type-annotated let, not a single-line
        # block. The preprocessor must leave it alone.
        src = "fn f():\n    let x: Int = 5\n"
        # Should parse without error.
        parse(src)

    def test_struct_with_field_colon(self) -> None:
        # Multi-line struct stays multi-line; one-line `struct Point: x: Int`
        # is rejected.
        src_ml = "struct Point:\n    x: Int\n    y: Int\n"
        parse(src_ml)
        # Single-line form should fail to parse (or parse incorrectly).
        with pytest.raises(ParseError):
            parse("struct Point: x: Int\n")

    def test_match_with_arm_on_same_line(self) -> None:
        # `match e: Pat => 1` is rejected — match needs multi-line.
        with pytest.raises(ParseError):
            parse("fn f() -> Int: match e: IntLit(_) => 1\n")

    def test_expression_brace_passthrough(self) -> None:
        # `let x = if cond { 1 } else { 2 }` — if-expression in
        # expression context. Must not migrate.
        src = "fn f() -> Int:\n    let x = if true { 1 } else { 2 }\n    return x\n"
        parse(src)

    def test_struct_literal_passthrough(self) -> None:
        # Mapanare struct literals use `new` keyword.
        src = "struct Point:\n    x: Int\n    y: Int\nfn f() -> Point:\n    return new Point { x: 1, y: 2 }\n"  # noqa: E501
        parse(src)


# ---------------------------------------------------------------------------
# Phase 2 — match-arm statement shorthand
# ---------------------------------------------------------------------------


class TestArmStmtShorthand:
    def _ast_eq(self, a: str, b: str) -> None:
        assert _norm(parse(a)) == _norm(parse(b))

    def test_arm_return(self) -> None:
        self._ast_eq(
            'fn f(e: Int) -> String:\n    match e:\n        1 => return "one"\n        _ => return "other"\n',  # noqa: E501
            'fn f(e: Int) -> String:\n    match e:\n        1 => { return "one" }\n        _ => { return "other" }\n',  # noqa: E501
        )

    def test_arm_da(self) -> None:
        self._ast_eq(
            'fn f(e: Int) -> String:\n    match e:\n        1 => da "one"\n        _ => da "other"\n',  # noqa: E501
            'fn f(e: Int) -> String:\n    match e:\n        1 => { da "one" }\n        _ => { da "other" }\n',  # noqa: E501
        )

    def test_arm_break(self) -> None:
        # Arm body of break inside a while loop.
        self._ast_eq(
            "fn f():\n    while true:\n        match 0:\n            1 => break\n            _ => break\n",  # noqa: E501
            "fn f():\n    while true:\n        match 0:\n            1 => { break }\n            _ => { break }\n",  # noqa: E501
        )

    def test_arm_pass(self) -> None:
        self._ast_eq(
            "fn f(e: Int):\n    match e:\n        1 => pass\n        _ => pass\n",
            "fn f(e: Int):\n    match e:\n        1 => { pass }\n        _ => { pass }\n",
        )

    def test_arm_continue(self) -> None:
        self._ast_eq(
            "fn f():\n    while true:\n        match 0:\n            1 => continue\n            _ => break\n",  # noqa: E501
            "fn f():\n    while true:\n        match 0:\n            1 => { continue }\n            _ => { break }\n",  # noqa: E501
        )


class TestArmStmtRewriter:
    """Direct unit tests of ``_rewrite_arm_stmt_shorthand``."""

    def test_simple_return(self) -> None:
        line = "        IntLit(n) => return n,"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == "        IntLit(n) => { return n },"

    def test_simple_da(self) -> None:
        line = "        FloatLit(f) => da f,"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == "        FloatLit(f) => { da f },"

    def test_break_no_body(self) -> None:
        line = "        Pat => break"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == "        Pat => { break }"

    def test_pass(self) -> None:
        line = "        _ => pass,"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == "        _ => { pass },"

    def test_already_brace_unchanged(self) -> None:
        line = "        Pat => { return x }"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == line

    def test_expression_arm_unchanged(self) -> None:
        # Identifier `k` is not a stmt keyword.
        line = "        Pat => k = 1,"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == line

    def test_string_with_arrow_unchanged(self) -> None:
        # `=>` inside a string must not match.
        line = '        let s = "Pat => return x"'
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == line

    def test_word_continuation_not_matched(self) -> None:
        # `return_value` (identifier) should not match `return` keyword.
        line = "        Pat => return_value(x),"
        out = _rewrite_arm_stmt_shorthand(line)
        # Body extends to comma; result wraps the expression. But the
        # word `return_value` doesn't end at a word boundary after
        # `return` — the rewriter rejects it. So the line is unchanged.
        assert out == line

    def test_inline_match(self) -> None:
        # Inline match on one line.
        line = "    match e { Pat => return x }"
        out = _rewrite_arm_stmt_shorthand(line)
        assert "Pat => { return x }" in out

    def test_return_with_function_call(self) -> None:
        line = "        Pat => return f(a, b),"
        out = _rewrite_arm_stmt_shorthand(line)
        assert out == "        Pat => { return f(a, b) },"


# ---------------------------------------------------------------------------
# Idempotence — running parse twice (already-brace-form input) is stable
# ---------------------------------------------------------------------------


class TestIdempotence:
    def test_brace_form_unchanged(self) -> None:
        # Already-brace input: pre-existing `{...}` blocks parse the
        # same as before v5.48.0.
        src = (
            "fn f(e: Int) -> String {\n"
            '    if e <= 0 { return "neg" }\n'
            '    return "pos"\n'
            "}\n"
        )
        parse(src)


# ---------------------------------------------------------------------------
# Phase 3 — formatter migration (``to_terse``)
# ---------------------------------------------------------------------------


class TestFormatterMigration:
    """Verify ``to_terse`` migrates one-line braces to colon form."""

    def test_one_line_if_to_colon(self) -> None:
        from mapanare.format import to_terse

        src = "fn f(x: Int) -> Bool {\n    if x <= 16 { return false }\n    return true\n}\n"
        out = to_terse(src)
        assert "if x <= 16: return false" in out
        # No raw `{` / `}` blocks remaining for if/fn.
        assert "{ return false }" not in out

    def test_one_line_fn_to_colon(self) -> None:
        from mapanare.format import to_terse

        src = 'fn main() { print("hi") }\n'
        out = to_terse(src)
        assert 'fn main(): print("hi")' in out

    def test_one_line_si_da_to_colon(self) -> None:
        from mapanare.format import to_terse

        src = "fn f(x: Int) -> Bool {\n    si x <= 16 { da false }\n    da true\n}\n"
        out = to_terse(src)
        assert "si x <= 16: da false" in out

    def test_arm_return_to_compact(self) -> None:
        from mapanare.format import to_terse

        src = (
            "fn f(e: Int) -> String {\n"
            "    match e {\n"
            '        1 => { return "one" }\n'
            '        _ => { return "other" }\n'
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        assert '1 => return "one"' in out
        assert '_ => return "other"' in out
        # No brace-form arm bodies remaining.
        assert "=> { return" not in out

    def test_arm_da_to_compact(self) -> None:
        from mapanare.format import to_terse

        src = (
            "fn f(e: Int) -> String {\n"
            "    match e {\n"
            '        1 => { da "one" }\n'
            '        _ => { da "other" }\n'
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        assert '1 => da "one"' in out

    def test_struct_literal_not_migrated(self) -> None:
        from mapanare.format import to_terse

        src = "fn f() -> Point {\n    return new Point { x: 1, y: 2 }\n}\n"
        out = to_terse(src)
        # Struct literal `Point { x: 1, y: 2 }` must remain.
        assert "new Point { x: 1, y: 2 }" in out

    def test_empty_map_not_migrated(self) -> None:
        from mapanare.format import to_terse

        src = "fn f() {\n    let m: Map<String, Int> = #{}\n}\n"
        out = to_terse(src)
        assert "#{}" in out

    def test_idempotent_on_migrated(self) -> None:
        from mapanare.format import to_terse

        src = "fn f(x: Int) -> Bool {\n    if x <= 16 { return false }\n    return true\n}\n"
        once = to_terse(src)
        twice = to_terse(once)
        assert once == twice

    def test_ast_preserving_one_line_if(self) -> None:
        from mapanare.format import to_terse

        src = "fn f(x: Int) -> Bool {\n    if x <= 16 { return false }\n    return true\n}\n"
        out = to_terse(src)
        assert _norm(parse(src)) == _norm(parse(out))

    def test_ast_preserving_arm_return(self) -> None:
        from mapanare.format import to_terse

        src = (
            "fn f(e: Int) -> Int {\n"
            "    match e {\n"
            "        1 => { return 1 },\n"
            "        _ => { return 0 }\n"
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        assert _norm(parse(src)) == _norm(parse(out))

    def test_multi_stmt_arm_migrates_to_semicolon_form(self) -> None:
        # v5.48.0 Te.3.D kept ``;``-bearing arm bodies as brace form;
        # v5.50.0 Te.3.E.1 introduces the ``;``-separated colon form.
        from mapanare.format import to_terse

        src = (
            "fn f(e: Int) -> List<Int> {\n"
            "    match e {\n"
            "        _ => { let empty: List<Int> = []; return empty }\n"
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        assert "_ => let empty: List<Int> = []; return empty" in out

    def test_if_else_inline_kept_as_brace(self) -> None:
        from mapanare.format import to_terse

        src = "fn f() -> Int {\n    let x = if true { 1 } else { 2 }\n    return x\n}\n"
        out = to_terse(src)
        # Expression-context if must remain in brace form.
        assert "if true { 1 } else { 2 }" in out


# ---------------------------------------------------------------------------
# v5.53.0 Te.3.F — nested single-line stmt-block migration
# ---------------------------------------------------------------------------
#
# Falsifiability anchor — revert ``_migrate_one_line_stmt_block``'s
# Te.3.F recursive branch (the ``"{" in body_shadow or "}" in body_shadow``
# branch in mapanare/format.py that calls itself on the body) and the
# tests below FAIL with the recorded signature:
#
#   AssertionError: assert 'if ch >= "a": if ch <= "z": return true' in
#                          'fn f(ch: String) -> Bool:\n    if ch >= "a"
#                          { if ch <= "z" { return true } }\n    ...'
#
# i.e. ``to_terse`` returns the unchanged brace form because the
# line-363 ``{`` / ``}`` reject is what gated the recursion.
#
# Scope: Te.3.F.1 closes 7 of 11 first-party residuals — the pure-
# nested-2 shape (``if A { if B { stmt } }``). The 4 chained-if-else
# shapes (lexer.mn 267/276/285, lower.mn:4843) need a single-line
# ``else:`` continuation grammar rule that v5.48.0 does NOT support
# and is deferred to v6.0 PLAN. The deferral tests below assert
# those shapes are correctly LEFT alone (no half-migration that
# would crash the parser).


class TestNestedStmtBlock:
    """Nested pure-nested-2 ``if A { if B { stmt } }`` migration."""

    def test_pure_nested_2_lexer_191(self) -> None:
        from mapanare.format import to_terse

        src = (
            "fn is_alpha(ch: String) -> Bool:\n"
            '    if ch >= "a" { if ch <= "z" { return true } }\n'
            "    return false\n"
        )
        out = to_terse(src)
        assert 'if ch >= "a": if ch <= "z": return true' in out
        assert "{ if ch <= " not in out

    def test_pure_nested_2_round_trips_to_same_ast(self) -> None:
        # AST-equivalence check: the migrated colon form must parse
        # to the same AST as the original brace form.
        from mapanare.format import to_terse

        brace_src = (
            "fn f(ch: String) -> Bool:\n"
            '    if ch >= "a" { if ch <= "z" { return true } }\n'
            "    return false\n"
        )
        colon_src = to_terse(brace_src)
        assert _norm(parse(brace_src)) == _norm(parse(colon_src))

    def test_pure_nested_2_idempotent(self) -> None:
        from mapanare.format import to_terse

        src = (
            "fn f(ch: String) -> Bool:\n"
            '    if ch >= "a" { if ch <= "z" { return true } }\n'
            "    return false\n"
        )
        out1 = to_terse(src)
        out2 = to_terse(out1)
        assert out1 == out2

    def test_pure_nested_2_complex_body(self) -> None:
        # Inner body with function call + multi-arg
        from mapanare.format import to_terse

        src = (
            "fn scan_op() -> Int:\n"
            '    if ch == "&" { if ch1 == "&" { return new_token("AND", line, col) } }\n'
            "    return 0\n"
        )
        out = to_terse(src)
        assert 'if ch == "&": if ch1 == "&": return new_token("AND", line, col)' in out

    def test_pure_nested_2_with_assignment_inner(self) -> None:
        # Inner body is an assignment, not a return.
        from mapanare.format import to_terse

        src = (
            "fn f() -> Int:\n"
            '    if p < n { if source.char_at(p) == "\'" { p = p + 1 } }\n'
            "    return p\n"
        )
        out = to_terse(src)
        assert "if p < n: if source.char_at(p)" in out
        # No braces left over on that line
        for line in out.split("\n"):
            if "p = p + 1" in line:
                assert "{" not in line and "}" not in line

    def test_chained_if_else_deferred_left_alone(self) -> None:
        # 4 deferred shapes — to_terse must NOT half-migrate them
        # (would produce un-parseable output). The body has chained
        # `else { ... }` which the v5.48.0 grammar doesn't accept in
        # colon form.
        from mapanare.format import to_terse

        # lower.mn:4843 shape — single-arm outer + if-else inner
        src = (
            "fn f(b: Bool) -> String:\n"
            '    if true { if b { return "T" } else { return "F" } }\n'
            '    return ""\n'
        )
        out = to_terse(src)
        # Body has chained-if-else; migration must reject. The line
        # stays unchanged.
        assert "if true { if b { return" in out

    def test_chained_in_else_branch_deferred(self) -> None:
        # lexer.mn:267 shape — outer if-else with nested-in-else
        from mapanare.format import to_terse

        src = (
            "fn f(hc: String) -> String:\n"
            '    if hc == "0" { return "Z" } else { if hc != "_" { return "X" } }\n'
            '    return ""\n'
        )
        out = to_terse(src)
        # Outer is chained-if-else (tail.strip() != ""), so outer
        # rejects via the existing tail check. Line unchanged.
        assert "if hc == " in out
        # Crucially: no half-migration to ``if hc == "0": return "Z" else: ...``
        assert ': return "Z" else' not in out
