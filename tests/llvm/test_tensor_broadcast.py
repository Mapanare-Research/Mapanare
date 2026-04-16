"""LLVM emission tests for tensor broadcasting (v4.44.0)."""

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(src: str) -> str:
    ast = parse(src)
    checker = SemanticChecker()
    checker.check(ast)
    return LLVMTextEmitter().emit(lower(ast))


class TestTensorBroadcastLLVM:
    def test_add_broadcast(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[1.0]; let b = Tensor<Float>[2.0]; let c = a + b }"
        )
        assert "__mn_tensor_add_broadcast_f64" in ir

    def test_sub_broadcast(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[1.0]; let b = Tensor<Float>[2.0]; let c = a - b }"
        )
        assert "__mn_tensor_sub_broadcast_f64" in ir

    def test_mul_broadcast(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[1.0]; let b = Tensor<Float>[2.0]; let c = a * b }"
        )
        assert "__mn_tensor_mul_broadcast_f64" in ir

    def test_div_broadcast(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[1.0]; let b = Tensor<Float>[2.0]; let c = a / b }"
        )
        assert "__mn_tensor_div_broadcast_f64" in ir

    def test_int_tensor_broadcast(self):
        ir = _emit(
            "fn main() { let a = Tensor<Int>[1, 2]; let b = Tensor<Int>[3, 4]; let c = a + b }"
        )
        assert "__mn_tensor_add_broadcast_i64" in ir

    def test_scalar_add(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0]; let c = a + 5.0 }")
        assert "__mn_tensor_add_scalar_f64" in ir

    def test_scalar_mul(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0]; let c = a * 2.0 }")
        assert "__mn_tensor_mul_scalar_f64" in ir

    def test_drop_glue_for_result(self):
        ir = _emit(
            "fn main() { let a = Tensor<Float>[1.0]; let b = Tensor<Float>[2.0]; let c = a + b }"
        )
        assert "__mn_tensor_free" in ir

    def test_list_add_no_regression(self):
        ir = _emit("fn main() { let a = [1, 2]; let b = [3, 4]; let c = a + b }")
        assert "__mn_tensor" not in ir
