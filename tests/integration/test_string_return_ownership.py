"""String accessors must not transfer ownership of their source's heap buffer.

The native compiler tracks String call results as owned. Before the return
fix, consuming an enum's string twice double-freed its borrowed payload.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPILER = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))

SOURCES = [
    """
enum Name:
    Text(String)
fn get_name(value: Name) -> String:
    match value:
        Text(name) => return name
fn consume(value: Name) -> Int:
    let name: String = get_name(value)
    print(name)
    return len(name)
fn main():
    let text: String = "field-" + str(42)
    let value: Name = Text(text)
    print(consume(value))
    print(consume(value))
""",
    """
struct Name:
    text: String
fn get_name(value: Name) -> String:
    return value.text
fn consume(value: Name) -> Int:
    let name: String = get_name(value)
    print(name)
    return len(name)
fn main():
    let value: Name = new Name { text: "field-" + str(42) }
    print(consume(value))
    print(consume(value))
""",
    """
fn make_name(n: Int) -> String:
    let result: String = "field-" + str(n)
    return result
fn consume(n: Int) -> Int:
    let name: String = make_name(n)
    print(name)
    return len(name)
fn main():
    print(consume(42))
    print(consume(42))
""",
    """
fn make_names() -> List<String>:
    let mut names: List<String> = []
    for i in 0..2:
        let name: String = "field-" + str(42)
        names.push(name)
    return names
fn main():
    let names: List<String> = make_names()
    print(names[0])
    print(len(names[0]))
    print(names[1])
    print(len(names[1]))
""",
    """
struct Names:
    values: List<String>
fn append_name(names: Names, text: String) -> Names:
    let mut result: Names = names
    result.values.push(text)
    return result
fn make_names() -> Names:
    let mut names: Names = new Names { values: [] }
    for i in 0..2:
        names = append_name(names, "field-" + str(42))
    return names
fn main():
    let names: Names = make_names()
    print(names.values[0])
    print(len(names.values[0]))
    print(names.values[1])
    print(len(names.values[1]))
""",
]


@pytest.mark.parametrize(
    "source", SOURCES, ids=["enum-borrow", "struct-borrow", "owned", "loop-list", "loop-call"]
)
def test_native_string_return(source: str, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists() or not COMPILER.exists():
        pytest.skip("requires Linux native compiler/runtime and AddressSanitizer")
    source_path = tmp_path / "return.mn"
    source_path.write_text(source)
    emitted = subprocess.run(
        [str(COMPILER), "emit-llvm", str(source_path)],
        capture_output=True,
        check=True,
        text=True,
        timeout=30,
    )
    assert emitted.stdout.strip(), emitted.stderr
    ir_path = tmp_path / "return.ll"
    ir_path.write_text(emitted.stdout)
    executable = tmp_path / "return"
    subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address",
            str(ir_path),
            str(runtime),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(executable),
        ],
        capture_output=True,
        check=True,
        text=True,
        timeout=60,
    )
    # This regression checks invalid frees/reads. General nested-container
    # retention remains separately tracked by the existing LSan baseline.
    result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=15,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "field-42\n8\nfield-42\n8\n"
