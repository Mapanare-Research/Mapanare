"""Tests for context-aware LSP completion (v4.39.0)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mapanare.lsp.completion import (
    complete_field_method,
    complete_identifiers,
    complete_import,
    complete_type,
)
from mapanare.lsp.workspace import WorkspaceIndex


def _make_workspace(files: dict[str, str]) -> tuple[Path, WorkspaceIndex]:
    tmpdir = Path(tempfile.mkdtemp())
    for name, content in files.items():
        (tmpdir / name).write_text(content, encoding="utf-8")
    ws = WorkspaceIndex()
    ws.scan_root(tmpdir)
    return tmpdir, ws


class TestImportCompletion:
    def test_import_offers_local_modules(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "utils.mn": "pub fn util() -> Int { return 1 }",
            }
        )
        candidates = complete_import("", ws)
        labels = {c.label for c in candidates}
        assert "helpers" in labels
        assert "utils" in labels
        assert "main" in labels

    def test_import_filters_by_prefix(self) -> None:
        _, ws = _make_workspace(
            {
                "helpers.mn": "pub fn helper() -> Int { return 42 }",
                "utils.mn": "pub fn util() -> Int { return 1 }",
            }
        )
        candidates = complete_import("h", ws)
        labels = {c.label for c in candidates}
        assert "helpers" in labels
        assert "utils" not in labels

    def test_import_offers_stdlib(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_import("", ws)
        labels = {c.label for c in candidates}
        assert "stdlib" in labels


class TestTypeCompletion:
    def test_type_offers_builtins(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_type(ws)
        labels = {c.label for c in candidates}
        assert "Int" in labels
        assert "Float" in labels
        assert "String" in labels
        assert "Bool" in labels
        assert "Option<T>" in labels
        assert "Result<T, E>" in labels

    def test_type_offers_user_types(self) -> None:
        _, ws = _make_workspace(
            {
                "types.mn": "struct Point { x: Int, y: Int }\nenum Color { Red, Green, Blue }",
            }
        )
        candidates = complete_type(ws)
        labels = {c.label for c in candidates}
        assert "Point" in labels
        assert "Color" in labels


class TestFieldMethodCompletion:
    def test_field_completion_on_struct(self) -> None:
        _, ws = _make_workspace(
            {
                "types.mn": "struct Point { x: Int, y: Int }",
            }
        )
        candidates = complete_field_method("Point", ws)
        labels = {c.label for c in candidates}
        assert "x" in labels or "y" in labels  # at least one field

    def test_method_completion_on_option(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_field_method("Option<Int>", ws)
        labels = {c.label for c in candidates}
        assert "is_some" in labels
        assert "unwrap" in labels

    def test_method_completion_on_string(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_field_method("String", ws)
        labels = {c.label for c in candidates}
        assert "len" in labels
        assert "contains" in labels
        assert "split" in labels

    def test_method_completion_on_list(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_field_method("List<Int>", ws)
        labels = {c.label for c in candidates}
        assert "len" in labels
        assert "push" in labels
        assert "map" in labels


class TestFallbackCompletion:
    def test_fallback_offers_current_module_symbols(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": (
                    "fn foo() -> Int { return 1 }\n"
                    "fn bar() -> Int { return 2 }\n"
                    "fn main() { print(str(foo())) }"
                ),
            }
        )
        candidates = complete_identifiers(ws, current_module="main")
        labels = {c.label for c in candidates}
        assert "foo" in labels
        assert "bar" in labels

    def test_fallback_offers_builtins(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
            }
        )
        candidates = complete_identifiers(ws, current_module="main")
        labels = {c.label for c in candidates}
        assert "print" in labels
        assert "len" in labels
        assert "str" in labels

    def test_visibility_respected(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": 'fn main() { print("hello") }',
                "helpers.mn": (
                    "pub fn public_fn() -> Int { return 1 }\n"
                    "fn internal_fn() -> Int { return 2 }"
                ),
            }
        )
        candidates = complete_identifiers(ws, current_module="main")
        labels = {c.label for c in candidates}
        assert "public_fn" in labels
        # internal_fn is from another module — should not be offered
        assert "internal_fn" not in labels

    def test_current_module_symbols_ranked_first(self) -> None:
        _, ws = _make_workspace(
            {
                "main.mn": (
                    "fn local_fn() -> Int { return 1 }\n" "fn main() { print(str(local_fn())) }"
                ),
                "helpers.mn": "pub fn remote_fn() -> Int { return 2 }",
            }
        )
        candidates = complete_identifiers(ws, current_module="main")
        local = next((c for c in candidates if c.label == "local_fn"), None)
        remote = next((c for c in candidates if c.label == "remote_fn"), None)
        assert local is not None
        assert remote is not None
        # Local should sort before remote
        assert local.sort_text < remote.sort_text
