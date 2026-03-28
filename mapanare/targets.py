"""Cross-compilation target definitions for the Mapanare compiler.

Phase 4.5: Defines supported target triples, their LLVM data layouts,
and helpers for selecting/resolving targets at compile time.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    """A compilation target with its LLVM triple and data layout."""

    triple: str
    data_layout: str
    description: str
    # Object file extension for the target
    obj_ext: str
    # Executable extension (empty string for ELF/Mach-O)
    exe_ext: str
    # Shared library extension
    lib_ext: str
    # Default linker to invoke
    linker: str


# ---------------------------------------------------------------------------
# Supported targets
# ---------------------------------------------------------------------------

TARGET_X86_64_LINUX_GNU = Target(
    triple="x86_64-unknown-linux-gnu",
    data_layout=(
        "e-m:e-p270:32:32-p271:32:32-p272:64:64-" "i64:64-i128:128-f80:128-n8:16:32:64-S128"
    ),
    description="Linux x86-64 (GNU)",
    obj_ext=".o",
    exe_ext="",
    lib_ext=".so",
    linker="cc",
)

TARGET_AARCH64_APPLE_MACOS = Target(
    triple="aarch64-apple-macos14.0",
    data_layout="e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32",
    description="macOS (ARM64 / Apple Silicon)",
    obj_ext=".o",
    exe_ext="",
    lib_ext=".dylib",
    linker="clang",
)

TARGET_X86_64_WINDOWS_GNU = Target(
    triple="x86_64-w64-windows-gnu",
    data_layout=(
        "e-m:w-p270:32:32-p271:32:32-p272:64:64-" "i64:64-i128:128-f80:128-n8:16:32:64-S128"
    ),
    description="Windows x86-64 (MinGW/GNU)",
    obj_ext=".o",
    exe_ext=".exe",
    lib_ext=".dll",
    linker="gcc",
)

TARGET_X86_64_WINDOWS_MSVC = Target(
    triple="x86_64-pc-windows-msvc",
    data_layout=(
        "e-m:w-p270:32:32-p271:32:32-p272:64:64-" "i64:64-i128:128-f80:128-n8:16:32:64-S128"
    ),
    description="Windows x86-64 (MSVC)",
    obj_ext=".obj",
    exe_ext=".exe",
    lib_ext=".dll",
    linker="link.exe",
)

TARGET_WASM32 = Target(
    triple="wasm32-unknown-unknown",
    data_layout="e-m:e-p:32:32-i64:64-n32:64-S128",
    description="WebAssembly (32-bit)",
    obj_ext=".o",
    exe_ext=".wasm",
    lib_ext=".wasm",
    linker="wasm-ld",
)

TARGET_WASM32_WASI = Target(
    triple="wasm32-wasi",
    data_layout="e-m:e-p:32:32-i64:64-n32:64-S128",
    description="WebAssembly + WASI",
    obj_ext=".o",
    exe_ext=".wasm",
    lib_ext=".wasm",
    linker="wasm-ld",
)

TARGET_AARCH64_APPLE_IOS = Target(
    triple="aarch64-apple-ios17.0",
    data_layout="e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32",
    description="iOS (ARM64)",
    obj_ext=".o",
    exe_ext="",
    lib_ext=".dylib",
    linker="clang",
)

TARGET_AARCH64_LINUX_ANDROID = Target(
    triple="aarch64-linux-android34",
    data_layout="e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128",
    description="Android (ARM64)",
    obj_ext=".o",
    exe_ext="",
    lib_ext=".so",
    linker="aarch64-linux-android34-clang",
)

TARGET_X86_64_LINUX_ANDROID = Target(
    triple="x86_64-linux-android34",
    data_layout=(
        "e-m:e-p270:32:32-p271:32:32-p272:64:64-" "i64:64-i128:128-f80:128-n8:16:32:64-S128"
    ),
    description="Android (x86_64, emulator)",
    obj_ext=".o",
    exe_ext="",
    lib_ext=".so",
    linker="x86_64-linux-android34-clang",
)

# Registry of all supported targets
TARGETS: dict[str, Target] = {
    "x86_64-linux-gnu": TARGET_X86_64_LINUX_GNU,
    "aarch64-apple-macos": TARGET_AARCH64_APPLE_MACOS,
    "x86_64-windows-msvc": TARGET_X86_64_WINDOWS_MSVC,
    "x86_64-windows-gnu": TARGET_X86_64_WINDOWS_GNU,
    "wasm32": TARGET_WASM32,
    "wasm32-wasi": TARGET_WASM32_WASI,
    "aarch64-apple-ios": TARGET_AARCH64_APPLE_IOS,
    "aarch64-linux-android": TARGET_AARCH64_LINUX_ANDROID,
    "x86_64-linux-android": TARGET_X86_64_LINUX_ANDROID,
}


def host_target_name() -> str:
    """Detect the host platform and return the matching target name."""
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Linux" and machine in ("x86_64", "amd64"):
        return "x86_64-linux-gnu"
    if system == "Darwin" and machine in ("arm64", "aarch64"):
        return "aarch64-apple-macos"
    if system == "Darwin" and machine in ("x86_64", "amd64"):
        # Fall back to x86_64 macOS using the linux layout (close enough for IR)
        return "x86_64-linux-gnu"
    if system == "Windows" and machine in ("x86_64", "amd64", "x86"):
        return "x86_64-windows-gnu"

    # Default fallback
    return "x86_64-linux-gnu"


def get_target(name: str | None = None) -> Target:
    """Resolve a target by name, or auto-detect from the host platform."""
    if name is None:
        name = host_target_name()
    if name not in TARGETS:
        valid = ", ".join(sorted(TARGETS.keys()))
        raise ValueError(f"Unknown target '{name}'. Valid targets: {valid}")
    return TARGETS[name]


def list_targets() -> list[tuple[str, str]]:
    """Return a list of (name, description) for all supported targets."""
    return [(name, t.description) for name, t in sorted(TARGETS.items())]
