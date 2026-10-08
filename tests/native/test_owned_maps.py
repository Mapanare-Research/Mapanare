"""Owned maps must copy inputs, release replaced/deleted fields, and move on rehash."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def owned_map_probe(tmp_path_factory: pytest.TempPathFactory) -> Path:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux and clang ASan/UBSan/LSan")
    executable = tmp_path_factory.mktemp("owned-maps") / "probe"
    runtime = Path(os.environ.get("MAPANARE_TEST_RUNTIME", ROOT / "runtime/native/mapanare_core.c"))
    run = subprocess.run(
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
            str(ROOT / "tests/native/fixtures/owned_maps.c"),
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
    assert run.returncode == 0, run.stderr
    return executable


@pytest.mark.parametrize(
    "mode",
    range(13),
    ids=[
        "replace-alias",
        "delete-alias",
        "grow-alias",
        "tombstones",
        "long-chain",
        "keys-outlive-map",
        "large-callbacks",
        "nested-values",
        "float-plain",
        "reference-model",
        "empty-keys-policy",
        "grow-key-and-value-alias",
        "string-key-plain-value",
    ],
)
@pytest.mark.parametrize("deep", [0, 1], ids=["free", "free-deep"])
def test_owned_map_lifecycle(owned_map_probe: Path, mode: int, deep: int) -> None:
    result = subprocess.run(
        [str(owned_map_probe), str(mode), str(deep)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"


@pytest.mark.parametrize("mode", range(20, 25))
def test_owned_map_rejects_invalid_policy(owned_map_probe: Path, mode: int) -> None:
    result = subprocess.run(
        [str(owned_map_probe), str(mode), "0"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == -6, result.stdout + result.stderr
    assert "mapanare:" in result.stderr
    assert "owned map" in result.stderr
