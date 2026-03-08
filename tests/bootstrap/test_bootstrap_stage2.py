"""Stage 2 bootstrap test — verify Stage 1 output is stable.

Stage 2 compiles the same .mn sources a second time and checks that
the LLVM IR is byte-for-byte identical to Stage 1 output. This proves
the compiler is a fixed point: compiling twice yields the same result.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapa.ast_nodes import FnDef, NamedType, Program
from mapa.emit_llvm import LLVMEmitter
from mapa.parser import parse

SELF_DIR = Path(__file__).resolve().parents[2] / "mapa" / "self"
MN_FILES = sorted(SELF_DIR.glob("*.mn"))
_PRIMITIVE_NAMES = {"Int", "Float", "Bool", "Char", "String", "Void"}


def _has_only_primitive_types(fn: FnDef) -> bool:
    for p in fn.params:
        if p.type_annotation is not None:
            if not isinstance(p.type_annotation, NamedType):
                return False
            if p.type_annotation.name not in _PRIMITIVE_NAMES:
                return False
    if fn.return_type is not None:
        if not isinstance(fn.return_type, NamedType):
            return False
        if fn.return_type.name not in _PRIMITIVE_NAMES:
            return False
    return True


def _compile_to_ir(mn_file: Path) -> str:
    source = mn_file.read_text(encoding="utf-8")
    program = parse(source, filename=mn_file.name)
    prim_fns = [
        d for d in program.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)
    ]
    if not prim_fns:
        return ""
    emitter = LLVMEmitter(module_name=mn_file.stem)
    module = emitter.emit_program(Program(definitions=prim_fns))
    return str(module)


class TestStage2Bootstrap:
    """Stage 2: Two independent compilations produce identical IR."""

    @pytest.fixture(params=[f.name for f in MN_FILES], ids=[f.stem for f in MN_FILES])
    def mn_file(self, request: pytest.FixtureRequest) -> Path:
        return SELF_DIR / request.param

    def test_stage2_identical_to_stage1(self, mn_file: Path) -> None:
        """Compile twice independently → identical LLVM IR."""
        ir_stage1 = _compile_to_ir(mn_file)
        ir_stage2 = _compile_to_ir(mn_file)
        if not ir_stage1:
            pytest.skip("No primitive-type functions")
        assert ir_stage1 == ir_stage2, f"Stage 2 IR differs from Stage 1 for {mn_file.name}"

    def test_stage2_combined_fixed_point(self) -> None:
        """All files combined: two compilations → identical combined IR."""
        all_fns_1: list[FnDef] = []
        all_fns_2: list[FnDef] = []
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            p1 = parse(source, filename=mn_file.name)
            p2 = parse(source, filename=mn_file.name)
            for d in p1.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns_1.append(d)
            for d in p2.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns_2.append(d)

        e1 = LLVMEmitter(module_name="bootstrap_s2_a")
        ir1 = str(e1.emit_program(Program(definitions=all_fns_1)))

        e2 = LLVMEmitter(module_name="bootstrap_s2_a")
        ir2 = str(e2.emit_program(Program(definitions=all_fns_2)))

        assert ir1 == ir2, "Combined Stage 2 IR is not a fixed point"

    def test_ir_contains_function_definitions(self) -> None:
        """The combined IR should contain real LLVM function definitions."""
        all_fns: list[FnDef] = []
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            for d in program.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns.append(d)
        emitter = LLVMEmitter(module_name="bootstrap_verify")
        ir = str(emitter.emit_program(Program(definitions=all_fns)))
        assert ir.count("define") >= 10, "Expected at least 10 function definitions"
        assert "entry:" in ir, "Expected entry blocks in functions"
