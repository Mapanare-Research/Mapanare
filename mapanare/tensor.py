"""Tensor runtime for Mapanare — CPU tensor operations (Phase 5.1).

Provides:
  - Tensor class with contiguous row-major memory layout
  - Tensor creation (zeros, ones, full, from_list)
  - Element-wise operations (+, -, *, /)
  - Matrix multiply (@)
  - Compile-time and runtime shape validation
"""

from __future__ import annotations

from typing import Iterator, Sequence, Union

# Type alias for shape tuples
Shape = tuple[int, ...]
Numeric = Union[int, float]


class ShapeError(Exception):
    """Raised when tensor shapes are incompatible for an operation."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class Tensor:
    """A multi-dimensional array with contiguous row-major storage.

    Memory layout:
      - data:  flat list of elements (row-major / C order)
      - shape: tuple of dimension sizes
      - ndim:  number of dimensions
      - size:  total number of elements (product of shape)
    """

    __slots__ = ("_data", "_shape", "_ndim", "_size")

    def __init__(self, data: list[Numeric], shape: Shape) -> None:
        expected_size = _shape_size(shape)
        if len(data) != expected_size:
            raise ShapeError(
                f"Data length {len(data)} does not match shape {shape} "
                f"(expected {expected_size} elements)"
            )
        self._data: list[Numeric] = data
        self._shape: Shape = shape
        self._ndim: int = len(shape)
        self._size: int = expected_size

    @property
    def data(self) -> list[Numeric]:
        return self._data

    @property
    def shape(self) -> Shape:
        return self._shape

    @property
    def ndim(self) -> int:
        return self._ndim

    @property
    def size(self) -> int:
        return self._size

    # -- Indexing -----------------------------------------------------------

    def _flat_index(self, indices: tuple[int, ...]) -> int:
        """Convert multi-dimensional indices to a flat index (row-major)."""
        if len(indices) != self._ndim:
            raise ShapeError(f"Expected {self._ndim} indices, got {len(indices)}")
        flat = 0
        stride = 1
        for i in range(self._ndim - 1, -1, -1):
            idx = indices[i]
            dim = self._shape[i]
            if idx < 0 or idx >= dim:
                raise IndexError(f"Index {idx} out of bounds for dimension {i} with size {dim}")
            flat += idx * stride
            stride *= dim
        return flat

    def get(self, *indices: int) -> Numeric:
        """Get element at the given indices."""
        return self._data[self._flat_index(indices)]

    def set(self, *args: int | Numeric) -> None:
        """Set element: tensor.set(i, j, ..., value)."""
        indices = tuple(int(x) for x in args[:-1])
        value = args[-1]
        if not isinstance(value, (int, float)):
            raise TypeError(f"Expected numeric value, got {type(value)}")
        self._data[self._flat_index(indices)] = value

    # -- Creation -----------------------------------------------------------

    @staticmethod
    def zeros(shape: Shape) -> Tensor:
        """Create a tensor filled with zeros."""
        size = _shape_size(shape)
        return Tensor([0.0] * size, shape)

    @staticmethod
    def ones(shape: Shape) -> Tensor:
        """Create a tensor filled with ones."""
        size = _shape_size(shape)
        return Tensor([1.0] * size, shape)

    @staticmethod
    def full(shape: Shape, value: Numeric) -> Tensor:
        """Create a tensor filled with a constant value."""
        size = _shape_size(shape)
        return Tensor([value] * size, shape)

    @staticmethod
    def from_list(data: list[Numeric], shape: Shape | None = None) -> Tensor:
        """Create a tensor from a flat list.

        If shape is None, creates a 1D tensor.
        """
        if shape is None:
            shape = (len(data),)
        return Tensor(list(data), shape)

    @staticmethod
    def from_nested(nested: Sequence[object]) -> Tensor:
        """Create a tensor from nested lists, inferring shape."""
        shape = _infer_shape(nested)
        flat = _flatten(nested)
        return Tensor(flat, shape)

    @staticmethod
    def identity(n: int) -> Tensor:
        """Create an n×n identity matrix."""
        data: list[Numeric] = [0.0] * (n * n)
        for i in range(n):
            data[i * n + i] = 1.0
        return Tensor(data, (n, n))

    # -- Element-wise operations -------------------------------------------

    def _elementwise(self, other: Tensor | Numeric, op: str) -> Tensor:
        """Apply an element-wise binary operation."""
        if isinstance(other, (int, float)):
            # Scalar broadcast
            if op == "+":
                result = [x + other for x in self._data]
            elif op == "-":
                result = [x - other for x in self._data]
            elif op == "*":
                result = [x * other for x in self._data]
            elif op == "/":
                result = [x / other for x in self._data]
            else:
                raise ValueError(f"Unknown op: {op}")
            return Tensor(result, self._shape)

        if not isinstance(other, Tensor):
            raise TypeError(f"Unsupported operand type: {type(other)}")

        if self._shape != other._shape:
            raise ShapeError(
                f"Shape mismatch for element-wise '{op}': " f"{self._shape} vs {other._shape}"
            )

        if op == "+":
            result = [a + b for a, b in zip(self._data, other._data)]
        elif op == "-":
            result = [a - b for a, b in zip(self._data, other._data)]
        elif op == "*":
            result = [a * b for a, b in zip(self._data, other._data)]
        elif op == "/":
            result = [a / b for a, b in zip(self._data, other._data)]
        else:
            raise ValueError(f"Unknown op: {op}")

        return Tensor(result, self._shape)

    def __add__(self, other: Tensor | Numeric) -> Tensor:
        return self._elementwise(other, "+")

    def __sub__(self, other: Tensor | Numeric) -> Tensor:
        return self._elementwise(other, "-")

    def __mul__(self, other: Tensor | Numeric) -> Tensor:
        return self._elementwise(other, "*")

    def __truediv__(self, other: Tensor | Numeric) -> Tensor:
        return self._elementwise(other, "/")

    def __neg__(self) -> Tensor:
        return Tensor([-x for x in self._data], self._shape)

    # -- Matrix multiply ---------------------------------------------------

    def __matmul__(self, other: Tensor) -> Tensor:
        """Matrix multiply: self @ other.

        Supports:
          - 2D @ 2D: standard matrix multiply (M,K) @ (K,N) → (M,N)
          - 1D @ 1D: dot product → scalar in (1,) tensor
          - 2D @ 1D: matrix-vector multiply (M,K) @ (K,) → (M,)
          - 1D @ 2D: vector-matrix multiply (K,) @ (K,N) → (N,)
        """
        return matmul(self, other)

    # -- Reshape -----------------------------------------------------------

    def reshape(self, new_shape: Shape) -> Tensor:
        """Reshape the tensor to a new shape (must have same total size)."""
        new_size = _shape_size(new_shape)
        if new_size != self._size:
            raise ShapeError(
                f"Cannot reshape {self._shape} ({self._size} elements) "
                f"to {new_shape} ({new_size} elements)"
            )
        return Tensor(list(self._data), new_shape)

    def transpose(self) -> Tensor:
        """Transpose a 2D tensor."""
        if self._ndim != 2:
            raise ShapeError(f"transpose requires 2D tensor, got {self._ndim}D")
        rows, cols = self._shape
        result: list[Numeric] = [0.0] * self._size
        for i in range(rows):
            for j in range(cols):
                result[j * rows + i] = self._data[i * cols + j]
        return Tensor(result, (cols, rows))

    # -- Reductions --------------------------------------------------------

    def sum(self) -> Numeric:
        """Sum of all elements."""
        return sum(self._data)

    def mean(self) -> float:
        """Mean of all elements."""
        return sum(self._data) / self._size

    def max(self) -> Numeric:
        """Maximum element."""
        return max(self._data)

    def min(self) -> Numeric:
        """Minimum element."""
        return min(self._data)

    # -- Comparison --------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tensor):
            return NotImplemented
        return self._shape == other._shape and self._data == other._data

    def allclose(self, other: Tensor, atol: float = 1e-8) -> bool:
        """Check if all elements are close within absolute tolerance."""
        if self._shape != other._shape:
            return False
        return all(abs(a - b) <= atol for a, b in zip(self._data, other._data))

    # -- String representation ---------------------------------------------

    def __repr__(self) -> str:
        if self._ndim == 1:
            return f"Tensor({self._data}, shape={self._shape})"
        if self._ndim == 2:
            rows, cols = self._shape
            row_strs = []
            for i in range(rows):
                row = self._data[i * cols : (i + 1) * cols]
                row_strs.append(f"  {row}")
            inner = ",\n".join(row_strs)
            return f"Tensor([\n{inner}\n], shape={self._shape})"
        return f"Tensor(data=[...{self._size} elements], shape={self._shape})"

    def __iter__(self) -> Iterator[Numeric]:
        return iter(self._data)

    def __len__(self) -> int:
        return self._size


# ---------------------------------------------------------------------------
# Matrix multiply implementation
# ---------------------------------------------------------------------------


def matmul(a: Tensor, b: Tensor) -> Tensor:
    """Matrix multiply two tensors.

    Shape rules:
      (M, K) @ (K, N) → (M, N)
      (K,)   @ (K,)   → (1,)      (dot product)
      (M, K) @ (K,)   → (M,)      (matrix-vector)
      (K,)   @ (K, N) → (N,)      (vector-matrix)
    """
    if a.ndim == 1 and b.ndim == 1:
        # Dot product
        if a.shape[0] != b.shape[0]:
            raise ShapeError(f"Dot product shape mismatch: ({a.shape[0]},) and ({b.shape[0]},)")
        result = sum(x * y for x, y in zip(a.data, b.data))
        return Tensor([result], (1,))

    if a.ndim == 2 and b.ndim == 2:
        # Standard matrix multiply
        m, k1 = a.shape
        k2, n = b.shape
        if k1 != k2:
            raise ShapeError(
                f"Matmul shape mismatch: ({m}, {k1}) @ ({k2}, {n}) — "
                f"inner dimensions {k1} and {k2} must match"
            )
        return _matmul_2d(a, b, m, k1, n)

    if a.ndim == 2 and b.ndim == 1:
        # Matrix-vector: (M, K) @ (K,) → (M,)
        m, k1 = a.shape
        (k2,) = b.shape
        if k1 != k2:
            raise ShapeError(
                f"Matmul shape mismatch: ({m}, {k1}) @ ({k2},) — "
                f"inner dimensions {k1} and {k2} must match"
            )
        result_data: list[Numeric] = [0.0] * m
        for i in range(m):
            s: Numeric = 0.0
            for j in range(k1):
                s += a.data[i * k1 + j] * b.data[j]
            result_data[i] = s
        return Tensor(result_data, (m,))

    if a.ndim == 1 and b.ndim == 2:
        # Vector-matrix: (K,) @ (K, N) → (N,)
        (k1,) = a.shape
        k2, n = b.shape
        if k1 != k2:
            raise ShapeError(
                f"Matmul shape mismatch: ({k1},) @ ({k2}, {n}) — "
                f"inner dimensions {k1} and {k2} must match"
            )
        result_data = [0.0] * n
        for j in range(n):
            s = 0.0
            for i in range(k1):
                s += a.data[i] * b.data[i * n + j]
            result_data[j] = s
        return Tensor(result_data, (n,))

    raise ShapeError(f"Matmul not supported for {a.ndim}D @ {b.ndim}D tensors")


def _matmul_2d(a: Tensor, b: Tensor, m: int, k: int, n: int) -> Tensor:
    """Optimized 2D matrix multiply using row-major layout.

    Uses a simple triple-loop with j-k reordering for better cache locality.
    For production, this would call BLAS (dgemm) or use SIMD intrinsics.
    """
    result: list[Numeric] = [0.0] * (m * n)
    a_data = a.data
    b_data = b.data

    for i in range(m):
        for p in range(k):
            a_ip = a_data[i * k + p]
            for j in range(n):
                result[i * n + j] += a_ip * b_data[p * n + j]

    return Tensor(result, (m, n))


# ---------------------------------------------------------------------------
# Shape utilities
# ---------------------------------------------------------------------------


def _shape_size(shape: Shape) -> int:
    """Compute total number of elements from shape tuple."""
    if not shape:
        return 1
    result = 1
    for dim in shape:
        if dim < 0:
            raise ShapeError(f"Negative dimension in shape: {shape}")
        result *= dim
    return result


def _infer_shape(nested: Sequence[object]) -> Shape:
    """Infer shape from nested sequences."""
    shape: list[int] = []
    current: object = nested
    while isinstance(current, (list, tuple)):
        shape.append(len(current))
        if len(current) == 0:
            break
        current = current[0]
    return tuple(shape)


def _flatten(nested: object) -> list[Numeric]:
    """Flatten nested sequences into a flat list of numbers."""
    result: list[Numeric] = []
    if isinstance(nested, (list, tuple)):
        for item in nested:
            result.extend(_flatten(item))
    elif isinstance(nested, (int, float)):
        result.append(nested)
    else:
        raise TypeError(f"Cannot flatten {type(nested)}")
    return result


# ---------------------------------------------------------------------------
# Shape validation utilities (used by semantic checker)
# ---------------------------------------------------------------------------


def validate_matmul_shapes(
    a_shape: tuple[int, ...], b_shape: tuple[int, ...]
) -> tuple[int, ...] | None:
    """Validate shapes for matmul and return result shape, or None if invalid.

    Returns the output shape if the matmul is valid, None otherwise.
    """
    a_ndim = len(a_shape)
    b_ndim = len(b_shape)

    if a_ndim == 1 and b_ndim == 1:
        if a_shape[0] == b_shape[0]:
            return (1,)
        return None

    if a_ndim == 2 and b_ndim == 2:
        if a_shape[1] == b_shape[0]:
            return (a_shape[0], b_shape[1])
        return None

    if a_ndim == 2 and b_ndim == 1:
        if a_shape[1] == b_shape[0]:
            return (a_shape[0],)
        return None

    if a_ndim == 1 and b_ndim == 2:
        if a_shape[0] == b_shape[0]:
            return (b_shape[1],)
        return None

    return None


def validate_elementwise_shapes(a_shape: tuple[int, ...], b_shape: tuple[int, ...]) -> bool:
    """Check if two shapes are compatible for element-wise operations."""
    return a_shape == b_shape


def resolve_shape_from_type(
    shape_exprs: list[object],
) -> tuple[int, ...] | None:
    """Try to resolve a shape tuple from AST shape expressions.

    Returns the shape if all dimensions are integer literals, None if
    any dimension is dynamic (non-literal).
    """
    from mapanare.ast_nodes import IntLiteral

    dims: list[int] = []
    for expr in shape_exprs:
        if isinstance(expr, IntLiteral):
            dims.append(expr.value)
        else:
            return None  # Dynamic dimension
    return tuple(dims)
