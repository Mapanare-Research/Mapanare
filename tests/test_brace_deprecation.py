"""v5.19.0 Te.3 — brace-block deprecation warning + auto-migration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from mapanare.parser import (
    count_user_brace_block_openers,
    parse,
)

# ---------------------------------------------------------------------------
# Te.3.A — count_user_brace_block_openers
# ---------------------------------------------------------------------------


def test_count_pure_colon_source_is_zero():
    src = 'fn main():\n    print("hi")\n'
    assert count_user_brace_block_openers(src) == 0


def test_count_pure_brace_source():
    src = 'fn main() {\n    print("hi")\n}\n'
    assert count_user_brace_block_openers(src) == 1


def test_count_mixed_source():
    src = 'fn a() {\n    print("a")\n}\n\nfn b():\n    print("b")\n'
    assert count_user_brace_block_openers(src) == 1


def test_count_multiple_brace_blocks():
    src = "fn a() {\n" "    if x > 0 {\n" '        print("yes")\n' "    }\n" "}\n"
    assert count_user_brace_block_openers(src) == 2


def test_count_ignores_map_literal():
    src = "let m = #{\n    1: 2,\n}\n"
    assert count_user_brace_block_openers(src) == 0


def test_count_ignores_brace_inside_string():
    src = 'fn main():\n    let s = "contains { in string"\n'
    assert count_user_brace_block_openers(src) == 0


def test_count_ignores_line_comment_with_brace():
    src = "fn main():\n    let x = 1 // comment with {\n"
    assert count_user_brace_block_openers(src) == 0


def test_count_ignores_full_comment_line():
    src = 'fn main():\n    // a brace here {\n    print("x")\n'
    assert count_user_brace_block_openers(src) == 0


def test_count_handles_escaped_quote_in_string():
    src = 'fn main():\n    let s = "x\\"y" + "{"\n'
    # The brace is inside a string literal — must not count.
    assert count_user_brace_block_openers(src) == 0


# ---------------------------------------------------------------------------
# Te.3.A — warning emission via parse()
# ---------------------------------------------------------------------------


def test_parse_emits_warning_for_brace_source(capsys):
    src = 'fn main() {\n    print("hi")\n}\n'
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    assert "deprecated" in captured.err
    assert "test.mn" in captured.err
    assert "1 occurrence" in captured.err


def test_parse_silent_on_colon_source(capsys):
    src = 'fn main():\n    print("hi")\n'
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    assert captured.err == ""


def test_parse_warning_plural_for_multiple_braces(capsys):
    src = "fn a() {\n" "    if x > 0 {\n" '        print("y")\n' "    }\n" "}\n"
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    assert "2 occurrences" in captured.err


def test_parse_one_warning_per_file_not_per_block(capsys):
    src = (
        "fn a() {\n"
        '    print("a")\n'
        "}\n"
        "fn b() {\n"
        '    print("b")\n'
        "}\n"
        "fn c() {\n"
        '    print("c")\n'
        "}\n"
    )
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    # Exactly one "warning:" line, not three.
    assert captured.err.count("warning:") == 1
    assert "3 occurrences" in captured.err


# ---------------------------------------------------------------------------
# Te.3.C — MAPANARE_NO_BRACE_WARNING suppresses
# ---------------------------------------------------------------------------


def test_env_var_suppresses_warning(monkeypatch, capsys):
    monkeypatch.setenv("MAPANARE_NO_BRACE_WARNING", "1")
    src = 'fn main() {\n    print("hi")\n}\n'
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    assert captured.err == ""


def test_env_var_unset_does_not_suppress(monkeypatch, capsys):
    monkeypatch.delenv("MAPANARE_NO_BRACE_WARNING", raising=False)
    src = 'fn main() {\n    print("hi")\n}\n'
    parse(src, filename="test.mn")
    captured = capsys.readouterr()
    assert "deprecated" in captured.err


# ---------------------------------------------------------------------------
# Te.3.B — mnc fmt auto-migration
# ---------------------------------------------------------------------------


def _run_fmt(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parent.parent
    env = {**os.environ, "PYTHONPATH": str(repo_root)}
    return subprocess.run(
        [sys.executable, "-m", "mapanare", "fmt", *args],
        cwd=cwd or repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_fmt_default_auto_migrates_braces(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main() {\n    print("hi")\n}\n', encoding="utf-8")
    result = _run_fmt([str(f)])
    assert result.returncode == 0, result.stderr
    text = f.read_text(encoding="utf-8")
    assert "{" not in text
    assert "fn main():" in text


def test_fmt_keep_braces_does_not_migrate(tmp_path):
    f = tmp_path / "x.mn"
    original = 'fn main() {\n    print("hi")\n}\n'
    f.write_text(original, encoding="utf-8")
    result = _run_fmt([str(f), "--keep-braces"])
    assert result.returncode == 0, result.stderr
    text = f.read_text(encoding="utf-8")
    # Whitespace-only formatting preserved braces
    assert "fn main() {" in text


def test_fmt_check_fails_on_brace_source(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main() {\n    print("hi")\n}\n', encoding="utf-8")
    result = _run_fmt([str(f), "--check"])
    assert result.returncode == 1
    assert "would format" in result.stderr


def test_fmt_check_passes_on_colon_source(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main():\n    print("hi")\n', encoding="utf-8")
    result = _run_fmt([str(f), "--check"])
    assert result.returncode == 0


def test_fmt_check_keep_braces_passes_on_brace_source(tmp_path):
    """--keep-braces + already-formatted brace source: --check passes."""
    f = tmp_path / "x.mn"
    # Already canonical whitespace, brace style.
    f.write_text('fn main() {\n    print("hi")\n}\n', encoding="utf-8")
    result = _run_fmt([str(f), "--check", "--keep-braces"])
    assert result.returncode == 0


def test_fmt_does_not_emit_redundant_warning_during_migration(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main() {\n    print("hi")\n}\n', encoding="utf-8")
    result = _run_fmt([str(f)])
    # The "Run mnc fmt to migrate" warning would be redundant since
    # the user is already running fmt; cmd_fmt suppresses it during
    # its parse-validation call.
    assert "deprecated" not in result.stderr


def test_fmt_to_terse_and_keep_braces_mutually_exclusive(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main():\n    print("hi")\n', encoding="utf-8")
    result = _run_fmt([str(f), "--to-terse", "--keep-braces"])
    assert result.returncode == 1
    assert "mutually exclusive" in result.stderr


def test_fmt_to_braces_and_keep_braces_mutually_exclusive(tmp_path):
    f = tmp_path / "x.mn"
    f.write_text('fn main():\n    print("hi")\n', encoding="utf-8")
    result = _run_fmt([str(f), "--to-braces", "--keep-braces"])
    assert result.returncode == 1
    assert "mutually exclusive" in result.stderr
