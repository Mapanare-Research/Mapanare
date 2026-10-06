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


# v5.33.0 Nu.5: cross-platform suffix-selection lock. The host-coupled
# ``test_native_binary_present`` above only exercises the host's branch
# of the ``os.name == "nt"`` ternary in ``_native_binary_name``. This
# case pins both branches independent of host: a Linux CI worker
# validates the Windows ``mnc.exe`` selection, and a Windows CI worker
# validates the Linux/macOS ``mnc`` selection. A regression that
# hardcodes the wrong suffix at one of the four platform tarballs
# (Linux x64, macOS arm64, Windows x64, plus future v5.34.0+
# Linux aarch64 / macOS x86_64) would surface here.
#
# We can't monkeypatch ``os.name`` globally — pathlib reads it during
# ``Path(...)`` construction and on Linux it raises NotImplementedError
# when asked to instantiate WindowsPath. v5.33.0 extracts
# ``_native_binary_name(os_name=...)`` so the suffix logic is testable
# without disturbing pathlib.
@pytest.mark.parametrize(
    "fake_os_name,expected_bin",
    [
        ("posix", "mnc"),  # Linux + macOS
        ("nt", "mnc.exe"),  # Windows
    ],
)
def test_native_binary_suffix_per_platform(fake_os_name: str, expected_bin: str) -> None:
    """The wrapper's suffix selection must depend only on os.name."""
    from mapanare.__main__ import _native_binary_name

    assert _native_binary_name(os_name=fake_os_name) == expected_bin
