"""Tests for DWARF debug info emission in the LLVM MIR emitter."""

from __future__ import annotations

import pytest

try:
    from llvmlite import ir as llvm_ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.lower import lower
from mapanare.mir import (
    BasicBlock,
    MIRFunction,
    MIRModule,
    MIRType,
    Return,
    SourceSpan,
    mir_int,
    mir_void,
)
from mapanare.parser import parse
from mapanare.semantic import check_or_raise
from mapanare.types import TypeInfo, TypeKind

pytestmark = pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")


def _emit_with_debug(source: str, filename: str = "test.mn") -> str:
    """Parse, lower, and emit LLVM IR with debug info enabled."""
    from mapanare.emit_llvm_mir import LLVMMIREmitter

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    mir = lower(ast, module_name="test", source_file=filename, source_directory="/test")
    emitter = LLVMMIREmitter(module_name="test", debug=True)
    llvm_module = emitter.emit(mir)
    return str(llvm_module)


def _emit_without_debug(source: str, filename: str = "test.mn") -> str:
    """Parse, lower, and emit LLVM IR with debug info disabled."""
    from mapanare.emit_llvm_mir import LLVMMIREmitter

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    mir = lower(ast, module_name="test", source_file=filename, source_directory="/test")
    emitter = LLVMMIREmitter(module_name="test", debug=False)
    llvm_module = emitter.emit(mir)
    return str(llvm_module)


# ---------------------------------------------------------------------------
# Task 1: DIBuilder integration — compile unit metadata
# ---------------------------------------------------------------------------


class TestCompileUnitMetadata:
    """Verify compile unit metadata is emitted."""

    def test_di_compile_unit_present(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "!DICompileUnit" in ir

    def test_di_file_present(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "!DIFile" in ir

    def test_di_file_has_filename(self) -> None:
        ir = _emit_with_debug("fn main() {}", filename="hello.mn")
        assert 'filename: "hello.mn"' in ir

    def test_di_file_has_directory(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert 'directory: "/test"' in ir

    def test_producer_is_mapanare(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert 'producer: "mapanare' in ir

    def test_emission_kind_full_debug(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "emissionKind: FullDebug" in ir

    def test_named_metadata_dbg_cu(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "!llvm.dbg.cu" in ir

    def test_debug_info_version_flag(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "Debug Info Version" in ir

    def test_dwarf_version_flag(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "Dwarf Version" in ir


# ---------------------------------------------------------------------------
# Task 3: Function debug info — DISubprogram
# ---------------------------------------------------------------------------


class TestFunctionDebugInfo:
    """Verify DISubprogram is emitted for functions."""

    def test_di_subprogram_present(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "!DISubprogram" in ir

    def test_di_subprogram_has_name(self) -> None:
        ir = _emit_with_debug("fn add(a: Int, b: Int) -> Int { return a + b }")
        assert 'name: "add"' in ir

    def test_di_subprogram_has_line(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "line: 1" in ir

    def test_di_subprogram_attached_to_function(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        # The define line should have !dbg
        for line in ir.split("\n"):
            if line.startswith("define") and "main" in line:
                assert "!dbg" in line, f"Function definition missing !dbg: {line}"
                break
        else:
            pytest.fail("Could not find function definition")

    def test_multiple_functions_have_subprograms(self) -> None:
        source = """
fn foo() -> Int { return 1 }
fn bar() -> Int { return 2 }
fn main() {}
"""
        ir = _emit_with_debug(source)
        assert ir.count("!DISubprogram") == 3

    def test_subroutine_type_present(self) -> None:
        ir = _emit_with_debug("fn main() {}")
        assert "!DISubroutineType" in ir


# ---------------------------------------------------------------------------
# Task 4: Line number info for MIR instructions
# ---------------------------------------------------------------------------


class TestLineNumberInfo:
    """Verify DILocation is emitted and attached to instructions."""

    def test_di_location_present(self) -> None:
        ir = _emit_with_debug("fn main() { let x: Int = 42 }")
        assert "!DILocation" in ir

    def test_dbg_metadata_on_instructions(self) -> None:
        source = """
fn main() {
    let x: Int = 42
    let y: Int = 10
}
"""
        ir = _emit_with_debug(source)
        # Count !dbg references on instructions (not metadata lines)
        dbg_instructions = [
            line for line in ir.split("\n") if "!dbg" in line and not line.strip().startswith("!")
        ]
        assert len(dbg_instructions) > 0, "No instructions have !dbg metadata"

    def test_line_numbers_are_accurate(self) -> None:
        source = "fn main() { let x: Int = 42 }"
        ir = _emit_with_debug(source)
        assert "line: 1" in ir  # main() is on line 1


# ---------------------------------------------------------------------------
# Task 5: Variable debug info — DILocalVariable
# ---------------------------------------------------------------------------


class TestVariableDebugInfo:
    """Verify DILocalVariable is emitted for named let bindings."""

    def test_di_local_variable_present(self) -> None:
        ir = _emit_with_debug("fn main() { let x: Int = 42 }")
        assert "!DILocalVariable" in ir

    def test_di_local_variable_has_name(self) -> None:
        ir = _emit_with_debug("fn main() { let x: Int = 42 }")
        assert 'name: "x"' in ir

    def test_di_local_variable_has_type(self) -> None:
        ir = _emit_with_debug("fn main() { let x: Int = 42 }")
        # Should have DIBasicType for Int
        assert "DW_ATE_signed" in ir

    def test_multiple_variables(self) -> None:
        source = """
fn main() {
    let a: Int = 1
    let b: Int = 2
    let c: Int = 3
}
"""
        ir = _emit_with_debug(source)
        assert 'name: "a"' in ir
        assert 'name: "b"' in ir
        assert 'name: "c"' in ir


# ---------------------------------------------------------------------------
# Task 6: Struct type debug info
# ---------------------------------------------------------------------------


class TestStructTypeDebugInfo:
    """Verify struct types get DICompositeType."""

    def test_struct_composite_type(self) -> None:
        source = """
struct Point {
    x: Int,
    y: Int,
}
fn main() {
    let p: Point = new Point { x: 10, y: 20 }
}
"""
        ir = _emit_with_debug(source)
        assert "DICompositeType" in ir
        assert "DW_TAG_structure_type" in ir

    def test_struct_has_name(self) -> None:
        source = """
struct Point {
    x: Int,
    y: Int,
}
fn main() {
    let p: Point = new Point { x: 10, y: 20 }
}
"""
        ir = _emit_with_debug(source)
        assert 'name: "Point"' in ir

    def test_struct_has_members(self) -> None:
        source = """
struct Point {
    x: Int,
    y: Int,
}
fn main() {
    let p: Point = new Point { x: 10, y: 20 }
}
"""
        ir = _emit_with_debug(source)
        assert "DW_TAG_member" in ir


# ---------------------------------------------------------------------------
# Task 7: --debug / -g CLI flag
# ---------------------------------------------------------------------------


class TestDebugCLIFlag:
    """Verify the -g/--debug CLI flag."""

    def test_debug_flag_exists(self) -> None:
        """The -g flag should be accepted by build, emit-llvm, and jit."""

        # Just check the argument parser accepts -g
        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args(["-g"])
        assert ns.debug is True

    def test_debug_flag_long_form(self) -> None:
        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args(["--debug"])
        assert ns.debug is True

    def test_no_debug_by_default(self) -> None:
        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args([])
        assert ns.debug is False


# ---------------------------------------------------------------------------
# Task 9: No debug info when disabled
# ---------------------------------------------------------------------------


class TestNoDebugWhenDisabled:
    """Verify no debug metadata when debug is off."""

    def test_no_di_compile_unit(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        assert "!DICompileUnit" not in ir

    def test_no_di_subprogram(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        assert "!DISubprogram" not in ir

    def test_no_di_location(self) -> None:
        ir = _emit_without_debug("fn main() { let x: Int = 42 }")
        assert "!DILocation" not in ir

    def test_no_dbg_attachments(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        for line in ir.split("\n"):
            if line.strip().startswith("!"):
                continue
            assert "!dbg" not in line, f"Unexpected !dbg on: {line}"


# ---------------------------------------------------------------------------
# MIR-level span tests
# ---------------------------------------------------------------------------


class TestMIRSpanThreading:
    """Verify AST spans are preserved in MIR instructions."""

    def test_source_span_on_module(self) -> None:
        ast = parse("fn main() {}", filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn", source_directory="/src")
        assert mir.source_file == "test.mn"
        assert mir.source_directory == "/src"

    def test_source_line_on_function(self) -> None:
        ast = parse("fn main() {}", filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn")
        fn = mir.functions[0]
        assert fn.source_line == 1
        assert fn.source_file == "test.mn"

    def test_span_on_instructions(self) -> None:
        source = "fn main() { let x: Int = 42 }"
        ast = parse(source, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn")
        fn = mir.functions[0]
        # At least some instructions should have spans
        has_span = any(inst.span is not None for bb in fn.blocks for inst in bb.instructions)
        assert has_span, "No instructions have source spans"

    def test_source_span_dataclass(self) -> None:
        span = SourceSpan(line=10, column=5, end_line=10, end_column=20)
        assert span.line == 10
        assert span.column == 5
        assert span.end_line == 10
        assert span.end_column == 20


# ---------------------------------------------------------------------------
# Direct emitter tests with manually constructed MIR
# ---------------------------------------------------------------------------


class TestDirectEmitterDebug:
    """Test DWARF emission with manually constructed MIR modules."""

    def test_empty_module_with_debug(self) -> None:
        from mapanare.emit_llvm_mir import LLVMMIREmitter

        mir = MIRModule(name="empty", source_file="empty.mn", source_directory=".")
        emitter = LLVMMIREmitter(module_name="empty", debug=True)
        llvm_mod = emitter.emit(mir)
        ir_str = str(llvm_mod)
        assert "!DICompileUnit" in ir_str
        assert "!DIFile" in ir_str

    def test_function_with_span(self) -> None:
        from mapanare.emit_llvm_mir import LLVMMIREmitter

        fn = MIRFunction(
            name="my_fn",
            params=[],
            return_type=mir_void(),
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Return(val=None, span=SourceSpan(line=5, column=1)),
                    ],
                )
            ],
            source_line=3,
            source_file="manual.mn",
        )
        mir = MIRModule(
            name="manual",
            source_file="manual.mn",
            source_directory="/manual",
            functions=[fn],
        )
        emitter = LLVMMIREmitter(module_name="manual", debug=True)
        llvm_mod = emitter.emit(mir)
        ir_str = str(llvm_mod)
        assert 'name: "my_fn"' in ir_str
        assert "line: 3" in ir_str
        assert "!DILocation" in ir_str

    def test_di_basic_types(self) -> None:
        from mapanare.emit_llvm_mir import LLVMMIREmitter

        mir = MIRModule(name="types", source_file="types.mn", source_directory=".")
        emitter = LLVMMIREmitter(module_name="types", debug=True)
        emitter.emit(mir)

        # Test type creation
        di_int = emitter._get_di_type(mir_int())
        assert di_int is not None

        from mapanare.mir import mir_bool, mir_float

        di_float = emitter._get_di_type(mir_float())
        assert di_float is not None

        di_bool = emitter._get_di_type(mir_bool())
        assert di_bool is not None

        # Void should return None
        di_void = emitter._get_di_type(mir_void())
        assert di_void is None

    def test_struct_debug_type(self) -> None:
        from mapanare.emit_llvm_mir import LLVMMIREmitter

        mir = MIRModule(
            name="struct_test",
            source_file="s.mn",
            source_directory=".",
            structs={"Vec2": [("x", mir_int()), ("y", mir_int())]},
        )
        emitter = LLVMMIREmitter(module_name="struct_test", debug=True)
        emitter.emit(mir)

        struct_type = MIRType(TypeInfo(kind=TypeKind.STRUCT, name="Vec2"))
        di_struct = emitter._get_di_type(struct_type)
        assert di_struct is not None

        ir_str = str(emitter.module)
        assert "DW_TAG_structure_type" in ir_str
        assert 'name: "Vec2"' in ir_str
