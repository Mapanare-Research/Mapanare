"""Concurrent runtime builds must publish complete, independently built archives."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_overlapping_builds_keep_all_objects(tmp_path):
    gcc = shutil.which("gcc")
    if os.name == "nt" or not gcc or not shutil.which("make") or not shutil.which("ar"):
        # v5.54.0: the Makefile runtime build is a POSIX toolchain workflow.
        pytest.skip("requires POSIX make, gcc and ar")
    shutil.copy(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "VERSION").write_text("5.54.0\n")
    native = tmp_path / "runtime" / "native"
    native.mkdir(parents=True)
    for name in ("alpha", "beta"):
        (native / f"{name}.c").write_text(f"int {name}(void) {{ return 1; }}\n")
    (native / "mapanare_metal.m").write_text("int metal(void) { return 1; }\n")
    wrappers = tmp_path / "bin"
    wrappers.mkdir()
    compiler = wrappers / "gcc"
    compiler.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, subprocess, sys, time\n"
        f"real_gcc = {gcc!r}\n"
        "root = pathlib.Path(os.environ['BUILD_SYNC'])\n"
        "role = os.environ['BUILD_ROLE']\n"
        "def wait(name):\n"
        "    deadline = time.monotonic() + 20\n"
        "    while not (root / name).exists():\n"
        "        if time.monotonic() > deadline: raise RuntimeError(name)\n"
        "        time.sleep(0.02)\n"
        "alpha = any(arg.endswith('/alpha.c') for arg in sys.argv)\n"
        "if alpha and role == 'B':\n"
        "    (root / 'b-started').touch()\n"
        "    wait('a-done')\n"
        "subprocess.run([real_gcc, *sys.argv[1:]], check=True)\n"
        "if alpha and role == 'A':\n"
        "    (root / 'alpha-ready').touch()\n"
        "    wait('b-started')\n"
    )
    compiler.chmod(0o755)
    command = ["make", "build-rt", "RUNTIME_SOURCES=alpha.c beta.c", "RUNTIME_EXCLUDES="]
    environment = {
        **os.environ,
        "PATH": f"{wrappers}:{os.environ['PATH']}",
        "BUILD_SYNC": str(tmp_path),
    }
    second = None
    with (
        (tmp_path / "first.log").open("w") as first_log,
        (tmp_path / "second.log").open("w") as second_log,
    ):
        first = subprocess.Popen(
            [*command, "RT_OUTPUT=first.a"],
            cwd=tmp_path,
            env={**environment, "BUILD_ROLE": "A"},
            stdout=first_log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while not (tmp_path / "alpha-ready").exists():
                assert first.poll() is None, (tmp_path / "first.log").read_text()
                assert time.monotonic() < deadline, "first build did not reach the barrier"
                time.sleep(0.02)
            second = subprocess.Popen(
                [*command, "RT_OUTPUT=second.a"],
                cwd=tmp_path,
                env={**environment, "BUILD_ROLE": "B"},
                stdout=second_log,
                stderr=subprocess.STDOUT,
            )
            assert first.wait(timeout=30) == 0, (tmp_path / "first.log").read_text()
            (tmp_path / "a-done").touch()
            assert second.wait(timeout=30) == 0, (tmp_path / "second.log").read_text()
        finally:
            (tmp_path / "a-done").touch()
            (tmp_path / "b-started").touch()
            for process in (first, second):
                if process is not None and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=30)
    for name in ("first.a", "second.a"):
        members = subprocess.check_output(["ar", "t", str(tmp_path / name)], text=True).splitlines()
        expected = {"mapanare_rt_alpha.o", "mapanare_rt_beta.o"}
        if sys.platform == "darwin":
            expected.add("mapanare_rt_mapanare_metal.o")
            # Apple's ar also lists its archive symbol table, which is not an object.
            members = [name for name in members if name not in {"__.SYMDEF", "__.SYMDEF SORTED"}]
        assert set(members) == expected
    assert not list(tmp_path.glob(".mapanare-rt.*")), "temporary build directories leaked"
