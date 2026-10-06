"""v5.31.0 Bn.4 — banner-firing matrix lock.

Locks the four {dev clone, release install} x {metadata cmd, compile cmd}
matrix cells plus the new banner wording. The banner used to fire
unconditionally at the top of ``main()`` (publish run #50 user reported a
release-install ``mnc --version`` printing the dev banner before the version
string); the v5.31.0 fix gates it on:

* ``_should_show_dev_banner`` — argv-peek skip for ``--version`` / ``--help``
  / ``-h`` / ``init`` / ``list`` (Bn.1).
* ``_is_release_install`` — ``MAPANARE_RELEASE=1`` env var (primary) or absence
  of ``pyproject.toml`` + ``.git`` at the repo root (path heuristic fallback,
  Bn.2).

Falsifiability round-trip: removing either gate in ``mapanare/cli.py`` and
re-running this file reproduces a publish-run-#50-shaped failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _run(argv: list[str], *, release: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if release:
        env["MAPANARE_RELEASE"] = "1"
    else:
        env.pop("MAPANARE_RELEASE", None)
    return subprocess.run(
        [sys.executable, "-m", "mapanare", *argv],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO,
    )


def test_version_release_install_no_banner() -> None:
    r = _run(["--version"], release=True)
    assert r.returncode == 0
    assert "dev" not in r.stderr.lower()
    assert "5." in r.stdout


def test_version_dev_clone_no_banner_on_metadata() -> None:
    r = _run(["--version"], release=False)
    assert r.returncode == 0
    assert "dev" not in r.stderr.lower()


def test_help_release_install_no_banner() -> None:
    r = _run(["--help"], release=True)
    assert r.returncode == 0
    assert "dev" not in r.stderr.lower()


def test_run_release_install_no_banner(tmp_path: Path) -> None:
    src = tmp_path / "h.mn"
    src.write_text('fn main():\n    print("hi")\n')
    r = _run(["check", str(src)], release=True)
    assert "dev" not in r.stderr.lower()


def test_run_dev_clone_does_show_banner(tmp_path: Path) -> None:
    src = tmp_path / "h.mn"
    src.write_text('fn main():\n    print("hi")\n')
    r = _run(["check", str(src)], release=False)
    assert "running from source clone" in r.stderr
