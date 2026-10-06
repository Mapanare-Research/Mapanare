"""Cross-platform link helpers for tests that link against
``runtime/native/libmapanare_rt.a``.

The runtime archive bundles ``mapanare_metal.o`` on Darwin (per the
v5.8.8 Da.2 Makefile fix). That object file calls into the Metal /
Foundation / CoreFoundation Objective-C runtimes, so any link line
that consumes the archive on macOS must add the matching frameworks
or the link fails with ``Undefined symbols for architecture arm64:
_MTLCreateSystemDefaultDevice`` (and friends).

``tests/integration/conftest.py`` already does this for the
integration pipeline; this module shares the same fragment with the
LLVM / runtime test files that don't go through that conftest.
"""

from __future__ import annotations

import os
import sys


def darwin_link_extras() -> list[str]:
    """Extra linker args required on Darwin to satisfy mapanare_metal.o.

    Returns ``[]`` on every other platform so callers can splat the
    result unconditionally.
    """
    if sys.platform == "darwin":
        return ["-framework", "Metal", "-framework", "Foundation", "-fobjc-arc"]
    return []


def asan_env(detect_leaks: bool = True) -> dict[str, str]:
    """Build an env overlay for ASan tests.

    macOS's libclang_rt.asan does not support ``detect_leaks`` — setting
    it to 1 aborts the binary at startup with rc=-6. Tests that want
    leak detection on Linux but tolerate macOS's missing support should
    use this helper instead of hardcoding ``ASAN_OPTIONS=detect_leaks=1``.
    """
    env = os.environ.copy()
    if detect_leaks and sys.platform != "darwin":
        env["ASAN_OPTIONS"] = "detect_leaks=1"
    return env


def whole_archive_args(archive_path: str) -> list[str]:
    """``--whole-archive`` equivalent that works on macOS too.

    GNU ld uses ``-Wl,--whole-archive ARCHIVE -Wl,--no-whole-archive``;
    macOS ld64 uses ``-Wl,-force_load,ARCHIVE``. Returns the appropriate
    fragment for the current platform.
    """
    if sys.platform == "darwin":
        return [f"-Wl,-force_load,{archive_path}"]
    return ["-Wl,--whole-archive", archive_path, "-Wl,--no-whole-archive"]
