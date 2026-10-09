"""Explicit map owners and cursors release storage only after the last owner."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", params=["-O0", "-O2"])
def retained_map_probe(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux and clang ASan/UBSan/LSan")
    executable = tmp_path_factory.mktemp("retained-maps") / "probe"
    runtime = Path(os.environ.get("MAPANARE_TEST_RUNTIME", ROOT / "runtime/native/mapanare_core.c"))
    result = subprocess.run(
        [
            clang,
            "-std=c11",
            request.param,
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            "-I",
            str(ROOT / "runtime/native"),
            str(ROOT / "tests/native/fixtures/retained_maps.c"),
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
    assert result.returncode == 0, result.stderr
    return executable


@pytest.mark.parametrize(
    "mode",
    range(6),
    ids=[
        "deep-first",
        "deep-last",
        "owned-forward",
        "owned-reverse",
        "owned-cursor",
        "legacy-cursor",
    ],
)
def test_retained_maps(retained_map_probe: Path, mode: int) -> None:
    result = subprocess.run(
        [str(retained_map_probe), str(mode)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"
