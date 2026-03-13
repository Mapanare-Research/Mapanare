"""Build the Mapanare I/O runtime shared library.

Compiles mapanare_io.c into a loadable shared library for TCP, TLS,
file I/O, and event loop primitives.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

NATIVE_DIR = Path(__file__).parent
SRC = NATIVE_DIR / "mapanare_io.c"


def _lib_name() -> str:
    """Return the expected shared library file name for the current platform."""
    if platform.system() == "Windows":
        return "mapanare_io.dll"
    elif platform.system() == "Darwin":
        return "libmapanare_io.dylib"
    else:
        return "libmapanare_io.so"


def lib_path() -> Path:
    """Absolute path to the built shared library."""
    return NATIVE_DIR / _lib_name()


def build() -> Path:
    """Compile the I/O runtime and return the path to the shared library."""
    out = lib_path()
    system = platform.system()

    if system == "Windows":
        _build_msvc(out)
    else:
        _build_gcc(out)

    if not out.exists():
        raise RuntimeError(f"Build failed — {out} not found")
    return out


def _build_msvc(out: Path) -> None:
    """Compile with MSVC cl.exe."""
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

    cmd = (
        f'"{vcvars}" x64 && '
        f"cl /nologo /O2 /LD /D_CRT_SECURE_NO_WARNINGS "
        f'"{src}" /Fe:"{dll}" /link /DLL ws2_32.lib'
    )

    subprocess.run(cmd, shell=True, check=True, cwd=str(NATIVE_DIR))

    for ext in [".obj", ".lib", ".exp"]:
        p = NATIVE_DIR / f"mapanare_io{ext}"
        if p.exists():
            p.unlink()


def _build_gcc(out: Path) -> None:
    """Compile with GCC/Clang."""
    cc = os.environ.get("CC", "cc")
    flags = ["-O2", "-shared", "-fPIC", "-pthread"]
    if platform.system() == "Darwin":
        flags.append("-dynamiclib")

    # Link against dl for dlopen/dlsym (needed for OpenSSL dynamic loading)
    libs = ["-ldl"]

    cmd = [cc] + flags + [str(SRC), "-o", str(out)] + libs
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    try:
        p = build()
        print(f"Built: {p}")
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
