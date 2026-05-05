"""Tests for the v5.44.0 Ps.10 tarball-exclusion contract.

When `mnc package` builds a publish tarball, the project's local
`mn_modules/` directory must be excluded. Including dependencies in
the tarball would bloat packages and ship transitive deps
unintentionally.

This behavior was already correct at v5.43.0 HEAD (`stdlib/pkg.py:
_build_tarball` line ~605 explicitly skips `mn_modules`,
`mapanare_packages`, `__pycache__`, `node_modules`, and hidden dirs).
v5.44.0 locks it as a regression gate so a future refactor can't
silently re-include them.

Falsifiability: removing the `mn_modules` filter from `_build_tarball`
fails this test.
"""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

from stdlib.pkg import _build_tarball


def _make_publishable(tmp_path: Path) -> Path:
    """Create a minimal publishable project with installed deps."""
    proj = tmp_path / "publishable"
    proj.mkdir()
    (proj / "mapanare.toml").write_text(
        '[package]\nname = "publishable"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (proj / "main.mn").write_text(
        'fn main() { print("hi") }\n', encoding="utf-8"
    )
    # Stage an installed dependency that MUST NOT appear in the tarball.
    pkg = proj / "mn_modules" / "should_not_publish-0.1.0"
    pkg.mkdir(parents=True)
    (pkg / "main.mn").write_text(
        'pub fn dep() -> Int { return 1 }\n', encoding="utf-8"
    )
    (pkg / "mapanare.toml").write_text(
        '[package]\nname = "should_not_publish"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    # Also stage a __pycache__ and a hidden dir — both should be excluded.
    (proj / "__pycache__").mkdir()
    (proj / "__pycache__" / "junk.pyc").write_bytes(b"\x00\x00")
    (proj / ".git").mkdir()
    (proj / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    return proj


def test_tarball_excludes_mn_modules(tmp_path: Path) -> None:
    proj = _make_publishable(tmp_path)
    data = _build_tarball(str(proj))

    members: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            members.append(m.name)

    # The consumer's own files SHOULD be present.
    assert "mapanare.toml" in members
    assert "main.mn" in members

    # The installed dep MUST NOT be present anywhere.
    for name in members:
        assert "mn_modules" not in name, (
            f"tarball includes {name!r} — Ps.10 tarball-exclusion violated"
        )
        assert "should_not_publish" not in name


def test_tarball_excludes_pycache(tmp_path: Path) -> None:
    proj = _make_publishable(tmp_path)
    data = _build_tarball(str(proj))

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        members = [m.name for m in tar.getmembers()]

    for name in members:
        assert "__pycache__" not in name


def test_tarball_excludes_hidden_dirs(tmp_path: Path) -> None:
    proj = _make_publishable(tmp_path)
    data = _build_tarball(str(proj))

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        members = [m.name for m in tar.getmembers()]

    for name in members:
        # No path component starts with "."
        parts = name.split("/")
        for p in parts:
            assert not p.startswith("."), (
                f"tarball includes hidden path {name!r}"
            )
