"""Integration tests — compile golden .mn files through the full LLVM pipeline.

Each test takes a golden .mn file through:
  emit-llvm → llvm-as → opt -O2 → llc -filetype=obj → clang link → execute

Stdout is compared against tests/integration/expected/<name>.expected.
"""

from __future__ import annotations

import pytest

from tests.integration.conftest import (
    EXTERNAL_RESOURCE_TESTS,
    discover_golden_tests,
    full_pipeline,
)

GOLDEN_TESTS = discover_golden_tests()

# v4.77.0: known failures — these are tracked, not ignored.
# Each entry maps test stem → (xfail reason, failing stage).
KNOWN_FAILURES: dict[str, str] = {
    # emit-llvm does not yet support the try operator (?) in LLVM backend
    "47_try_operator": "try operator emits IR with type mismatch (llvm-as rejects)",
    # emit-llvm does not yet support combined guard+or match patterns
    "51_match_guards_and_or": "combined guard+or match patterns not yet in emit-llvm",
    # async/await emit-llvm not yet implemented
    "55_async_basic": "async/await not yet implemented in emit-llvm",
    "56_async_await": "async/await not yet implemented in emit-llvm",
    "57_real_await": "async/await not yet implemented in emit-llvm",
}


@pytest.mark.parametrize(
    "source",
    GOLDEN_TESTS,
    ids=[p.stem for p in GOLDEN_TESTS],
)
def test_golden_pipeline(source, tmp_path, integration_stage):
    """Run a golden test through the full LLVM pipeline."""
    test_name = source.stem

    # Skip tests that need external resources
    if test_name in EXTERNAL_RESOURCE_TESTS:
        pytest.skip(f"{test_name} requires external resources")

    # Mark known failures as xfail so they don't block CI
    if test_name in KNOWN_FAILURES:
        pytest.xfail(KNOWN_FAILURES[test_name])

    result = full_pipeline(source, tmp_path, stop_after=integration_stage)

    # Report which stage was reached even on failure
    if not result.passed:
        stage = result.stage_reached
        errors = result.errors
        failed_stage = next(iter(errors)) if errors else "unknown"
        error_msg = errors.get(failed_stage, "no error captured")

        pytest.fail(
            f"Pipeline stopped at '{stage}', failed at '{failed_stage}'.\n"
            f"Error:\n{error_msg}"
        )
