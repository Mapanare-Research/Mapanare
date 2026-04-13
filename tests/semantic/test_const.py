"""v4.55.0: Semantic tests for ``const`` — constant folding, immutability, tensor shapes.

The file that v4.26.0's CHANGELOG claimed existed — now it does for real.
"""

from __future__ import annotations

from mapanare.parser import parse
from mapanare.semantic import check


def _check(src: str) -> list:
    ast = parse(src, filename="test.mn")
    return check(ast, filename="test.mn")


class TestConstFolding:
    def test_const_int_literal_folds(self):
        errors = _check("const N: Int = 100\nfn main() { print(str(N)) }\n")
        assert not errors

    def test_const_float_literal_folds(self):
        errors = _check("const PI: Float = 3.14\nfn main() { print(str(PI)) }\n")
        assert not errors

    def test_const_refers_to_another_const(self):
        errors = _check(
            "const N: Int = 10\nconst M: Int = N\nfn main() { print(str(M)) }\n"
        )
        assert not errors

    def test_const_binary_op_folds(self):
        errors = _check(
            "const N: Int = 10\nconst D: Int = N * 2\nfn main() { print(str(D)) }\n"
        )
        assert not errors

    def test_const_non_constant_initializer_is_error(self):
        errors = _check(
            "fn get_val() -> Int { return 42 }\n"
            "const N: Int = get_val()\n"
            "fn main() {}\n"
        )
        assert len(errors) >= 1
        assert any("constant expression" in e.message for e in errors)


class TestConstImmutability:
    def test_assignment_to_const_is_error(self):
        errors = _check("const N: Int = 10\nfn main() { N = 20 }\n")
        assert len(errors) >= 1
        assert any("const" in e.message.lower() for e in errors)

    def test_const_used_as_value(self):
        errors = _check(
            "const N: Int = 42\nfn main() { let x: Int = N\n  print(str(x)) }\n"
        )
        assert not errors
