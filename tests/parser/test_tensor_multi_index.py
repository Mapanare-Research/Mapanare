"""Parser tests for self-hosted multi-dim tensor indexing (v5.6.1 — Sh.6 Phase 2).

Exercises mnc-stage1's parser for `a[i, j]` / `a[i, j, k]` subscripts
and the multi-dim assignment target `d[i, j] = val`. Complements
`tests/parser/test_tensor_indexing.py` which tests the Python bootstrap.

Compiles programs via mnc-stage1 and asserts absence of parse errors.
Single-subscript `a[i]` must still route through the existing path
(list/map/string index) without regression.
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
    tmp = ROOT / "_tensor_mi_test.mn"
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


class TestMultiIndexRead:
    def test_single_index_tensor(self):
        _parses("let a = Tensor<Float>[10.0, 20.0]\nprint(str(a[0]))")

    def test_two_indices(self):
        _parses("let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]\n" "print(str(a[0, 1]))")

    def test_three_indices(self):
        _parses(
            "let a = Tensor<Float>[[[1.0, 2.0], [3.0, 4.0]], "
            "[[5.0, 6.0], [7.0, 8.0]]]\n"
            "print(str(a[0, 1, 1]))"
        )

    def test_expression_indices(self):
        _parses(
            "let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]\n"
            "let i = 0\nlet j = 1\n"
            "print(str(a[i + 0, j * 1]))"
        )

    def test_int_tensor_two_indices(self):
        _parses("let a = Tensor<Int>[[1, 2], [3, 4]]\n" "print(str(a[1, 1]))")


class TestMultiIndexWrite:
    def test_two_index_assign(self):
        _parses(
            "let mut d = Tensor<Float>[[0.0, 0.0], [0.0, 0.0]]\n"
            "d[0, 0] = 42.0\n"
            "print(str(d[0, 0]))"
        )

    def test_three_index_assign(self):
        _parses(
            "let mut d = Tensor<Float>[[[0.0]]]\n" "d[0, 0, 0] = 7.0\n" "print(str(d[0, 0, 0]))"
        )


class TestSingleIndexPreserved:
    """a[i] on a List must keep the existing Expr::Index path."""

    def test_list_single(self):
        _parses("let xs = [10, 20, 30]\nprint(str(xs[1]))")

    def test_string_single(self):
        _parses('let s = "abc"\nprint(s[1])')

    def test_map_single(self):
        _parses('let m: Map<String, Int> = {"a": 1}\nprint(str(m["a"]))')


class TestChainedIndex:
    """`a[i][j]` is two separate Index expressions, not a tensor multi-index."""

    def test_list_of_list(self):
        _parses("let g: List<List<Int>> = [[1, 2], [3, 4]]\n" "print(str(g[0][1]))")
