"""Parser tests for self-hosted tensor slicing (v5.6.3 — Sh.6 Phase 4).

Exercises mnc-stage1's parser for range (`a[1..3]`), wildcard (`a[_]`),
and mixed (`a[0..2, _]`) subscripts. Complements the v5.6.1 multi-index
tests — scalar-only subscripts must still route through Index /
TensorIndex without regression.

Compiles programs via mnc-stage1 and asserts absence of parse errors.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MNC = ROOT / "mapanare" / "self" / "mnc-stage1"


def _compile(src: str) -> tuple[int, str, str]:
    if not MNC.exists():
        pytest.skip(f"{MNC} missing — build stage1 first")
    tmp = ROOT / "_tensor_slice_test.mn"
    tmp.write_text(src)
    try:
        p = subprocess.run(
            [str(MNC), str(tmp)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT),
        )
        return p.returncode, p.stdout, p.stderr
    finally:
        tmp.unlink(missing_ok=True)


def _parses(src: str) -> tuple[str, str]:
    rc, out, err = _compile(f'fn main() {{ {src}\nprint("ok") }}')
    combined = out + err
    assert "parse error" not in combined, (
        f"unexpected parse error compiling: {src!r}\n--- stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )
    return out, err


class TestRangeSubscript:
    def test_bounded_range_1d(self):
        _parses(
            "let a = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0]\n" "let s = a[1..3]\nprint(str(s[0]))"
        )

    def test_open_start_range(self):
        _parses("let a = Tensor<Float>[1.0, 2.0, 3.0]\n" "let s = a[..2]\nprint(str(s[0]))")

    def test_open_end_range(self):
        _parses("let a = Tensor<Float>[1.0, 2.0, 3.0]\n" "let s = a[1..]\nprint(str(s[0]))")


class TestWildcardSubscript:
    def test_bare_wildcard_1d(self):
        _parses("let a = Tensor<Float>[1.0, 2.0, 3.0]\n" "let s = a[_]\nprint(str(s[0]))")

    def test_range_with_wildcard_2d(self):
        _parses(
            "let d = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]\n"
            "let row = d[0..1, _]\nprint(str(row[0]))"
        )

    def test_wildcard_with_scalar_2d(self):
        _parses(
            "let d = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]\n"
            "let col = d[_, 0]\nprint(str(col[0]))"
        )


class TestScalarPreserved:
    """Scalar-only subscripts must still route through Index / TensorIndex."""

    def test_single_scalar_list(self):
        _parses("let xs = [10, 20, 30]\nprint(str(xs[1]))")

    def test_two_scalars_tensor(self):
        _parses("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]\n" "print(str(a[1, 1]))")

    def test_three_scalars_tensor(self):
        _parses("let a = Tensor<Float>[[[1.0, 2.0]], [[3.0, 4.0]]]\n" "print(str(a[1, 0, 0]))")


class TestMixedItems:
    def test_range_then_scalar(self):
        _parses(
            "let d = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]\n"
            "let x = d[0..1, 2]\nprint(str(x[0]))"
        )

    def test_scalar_then_range(self):
        _parses(
            "let d = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]\n"
            "let x = d[1, 1..3]\nprint(str(x[0]))"
        )
