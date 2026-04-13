"""v4.65.0: DWARF variable debug info tests.

Verifies DILocalVariable, llvm.dbg.declare, and parameter debug info
with arg indices.
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


class TestParameterDebugInfo:
    def test_parameter_has_di_local_variable(self) -> None:
        ir = _emit_with_debug("fn f(x: Int) -> Int { return x }\nfn main() { f(1) }")
        assert "DILocalVariable" in ir
        assert '"x"' in ir

    def test_parameter_has_arg_index(self) -> None:
        ir = _emit_with_debug(
            "fn add(a: Int, b: Int) -> Int { return a + b }\nfn main() { add(1, 2) }"
        )
        lines = [l for l in ir.split("\n") if "DILocalVariable" in l]
        arg_lines = [l for l in lines if "arg:" in l]
        assert len(arg_lines) >= 2, f"Expected >=2 params with arg:, got {len(arg_lines)}"
        assert "arg: 1" in arg_lines[0]
        assert "arg: 2" in arg_lines[1]

    def test_dbg_declare_after_param_alloca(self) -> None:
        ir = _emit_with_debug("fn f(x: Int) -> Int { return x }\nfn main() { f(1) }")
        assert "llvm.dbg.declare" in ir


class TestDbgDeclareIntrinsic:
    def test_intrinsic_declared(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "declare void @llvm.dbg.declare" in ir

    def test_intrinsic_value_declared(self) -> None:
        ir = _emit_with_debug('fn main() { print("hello") }')
        assert "declare void @llvm.dbg.value" in ir


class TestNoVariablesWithoutDebug:
    def test_no_di_local_variable(self) -> None:
        ast = parse("fn f(x: Int) -> Int { return x }\nfn main() { f(1) }", filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir = build_mir(ast, module_name="test")
        emitter = LLVMTextEmitter(module_name="test", debug=False)
        ir = emitter.emit(mir)
        assert "DILocalVariable" not in ir
        assert "llvm.dbg.declare" not in ir
