"""Build the Mapanare GPU runtime shared library.

Compiles mapanare_gpu.c (+ mapanare_runtime.c for tensor fallbacks) into
a loadable shared library. Links against dl (Linux) for dlopen, or uses
LoadLibrary (Windows) which requires no extra link flags.

No compile-time dependency on CUDA or Vulkan SDKs — all GPU functions
are loaded at runtime via dlopen / LoadLibrary. If CUDA or Vulkan SDK
headers are found on the system, they are NOT used; we define our own
minimal typedefs for full portability.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

NATIVE_DIR = Path(__file__).parent
GPU_SRC = NATIVE_DIR / "mapanare_gpu.c"
RUNTIME_SRC = NATIVE_DIR / "mapanare_runtime.c"


def _lib_name() -> str:
    """Return the expected shared library file name for the current platform."""
    if platform.system() == "Windows":
        return "mapanare_gpu.dll"
    elif platform.system() == "Darwin":
        return "libmapanare_gpu.dylib"
    else:
        return "libmapanare_gpu.so"


def lib_path() -> Path:
    """Absolute path to the built shared library."""
    return NATIVE_DIR / _lib_name()


def _find_cuda_include() -> str | None:
    """Try to locate CUDA SDK include directory (optional, for type checking only)."""
    candidates = []
    cuda_path = os.environ.get("CUDA_PATH") or os.environ.get("CUDA_HOME")
    if cuda_path:
        candidates.append(os.path.join(cuda_path, "include"))

    if platform.system() == "Windows":
        candidates.extend(
            [
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\include",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.7\include",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/local/cuda/include",
                "/usr/include",
                "/opt/cuda/include",
            ]
        )

    for path in candidates:
        if os.path.isfile(os.path.join(path, "cuda.h")):
            return path
    return None


def _find_vulkan_include() -> str | None:
    """Try to locate Vulkan SDK include directory (optional)."""
    vulkan_sdk = os.environ.get("VULKAN_SDK")
    if vulkan_sdk:
        inc = os.path.join(vulkan_sdk, "include")
        if os.path.isdir(inc):
            return inc

    candidates = []
    if platform.system() == "Windows":
        candidates.extend(
            [
                r"C:\VulkanSDK\include",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/include",
                "/usr/local/include",
            ]
        )

    for path in candidates:
        if os.path.isfile(os.path.join(path, "vulkan", "vulkan.h")):
            return path
    return None


def build() -> Path:
    """Compile the GPU runtime and return the path to the shared library."""
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

    gpu_src = str(GPU_SRC).replace("/", "\\")
    runtime_src = str(RUNTIME_SRC).replace("/", "\\")
    dll = str(out).replace("/", "\\")

    # Optional: add CUDA/Vulkan include paths if found
    extra_includes = ""
    cuda_inc = _find_cuda_include()
    if cuda_inc:
        extra_includes += f' /I"{cuda_inc}"'
    vulkan_inc = _find_vulkan_include()
    if vulkan_inc:
        extra_includes += f' /I"{vulkan_inc}"'

    cmd = (
        f'"{vcvars}" x64 && '
        f"cl /nologo /O2 /LD /D_CRT_SECURE_NO_WARNINGS{extra_includes} "
        f'"{runtime_src}" "{gpu_src}" /Fe:"{dll}" /link /DLL'
    )

    subprocess.run(cmd, shell=True, check=True, cwd=str(NATIVE_DIR))

    # Clean up intermediate files
    for ext in [".obj", ".lib", ".exp"]:
        p = NATIVE_DIR / f"mapanare_gpu{ext}"
        if p.exists():
            p.unlink()
        p = NATIVE_DIR / f"mapanare_runtime{ext}"
        if p.exists():
            p.unlink()


def _build_gcc(out: Path) -> None:
    """Compile with GCC/Clang."""
    cc = os.environ.get("CC", "cc")
    flags = ["-O2", "-shared", "-fPIC", "-pthread"]
    if platform.system() == "Darwin":
        flags.append("-dynamiclib")

    # Optional include paths
    cuda_inc = _find_cuda_include()
    if cuda_inc:
        flags.extend(["-I", cuda_inc])
    vulkan_inc = _find_vulkan_include()
    if vulkan_inc:
        flags.extend(["-I", vulkan_inc])

    # Link against dl for dlopen/dlsym
    libs = ["-ldl"]
    if platform.system() == "Darwin":
        # macOS doesn't need -ldl (it's in libSystem)
        libs = []

    cmd = [cc] + flags + [str(RUNTIME_SRC), str(GPU_SRC), "-o", str(out)] + libs
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    try:
        p = build()
        print(f"Built: {p}")
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
