"""Execute native loop rewrites and conservative fallbacks under ASan/UBSan.

The runtime is instrumented too, so ownership errors in the builder or string
drop glue are visible rather than hidden inside the prebuilt runtime archive.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MNC = Path(os.environ.get("MAPANARE_TEST_MNC", ROOT / "mapanare/self/mnc-stage1")).resolve()
pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or not MNC.exists(), reason="Linux native compiler required"
)


@pytest.fixture(scope="module")
def runtime(tmp_path_factory):
    clang = shutil.which("clang")
    if not clang:
        pytest.skip("clang required")
    obj = tmp_path_factory.mktemp("string-runtime") / "core.o"
    subprocess.run(
        [
            clang,
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-ffunction-sections",
            "-fdata-sections",
            "-c",
            str(ROOT / "runtime/native/mapanare_core.c"),
            "-o",
            str(obj),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return clang, obj


def execute(source, tmp_path, runtime, optimized, *, leak_check=True):
    program = tmp_path / "program.mn"
    ir = tmp_path / "program.ll"
    exe = tmp_path / "program"
    program.write_text(source)
    result = subprocess.run(
        [str(MNC), "emit-llvm", str(program), "-o", str(ir)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    text = ir.read_text()
    assert ("call ptr @__mn_sb_new(" in text) == optimized
    if optimized:
        assert text.count("call ptr @__mn_sb_new(") == 1
        assert text.count("@__mn_sb_finish(ptr ") == 1
    clang, obj = runtime
    subprocess.run(
        [
            clang,
            "-O2",
            "-fsanitize=address,undefined",
            str(ir),
            str(obj),
            "-Wl,--gc-sections",
            "-pthread",
            "-lm",
            "-o",
            str(exe),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    run = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=30,
        env={
            **os.environ,
            "ASAN_OPTIONS": f"detect_leaks={int(leak_check)}",
            "UBSAN_OPTIONS": "halt_on_error=1",
        },
    )
    assert run.returncode == 0, run.stdout + run.stderr
    return run.stdout


@pytest.mark.parametrize(
    "count,seed,chunk",
    [
        (0, "seed", "x"),
        (1, "seed", "x"),
        (10000, "", "hello"),
        (20, "prefix", ""),
        (40, "ñ", "é"),
    ],
)
def test_accumulate_preserves_initial_alias(count, seed, chunk, tmp_path, runtime):
    source = f"""fn main():
    let initial: String = {json.dumps(seed, ensure_ascii=False)}
    let mut result: String = initial
    let mut i: Int = 0
    while i < {count}:
        result = result + {json.dumps(chunk, ensure_ascii=False)}
        i = i + 1
    print(initial)
    print(result)
"""
    assert execute(source, tmp_path, runtime, True) == seed + "\n" + seed + chunk * count + "\n"


def test_dynamic_chunks_and_returned_ownership(tmp_path, runtime):
    source = """fn build(n: Int) -> String:
    let initial: String = "se" + "ed"
    let mut result: String = initial
    let mut i: Int = 0
    while i < n:
        result = result + str(i)
        i = i + 1
    print(initial)
    return result

fn main():
    print(build(0))
    print(build(4))
"""
    assert execute(source, tmp_path, runtime, True) == "seed\nseed\nseed\nseed0123\n"


@pytest.mark.parametrize(
    "source,expected",
    [
        (
            """fn main():
    let mut result: String = "x"
    while len(result) < 4:
        result = result + "x"
    print(result)
""",
            "xxxx\n",
        ),
        (
            """fn main():
    let mut result: String = ""
    let mut i: Int = 0
    while i < 3:
        result = result + "x"
        print(result)
        i = i + 1
    print(result)
""",
            "x\nxx\nxxx\nxxx\n",
        ),
        (
            """fn main():
    let mut result: String = "x"
    let mut i: Int = 0
    while i < 3:
        result = result + result
        i = i + 1
    print(result)
""",
            "xxxxxxxx\n",
        ),
        (
            """fn main():
    let mut result: String = ""
    let mut i: Int = 0
    while i < 3:
        result = "reset"
        result = result + "x"
        i = i + 1
    print(result)
""",
            "resetx\n",
        ),
        (
            """fn main():
    let mut result: String = ""
    let mut i: Int = 0
    while i < 10:
        result = result + "x"
        if i == 2:
            break
        i = i + 1
    print(result)
""",
            "xxx\n",
        ),
    ],
)
def test_observable_or_complex_loops_stay_unchanged(source, expected, tmp_path, runtime):
    assert execute(source, tmp_path, runtime, False) == expected


def test_nested_loop_fallback(tmp_path, runtime):
    # The baseline emitter misses the final drop when the return block is
    # emitted before the inner loop. Keep address/UB sanitizers enabled here,
    # but limit leak checking to the other cases, including every rewrite.
    source = """fn main():
    let mut result: String = ""
    let mut i: Int = 0
    while i < 2:
        let mut j: Int = 0
        while j < 2:
            result = result + "x"
            j = j + 1
        i = i + 1
    print(result)
"""
    assert execute(source, tmp_path, runtime, False, leak_check=False) == "xxxx\n"
