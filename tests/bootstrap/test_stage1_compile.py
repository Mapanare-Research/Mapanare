"""Stage 1 bootstrap compilation tests.

Verifies that the Python bootstrap compiler can compile the self-hosted
compiler (mapanare/self/*.mn) to valid LLVM IR.
"""

from __future__ import annotations

import pathlib

from mapanare.cli import _compile_to_llvm_ir


def _read_self_hosted() -> tuple[str, str]:
    """Read the self-hosted compiler entry point."""
    path = pathlib.Path("mapanare/self/main.mn")
    return path.read_text(encoding="utf-8"), str(path)


class TestStage1Compilation:
    """The bootstrap compiler must produce valid LLVM IR for the self-hosted compiler."""

    def test_self_hosted_compiles_to_llvm_ir(self) -> None:
        """All 7 self-hosted modules compile to LLVM IR."""
        source, filename = _read_self_hosted()
        llvm_ir = _compile_to_llvm_ir(source, filename)
        assert llvm_ir, "LLVM IR output is empty"
        assert "define" in llvm_ir

    def test_self_hosted_ir_verifies(self) -> None:
        """The generated LLVM IR passes LLVM's module verifier."""
        from llvmlite import binding as llvm

        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        source, filename = _read_self_hosted()
        llvm_ir = _compile_to_llvm_ir(source, filename)
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()

    def test_self_hosted_ir_compiles_to_object(self) -> None:
        """The LLVM IR can be compiled to native object code."""
        from mapanare.jit import jit_compile_to_object

        source, filename = _read_self_hosted()
        llvm_ir = _compile_to_llvm_ir(source, filename)
        obj_bytes = jit_compile_to_object(llvm_ir, opt_level=0)
        assert len(obj_bytes) > 0, "Object code is empty"

    def test_self_hosted_contains_all_modules(self) -> None:
        """The compiled IR contains functions from all 7 self-hosted modules."""
        source, filename = _read_self_hosted()
        llvm_ir = _compile_to_llvm_ir(source, filename)
        for prefix in ["lexer__", "parser__", "semantic__", "lower__", "emit_llvm__"]:
            assert prefix in llvm_ir, f"Module prefix '{prefix}' not found in IR"

    def test_self_hosted_ir_size_reasonable(self) -> None:
        """8000+ lines of .mn should produce substantial IR."""
        source, filename = _read_self_hosted()
        llvm_ir = _compile_to_llvm_ir(source, filename)
        lines = llvm_ir.count("\n")
        assert lines > 10000, f"IR only has {lines} lines"
