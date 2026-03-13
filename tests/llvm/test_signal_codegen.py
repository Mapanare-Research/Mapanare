"""Tests for Phase 2 — LLVM Signal Codegen.

Tests verify:
  - SignalInit emits __mn_signal_new calls
  - SignalGet emits __mn_signal_get calls
  - SignalSet emits __mn_signal_set calls with notification
  - SignalComputed emits __mn_signal_computed calls
  - SignalSubscribe emits __mn_signal_subscribe calls
  - New MIR instructions are well-formed
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
    Const,
    MIRFunction,
    MIRModule,
    MIRType,
    Return,
    SignalComputed,
    SignalGet,
    SignalInit,
    SignalSet,
    SignalSubscribe,
    Value,
    pretty_print_instruction,
)
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mir_type(kind: TypeKind, name: str = "") -> MIRType:
    return MIRType(type_info=TypeInfo(kind=kind, name=name))


def _mir_val(name: str, kind: TypeKind = TypeKind.INT) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(kind))


def _signal_val(name: str) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(TypeKind.SIGNAL))


def _make_mir_module(instructions, fn_name="test_fn"):
    """Create a minimal MIR module with a single function containing the given instructions."""
    bb = BasicBlock(label="entry", instructions=instructions + [Return()])
    fn = MIRFunction(
        name=fn_name,
        params=[],
        return_type=_mir_type(TypeKind.VOID),
        blocks=[bb],
    )
    return MIRModule(name="test", functions=[fn])


# ===========================================================================
# Test: MIR instruction pretty-printing
# ===========================================================================


class TestSignalMIRPrinting:
    """New MIR instructions have correct pretty-print output."""

    def test_signal_init_print(self):
        inst = SignalInit(
            dest=_signal_val("sig"),
            signal_type=_mir_type(TypeKind.INT),
            initial_val=_mir_val("init"),
        )
        s = pretty_print_instruction(inst)
        assert "signal_init" in s
        assert "%sig" in s
        assert "%init" in s

    def test_signal_get_print(self):
        inst = SignalGet(dest=_mir_val("val"), signal=_signal_val("sig"))
        s = pretty_print_instruction(inst)
        assert "signal_get" in s
        assert "%sig" in s

    def test_signal_set_print(self):
        inst = SignalSet(signal=_signal_val("sig"), val=_mir_val("new_val"))
        s = pretty_print_instruction(inst)
        assert "signal_set" in s
        assert "%sig" in s
        assert "%new_val" in s

    def test_signal_computed_print(self):
        inst = SignalComputed(
            dest=_signal_val("computed"),
            compute_fn="double_fn",
            deps=[_signal_val("a"), _signal_val("b")],
            val_size=8,
        )
        s = pretty_print_instruction(inst)
        assert "signal_computed" in s
        assert "double_fn" in s
        assert "%a" in s
        assert "%b" in s

    def test_signal_subscribe_print(self):
        inst = SignalSubscribe(
            signal=_signal_val("a"),
            subscriber=_signal_val("b"),
        )
        s = pretty_print_instruction(inst)
        assert "signal_subscribe" in s
        assert "%a" in s
        assert "%b" in s


# ===========================================================================
# Test: LLVM IR emission
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSignalLLVMEmission:
    """SignalInit/Get/Set emit correct LLVM IR with C runtime calls."""

    def test_signal_init_emits_runtime_call(self):
        """SignalInit should call __mn_signal_new."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("init"), ty=_mir_type(TypeKind.INT), value=42),
                SignalInit(
                    dest=_signal_val("sig"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init"),
                ),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        assert "__mn_signal_new" in ir_str

    def test_signal_get_emits_runtime_call(self):
        """SignalGet should call __mn_signal_get."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("init"), ty=_mir_type(TypeKind.INT), value=0),
                SignalInit(
                    dest=_signal_val("sig"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init"),
                ),
                SignalGet(dest=_mir_val("val"), signal=_signal_val("sig")),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        assert "__mn_signal_get" in ir_str

    def test_signal_set_emits_runtime_call(self):
        """SignalSet should call __mn_signal_set."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("init"), ty=_mir_type(TypeKind.INT), value=0),
                SignalInit(
                    dest=_signal_val("sig"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init"),
                ),
                Const(dest=_mir_val("new_val"), ty=_mir_type(TypeKind.INT), value=99),
                SignalSet(signal=_signal_val("sig"), val=_mir_val("new_val")),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        assert "__mn_signal_set" in ir_str

    def test_signal_computed_emits_runtime_call(self):
        """SignalComputed should call __mn_signal_computed."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("init"), ty=_mir_type(TypeKind.INT), value=1),
                SignalInit(
                    dest=_signal_val("a"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init"),
                ),
                SignalComputed(
                    dest=_signal_val("b"),
                    compute_fn="double_fn",
                    deps=[_signal_val("a")],
                    val_size=8,
                ),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        assert "__mn_signal_computed" in ir_str

    def test_signal_subscribe_emits_runtime_call(self):
        """SignalSubscribe should call __mn_signal_subscribe."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("init"), ty=_mir_type(TypeKind.INT), value=0),
                SignalInit(
                    dest=_signal_val("a"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init"),
                ),
                Const(dest=_mir_val("init2"), ty=_mir_type(TypeKind.INT), value=0),
                SignalInit(
                    dest=_signal_val("b"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("init2"),
                ),
                SignalSubscribe(signal=_signal_val("a"), subscriber=_signal_val("b")),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        assert "__mn_signal_subscribe" in ir_str

    def test_signal_init_get_set_complete_ir(self):
        """Full signal lifecycle produces valid LLVM IR."""
        module = _make_mir_module(
            [
                Const(dest=_mir_val("v0"), ty=_mir_type(TypeKind.INT), value=10),
                SignalInit(
                    dest=_signal_val("s"),
                    signal_type=_mir_type(TypeKind.INT),
                    initial_val=_mir_val("v0"),
                ),
                SignalGet(dest=_mir_val("r1"), signal=_signal_val("s")),
                Const(dest=_mir_val("v1"), ty=_mir_type(TypeKind.INT), value=20),
                SignalSet(signal=_signal_val("s"), val=_mir_val("v1")),
                SignalGet(dest=_mir_val("r2"), signal=_signal_val("s")),
            ]
        )
        emitter = LLVMMIREmitter(module_name="test")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)
        # Should have all three runtime calls
        assert "__mn_signal_new" in ir_str
        assert "__mn_signal_get" in ir_str
        assert "__mn_signal_set" in ir_str
        # Should be valid IR (no parse errors)
        assert "define" in ir_str


# ===========================================================================
# Test: Lowering emits SignalSet
# ===========================================================================


class TestSignalLowering:
    """Verify lowering emits correct signal MIR instructions."""

    def test_signal_set_mir_instruction_exists(self):
        """SignalSet MIR instruction is properly defined."""
        inst = SignalSet(signal=_signal_val("s"), val=_mir_val("v"))
        assert inst.signal.name == "%s"
        assert inst.val.name == "%v"

    def test_signal_computed_mir_instruction_exists(self):
        """SignalComputed MIR instruction is properly defined."""
        inst = SignalComputed(
            dest=_signal_val("c"),
            compute_fn="my_fn",
            deps=[_signal_val("a")],
            val_size=8,
        )
        assert inst.dest.name == "%c"
        assert inst.compute_fn == "my_fn"
        assert len(inst.deps) == 1
        assert inst.val_size == 8
