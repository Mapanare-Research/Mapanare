"""v5.13.1 At.3 — smoke test for the @test runtime.

Pre-v5.13.1, both `mapanare test` (Python bootstrap) and
`mnc-stage1 test` (native) failed on the simplest possible @test
fixture: the Python side blew up at link time on undefined `main`,
the native side blew up at clang IR-parse on undefined
`@__mn_assert_fail`. v5.13.0-prep audit caught the gap; this file
locks in the fix so a re-break trips CI instead of waiting for the
next person to try `mnc test`.

Both cases use a 3-test fixture:
  - one passing assert
  - one passing string equality
  - one failing assert with a custom message

We assert the runner prints PASS / FAIL with the test names, surfaces
the failing test's user message, and exits non-zero overall.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "at_test_smoke.mn"
NATIVE_BIN = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"


def _run_python_test() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "mapanare", "test", str(FIXTURE)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )


def _run_native_test() -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(NATIVE_BIN), "test", str(FIXTURE)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )


def test_fixture_present():
    """Fixture file must exist — the rest of the suite asserts on its content."""
    assert FIXTURE.is_file(), f"missing fixture: {FIXTURE}"
    text = FIXTURE.read_text()
    assert "test_passes" in text
    assert "test_string_eq" in text
    assert "test_fails" in text
    assert "this should fail" in text


def test_python_bootstrap_at_test_runtime():
    """`mapanare test` runs all three tests, surfaces pass/fail correctly."""
    if not shutil.which("clang"):
        pytest.skip("clang not on PATH")
    result = _run_python_test()
    combined = result.stdout + result.stderr
    assert "PASS" in result.stdout, f"no PASS in stdout:\n{combined}"
    assert "FAIL" in result.stdout, f"no FAIL in stdout:\n{combined}"
    assert "test_passes" in result.stdout
    assert "test_string_eq" in result.stdout
    assert "test_fails" in result.stdout
    assert "this should fail" in combined, f"custom assertion message not surfaced:\n{combined}"
    assert result.returncode != 0, f"runner exited 0 despite failing test:\n{combined}"


def test_native_at_test_runtime():
    """`mnc-stage1 test` matches the Python runner's per-test pass/fail output."""
    if not NATIVE_BIN.is_file():
        pytest.skip(f"mnc-stage1 not built: {NATIVE_BIN}")
    if not shutil.which("clang") and not shutil.which("gcc"):
        pytest.skip("no system C compiler on PATH")
    if os.name == "nt":
        pytest.skip("native runner shells out to gcc/clang via /tmp paths — POSIX-only for v5.13.1")
    result = _run_native_test()
    combined = result.stdout + result.stderr
    assert "PASS" in combined, f"no PASS in output:\n{combined}"
    assert "FAIL" in combined, f"no FAIL in output:\n{combined}"
    assert "test_passes" in combined
    assert "test_string_eq" in combined
    assert "test_fails" in combined
    assert "this should fail" in combined, f"custom assertion message not surfaced:\n{combined}"
    assert result.returncode != 0, f"runner exited 0 despite failing test:\n{combined}"
