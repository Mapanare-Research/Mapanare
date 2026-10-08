"""Owned list copy/drop policies must survive every COW lifecycle operation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def owned_list_probe(tmp_path_factory: pytest.TempPathFactory) -> Path:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux and clang ASan/UBSan/LSan")
    executable = tmp_path_factory.mktemp("owned-lists") / "probe"
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
            str(ROOT / "tests/native/fixtures/owned_lists.c"),
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
    range(11),
    ids=[
        "share",
        "detach",
        "grow-aliased-input",
        "replace-self",
        "clear",
        "pop-transfer",
        "concat-self",
        "concat-empty",
        "deep-clone",
        "large-callbacks",
        "nested-fields",
    ],
)
@pytest.mark.parametrize("reverse", [0, 1], ids=["source-first", "copy-first"])
def test_owned_list_lifecycle(owned_list_probe: Path, mode: int, reverse: int) -> None:
    result = subprocess.run(
        [str(owned_list_probe), str(mode), str(reverse)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"


def test_owned_concat_rejects_raw_policy(owned_list_probe: Path) -> None:
    result = subprocess.run(
        [str(owned_list_probe), "11", "0"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == -6, result.stdout + result.stderr
    assert "incompatible owned list concat policies" in result.stderr
