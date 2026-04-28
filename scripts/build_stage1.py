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
import shutil as _shutil
import subprocess
import sys
import tempfile

# Use the same compiler for C runtime and IR to avoid ABI mismatches.
# On macOS, `gcc` is Apple Clang while LLVM IR is compiled with Homebrew
# clang-18 — different ABIs cause struct layout corruption at runtime.
#
# Prefer gcc on Windows: system LLVM clang there defaults to the
# x86_64-pc-windows-msvc target, where MSVC's UCRT marks fopen and
# strncpy as deprecated and -Werror blows up. w64devkit's MinGW gcc
# has clean headers. On macOS / Linux keep clang first to avoid the
# Apple-Clang vs Homebrew-clang ABI mismatch documented above.
if sys.platform == "win32":
    CC = os.environ.get("CC", _shutil.which("gcc") or _shutil.which("clang") or "gcc")
else:
    CC = os.environ.get("CC", _shutil.which("clang") or "gcc")

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

    # v5.0.6 Dr.1-mutation: compile from a tempdir copy of SELF_DIR so the
    # source tree is never mutated. Prior pattern substituted __MN_VERSION__
    # in-place under try/finally — if the restore itself crashed (e.g. due
    # to a killed process during a long build) the tree was left corrupt.
    # The tempdir pattern makes substitution purely local, auto-cleaned.
    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    if "--use-committed" in sys.argv:
        print("[1/6] Using committed LLVM IR (--use-committed) ...")
        ir = ir_path.read_text(encoding="utf-8")
        print(f"  IR: {ir.count(chr(10))} lines <- {ir_path}")
    else:
        print("[1/6] Generating LLVM IR from mapanare/self/*.mn ...")
        from mapanare.multi_module import compile_multi_module_mir

        with tempfile.TemporaryDirectory(prefix="mn_build_") as td:
            build_src = pathlib.Path(td)
            # Mirror every .mn file into the tempdir, substituting the
            # version placeholder on the way in. The multi-module resolver
            # walks imports relative to `root_file`, so keeping everything
            # in a single flat tempdir mirrors SELF_DIR's layout exactly.
            for mn_file in sorted(SELF_DIR.glob("*.mn")):
                text = mn_file.read_text(encoding="utf-8")
                (build_src / mn_file.name).write_text(
                    text.replace(VERSION_PLACEHOLDER, version),
                    encoding="utf-8",
                )
            root_file = build_src / "main.mn"
            source = root_file.read_text(encoding="utf-8")
            ir = compile_multi_module_mir(
                root_source=source,
                root_file=str(root_file),
                opt_level=2,
                skip_check=True,
            )

    # 2. Post-process: make compile() and format_error() externally visible
    print("[2/6] Post-processing IR (external linkage for entry points) ...")
    # Remove 'internal' linkage from ALL function definitions.
    # LLVM -O2 dead-code-eliminates internal functions it considers
    # unreachable, but with sret calling conventions it sometimes
    # misjudges reachability, stripping functions that ARE called.
    ir = ir.replace("define internal ", "define ")

    # v5.8.8 Da.1: triple + datalayout are now plumbed through
    # ``compile_multi_module_mir(target_name=None)`` —
    # ``get_target(host_target_name())`` resolves the host target and
    # the emitter writes correct ``target triple`` + ``target
    # datalayout`` lines directly into the IR. The previous post-emit
    # text-patch (Linux→Apple/Windows triple replacement) was a hack
    # on top of an emit pipeline that already supports per-target
    # emission; removing it eliminates a structural inconsistency
    # that masked the v5.8.7 macOS arm64 ABI bug. See
    # docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md.

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
    clang_extra: list[str] = []
    if sys.platform == "win32":
        # Disable stack probing on Windows. Clang normally emits ``__chkstk``
        # calls for functions with large stack frames; that symbol is only
        # provided by MSVC's CRT, not by MinGW's libgcc, which instead
        # supplies ``___chkstk_ms``. We already reserve a 64 MB linker stack
        # (``-Wl,--stack,67108864``), so the probes are redundant and
        # skipping them lets MinGW's ld link the IR object cleanly.
        clang_extra.append("-mno-stack-arg-probe")
    subprocess.run(
        [clang_bin, "-c", opt_flag, *clang_extra, str(ir_path), "-o", str(obj_path)],
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
    # v5.8.x: ``-fPIC`` is rejected by clang targeting
    # ``x86_64-pc-windows-msvc`` (Windows PE/COFF code is position-
    # independent by default). Omit it on win32 builds.
    pic_flag = [] if sys.platform == "win32" else ["-fPIC"]
    c_base_flags = [
        CC,
        "-c",
        "-O2",
        "-g",
        *pic_flag,
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
    binary_name = "mnc-stage1.exe" if sys.platform == "win32" else "mnc-stage1"
    binary = SELF_DIR / binary_name
    if sys.platform == "win32":
        link_flags = [
            "-lm",
            "-Wl,--stack,67108864",  # 64MB stack for deep recursion on Windows
            # Alias __chkstk (emitted by clang for large stack frames) to
            # MinGW's ___chkstk_ms. Without this the linker fails with
            # "undefined reference to __chkstk" because clang targets the
            # MSVC probe name but MinGW's libgcc only provides the _ms
            # variant. Both have the same calling convention (size in rax).
            "-Wl,--defsym=__chkstk=___chkstk_ms",
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
