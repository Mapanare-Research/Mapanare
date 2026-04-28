"""Smoke test: native CLI --help and version surface.

v5.9.0 DX.1 + DX.2. Catches drift between mapanare/self/main.mn dispatch
and the help text that documents it; asserts the version export is wired
so the published binary never ships ``__MN_VERSION__`` as the literal.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MNC = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_help_flag_works() -> None:
    r = subprocess.run([str(MNC), "--help"], capture_output=True, text=True)
    assert r.returncode == 0, f"--help should exit 0, got {r.returncode}"
    assert "Usage:" in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_short_help_flag() -> None:
    r = subprocess.run([str(MNC), "-h"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_help_subcommand_word() -> None:
    r = subprocess.run([str(MNC), "help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
@pytest.mark.parametrize("subcmd", ["build", "run", "test", "cache", "compile"])
def test_help_mentions_each_subcommand(subcmd: str) -> None:
    r = subprocess.run([str(MNC), "--help"], capture_output=True, text=True)
    assert subcmd in r.stdout, f"--help text missing subcommand: {subcmd}"


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
@pytest.mark.parametrize("subcmd", ["build", "run", "test", "cache", "compile"])
def test_per_subcommand_help_via_help_word(subcmd: str) -> None:
    r = subprocess.run([str(MNC), "help", subcmd], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert subcmd in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
@pytest.mark.parametrize("subcmd", ["build", "run", "test", "cache", "compile"])
def test_per_subcommand_help_via_dash_dash_help(subcmd: str) -> None:
    r = subprocess.run([str(MNC), subcmd, "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert subcmd in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_version_no_placeholder() -> None:
    """v5.9.0 DX.2: version must NOT contain the legacy __MN_VERSION__ literal."""
    r = subprocess.run([str(MNC), "version"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "__MN_VERSION__" not in r.stdout, (
        f"version output still contains the placeholder: {r.stdout!r}. "
        "DX.2 wires __mn_version_string() in the C runtime; if the literal "
        "leaks through, the build flag is missing on the relevant clang/gcc step."
    )
    assert "mapanare" in r.stdout.lower()


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_version_dash_dash_form() -> None:
    r = subprocess.run([str(MNC), "--version"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "__MN_VERSION__" not in r.stdout
