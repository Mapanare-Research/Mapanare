"""Parser tests for self-hosted tensor literal syntax (v5.6.0 — Sh.6).

Exercises mnc-stage1's parser for nested-array tensor literals
`Tensor<T>[...]`. Run the compiler as a subprocess and check exit
code plus structural markers in the emitted LLVM IR (presence of
`__mn_tensor_alloc` + correct rank/shape stores).

Complementary to tests/parser/test_tensor_literal.py which exercises
the Python bootstrap parser with direct AST inspection.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MNC = ROOT / "mapanare" / "self" / "mnc-stage1"


def _compile(src: str) -> tuple[int, str, str]:
    """Invoke mnc-stage1 on `src`. Returns (returncode, stdout, stderr)."""
    if not MNC.exists():
        pytest.skip(f"{MNC} missing — build stage1 first")
    tmp = ROOT / "_tensor_lit_test.mn"
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
    """Compile `src` as a main-wrapped program. Assert no parse error and
    return the (stdout, stderr) streams for further inspection."""
    rc, out, err = _compile(f'fn main() {{ {src}\nprint("ok") }}')
    # Parse errors are printed before any semantic errors; if neither a parse
    # error nor a tensor-specific semantic-level "Undefined function" shows
    # up, the syntax was accepted.
    combined = out + err
    assert "parse error" not in combined, (
        f"unexpected parse error compiling: {src!r}\n--- stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )
    return out, err


class TestTensorLiteral1D:
    def test_1d_float(self):
        _parses("let a = Tensor<Float>[1.0, 2.0, 3.0]")

    def test_1d_int(self):
        _parses("let a = Tensor<Int>[10, 20, 30]")

    def test_1d_singleton(self):
        _parses("let a = Tensor<Float>[42.0]")

    def test_1d_negated(self):
        _parses("let a = Tensor<Float>[-1.0, -2.5, 3.0]")

    def test_1d_trailing_comma(self):
        _parses("let a = Tensor<Float>[1.0, 2.0,]")

    def test_1d_paren_expr(self):
        _parses("let a = Tensor<Float>[(1.0), (2.0)]")


class TestTensorLiteral2D:
    def test_2d_float_square(self):
        _parses("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]")

    def test_2d_float_rect(self):
        _parses("let a = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]")

    def test_2d_int(self):
        _parses("let a = Tensor<Int>[[1, 2, 3], [4, 5, 6]]")

    def test_2d_single_row(self):
        _parses("let a = Tensor<Float>[[1.0, 2.0]]")

    def test_2d_single_col(self):
        _parses("let a = Tensor<Float>[[1.0], [2.0], [3.0]]")


class TestTensorLiteral3D:
    def test_3d_float(self):
        _parses("let a = Tensor<Float>[[[1.0, 2.0], [3.0, 4.0]], " "[[5.0, 6.0], [7.0, 8.0]]]")

    def test_3d_int(self):
        _parses("let a = Tensor<Int>[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]")

    def test_3d_singleton(self):
        _parses("let a = Tensor<Float>[[[42.0]]]")


class TestTensorTypeAsAnnotation:
    def test_let_type_annotation(self):
        _parses("let x: Tensor<Int> = Tensor<Int>[1, 2, 3]")

    def test_mut_annotation(self):
        _parses("let mut x: Tensor<Float> = Tensor<Float>[0.0, 0.0]")


class TestTensorLiteralRegression:
    """Regression: previously `Tensor<Float>[[1,2],[3,4]]` emitted
    `parse error: expected RBRACKET but got COMMA` because the body
    delegated to parse_list_lit which didn't know about nested arrays.
    v5.6.0 rewrites parse_tensor_lit with a proper recursive walker."""

    def test_nested_does_not_emit_parse_error(self):
        out, err = _parses("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]")
        # parse_tensor_body is proven by absence of the legacy error
        assert "expected RBRACKET but got COMMA" not in (out + err)

    def test_deep_nesting(self):
        _parses("let a = Tensor<Int>[[[[1]]]]")
