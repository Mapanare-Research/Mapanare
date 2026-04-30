"""End-to-end tests for ``mapanare init``.

v5.18.0 Mc.3: scaffolding now copies from
``mapanare/templates/init/<template>/`` instead of inline strings.
This suite locks in:

* full file set scaffolded (main.mn, mapanare.toml, .gitignore, README.md)
* {{NAME}} substitution applied
* main.mn uses canonical terse syntax (no brace blocks)
* scaffolded project parses + type-checks cleanly
* invalid project names are rejected
* re-init is non-destructive on existing files
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mapanare", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_init_scaffolds_full_file_set(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    r = _run("init", str(target), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert (target / "main.mn").is_file()
    assert (target / "mapanare.toml").is_file()
    assert (target / ".gitignore").is_file()
    assert (target / "README.md").is_file()


def test_init_substitutes_name_placeholder(tmp_path: Path) -> None:
    target = tmp_path / "myapp"
    r = _run("init", str(target), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "myapp" in (target / "main.mn").read_text()
    assert "myapp" in (target / "README.md").read_text()
    assert "myapp" in (target / "mapanare.toml").read_text()


def test_init_main_uses_terse_syntax(tmp_path: Path) -> None:
    """main.mn should use ``fn main():`` not ``fn main() {`` post-v5.17.0."""
    target = tmp_path / "terse"
    r = _run("init", str(target), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    body = (target / "main.mn").read_text()
    assert "fn main():" in body
    assert "{" not in body, "scaffold should emit terse colon-block, not braces"


def test_init_scaffolded_project_type_checks(tmp_path: Path) -> None:
    target = tmp_path / "checkable"
    r1 = _run("init", str(target), cwd=tmp_path)
    assert r1.returncode == 0, r1.stderr
    r2 = _run("check", str(target / "main.mn"), cwd=target)
    assert r2.returncode == 0, r2.stderr


def test_init_rejects_invalid_name(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    r = _run("init", str(target), "--name", "has spaces", cwd=tmp_path)
    assert r.returncode != 0


def test_init_preserves_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "main.mn").write_text("// existing user file\n")
    r = _run("init", str(target), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    # user's main.mn must not be overwritten
    assert (target / "main.mn").read_text() == "// existing user file\n"


@pytest.mark.parametrize(
    "name",
    ["mybin", "my_app", "my-app", "App2"],
)
def test_init_accepts_valid_names(tmp_path: Path, name: str) -> None:
    target = tmp_path / name
    r = _run("init", str(target), cwd=tmp_path)
    assert r.returncode == 0, r.stderr
