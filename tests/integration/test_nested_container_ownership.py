"""Nested-container ownership: List<String> and List<List<Int>> programs.

Exercises copy-in push, aliasing (COW detach), pop transfer, clear/reuse,
concat, returns, and replacement under ASan/UBSan/LSan on both the Python
bootstrap emitter and the native compiler, linking an instrumented runtime
core in each case.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel

pytest_plugins = ["tests.integration.test_map_return_ownership"]

ROOT = Path(__file__).resolve().parents[2]

CASES = {
    "string-loop": (
        """
fn score() -> Int:
    let mut items: List<String> = []
    for i in 0..100:
        items.push("item-" + str(i))
    let mut total: Int = 0
    for i in 0..100:
        total = total + len(items[i])
    return total
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score()
    print(total)
""",
        "690000\n",
    ),
    "nested-int": (
        """
fn score(n: Int) -> Int:
    let mut inner: List<Int> = []
    inner.push(n)
    inner.push(n + 1)
    let mut outer: List<List<Int>> = []
    outer.push(inner)
    outer.push(inner)
    let first = outer[0]
    return first[0] + first[1] + outer[1][1]
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score(10)
    print(total)
""",
        "32000\n",
    ),
    "nested-string": (
        """
fn score(n: Int) -> Int:
    let mut inner: List<String> = []
    inner.push("a" + str(n))
    let mut outer: List<List<String>> = []
    outer.push(inner)
    inner.push("b")
    return len(outer[0]) + len(inner)
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score(3)
    print(total)
""",
        "3000\n",
    ),
    "alias-shared": (
        """
fn main():
    let mut a: List<String> = []
    a.push("first")
    a.push("second")
    let b = a
    print(len(a))
    print(len(b))
    print(b[1])
""",
        "2\n2\nsecond\n",
    ),
    "alias-detach": (
        """
fn main():
    let mut a: List<String> = []
    a.push("first")
    let b = a
    for i in 0..100:
        a.push("x" + str(i))
    print(len(a))
    print(len(b))
    print(b[0])
    print(a[1])
""",
        "101\n1\nfirst\nx0\n",
    ),
    "last-element": (
        """
fn score() -> Int:
    let mut items: List<String> = []
    for i in 0..50:
        items.push("v" + str(i))
    let last = items[49]
    return len(last) + len(items)
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score()
    print(total)
""",
        "53000\n",
    ),
    "replace-element": (
        """
fn score() -> Int:
    let mut items: List<String> = []
    items.push("x")
    items[0] = "yy"
    return len(items) + len(items[0])
fn main():
    let mut total = 0
    for i in 0..1000:
        total = total + score()
    print(total)
""",
        "3000\n",
    ),
    "concat-independent": (
        """
fn main():
    let mut a: List<String> = []
    a.push("one")
    let mut b: List<String> = []
    b.push("two")
    let c = a + b
    a.push("three")
    print(len(a))
    print(len(c))
    print(c[0] + c[1])
""",
        "2\n2\nonetwo\n",
    ),
    "return-list": (
        """
fn make(n: Int) -> List<String>:
    let mut out: List<String> = []
    out.push("r" + str(n))
    return out
fn main():
    let mut total = 0
    for i in 0..1000:
        let items: List<String> = make(i)
        total = total + len(items[0])
    print(total)
""",
        "3890\n",
    ),
    "return-alias": (
        """
fn make() -> List<String>:
    let mut a: List<String> = []
    a.push("first")
    let b = a
    for i in 0..100:
        a.push("x" + str(i))
    return b
fn main():
    let kept: List<String> = make()
    print(len(kept))
    print(kept[0])
""",
        "1\nfirst\n",
    ),
    "return-inner": (
        """
fn make() -> List<String>:
    let mut inner: List<String> = []
    inner.push("inner")
    let mut outer: List<List<String>> = []
    outer.push(inner)
    return outer[0]
fn main():
    let kept: List<String> = make()
    print(len(kept))
    print(kept[0])
""",
        "1\ninner\n",
    ),
    "struct-list-copy": (
        """
struct Box:
    items: List<String>

fn make_box(n: Int) -> Box:
    let mut items: List<String> = []
    items.push("v" + str(n))
    return new Box { items: items }

fn choose(n: Int) -> Box:
    let mut first: Box = make_box(n)
    let second: Box = first
    first.items.push("more")
    return second

fn main():
    let mut total = 0
    for i in 0..1000:
        let box: Box = choose(i)
        total = total + len(box.items)
        total = total + len(box.items[0])
    print(total)
""",
        "4890\n",
    ),
    "struct-string-return": (
        """
struct Box:
    text: String
fn make_box(n: Int) -> Box:
    let text = "v" + str(n)
    return new Box { text: text }
fn main():
    let mut total = 0
    for i in 0..1000:
        let box: Box = make_box(i)
        total = total + len(box.text)
    print(total)
""",
        "3890\n",
    ),
    "struct-string-copy-replace": (
        """
struct Box:
    text: String
fn make_box(n: Int) -> Box:
    let text = "v" + str(n)
    return new Box { text: text }
fn choose(n: Int) -> Box:
    let mut first: Box = make_box(n)
    let second: Box = first
    first.text = "changed-" + str(n)
    return second
fn main():
    let mut total = 0
    for i in 0..1000:
        let box: Box = choose(i)
        total = total + len(box.text)
    print(total)
""",
        "3890\n",
    ),
    "struct-map-return": (
        """
struct Box:
    values: Map<String, String>
fn make_box(n: Int) -> Box:
    let mut values: Map<String, String> = #{}
    values["key"] = "v" + str(n)
    return new Box { values: values }
fn main():
    let mut total = 0
    for i in 0..1000:
        let box: Box = make_box(i)
        total = total + len(box.values["key"])
    print(total)
""",
        "3890\n",
    ),
    "struct-map-copy-replace": (
        """
struct Box:
    values: Map<String, String>
fn make_box(n: Int) -> Box:
    let mut values: Map<String, String> = #{}
    values["key"] = "v" + str(n)
    return new Box { values: values }
fn choose(n: Int) -> Box:
    let mut first: Box = make_box(n)
    let second: Box = first
    first.values["key"] = "changed-" + str(n)
    return second
fn main():
    let mut total = 0
    for i in 0..1000:
        let box: Box = choose(i)
        total = total + len(box.values["key"])
    print(total)
""",
        "10890\n",
    ),
    "struct-map-field-reassign": (
        """
struct Box:
    values: Map<String, String>
fn make_box(n: Int) -> Box:
    let mut values: Map<String, String> = #{}
    values["key"] = "v" + str(n)
    return new Box { values: values }
fn main():
    let mut total = 0
    for i in 0..1000:
        let mut box: Box = make_box(i)
        let mut other: Map<String, String> = #{}
        other["key"] = "replacement-" + str(i)
        box.values = other
        total = total + len(box.values["key"])
    print(total)
""",
        "14890\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("backend", ["bootstrap", "native"])
@pytest.mark.parametrize("opt", ["-O0", "-O2"])
def test_nested_containers(
    case: str, backend: str, opt: str, instrumented_core: Path, tmp_path: Path
) -> None:
    clang = shutil.which("clang")
    if sys.platform != "linux" or not clang:
        pytest.skip("requires Linux/WSL and clang")
    source, expected = CASES[case]
    path = tmp_path / "nested.mn"
    path.write_text(source)
    if backend == "native":
        compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
        runtime = ROOT / "runtime/native/libmapanare_rt.a"
        if not compiler.exists() or not runtime.exists():
            pytest.skip("requires native compiler and runtime archive")
        emitted = subprocess.run(
            [str(compiler), "emit-llvm", str(path)], capture_output=True, text=True, timeout=30
        )
        assert emitted.returncode == 0, emitted.stderr
        llvm = emitted.stdout
        # Instrument the core for native programs too; ASan intercepts
        # allocations in an optimized archive but cannot check uninstrumented
        # reads inside its list/map operations.
        link_inputs = [str(instrumented_core), str(runtime)]
    else:
        llvm = _compile_to_llvm_ir(source, str(path), opt_level=MIROptLevel.O2)
        link_inputs = [str(instrumented_core)]
    ir = path.with_suffix(".ll")
    ir.write_text(llvm)
    exe = tmp_path / "nested"
    linked = subprocess.run(
        [
            clang,
            opt,
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            "-Wno-override-module",
            str(ir),
            *link_inputs,
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
