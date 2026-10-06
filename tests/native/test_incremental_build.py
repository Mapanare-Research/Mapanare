"""Build-driver integration tests with observable fake compiler processes."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux Bash build-driver tests")


@pytest.fixture
def project(tmp_path):
    sources = tmp_path / "project with spaces"
    sources.mkdir()
    (sources / "a.mn").write_text("fn a() -> Int = 1\n")
    (sources / "b.mn").write_text("import self::a\nfn b() -> Int = a()\n")
    compiler = tmp_path / "fake-mnc"
    compiler.write_text(f"#!{sys.executable}\n" + """
import json, os, pathlib, sys, time
source = pathlib.Path(sys.argv[2])
with open(os.environ["BUILD_LOG"], "a") as log:
    log.write(json.dumps([source.stem, "start", time.monotonic()]) + "\\n")
time.sleep(0.1)
if os.environ.get("EXPECT_PARALLEL"):
    marker = source.parent / (source.stem + ".started")
    marker.touch()
    deadline = time.monotonic() + 10
    while len(list(source.parent.glob("*.started"))) < 2:
        if time.monotonic() > deadline:
            raise SystemExit(8)
        time.sleep(0.01)
if "BROKEN" in source.read_text():
    raise SystemExit(1)
print(source.read_text())
with open(os.environ["BUILD_LOG"], "a") as log:
    log.write(json.dumps([source.stem, "end", time.monotonic()]) + "\\n")
""")
    compiler.chmod(0o755)
    cc = tmp_path / "fake-clang"
    cc.write_text(f"#!{sys.executable}\n" + """
import pathlib, sys
if "--version" in sys.argv:
    print("fake clang 1")
else:
    pathlib.Path(sys.argv[sys.argv.index("-o") + 1]).write_text("object or executable")
""")
    cc.chmod(0o755)
    env = {**os.environ, "MNC": str(compiler), "CC": str(cc), "BUILD_LOG": str(tmp_path / "log")}
    command = [
        "bash",
        str(ROOT / "scripts/mnc-build.sh"),
        str(sources),
        "--timing",
        "-o",
        str(tmp_path / "output with spaces"),
    ]
    yield sources, compiler, env, command
    subprocess.run(command + ["--clean"], env=env, capture_output=True)


def build(project, *args):
    return subprocess.run(project[3] + list(args), env=project[2], capture_output=True, text=True)


def test_cache_dependency_and_failure_recovery(project):
    sources = project[0]
    first = build(project)
    assert first.returncode == 0, first.stderr
    assert "2/2 cached" in build(project).stdout
    (sources / "a.mn").write_text("BROKEN\n")
    assert build(project).returncode != 0
    assert build(project).returncode != 0  # may not bless old a.o with the new hash
    (sources / "a.mn").write_text("fn a() -> Int = 2\n")
    rebuilt = build(project)
    assert rebuilt.returncode == 0, rebuilt.stderr
    assert "0/2 cached" in rebuilt.stdout
    assert "2/2 cached" in build(project).stdout


def test_flags_and_compiler_invalidate_cache(project):
    assert build(project).returncode == 0
    assert "0/2 cached" in build(project, "--debug").stdout
    assert "2/2 cached" in build(project, "--debug").stdout
    project[1].write_text(project[1].read_text() + "\n# changed compiler\n")
    assert "0/2 cached" in build(project).stdout


def test_parallel_jobs_overlap(project):
    project[2]["EXPECT_PARALLEL"] = "1"
    result = build(project, "--jobs", "2")
    assert result.returncode == 0, result.stderr
    events = [json.loads(line) for line in Path(project[2]["BUILD_LOG"]).read_text().splitlines()]
    starts = [t for _, event, t in events if event == "start"]
    ends = [t for _, event, t in events if event == "end"]
    assert max(starts) < min(ends), events


def test_unknown_import_never_reuses_stale_object(project):
    (project[0] / "a.mn").write_text("import other::module\nfn a() -> Int = 1\n")
    assert build(project).returncode == 0
    assert "0/2 cached" in build(project).stdout
