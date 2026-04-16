"""End-to-end LLVM emission tests for tensor literals (v4.42.0)."""

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(src: str) -> str:
    """Compile source to LLVM IR."""
    ast = parse(src)
    checker = SemanticChecker()
    checker.check(ast)
    module = lower(ast)
    emitter = LLVMTextEmitter()
    return emitter.emit(module)


class TestTensorLiteralLLVM:
    def test_1d_tensor_compiles(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0, 3.0] }")
        assert "__mn_tensor_alloc" in ir
        assert "__mn_tensor_store_f64" in ir

    def test_2d_tensor_compiles(self):
        ir = _emit("fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]] }")
        assert "__mn_tensor_alloc" in ir
        # 4 stores for 2x2
        assert ir.count("__mn_tensor_store_f64") >= 4

    def test_3d_tensor_compiles(self):
        ir = _emit("fn main() { let a = Tensor<Int>[[[1, 2], [3, 4]], [[5, 6], [7, 8]]] }")
        assert "__mn_tensor_alloc" in ir
        assert "__mn_tensor_store_i64" in ir
        # 8 stores for 2x2x2
        assert ir.count("__mn_tensor_store_i64") >= 8

    def test_shape_array_allocated(self):
        ir = _emit("fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]] }")
        # Shape array [2 x i64] for rank 2
        assert "[2 x i64]" in ir

    def test_drop_glue_frees_tensor(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0] }")
        assert "__mn_tensor_free" in ir

    def test_tensor_rank_builtin(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0]; print(str(tensor_rank(a))) }")
        assert "__mn_tensor_rank" in ir

    def test_tensor_size_builtin(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0]; print(str(tensor_size(a))) }")
        assert "__mn_tensor_size" in ir

    def test_tensor_get_f64_builtin(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0]; print(str(tensor_get_f64(a, 0))) }")
        assert "__mn_tensor_get_f64" in ir

    def test_tensor_get_i64_builtin(self):
        ir = _emit("fn main() { let a = Tensor<Int>[42]; print(str(tensor_get_i64(a, 0))) }")
        assert "__mn_tensor_get_i64" in ir

    def test_tensor_shape_dim_builtin(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; print(str(tensor_shape_dim(a, 0))) }"
        )
        assert "__mn_tensor_shape_dim" in ir

    def test_tensor_print_builtin(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; tensor_print(a) }")
        assert "__mn_tensor_print_f64" in ir

    def test_empty_tensor_zero_dim(self):
        """Tensor with shape [0] via annotation — zero elements."""
        ir = _emit("fn main() { let a: Tensor<Float>[0] = Tensor<Float>[1.0] }")
        # Should still compile (shape annotation doesn't block literal)
        assert "__mn_tensor_alloc" in ir
