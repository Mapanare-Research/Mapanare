"""Allow running Mapanare as ``python -m mapanare``.

v5.32.0 Nw.3: when a sibling native ``mnc[.exe]`` binary is present (shipped
by the Windows SDK ZIP or copied into the install layout), prefer it over
the Python bootstrap. Set ``MAPANARE_FORCE_PYTHON=1`` to opt out for dev or
debug. The Python path remains the fallback for clean clones and broken
installs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _native_binary() -> Path | None:
    """Locate a sibling native compiler, if installed."""
    if os.environ.get("MAPANARE_FORCE_PYTHON") == "1":
        return None
    pkg_dir = Path(__file__).resolve().parent
    name = "mnc.exe" if os.name == "nt" else "mnc"
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
