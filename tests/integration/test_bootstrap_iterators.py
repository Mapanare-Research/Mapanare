"""Map cursors must progress, preserve key types, and be released on every exit."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "nested-same-map": (
        """
fn main():
    let values = #{"a": 1, "bb": 2, "ccc": 3}
    let mut total: Int = 0
    for i in 0..100:
        for first in values:
            if first == "bb": continue
            for second in values:
                total = total + len(first) + len(second)
        for key in values:
            total = total + 1
            break
        for key in values:
            total = total + 1
    print(total)
""",
        "2800\n",
    ),
    "int-keys": (
        """
fn main():
    let values = #{10: 1, 20: 2, 30: 3}
    let mut total: Int = 0
    for key in values:
        total = total + key
    print(total)
""",
        "60\n",
    ),
    "empty-then-insert": (
        """
fn main():
    let mut values: Map<String, Int> = #{}
    let mut total: Int = 0
    for key in values:
        total = total + 1000
    values["hello"] = 1
    for key in values:
        total = total + len(key)
    print(total)
""",
        "5\n",
    ),
    "early-return": (
        """
fn score(values: Map<String, Int>, visit: Bool) -> Int:
    if visit:
        for first in values:
            for second in values:
                if second == "bb": return len(second)
    return 7
fn main():
    let values: Map<String, Int> = #{"a": 1, "bb": 2, "ccc": 3}
    let mut total: Int = 0
    for i in 0..100:
        total = total + score(values, true) + score(values, false)
    print(total)
""",
        "900\n",
    ),
    "inclusive-max": (
        """
fn main():
    let mut count: Int = 0
    for i in 9223372036854775806..=9223372036854775807:
        print(i)
        count = count + 1
    print(count)
""",
        "9223372036854775806\n9223372036854775807\n2\n",
    ),
}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("opt", list(MIROptLevel))
def test_bootstrap_iterator_lifetime(case: str, opt: MIROptLevel, tmp_path: Path) -> None:
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not runtime.exists():
        pytest.skip("requires Linux/WSL, clang, and runtime")
    source, expected = CASES[case]
    ir = tmp_path / "iterator.ll"
    ir.write_text(_compile_to_llvm_ir(source, "iterator.mn", opt_level=opt))
    executable = tmp_path / "iterator"
    linked = subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address",
            "-no-pie",
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
        timeout=5,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == expected
