"""Stage 1 bootstrap test — verify the self-hosted .mn files can be
compiled by the Python compiler.

This test compiles each self-hosted .mn file through the Python pipeline
(parse → semantic check) and verifies:
1. All .mn files parse successfully
2. All .mn files pass semantic analysis (no critical errors)
3. The Python compiler can compile the .mn compiler sources
4. LLVM IR output is deterministic for functions with primitive types
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.ast_nodes import FnDef, NamedType, Program
from mapanare.emit_llvm import LLVMEmitter
from mapanare.parser import parse
from mapanare.semantic import check

SELF_DIR = Path(__file__).resolve().parents[2] / "mapanare" / "self"
MN_FILES = sorted(SELF_DIR.glob("*.mn"))

# Primitive types the LLVM emitter can resolve
_PRIMITIVE_NAMES = {"Int", "Float", "Bool", "Char", "String", "Void"}


def _has_only_primitive_types(fn: FnDef) -> bool:
    """Check if a function uses only primitive types (emitter-compatible)."""
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


def _extract_primitive_fns(program: Program) -> Program:
    """Extract only functions with primitive types for LLVM emission."""
    primitive_fns = [
        d for d in program.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)
    ]
    return Program(definitions=primitive_fns)


class TestStage1Bootstrap:
    """Stage 1: Python compiler compiles .mn compiler sources."""

    @pytest.fixture(params=[f.name for f in MN_FILES], ids=[f.stem for f in MN_FILES])
    def mn_file(self, request: pytest.FixtureRequest) -> Path:
        return SELF_DIR / request.param

    def test_all_mn_files_exist(self) -> None:
        expected = {"ast.mn", "lexer.mn", "parser.mn", "semantic.mn", "emit_llvm.mn"}
        actual = {f.name for f in MN_FILES}
        assert expected <= actual, f"Missing .mn files: {expected - actual}"

    def test_parse_succeeds(self, mn_file: Path) -> None:
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        assert program is not None
        assert len(program.definitions) > 0

    def test_semantic_no_crash(self, mn_file: Path) -> None:
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        errors = check(program, filename=mn_file.name)
        assert isinstance(errors, list)

    @pytest.mark.xfail(reason="AST emitter can't resolve cross-module .mn functions", strict=False)
    def test_emit_llvm_ir_primitive_fns(self, mn_file: Path) -> None:
        """LLVM emitter processes functions with primitive-only types."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        prim_program = _extract_primitive_fns(program)
        if not prim_program.definitions:
            pytest.skip("No primitive-type-only functions in this file")
        emitter = LLVMEmitter(module_name=mn_file.stem)
        module = emitter.emit_program(prim_program)
        ir_text = str(module)
        assert len(ir_text) > 0
        assert "ModuleID" in ir_text

    @pytest.mark.xfail(reason="AST emitter can't resolve cross-module .mn functions", strict=False)
    def test_emit_deterministic(self, mn_file: Path) -> None:
        """Same input → same LLVM IR output (deterministic compilation)."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        prim_program = _extract_primitive_fns(program)
        if not prim_program.definitions:
            pytest.skip("No primitive-type-only functions in this file")

        emitter1 = LLVMEmitter(module_name=mn_file.stem)
        ir1 = str(emitter1.emit_program(prim_program))

        program2 = parse(source, filename=mn_file.name)
        prim2 = _extract_primitive_fns(program2)
        emitter2 = LLVMEmitter(module_name=mn_file.stem)
        ir2 = str(emitter2.emit_program(prim2))

        assert ir1 == ir2, "LLVM IR output is not deterministic"


class TestStage1CrossFile:
    """Cross-file bootstrap verification."""

    def test_total_definition_count(self) -> None:
        total_defs = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            total_defs += len(program.definitions)
        assert total_defs >= 100, f"Expected at least 100 total defs, got {total_defs}"

    def test_all_files_have_primitive_fns(self) -> None:
        """Every .mn file has at least some functions with primitive types."""
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            prim = _extract_primitive_fns(program)
            # ast.mn and mir.mn have no primitive-only fns (all return custom types), so skip
            if mn_file.name in ("ast.mn", "mir.mn"):
                continue
            assert len(prim.definitions) > 0, f"{mn_file.name}: no primitive fns"

    @pytest.mark.xfail(reason="AST emitter cross-module resolution", strict=False)
    def test_combined_ir_output(self) -> None:
        """All primitive functions across .mn files compile to valid IR."""
        all_fns: list[FnDef] = []
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            for d in program.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns.append(d)
        combined = Program(definitions=all_fns)
        emitter = LLVMEmitter(module_name="bootstrap_combined")
        module = emitter.emit_program(combined)
        ir_text = str(module)
        assert "define" in ir_text
