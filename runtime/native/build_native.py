"""Build the Mapanare native runtime shared library.

Uses cffi to compile mapanare_runtime.c into a loadable shared library.
Falls back to direct compiler invocation if cffi ABI mode is used.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

NATIVE_DIR = Path(__file__).parent
SRC = NATIVE_DIR / "mapanare_runtime.c"


def _lib_name() -> str:
    """Return the expected shared library file name for the current platform."""
    if platform.system() == "Windows":
        return "mapanare_runtime.dll"
    elif platform.system() == "Darwin":
        return "libmapanare_runtime.dylib"
    else:
        return "libmapanare_runtime.so"


def lib_path() -> Path:
    """Absolute path to the built shared library."""
    return NATIVE_DIR / _lib_name()


def build() -> Path:
    """Compile the native runtime and return the path to the shared library."""
    out = lib_path()
    system = platform.system()

    if system == "Windows":
        # Try MSVC first via a Developer Command Prompt helper
        _build_msvc(out)
    else:
        _build_gcc(out)

    if not out.exists():
        raise RuntimeError(f"Build failed — {out} not found")
    return out


def _build_msvc(out: Path) -> None:
    """Compile with MSVC cl.exe."""
    # Find vcvarsall.bat
    _vs_base = r"C:\Program Files\Microsoft Visual Studio"
    _vs_x86 = r"C:\Program Files (x86)\Microsoft Visual Studio"
    _vc_tail = r"VC\Auxiliary\Build\vcvarsall.bat"
    vs_paths = [
        rf"{_vs_base}\2022\Community\{_vc_tail}",
        rf"{_vs_base}\2022\Professional\{_vc_tail}",
        rf"{_vs_base}\2022\Enterprise\{_vc_tail}",
        rf"{_vs_x86}\2019\Community\{_vc_tail}",
    ]
    vcvars = None
    for vs_path in vs_paths:
        if os.path.exists(vs_path):
            vcvars = vs_path
            break

    if vcvars is None:
        raise RuntimeError("Cannot find vcvarsall.bat — install Visual Studio Build Tools")

    src = str(SRC).replace("/", "\\")
    dll = str(out).replace("/", "\\")

    # Build command: set up MSVC env, compile as DLL
    cmd = (
        f'"{vcvars}" x64 && '
        f"cl /nologo /O2 /LD /D_CRT_SECURE_NO_WARNINGS "
        f'"{src}" /Fe:"{dll}" /link /DLL'
    )

    subprocess.run(cmd, shell=True, check=True, cwd=str(NATIVE_DIR))

    # Clean up intermediate files
    for ext in [".obj", ".lib", ".exp"]:
        p = NATIVE_DIR / f"mapanare_runtime{ext}"
        if p.exists():
            p.unlink()


def _build_gcc(out: Path) -> None:
    """Compile with GCC/Clang."""
    cc = os.environ.get("CC", "cc")
    flags = ["-O2", "-shared", "-fPIC", "-pthread"]
    if platform.system() == "Darwin":
        flags.append("-dynamiclib")

    cmd = [cc] + flags + [str(SRC), "-o", str(out)]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    try:
        p = build()
        print(f"Built: {p}")
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
