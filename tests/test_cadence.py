"""scripts/check_cadence.py unit tests.

History
-------
v5.24.0 Hy.3 introduced the cadence gate as an enforcing gate
(exit 1 on overdue) and these tests asserted that. v5.33.2 Cd.2
relaxed the script to informational-only (always exit 0); the
fixture tests below now assert the REMINDER message is printed
when lag is past threshold, but exit code stays 0. See
``scripts/check_cadence.py`` docstring + the user-level
``feedback_no_forced_cadence_gates`` memory for rationale.
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


def test_cadence_always_exits_zero_at_head() -> None:
    """v5.33.2 Cd.1: script is informational-only — always exits 0
    regardless of lag at HEAD."""
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT,
    )
    assert (
        result.returncode == 0
    ), f"expected exit 0 (informational), got:\n{result.stdout}\n{result.stderr}"
    # Either OK or REMINDER is acceptable; both are exit 0.
    assert "OK" in result.stdout or "REMINDER" in result.stdout


# ── Constructed fixtures ──


def test_cadence_overdue_fixture(tmp_path: Path) -> None:
    """Latest panel at v5.10.0, current at v5.30.0 (lag 20) → REMINDER, exit 0."""
    cwd = _make_fixture(tmp_path, version="5.30.0", panels=["v5.10.0"])
    result = _run(cwd)
    assert result.returncode == 0, f"expected exit 0 (informational), got: {result.stdout}"
    assert "REMINDER" in result.stdout
    assert "v5.10.0" in result.stdout


def test_cadence_at_threshold_prints_reminder(tmp_path: Path) -> None:
    """5-minor lag exactly → REMINDER printed (boundary), exit 0."""
    cwd = _make_fixture(tmp_path, version="5.27.0", panels=["v5.22.0"])
    result = _run(cwd)
    assert result.returncode == 0, f"expected exit 0, got: {result.stdout}"
    assert "REMINDER" in result.stdout


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
