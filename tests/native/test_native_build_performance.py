"""Validate native release flags, object reuse, and PHI edges with real binaries."""

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MNC = Path(os.environ.get("MAPANARE_TEST_MNC", str(ROOT / "mapanare/self/mnc-stage1"))).resolve()
pytestmark = pytest.mark.skipif(
    not MNC.exists() or sys.platform != "linux", reason="Linux native compiler required"
)


@pytest.fixture
def native_tools(tmp_path):
    real_clang = shutil.which("clang")
    if not real_clang:
        pytest.skip("clang required")
    tools = tmp_path / "tools"
    tools.mkdir()
    wrapper = tools / "clang"
    wrapper.write_text(f"#!{sys.executable}\n" + """
import json, os, pathlib, subprocess, sys
args = sys.argv[1:]
with open(os.environ["CLANG_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
result = subprocess.run([os.environ["REAL_CLANG"], *args])
if result.returncode == 0 and "-c" in args and "-flto" in args:
    obj = pathlib.Path(args[args.index("-o") + 1])
    pathlib.Path(os.environ["BITCODE_MAGIC"]).write_bytes(obj.read_bytes()[:4])
raise SystemExit(result.returncode)
""")
    wrapper.chmod(0o755)
    # Exercise installed-layout runtime discovery from an isolated cache cwd.
    compiler = tmp_path / "mnc"
    shutil.copy2(MNC, compiler)
    lib = tmp_path / "lib/mapanare"
    lib.mkdir(parents=True)
    shutil.copy2(ROOT / "runtime/native/libmapanare_rt.a", lib / "libmapanare_rt.a")
    env = {
        **os.environ,
        "PATH": str(tools) + os.pathsep + os.environ["PATH"],
        "REAL_CLANG": real_clang,
        "CLANG_LOG": str(tmp_path / "clang.jsonl"),
        "BITCODE_MAGIC": str(tmp_path / "magic"),
    }
    return compiler, env


def native_build(tools, directory, source, output, *flags):
    compiler, env = tools
    result = subprocess.run(
        [str(compiler), "build", str(source), *flags, "-o", str(output)],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_lto_and_warm_cache_invalidation(native_tools, tmp_path):
    source = tmp_path / "hello.mn"
    source.write_text('fn main():\n    print("first")\n')
    output = tmp_path / "program"
    native_build(native_tools, tmp_path, source, output, "--release")
    assert (tmp_path / "magic").read_bytes() == b"BC\xc0\xde"
    log = tmp_path / "clang.jsonl"
    first = [json.loads(line) for line in log.read_text().splitlines()]
    assert any("-flto" in args and "-c" not in args for args in first)
    log.write_text("")
    native_build(native_tools, tmp_path, source, output, "--release")
    warm = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any("-c" in args for args in warm), warm
    assert any("-o" in args and "-flto" in args for args in warm), warm
    assert subprocess.check_output([str(output)], text=True).strip() == "first"
    next((tmp_path / ".mnc_cache/objects").glob("*.o")).write_bytes(b"damaged object")
    log.write_text("")
    native_build(native_tools, tmp_path, source, output, "--release")
    assert any("-c" in json.loads(line) for line in log.read_text().splitlines())
    assert subprocess.check_output([str(output)], text=True).strip() == "first"
    source.write_text('fn main():\n    print("changed")\n')
    log.write_text("")
    native_build(native_tools, tmp_path, source, output, "--release")
    assert any("-c" in json.loads(line) for line in log.read_text().splitlines())
    assert subprocess.check_output([str(output)], text=True).strip() == "changed"
    log.write_text("")
    native_build(native_tools, tmp_path, source, output, "--debug")
    assert any("-O0" in json.loads(line) for line in log.read_text().splitlines())


def test_parallel_native_builds_keep_outputs_separate(native_tools, tmp_path):
    sources = [tmp_path / f"p{i}.mn" for i in range(4)]
    for i, source in enumerate(sources):
        source.write_text(f'fn main():\n    print("program {i}")\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(native_build, native_tools, tmp_path, source, tmp_path / f"out{i}")
            for i, source in enumerate(sources)
        ]
        for future in futures:
            future.result()
    for i in range(4):
        assert (
            subprocess.check_output([str(tmp_path / f"out{i}")], text=True).strip()
            == f"program {i}"
        )


def test_quicksort_ir_verifies(tmp_path):
    ir = tmp_path / "quicksort.ll"
    subprocess.run(
        [str(MNC), "emit-llvm", str(ROOT / "benchmarks/optimizer/quicksort.mn"), "-o", str(ir)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    result = subprocess.run(["llvm-as", str(ir), "-o", os.devnull], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
