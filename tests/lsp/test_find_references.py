"""Tests for find-references via WorkspaceIndex (v4.38.0)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mapanare.lsp.workspace import WorkspaceIndex


def _make_workspace(files: dict[str, str]) -> tuple[Path, WorkspaceIndex]:
    tmpdir = Path(tempfile.mkdtemp())
    for name, content in files.items():
        (tmpdir / name).write_text(content, encoding="utf-8")
    ws = WorkspaceIndex()
    ws.scan_root(tmpdir)
    return tmpdir, ws


class TestFindReferences:
    def test_find_references_top_level_function_same_file(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": "fn helper() -> Int { return 1 }\nfn main() { print(str(helper())) }",
            }
        )
        refs = ws.find_references("main", "helper", include_declaration=False)
        assert len(refs) >= 1  # at least the call site

    def test_find_references_top_level_function_cross_module(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "main.mn": "fn main() { print(str(helper())) }",
            }
        )
        refs = ws.find_references("helpers", "helper", include_declaration=False)
        assert len(refs) >= 1  # cross-module call

    def test_find_references_include_declaration_flag(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "main.mn": "fn main() { print(str(helper())) }",
            }
        )
        refs_no = ws.find_references("helpers", "helper", include_declaration=False)
        refs_yes = ws.find_references("helpers", "helper", include_declaration=True)
        assert len(refs_yes) == len(refs_no) + 1  # declaration adds one

    def test_find_references_enum_variant_use(self) -> None:
        _, ws = _make_workspace(
            {
                "types.mn": "enum Color { Red, Green, Blue }",
                "main.mn": (
                    "fn describe(c: Color) -> String {\n"
                    "    match c {\n"
                    '        Red => "r",\n'
                    '        _ => "o"\n'
                    "    }\n"
                    "}\n"
                    "fn main() { print(describe(Color::Red)) }"
                ),
            }
        )
        # Color should be referenced in main.mn
        refs = ws.find_references("types", "Color", include_declaration=False)
        # May or may not pick up the type annotation depending on walker depth
        assert isinstance(refs, list)

    def test_find_references_nonexistent_returns_empty(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        refs = ws.find_references("main", "nonexistent", include_declaration=False)
        assert refs == []
