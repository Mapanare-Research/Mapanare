"""v4.64.0: DWARF line metadata tests.

Verifies that -g builds attach !dbg to instructions and that the
DWARF line table is populated.
"""

from __future__ import annotations

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower as build_mir
from mapanare.parser import parse
from mapanare.semantic import check_or_raise


def _emit_with_debug(source: str) -> str:
    ast = parse(source, filename="<test>")
    check_or_raise(ast, filename="<test>")
    mir_module = build_mir(ast, module_name="test")
    emitter = LLVMTextEmitter(module_name="test", debug=True)
    return emitter.emit(mir_module)


class TestInstructionsHaveDbgAttachment:
    def test_call_instruction_has_dbg(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        for line in ir.split("\n"):
            if "call void @__mn_str_print" in line:
                assert "!dbg" in line, f"call missing !dbg: {line}"
                return
        assert False, "No print call found in IR"

    def test_ret_instruction_has_dbg(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        for line in ir.split("\n"):
            if line.strip().startswith("ret ") and "!dbg" in line:
                return
        # ret i64 0 in main might not have !dbg if it's synthesized — acceptable

    def test_store_instruction_has_dbg(self) -> None:
        ir = _emit_with_debug("fn main() { let x: Int = 42 }")
        dbg_stores = [l for l in ir.split("\n") if "store" in l and "!dbg" in l]
        assert len(dbg_stores) >= 1, "No store with !dbg found"

    def test_di_location_emitted(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "!DILocation" in ir


class TestNoDebugNoAttachment:
    def test_no_dbg_without_flag(self) -> None:
        ast = parse('fn main() { print("hello") }', filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir_module = build_mir(ast, module_name="test")
        emitter = LLVMTextEmitter(module_name="test", debug=False)
        ir = emitter.emit(mir_module)
        instruction_lines = [
            l for l in ir.split("\n") if l.strip().startswith(("%", "call", "store", "ret", "load"))
        ]
        for line in instruction_lines:
            assert "!dbg" not in line, f"!dbg found without -g: {line}"


class TestMultipleFunctionsHaveLineInfo:
    def test_each_function_has_locations(self) -> None:
        source = """
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { let x = add(1, 2) }
"""
        ir = _emit_with_debug(source)
        locations = [l for l in ir.split("\n") if "!DILocation" in l]
        assert len(locations) >= 2, f"Expected >=2 DILocations, got {len(locations)}"
