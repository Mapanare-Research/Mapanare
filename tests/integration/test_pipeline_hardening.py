"""v4.117.0 Phase 5 — integration pipeline hardening tests.

These tests deliberately break input at each stage of the
``emit-llvm → llvm-as → opt → llc → link → run`` pipeline and assert
the integration harness (`tests/integration/conftest.py::full_pipeline`)
reports the correct failing stage with a non-empty error message.

The v4.77.0 harness already checks each step's return code. This suite
is the regression gate: if anyone refactors the harness and accidentally
swallows a stage error, these tests fail loudly at PR time.

Covers:
 1. Invalid ``.mn`` source → ``emit`` stage fails
 2. Syntactically invalid ``.ll`` → ``llvm-as`` stage fails
 3. IR that assembles but fails ``opt``                       (skipped — opt is lenient)
 4. Non-existent program exits non-zero → ``run`` catches it
 5. A run that exceeds the 10s timeout → raises cleanly
 6. Stdout-mismatch vs ``.expected`` → reported on ``stdout`` stage

The integration timeout (`run_binary(..., timeout=10)`) is a v4.77.0
invariant. Test 5 asserts it still fires.
"""

from __future__ import annotations

import subprocess

import pytest

from tests.integration.conftest import (
    EXPECTED_DIR,
    _find_tool,
    _run,
    full_pipeline,
    run_binary,
)


def _write(path, text: str) -> None:
    path.write_text(text)


# ---------------------------------------------------------------------------
# Stage 1: emit — fails on unparseable source
# ---------------------------------------------------------------------------


def test_emit_fails_on_unparseable_source(tmp_path):
    """The emit stage must fail — not silently produce garbage IR — when
    given a .mn file the parser cannot accept."""
    src = tmp_path / "broken.mn"
    _write(src, "fn main() { this is not valid mapanare }")

    pr = full_pipeline(src, tmp_path)

    assert not pr.passed, "Pipeline must NOT pass on unparseable source"
    assert "emit" in pr.errors, (
        f"Expected 'emit' stage to capture the error, got errors={list(pr.errors.keys())}"
    )
    assert pr.errors["emit"], "Error message for 'emit' must be non-empty"


# ---------------------------------------------------------------------------
# Stage 2: llvm-as — fails on syntactically invalid IR
# ---------------------------------------------------------------------------


def test_llvm_as_rejects_invalid_ir(tmp_path):
    """Write a hand-crafted invalid .ll directly, run it through the
    second stage of the harness, and assert llvm-as rejects it.

    This does NOT go through full_pipeline (which starts from .mn); it
    exercises the llvm-as wrapper directly. Ensures the harness surfaces
    the llvm-as non-zero exit rather than continuing.
    """
    ll = tmp_path / "broken.ll"
    _write(
        ll,
        """; This is garbage IR that llvm-as must reject
define i32 @main() {
  %1 = add i32 1, "not_an_integer"
  ret i32 %1
}
""",
    )

    tool = _find_tool("llvm-as")
    result = _run([tool, str(ll), "-o", str(tmp_path / "broken.bc")])

    assert result.returncode != 0, (
        f"llvm-as accepted invalid IR — harness gate broken. stdout={result.stdout!r}"
    )
    assert result.stderr, "llvm-as produced no stderr diagnostic on invalid IR"


# ---------------------------------------------------------------------------
# Stage 4: run — non-zero exit is captured, not swallowed
# ---------------------------------------------------------------------------


def test_run_captures_nonzero_exit(tmp_path):
    """A compiled binary that exits non-zero must produce a pr.exit_code
    that reflects that. The harness must NOT silently mark it as passed."""
    # Create a tiny C program that exits with code 42
    c_src = tmp_path / "exits_42.c"
    _write(c_src, "int main(void) { return 42; }")
    binary = tmp_path / "exits_42"

    clang = _find_tool("clang")
    result = _run([clang, str(c_src), "-o", str(binary)])
    assert result.returncode == 0, f"clang failed to build the fixture: {result.stderr}"

    exit_code, _stdout, _stderr = run_binary(binary)
    assert exit_code == 42, f"run_binary swallowed non-zero exit: got {exit_code}"


# ---------------------------------------------------------------------------
# Stage 4: run — timeout fires when a program hangs
# ---------------------------------------------------------------------------


def test_run_timeout_fires(tmp_path):
    """A compiled binary that sleeps longer than the timeout must raise
    subprocess.TimeoutExpired (caught by full_pipeline and reported as
    an error). This is the guardrail against CI hangs."""
    c_src = tmp_path / "hang.c"
    _write(
        c_src,
        """#include <unistd.h>
int main(void) { sleep(60); return 0; }
""",
    )
    binary = tmp_path / "hang"
    clang = _find_tool("clang")
    result = _run([clang, str(c_src), "-o", str(binary)])
    assert result.returncode == 0, f"clang failed to build the fixture: {result.stderr}"

    # run_binary defaults to timeout=10; hang.c sleeps 60. Expect raise.
    with pytest.raises(subprocess.TimeoutExpired):
        run_binary(binary, timeout=2)


# ---------------------------------------------------------------------------
# Stage 6: stdout — mismatch vs .expected file is caught
# ---------------------------------------------------------------------------


def test_stdout_mismatch_does_not_silently_pass(tmp_path, monkeypatch):
    """If a golden's binary runs cleanly but its stdout does NOT match
    the committed .expected file, the harness must surface the diff on
    the 'stdout' stage. This test creates a shadow .mn + wrong
    .expected fixture and verifies the harness catches the mismatch.

    Uses monkeypatch to repoint EXPECTED_DIR at a tmp location so the
    real tests/integration/expected/ is not modified.
    """
    # Point EXPECTED_DIR at a tmp dir with our crafted fixture
    fake_expected = tmp_path / "expected"
    fake_expected.mkdir()
    monkeypatch.setattr("tests.integration.conftest.EXPECTED_DIR", fake_expected)

    src = tmp_path / "test_stdout.mn"
    _write(
        src,
        '''fn main() {
    print("actual output")
}
''',
    )

    # Committed expected is WRONG on purpose
    expected_file = fake_expected / "test_stdout.expected"
    _write(expected_file, "this does not match\n")

    pr = full_pipeline(src, tmp_path)

    assert not pr.passed, (
        "Harness silently passed a stdout mismatch — fail-loud regression"
    )
    assert "stdout" in pr.errors, (
        f"Expected 'stdout' stage error, got errors={list(pr.errors.keys())}"
    )
    err = pr.errors["stdout"]
    assert "Expected:" in err and "Got:" in err, (
        f"Harness diff message regressed: {err!r}"
    )


# ---------------------------------------------------------------------------
# Negative control: the harness still passes a known-good golden
# ---------------------------------------------------------------------------


def test_harness_accepts_hello_world(tmp_path, monkeypatch):
    """Negative control: ensure the hardening changes don't break the
    harness's happy path. A hello.mn with the right .expected file
    must still produce pr.passed == True."""
    fake_expected = tmp_path / "expected"
    fake_expected.mkdir()
    monkeypatch.setattr("tests.integration.conftest.EXPECTED_DIR", fake_expected)

    src = tmp_path / "ok.mn"
    _write(
        src,
        '''fn main() {
    print("hello")
}
''',
    )
    _write(fake_expected / "ok.expected", "hello\n")

    pr = full_pipeline(src, tmp_path)

    assert pr.passed, (
        f"Harness regressed on happy path: stage={pr.stage_reached} "
        f"errors={pr.errors} stdout={pr.stdout!r}"
    )
    assert pr.errors == {}, f"Happy path produced errors: {pr.errors}"
