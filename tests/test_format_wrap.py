"""Tests for ``mapanare.format.find_long_lines`` — v5.27.0 (Mc.8).

Mc.8 ships as detect-only because Mapanare's grammar is strictly
single-line for all expressions: newlines are not implicit
continuations inside parens, brackets, or braces. Every wrap shape
(split arg list at comma, multi-line method chain at dot, multi-line
``&&`` / ``||`` / ``|>`` operator chain) fails the parser, so an
automatic line-wrap rewriter cannot satisfy the v5.13.0 Mc.2
AST-preservation invariant.

``find_long_lines`` is a pure read-only detector. The CLI surfaces
its results as warnings on stderr and (under ``--check``) treats
them as a check failure. The source is never modified by Mc.8.

These tests assert:

- The detector flags lines strictly exceeding ``max_length`` (off-by-one).
- It is trivially idempotent and AST-preserving (it never modifies source).
- ``max_length=0`` disables the check.
- Lines with embedded tabs, strings, comments are counted by raw length.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.format import find_long_lines

_REPO_ROOT = Path(__file__).resolve().parent.parent


class TestFindLongLines:
    def test_empty_source_returns_empty(self) -> None:
        assert find_long_lines("", 100) == []

    def test_short_lines_not_flagged(self) -> None:
        src = 'fn main() {\n    print("hi")\n}\n'
        assert find_long_lines(src, 100) == []

    def test_overlong_line_flagged(self) -> None:
        # 101-character line at line 1 (1-based).
        line = "x" * 101
        assert find_long_lines(line + "\n", 100) == [(1, 101)]

    def test_exact_max_length_not_flagged(self) -> None:
        # Strict inequality: a line of exactly max_length is under
        # the limit. Locks the off-by-one boundary.
        line = "x" * 100
        assert find_long_lines(line + "\n", 100) == []

    def test_one_over_max_length_flagged(self) -> None:
        line = "x" * 101
        assert find_long_lines(line + "\n", 100) == [(1, 101)]

    def test_line_numbers_one_based(self) -> None:
        src = "ok\n" + ("x" * 105) + "\nok\n"
        assert find_long_lines(src, 100) == [(2, 105)]

    def test_multiple_overlong_lines(self) -> None:
        src = ("x" * 101) + "\n" + "ok\n" + ("y" * 102) + "\n"
        assert find_long_lines(src, 100) == [(1, 101), (3, 102)]

    def test_max_length_zero_disables_check(self) -> None:
        # 0 is the CLI sentinel for "disabled" — empty result regardless
        # of input.
        src = ("x" * 999) + "\n"
        assert find_long_lines(src, 0) == []

    def test_negative_max_length_disables_check(self) -> None:
        src = ("x" * 999) + "\n"
        assert find_long_lines(src, -1) == []

    def test_idempotent_no_source_modification(self) -> None:
        # ``find_long_lines`` is a pure read-only detector — by
        # construction it cannot violate idempotence or AST preservation.
        # This test locks the contract via a representative invocation.
        src = "fn x() {\n    return " + ("a + " * 30) + "1\n}\n"
        before = src
        result_a = find_long_lines(src, 100)
        result_b = find_long_lines(src, 100)
        assert src == before  # input unchanged
        assert result_a == result_b  # deterministic

    def test_trailing_newline_excluded_from_length(self) -> None:
        # 100 visible chars + ``\n`` should NOT be flagged at limit 100.
        line = "x" * 100
        assert find_long_lines(line + "\n", 100) == []

    def test_no_trailing_newline(self) -> None:
        # Input without a trailing newline — last segment still counted.
        line = "x" * 101
        assert find_long_lines(line, 100) == [(1, 101)]

    def test_string_literal_content_counted(self) -> None:
        # The detector counts raw source-line length; it does not
        # peek inside string literals.
        long_str = '"' + ("a" * 110) + '"'
        src = f"let s: String = {long_str}\n"
        result = find_long_lines(src, 100)
        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == len(src.rstrip("\n"))

    def test_tabs_count_as_one_char(self) -> None:
        # Pre-formatter sources may contain tabs. Each tab counts as
        # one character for the detector — ``format_source`` would
        # normalize leading tabs to 4 spaces before this point in the
        # CLI pipeline, but the function itself is pre-normalization
        # safe.
        line = "\t" * 50  # 50 chars; well under the limit
        assert find_long_lines(line + "\n", 100) == []


class TestFmtCliLineLength:
    """End-to-end CLI wiring for ``mapanare fmt --line-length N``."""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "mapanare.cli", *args],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )

    # Tests use colon-style sources so the default ``--auto-migrate``
    # behavior (``{}`` → colon) is a no-op and only the long-line
    # detector contributes to the exit code.
    def test_line_length_zero_silent(self, tmp_path: Path) -> None:
        f = tmp_path / "long.mn"
        f.write_text('fn x():\n    let s = "' + ("a" * 200) + '"\n')
        result = self._run_cli("fmt", "--line-length", "0", str(f))
        assert "exceeds" not in result.stderr

    def test_line_length_reports_long_line_to_stderr(self, tmp_path: Path) -> None:
        f = tmp_path / "long.mn"
        f.write_text('fn x():\n    let s = "' + ("a" * 200) + '"\n')
        result = self._run_cli("fmt", "--line-length", "50", "--stdout", str(f))
        assert "exceeds 50 chars" in result.stderr
        assert str(f) in result.stderr

    def test_line_length_check_fails_on_long_line(self, tmp_path: Path) -> None:
        f = tmp_path / "long.mn"
        # Canonical colon-style: only failure source is line length.
        f.write_text('fn x():\n    let s = "' + ("a" * 200) + '"\n')
        result = self._run_cli("fmt", "--check", "--line-length", "50", str(f))
        assert result.returncode == 1
        assert "exceeds 50 chars" in result.stderr

    def test_line_length_check_passes_when_under_limit(self, tmp_path: Path) -> None:
        f = tmp_path / "short.mn"
        f.write_text("fn x():\n    return 1\n")
        result = self._run_cli("fmt", "--check", "--line-length", "100", str(f))
        assert result.returncode == 0
        assert "exceeds" not in result.stderr

    def test_line_length_does_not_modify_source(self, tmp_path: Path) -> None:
        # Detect-only: the source must be unchanged after a long-line scan.
        original = 'fn x():\n    let s = "' + ("a" * 200) + '"\n'
        f = tmp_path / "long.mn"
        f.write_text(original)
        self._run_cli("fmt", "--line-length", "50", str(f))
        # Canonical colon-style + canonical whitespace → formatter writes
        # nothing. The detector reports but never modifies.
        assert f.read_text() == original


@pytest.mark.parametrize(
    "src",
    [
        'fn main() {\n    print("hi")\n}\n',
        "let m: Map<String, Int> = #{}\n",
        "fn x() {\n    return " + ("a + " * 30) + "1\n}\n",
    ],
)
def test_find_long_lines_pure(src: str) -> None:
    """Pure-function sanity over a small fixture set."""
    snapshot = src
    find_long_lines(src, 100)
    find_long_lines(src, 50)
    find_long_lines(src, 1000)
    assert src == snapshot
