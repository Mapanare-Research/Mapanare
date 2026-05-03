"""v5.34.0 Dt.* — date / time stdlib tests.

Mirrors the v3.x-era pattern from tests/stdlib/test_crypto.py: read
`stdlib/time.mn`, prepend it to each `.mn` test main body, compile via
the MIR-based LLVM emitter, link against `libmapanare_rt.a`, and run
the resulting binary. Each test prints "<name> PASSED" or "<name> FAILED".

Why concatenation instead of `import time`: cross-module function calls
have a known limitation in both backends (Python LLVM emitter mangles
defined names with the `time__` module prefix but emits unprefixed forward
declarations at call sites; native compiler stage1 does not propagate
extern_fn_def declarations across modules). Every existing stdlib module
is single-file with self-contained tests for the same reason. v5.34.0
ships `stdlib/time.mn` as the surface; tests verify the SAME source code
(concatenated by this harness) produces correct behavior.

Test files under `stdlib/time/tests/`:
  - test_date.mn          — Dt.1 leap-year boundaries + construction
  - test_datetime.mn      — Dt.2 datetime_now + epoch round-trip
  - test_parse_iso.mn     — Dt.3 ISO 8601 + RFC 3339 + duration parsing
  - test_format.mn        — Dt.4 strftime specifier coverage
  - test_arithmetic.mn    — Dt.5 month/day rollover + datetime_diff
  - test_property.mn      — Dt.7 three property-style tests
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TIME_MN = REPO_ROOT / "stdlib" / "time.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "time" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_date.mn",
    "test_datetime.mn",
    "test_parse_iso.mn",
    "test_format.mn",
    "test_arithmetic.mn",
    "test_property.mn",
    "test_tz.mn",
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
def time_mn_source() -> str:
    return TIME_MN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    """Ensure libmapanare_rt.a exists with v5.34.0 mapanare_time.c symbols."""
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
    """Compile combined_source via Python LLVM emitter, link, run; return stdout."""
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
def test_dt_module(test_file, time_mn_source, runtime_archive, tmp_path):
    """Run each Dt.* .mn test file and assert "PASSED" appears in output."""
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = time_mn_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL" in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"


def test_stdlib_time_parses_clean(time_mn_source):
    """stdlib/time.mn parses without errors on its own."""
    from mapanare.parser import parse

    ast = parse(time_mn_source)
    assert len(ast.definitions) > 0


def test_stdlib_time_typechecks_clean(time_mn_source):
    """stdlib/time.mn type-checks without errors on its own."""
    from mapanare.parser import parse
    from mapanare.semantic import check

    ast = parse(time_mn_source)
    errs = check(ast, filename="stdlib/time.mn")
    real_errors = [e for e in errs if getattr(e, "severity", "error") == "error"]
    assert len(real_errors) == 0, f"semantic errors in stdlib/time.mn: {real_errors}"
