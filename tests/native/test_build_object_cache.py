"""Exercise real cache I/O, invalidation, concurrency and failure recovery."""

from __future__ import annotations

import concurrent.futures
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux cache probe linker flags")


@pytest.fixture(scope="module")
def cache_probe(tmp_path_factory):
    clang = shutil.which("clang")
    if not clang:
        pytest.skip("clang required")
    directory = tmp_path_factory.mktemp("cache-probe")
    source = directory / "probe.c"
    source.write_text("""
#include "mapanare_core.h"
#include <string.h>
#include <stdio.h>
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    MnString key = {argv[2], strlen(argv[2]), 0};
    MnString path = {argv[3], strlen(argv[3]), 0};
    if (strcmp(argv[1], "temp") == 0) {
        MnString temp = __mn_temp_path(key);
        FILE *file = fopen(temp.data, "wb");
        if (!file) return 3;
        fputs("temporary", file);
        fclose(file);
        puts(temp.data);
        __mn_str_free(temp.data, (int64_t)(temp.len | ((uint64_t)temp.is_heap << 63)));
        return 0;
    }
    int ok = strcmp(argv[1], "store") == 0
        ? __mn_build_cache_store(key, path) : __mn_build_cache_lookup(key, path);
    return ok == 1 ? 0 : 1;
}
""")
    binary = directory / "probe"
    subprocess.run(
        [
            clang,
            str(source),
            str(ROOT / "runtime/native/mapanare_core.c"),
            "-I",
            str(ROOT / "runtime/native"),
            "-ffunction-sections",
            "-fdata-sections",
            "-Wl,--gc-sections",
            *(["-fsanitize=address,undefined"] if os.environ.get("CACHE_TEST_SANITIZERS") else []),
            "-lm",
            "-lpthread",
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return binary


def invoke(probe, cwd, operation, key, path):
    return subprocess.run([str(probe), operation, key, str(path)], cwd=cwd).returncode


def test_exact_key_and_binary_roundtrip(cache_probe, tmp_path):
    original = tmp_path / "input.o"
    original.write_bytes(bytes(range(256)) * 100)
    output = tmp_path / "output.o"
    assert invoke(cache_probe, tmp_path, "lookup", "ir+flags+toolchain", output) == 1
    assert invoke(cache_probe, tmp_path, "store", "ir+flags+toolchain", original) == 0
    assert invoke(cache_probe, tmp_path, "lookup", "ir+flags+toolchain", output) == 0
    assert output.read_bytes() == original.read_bytes()
    for key in ("changed IR", "changed flags", "changed toolchain"):
        assert invoke(cache_probe, tmp_path, "lookup", key, output) == 1
    # A hash slot alone is never enough: the full key must match.
    next((tmp_path / ".mnc_cache/objects").glob("*.key")).write_bytes(b"wrong key")
    assert invoke(cache_probe, tmp_path, "lookup", "ir+flags+toolchain", output) == 1


def test_failed_store_invalidates_old_object(cache_probe, tmp_path):
    original = tmp_path / "input.o"
    original.write_bytes(b"old")
    assert invoke(cache_probe, tmp_path, "store", "key", original) == 0
    assert invoke(cache_probe, tmp_path, "store", "key", tmp_path / "missing") == 1
    assert invoke(cache_probe, tmp_path, "lookup", "key", tmp_path / "output") == 1


def test_cache_unavailable_is_a_miss(cache_probe, tmp_path):
    (tmp_path / ".mnc_cache").write_text("not a directory")
    original = tmp_path / "input.o"
    original.write_bytes(b"object")
    assert invoke(cache_probe, tmp_path, "store", "key", original) == 1
    assert invoke(cache_probe, tmp_path, "lookup", "key", tmp_path / "output") == 1


def test_concurrent_writers_never_publish_partial_objects(cache_probe, tmp_path):
    original = tmp_path / "input.o"
    original.write_bytes(bytes(range(256)) * 4096)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda _: invoke(cache_probe, tmp_path, "store", "key", original), range(16)
            )
        )
    output = tmp_path / "output.o"
    assert invoke(cache_probe, tmp_path, "lookup", "key", output) == 0
    assert output.read_bytes() == original.read_bytes()


def test_temp_paths_are_process_specific_and_cleaned(cache_probe, tmp_path):
    paths = [
        subprocess.check_output(
            [str(cache_probe), "temp", "cache-test.tmp", "unused"], cwd=tmp_path, text=True
        ).strip()
        for _ in range(2)
    ]
    assert paths[0] != paths[1]
    assert all(not Path(path).exists() for path in paths)
