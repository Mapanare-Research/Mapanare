"""v4.31.0 Phase 1.4 — User-Agent is wired to VERSION.

The v4.26.0 seven-reviewer panel flagged the hardcoded
``User-Agent: Mapanare/3.42`` string in ``runtime/native/mapanare_io.c``
as a 5+ minor version carry-forward (Mamba, Viper). v4.31.0 wires the
string to a compile-time ``MAPANARE_VERSION`` macro sourced from the
``VERSION`` file by both the Python bootstrap and the Makefile. This
test is the regression gate — it verifies the string inside the built
runtime archive matches the contents of ``VERSION`` on disk.

The test is cheap (reads the archive, greps for the User-Agent line)
and does not require network access. It runs on every pytest invocation
so a future release that rolls back the macro wiring gets caught at
PR time, not by another panel six versions later.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_VERSION_FILE = _PROJECT_ROOT / "VERSION"
_RUNTIME_ARCHIVE = _PROJECT_ROOT / "runtime" / "native" / "libmapanare_rt.a"


def _current_version() -> str:
    return _VERSION_FILE.read_text(encoding="utf-8").strip()


def _strings_from_archive() -> list[str]:
    if not _RUNTIME_ARCHIVE.exists():
        pytest.skip(f"{_RUNTIME_ARCHIVE} not built; run `make build-rt` before this test.")
    result = subprocess.run(
        ["strings", str(_RUNTIME_ARCHIVE)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("strings(1) unavailable")
    return result.stdout.splitlines()


class TestUserAgentMatchesVersion:
    """The compiled archive's User-Agent string must match the repo VERSION."""

    def test_user_agent_contains_current_version(self) -> None:
        version = _current_version()
        lines = _strings_from_archive()
        ua_lines = [ln for ln in lines if "User-Agent:" in ln and "Mapanare/" in ln]
        assert ua_lines, (
            "no User-Agent line found in libmapanare_rt.a — "
            "did mapanare_io.c stop including the string?"
        )
        # There may be multiple strings if the archive has been rebuilt
        # with a different VERSION since last clean; the current version
        # must appear at least once.
        expected = f"Mapanare/{version}"
        assert any(
            expected in ln for ln in ua_lines
        ), f"User-Agent did not include {expected!r}. Found lines:\n" + "\n".join(
            f"  {ln}" for ln in ua_lines
        )

    def test_user_agent_is_not_stale_3_x(self) -> None:
        """v4.26.0 panel: ``Mapanare/3.42`` was the stale string.

        Regression gate — any 3.x in the User-Agent string means the
        macro wiring broke.
        """
        version = _current_version()
        if version.startswith("3."):
            pytest.skip("VERSION is genuinely a 3.x release")
        lines = _strings_from_archive()
        ua_lines = [ln for ln in lines if "User-Agent:" in ln]
        stale_lines = [ln for ln in ua_lines if "Mapanare/3." in ln]
        assert (
            stale_lines == []
        ), f"User-Agent still advertises a 3.x Mapanare release: {stale_lines}"

    def test_user_agent_is_not_fallback_unknown(self) -> None:
        """If MAPANARE_VERSION was not passed at compile time, the
        fallback ``"unknown"`` fires. That is a build-system bug.
        """
        lines = _strings_from_archive()
        ua_lines = [ln for ln in lines if "User-Agent:" in ln]
        fallback_lines = [ln for ln in ua_lines if "Mapanare/unknown" in ln]
        assert fallback_lines == [], (
            "User-Agent contains the 'unknown' fallback. Either "
            "scripts/build_stage1.py or Makefile build-rt failed to "
            "pass -DMAPANARE_VERSION=... at compile time."
        )
