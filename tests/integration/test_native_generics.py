"""Executable native generic specialization, including explicit type arguments."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    (
        "inferred-body",
        """
fn echo<T>(value: T) -> T:
    let copy: T = value
    return copy
fn main():
    print(echo("first"))
    print(echo(42))
    print(echo("last"))
""",
        "first\n42\nlast\n",
    ),
    (
        "nested-explicit",
        """
fn echo<T>(value: T) -> T:
    let copy: T = value
    return copy
fn forward<T>(value: T) -> T:
    let items: List<T> = [value]
    if true:
        return echo::<T>(items[0])
    return value
fn main():
    print(forward::<String>("first"))
    print(forward::<Int>(42))
    print(forward::<String>("last"))
""",
        "first\n42\nlast\n",
    ),
    (
        "return-only",
        """
fn empty<T>() -> List<T>:
    let values: List<T> = []
    return values
fn main():
    let mut ints: List<Int> = empty::<Int>()
    ints.push(42)
    let mut strings: List<String> = empty::<String>()
    strings.push("hello")
    print(ints[0])
    print(strings[0])
""",
        "42\nhello\n",
    ),
    (
        "nested-types",
        """
fn show<T>(value: T):
    print(value[0])
fn main():
    show::<List<Int>>([42])
    show::<List<String>>(["hello"])
    show::<List<Int>>([7])
""",
        "42\nhello\n7\n",
    ),
    (
        "recursive-and-pipe",
        """
fn descend<T>(value: T, n: Int) -> T:
    if n == 0:
        return value
    return descend::<T>(value, n - 1)
fn main():
    print(descend::<String>("recursive", 3))
    print(42 |> descend::<Int>(3))
""",
        "recursive\n42\n",
    ),
    (
        "schema-body",
        """
struct Answer:
    value: Int
struct Label:
    text: String
struct Holder<T>:
    value: T
impl<T> Holder<T>:
    fn schema(self) -> String:
        return __struct_meta::<T>()
fn schema<T>(value: T) -> String:
    if true:
        return __struct_meta::<T>()
    return "unreachable"
fn main():
    print(schema(new Answer { value: 42 }))
    print(schema(new Label { text: "hello" }))
    print(schema(new Answer { value: 7 }))
    let held = new Holder { value: new Answer { value: 9 } }
    print(held.schema())
""",
        '{"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}\n'
        '{"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}\n'
        '{"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}\n'
        '{"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}\n',
    ),
]


@pytest.mark.parametrize("name,source,expected", CASES, ids=[case[0] for case in CASES])
def test_native_generics(name: str, source: str, expected: str, tmp_path: Path) -> None:
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    clang = shutil.which("clang")
    if sys.platform != "linux" or not compiler.exists() or not runtime.exists() or not clang:
        pytest.skip("requires Linux native compiler/runtime and clang")
    program = tmp_path / (name + ".mn")
    program.write_text(source)
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(program)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert emitted.returncode == 0, emitted.stderr
    ir = program.with_suffix(".ll")
    ir.write_text(emitted.stdout)
    exe = tmp_path / name
    linked = subprocess.run(
        [clang, "-O2", str(ir), str(runtime), "-lm", "-lpthread", "-ldl", "-o", str(exe)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.parametrize(
    "call,diagnostic",
    [
        ("echo::<Int, String>(1)", "type argument count mismatch"),
        ('echo::<Int>("bad")', "argument type mismatch"),
        ("echo::<Int>()", "argument count mismatch"),
        ("plain::<Int>(1)", "does not accept type arguments"),
        ("echo::<Missing>(1)", "Unknown type argument"),
    ],
)
def test_native_generic_diagnostics(call: str, diagnostic: str, tmp_path: Path) -> None:
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    if sys.platform != "linux" or not compiler.exists():
        pytest.skip("requires Linux native compiler")
    source = tmp_path / "invalid.mn"
    source.write_text(
        "fn echo<T>(value: T) -> T:\n    return value\n"
        "fn plain(value: Int) -> Int:\n    return value\n"
        f"fn main():\n    print({call})\n"
    )
    result = subprocess.run(
        [str(compiler), "emit-llvm", str(source)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert diagnostic in result.stderr
