"""v4.63.0: DWARF DICompileUnit + DISubprogram emission tests.

Verifies that -g produces DWARF metadata with compile unit, file,
basic types, subroutine types, and subprograms.
"""

from __future__ import annotations

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower as build_mir
from mapanare.parser import parse
from mapanare.semantic import check_or_raise


def _emit_with_debug(source: str, filename: str = "<test>") -> str:
    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    mir_module = build_mir(ast, module_name="test")
    emitter = LLVMTextEmitter(module_name="test", debug=True)
    return emitter.emit(mir_module)


class TestCompileUnitEmitted:
    def test_has_di_compile_unit(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "!DICompileUnit" in ir

    def test_has_dwarf_version_5(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert '"Dwarf Version", i32 5' in ir

    def test_has_debug_info_version(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert '"Debug Info Version", i32 3' in ir

    def test_language_is_c99(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "DW_LANG_C99" in ir

    def test_producer_is_mapanare(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "Mapanare" in ir


class TestSubprogramEmitted:
    def test_main_has_subprogram(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "!DISubprogram" in ir
        assert '"main"' in ir

    def test_function_linked_via_dbg(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "!dbg" in ir
        # The define line should have !dbg
        for line in ir.split("\n"):
            if line.startswith("define") and "@main" in line:
                assert "!dbg" in line, f"define line missing !dbg: {line}"
                break

    def test_multiple_functions_each_have_subprogram(self) -> None:
        source = """
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(str(add(1, 2))) }
"""
        ir = _emit_with_debug(source)
        subprograms = [line for line in ir.split("\n") if "!DISubprogram" in line]
        assert len(subprograms) >= 2, f"Expected >=2 subprograms, got {len(subprograms)}"


class TestBasicTypesEmitted:
    def test_int_basic_type(self) -> None:
        ir = _emit_with_debug("fn f(x: Int) -> Int { return x }\nfn main() { f(1) }")
        assert "DW_ATE_signed" in ir

    def test_float_basic_type(self) -> None:
        ir = _emit_with_debug("fn f(x: Float) -> Float { return x }\nfn main() { f(1.0) }")
        assert "DW_ATE_float" in ir

    def test_bool_basic_type(self) -> None:
        ir = _emit_with_debug("fn f(x: Bool) -> Bool { return x }\nfn main() { f(true) }")
        assert "DW_ATE_boolean" in ir


class TestNoDebugNoDwarf:
    def test_no_debug_flag_no_metadata(self) -> None:
        ast = parse('fn main() { print("hello") }', filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir_module = build_mir(ast, module_name="test")
        emitter = LLVMTextEmitter(module_name="test", debug=False)
        ir = emitter.emit(mir_module)
        assert "!DICompileUnit" not in ir
        assert "!DISubprogram" not in ir
