"""v5.32.0 Nw.3 — native binary fallback wrapper tests.

The Python ``__main__`` should detect a sibling ``bin/mnc[.exe]`` and
``os.execv`` to it, falling back to the Python entry only when missing.
``MAPANARE_FORCE_PYTHON=1`` opts out unconditionally so devs can keep
hitting the Python path while debugging.

Falsifiability: deleting either gate in ``mapanare/__main__.py``
(the existence check or the env-var bypass) flips one of these
tests RED.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _patch_pkg_dir(monkeypatch: pytest.MonkeyPatch, fake_pkg: Path) -> None:
    """Re-resolve ``__file__`` inside ``mapanare.__main__`` so the
    sibling-binary lookup walks our temp dir instead of the real
    install."""
    import mapanare.__main__ as main_mod

    monkeypatch.setattr(main_mod, "__file__", str(fake_pkg / "__main__.py"))


def test_native_binary_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAPANARE_FORCE_PYTHON", raising=False)
    fake_pkg = tmp_path / "mapanare"
    fake_pkg.mkdir()
    _patch_pkg_dir(monkeypatch, fake_pkg)

    from mapanare.__main__ import _native_binary

    assert _native_binary() is None


def test_native_binary_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAPANARE_FORCE_PYTHON", raising=False)
    fake_pkg = tmp_path / "mapanare"
    fake_pkg.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_name = "mnc.exe" if os.name == "nt" else "mnc"
    binary = bin_dir / bin_name
    binary.write_text("#!/bin/sh\necho fake-native\n")
    binary.chmod(0o755)
    _patch_pkg_dir(monkeypatch, fake_pkg)

    from mapanare.__main__ import _native_binary

    found = _native_binary()
    assert found is not None
    assert found.resolve() == binary.resolve()


def test_force_python_disables_native(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAPANARE_FORCE_PYTHON", "1")
    fake_pkg = tmp_path / "mapanare"
    fake_pkg.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_name = "mnc.exe" if os.name == "nt" else "mnc"
    (bin_dir / bin_name).write_text("x")
    _patch_pkg_dir(monkeypatch, fake_pkg)

    from mapanare.__main__ import _native_binary

    assert _native_binary() is None
