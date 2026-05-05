"""v5.42.0 As.5 — link-and-run regression for stdlib/agent/supervisor.mn.

Mirrors the v5.34.0 / v5.35.0 / v5.39.x concatenation harness exactly:
read `stdlib/agent/supervisor.mn`, prepend to each `.mn` test main
body, compile via the Python LLVM emitter, link against
`libmapanare_rt.a`, run, assert "PASSED" appears in stdout (and
"FAIL " does NOT).

Tests cover:
- Strategy semantics (OneForOne, RestForOne, OneForAll)
- Restart limit window enforcement → escalate
- Backoff exponential progression + max cap
- Per-child policy (Permanent / Temporary / Transient) on Normal /
  Crashed exits
- Child-id remapping after restart (replace_child_id)
- Window reset on time-horizon elapse
- Stale notification (no-op for unknown child)

Falsifiability: revert any of the strategy branches in
supervisor_handle_exit / ids_for_strategy and the corresponding
.mn test fails with the recorded FAIL message.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUPERVISOR_MN = REPO_ROOT / "stdlib" / "agent" / "supervisor.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "agent" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_one_for_one.mn",
    "test_rest_for_one.mn",
    "test_one_for_all.mn",
    "test_restart_limit.mn",
    "test_backoff.mn",
    "test_normal_exit.mn",
    "test_replace_child_id.mn",
    "test_window_reset.mn",
    "test_unknown_child.mn",
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def stdlib_source() -> str:
    return SUPERVISOR_MN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    if not RT_ARCHIVE.is_file():
        subprocess.run(
            ["make", "build-rt"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
    return RT_ARCHIVE


def _compile_link_run(
    combined_source: str, label: str, runtime_archive: Path, tmp_path: Path
) -> str:
    from mapanare.cli import _compile_to_llvm_ir

    ir_text = _compile_to_llvm_ir(combined_source, f"{label}.mn")
    ir_path = tmp_path / f"{label}.ll"
    ir_path.write_text(ir_text)

    bin_path = tmp_path / label
    result = subprocess.run(
        [
            "clang",
            str(ir_path),
            str(runtime_archive),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"link failed for {label}:\n{result.stderr}")

    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if run.returncode != 0:
        pytest.fail(
            f"{label} exited nonzero ({run.returncode}):\n"
            f"--- stdout ---\n{run.stdout}\n"
            f"--- stderr ---\n{run.stderr}"
        )
    return run.stdout


@pytest.mark.skipif(not _have_clang(), reason="clang required to link runtime")
@pytest.mark.skipif(not _have_llvmlite(), reason="llvmlite required for MIR LLVM emit")
@pytest.mark.parametrize("test_file", TEST_FILES)
def test_supervisor_strategy(test_file, stdlib_source, runtime_archive, tmp_path):
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = stdlib_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL " in stdout or "FAIL:" in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"
