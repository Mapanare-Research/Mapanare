#!/usr/bin/env python3
"""Build the Stage 1 self-hosted compiler binary (mnc-stage1).

Pipeline:
    1. Compile mapanare/self/*.mn (10 modules) -> LLVM IR via Python bootstrap
    2. Post-process IR: make compile() externally visible
    3. Compile IR -> native object code
    4. Compile C runtime (mapanare_core.c + mapanare_io.c + mapanare_gpu.c)
    5. Compile C main wrapper (mnc_main.c)
    6. Link: main wrapper + compiler object + C runtime -> mnc-stage1
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

CC = os.environ.get("CC", "gcc")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SELF_DIR = ROOT / "mapanare" / "self"
NATIVE_DIR = ROOT / "runtime" / "native"
VERSION_FILE = ROOT / "VERSION"

# v4.28.0: build-time placeholder in ``mapanare/self/main.mn`` that the
# build substitutes from the top-level ``VERSION`` file. Prior to this,
# the self-hosted ``version()`` function returned a hardcoded string that
# became 19 minor versions stale because the manual bump step was dropped
# at v4.8.0. See ``docs/roadmap/v4/v4.28.0/FORENSICS.md``.
VERSION_PLACEHOLDER = "__MN_VERSION__"


def _substitute_version(source: str) -> str:
    """Replace the ``__MN_VERSION__`` placeholder with the live VERSION contents.

    Called on the self-hosted source text before it reaches the compiler.
    The placeholder must occur; a missing placeholder is a build error so
    that no future edit can silently unwire the substitution.
    """
    if VERSION_PLACEHOLDER not in source:
        raise SystemExit(
            f"error: {VERSION_PLACEHOLDER!r} placeholder not found in self-hosted "
            "source. Re-add it to mapanare/self/main.mn:version() — see "
            "docs/roadmap/v4/v4.28.0/FORENSICS.md for why this matters."
        )
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit(f"error: {VERSION_FILE} is empty")
    return source.replace(VERSION_PLACEHOLDER, version)


def build() -> pathlib.Path:
    """Build mnc-stage1 and return its path."""
    print("=== Stage 1: Building self-hosted compiler ===")

    ir_path = SELF_DIR / "main.ll"

    # Dr.1 (v4.139.0): substitute __MN_VERSION__ in all self-hosted modules
    # so the multi-module compiler sees the real version in emit_llvm.mn etc.
    restored: dict[pathlib.Path, str] = {}
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    for mn_file in sorted(SELF_DIR.glob("*.mn")):
        text = mn_file.read_text(encoding="utf-8")
        if VERSION_PLACEHOLDER in text:
            restored[mn_file] = text
            mn_file.write_text(text.replace(VERSION_PLACEHOLDER, version), encoding="utf-8")

    if "--use-committed" in sys.argv:
        print("[1/6] Using committed LLVM IR (--use-committed) ...")
        ir = ir_path.read_text(encoding="utf-8")
        print(f"  IR: {ir.count(chr(10))} lines <- {ir_path}")
        for path, original in restored.items():
            path.write_text(original, encoding="utf-8")
    else:
        print("[1/6] Generating LLVM IR from mapanare/self/*.mn ...")
        from mapanare.multi_module import compile_multi_module_mir

        source = (SELF_DIR / "main.mn").read_text(encoding="utf-8")
        try:
            ir = compile_multi_module_mir(
                root_source=source,
                root_file=str(SELF_DIR / "main.mn"),
                opt_level=2,
                skip_check=True,
            )
        finally:
            for path, original in restored.items():
                path.write_text(original, encoding="utf-8")

    # 2. Post-process: make compile() and format_error() externally visible
    print("[2/6] Post-processing IR (external linkage for entry points) ...")
    # Remove 'internal' linkage from ALL function definitions.
    # LLVM -O2 dead-code-eliminates internal functions it considers
    # unreachable, but with sret calling conventions it sometimes
    # misjudges reachability, stripping functions that ARE called.
    ir = ir.replace("define internal ", "define ")

    # Fix target triple if building on a different platform than where
    # the IR was committed (e.g., committed on Linux x86_64, building on macOS ARM64).
    import platform

    if sys.platform == "darwin":
        arch = platform.machine()  # arm64 or x86_64
        host_triple = f"{arch}-apple-macos"
        ir = ir.replace(
            'target triple = "x86_64-unknown-linux-gnu"',
            f'target triple = "{host_triple}"',
        )
        # Also fix datalayout for ARM64
        if arch == "arm64":
            linux_x86_dl = (
                'target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64'
                '-i64:64-i128:128-f80:128-n8:16:32:64-S128"'
            )
            mac_arm64_dl = 'target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128-Fn32"'
            ir = ir.replace(linux_x86_dl, mac_arm64_dl)
    elif sys.platform == "win32":
        ir = ir.replace(
            'target triple = "x86_64-unknown-linux-gnu"',
            'target triple = "x86_64-pc-windows-msvc"',
        )

    ir_path.write_text(ir, encoding="utf-8")
    print(f"  IR: {ir.count(chr(10))} lines -> {ir_path}")

    # 3. Compile IR to object code
    print("[3/6] Compiling LLVM IR -> object code ...")
    obj_path = SELF_DIR / "main.o"

    # Prefer clang for IR->object compilation.  The text emitter generates
    # UB-free alloca-based IR that is safe at all optimization levels.
    # -O2 produces a 6.7x smaller binary with ~30x faster compile times.
    import shutil

    clang_bin = shutil.which("clang")
    if not clang_bin:
        print("error: clang not found. Install LLVM/clang to compile IR to object code.")
        sys.exit(1)
    opt_flag = "-O2"
    subprocess.run(
        [clang_bin, "-c", opt_flag, str(ir_path), "-o", str(obj_path)],
        check=True,
        capture_output=True,
    )
    print(f"  Object: {obj_path.stat().st_size} bytes -> {obj_path} (clang {opt_flag})")

    # 4. Compile C runtime
    # v4.29.0: ``mapanare_db.c`` (1,130 lines, SQLite/Postgres/Redis +
    # extended filesystem) and ``mapanare_html.c`` (812 lines, HTML parser
    # + time/env/URL helpers) are now compiled and linked into every
    # mnc-stage1 build. Previously they were orphaned — 1,942 lines of
    # runtime code that no CI job touched (v4.26.0 panel: Anaconda HIGH).
    print("[4/6] Compiling C runtime ...")
    # Core modules needed by the native compiler on all platforms
    runtime_sources: list[tuple[pathlib.Path, pathlib.Path]] = [
        (NATIVE_DIR / "mapanare_core.c", SELF_DIR / "mapanare_core.o"),
        (NATIVE_DIR / "mapanare_runtime.c", SELF_DIR / "mapanare_runtime.o"),
        (NATIVE_DIR / "mapanare_gpu.c", SELF_DIR / "mapanare_gpu.o"),
        (NATIVE_DIR / "mapanare_gpu_builtins.c", SELF_DIR / "mapanare_gpu_builtins.o"),
    ]
    # These modules use POSIX-only APIs (opendir, dlopen, etc.) — skip on Windows
    if sys.platform != "win32":
        runtime_sources += [
            (NATIVE_DIR / "mapanare_io.c", SELF_DIR / "mapanare_io.o"),
            (NATIVE_DIR / "mapanare_db.c", SELF_DIR / "mapanare_db.o"),
            (NATIVE_DIR / "mapanare_html.c", SELF_DIR / "mapanare_html.o"),
        ]
    # macOS: compile Metal backend (Objective-C, provides GPU symbols)
    if sys.platform == "darwin":
        metal_src = NATIVE_DIR / "mapanare_metal.m"
        metal_obj = SELF_DIR / "mapanare_metal.o"
        if metal_src.exists():
            runtime_sources.append((metal_src, metal_obj))
    asan_flags = ["-fsanitize=address", "-fno-omit-frame-pointer"] if "--asan" in sys.argv else []
    profile_flags = ["-DMN_PROFILE_MEM"] if "--profile-mem" in sys.argv else []
    # v4.31.0: propagate the VERSION file contents into a compile-time
    # ``MAPANARE_VERSION`` macro. ``mapanare_io.c`` uses this to build
    # the User-Agent string for ``__mn_http_get``; prior to v4.31.0
    # the string was hardcoded as ``Mapanare/3.42`` and five minors
    # stale (Mamba, v4.26.0 panel).
    version_str = VERSION_FILE.read_text(encoding="utf-8").strip()
    version_flags = [f'-DMAPANARE_VERSION="{version_str}"']
    c_base_flags = [
        CC,
        "-c",
        "-O2",
        "-g",
        "-fPIC",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(NATIVE_DIR),
    ] + version_flags
    for src, obj in runtime_sources:
        extra = profile_flags if src.name == "mapanare_core.c" else []
        if src.suffix == ".m":
            extra = extra + ["-fobjc-arc"]
        subprocess.run(
            c_base_flags + asan_flags + extra + [str(src), "-o", str(obj)],
            check=True,
        )
    print(f"  Runtime: {', '.join(str(o) for _, o in runtime_sources)}")

    # 5. Compile main wrapper
    print("[5/6] Compiling C main wrapper ...")
    main_c = SELF_DIR / "mnc_main.c"
    main_o = SELF_DIR / "mnc_main.o"
    subprocess.run(
        [CC, "-c", "-O2", "-g"] + asan_flags + [str(main_c), "-o", str(main_o)],
        check=True,
    )
    print(f"  Wrapper: {main_o}")

    # 6. Link
    print("[6/6] Linking mnc-stage1 ...")
    binary = SELF_DIR / "mnc-stage1"
    if sys.platform == "win32":
        link_flags = [
            "-lm",
            "-Wl,--stack,67108864",  # 64MB stack for deep recursion on Windows
        ]
    elif sys.platform == "darwin":
        link_flags = [
            "-lm",
            "-lpthread",
            "-framework",
            "Metal",
            "-framework",
            "Foundation",
            "-fobjc-arc",
            "-Wl,-stack_size,0x4000000",  # 64MB stack for deep recursion on macOS
        ]
    else:
        link_flags = [
            "-no-pie",
            "-rdynamic",
            "-lm",
            "-lpthread",
            "-ldl",
            "-Wl,-z,stacksize=67108864",  # 64MB stack for deep recursion on Linux
        ]

    runtime_objects = [obj for _, obj in runtime_sources]
    subprocess.run(
        [
            CC,
            "-o",
            str(binary),
            str(main_o),
            str(obj_path),
            *(str(o) for o in runtime_objects),
        ]
        + link_flags
        + asan_flags,
        check=True,
    )
    unstripped_size = binary.stat().st_size
    print(f"  Binary: {binary} ({unstripped_size} bytes)")

    # v4.33.0 Phase 4.2 (Mamba): strip the binary to reduce size.
    # Default on; set STRIP=0 to keep debug symbols for development.
    if os.environ.get("STRIP", "1") != "0":
        import shutil

        strip_bin = shutil.which("strip")
        if strip_bin:
            subprocess.run([strip_bin, str(binary)], check=True, capture_output=True)
            stripped_size = binary.stat().st_size
            pct = 100.0 * (1.0 - stripped_size / unstripped_size) if unstripped_size else 0
            print(f"  Stripped: {stripped_size} bytes ({pct:.0f}% reduction)")

    # Cleanup intermediate .o files
    for f in [main_o, obj_path, *runtime_objects]:
        if f.exists():
            f.unlink()

    return binary


if __name__ == "__main__":
    try:
        binary = build()
        print(f"\n=== Success: {binary} ===")
    except Exception as e:
        print(f"\n=== Build failed: {e} ===", file=sys.stderr)
        sys.exit(1)
