"""LLVM emission tests for tensor indexing (v4.43.0)."""

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(src: str) -> str:
    ast = parse(src)
    checker = SemanticChecker()
    checker.check(ast)
    module = lower(ast)
    return LLVMTextEmitter().emit(module)


class TestTensorIndexingLLVM:
    def test_2d_get_emits_variadic_call(self):
        ir = _emit("fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let x = a[0, 1] }")
        assert "__mn_tensor_get_f64_nd" in ir

    def test_1d_get_emits_call(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a[0] }")
        assert "__mn_tensor_get_f64_nd" in ir

    def test_3d_get_emits_call(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]; let x = a[0, 1, 0] }"
        )
        assert "__mn_tensor_get_f64_nd" in ir

    def test_int_tensor_uses_i64_variant(self):
        ir = _emit("fn main() { let a = Tensor<Int>[10, 20, 30]; let x = a[1] }")
        assert "__mn_tensor_get_i64_nd" in ir

    def test_2d_set_emits_variadic_call(self):
        ir = _emit(
            "fn main() { let mut a = Tensor<Float>[[0.0, 0.0], [0.0, 0.0]]; a[0, 1] = 42.0 }"
        )
        assert "__mn_tensor_set_f64_nd" in ir

    def test_list_single_index_no_regression(self):
        ir = _emit("fn main() { let a = [1, 2, 3]; let x = a[0] }")
        assert "__mn_list_get" in ir
        assert "__mn_tensor_get" not in ir

    def test_variadic_declaration_present(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a[0] }")
        assert "declare" in ir
        assert "__mn_tensor_get_f64_nd" in ir
