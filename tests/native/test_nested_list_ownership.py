"""Nested list clones must retain allocated empty buffers and detach safely."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def ownership_probe(tmp_path_factory: pytest.TempPathFactory) -> Path:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux and clang AddressSanitizer/LeakSanitizer")
    executable = tmp_path_factory.mktemp("container-ownership") / "probe"
    compiled = subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address",
            "-fno-omit-frame-pointer",
            "-no-pie",
            "-I",
            str(ROOT / "runtime/native"),
            str(ROOT / "tests/native/fixtures/container_ownership.c"),
            str(ROOT / "runtime/native/mapanare_core.c"),
            "-lm",
            "-lpthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert compiled.returncode == 0, compiled.stderr
    return executable


@pytest.mark.parametrize("state", [0, 1, 2, 3], ids=["fresh", "cleared", "popped", "nonempty"])
@pytest.mark.parametrize("reverse", [0, 1], ids=["source-freed-first", "copy-freed-first"])
@pytest.mark.parametrize("mutate_first", [0, 1], ids=["free", "detach-then-free"])
def test_nested_clone_owns_its_buffers(
    ownership_probe: Path,
    state: int,
    reverse: int,
    mutate_first: int,
) -> None:
    result = subprocess.run(
        [str(ownership_probe), "deep-clone", str(state), str(reverse), str(mutate_first)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"
