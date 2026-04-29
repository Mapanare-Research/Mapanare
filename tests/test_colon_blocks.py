"""v5.14.0 Te.1 — colon-block syntax cross-style validation.

For every parseable .mn file in ``tests/golden/``, assert that
``to_terse(brace_src)`` and ``to_braces(to_terse(brace_src))``
parse to ASTs equivalent to the original (modulo span info and the
no-op ``PassStmt`` inserted for previously-empty blocks).

Also unit-tests the rewriter rules in isolation.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from mapanare.ast_nodes import Block, PassStmt, Span
from mapanare.format import format_source, to_braces, to_terse
from mapanare.parser import ParseError, parse

GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN_FILES = sorted(GOLDEN_DIR.glob("*.mn"))


def _normalize(node: Any) -> Any:
    """Recursively strip ``span`` fields and treat a single-``PassStmt``
    body as equivalent to an empty body. Used to compare ASTs across
    surface-syntax rewrites where line/column shift and ``fn empty() {}``
    expands to ``fn empty(): pass``.
    """
    if isinstance(node, Span):
        return None
    if isinstance(node, list):
        return [_normalize(x) for x in node]
    if isinstance(node, tuple):
        return tuple(_normalize(x) for x in node)
    if isinstance(node, Block):
        # Collapse a body of [PassStmt] to [] for cross-style equivalence.
        stmts = [s for s in node.stmts if not isinstance(s, PassStmt)]
        return ("Block", _normalize(stmts))
    if is_dataclass(node):
        out: dict[str, Any] = {}
        for f in fields(node):
            if f.name == "span":
                continue
            out[f.name] = _normalize(getattr(node, f.name))
        return (type(node).__name__, out)
    return node


def _parseable(src: str) -> bool:
    try:
        parse(src)
        return True
    except ParseError:
        return False


# ---------------------------------------------------------------------------
# Unit tests — rewriter rules in isolation
# ---------------------------------------------------------------------------


class TestToTerseRules:
    def test_simple_fn(self) -> None:
        src = 'fn main() {\n    print("hi")\n}\n'
        out = to_terse(src)
        assert "fn main():" in out
        assert "{" not in out
        assert "}" not in out

    def test_if_else_chain(self) -> None:
        src = (
            "fn f() {\n"
            "    if true {\n"
            '        print("a")\n'
            "    } else if false {\n"
            '        print("b")\n'
            "    } else {\n"
            '        print("c")\n'
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        assert "if true:" in out
        assert "else if false:" in out
        assert "else:" in out
        assert "{" not in out

    def test_struct_strips_commas(self) -> None:
        src = "struct Point {\n    x: int,\n    y: int,\n}\n"
        out = to_terse(src)
        assert "x: int" in out and "x: int," not in out
        assert "y: int" in out and "y: int," not in out

    def test_enum_strips_commas(self) -> None:
        src = "enum Shape {\n    Circle,\n    Square,\n}\n"
        out = to_terse(src)
        assert "Circle\n" in out
        assert "Square\n" in out
        assert "Square," not in out

    def test_empty_fn_expands_to_pass(self) -> None:
        src = "fn empty() {}\n"
        out = to_terse(src)
        assert "fn empty():" in out
        assert "pass" in out

    def test_idempotent(self) -> None:
        src = "fn f() {\n    if x {\n        return 1\n    }\n}\n"
        once = to_terse(src)
        twice = to_terse(once)
        assert once == twice

    def test_brace_only_passthrough_on_already_terse(self) -> None:
        src = "fn f():\n    pass\n"
        out = to_terse(src)
        assert out == format_source(src)

    # v5.17.0 Sh.A.1: regression — match arms must not be rewritten to
    # `=>:`, which is invalid syntax. Multi-line arms keep braces;
    # empty arms `=> {}` keep braces. Matches that contain any
    # multi-line arm body stay entirely in brace form because the
    # `_indent_to_braces` preprocessor cannot track brace nesting
    # inside match bodies.
    def test_to_terse_preserves_multiline_match_arm(self) -> None:
        src = (
            "fn f(d: Definition) -> Bool {\n"
            "    match d {\n"
            "        FnDef(fd) => {\n"
            '            if fd.name == "main" {\n'
            "                return true\n"
            "            }\n"
            "        },\n"
            "        _ => {}\n"
            "    }\n"
            "    return false\n"
            "}\n"
        )
        out = to_terse(src)
        # Match block stayed in brace form (entire match was multi-line)
        assert "match d {" in out
        assert "FnDef(fd) => {" in out
        # The invalid `=>:` form must NEVER appear
        assert "=>:" not in out
        # Round-trips to a parseable AST.
        from mapanare.parser import parse

        parse(out)

    def test_to_terse_preserves_empty_match_arm(self) -> None:
        src = (
            "fn f(c: Color) -> Int {\n"
            "    match c {\n"
            "        Red => { return 1 },\n"
            "        Green => { return 2 },\n"
            "        _ => {}\n"
            "    }\n"
            "    return 0\n"
            "}\n"
        )
        out = to_terse(src)
        # Match converts to colon form (only single-line arms).
        assert "match c:" in out
        # Empty arm `=> {}` retained verbatim — no `=>:` corruption.
        assert "=>:" not in out
        assert "_ => {}" in out
        from mapanare.parser import parse

        parse(out)

    def test_to_terse_preserves_if_expression(self) -> None:
        # `let x = if cond { ... } else { ... }` is an expression
        # context — braces are part of the if-expr grammar and must
        # not be rewritten to colons.
        src = (
            "fn f(b: Bool) -> Int {\n"
            "    let x: Int = if b {\n"
            "        1\n"
            "    } else {\n"
            "        2\n"
            "    }\n"
            "    return x\n"
            "}\n"
        )
        out = to_terse(src)
        assert "let x: Int = if b {" in out
        assert "} else {" in out
        from mapanare.parser import parse

        parse(out)

    def test_to_terse_multi_level_else_dedent(self) -> None:
        # Multi-level dedent on `else:` (the round-trip exercise that
        # forced the v5.17.0 `_indent_to_braces` continuation fix).
        # Both `to_terse` output and round-trip via parse must work.
        src = (
            "fn f(a: Bool, b: Bool) -> Int {\n"
            "    if a {\n"
            "        if b {\n"
            "            return 1\n"
            "        } else {\n"
            "            return 2\n"
            "        }\n"
            "    } else {\n"
            "        return 3\n"
            "    }\n"
            "}\n"
        )
        out = to_terse(src)
        from mapanare.parser import parse

        parse(out)


class TestToBracesRules:
    def test_simple_fn(self) -> None:
        src = 'fn main():\n    print("hi")\n'
        out = to_braces(src)
        assert "fn main() {" in out
        assert out.rstrip().endswith("}")

    def test_struct(self) -> None:
        src = "struct Point:\n    x: int\n    y: int\n"
        out = to_braces(src)
        assert "struct Point {" in out
        # No trailing comma on the last field is acceptable
        assert "x: int," in out

    def test_idempotent_on_braces(self) -> None:
        src = "fn f() {\n    return 1\n}\n"
        out = to_braces(src)
        assert out == format_source(src)


# ---------------------------------------------------------------------------
# Cross-style validation across the golden corpus
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=lambda p: p.name)
class TestGoldenCrossStyle:
    def test_to_terse_idempotent(self, path: Path) -> None:
        src = path.read_text(encoding="utf-8")
        if not _parseable(src):
            pytest.skip("source does not parse on HEAD; rewriter not applicable")
        once = to_terse(src)
        twice = to_terse(once)
        assert twice == once, f"to_terse not idempotent on {path.name}"

    def test_to_terse_ast_equivalent(self, path: Path) -> None:
        src = path.read_text(encoding="utf-8")
        if not _parseable(src):
            pytest.skip("source does not parse on HEAD; rewriter not applicable")
        terse = to_terse(src)
        try:
            ast_terse = parse(terse)
        except ParseError as e:
            pytest.fail(f"to_terse output does not parse: {e}\n--- output ---\n{terse}")
        ast_orig = parse(src)
        assert _normalize(ast_orig) == _normalize(
            ast_terse
        ), f"AST diverged after to_terse on {path.name}"

    def test_round_trip_ast_equivalent(self, path: Path) -> None:
        src = path.read_text(encoding="utf-8")
        if not _parseable(src):
            pytest.skip("source does not parse on HEAD; rewriter not applicable")
        round_tripped = to_braces(to_terse(src))
        try:
            ast_rt = parse(round_tripped)
        except ParseError as e:
            pytest.fail(f"round-trip output does not parse: {e}")
        ast_orig = parse(src)
        assert _normalize(ast_orig) == _normalize(
            ast_rt
        ), f"AST diverged after to_braces(to_terse(...)) on {path.name}"
