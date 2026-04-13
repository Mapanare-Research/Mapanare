"""v4.62.0: DWARF debug info infrastructure tests.

Verifies the emitter's debug metadata helpers work correctly and that
the -g flag enables debug emission without breaking IR generation.
"""

from __future__ import annotations

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower as build_mir
from mapanare.parser import parse
from mapanare.semantic import check_or_raise


def _make_emitter(debug: bool = False) -> LLVMTextEmitter:
    return LLVMTextEmitter(module_name="test", debug=debug)


class TestDebugFlagEnablesEmission:
    """The -g flag must set _debug_enabled on the emitter."""

    def test_debug_false_by_default(self) -> None:
        e = _make_emitter(debug=False)
        assert not e._debug_enabled

    def test_debug_true_when_set(self) -> None:
        e = _make_emitter(debug=True)
        assert e._debug_enabled


class TestEmitDebugMetadata:
    """Infrastructure smoke tests for metadata helpers."""

    def test_returns_id_reference(self) -> None:
        e = _make_emitter(debug=True)
        ref = e._emit_debug_metadata("!{i32 42}")
        assert ref.startswith("!")
        assert ref[1:].isdigit()

    def test_increments_counter(self) -> None:
        e = _make_emitter(debug=True)
        r1 = e._emit_debug_metadata("!{i32 1}")
        r2 = e._emit_debug_metadata("!{i32 2}")
        assert r1 != r2
        assert int(r2[1:]) == int(r1[1:]) + 1

    def test_metadata_stored_in_lines(self) -> None:
        e = _make_emitter(debug=True)
        e._emit_debug_metadata("!{i32 99}")
        assert len(e._debug_metadata_lines) == 1
        assert "99" in e._debug_metadata_lines[0]


class TestFileTableDeduplication:
    """Requesting the same file twice returns the same ID."""

    def test_same_file_same_id(self) -> None:
        e = _make_emitter(debug=True)
        id1 = e._get_debug_file("src/main.mn")
        id2 = e._get_debug_file("src/main.mn")
        assert id1 == id2

    def test_different_files_different_ids(self) -> None:
        e = _make_emitter(debug=True)
        id1 = e._get_debug_file("src/main.mn")
        id2 = e._get_debug_file("src/lib.mn")
        assert id1 != id2


class TestLocationTableDeduplication:
    """Requesting the same location twice returns the same ID."""

    def test_same_location_same_id(self) -> None:
        e = _make_emitter(debug=True)
        id1 = e._get_debug_location(0, 10, 5)
        id2 = e._get_debug_location(0, 10, 5)
        assert id1 == id2

    def test_different_locations_different_ids(self) -> None:
        e = _make_emitter(debug=True)
        id1 = e._get_debug_location(0, 10, 5)
        id2 = e._get_debug_location(0, 20, 1)
        assert id1 != id2


class TestEmptyDwarfEmission:
    """A -g build must still produce valid LLVM IR (empty DWARF at v4.62.0)."""

    def test_debug_flag_does_not_break_emission(self) -> None:
        source = 'fn main() { print("hello") }'
        ast = parse(source, filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir_module = build_mir(ast, module_name="test")
        emitter = LLVMTextEmitter(module_name="test", debug=True)
        ir = emitter.emit(mir_module)
        assert "define" in ir
        assert "hello" in ir
