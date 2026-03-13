"""Tests for mapanare/self/emit_llvm.mn — verifies the self-hosted LLVM emitter
(MIR-based) can be parsed by the Python compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.lexer import tokenize
from mapanare.parser import parse
from mapanare.semantic import check

EMIT_LLVM_MN = Path(__file__).resolve().parents[2] / "mapanare" / "self" / "emit_llvm.mn"


@pytest.fixture
def emitter_source() -> str:
    return EMIT_LLVM_MN.read_text(encoding="utf-8")


class TestEmitLlvmMnParsing:
    """Ensure emit_llvm.mn parses without errors."""

    def test_tokenize(self, emitter_source: str) -> None:
        tokens = tokenize(emitter_source, filename="emit_llvm.mn")
        assert len(tokens) > 0

    def test_parse(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_has_emitter_struct(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        struct_names = {s.name for s in structs}
        assert "EmitState" in struct_names

    def test_has_type_functions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "llvm_int" in fn_names
        assert "llvm_float" in fn_names
        assert "llvm_bool" in fn_names
        assert "llvm_char" in fn_names
        assert "llvm_void" in fn_names
        assert "llvm_string" in fn_names

    def test_has_composite_type_functions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "llvm_option_type" in fn_names
        assert "llvm_result_type" in fn_names
        assert "llvm_tensor_type" in fn_names
        assert "llvm_list_type" in fn_names
        assert "llvm_map_type" in fn_names

    def test_has_type_resolver(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "resolve_mir_type" in fn_names

    def test_has_arithmetic_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        for name in ["emit_add", "emit_sub", "emit_mul", "emit_sdiv", "emit_srem"]:
            assert name in fn_names
        for name in ["emit_fadd", "emit_fsub", "emit_fmul", "emit_fdiv", "emit_frem"]:
            assert name in fn_names

    def test_has_unary_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_fneg" in fn_names
        assert "emit_neg" in fn_names
        assert "emit_not" in fn_names

    def test_has_comparison_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_icmp" in fn_names
        assert "emit_fcmp" in fn_names
        assert "emit_and_instr" in fn_names
        assert "emit_or_instr" in fn_names

    def test_has_control_flow(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_br" in fn_names
        assert "emit_cbranch" in fn_names
        assert "emit_mir_phi" in fn_names
        assert "emit_switch_case" in fn_names

    def test_has_memory_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_alloca" in fn_names
        assert "emit_store" in fn_names
        assert "emit_load" in fn_names

    def test_has_call_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_call_ir" in fn_names
        assert "emit_call_void" in fn_names
        assert "emit_ret" in fn_names
        assert "emit_ret_void" in fn_names

    def test_has_tensor_runtime(self, emitter_source: str) -> None:
        assert "__mapanare_tensor_add" in emitter_source
        assert "__mapanare_matmul" in emitter_source

    def test_has_public_api(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_mir_module" in fn_names
        assert "emit_mir_function" in fn_names
        assert "emit_mir_basic_block" in fn_names

    def test_semantic_check(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        errors = check(program, filename="emit_llvm.mn")
        assert isinstance(errors, list)


class TestEmitLlvmMnCoverage:
    """Verify the emitter covers all LLVM type mappings from Python."""

    def test_primitive_type_mappings(self, emitter_source: str) -> None:
        assert '"i64"' in emitter_source  # Int
        assert '"double"' in emitter_source  # Float
        assert '"i1"' in emitter_source  # Bool
        assert '"i8"' in emitter_source  # Char
        assert '"void"' in emitter_source  # Void
        assert '"{ i8*, i64 }"' in emitter_source  # String

    def test_tensor_runtime_fns_listed(self, emitter_source: str) -> None:
        runtime_fns = [
            "__mapanare_tensor_add",
            "__mapanare_tensor_sub",
            "__mapanare_tensor_mul",
            "__mapanare_tensor_div",
            "__mapanare_matmul",
            "__mapanare_tensor_alloc",
            "__mapanare_tensor_free",
            "__mapanare_tensor_shape_eq",
            "__mapanare_detect_gpus",
        ]
        for fn in runtime_fns:
            assert fn in emitter_source, f"Missing tensor runtime fn: {fn}"

    def test_emitter_struct_has_fields(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        emit_state = next(s for s in structs if s.name == "EmitState")
        field_names = {f.name for f in emit_state.fields}
        assert "lines" in field_names
        assert "counter" in field_names
        assert "module_name" in field_names

    def test_emittable_function_ratio(self, emitter_source: str) -> None:
        """emit_llvm.mn should have many functions (MIR handlers + builders)."""
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        assert len(fns) >= 50, f"Only {len(fns)} functions (expected >= 50)"
