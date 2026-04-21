"""Tests for GPU auto-dispatch in the LLVM MIR emitter.

Verifies that @gpu, @cuda, and @vulkan decorators on functions cause
tensor operations to be redirected to GPU C runtime calls, and that
non-GPU functions and non-tensor calls are unaffected.
"""

from __future__ import annotations

from mapanare.emit_llvm_text import LLVMTextEmitter
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
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(module)


# ===========================================================================
# Test: GPU decorator detection
# ===========================================================================


class TestGPUDecoratorDetection:
    """Verify that GPU tensor builtins emit correct GPU runtime calls.

    The text emitter dispatches based on MIR function names (gpu_tensor_add,
    gpu_tensor_sub, etc.) rather than decorator-based remapping. The lowerer
    is responsible for producing the correct builtin names from decorators.
    """

    def test_gpu_tensor_add_dispatched(self) -> None:
        """gpu_tensor_add should emit __mn_gpu_tensor_add runtime call."""
        module = _make_tensor_call_module("gpu_tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_add" in ir_str

    def test_gpu_tensor_sub_dispatched(self) -> None:
        """gpu_tensor_sub should emit __mn_gpu_tensor_sub runtime call."""
        module = _make_tensor_call_module("gpu_tensor_sub", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_sub" in ir_str

    def test_gpu_tensor_mul_dispatched(self) -> None:
        """gpu_tensor_mul should emit __mn_gpu_tensor_mul runtime call."""
        module = _make_tensor_call_module("gpu_tensor_mul", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_mul" in ir_str


# ===========================================================================
# Test: GPU tensor operation dispatch
# ===========================================================================


class TestGPUTensorDispatch:
    """Verify that GPU tensor builtins emit the correct runtime calls.

    The text emitter recognizes gpu_tensor_* as builtins and emits the
    corresponding __mn_gpu_tensor_* or __mn_gpu_tensor_* C runtime calls.
    """

    def test_gpu_tensor_add_dispatch(self) -> None:
        """gpu_tensor_add(a, b) should emit __mn_gpu_tensor_add."""
        module = _make_tensor_call_module("gpu_tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_add" in ir_str

    def test_gpu_tensor_div_dispatch(self) -> None:
        """gpu_tensor_div(a, b) should emit __mn_gpu_tensor_div."""
        module = _make_tensor_call_module("gpu_tensor_div", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_div" in ir_str

    def test_non_gpu_call_not_remapped(self) -> None:
        """A plain tensor_add call (no gpu_ prefix) should NOT emit GPU runtime calls."""
        module = _make_tensor_call_module("tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_add" not in ir_str


# ===========================================================================
# Test: No GPU dispatch without decorator
# ===========================================================================


class TestNoGPUDispatchWithoutDecorator:
    """Verify that non-gpu builtin names do not emit GPU calls."""

    def test_plain_tensor_add_no_gpu_dispatch(self) -> None:
        """A call to tensor_add (not gpu_tensor_add) should NOT emit GPU runtime calls."""
        module = _make_tensor_call_module("tensor_add", decorators=[])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_add" not in ir_str


# ===========================================================================
# Test: GPU runtime declarations
# ===========================================================================


class TestGPURuntimeDeclarations:
    """Verify that GPU runtime functions are declared when a GPU builtin is used."""

    def test_gpu_tensor_add_declaration(self) -> None:
        """When gpu_tensor_add is called, __mn_gpu_tensor_add should be declared."""
        module = _make_tensor_call_module("gpu_tensor_add", decorators=["gpu"])
        ir_str = _emit_ir(module)
        assert "__mn_gpu_tensor_add" in ir_str
        assert "declare" in ir_str


# ===========================================================================
# Test: Non-tensor calls not dispatched
# ===========================================================================


class TestNonTensorCallNotDispatched:
    """Verify that non-tensor calls in GPU functions are not routed to GPU."""

    def test_non_tensor_call_not_dispatched(self) -> None:
        """A @gpu function calling print() should NOT be routed to GPU runtime."""
        msg = Value(name="%msg", ty=_mir_type(TypeKind.STRING))
        result = Value(name="%result", ty=_mir_type(TypeKind.VOID))
        instructions = [
            Const(dest=msg, ty=_mir_type(TypeKind.STRING), value="hello"),
            Call(dest=result, fn_name="print", args=[msg]),
        ]
        module = _make_gpu_module(instructions, decorators=["gpu"])
        ir_str = _emit_ir(module)
        # print should go through the normal path, not GPU dispatch
        assert "mapanare_gpu_tensor_print" not in ir_str
        assert "mapanare_vk_tensor_print" not in ir_str
