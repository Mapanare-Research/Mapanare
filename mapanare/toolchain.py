"""Host-toolchain discovery for `mapanare run` / `mapanare build`.

On Windows the PyInstaller bundle may ship a curated compiler SDK under
``<install>/sdk/`` (preferred) or ``<install>/llvm/`` (legacy naming). Older
bundles used ``<install>/toolchain/`` for w64devkit; keep that layout as a
fallback so old installs and local tests still work. When neither a bundled
SDK nor a system gcc/clang is on PATH, we fall back to well-known install
locations left by common package managers (winget, scoop, chocolatey).

On Linux and macOS the helpers just look at PATH — nothing is bundled.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Toolchain:
    """A concrete, invocable C toolchain."""

    name: str  # "gcc" | "clang"
    compiler: str  # absolute path to the C compiler
    clang: str | None  # absolute path to clang (for .ll compilation), if any
    bin_dir: str | None  # directory to prepend to PATH (for ld.exe, libgcc, etc.)
    rt_archive: str | None  # optional pre-built libmapanare_rt.a

    @property
    def needs_pthread_flag(self) -> bool:
        """Whether this toolchain needs `-lpthread` on the link line.

        MinGW-w64 / LLVM-MinGW on Windows use the Win32 threading layer in the
        runtime (HANDLE/CRITICAL_SECTION) — no pthread link. System gcc/clang
        on Linux/macOS do need it.
        """
        return os.name != "nt"

    @property
    def needs_libm_flag(self) -> bool:
        # libm is folded into the C runtime on Windows / macOS but separate on Linux.
        return os.name == "posix" and sys.platform != "darwin"


def _bundle_root() -> Path | None:
    """Return the directory that holds an optional bundled Windows SDK.

    Three situations:
      1. Running from a PyInstaller one-dir bundle: files live next to the exe.
      2. Running from a PyInstaller one-file bundle: ``sys._MEIPASS`` points at
         the extracted tmp dir, but our data files also live next to the exe.
      3. Running from source (``pip install -e .``): check alongside the
         package for a ``toolchain/`` — used for local testing.
    """
    # Running from a PyInstaller bundle
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if _has_bundled_sdk_root(exe_dir):
            return exe_dir
        # one-file build: _MEIPASS holds the extracted datas
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and _has_bundled_sdk_root(Path(meipass)):
            return Path(meipass)
        return None

    # Source install: repo-root/toolchain/ if someone staged one
    pkg_root = Path(__file__).resolve().parent.parent
    if (pkg_root / "toolchain").is_dir():
        return pkg_root

    return None


def _bundled_sdk_candidates(root: Path) -> list[Path]:
    """Candidate bundled compiler SDK bin directories, preferred first."""
    return [
        root / "sdk" / "bin",
        root / "llvm" / "bin",
        root / "toolchain" / "bin",
    ]


def _has_bundled_sdk_root(root: Path) -> bool:
    """Return True if root looks like a PyInstaller directory with an SDK."""
    return any(candidate.is_dir() for candidate in _bundled_sdk_candidates(root))


def _runtime_archive_for(root: Path, bin_dir: Path) -> Path | None:
    """Return the bundled libmapanare runtime archive for a SDK bin dir."""
    sdk_root = bin_dir.parent
    candidates = [
        sdk_root / "lib" / "mapanare" / "libmapanare_rt.a",
        sdk_root / "lib" / "libmapanare_rt.a",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _candidate_install_paths() -> list[str]:
    """Common Windows install locations for third-party toolchains.

    Checked in order. First gcc.exe or clang.exe wins.
    """
    if os.name != "nt":
        return []

    local = os.environ.get("LOCALAPPDATA", "")
    user_profile = os.environ.get("USERPROFILE", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")

    roots = [
        # User-initiated `mapanare install-toolchain` location (future).
        os.path.join(local, "mapanare", "toolchain", "bin"),
        # winget: LLVM-MinGW UCRT variants land here, exact version suffix varies.
        os.path.join(
            local,
            "Microsoft",
            "WinGet",
            "Packages",
        ),
        # scoop
        os.path.join(user_profile, "scoop", "apps", "mingw", "current", "bin"),
        os.path.join(user_profile, "scoop", "apps", "llvm-mingw", "current", "bin"),
        os.path.join(user_profile, "scoop", "apps", "llvm", "current", "bin"),
        # chocolatey / MSYS2
        r"C:\msys64\ucrt64\bin",
        r"C:\msys64\mingw64\bin",
        r"C:\ProgramData\mingw64\mingw64\bin",
        # LLVM installer default
        os.path.join(program_files, "LLVM", "bin"),
    ]
    return roots


def _winget_glob(winget_root: str) -> list[str]:
    """Expand the winget Packages root into per-package bin/ subdirs.

    winget buries binaries under
    ``WinGet/Packages/<Publisher.Name.Source_hash>/<version-dir>/bin``.
    We don't know the version suffix ahead of time, so glob one level deep.
    """
    if not os.path.isdir(winget_root):
        return []
    out: list[str] = []
    # Match a couple of known publishers that ship gcc/clang.
    for pkg in os.listdir(winget_root):
        pkg_lower = pkg.lower()
        if not any(token in pkg_lower for token in ("mingw", "llvm", "msys", "clang")):
            continue
        pkg_path = os.path.join(winget_root, pkg)
        if not os.path.isdir(pkg_path):
            continue
        # Inner version dir, then optional nested bin/.
        for entry in os.listdir(pkg_path):
            inner = os.path.join(pkg_path, entry)
            if not os.path.isdir(inner):
                continue
            bin_dir = os.path.join(inner, "bin")
            if os.path.isdir(bin_dir):
                out.append(bin_dir)
    return out


def _probe_compiler(path: str) -> bool:
    """Return True if ``path`` can actually be launched on this host.

    Catches wrong-architecture installs (e.g. an ARM64 clang on an x64 Windows
    box — WinError 216) that would otherwise crash deep in subprocess.run.
    """
    import subprocess

    try:
        res = subprocess.run(
            [path, "--version"],
            capture_output=True,
            timeout=10,
        )
        return res.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _compiler_filenames(name: str) -> list[str]:
    """Return platform-preferred executable filenames for a compiler name."""
    suffixes = [".exe", ""] if os.name == "nt" else ["", ".exe"]
    out: list[str] = []
    for suffix in suffixes:
        filename = name + suffix
        if filename not in out:
            out.append(filename)
    return out


def _search_dir_for_compiler(
    bin_dir: str,
    names: tuple[str, ...] = ("gcc", "clang"),
) -> tuple[str, str] | None:
    """Return (name, absolute_path) if a runnable compiler lives in bin_dir."""
    if not os.path.isdir(bin_dir):
        return None
    for name in names:
        for filename in _compiler_filenames(name):
            candidate = os.path.join(bin_dir, filename)
            if os.path.isfile(candidate) and _probe_compiler(candidate):
                return (name, candidate)
    return None


def _clang_sibling(compiler_path: str, compiler_name: str) -> str | None:
    """Return path to clang.exe sitting next to ``compiler_path``, if present.

    LLVM-MinGW ships both gcc.exe (a wrapper) and clang.exe in the same bin/.
    Real MinGW-w64 ships only gcc. We need clang specifically to compile the
    LLVM IR that ``mapanare build`` emits.
    """
    if compiler_name == "clang":
        return compiler_path
    bin_dir = os.path.dirname(compiler_path)
    for filename in _compiler_filenames("clang"):
        cand = os.path.join(bin_dir, filename)
        if os.path.isfile(cand) and _probe_compiler(cand):
            return cand
    # Search PATH as a last resort.
    fallback = shutil.which("clang")
    if fallback and _probe_compiler(fallback):
        return fallback
    return None


def detect_toolchain() -> Toolchain | None:
    """Locate a usable C toolchain.

    Order:
      1. Bundled ``sdk/`` or ``llvm/`` alongside the Mapanare install.
         Legacy ``toolchain/`` is kept as the last bundled fallback.
      2. System PATH (``gcc`` then ``clang``).
      3. Well-known install roots (winget, scoop, msys2, chocolatey, LLVM).

    The bundled SDK comes first so a stray system MinGW on PATH cannot shadow
    the curated compiler + ``libmapanare_rt.a`` we ship next to the
    PyInstaller bundle. Without bundled-wins, an end user with ``C:/mingw64``
    on PATH could link against a compiler that has no runtime archive,
    producing ``undefined reference to __mn_str_*``.

    Returns ``None`` if nothing works. Callers should print install guidance.
    """
    # 1. Bundled toolchain
    root = _bundle_root()
    if root is not None:
        for sdk_bin in _bundled_sdk_candidates(root):
            bundle_bin = str(sdk_bin)
            # SDK bundles should use clang. Legacy toolchain/ may only have gcc.
            names = ("clang", "gcc") if sdk_bin.parent.name != "toolchain" else ("gcc", "clang")
            hit = _search_dir_for_compiler(bundle_bin, names=names)
            if not hit:
                continue
            name, path = hit
            rt = _runtime_archive_for(root, sdk_bin)
            return Toolchain(
                name=name,
                compiler=path,
                clang=_clang_sibling(path, name),
                bin_dir=bundle_bin,
                rt_archive=str(rt) if rt else None,
            )

    # 2. System PATH
    for name in ("gcc", "clang"):
        found = shutil.which(name)
        if found and _probe_compiler(found):
            return Toolchain(
                name=name,
                compiler=found,
                clang=_clang_sibling(found, name),
                bin_dir=None,
                rt_archive=None,
            )

    # 3. Known install roots (Windows-only)
    for root_path in _candidate_install_paths():
        # Expand winget root before probing.
        if root_path.endswith(os.path.join("WinGet", "Packages")):
            for inner_bin in _winget_glob(root_path):
                hit = _search_dir_for_compiler(inner_bin)
                if hit:
                    name, compiler = hit
                    return Toolchain(
                        name=name,
                        compiler=compiler,
                        clang=_clang_sibling(compiler, name),
                        bin_dir=inner_bin,
                        rt_archive=None,
                    )
            continue

        hit = _search_dir_for_compiler(root_path)
        if hit:
            name, compiler = hit
            return Toolchain(
                name=name,
                compiler=compiler,
                clang=_clang_sibling(compiler, name),
                bin_dir=root_path,
                rt_archive=None,
            )

    return None


def invocation_env(tc: Toolchain) -> dict[str, str] | None:
    """Return an os.environ snapshot with the toolchain's bin/ prepended.

    Needed on Windows so the compiler can find its own ld.exe, libgcc_s_seh-1.dll,
    libwinpthread-1.dll, etc. Returns ``None`` if no PATH tweaking is required.
    """
    if not tc.bin_dir:
        return None
    env = os.environ.copy()
    sep = os.pathsep
    env["PATH"] = tc.bin_dir + sep + env.get("PATH", "")
    return env


def install_instructions() -> str:
    """User-facing hint when we can't find any compiler."""
    if os.name == "nt":
        return (
            "install one of the following to compile and run .mn files:\n"
            "  - winget install MartinStorsjo.LLVM-MinGW.UCRT   (recommended)\n"
            "  - winget install BrechtSanders.WinLibs.POSIX.UCRT\n"
            "  - w64devkit: https://github.com/skeeto/w64devkit/releases\n"
            "  - MSYS2:     https://www.msys2.org (then `pacman -S mingw-w64-ucrt-x86_64-gcc`)\n"
            "\n"
            "alternatively, use 'mapanare check' to type-check without compiling,\n"
            "or 'mapanare emit-llvm' / 'mapanare emit-c' to view generated code."
        )
    return (
        "install gcc or clang to compile and run .mn files\n"
        "\n"
        "alternatively, use 'mapanare check' to type-check without compiling,\n"
        "or 'mapanare emit-llvm' / 'mapanare emit-c' to view generated code."
    )
