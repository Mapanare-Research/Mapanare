"""LLVM emission tests for tensor reductions and slicing (v4.45.0)."""

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(src: str) -> str:
    ast = parse(src)
    checker = SemanticChecker()
    checker.check(ast)
    return LLVMTextEmitter().emit(lower(ast))


class TestTensorReductionsLLVM:
    def test_sum_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.sum() }")
        assert "__mn_tensor_sum_f64" in ir

    def test_mean_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.mean() }")
        assert "__mn_tensor_mean_f64" in ir

    def test_max_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.max() }")
        assert "__mn_tensor_max_f64" in ir

    def test_min_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.min() }")
        assert "__mn_tensor_min_f64" in ir

    def test_argmax_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.argmax() }")
        assert "__mn_tensor_argmax_f64" in ir

    def test_argmin_f64(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0]; let x = a.argmin() }")
        assert "__mn_tensor_argmin_f64" in ir

    def test_sum_i64(self):
        ir = _emit("fn main() { let a = Tensor<Int>[1, 2, 3]; let x = a.sum() }")
        assert "__mn_tensor_sum_i64" in ir

    def test_max_i64(self):
        ir = _emit("fn main() { let a = Tensor<Int>[1, 2, 3]; let x = a.max() }")
        assert "__mn_tensor_max_i64" in ir


class TestTensorSlicingLLVM:
    def test_range_slice_emits_call(self):
        ir = _emit("fn main() { let a = Tensor<Float>[1.0, 2.0, 3.0]; let s = a[0..2] }")
        assert "__mn_tensor_slice" in ir

    def test_wildcard_slice_emits_call(self):
        ir = _emit("fn main() { let a = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]; let s = a[0, _] }")
        # Mixed scalar+wildcard triggers slice path
        assert "__mn_tensor_slice" in ir or "__mn_tensor_get" in ir
