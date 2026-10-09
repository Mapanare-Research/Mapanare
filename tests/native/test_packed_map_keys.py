"""Legacy packed map keys must not require aligned addresses."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("optimization", ["-O0", "-O2"])
def test_packed_map_keys(optimization: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux and clang ASan/UBSan/LSan")
    executable = tmp_path / "probe"
    runtime = Path(os.environ.get("MAPANARE_TEST_RUNTIME", ROOT / "runtime/native/mapanare_core.c"))
    build = subprocess.run(
        [
            clang,
            "-std=c11",
            optimization,
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            "-I",
            str(ROOT / "runtime/native"),
            str(ROOT / "tests/native/fixtures/packed_map_keys.c"),
            str(runtime),
            "-lm",
            "-lpthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert build.returncode == 0, build.stderr
    result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"
