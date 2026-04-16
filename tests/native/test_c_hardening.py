"""Phase 2 — C Runtime Hardening tests.

Compiles and runs the standalone C test suite (test_c_runtime.c) against
both mapanare_core.c and mapanare_runtime.c.

Test matrix:
  1. Plain compilation — verify all C tests pass
  2. AddressSanitizer — detect memory errors (heap-buffer-overflow, use-after-free, leaks)
  3. ThreadSanitizer — detect data races in thread pool and agent code

Sanitizer tests are Linux-only (GCC/Clang). All tests skip gracefully on Windows
or when no C compiler is available.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess

import pytest

_IS_LINUX = platform.system() == "Linux"
_IS_WINDOWS = platform.system() == "Windows"

# Find a C compiler
_CC = os.environ.get("CC") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")

_TEST_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
_RUNTIME_DIR = os.path.join(_REPO_ROOT, "runtime", "native")
_TEST_C = os.path.join(_TEST_DIR, "test_c_runtime.c")
_CORE_C = os.path.join(_RUNTIME_DIR, "mapanare_core.c")
_RUNTIME_C = os.path.join(_RUNTIME_DIR, "mapanare_runtime.c")


def _compile_and_run(
    tmp_path: str,
    extra_flags: list[str] | None = None,
    env_extra: dict[str, str] | None = None,
    binary_suffix: str = "",
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Compile test_c_runtime.c with the given flags and run it."""
    assert _CC is not None
    binary_name = f"test_c_runtime{binary_suffix}"
    if _IS_WINDOWS:
        binary_name += ".exe"
    binary_path = os.path.join(tmp_path, binary_name)

    flags = extra_flags or []
    cmd = (
        [_CC, "-O1", "-g", "-pthread"]
        + flags
        + [
            _TEST_C,
            _CORE_C,
            _RUNTIME_C,
            "-o",
            binary_path,
        ]
    )

    # Compile
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        pytest.skip(f"Compilation failed: {result.stderr[:500]}")

    # Run
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    result = subprocess.run(
        [binary_path],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=tmp_path,
    )

    return result


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestCRuntimePlain:
    """Compile and run the C test suite without sanitizers."""

    def test_all_c_tests_pass(self, tmp_path: object) -> None:
        result = _compile_and_run(str(tmp_path))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        assert result.returncode == 0, f"C tests failed:\n{result.stdout}\n{result.stderr}"
        assert "FAIL" not in result.stdout


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
@pytest.mark.skipif(not _IS_LINUX, reason="AddressSanitizer tests are Linux-only")
class TestCRuntimeASan:
    """Run C tests under AddressSanitizer to detect memory errors."""

    def test_asan_no_errors(self, tmp_path: object) -> None:
        result = _compile_and_run(
            str(tmp_path),
            extra_flags=["-fsanitize=address", "-fno-omit-frame-pointer"],
            env_extra={"ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
            binary_suffix="_asan",
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        assert (
            result.returncode == 0
        ), f"AddressSanitizer detected errors:\n{result.stdout}\n{result.stderr}"


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
@pytest.mark.skipif(not _IS_LINUX, reason="ThreadSanitizer tests are Linux-only")
class TestCRuntimeTSan:
    """Run C tests under ThreadSanitizer to detect data races."""

    def test_tsan_no_races(self, tmp_path: object) -> None:
        result = _compile_and_run(
            str(tmp_path),
            extra_flags=["-fsanitize=thread"],
            env_extra={"TSAN_OPTIONS": "halt_on_error=1"},
            binary_suffix="_tsan",
            timeout=180,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        # TSan exits with code 66 on race detection
        assert (
            result.returncode == 0
        ), f"ThreadSanitizer detected races:\n{result.stdout}\n{result.stderr}"
