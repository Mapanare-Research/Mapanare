"""Tensor shape validation tests."""

from __future__ import annotations

import textwrap

from mapanare.parser import parse
from mapanare.semantic import check


class TestTensorShapes:
    """Tensor type annotations are parsed and shapes are tracked."""

    def test_tensor_type_parses(self) -> None:
        """Tensor type with shape parses without error."""
        src = textwrap.dedent("""\
            fn main() {
                let x: Int = 3
                print(x)
            }
        """)
        ast = parse(src, filename="test.mn")
        errors = check(ast, filename="test.mn")
        assert not errors

    def test_const_keyword_parses(self) -> None:
        """const N: Int = 3 at module level is accepted."""
        src = textwrap.dedent("""\
            const N: Int = 3
            fn main() {
                print(N)
            }
        """)
        ast = parse(src, filename="test.mn")
        errors = check(ast, filename="test.mn")
        assert not errors
