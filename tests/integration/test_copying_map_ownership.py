"""Generated map programs exercise copy-in replacement and borrowed snapshots."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel

pytest_plugins = ["tests.integration.test_map_return_ownership"]

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
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_copying_maps(case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path):
    source, expected = CASES[case]
    llvm = _compile_to_llvm_ir(source, "copying.mn", opt_level=opt)
    ir = tmp_path / "copying.ll"
    ir.write_text(llvm)
    exe = tmp_path / "copying"
    linked = subprocess.run(
        [
            "clang",
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            str(ir),
            str(instrumented_core),
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
