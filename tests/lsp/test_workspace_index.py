"""Tests for the WorkspaceIndex (v4.37.0 — cross-module LSP foundation)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mapanare.lsp.workspace import WorkspaceIndex, _extract_top_level_symbols
from mapanare.parser import parse


def _make_workspace(files: dict[str, str]) -> tuple[Path, WorkspaceIndex]:
    """Create a temp workspace with given files and return (root, index)."""
    tmpdir = Path(tempfile.mkdtemp())
    for name, content in files.items():
        fpath = tmpdir / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    ws = WorkspaceIndex()
    ws.scan_root(tmpdir)
    return tmpdir, ws


class TestWorkspaceScan:
    def test_scan_root_finds_all_files(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
                "helpers.mn": "fn helper() -> Int { return 42 }",
                "types.mn": "struct Point { x: Int, y: Int }",
            }
        )
        assert len(ws.files) == 3

    def test_scan_collects_top_level_symbols(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
                "helpers.mn": (
                    "pub fn helper() -> Int { return 42 }\n" "fn internal_fn() -> Int { return 1 }"
                ),
                "types.mn": "struct Point { x: Int, y: Int }\nenum Color { Red, Green, Blue }",
            }
        )
        all_syms = ws.all_symbols()
        names = {s.name for s in all_syms}
        assert "main" in names
        assert "helper" in names
        assert "internal_fn" in names
        assert "Point" in names
        assert "Color" in names
        assert len(all_syms) == 5

    def test_lookup_by_module_and_name(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        assert sym is not None
        assert sym.kind == "fn"
        assert sym.name == "helper"
        assert sym.visibility == "pub"

    def test_lookup_by_name_across_modules(self) -> None:
        _, ws = _make_workspace(
            {
                "a.mn": "fn shared_name() -> Int { return 1 }",
                "b.mn": "fn shared_name() -> Int { return 2 }",
            }
        )
        results = ws.lookup_by_name("shared_name")
        assert len(results) == 2

    def test_lookup_nonexistent_returns_none(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        assert ws.lookup("main", "nonexistent") is None
        assert ws.lookup_by_name("nonexistent") == []


class TestWorkspaceRebuild:
    def test_rebuild_file_replaces_old_symbols(self) -> None:
        root, ws = _make_workspace(
            {
                "helpers.mn": "fn old_fn() -> Int { return 1 }",
            }
        )
        assert ws.lookup("helpers", "old_fn") is not None

        # Rebuild with new content
        new_source = "fn old_fn() -> Int { return 1 }\nfn new_fn() -> Int { return 2 }"
        ws.rebuild_file(root / "helpers.mn", source=new_source)

        assert ws.lookup("helpers", "old_fn") is not None
        assert ws.lookup("helpers", "new_fn") is not None

    def test_rebuild_file_removes_deleted_symbols(self) -> None:
        root, ws = _make_workspace(
            {
                "helpers.mn": "fn old_fn() -> Int { return 1 }\nfn doomed() -> Int { return 0 }",
            }
        )
        assert ws.lookup("helpers", "doomed") is not None

        # Rebuild without doomed
        ws.rebuild_file(root / "helpers.mn", source="fn old_fn() -> Int { return 1 }")
        assert ws.lookup("helpers", "doomed") is None
        assert ws.lookup("helpers", "old_fn") is not None

    def test_handles_file_with_parse_errors(self) -> None:
        _, ws = _make_workspace(
            {
                "broken.mn": "fn broken( { invalid syntax",
                "good.mn": "fn good() -> Int { return 1 }",
            }
        )
        # Broken file should not crash the index
        assert ws.lookup("good", "good") is not None
        assert len(ws.files) == 2  # Both files tracked even if broken


class TestSymbolExtraction:
    def test_extracts_functions(self) -> None:
        prog = parse("fn add(a: Int, b: Int) -> Int { return a + b }", filename="test.mn")
        syms = _extract_top_level_symbols(prog, "test", Path("test.mn"))
        assert len(syms) == 1
        assert syms[0].kind == "fn"
        assert syms[0].name == "add"
        assert "fn add" in syms[0].detail

    def test_extracts_structs(self) -> None:
        prog = parse("struct Point { x: Int, y: Int }", filename="test.mn")
        syms = _extract_top_level_symbols(prog, "test", Path("test.mn"))
        assert len(syms) == 1
        assert syms[0].kind == "struct"
        assert syms[0].name == "Point"

    def test_extracts_enums(self) -> None:
        prog = parse("enum Color { Red, Green, Blue }", filename="test.mn")
        syms = _extract_top_level_symbols(prog, "test", Path("test.mn"))
        assert len(syms) == 1
        assert syms[0].kind == "enum"
        assert syms[0].name == "Color"

    def test_pub_visibility(self) -> None:
        prog = parse("pub fn public_fn() -> Int { return 1 }", filename="test.mn")
        syms = _extract_top_level_symbols(prog, "test", Path("test.mn"))
        assert syms[0].visibility == "pub"

    def test_internal_visibility(self) -> None:
        prog = parse("fn private_fn() -> Int { return 1 }", filename="test.mn")
        syms = _extract_top_level_symbols(prog, "test", Path("test.mn"))
        assert syms[0].visibility == "internal"
