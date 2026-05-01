"""v5.24.0 Hy.2 — docs-freshness gate unit tests.

Exercises ``scripts/check_doc_freshness.py`` against the repo state
(must be clean at HEAD) plus constructed fixtures for each violation
class. Constructed-fixture tests use a temporary working directory so
they do not perturb the live tree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_doc_freshness.py"


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
    )


def _make_fixture(
    tmp_path: Path,
    *,
    version: str = "5.24.0",
    goldens: int = 95,
    readme_text: str | None = None,
    spec_text: str | None = None,
) -> Path:
    """Create a minimal repo-shaped fixture."""
    (tmp_path / "VERSION").write_text(f"{version}\n")
    golden_dir = tmp_path / "tests" / "golden"
    golden_dir.mkdir(parents=True)
    for i in range(goldens):
        (golden_dir / f"{i:02d}.mn").write_text("// fixture\n")
    if readme_text is not None:
        (tmp_path / "README.md").write_text(readme_text)
    if spec_text is not None:
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "SPEC.md").write_text(spec_text)
    return tmp_path


# ── Live-repo invariant ──


def test_check_doc_freshness_clean_at_head() -> None:
    """The gate must be GREEN at v5.24.0 HEAD (post-RC.* / Mb.* / Te.3.B)."""
    result = _run(ROOT)
    assert result.returncode == 0, f"expected clean at HEAD, got:\n{result.stdout}\n{result.stderr}"
    assert "clean" in result.stdout


# ── Constructed fixtures: each violation class must be detected ──


def test_detects_version_badge_drift(tmp_path: Path) -> None:
    """Badge says v5.0.0 but VERSION says v5.24.0 — RED."""
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-green.svg)]()\n"
        "Body: (95/95 native goldens) at v5.24.0.\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme)
    result = _run(cwd)
    assert result.returncode == 1, f"expected RED, got: {result.stdout}"
    assert "5.0.0" in result.stdout
    assert "5.24.0" in result.stdout


def test_detects_goldens_badge_drift(tmp_path: Path) -> None:
    """Badge says 80/80 but actual is 95/95 — RED."""
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.24.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-80%2F80-green.svg)]()\n"
        "Body: (95/95 native goldens) at v5.24.0.\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme)
    result = _run(cwd)
    assert result.returncode == 1, f"expected RED, got: {result.stdout}"
    assert "80/80" in result.stdout
    assert "95/95" in result.stdout


def test_detects_multiple_distinct_line_counts(tmp_path: Path) -> None:
    """README body has both '238,086 lines' and '239,835 lines' — RED."""
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.24.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-green.svg)]()\n"
        "STRICT 3-stage fixed point at 238,086 lines (preserved).\n"
        "After the latest changes: 239,835 lines.\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme)
    result = _run(cwd)
    assert result.returncode == 1, f"expected RED, got: {result.stdout}"
    assert "238,086" in result.stdout
    assert "239,835" in result.stdout


def test_detects_body_goldens_drift(tmp_path: Path) -> None:
    """Body says (66/66 native goldens) but actual is 95 — RED."""
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.24.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-green.svg)]()\n"
        "Body: (66/66 native goldens) at v5.24.0.\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme)
    result = _run(cwd)
    assert result.returncode == 1, f"expected RED, got: {result.stdout}"
    assert "66/66" in result.stdout


def test_detects_spec_header_drift(tmp_path: Path) -> None:
    """SPEC says synced to v5.10.0 but VERSION is 5.24.0 (lag = 14) — RED."""
    spec = (
        "# Mapanare Language Specification\n\n"
        "**Version:** 5.10.0\n"
        "**Status:** Live — synced to the v5.10.0 cut (2026-01-01)\n"
    )
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.24.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-green.svg)]()\n"
        "Body: (95/95 native goldens).\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme, spec_text=spec)
    result = _run(cwd)
    assert result.returncode == 1, f"expected RED, got: {result.stdout}"
    assert "SPEC.md" in result.stdout


def test_tolerates_two_minor_spec_lag(tmp_path: Path) -> None:
    """SPEC at v5.22.0 cut + VERSION 5.24.0 = lag 2 — tolerated, GREEN."""
    spec = (
        "# Mapanare Language Specification\n\n"
        "**Version:** 5.22.0\n"
        "**Status:** Live — synced to the v5.22.0 cut\n"
    )
    readme = (
        "[![Version](https://img.shields.io/badge/version-5.24.0-blue.svg)]()\n"
        "[![Goldens](https://img.shields.io/badge/goldens-95%2F95-green.svg)]()\n"
        "Body: (95/95 native goldens).\n"
    )
    cwd = _make_fixture(tmp_path, readme_text=readme, spec_text=spec)
    result = _run(cwd)
    assert result.returncode == 0, f"expected GREEN with lag=2, got: {result.stdout}"
