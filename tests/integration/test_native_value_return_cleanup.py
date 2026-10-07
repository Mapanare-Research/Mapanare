"""Value-only struct returns must not suppress cleanup of unrelated locals."""

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
        "flat",
        "struct Count:\n    value: Int\n",
        "Count",
        "new Count { value: total }",
        "result.value",
    ),
    (
        "nested",
        "struct Count:\n    value: Int\nstruct Summary:\n    count: Count\n    valid: Bool\n",
        "Summary",
        "new Summary { count: new Count { value: total }, valid: true }",
        "result.count.value",
    ),
    (
        "wide",
        "struct Counts:\n    a: Int\n    b: Int\n    c: Int\n    d: Int\n    e: Int\n",
        "Counts",
        "new Counts { a: total, b: 2, c: 3, d: 4, e: 5 }",
        "result.a",
    ),
]


@pytest.mark.parametrize(
    "name,definitions,return_type,result,read", CASES, ids=[c[0] for c in CASES]
)
@pytest.mark.parametrize("iterations", [100, 10000])
def test_value_struct_return_is_leak_free(
    name: str,
    definitions: str,
    return_type: str,
    result: str,
    read: str,
    iterations: int,
    tmp_path: Path,
) -> None:
    compiler = Path(os.environ.get("MAPANARE_TEST_COMPILER", ROOT / "mapanare/self/mnc-stage1"))
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if sys.platform != "linux" or not clang or not compiler.exists() or not runtime.exists():
        pytest.skip("requires Linux native compiler/runtime and LeakSanitizer")
    source = tmp_path / f"{name}.mn"
    source.write_text(definitions + f"""
fn count(n: Int) -> {return_type}:
    let mut total: Int = 0
    let mut values: List<Int> = []
    for i in 0..3:
        let text: String = "item-" + str(n + i)
        values.push(len(text))
        total = total + values[i]
    return {result}
fn main():
    let mut total: Int = 0
    for i in 0..{iterations}:
        let result = count(42)
        total = total + {read}
    print(total)
""")
    emitted = subprocess.run(
        [str(compiler), "emit-llvm", str(source)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert emitted.returncode == 0, emitted.stderr
    ir = source.with_suffix(".ll")
    ir.write_text(emitted.stdout)
    executable = tmp_path / name
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
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout == f"{21 * iterations}\n"
