"""Tests for advanced WASM emitter features -- signals, streams, closures.

Tests cover:
  1. Signal computed emits call to compute function
  2. Signal subscribe emits memory store operations
  3. Stream map emits loop
  4. Stream filter emits loop
  5. Stream take emits loop with count check
  6. Stream skip emits loop with offset
  7. Stream collect extracts list pointer via i32.load
  8. Stream fold emits loop with accumulator
  9. Closure call emits call_indirect
  10. Function table populated with (table) and (elem) for closures
  11. Signal computed output contains no stubs
  12. Stream map output is not a trivial pass-through
"""

from __future__ import annotations

from dataclasses import field
from pathlib import Path

import pytest

from mapanare.parser import parse
from mapanare.semantic import check_or_raise

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Skip all tests if the WASM emitter module is not yet available
_wasm_emitter_available = True
try:
    from mapanare.emit_wasm import WasmEmitter  # type: ignore[import-not-found]
except ImportError:
    _wasm_emitter_available = False

pytestmark = pytest.mark.skipif(
    not _wasm_emitter_available,
    reason="mapanare.emit_wasm not yet implemented (v2.0.0 target)",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit(source: str) -> str:
    """Parse, type-check, lower to MIR, and emit WASM/WAT text."""
    from mapanare.lower import lower as build_mir

    ast = parse(source, filename="test.mn")
    check_or_raise(ast, filename="test.mn")
    mir_module = build_mir(ast, module_name="test")
    emitter = WasmEmitter()  # type: ignore[possibly-undefined]
    return emitter.emit(mir_module)


def _emit_from_mir(mir_module) -> str:  # type: ignore[no-untyped-def]
    """Emit WASM/WAT directly from a pre-built MIR module."""
    emitter = WasmEmitter()  # type: ignore[possibly-undefined]
    return emitter.emit(mir_module)


def _make_signal_computed_module():  # type: ignore[no-untyped-def]
    """Build a MIR module containing a SignalComputed instruction.

    Since the current lowerer does not produce SignalComputed from source,
    we construct the MIR manually to test the emitter.
    """
    from mapanare.mir import (
        BasicBlock,
        Const,
        MIRFunction,
        MIRModule,
        MIRType,
        Return,
        SignalComputed,
        Value,
    )
    from mapanare.types import TypeInfo, TypeKind

    sig_ty = MIRType(TypeInfo(kind=TypeKind.SIGNAL))
    int_ty = MIRType(TypeInfo(kind=TypeKind.INT))
    void_ty = MIRType(TypeInfo(kind=TypeKind.VOID))

    # A compute function that returns a constant
    ret_val = Value(name="%ret", ty=int_ty)
    compute_fn = MIRFunction(
        name="compute_val",
        params=[],
        return_type=int_ty,
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=ret_val, value=42, ty=int_ty),
                    Return(val=ret_val),
                ],
            )
        ],
    )

    # Main function that creates a computed signal
    sig_dest = Value(name="%sig0", ty=sig_ty)
    main_fn = MIRFunction(
        name="main",
        params=[],
        return_type=void_ty,
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    SignalComputed(dest=sig_dest, compute_fn="compute_val"),
                    Return(val=None),
                ],
            )
        ],
    )

    return MIRModule(name="test", functions=[compute_fn, main_fn])


def _make_signal_subscribe_module():  # type: ignore[no-untyped-def]
    """Build a MIR module containing a SignalSubscribe instruction.

    Since the current lowerer does not produce SignalSubscribe from source,
    we construct the MIR manually to test the emitter.
    """
    from mapanare.mir import (
        BasicBlock,
        Const,
        MIRFunction,
        MIRModule,
        MIRType,
        Return,
        SignalInit,
        SignalSubscribe,
        Value,
    )
    from mapanare.types import TypeInfo, TypeKind

    sig_ty = MIRType(TypeInfo(kind=TypeKind.SIGNAL))
    int_ty = MIRType(TypeInfo(kind=TypeKind.INT))
    void_ty = MIRType(TypeInfo(kind=TypeKind.VOID))

    sig_dest = Value(name="%sig0", ty=sig_ty)
    init_val = Value(name="%init", ty=int_ty)
    sub_val = Value(name="%sub", ty=int_ty)

    main_fn = MIRFunction(
        name="main",
        params=[],
        return_type=void_ty,
        blocks=[
            BasicBlock(
                label="entry",
                instructions=[
                    Const(dest=init_val, value=0, ty=int_ty),
                    SignalInit(dest=sig_dest, signal_type=sig_ty, initial_val=init_val),
                    Const(dest=sub_val, value=1, ty=int_ty),
                    SignalSubscribe(signal=sig_dest, subscriber=sub_val),
                    Return(val=None),
                ],
            )
        ],
    )

    return MIRModule(name="test", functions=[main_fn])


# ===========================================================================
# Signal tests
# ===========================================================================


class TestSignalComputed:
    """Test that computed signal emission calls the compute function."""

    def test_signal_computed_emits_call(self) -> None:
        """A computed signal should emit `call $compute_fn` in WAT."""
        mir_mod = _make_signal_computed_module()
        wat = _emit_from_mir(mir_mod)
        assert "signal_computed" in wat, "Expected signal_computed comment in WAT output"
        assert "call $compute_val" in wat, (
            "Computed signal must call the compute function to get initial value"
        )

    def test_no_empty_stubs_in_signals(self) -> None:
        """Signal computed output should NOT contain the word 'stub'."""
        mir_mod = _make_signal_computed_module()
        wat = _emit_from_mir(mir_mod)
        assert "stub" not in wat.lower(), (
            "Signal computed should have a real implementation, not a stub"
        )


class TestSignalSubscribe:
    """Test that signal subscription emits memory store operations."""

    def test_signal_subscribe_emits_store(self) -> None:
        """Subscribing to a signal should emit i32.store for the subscriber list."""
        mir_mod = _make_signal_subscribe_module()
        wat = _emit_from_mir(mir_mod)
        assert "signal_subscribe" in wat, "Expected signal_subscribe comment in WAT output"
        assert "i32.store" in wat, (
            "Signal subscribe must store subscriber pointer in linear memory"
        )

    def test_signal_subscribe_manages_count(self) -> None:
        """Signal subscribe should read and increment the subscriber count."""
        mir_mod = _make_signal_subscribe_module()
        wat = _emit_from_mir(mir_mod)
        # The subscriber count is loaded from offset 8 and incremented
        assert "i32.load" in wat, "Must load current subscriber count"
        assert "i32.add" in wat, "Must increment subscriber count"


# ===========================================================================
# Stream tests
# ===========================================================================


class TestStreamMap:
    """Test stream map emits a loop in WAT."""

    def test_stream_map_emits_loop(self) -> None:
        """stream.map(fn) should emit a loop block in WAT."""
        src = (
            "fn double(x: Int) -> Int { return x * 2 }\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    let s = stream(items)\n"
            "    let mapped = s.map(double)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "loop" in wat, "Stream map must emit a loop for iteration"

    def test_no_empty_stubs_in_streams(self) -> None:
        """Stream map output should NOT just be a trivial pass-through."""
        src = (
            "fn double(x: Int) -> Int { return x * 2 }\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    let s = stream(items)\n"
            "    let mapped = s.map(double)\n"
            "}\n"
        )
        wat = _emit(src)
        # The old stub just did (local.set $dest (local.get $source))
        # The real implementation should have loop + call
        assert "stream_map" in wat, "Expected stream_map comment"
        # Verify it is NOT just a trivial assignment by checking for loop presence
        # Extract lines around stream_map comment
        lines = wat.split("\n")
        stream_section = []
        in_section = False
        for line in lines:
            if "stream_map" in line:
                in_section = True
            if in_section:
                stream_section.append(line)
                if len(stream_section) > 20:
                    break
        stream_text = "\n".join(stream_section)
        assert "loop" in stream_text, (
            "Stream map section must contain a loop, not a trivial pass-through"
        )


class TestStreamFilter:
    """Test stream filter emits a loop in WAT."""

    def test_stream_filter_emits_loop(self) -> None:
        """stream.filter(fn) should emit a loop block in WAT."""
        src = (
            "fn positive(x: Int) -> Bool { return x > 0 }\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    let s = stream(items)\n"
            "    let filtered = s.filter(positive)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "loop" in wat, "Stream filter must emit a loop for iteration"


class TestStreamTake:
    """Test stream take emits loop with count check."""

    def test_stream_take_emits_loop(self) -> None:
        """stream.take(n) should emit a loop with a count check."""
        src = (
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3, 4, 5]\n"
            "    let s = stream(items)\n"
            "    let taken = s.take(3)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "loop" in wat, "Stream take must emit a loop"
        assert "stream_take" in wat, "Expected stream_take comment in WAT"


class TestStreamSkip:
    """Test stream skip emits loop with offset."""

    def test_stream_skip_emits_loop(self) -> None:
        """stream.skip(n) should emit a loop with offset computation."""
        src = (
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3, 4, 5]\n"
            "    let s = stream(items)\n"
            "    let skipped = s.skip(2)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "loop" in wat, "Stream skip must emit a loop"
        assert "stream_skip" in wat, "Expected stream_skip comment in WAT"


class TestStreamCollect:
    """Test stream collect extracts list pointer."""

    def test_stream_collect_extracts_list(self) -> None:
        """collect should emit i32.load to extract the list pointer from the stream."""
        src = (
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    let s = stream(items)\n"
            "    let collected = s.collect()\n"
            "}\n"
        )
        wat = _emit(src)
        assert "stream_collect" in wat, "Expected stream_collect comment"
        assert "i32.load" in wat, "Collect must load the list pointer from the stream struct"


class TestStreamFold:
    """Test stream fold emits a loop with accumulator."""

    def test_stream_fold_emits_loop(self) -> None:
        """fold should emit a loop that applies the accumulator function."""
        src = (
            "fn add(a: Int, b: Int) -> Int { return a + b }\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    let s = stream(items)\n"
            "    let total = s.fold(0, add)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "loop" in wat, "Stream fold must emit a loop"
        assert "stream_fold" in wat, "Expected stream_fold comment in WAT"


# ===========================================================================
# Closure tests
# ===========================================================================


class TestClosureCall:
    """Test closure call emits call_indirect."""

    def test_closure_call_emits_call_indirect(self) -> None:
        """Calling a closure should emit call_indirect in WAT."""
        src = (
            "fn main() -> Int {\n"
            "    let y: Int = 10\n"
            "    let f = (x) => x + y\n"
            "    return f(5)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "call_indirect" in wat, (
            "Closure call must use call_indirect for indirect function dispatch"
        )


class TestFunctionTable:
    """Test function table is populated when closures are used."""

    def test_function_table_populated(self) -> None:
        """When closures are used, WAT should contain (table) and (elem) declarations."""
        src = (
            "fn main() -> Int {\n"
            "    let y: Int = 10\n"
            "    let f = (x) => x + y\n"
            "    return f(5)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "(table" in wat, "WAT must declare a function table for indirect calls"
        assert "(elem" in wat, (
            "WAT must have an (elem) section populating the table with function references"
        )

    def test_function_table_has_funcref(self) -> None:
        """The table declaration should specify funcref type."""
        src = (
            "fn main() -> Int {\n"
            "    let y: Int = 10\n"
            "    let f = (x) => x + y\n"
            "    return f(5)\n"
            "}\n"
        )
        wat = _emit(src)
        assert "funcref" in wat, "Table must use funcref type"
