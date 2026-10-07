"""The bootstrap gate must reject crashes, empty IR, and any output drift."""

import sys
from pathlib import Path

import pytest

from scripts.verify_fixed_point import require_fixed_point, run_checked, validate_ir


def test_compiler_crash_with_output_is_failure(tmp_path: Path) -> None:
    output = tmp_path / "stage3.ll"
    with pytest.raises(RuntimeError, match="exit 7"):
        run_checked(
            [sys.executable, "-c", "print('valid-looking IR'); raise SystemExit(7)"], output
        )
    assert output.read_text().strip() == "valid-looking IR"


def test_empty_ir_is_failure(tmp_path: Path) -> None:
    output = tmp_path / "empty.ll"
    output.touch()
    with pytest.raises(RuntimeError, match="empty"):
        validate_ir(output)


@pytest.mark.parametrize("other", [b"", b"same\n ", b"different\n"])
def test_fixed_point_has_no_tolerance(tmp_path: Path, other: bytes) -> None:
    first, second = tmp_path / "stage2.ll", tmp_path / "stage3.ll"
    first.write_bytes(b"same\n")
    second.write_bytes(other)
    with pytest.raises(RuntimeError, match="strict fixed point failed"):
        require_fixed_point(first, second)


def test_identical_nonempty_stages_pass(tmp_path: Path) -> None:
    first, second = tmp_path / "stage2.ll", tmp_path / "stage3.ll"
    first.write_bytes(b"same\n")
    second.write_bytes(b"same\n")
    require_fixed_point(first, second)
