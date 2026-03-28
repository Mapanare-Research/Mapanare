"""Tests for GPU auto-dispatch in the LLVM MIR emitter.

Verifies that @gpu, @cuda, and @vulkan decorators on functions cause
tensor operations to be redirected to GPU C runtime calls, and that
non-GPU functions and non-tensor calls are unaffected.
"""

from __future__ import annotations

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.emit_llvm_mir import LLVMMIREmitter
from mapanare.mir import (
    BasicBlock,
    Call,
    Const,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRType,
    Return,
    Value,
)
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mir_type(kind: TypeKind, name: str = "") -> MIRType:
    return MIRType(type_info=TypeInfo(kind=kind, name=name))


def _mir_val(name: str, kind: TypeKind = TypeKind.INT) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(kind))


def _tensor_val(name: str) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(TypeKind.TENSOR))


def _tensor_param(name: str) -> MIRParam:
    return MIRParam(name=name, ty=_mir_type(TypeKind.TENSOR))


def _make_tensor_call_module(fn_name_to_call: str, decorators: list[str]) -> MIRModule:
    """Create a MIR module with a function that takes two tensor params and calls
    fn_name_to_call(a, b). The function has the given decorators."""
    a = _tensor_val("a")
    b = _tensor_val("b")
    result = _tensor_val("result")
    instructions = [
        Call(dest=result, fn_name=fn_name_to_call, args=[a, b]),
    ]
    bb = BasicBlock(label="entry", instructions=instructions + [Return()])
    fn = MIRFunction(
        name="test_fn",
        params=[_tensor_param("a"), _tensor_param("b")],
        return_type=_mir_type(TypeKind.VOID),
        blocks=[bb],
        decorators=decorators,
    )
    return MIRModule(name="test", functions=[fn])


def _make_gpu_module(
    instructions,
    fn_name="test_fn",
    params=None,
    decorators=None,
):
    """Create a minimal MIR module with a single function and optional decorators."""
    bb = BasicBlock(label="entry", instructions=instructions + [Return()])
    fn = MIRFunction(
        name=fn_name,
        params=params or [],
        return_type=_mir_type(TypeKind.VOID),
        blocks=[bb],
        decorators=decorators or [],
    )
    return MIRModule(name="test", functions=[fn])


def _emit_ir(module: MIRModule) -> str:
    """Emit a MIR module to LLVM IR and return the IR string."""
    emitter = LLVMMIREmitter(module_name="test")
    emitter.emit(module)
    return str(emitter.module)


# ===========================================================================
# Test: GPU decorator detection
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestGPUDecoratorDetection:
    """Verify that @gpu, @cuda, and @vulkan decorators set _gpu_device."""

    def test_gpu_decorator_detected(self) -> None:
        """A function with @gpu should dispatch tensor ops to GPU runtime."""
        module = _make_tensor_call_module("tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "mapanare_gpu_tensor_add" in ir_str

    def test_cuda_decorator_detected(self) -> None:
        """A function with @cuda should dispatch tensor ops to GPU runtime."""
        module = _make_tensor_call_module("tensor_add", decorators=["cuda"])
        ir_str = _emit_ir(module)
        # cuda uses the same mapanare_gpu_tensor_* functions
        assert "mapanare_gpu_tensor_add" in ir_str

    def test_vulkan_decorator_detected(self) -> None:
        """A function with @vulkan should dispatch tensor ops to Vulkan runtime."""
        module = _make_tensor_call_module("tensor_add", decorators=["vulkan"])
        ir_str = _emit_ir(module)
        # vulkan uses mapanare_vk_tensor_* functions
        assert "mapanare_vk_tensor_add" in ir_str


# ===========================================================================
# Test: GPU tensor operation dispatch
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestGPUTensorDispatch:
    """Verify that tensor operations in GPU functions emit GPU runtime calls."""

    def test_gpu_tensor_add_dispatch(self) -> None:
        """@gpu function calling tensor_add(a, b) should emit mapanare_gpu_tensor_add."""
        module = _make_tensor_call_module("tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "mapanare_gpu_tensor_add" in ir_str

    def test_gpu_tensor_matmul_dispatch(self) -> None:
        """@gpu function calling matmul(a, b) should emit mapanare_gpu_tensor_matmul."""
        module = _make_tensor_call_module("matmul", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "mapanare_gpu_tensor_matmul" in ir_str

    def test_vulkan_tensor_add_dispatch(self) -> None:
        """@vulkan function calling tensor_add(a, b) should emit mapanare_vk_tensor_add."""
        module = _make_tensor_call_module("tensor_add", decorators=["vulkan"])
        ir_str = _emit_ir(module)
        assert "mapanare_vk_tensor_add" in ir_str
        # Should NOT contain the generic GPU variant for the call
        # (though declarations for both sets are emitted by _declare_gpu_runtime)


# ===========================================================================
# Test: No GPU dispatch without decorator
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestNoGPUDispatchWithoutDecorator:
    """Verify that functions without GPU decorators do not emit GPU calls."""

    def test_no_decorator_no_gpu_dispatch(self) -> None:
        """A function WITHOUT any GPU decorator should NOT emit GPU runtime calls."""
        module = _make_tensor_call_module("tensor_add", decorators=[])
        ir_str = _emit_ir(module)
        assert "mapanare_gpu_tensor_add" not in ir_str
        assert "mapanare_vk_tensor_add" not in ir_str


# ===========================================================================
# Test: GPU runtime declarations
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestGPURuntimeDeclarations:
    """Verify that GPU runtime functions are declared in the LLVM module."""

    def test_gpu_runtime_declarations(self) -> None:
        """When a GPU function is compiled, the IR should contain declare statements
        for the GPU runtime functions."""
        module = _make_tensor_call_module("tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)

        # Should contain declarations for GPU init/detection
        assert "mapanare_gpu_init" in ir_str
        assert "mapanare_gpu_has_cuda" in ir_str
        assert "mapanare_gpu_has_vulkan" in ir_str

        # Should contain declarations for buffer management
        assert "mapanare_gpu_buffer_alloc" in ir_str
        assert "mapanare_gpu_buffer_free" in ir_str

        # Should contain tensor op declarations
        for op in ("add", "sub", "mul", "div", "matmul"):
            assert f"mapanare_gpu_tensor_{op}" in ir_str
            assert f"mapanare_vk_tensor_{op}" in ir_str


# ===========================================================================
# Test: Non-tensor calls not dispatched
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestNonTensorCallNotDispatched:
    """Verify that non-tensor calls in GPU functions are not routed to GPU."""

    def test_non_tensor_call_not_dispatched(self) -> None:
        """A @gpu function calling println() should NOT be routed to GPU runtime."""
        msg = Value(name="%msg", ty=_mir_type(TypeKind.STRING))
        result = Value(name="%result", ty=_mir_type(TypeKind.VOID))
        instructions = [
            Const(dest=msg, ty=_mir_type(TypeKind.STRING), value="hello"),
            Call(dest=result, fn_name="println", args=[msg]),
        ]
        module = _make_gpu_module(instructions, decorators=["gpu"])
        ir_str = _emit_ir(module)
        # println should go through the normal path, not GPU dispatch
        assert "mapanare_gpu_tensor_println" not in ir_str
        assert "mapanare_vk_tensor_println" not in ir_str
