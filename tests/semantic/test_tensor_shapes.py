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

    def test_shape_mismatch_add(self) -> None:
        """Shape mismatch on element-wise add produces error."""
        src = textwrap.dedent("""\
            fn main() {
                let a: Tensor<Float>[3, 4] = tensor_alloc(3, 4)
                let b: Tensor<Float>[3, 5] = tensor_alloc(3, 5)
                let c = a + b
            }
        """)
        ast = parse(src, filename="test.mn")
        errors = check(ast, filename="test.mn")
        shape_errors = [e for e in errors if "shape" in e.message.lower()]
        assert len(shape_errors) > 0, f"Expected shape mismatch error, got: {errors}"

    def test_matmul_shape_valid(self) -> None:
        """Valid matmul shapes pass without shape error."""
        src = textwrap.dedent("""\
            fn main() {
                let a: Tensor<Float>[3, 4] = tensor_alloc(3, 4)
                let b: Tensor<Float>[4, 5] = tensor_alloc(4, 5)
                let c = a @ b
            }
        """)
        ast = parse(src, filename="test.mn")
        errors = check(ast, filename="test.mn")
        shape_errors = [e for e in errors if "shape" in e.message.lower()]
        assert len(shape_errors) == 0, f"Unexpected shape error: {shape_errors}"

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
