"""Cb.5-tests (v4.144.0): unit tests for _enum_inline machinery.

Parent docket Cb.5 closed v4.140.0 (self-hosted enum_inline parity
with Python emitter). At v4.143.0 Rattler + Cobra flagged that
coverage was integration-only (benchmarks/system/enum_match.mn
checksum 52818168). This module adds dedicated eligibility +
pack/unpack + ABI-parity tests.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower as build_mir
from mapanare.mir import MIRType, mir_bool, mir_float, mir_int, mir_string
from mapanare.types import TypeInfo, TypeKind

ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mir_type(kind: TypeKind, name: str = "") -> MIRType:
    """Build a MIRType from a TypeKind and optional name."""
    return MIRType(TypeInfo(kind=kind, name=name))


def _emit_program(source: str) -> str:
    """Compile a Mapanare source string to LLVM IR text via the Python pipeline."""
    from mapanare.parser import parse

    ast = parse(source)
    mir_module = build_mir(ast, module_name="test_enum_inline")
    emitter = LLVMTextEmitter(module_name="test_enum_inline")
    return emitter.emit(mir_module)


# ---------------------------------------------------------------------------
# Test class 1: Inline-slot eligibility
# ---------------------------------------------------------------------------


class TestEnumInlineEligibility:
    """Test _compute_enum_inline_slots eligibility logic."""

    def _make_emitter(self) -> LLVMTextEmitter:
        return LLVMTextEmitter(module_name="test")

    def test_two_int_payloads_eligible(self) -> None:
        """Enum with ≤ 2 Int fields per variant qualifies for inline."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "A": [mir_int()],
            "B": [mir_int(), mir_int()],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 2  # max payload fields across variants

    def test_single_int_payload_eligible(self) -> None:
        """Enum with a single Int payload qualifies with 1 slot."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Just": [mir_int()],
            "Nothing": [],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 1

    def test_float_payload_eligible(self) -> None:
        """Float (double) fits an i64 slot via bitcast."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Val": [mir_float()],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 1

    def test_bool_payload_eligible(self) -> None:
        """Bool (i1) fits an i64 slot via zext."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Flag": [mir_bool()],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 1

    def test_three_payloads_ineligible(self) -> None:
        """Enum with > 2 payload fields in any variant is ineligible."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Triple": [mir_int(), mir_int(), mir_int()],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 0  # exceeds _MAX_INLINE_SLOTS=2

    def test_string_field_ineligible(self) -> None:
        """String ({ptr, i64}) does not fit an i64 slot."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Msg": [mir_string()],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 0

    def test_list_field_ineligible(self) -> None:
        """List ({ptr, i64, i64}) does not fit an i64 slot."""
        e = self._make_emitter()
        list_type = _mir_type(TypeKind.LIST, "List")
        pays: dict[str, list[MIRType]] = {
            "Items": [list_type],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 0

    def test_self_reference_ineligible(self) -> None:
        """Boxed (self-referencing) fields force boxed representation."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Node": [mir_int(), mir_int()],
        }
        # Simulate a boxed field (self-referencing)
        boxed = {("Node", 1)}
        result = e._compute_enum_inline_slots(pays, boxed)
        assert result == 0

    def test_unit_only_enum_returns_zero(self) -> None:
        """Enum with only unit variants returns 0 (no payload to inline)."""
        e = self._make_emitter()
        pays: dict[str, list[MIRType]] = {
            "Red": [],
            "Green": [],
            "Blue": [],
        }
        result = e._compute_enum_inline_slots(pays, boxed=set())
        assert result == 0  # max_fields == 0, stays at 0


class TestTypeFitsInlineSlot:
    """Test _type_fits_inline_slot static method."""

    @pytest.mark.parametrize(
        "ty,expected",
        [
            ("i64", True),
            ("double", True),
            ("i1", True),
            ("i8", True),
            ("i16", True),
            ("i32", True),
            ("ptr", True),
            ("i64*", True),  # legacy typed pointer
            ("{ptr, i64}", False),  # String
            ("{ptr, i64, i64}", False),  # List
            ("%struct.Foo", False),  # user struct
            ("void", False),
        ],
    )
    def test_inline_slot_predicate(self, ty: str, expected: bool) -> None:
        assert LLVMTextEmitter._type_fits_inline_slot(ty) == expected


# ---------------------------------------------------------------------------
# Test class 2: Pack/unpack round-trips
# ---------------------------------------------------------------------------


class TestEnumInlinePackUnpack:
    """Test _pack_to_i64 / _unpack_from_i64 instruction generation."""

    def _make_emitter_in_fn(self) -> LLVMTextEmitter:
        """Create an emitter with enough state to call _pack/_unpack."""
        e = LLVMTextEmitter(module_name="test")
        # Set up minimal function context so _f() and _L() work
        e._cb = "entry"
        e._blk = {"entry": []}
        e._c = 0
        e._lines = []
        return e

    def test_i64_passthrough(self) -> None:
        """i64 → i64: no conversion needed."""
        e = self._make_emitter_in_fn()
        result = e._pack_to_i64("%val", "i64")
        assert result == "%val"  # direct passthrough
        # Unpack should also be passthrough
        back = e._unpack_from_i64("%val", "i64")
        assert back == "%val"

    def test_double_bitcast(self) -> None:
        """double → i64 via bitcast; i64 → double via bitcast."""
        e = self._make_emitter_in_fn()
        packed = e._pack_to_i64("%fval", "double")
        assert packed.startswith("%")
        blk = e._blk["entry"]
        assert any("bitcast double %fval to i64" in line for line in blk)

        blk.clear()
        unpacked = e._unpack_from_i64("%ival", "double")
        assert unpacked.startswith("%")
        assert any("bitcast i64 %ival to double" in line for line in blk)

    @pytest.mark.parametrize("ty", ["i1", "i8", "i16", "i32"])
    def test_small_int_zext_trunc(self, ty: str) -> None:
        """Small ints zext to i64 for pack; trunc back for unpack."""
        e = self._make_emitter_in_fn()
        packed = e._pack_to_i64("%sval", ty)
        assert packed.startswith("%")
        blk = e._blk["entry"]
        assert any(f"zext {ty} %sval to i64" in line for line in blk)

        blk.clear()
        unpacked = e._unpack_from_i64("%ival", ty)
        assert unpacked.startswith("%")
        assert any(f"trunc i64 %ival to {ty}" in line for line in blk)

    def test_ptr_ptrtoint_inttoptr(self) -> None:
        """ptr → i64 via ptrtoint; i64 → ptr via inttoptr."""
        e = self._make_emitter_in_fn()
        packed = e._pack_to_i64("%pval", "ptr")
        assert packed.startswith("%")
        blk = e._blk["entry"]
        assert any("ptrtoint ptr %pval to i64" in line for line in blk)

        blk.clear()
        unpacked = e._unpack_from_i64("%ival", "ptr")
        assert unpacked.startswith("%")
        assert any("inttoptr i64 %ival to ptr" in line for line in blk)


# ---------------------------------------------------------------------------
# Test class 3: IR shape — full pipeline
# ---------------------------------------------------------------------------


class TestEnumInlineIRShape:
    """Test that inline enums produce the expected IR structure."""

    SHAPE_ENUM_SOURCE = """\
enum Shape {
    Circle(Int),
    Square(Int),
    Triangle(Int, Int),
    Point,
    Line(Int),
    Rect(Int, Int)
}

fn area(s: Shape) -> Int {
    match s {
        Circle(r) => { da r * r * 3 },
        Square(side) => { da side * side },
        Triangle(base, height) => { da base * height / 2 },
        Point => { da 0 },
        Line(len) => { da len },
        Rect(w, h) => { da w * h }
    }
}

fn main() {
    pon s: Shape = Shape::Circle(42)
    print(str(area(s)))
}
"""

    def test_shape_emits_inline_type(self) -> None:
        """Shape enum produces {i64, i64, i64} (tag + 2 payload slots),
        not {i64, ptr} (boxed)."""
        ir = _emit_program(self.SHAPE_ENUM_SOURCE)
        # The Python emitter uses anonymous struct types inline
        # The inline representation should have {i64, i64, i64}
        assert "{i64, i64, i64}" in ir
        # Should NOT have heap allocation for enum construction
        # (no malloc / __mn_alloc for enum init)
        # insertvalue with {i64, i64, i64} is the inline enum construction
        insertvalue_lines = [
            line for line in ir.split("\n") if "insertvalue {i64, i64, i64}" in line
        ]
        assert len(insertvalue_lines) > 0, "Expected inline insertvalue instructions"

    def test_no_malloc_for_inline_enum(self) -> None:
        """Inline enums should not call malloc / __mn_alloc for construction."""
        ir = _emit_program(self.SHAPE_ENUM_SOURCE)
        # Filter to just the area and main functions
        # Inline enums use insertvalue directly, not malloc
        enum_init_lines = [
            line
            for line in ir.split("\n")
            if ("__mn_alloc" in line or "malloc" in line) and "enum" in line.lower()
        ]
        # No malloc calls for enum construction in this program
        # (all variants have ≤ 2 Int fields → inline)
        assert len(enum_init_lines) == 0

    def test_extractvalue_for_payload(self) -> None:
        """Inline enum payload extraction uses extractvalue, not load from ptr."""
        ir = _emit_program(self.SHAPE_ENUM_SOURCE)
        extract_lines = [line for line in ir.split("\n") if "extractvalue {i64, i64, i64}" in line]
        assert len(extract_lines) > 0, "Expected inline extractvalue instructions"


class TestEnumInlineABIParity:
    """Test that Python emitter and self-hosted emitter produce ABI-compatible
    enum representations."""

    @pytest.fixture
    def enum_match_source(self) -> str:
        return (ROOT / "benchmarks" / "system" / "enum_match.mn").read_text()

    def test_python_emitter_uses_inline_for_shape(self, enum_match_source: str) -> None:
        """Python emitter produces {i64, i64, i64} for the Shape enum."""
        ir = _emit_program(enum_match_source)
        assert "{i64, i64, i64}" in ir

    def test_self_hosted_uses_inline_for_shape(self) -> None:
        """Self-hosted emitter (mnc-stage1) produces %enum.Shape = type {i64, i64, i64}."""
        stage1 = ROOT / "mapanare" / "self" / "mnc-stage1"
        if not stage1.exists():
            pytest.skip("mnc-stage1 not built")
        bench = ROOT / "benchmarks" / "system" / "enum_match.mn"
        result = subprocess.run(
            [str(stage1), "emit-llvm", str(bench)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        ir = result.stdout
        assert "%enum.Shape = type {i64, i64, i64}" in ir

    def test_abi_equivalent_type_width(self, enum_match_source: str) -> None:
        """Both emitters produce a 3×i64 enum type (24 bytes)."""
        stage1 = ROOT / "mapanare" / "self" / "mnc-stage1"
        if not stage1.exists():
            pytest.skip("mnc-stage1 not built")
        bench = ROOT / "benchmarks" / "system" / "enum_match.mn"

        # Python emitter
        py_ir = _emit_program(enum_match_source)

        # Self-hosted emitter
        result = subprocess.run(
            [str(stage1), "emit-llvm", str(bench)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        sh_ir = result.stdout

        # Both should use 3 i64 slots for Shape
        assert "{i64, i64, i64}" in py_ir
        # Self-hosted uses named type
        assert "{i64, i64, i64}" in sh_ir
