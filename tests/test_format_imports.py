"""Tests for ``mapanare.format.sort_imports`` — v5.27.0 (Mc.9).

Sorts contiguous top-level ``import`` blocks alphabetically. Block
boundaries are any non-import line (blank, comment, or other
statement), so the user's existing blank-line groupings (e.g.
stdlib / third-party / local) function as the de-facto group
structure: each group sorts independently.

Idempotent. AST-preserving up to ``ImportDecl`` declaration order
— Mapanare's import resolution does not depend on source order
for the shapes the corpus uses.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from mapanare.ast_nodes import Span
from mapanare.format import sort_imports
from mapanare.parser import ParseError, parse

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _normalize_no_order(node: Any) -> Any:
    """Strip ``span`` fields. Used to compare ASTs without source-position
    drift after a sort."""
    if isinstance(node, Span):
        return None
    if isinstance(node, list):
        return [_normalize_no_order(x) for x in node]
    if isinstance(node, tuple):
        return tuple(_normalize_no_order(x) for x in node)
    if is_dataclass(node):
        out: dict[str, Any] = {}
        for f in fields(node):
            if f.name == "span":
                continue
            out[f.name] = _normalize_no_order(getattr(node, f.name))
        return (type(node).__name__, out)
    return node


def _import_multiset(src: str) -> tuple[Any, ...]:
    """Return a sorted tuple of (normalized) ``ImportDecl`` nodes from
    ``src`` so two parses can be compared modulo declaration order.
    """
    program = parse(src)
    decls = [d for d in program.definitions if type(d).__name__ == "ImportDecl"]
    norm = [_normalize_no_order(d) for d in decls]
    # Sort by repr — deterministic equivalence-class signature.
    return tuple(sorted(norm, key=repr))


class TestSortImportsRules:
    def test_empty_source_passthrough(self) -> None:
        assert sort_imports("") == ""

    def test_no_imports_passthrough(self) -> None:
        src = 'fn main() {\n    print("hi")\n}\n'
        assert sort_imports(src) == src

    def test_single_import_passthrough(self) -> None:
        src = "import self::ast\n\nfn main() {}\n"
        assert sort_imports(src) == src

    def test_simple_block_sorted(self) -> None:
        src = "import self::mir\nimport self::ast\nimport self::lower\n"
        out = sort_imports(src)
        assert out == "import self::ast\nimport self::lower\nimport self::mir\n"

    def test_sort_is_idempotent(self) -> None:
        src = "import self::mir\nimport self::ast\nimport self::lower\n"
        once = sort_imports(src)
        twice = sort_imports(once)
        assert once == twice

    def test_already_sorted_unchanged(self) -> None:
        src = "import a::b\nimport c::d\nimport e::f\n"
        assert sort_imports(src) == src

    def test_blank_line_separator_creates_two_groups(self) -> None:
        # Two blocks, each sorted independently, blank line preserved.
        src = "import b::y\n" "import a::x\n" "\n" "import d::w\n" "import c::v\n"
        out = sort_imports(src)
        assert out == ("import a::x\n" "import b::y\n" "\n" "import c::v\n" "import d::w\n")

    def test_imports_then_code_only_imports_sort(self) -> None:
        src = "import b::y\n" "import a::x\n" "\n" "fn main() {\n" '    print("hi")\n' "}\n"
        out = sort_imports(src)
        assert out.startswith("import a::x\nimport b::y\n")
        assert "fn main()" in out

    def test_comment_inside_block_splits_subblocks(self) -> None:
        # A comment between two imports is a block boundary —
        # neither side is reordered across the comment.
        src = (
            "import b::y\n"
            "import a::x\n"
            "// keep self imports below\n"
            "import d::w\n"
            "import c::v\n"
        )
        out = sort_imports(src)
        assert out == (
            "import a::x\n"
            "import b::y\n"
            "// keep self imports below\n"
            "import c::v\n"
            "import d::w\n"
        )

    def test_indented_import_not_sorted(self) -> None:
        # Only top-level (column-0) imports are considered. Indented
        # ``import`` (e.g. inside a hypothetical block) is skipped.
        src = "    import b::y\n    import a::x\n"
        # The function does not sort indented lines; they pass through
        # as a non-import block.
        out = sort_imports(src)
        assert out == src

    def test_import_with_selectors_sorted_textually(self) -> None:
        src = "import b::y { foo, bar }\nimport a::x\n"
        out = sort_imports(src)
        assert out == "import a::x\nimport b::y { foo, bar }\n"

    def test_preserves_trailing_newline(self) -> None:
        src = "import b\nimport a\n"
        assert sort_imports(src).endswith("\n")

    def test_no_trailing_newline_passes_through(self) -> None:
        # If the input lacks a trailing newline, the output also lacks one.
        # (``format_source`` adds the newline; ``sort_imports`` does not.)
        src = "import b\nimport a"
        out = sort_imports(src)
        assert out == "import a\nimport b"


class TestSortImportsAstPreserving:
    """The sort must preserve the multiset of import declarations —
    Mapanare's import resolution is order-insensitive at the granularity
    the corpus uses (``import path::sub``)."""

    def test_ast_multiset_preserved_simple(self) -> None:
        src = "import self::mir\nimport self::ast\nimport self::lower\n\nfn main() {}\n"
        sorted_src = sort_imports(src)
        assert _import_multiset(src) == _import_multiset(sorted_src)

    def test_ast_multiset_preserved_with_selectors(self) -> None:
        src = "import b::y { foo }\nimport a::x\n\nfn main() {}\n"
        sorted_src = sort_imports(src)
        assert _import_multiset(src) == _import_multiset(sorted_src)


class TestFmtCliSortImports:
    """End-to-end CLI wiring for ``mapanare fmt --sort-imports``."""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "mapanare.cli", *args],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )

    def test_sort_imports_writes_in_place(self, tmp_path: Path) -> None:
        f = tmp_path / "imports.mn"
        f.write_text(
            "import self::mir\n" "import self::ast\n" "\n" "fn main() {\n" '    print("hi")\n' "}\n"
        )
        result = self._run_cli("fmt", "--sort-imports", "--keep-braces", str(f))
        assert result.returncode == 0
        text = f.read_text()
        # ``ast`` precedes ``mir`` after sort.
        ast_pos = text.index("import self::ast")
        mir_pos = text.index("import self::mir")
        assert ast_pos < mir_pos

    def test_sort_imports_idempotent_via_cli(self, tmp_path: Path) -> None:
        f = tmp_path / "imports.mn"
        f.write_text("import self::mir\n" "import self::ast\n" "\n" "fn main() {}\n")
        self._run_cli("fmt", "--sort-imports", "--keep-braces", str(f))
        first = f.read_text()
        self._run_cli("fmt", "--sort-imports", "--keep-braces", str(f))
        second = f.read_text()
        assert first == second

    def test_sort_imports_check_mode_flags_unsorted(self, tmp_path: Path) -> None:
        f = tmp_path / "imports.mn"
        f.write_text("import self::mir\n" "import self::ast\n" "\n" "fn main() {}\n")
        result = self._run_cli("fmt", "--check", "--sort-imports", "--keep-braces", str(f))
        assert result.returncode == 1


@pytest.mark.parametrize(
    "src",
    [
        # Empty
        "",
        # No imports
        'fn main() {\n    print("hi")\n}\n',
        # Already sorted
        "import a::x\nimport b::y\n",
        # Reverse-sorted
        "import b::y\nimport a::x\n",
        # Three groups separated by blanks
        "import c\nimport a\n\nimport f\nimport d\n\nimport z\nimport y\n",
    ],
)
def test_sort_imports_idempotent_fixtures(src: str) -> None:
    once = sort_imports(src)
    twice = sort_imports(once)
    assert once == twice


def test_sort_imports_preserves_self_main_ast() -> None:
    """Sort applied to ``mapanare/self/main.mn`` preserves the import
    multiset under the parser. This is the load-bearing corpus check —
    if any real-world import shape divergence exists, this test catches
    it."""
    main_path = _REPO_ROOT / "mapanare" / "self" / "main.mn"
    src = main_path.read_text(encoding="utf-8")
    # Suppress the brace-deprecation warning during the parse round-trip
    # so test stderr stays clean.
    import os

    prior = os.environ.get("MAPANARE_NO_BRACE_WARNING")
    os.environ["MAPANARE_NO_BRACE_WARNING"] = "1"
    try:
        try:
            before = _import_multiset(src)
        except ParseError:
            pytest.skip("main.mn does not parse on HEAD — skipping AST check")
        sorted_src = sort_imports(src)
        after = _import_multiset(sorted_src)
        assert before == after
    finally:
        if prior is None:
            os.environ.pop("MAPANARE_NO_BRACE_WARNING", None)
        else:
            os.environ["MAPANARE_NO_BRACE_WARNING"] = prior
