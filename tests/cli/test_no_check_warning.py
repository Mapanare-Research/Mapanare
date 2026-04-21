"""Tests for the ``--no-check`` stderr warning (v4.29.0).

``--no-check`` on ``mapanare build-multi`` bypasses semantic analysis for
bootstrapping self-hosted ``.mn`` modules that intentionally use
not-yet-checked constructs. Prior to v4.29.0 this was silent; now it
prints a loud warning to stderr whenever it is used.

The v4.18.0–v4.26.0 hollow-features regression was partly enabled by
escape hatches like this one that bypassed diagnostics without telling
anyone. The warning closes that loop: another developer reading CI logs
can now see when diagnostics were suppressed.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _tiny_module(body: str) -> str:
    """Write ``body`` to a scratch ``.mn`` file and return its path."""
    fd = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
    fd.write(body)
    fd.close()
    return fd.name


def _run_build_multi(
    source: str, extra: list[str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mapanare.cli",
            "build-multi",
            source,
            "-o",
            "/tmp/mapanare_no_check_test.ll",
            *(extra or []),
        ],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )


class TestNoCheckWarning:
    """``--no-check`` must print a stderr warning every time it is used."""

    def test_no_check_prints_warning_to_stderr(self) -> None:
        src = _tiny_module('fn main() {\n    print("hello")\n}\n')
        result = _run_build_multi(src, ["--no-check"])
        # The warning must land on stderr, not stdout.
        assert "warning" in result.stderr.lower()
        assert "--no-check" in result.stderr
        assert "bypasses semantic analysis" in result.stderr

    def test_absent_flag_produces_no_warning(self) -> None:
        src = _tiny_module('fn main() {\n    print("hello")\n}\n')
        result = _run_build_multi(src)
        assert "--no-check" not in result.stderr

    def test_warning_mentions_what_is_suppressed(self) -> None:
        """Reader must learn which classes of diagnostic are hidden."""
        src = _tiny_module('fn main() {\n    print("hello")\n}\n')
        result = _run_build_multi(src, ["--no-check"])
        stderr = result.stderr.lower()
        # At least one of the silenced diagnostic classes must be named.
        assert any(phrase in stderr for phrase in ("type error", "undefined symbol", "trait"))
