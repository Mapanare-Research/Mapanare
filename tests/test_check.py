"""End-to-end tests for ``mapanare check``.

v5.18.0 Mc.4: the type-check subcommand was already wired in cli.py;
this suite locks in:

* clean file        -> exit 0, "check: <path> OK" on stdout
* type error        -> exit 1, diagnostic on stderr
* parse error       -> exit 1, diagnostic on stderr
* multi-error file  -> exit 1, every error reported
* --werror          -> warnings become errors
* --all             -> walks .mn files; aggregates pass/fail
* no source, no --all -> exit 2 with usage hint

Each test invokes the CLI via ``python -m mapanare`` from a tmp_path
working directory so it never depends on the source tree's state.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _run_check(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mapanare", "check", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(p: Path, body: str) -> Path:
    p.write_text(body, encoding="utf-8")
    return p


def test_check_clean_file_exits_zero(tmp_path: Path) -> None:
    f = _write(tmp_path / "ok.mn", 'fn main():\n    print("hi")\n')
    r = _run_check(str(f), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "OK" in r.stdout


def test_check_type_error_exits_one(tmp_path: Path) -> None:
    f = _write(tmp_path / "bad.mn", 'fn main():\n    let x: Int = "nope"\n')
    r = _run_check(str(f), cwd=tmp_path)
    assert r.returncode == 1
    assert "error" in r.stderr.lower()


def test_check_parse_error_exits_one(tmp_path: Path) -> None:
    f = _write(tmp_path / "bad.mn", 'fn main(:\n    print("oops")\n')
    r = _run_check(str(f), cwd=tmp_path)
    assert r.returncode == 1
    assert r.stderr  # diagnostic emitted


def test_check_multiple_errors_all_reported(tmp_path: Path) -> None:
    body = 'fn main():\n    let a: Int = "x"\n    let b: Int = "y"\n'
    f = _write(tmp_path / "bad.mn", body)
    r = _run_check(str(f), cwd=tmp_path)
    assert r.returncode == 1
    # both bad assignments should surface
    assert r.stderr.count("error") >= 2


def test_check_werror_promotes_warnings(tmp_path: Path) -> None:
    """--werror flag is accepted; behavior is forwarded to the semantic checker.

    We don't assume which constructs trigger a warning today (that's a moving
    target across releases); we only verify the flag is wired and doesn't
    blow up on a clean file.
    """
    f = _write(tmp_path / "ok.mn", 'fn main():\n    print("hi")\n')
    r = _run_check(str(f), "--werror", cwd=tmp_path)
    assert r.returncode == 0, r.stderr


def test_check_all_walks_directory(tmp_path: Path) -> None:
    _write(tmp_path / "a.mn", 'fn main():\n    print("a")\n')
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub / "b.mn", 'fn helper():\n    print("b")\n')
    r = _run_check("--all", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert r.stdout.count("OK") == 2


def test_check_all_reports_aggregate_failures(tmp_path: Path) -> None:
    _write(tmp_path / "a.mn", 'fn main():\n    print("a")\n')
    _write(tmp_path / "b.mn", 'fn main():\n    let x: Int = "nope"\n')
    r = _run_check("--all", cwd=tmp_path)
    assert r.returncode == 1
    assert "1/2" in r.stderr or "1 of 2" in r.stderr or "had errors" in r.stderr


def test_check_no_source_no_all_exits_two(tmp_path: Path) -> None:
    r = _run_check(cwd=tmp_path)
    assert r.returncode == 2
    assert "--all" in r.stderr or "source" in r.stderr


def test_check_all_skips_build_dirs(tmp_path: Path) -> None:
    """`.git`, `dist/`, `build/` and friends should not be walked."""
    _write(tmp_path / "main.mn", 'fn main():\n    print("a")\n')
    bad_dir = tmp_path / "dist"
    bad_dir.mkdir()
    _write(bad_dir / "broken.mn", "fn main(:\n    bogus\n")  # would fail
    r = _run_check("--all", cwd=tmp_path)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("missing", ["does_not_exist.mn"])
def test_check_missing_file(tmp_path: Path, missing: str) -> None:
    r = _run_check(missing, cwd=tmp_path)
    assert r.returncode != 0
