"""Tests for Mapanare tensor runtime (Phase 5.1)."""

import pytest

from mapa.tensor import (
    ShapeError,
    Tensor,
    _shape_size,
    matmul,
    resolve_shape_from_type,
    validate_elementwise_shapes,
    validate_matmul_shapes,
)

# =====================================================================
# Task 1: Tensor memory layout and allocation
# =====================================================================


class TestTensorCreation:
    """Test tensor creation and memory layout."""

    def test_zeros(self) -> None:
        t = Tensor.zeros((3,))
        assert t.shape == (3,)
        assert t.data == [0.0, 0.0, 0.0]
        assert t.size == 3
        assert t.ndim == 1

    def test_ones(self) -> None:
        t = Tensor.ones((2, 3))
        assert t.shape == (2, 3)
        assert t.size == 6
        assert all(x == 1.0 for x in t.data)

    def test_full(self) -> None:
        t = Tensor.full((2, 2), 5.0)
        assert t.data == [5.0, 5.0, 5.0, 5.0]

    def test_from_list_1d(self) -> None:
        t = Tensor.from_list([1.0, 2.0, 3.0])
        assert t.shape == (1, 2, 3) or t.shape == (3,)
        assert t.data == [1.0, 2.0, 3.0]

    def test_from_list_with_shape(self) -> None:
        t = Tensor.from_list([1, 2, 3, 4, 5, 6], (2, 3))
        assert t.shape == (2, 3)
        assert t.size == 6

    def test_from_nested(self) -> None:
        t = Tensor.from_nested([[1, 2, 3], [4, 5, 6]])
        assert t.shape == (2, 3)
        assert t.data == [1, 2, 3, 4, 5, 6]

    def test_identity(self) -> None:
        t = Tensor.identity(3)
        assert t.shape == (3, 3)
        assert t.get(0, 0) == 1.0
        assert t.get(1, 1) == 1.0
        assert t.get(2, 2) == 1.0
        assert t.get(0, 1) == 0.0

    def test_data_shape_mismatch_raises(self) -> None:
        with pytest.raises(ShapeError, match="does not match shape"):
            Tensor([1, 2, 3], (2, 2))

    def test_negative_dim_raises(self) -> None:
        with pytest.raises(ShapeError, match="Negative dimension"):
            _shape_size((-1, 3))


class TestTensorLayout:
    """Test row-major memory layout."""

    def test_row_major_order(self) -> None:
        """2x3 matrix in row-major: row 0 then row 1."""
        t = Tensor.from_nested([[1, 2, 3], [4, 5, 6]])
        assert t.data == [1, 2, 3, 4, 5, 6]  # row-major

    def test_indexing_2d(self) -> None:
        t = Tensor.from_list([1, 2, 3, 4, 5, 6], (2, 3))
        assert t.get(0, 0) == 1
        assert t.get(0, 2) == 3
        assert t.get(1, 0) == 4
        assert t.get(1, 2) == 6

    def test_indexing_3d(self) -> None:
        data = list(range(24))
        t = Tensor.from_list(data, (2, 3, 4))
        assert t.get(0, 0, 0) == 0
        assert t.get(1, 2, 3) == 23
        assert t.ndim == 3

    def test_set_element(self) -> None:
        t = Tensor.zeros((2, 2))
        t.set(1, 0, 42.0)
        assert t.get(1, 0) == 42.0

    def test_index_out_of_bounds(self) -> None:
        t = Tensor.zeros((2, 3))
        with pytest.raises(IndexError):
            t.get(2, 0)

    def test_wrong_ndim_indexing(self) -> None:
        t = Tensor.zeros((2, 3))
        with pytest.raises(ShapeError, match="Expected 2 indices"):
            t.get(0)


class TestTensorReshape:
    """Test reshape and transpose."""

    def test_reshape(self) -> None:
        t = Tensor.from_list([1, 2, 3, 4, 5, 6], (2, 3))
        r = t.reshape((3, 2))
        assert r.shape == (3, 2)
        assert r.data == [1, 2, 3, 4, 5, 6]

    def test_reshape_to_1d(self) -> None:
        t = Tensor.from_list([1, 2, 3, 4], (2, 2))
        r = t.reshape((4,))
        assert r.shape == (4,)

    def test_reshape_invalid_size(self) -> None:
        t = Tensor.zeros((2, 3))
        with pytest.raises(ShapeError, match="Cannot reshape"):
            t.reshape((2, 2))

    def test_transpose(self) -> None:
        t = Tensor.from_nested([[1, 2, 3], [4, 5, 6]])
        tr = t.transpose()
        assert tr.shape == (3, 2)
        assert tr.get(0, 0) == 1
        assert tr.get(0, 1) == 4
        assert tr.get(2, 0) == 3
        assert tr.get(2, 1) == 6

    def test_transpose_non_2d_raises(self) -> None:
        t = Tensor.zeros((2, 3, 4))
        with pytest.raises(ShapeError, match="transpose requires 2D"):
            t.transpose()


class TestTensorReductions:
    """Test sum, mean, max, min."""

    def test_sum(self) -> None:
        t = Tensor.from_list([1, 2, 3, 4])
        assert t.sum() == 10

    def test_mean(self) -> None:
        t = Tensor.from_list([2, 4, 6, 8])
        assert t.mean() == 5.0

    def test_max(self) -> None:
        t = Tensor.from_list([3, 1, 4, 1, 5])
        assert t.max() == 5

    def test_min(self) -> None:
        t = Tensor.from_list([3, 1, 4, 1, 5])
        assert t.min() == 1


# =====================================================================
# Task 2: Matrix multiply @ → BLAS or custom SIMD
# =====================================================================


class TestMatmul:
    """Test matrix multiply operations."""

    def test_matmul_2d_basic(self) -> None:
        """(2,3) @ (3,2) → (2,2)."""
        a = Tensor.from_nested([[1, 2, 3], [4, 5, 6]])
        b = Tensor.from_nested([[7, 8], [9, 10], [11, 12]])
        c = a @ b
        assert c.shape == (2, 2)
        assert c.get(0, 0) == 58  # 1*7 + 2*9 + 3*11
        assert c.get(0, 1) == 64  # 1*8 + 2*10 + 3*12
        assert c.get(1, 0) == 139  # 4*7 + 5*9 + 6*11
        assert c.get(1, 1) == 154  # 4*8 + 5*10 + 6*12

    def test_matmul_identity(self) -> None:
        """A @ I == A."""
        a = Tensor.from_nested([[1, 2], [3, 4]])
        i = Tensor.identity(2)
        result = a @ i
        assert result == a

    def test_matmul_dot_product(self) -> None:
        """1D @ 1D → dot product."""
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([4, 5, 6])
        c = a @ b
        assert c.shape == (1,)
        assert c.data[0] == 32  # 1*4 + 2*5 + 3*6

    def test_matmul_matrix_vector(self) -> None:
        """(2,3) @ (3,) → (2,)."""
        a = Tensor.from_nested([[1, 2, 3], [4, 5, 6]])
        b = Tensor.from_list([1, 0, 1])
        c = a @ b
        assert c.shape == (2,)
        assert c.data[0] == 4  # 1*1 + 2*0 + 3*1
        assert c.data[1] == 10  # 4*1 + 5*0 + 6*1

    def test_matmul_vector_matrix(self) -> None:
        """(3,) @ (3,2) → (2,)."""
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_nested([[1, 2], [3, 4], [5, 6]])
        c = a @ b
        assert c.shape == (2,)
        assert c.data[0] == 22  # 1*1 + 2*3 + 3*5
        assert c.data[1] == 28  # 1*2 + 2*4 + 3*6

    def test_matmul_shape_mismatch(self) -> None:
        a = Tensor.from_nested([[1, 2], [3, 4]])
        b = Tensor.from_nested([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        with pytest.raises(ShapeError, match="inner dimensions"):
            a @ b

    def test_matmul_1d_mismatch(self) -> None:
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([1, 2])
        with pytest.raises(ShapeError, match="Dot product shape mismatch"):
            a @ b

    def test_matmul_3d_unsupported(self) -> None:
        a = Tensor.zeros((2, 3, 4))
        b = Tensor.zeros((2, 4, 3))
        with pytest.raises(ShapeError, match="not supported"):
            a @ b

    def test_matmul_square(self) -> None:
        """(3,3) @ (3,3) → (3,3)."""
        a = Tensor.from_nested([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        b = Tensor.from_nested([[2, 3, 4], [5, 6, 7], [8, 9, 10]])
        c = a @ b
        assert c == b  # identity @ anything = anything

    def test_matmul_function(self) -> None:
        a = Tensor.from_nested([[1, 2], [3, 4]])
        b = Tensor.from_nested([[5, 6], [7, 8]])
        c = matmul(a, b)
        assert c.shape == (2, 2)
        assert c.get(0, 0) == 19  # 1*5 + 2*7


# =====================================================================
# Task 3: Element-wise ops → LLVM SIMD vectorized
# =====================================================================


class TestElementwiseOps:
    """Test element-wise tensor operations."""

    def test_add_tensors(self) -> None:
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([4, 5, 6])
        c = a + b
        assert c.data == [5, 7, 9]

    def test_sub_tensors(self) -> None:
        a = Tensor.from_list([10, 20, 30])
        b = Tensor.from_list([1, 2, 3])
        c = a - b
        assert c.data == [9, 18, 27]

    def test_mul_tensors(self) -> None:
        a = Tensor.from_list([2, 3, 4])
        b = Tensor.from_list([5, 6, 7])
        c = a * b
        assert c.data == [10, 18, 28]

    def test_div_tensors(self) -> None:
        a = Tensor.from_list([10.0, 20.0, 30.0])
        b = Tensor.from_list([2.0, 5.0, 10.0])
        c = a / b
        assert c.data == [5.0, 4.0, 3.0]

    def test_scalar_add(self) -> None:
        t = Tensor.from_list([1, 2, 3])
        c = t + 10
        assert c.data == [11, 12, 13]

    def test_scalar_mul(self) -> None:
        t = Tensor.from_list([1, 2, 3])
        c = t * 2
        assert c.data == [2, 4, 6]

    def test_neg(self) -> None:
        t = Tensor.from_list([1, -2, 3])
        c = -t
        assert c.data == [-1, 2, -3]

    def test_elementwise_shape_mismatch(self) -> None:
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([1, 2])
        with pytest.raises(ShapeError, match="Shape mismatch"):
            a + b

    def test_elementwise_2d(self) -> None:
        a = Tensor.from_nested([[1, 2], [3, 4]])
        b = Tensor.from_nested([[5, 6], [7, 8]])
        c = a + b
        assert c.shape == (2, 2)
        assert c.data == [6, 8, 10, 12]


# =====================================================================
# Task 4: Compile-time shape validation
# =====================================================================


class TestCompileTimeShapeValidation:
    """Test shape validation utilities for the semantic checker."""

    def test_validate_matmul_2d_valid(self) -> None:
        result = validate_matmul_shapes((2, 3), (3, 4))
        assert result == (2, 4)

    def test_validate_matmul_2d_invalid(self) -> None:
        result = validate_matmul_shapes((2, 3), (4, 5))
        assert result is None

    def test_validate_matmul_1d_dot(self) -> None:
        result = validate_matmul_shapes((3,), (3,))
        assert result == (1,)

    def test_validate_matmul_1d_mismatch(self) -> None:
        result = validate_matmul_shapes((3,), (4,))
        assert result is None

    def test_validate_matmul_mv(self) -> None:
        result = validate_matmul_shapes((2, 3), (3,))
        assert result == (2,)

    def test_validate_matmul_vm(self) -> None:
        result = validate_matmul_shapes((3,), (3, 2))
        assert result == (2,)

    def test_validate_elementwise_same(self) -> None:
        assert validate_elementwise_shapes((2, 3), (2, 3)) is True

    def test_validate_elementwise_different(self) -> None:
        assert validate_elementwise_shapes((2, 3), (3, 2)) is False

    def test_resolve_shape_from_int_literals(self) -> None:
        from mapa.ast_nodes import IntLiteral

        exprs = [IntLiteral(value=3), IntLiteral(value=3)]
        result = resolve_shape_from_type(exprs)
        assert result == (3, 3)

    def test_resolve_shape_dynamic(self) -> None:
        from mapa.ast_nodes import Identifier

        exprs = [Identifier(name="n")]
        result = resolve_shape_from_type(exprs)
        assert result is None


# =====================================================================
# Task 5: Runtime shape checks for dynamic shapes
# =====================================================================


class TestRuntimeShapeChecks:
    """Test runtime shape validation during operations."""

    def test_runtime_matmul_check(self) -> None:
        """Matmul with incompatible shapes raises at runtime."""
        a = Tensor.zeros((2, 3))
        b = Tensor.zeros((4, 2))
        with pytest.raises(ShapeError):
            a @ b

    def test_runtime_elementwise_check(self) -> None:
        """Element-wise ops with mismatched shapes raise at runtime."""
        a = Tensor.zeros((2, 3))
        b = Tensor.zeros((3, 2))
        with pytest.raises(ShapeError):
            a + b

    def test_runtime_reshape_check(self) -> None:
        """Reshape with wrong total size raises at runtime."""
        t = Tensor.zeros((2, 3))
        with pytest.raises(ShapeError):
            t.reshape((2, 2))

    def test_runtime_construction_check(self) -> None:
        """Constructing tensor with wrong data length raises."""
        with pytest.raises(ShapeError):
            Tensor([1, 2, 3], (2, 2))

    def test_runtime_index_bounds_check(self) -> None:
        """Indexing out of bounds raises at runtime."""
        t = Tensor.zeros((3, 3))
        with pytest.raises(IndexError):
            t.get(3, 0)

    def test_runtime_negative_index_check(self) -> None:
        t = Tensor.zeros((3, 3))
        with pytest.raises(IndexError):
            t.get(-1, 0)

    def test_allclose(self) -> None:
        a = Tensor.from_list([1.0, 2.0, 3.0])
        b = Tensor.from_list([1.0 + 1e-10, 2.0, 3.0 - 1e-10])
        assert a.allclose(b)

    def test_allclose_different_shapes(self) -> None:
        a = Tensor.from_list([1.0, 2.0])
        b = Tensor.from_list([1.0, 2.0, 3.0])
        assert not a.allclose(b)

    def test_equality(self) -> None:
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([1, 2, 3])
        assert a == b

    def test_inequality(self) -> None:
        a = Tensor.from_list([1, 2, 3])
        b = Tensor.from_list([1, 2, 4])
        assert a != b

    def test_repr_1d(self) -> None:
        t = Tensor.from_list([1, 2, 3])
        assert "Tensor" in repr(t)

    def test_repr_2d(self) -> None:
        t = Tensor.from_nested([[1, 2], [3, 4]])
        assert "Tensor" in repr(t)

    def test_len(self) -> None:
        t = Tensor.zeros((2, 3))
        assert len(t) == 6

    def test_iter(self) -> None:
        t = Tensor.from_list([1, 2, 3])
        assert list(t) == [1, 2, 3]
