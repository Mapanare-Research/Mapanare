"""v5.37.0 Ht.1+Ht.2 — router and middleware tests for stdlib/net/http/router.mn.

Mirrors the v5.34.0 test_time_dt.py / v5.35.0 test_sq_sqlite.py harness:
read `stdlib/net/http/router.mn`, prepend it to each `.mn` test main body,
compile via the MIR-based Python LLVM emitter, link against
`libmapanare_rt.a`, and run the resulting binary. Each test prints
"<name> PASSED" or "<name> FAILED" and the harness asserts the former.

Why concatenation instead of `import`: cross-module function calls have
known limitations (mangling/extern-propagation). v5.34/v5.35 ship under
the same constraint with the same harness; v5.37.0 follows that pattern.

Test files under stdlib/net/http/tests/:
  - test_router.mn      — Ht.1 trie router (12 cases)
  - test_middleware.mn  — Ht.2 middleware registration table (6 cases)
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROUTER_MN = REPO_ROOT / "stdlib" / "net" / "http" / "router.mn"
STREAMING_MN = REPO_ROOT / "stdlib" / "net" / "http" / "streaming.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "net" / "http" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

# (test_filename, [extra modules to prepend])
TEST_CASES = [
    ("test_router.mn", []),
    ("test_middleware.mn", []),
    ("test_streaming.mn", [STREAMING_MN]),
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.parametrize("test_filename,extra_modules", TEST_CASES)
def test_http_router_mn(test_filename: str, extra_modules: list[Path], tmp_path: Path) -> None:
    if not _have_clang():
        pytest.skip("clang not available")
    if not _have_llvmlite():
        pytest.skip("llvmlite not available")
    if not RT_ARCHIVE.exists():
        pytest.skip(f"{RT_ARCHIVE} missing — run `make build-rt`")

    router_src = ROUTER_MN.read_text(encoding="utf-8")
    extra_src = "\n\n".join(p.read_text(encoding="utf-8") for p in extra_modules)
    test_src = (TESTS_DIR / test_filename).read_text(encoding="utf-8")

    combined = tmp_path / "combined.mn"
    parts = [router_src]
    if extra_src:
        parts.append(extra_src)
    parts.append(test_src)
    combined.write_text("\n\n".join(parts), encoding="utf-8")

    ll = tmp_path / "combined.ll"
    env = os.environ.copy()
    env["MAPANARE_RELEASE"] = "1"
    emit = subprocess.run(
        [
            "python3",
            "-m",
            "mapanare",
            "emit-llvm",
            str(combined),
            "-o",
            str(ll),
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert emit.returncode == 0, f"emit-llvm failed: {emit.stderr}"
    assert ll.exists(), "expected LLVM IR output"

    binary = tmp_path / "combined.out"
    link = subprocess.run(
        [
            "clang",
            str(ll),
            str(RT_ARCHIVE),
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert link.returncode == 0, f"clang link failed: {link.stderr}"
    assert binary.exists()

    run = subprocess.run(
        [str(binary)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    out = run.stdout + run.stderr
    assert "PASSED" in out, (
        f"{test_filename} did not print PASSED. exit={run.returncode}\n"
        f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
    assert run.returncode == 0, f"{test_filename} exited {run.returncode}"
