"""Executable parity for Boolean print/println on both compiler paths."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir

ROOT = Path(__file__).resolve().parents[2]
SOURCE = """
fn main():
    print(true)
    print(false)
    println(true)
    println(false)
"""


@pytest.mark.parametrize("backend", ["bootstrap", "native"])
def test_boolean_output(backend: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL native runtime and clang")
    source = tmp_path / "bool.mn"
    source.write_text(SOURCE)
    ir = tmp_path / "bool.ll"
    if backend == "bootstrap":
        ir.write_text(_compile_to_llvm_ir(SOURCE, str(source)))
    else:
        compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
        if not compiler.is_file():
            pytest.skip("native compiler not built")
        compiled = subprocess.run(
            [str(compiler), "emit-llvm", str(source)],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        assert compiled.stdout.strip(), compiled.stderr
        ir.write_text(compiled.stdout)
    exe = tmp_path / "bool"
    subprocess.run(
        [clang, "-O2", str(ir), str(runtime), "-lm", "-lpthread", "-ldl", "-o", str(exe)],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    result = subprocess.run([str(exe)], capture_output=True, text=True, check=True, timeout=15)
    assert result.stdout == "true\nfalse\ntrue\nfalse\n"
