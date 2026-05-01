"""Tests for ``mapanare.format`` — v5.13.0 (Mc.2).

The formatter is required to be:

- Idempotent on the entire ``.mn`` corpus.
- AST-preserving: ``parse(src) == parse(format(src))`` for every file
  that parses today.
- Conservative: it only normalizes whitespace; it does not rewrite
  expressions, change indentation, or touch braces.

These tests are the load-bearing safety net for the v5.14.0+ terseness
arc, which adds ``--to-terse`` rewrite passes on top of this core.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from mapanare.format import check_formatted, format_source
from mapanare.parser import parse

_REPO_ROOT = Path(__file__).resolve().parent.parent

_CORPUS_ROOTS = [
    _REPO_ROOT / "tests" / "golden",
    _REPO_ROOT / "mapanare" / "self",
    _REPO_ROOT / "examples",
]

_CORPUS: list[Path] = []
for _root in _CORPUS_ROOTS:
    if _root.exists():
        _CORPUS.extend(sorted(_root.rglob("*.mn")))

# ---------------------------------------------------------------------------
# Unit tests — pure rules
# ---------------------------------------------------------------------------


class TestRules:
    def test_empty_input_returns_empty(self) -> None:
        assert format_source("") == ""

    def test_single_line_no_newline_gets_one(self) -> None:
        assert format_source("fn main() {}") == "fn main() {}\n"

    def test_single_line_with_newline_unchanged(self) -> None:
        assert format_source("fn main() {}\n") == "fn main() {}\n"

    def test_strips_trailing_whitespace(self) -> None:
        assert format_source("a   \nb\t\n") == "a\nb\n"

    def test_normalizes_crlf_to_lf(self) -> None:
        assert format_source("a\r\nb\r\n") == "a\nb\n"

    def test_normalizes_bare_cr_to_lf(self) -> None:
        # Files with classic-Mac CR-only endings should still normalize.
        assert format_source("a\rb\rc\r") == "a\nb\nc\n"

    def test_collapses_multiple_blank_lines_to_one(self) -> None:
        assert format_source("a\n\n\n\nb\n") == "a\n\nb\n"

    def test_strips_leading_blank_lines(self) -> None:
        assert format_source("\n\n\nfn main() {}\n") == "fn main() {}\n"

    def test_strips_trailing_blank_lines(self) -> None:
        assert format_source("fn main() {}\n\n\n") == "fn main() {}\n"

    def test_replaces_leading_tabs_with_four_spaces(self) -> None:
        assert format_source("fn f() {\n\tprint(1)\n}\n") == "fn f() {\n    print(1)\n}\n"

    def test_does_not_touch_mid_line_tabs(self) -> None:
        # Only LEADING tabs are replaced — a tab inside a string literal
        # or after non-whitespace content stays put.
        assert format_source('print("a\tb")\n') == 'print("a\tb")\n'

    def test_check_formatted_true_on_canonical(self) -> None:
        assert check_formatted("fn main() {}\n") is True

    def test_check_formatted_false_on_non_canonical(self) -> None:
        assert check_formatted("fn main() {}") is False  # missing trailing \n
        assert check_formatted("fn main() {}\n\n\n") is False  # extra blanks
        assert check_formatted("fn main() {}\r\n") is False  # CRLF


# ---------------------------------------------------------------------------
# Corpus tests — invariants must hold on every .mn file
# ---------------------------------------------------------------------------


def _ast_signature(node: Any, depth: int = 0) -> str:
    """Stable repr of an AST that ignores ``span`` fields.

    Spans contain line/column metadata that legitimately changes when
    whitespace shifts, so they are excluded from the equality check.
    """
    if depth > 200:
        return "<deep>"
    if is_dataclass(node):
        parts = []
        for f in fields(node):
            if f.name == "span":
                continue
            parts.append(f"{f.name}={_ast_signature(getattr(node, f.name), depth + 1)}")
        return f"{type(node).__name__}({', '.join(parts)})"
    if isinstance(node, list):
        return "[" + ", ".join(_ast_signature(x, depth + 1) for x in node) + "]"
    if isinstance(node, tuple):
        return "(" + ", ".join(_ast_signature(x, depth + 1) for x in node) + ")"
    if isinstance(node, dict):
        return (
            "{"
            + ", ".join(f"{k!r}: {_ast_signature(v, depth + 1)}" for k, v in sorted(node.items()))
            + "}"
        )
    return repr(node)


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_idempotent(path: Path) -> None:
    src = path.read_text(encoding="utf-8", errors="replace")
    once = format_source(src)
    twice = format_source(once)
    assert once == twice, f"format_source not idempotent on {path}"


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_ast_preserved_when_parses(path: Path) -> None:
    """Files that parse before format must parse to the same AST after.

    Files that don't parse before formatting are skipped — preserving
    pre-existing parse failures is covered by ``test_no_parse_regressions``.
    """
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        ast_before = parse(src, filename=str(path))
    except Exception:
        pytest.skip(f"{path} does not parse")
    formatted = format_source(src)
    try:
        ast_after = parse(formatted, filename=str(path))
    except Exception as e:  # pragma: no cover - failure mode
        pytest.fail(f"format_source broke parsing of {path}: {e}")
    assert _ast_signature(ast_before) == _ast_signature(
        ast_after
    ), f"format_source changed AST of {path}"


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_no_parse_regressions(path: Path) -> None:
    """A file that fails to parse before formatting must fail the same
    way after formatting — the formatter must not turn a syntax error
    into something more confusing.
    """
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        parse(src, filename=str(path))
        pytest.skip(f"{path} parses fine")
    except Exception as before:
        formatted = format_source(src)
        try:
            parse(formatted, filename=str(path))
        except Exception as after:
            assert type(before) is type(after), (
                f"format_source changed failure type on {path}: "
                f"{type(before).__name__} -> {type(after).__name__}"
            )


# ---------------------------------------------------------------------------
# Output-shape invariants — must hold on every formatted output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_output_no_cr(path: Path) -> None:
    src = path.read_text(encoding="utf-8", errors="replace")
    out = format_source(src)
    assert "\r" not in out, f"output contains CR for {path}"


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_output_no_trailing_whitespace(path: Path) -> None:
    src = path.read_text(encoding="utf-8", errors="replace")
    out = format_source(src)
    for i, line in enumerate(out.split("\n"), start=1):
        assert line == line.rstrip(), f"trailing whitespace at {path}:{i}"


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_output_no_triple_blank(path: Path) -> None:
    src = path.read_text(encoding="utf-8", errors="replace")
    out = format_source(src)
    assert "\n\n\n" not in out, f"triple newline run in formatted output of {path}"


@pytest.mark.parametrize("path", _CORPUS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_output_single_trailing_newline(path: Path) -> None:
    src = path.read_text(encoding="utf-8", errors="replace")
    out = format_source(src)
    if out:
        assert out.endswith("\n"), f"missing trailing newline on formatted {path}"
        assert not out.endswith("\n\n"), f"extra trailing newline on formatted {path}"


# ---------------------------------------------------------------------------
# CLI integration — the user-facing contract
# ---------------------------------------------------------------------------


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mapanare.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


class TestCli:
    def test_check_clean_corpus_exits_zero(self, tmp_path: Path) -> None:
        # The golden corpus must be canonically formatted at HEAD.
        # v5.19.0 Te.3.B + Phase 1.5: corpus migrated to colon syntax,
        # so the bare ``mnc fmt --check`` (auto-migrate default) is
        # silent on the corpus.
        result = _run_cli("fmt", "--check", "tests/golden")
        assert result.returncode == 0, (
            f"tests/golden has files that need reformatting:\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
        )

    def test_check_dirty_file_exits_one(self, tmp_path: Path) -> None:
        f = tmp_path / "dirty.mn"
        f.write_text("fn main() {   \n}\n")
        result = _run_cli("fmt", "--check", str(f))
        assert result.returncode == 1
        assert "would format" in result.stderr

    def test_check_does_not_modify_file(self, tmp_path: Path) -> None:
        f = tmp_path / "dirty.mn"
        original = "fn main() {   \n}\n"
        f.write_text(original)
        _run_cli("fmt", "--check", str(f))
        assert f.read_text() == original

    def test_default_writes_in_place(self, tmp_path: Path) -> None:
        # v5.19.0 Te.3.B: bare ``mnc fmt`` auto-migrates braces. Use
        # ``--keep-braces`` to preserve the v5.13.0 whitespace-only
        # contract this test was written against.
        f = tmp_path / "dirty.mn"
        f.write_text("fn main() {   \n}\n")
        result = _run_cli("fmt", "--keep-braces", str(f))
        assert result.returncode == 0
        assert f.read_text() == "fn main() {\n}\n"

    def test_stdout_does_not_modify_file(self, tmp_path: Path) -> None:
        f = tmp_path / "dirty.mn"
        original = "fn main() {   \n}\n"
        f.write_text(original)
        result = _run_cli("fmt", "--stdout", "--keep-braces", str(f))
        assert result.returncode == 0
        assert f.read_text() == original
        assert "fn main() {\n}\n" in result.stdout

    def test_directory_walks_recursively(self, tmp_path: Path) -> None:
        (tmp_path / "a").mkdir()
        f1 = tmp_path / "a" / "x.mn"
        f1.write_text("fn x() {  \n}\n")
        f2 = tmp_path / "y.mn"
        f2.write_text("fn y() {\n}\n")
        # v5.19.0: ``--keep-braces`` so the test exercises whitespace-only
        # canonicalization. With the new auto-migrate default both files
        # would "format" (be migrated to colon).
        result = _run_cli("fmt", "--check", "--keep-braces", str(tmp_path))
        # f1 needs reformatting (trailing whitespace), f2 does not -> exit 1
        assert result.returncode == 1
        assert "x.mn" in result.stderr
        assert "y.mn" not in result.stderr

    def test_parse_error_exits_one(self, tmp_path: Path) -> None:
        f = tmp_path / "broken.mn"
        f.write_text("fn {{{ broken\n")
        result = _run_cli("fmt", str(f))
        assert result.returncode == 1
