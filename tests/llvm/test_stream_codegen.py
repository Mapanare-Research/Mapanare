"""Tests for Phase 3 — LLVM Stream Codegen.

Tests verify:
  - StreamInit emits __mn_stream_from_list calls
  - StreamOp MAP emits __mn_stream_map calls
  - StreamOp FILTER emits __mn_stream_filter calls
  - StreamOp TAKE/SKIP emit __mn_stream_take/__mn_stream_skip calls
  - StreamOp COLLECT emits __mn_stream_collect calls
  - StreamOp FOLD emits __mn_stream_fold calls
  - Stream iteration emits __mn_stream_next loop
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
    Call,
    Const,
    ListInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Return,
    StreamInit,
    StreamOp,
    StreamOpKind,
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


def _stream_val(name: str) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(TypeKind.STREAM))


def _list_val(name: str) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(TypeKind.LIST))


def _make_mir_module(instructions, fn_name="test_fn", params=None):
    """Create a minimal MIR module with a single function containing the given instructions."""
    bb = BasicBlock(label="entry", instructions=instructions + [Return()])
    fn = MIRFunction(
        name=fn_name,
        params=params or [],
        return_type=_mir_type(TypeKind.VOID),
        blocks=[bb],
    )
    return MIRModule(name="test", functions=[fn])


# ===========================================================================
# Test: MIR instruction pretty-printing
# ===========================================================================


class TestStreamMIRPrinting:
    """New MIR stream instructions have correct pretty-print output."""

    def test_stream_init_print(self):
        inst = StreamInit(
            dest=_stream_val("s"),
            source=_list_val("lst"),
            elem_type=_mir_type(TypeKind.INT),
        )
        s = pretty_print_instruction(inst)
        assert "stream_init" in s
        assert "%s" in s
        assert "%lst" in s

    def test_stream_op_map_print(self):
        inst = StreamOp(
            dest=_stream_val("mapped"),
            op_kind=StreamOpKind.MAP,
            source=_stream_val("s"),
            args=[_mir_val("fn")],
            fn_name="double_fn",
        )
        s = pretty_print_instruction(inst)
        assert "stream_op" in s
        assert "map" in s
        assert "%s" in s
        assert "fn=double_fn" in s

    def test_stream_op_filter_print(self):
        inst = StreamOp(
            dest=_stream_val("filtered"),
            op_kind=StreamOpKind.FILTER,
            source=_stream_val("s"),
            args=[_mir_val("pred")],
        )
        s = pretty_print_instruction(inst)
        assert "stream_op" in s
        assert "filter" in s

    def test_stream_op_take_print(self):
        inst = StreamOp(
            dest=_stream_val("taken"),
            op_kind=StreamOpKind.TAKE,
            source=_stream_val("s"),
            args=[_mir_val("n")],
        )
        s = pretty_print_instruction(inst)
        assert "stream_op" in s
        assert "take" in s

    def test_stream_op_collect_print(self):
        inst = StreamOp(
            dest=_list_val("result"),
            op_kind=StreamOpKind.COLLECT,
            source=_stream_val("s"),
        )
        s = pretty_print_instruction(inst)
        assert "stream_op" in s
        assert "collect" in s

    def test_stream_op_fold_print(self):
        inst = StreamOp(
            dest=_mir_val("sum"),
            op_kind=StreamOpKind.FOLD,
            source=_stream_val("s"),
            args=[_mir_val("init"), _mir_val("fn")],
        )
        s = pretty_print_instruction(inst)
        assert "stream_op" in s
        assert "fold" in s


# ===========================================================================
# Test: LLVM IR emission for StreamInit
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStreamInitEmission:
    """StreamInit emits __mn_stream_from_list call."""

    def test_stream_init_emits_from_list(self):
        # Create a list literal, then StreamInit
        list_dest = _list_val("lst")
        stream_dest = _stream_val("s")

        instructions = [
            ListInit(
                dest=list_dest,
                elem_type=_mir_type(TypeKind.INT),
                elements=[],
            ),
            StreamInit(
                dest=stream_dest,
                source=list_dest,
                elem_type=_mir_type(TypeKind.INT),
            ),
        ]
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_stream_init")
        llvm_mod = emitter.emit(module)
        ir_str = str(llvm_mod)

        assert "__mn_stream_from_list" in ir_str


# ===========================================================================
# Test: LLVM IR emission for StreamOp
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStreamOpEmission:
    """StreamOp instructions emit correct runtime calls."""

    def _make_stream_pipeline(self, ops):
        """Build instructions: list → stream → ops → return."""
        list_dest = _list_val("lst")
        stream_dest = _stream_val("s")
        instructions = [
            ListInit(
                dest=list_dest,
                elem_type=_mir_type(TypeKind.INT),
                elements=[],
            ),
            StreamInit(
                dest=stream_dest,
                source=list_dest,
                elem_type=_mir_type(TypeKind.INT),
            ),
        ]
        prev = stream_dest
        for i, (op_kind, args, fn_name) in enumerate(ops):
            dest_kind = TypeKind.LIST if op_kind == StreamOpKind.COLLECT else TypeKind.STREAM
            dest = Value(name=f"%op{i}", ty=_mir_type(dest_kind))
            instructions.append(
                StreamOp(
                    dest=dest,
                    op_kind=op_kind,
                    source=prev,
                    args=args,
                    fn_name=fn_name,
                )
            )
            prev = dest
        return instructions

    def test_take_emits_runtime_call(self):
        n_val = _mir_val("n")
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.TAKE, [n_val], ""),
            ]
        )
        # Prepend const for 'n'
        instructions.insert(0, Const(dest=n_val, ty=_mir_type(TypeKind.INT), value=3))
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_take")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_take" in ir_str

    def test_skip_emits_runtime_call(self):
        n_val = _mir_val("n")
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.SKIP, [n_val], ""),
            ]
        )
        instructions.insert(0, Const(dest=n_val, ty=_mir_type(TypeKind.INT), value=2))
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_skip")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_skip" in ir_str

    def test_collect_emits_runtime_call(self):
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.COLLECT, [], ""),
            ]
        )
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_collect")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_collect" in ir_str

    def test_map_emits_runtime_call(self):
        """Map with a function name emits __mn_stream_map."""
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.MAP, [], "my_map_fn"),
            ]
        )
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_map")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_map" in ir_str

    def test_filter_emits_runtime_call(self):
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.FILTER, [], "my_filter_fn"),
            ]
        )
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_filter")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_filter" in ir_str

    def test_chained_pipeline_emits_all(self):
        """filter |> take |> collect pipeline emits all three runtime calls."""
        n_val = _mir_val("n")
        instructions = self._make_stream_pipeline(
            [
                (StreamOpKind.FILTER, [], "pred_fn"),
                (StreamOpKind.TAKE, [n_val], ""),
                (StreamOpKind.COLLECT, [], ""),
            ]
        )
        instructions.insert(0, Const(dest=n_val, ty=_mir_type(TypeKind.INT), value=3))
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_chain")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_filter" in ir_str
        assert "__mn_stream_take" in ir_str
        assert "__mn_stream_collect" in ir_str


# ===========================================================================
# Test: Stream iteration via __iter_has_next / __iter_next
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStreamIteration:
    """for x in stream iteration emits __mn_stream_next."""

    def test_iter_has_next_emits_stream_next(self):
        """__iter_has_next on a STREAM type emits __mn_stream_next."""
        list_dest = _list_val("lst")
        stream_dest = _stream_val("s")
        has_next = _mir_val("hn", TypeKind.BOOL)

        instructions = [
            ListInit(
                dest=list_dest,
                elem_type=_mir_type(TypeKind.INT),
                elements=[],
            ),
            StreamInit(
                dest=stream_dest,
                source=list_dest,
                elem_type=_mir_type(TypeKind.INT),
            ),
            Call(dest=has_next, fn_name="__iter_has_next", args=[stream_dest]),
        ]
        module = _make_mir_module(instructions)
        emitter = LLVMMIREmitter(module_name="test_stream_iter")
        ir_str = str(emitter.emit(module))
        assert "__mn_stream_next" in ir_str
