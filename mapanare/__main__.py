"""Allow running Mapanare as ``python -m mapanare``.

v5.32.0 Nw.3: when a sibling native ``mnc[.exe]`` binary is present (shipped
by the Windows SDK ZIP or copied into the install layout), prefer it over
the Python bootstrap. Set ``MAPANARE_FORCE_PYTHON=1`` to opt out for dev or
debug. The Python path remains the fallback for clean clones and broken
installs.

v5.33.0 Nu.5: ``_native_binary_name()`` extracted so the suffix-selection
logic is testable without monkeypatching ``os.name`` globally (which would
force pathlib to instantiate WindowsPath on Linux hosts and crash).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _native_binary_name(os_name: str | None = None) -> str:
    """Return the platform-specific native binary filename.

    ``os_name`` defaults to ``os.name`` so callers in tests can pin
    the value without disturbing pathlib's global view.
    """
    name = os.name if os_name is None else os_name
    return "mnc.exe" if name == "nt" else "mnc"


def _native_binary() -> Path | None:
    """Locate a sibling native compiler, if installed."""
    if os.environ.get("MAPANARE_FORCE_PYTHON") == "1":
        return None
    pkg_dir = Path(__file__).resolve().parent
    name = _native_binary_name()
    for candidate in (pkg_dir.parent / "bin" / name,):
        if candidate.is_file():
            return candidate
    return None


def _exec_native_if_present() -> None:
    binary = _native_binary()
    if binary is None:
        return
    os.execv(str(binary), [str(binary), *sys.argv[1:]])


if __name__ == "__main__":
    _exec_native_if_present()
    from mapanare.cli import main

    main()
