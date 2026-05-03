"""v5.24.0 Hy.3 — cadence enforcement gate unit tests.

Exercises ``scripts/check_cadence.py`` against the live repo state
(must be within-cadence at HEAD) plus constructed fixtures for the
OVERDUE class.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_cadence.py"


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=cwd,
    )


def _make_fixture(tmp_path: Path, *, version: str, panels: list[str]) -> Path:
    (tmp_path / "VERSION").write_text(f"{version}\n")
    review_dir = tmp_path / ".reviews"
    review_dir.mkdir()
    for panel in panels:
        panel_dir = review_dir / panel
        panel_dir.mkdir()
        # Cadence script requires at least one .md file in the panel
        # directory to count it as a real panel.
        (panel_dir / "README.md").write_text("# fixture panel\n")
    return tmp_path


# ── Live-repo invariant ──


def test_cadence_within_window_at_head() -> None:
    """v5.23.2 + last panel v5.22.0 → 1 minor lag → OK."""
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT,
    )
    assert (
        result.returncode == 0
    ), f"expected within cadence at HEAD, got:\n{result.stdout}\n{result.stderr}"
    assert "OK" in result.stdout


# ── Constructed fixtures ──


def test_cadence_overdue_fixture(tmp_path: Path) -> None:
    """Latest panel at v5.10.0, current at v5.30.0 (lag 20) → OVERDUE."""
    cwd = _make_fixture(tmp_path, version="5.30.0", panels=["v5.10.0"])
    result = _run(cwd)
    assert result.returncode == 1, f"expected OVERDUE, got: {result.stdout}"
    assert "OVERDUE" in result.stdout
    assert "v5.10.0" in result.stdout


def test_cadence_at_threshold_fires(tmp_path: Path) -> None:
    """5-minor lag exactly → OVERDUE (boundary)."""
    cwd = _make_fixture(tmp_path, version="5.27.0", panels=["v5.22.0"])
    result = _run(cwd)
    assert result.returncode == 1, f"expected OVERDUE, got: {result.stdout}"


def test_cadence_just_below_threshold_passes(tmp_path: Path) -> None:
    """4-minor lag → OK (boundary)."""
    cwd = _make_fixture(tmp_path, version="5.26.0", panels=["v5.22.0"])
    result = _run(cwd)
    assert result.returncode == 0, f"expected OK, got: {result.stdout}"
    assert "OK" in result.stdout


def test_cadence_picks_latest_panel(tmp_path: Path) -> None:
    """Multiple panels — latest wins."""
    cwd = _make_fixture(
        tmp_path,
        version="5.24.0",
        panels=["v5.10.0", "v5.15.0", "v5.22.0"],
    )
    result = _run(cwd)
    assert result.returncode == 0, f"expected OK, got: {result.stdout}"
    assert "v5.22.0" in result.stdout


def test_cadence_no_panels_clean(tmp_path: Path) -> None:
    """No panel history at all → emit a note, exit 0 (not the gate's job)."""
    (tmp_path / "VERSION").write_text("5.0.0\n")
    (tmp_path / ".reviews").mkdir()
    result = _run(tmp_path)
    assert result.returncode == 0, f"expected 0, got: {result.stdout}"
    assert "no prior panel" in result.stdout
