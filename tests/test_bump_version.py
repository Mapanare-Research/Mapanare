"""tests/test_bump_version.py — verify scripts/bump_version.py sweeps.

v5.23.0 RC.3: structural fix for the goldens-badge drift that surfaced as
Bo.25 in the v5.22.0 panel (4 README locales pinned at 66/66 while the
golden corpus had 95 entries since v5.21.0). The sweep now happens in
lockstep with the version-badge sweep.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bump_version.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bump_version", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_goldens_badge_regex_matches_all_locales() -> None:
    """The single _GOLDENS_BADGE_RE must match the badge in every README."""
    mod = _load_module()
    locales = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "README.es.md",
        REPO_ROOT / "docs" / "README.pt.md",
        REPO_ROOT / "docs" / "README.zh-CN.md",
    ]
    for path in locales:
        text = path.read_text(encoding="utf-8")
        assert mod._GOLDENS_BADGE_RE.search(text), (
            f"{path.relative_to(REPO_ROOT)}: goldens badge not found by "
            f"_GOLDENS_BADGE_RE — locale-pinning regression?"
        )


def test_count_goldens_matches_directory() -> None:
    mod = _load_module()
    actual = mod._count_goldens()
    direct = len(list((REPO_ROOT / "tests" / "golden").glob("*.mn")))
    assert actual == direct
    assert actual >= 95, f"goldens count {actual} below v5.21.0 baseline of 95"


def test_bump_goldens_badge_rewrites_count(tmp_path: Path) -> None:
    mod = _load_module()
    fixture = tmp_path / "fake_readme.md"
    fixture.write_text(
        "[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg)]()\n",
        encoding="utf-8",
    )
    path, modified = mod._bump_goldens_badge(fixture, 95, dry_run=False)
    assert modified
    assert "goldens-95%2F95-brightgreen" in fixture.read_text(encoding="utf-8")


def test_bump_goldens_badge_idempotent(tmp_path: Path) -> None:
    mod = _load_module()
    fixture = tmp_path / "fake_readme.md"
    fixture.write_text(
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-brightgreen.svg)]()\n",
        encoding="utf-8",
    )
    path, modified = mod._bump_goldens_badge(fixture, 95, dry_run=False)
    assert not modified


def test_live_readmes_match_actual_count() -> None:
    """Every locale's badge count must match the live tests/golden/ count."""
    mod = _load_module()
    expected = mod._count_goldens()
    pattern = re.compile(r"badge/goldens-(\d+)%2F(\d+)-brightgreen")
    locales = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "README.es.md",
        REPO_ROOT / "docs" / "README.pt.md",
        REPO_ROOT / "docs" / "README.zh-CN.md",
    ]
    for path in locales:
        text = path.read_text(encoding="utf-8")
        m = pattern.search(text)
        assert m is not None, f"{path.relative_to(REPO_ROOT)}: badge missing"
        n, d = int(m.group(1)), int(m.group(2))
        assert n == d == expected, (
            f"{path.relative_to(REPO_ROOT)}: goldens badge {n}/{d} drifted from "
            f"actual count {expected}; run scripts/bump_version.py to fix"
        )
