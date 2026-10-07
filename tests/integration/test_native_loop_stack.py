"""Loop-local runtime argument slots must not grow the native stack."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = """
fn main():
    let mut values: List<String> = ["start"]
    for i in 0..100000:
        values[0] = "done"
    print(values[0])
"""


def test_loop_uses_bounded_stack(tmp_path: Path) -> None:
    clang = shutil.which("clang")
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not compiler.exists() or not runtime.exists():
        pytest.skip("requires Linux native compiler/runtime and clang")
    import resource

    source = tmp_path / "stack.mn"
    source.write_text(SOURCE)
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(source)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    ir = tmp_path / "stack.ll"
    ir.write_text(emitted.stdout)
    exe = tmp_path / "stack"
    subprocess.run(
        [clang, "-O2", str(ir), str(runtime), "-lm", "-lpthread", "-ldl", "-o", str(exe)],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    result = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=15,
        preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_STACK, (1024 * 1024, 1024 * 1024)),
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "done\n"
