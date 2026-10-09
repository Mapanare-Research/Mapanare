"""Native-compiler copy-in map ownership: replacement, deletion, borrowed reads.

Mirrors tests/integration/test_copying_map_ownership.py but compiles each
program with the self-hosted compiler (mnc-stage1) and links the prebuilt
runtime archive. ASan intercepts all allocations, so leaks inside the archive
are still reported; the runtime itself is separately sanitized in
tests/native and tests/runtime.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CASES = {
    "delete-reinsert": (
        """
fn score() -> Int:
    let mut values: Map<String, String> = #{}
    for i in 0..100:
        let key = "key-" + str(i)
        values[key] = "value-" + str(i)
        values.remove(key)
        values[key] = "again-" + str(i)
        values.remove("key-" + str(i))
    return len(values)
fn main():
    let mut total = 0
    for i in 0..100:
        total = total + score()
    print(total)
""",
        "0\n",
    ),
    "deleted-view": (
        """
fn score() -> String:
    let key = "key-" + str(42)
    let mut values = #{key: "saved-" + str(42)}
    let saved = values[key]
    values.remove(key)
    return saved
fn main():
    print(score())
""",
        "saved-42\n",
    ),
    "replacement": (
        """
fn score(n: Int) -> Int:
    let key = "key-" + str(n)
    let value = "first-" + str(n)
    let mut values = #{key: value}
    for i in 0..100:
        values["key-" + str(n)] = "next-" + str(i)
    return len(values[key]) + len(key) + len(value)
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score(42)
    print(total)
""",
        "21000\n",
    ),
    "saved-view": (
        """
fn score() -> Int:
    let mut values = #{"key": "first-" + str(42)}
    let saved = values["key"]
    let alias = saved
    values["key"] = "second-" + str(123)
    print(alias)
    return len(saved) + len(values["key"])
fn main():
    print(score())
""",
        "first-42\n18\n",
    ),
    "same-input": (
        """
fn score(n: Int) -> Int:
    let text = "shared-" + str(n)
    let mut values = #{text: text}
    values[text] = text
    values["other"] = text
    return len(text) + len(values[text]) + len(values["other"])
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score(42)
    print(total)
""",
        "27000\n",
    ),
    "numeric-keys": (
        """
fn score() -> Int:
    let mut values: Map<Int, String> = #{}
    for i in 0..100:
        values[1] = "value-" + str(i)
    return len(values[1])
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score()
    print(total)
""",
        "8000\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("clang_level", ["-O0", "-O2"])
def test_native_copying_maps(case: str, clang_level: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    if not compiler.exists():
        pytest.skip("requires native compiler")
    source, expected = CASES[case]
    path = tmp_path / "copying.mn"
    path.write_text(source)
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
    )
    assert emitted.returncode == 0, emitted.stderr
    ir = path.with_suffix(".ll")
    ir.write_text(emitted.stdout)
    executable = tmp_path / "copying"
    linked = subprocess.run(
        [
            clang,
            clang_level,
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            "-Wno-override-module",
            str(ir),
            str(runtime),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
