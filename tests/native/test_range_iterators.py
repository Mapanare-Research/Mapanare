"""Inclusive/exclusive range endpoints must stay defined across the Int domain."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("runtime", ["mapanare_core.c", "libmapanare_rt.a"])
def test_range_iterator_bounds(runtime: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    library = ROOT / "runtime/native" / runtime
    if sys.platform != "linux" or not clang or not library.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    executable = tmp_path / "ranges"
    linked = subprocess.run(
        [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            "-no-pie",
            "-I",
            str(ROOT / "runtime/native"),
            str(ROOT / "tests/native/fixtures/range_iterators.c"),
            str(library),
            "-lm",
            "-lpthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == "ok\n"
