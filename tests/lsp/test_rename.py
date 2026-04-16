"""Tests for rename refactoring via WorkspaceIndex (v4.38.0)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mapanare.lsp.rename import apply_rename, validate_rename
from mapanare.lsp.workspace import WorkspaceIndex


def _make_workspace(files: dict[str, str]) -> tuple[Path, WorkspaceIndex]:
    tmpdir = Path(tempfile.mkdtemp())
    for name, content in files.items():
        (tmpdir / name).write_text(content, encoding="utf-8")
    ws = WorkspaceIndex()
    ws.scan_root(tmpdir)
    return tmpdir, ws


class TestValidateRename:
    def test_valid_rename_accepted(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        assert sym is not None
        assert validate_rename(sym, "new_helper", ws) is None

    def test_rename_rejects_keyword(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        err = validate_rename(sym, "if", ws)
        assert err is not None
        assert "keyword" in err

    def test_rename_rejects_invalid_identifier(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        err = validate_rename(sym, "123bad", ws)
        assert err is not None
        assert "not a valid identifier" in err

    def test_rename_rejects_name_already_in_module(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "fn helper() -> Int { return 42 }\nfn other() -> Int { return 1 }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        err = validate_rename(sym, "other", ws)
        assert err is not None
        assert "already exists" in err

    def test_rename_allows_name_in_different_module(self) -> None:
        _, ws = _make_workspace(
            {
                "a.mn": "fn helper() -> Int { return 1 }",
                "b.mn": "fn other() -> Int { return 2 }",
            }
        )
        sym = ws.lookup("a", "helper")
        # "other" exists in module b, not in module a — should be allowed
        assert validate_rename(sym, "other", ws) is None


class TestApplyRename:
    def test_rename_single_file(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "fn old_name() -> Int { return 42 }",
            }
        )
        sym = ws.lookup("helpers", "old_name")
        changes = apply_rename(sym, "new_name", ws)
        assert len(changes) == 1  # one file
        edits = list(changes.values())[0]
        assert len(edits) >= 1
        assert edits[0]["newText"] == "new_name"

    def test_rename_across_modules(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "main.mn": "fn main() { print(str(helper())) }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        changes = apply_rename(sym, "new_helper", ws)
        assert len(changes) == 2  # both files

    def test_rename_preserves_all_edits(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "a.mn": "fn a() -> Int { return helper() }",
                "b.mn": "fn b() -> Int { return helper() }",
            }
        )
        sym = ws.lookup("helpers", "helper")
        changes = apply_rename(sym, "new_helper", ws)
        total_edits = sum(len(edits) for edits in changes.values())
        assert total_edits >= 3  # 1 def + 2 refs
