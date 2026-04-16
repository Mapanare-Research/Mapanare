"""v4.53.0: Error cascade suppression tests for the self-hosted compiler.

Verifies that a single root-cause error (e.g., undefined function) does NOT
cascade into multiple downstream errors for derived uses. The UNRESOLVED/ERROR
type split ensures that ERROR types propagate silently without firing new
diagnostics.
"""

from __future__ import annotations

import os
import subprocess
import tempfile

import pytest

MNC_STAGE1 = os.path.join(os.path.dirname(__file__), "..", "..", "mapanare", "self", "mnc-stage1")


def _needs_stage1():
    if not os.path.isfile(MNC_STAGE1):
        pytest.skip("mnc-stage1 not built")


def _compile(source: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False) as f:
        f.write(source)
        f.flush()
        try:
            return subprocess.run(
                [MNC_STAGE1, f.name],
                capture_output=True,
                text=True,
                timeout=30,
            )
        finally:
            os.unlink(f.name)


def _error_count(result: subprocess.CompletedProcess[str]) -> int:
    """Count 'error:' occurrences across both stdout and stderr."""
    return (result.stdout + result.stderr).count("error:")


class TestCascadeSuppression:
    def setup_method(self):
        _needs_stage1()

    def test_single_undefined_fn_fires_one_error(self):
        """One undefined function used in 4 downstream expressions → 1 error."""
        result = _compile(
            "fn main() {\n"
            "  let x = unknown_function(42)\n"
            "  let y = x + 1\n"
            "  let z = y.something()\n"
            "  print(z)\n"
            "}\n"
        )
        assert result.returncode == 1
        assert _error_count(result) == 1
        assert "unknown_function" in (result.stdout + result.stderr)

    def test_arithmetic_on_error_suppresses(self):
        """Arithmetic on an error-typed value should not produce operator errors."""
        result = _compile(
            "fn main() {\n"
            "  let x = foo()\n"
            "  let y = x + 1\n"
            "  let z = y * 2\n"
            "  let w = -z\n"
            "}\n"
        )
        assert result.returncode == 1
        assert _error_count(result) == 1
        assert "foo" in (result.stdout + result.stderr)

    def test_field_access_on_error_suppresses(self):
        """Field access on an error-typed value should not produce field errors."""
        result = _compile(
            "fn main() {\n" "  let x = bar()\n" "  let y = x.name\n" "  let z = y.len()\n" "}\n"
        )
        assert result.returncode == 1
        assert _error_count(result) == 1

    def test_method_call_on_error_suppresses(self):
        """Method call on an error-typed value should not produce method errors."""
        result = _compile("fn main() {\n" "  let x = baz()\n" "  let y = x.to_upper()\n" "}\n")
        assert result.returncode == 1
        assert _error_count(result) == 1

    def test_index_on_error_suppresses(self):
        """Index access on an error-typed value should not cascade."""
        result = _compile("fn main() {\n" "  let x = qux()\n" "  let y = x[0]\n" "}\n")
        assert result.returncode == 1
        assert _error_count(result) == 1

    def test_let_type_mismatch_on_error_suppresses(self):
        """Let binding with error-typed initializer should not report type mismatch."""
        result = _compile("fn main() {\n" "  let x: Int = missing_fn()\n" "}\n")
        assert result.returncode == 1
        assert _error_count(result) == 1
        assert "missing_fn" in (result.stdout + result.stderr)

    def test_two_independent_errors_both_report(self):
        """Two independent errors should both be reported (not suppressed)."""
        result = _compile("fn main() {\n" "  let x = foo()\n" "  let y = bar()\n" "}\n")
        assert result.returncode == 1
        assert _error_count(result) == 2

    def test_correct_program_unaffected(self):
        """Correct programs still compile without errors."""
        result = _compile(
            "fn main() {\n" "  let x: Int = 42\n" "  let y = x + 1\n" "  print(str(y))\n" "}\n"
        )
        assert result.returncode == 0
        assert _error_count(result) == 0
