#!/usr/bin/env python3
"""Build the Stage 1 self-hosted compiler binary (mnc-stage1).

Pipeline:
    1. Compile mapanare/self/*.mn (7 modules) → LLVM IR via Python bootstrap
    2. Post-process IR: make compile() externally visible
    3. Compile IR → native object code
    4. Compile C runtime (mapanare_core.c)
    5. Compile C main wrapper (mnc_main.c)
    6. Link: main wrapper + compiler object + C runtime → mnc-stage1
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


def build() -> pathlib.Path:
    """Build mnc-stage1 and return its path."""
    print("=== Stage 1: Building self-hosted compiler ===")

    # 1. Generate LLVM IR
    print("[1/6] Generating LLVM IR from mapanare/self/*.mn ...")
    from mapanare.multi_module import compile_multi_module_mir

    source = (SELF_DIR / "main.mn").read_text(encoding="utf-8")
    ir = compile_multi_module_mir(
        root_source=source,
        root_file=str(SELF_DIR / "main.mn"),
        opt_level=2,
    )

    # 2. Post-process: make compile() and format_error() externally visible
    print("[2/6] Post-processing IR (external linkage for entry points) ...")
    # Remove 'internal' linkage from ALL function definitions.
    # LLVM -O1 dead-code-eliminates internal functions it considers
    # unreachable, but with sret calling conventions it sometimes
    # misjudges reachability, stripping functions that ARE called.
    ir = ir.replace("define internal ", "define ")

    ir_path = SELF_DIR / "main.ll"
    ir_path.write_text(ir, encoding="utf-8")
    print(f"  IR: {ir.count(chr(10))} lines → {ir_path}")

    # 3. Compile IR to object code
    print("[3/6] Compiling LLVM IR → object code ...")
    from mapanare.jit import jit_compile_to_object

    obj_path = SELF_DIR / "main.o"
    obj_bytes = jit_compile_to_object(ir, opt_level=1)
    obj_path.write_bytes(obj_bytes)
    print(f"  Object: {len(obj_bytes)} bytes → {obj_path}")

    # 4. Compile C runtime
    print("[4/6] Compiling C runtime ...")
    core_c = NATIVE_DIR / "mapanare_core.c"
    core_o = SELF_DIR / "mapanare_core.o"
    asan_flags = ["-fsanitize=address", "-fno-omit-frame-pointer"] if "--asan" in sys.argv else []
    subprocess.run(
        [CC, "-c", "-O0", "-g", "-fPIC", "-I", str(NATIVE_DIR)]
        + asan_flags
        + [str(core_c), "-o", str(core_o)],
        check=True,
    )
    print(f"  Runtime: {core_o}")

    # 5. Compile main wrapper
    print("[5/6] Compiling C main wrapper ...")
    main_c = SELF_DIR / "mnc_main.c"
    main_o = SELF_DIR / "mnc_main.o"
    subprocess.run(
        [CC, "-c", "-O0", "-g"] + asan_flags + [str(main_c), "-o", str(main_o)],
        check=True,
    )
    print(f"  Wrapper: {main_o}")

    # 6. Link
    print("[6/6] Linking mnc-stage1 ...")
    binary = SELF_DIR / "mnc-stage1"
    subprocess.run(
        [
            CC,
            "-o",
            str(binary),
            str(main_o),
            str(obj_path),
            str(core_o),
            "-no-pie",
            "-rdynamic",
            "-lm",
            "-lpthread",
            "-Wl,-z,stacksize=67108864",  # 64MB stack for deep recursion
        ]
        + asan_flags
        + [],
        check=True,
    )
    print(f"  Binary: {binary} ({binary.stat().st_size} bytes)")

    # Cleanup intermediate .o files
    for f in [main_o, core_o]:
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
