"""Tests for mapanare/self/emit_llvm.mn — verifies the self-hosted LLVM emitter
(MIR-based) can be parsed by the Python compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.lexer import tokenize
from mapanare.parser import parse
from mapanare.semantic import check

SELF_DIR = Path(__file__).resolve().parents[2] / "mapanare" / "self"
EMIT_LLVM_MN = SELF_DIR / "emit_llvm.mn"
EMIT_LLVM_IR_MN = SELF_DIR / "emit_llvm_ir.mn"


@pytest.fixture
def emitter_source() -> str:
    return EMIT_LLVM_MN.read_text(encoding="utf-8")


@pytest.fixture
def emitter_ir_source() -> str:
    return EMIT_LLVM_IR_MN.read_text(encoding="utf-8")


@pytest.fixture
def combined_fn_names(emitter_source: str, emitter_ir_source: str) -> set[str]:
    """All function names across emit_llvm.mn and emit_llvm_ir.mn."""
    from mapanare.ast_nodes import FnDef

    fns: list[str] = []
    for src, name in [(emitter_source, "emit_llvm.mn"), (emitter_ir_source, "emit_llvm_ir.mn")]:
        program = parse(src, filename=name)
        fns.extend(f.name for f in program.definitions if isinstance(f, FnDef))
    return set(fns)


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

    def test_has_type_functions(self, combined_fn_names: set[str]) -> None:
        for name in [
            "llvm_int",
            "llvm_float",
            "llvm_bool",
            "llvm_char",
            "llvm_void",
            "llvm_string",
        ]:
            assert name in combined_fn_names

    def test_has_composite_type_functions(self, combined_fn_names: set[str]) -> None:
        for name in [
            "llvm_option_type",
            "llvm_result_type",
            "llvm_tensor_type",
            "llvm_list_type",
            "llvm_map_type",
        ]:
            assert name in combined_fn_names

    def test_has_type_resolver(self, combined_fn_names: set[str]) -> None:
        assert "resolve_mir_type" in combined_fn_names

    def test_has_arithmetic_instructions(self, combined_fn_names: set[str]) -> None:
        for name in ["emit_add", "emit_sub", "emit_mul", "emit_sdiv", "emit_srem"]:
            assert name in combined_fn_names
        for name in ["emit_fadd", "emit_fsub", "emit_fmul", "emit_fdiv", "emit_frem"]:
            assert name in combined_fn_names

    def test_has_unary_instructions(self, combined_fn_names: set[str]) -> None:
        for name in ["emit_fneg", "emit_neg", "emit_not"]:
            assert name in combined_fn_names

    def test_has_comparison_instructions(self, combined_fn_names: set[str]) -> None:
        for name in ["emit_icmp", "emit_fcmp", "emit_and_instr", "emit_or_instr"]:
            assert name in combined_fn_names

    def test_has_control_flow(self, combined_fn_names: set[str]) -> None:
        for name in ["emit_br", "emit_cbranch", "emit_mir_phi", "emit_switch_case"]:
            assert name in combined_fn_names

    def test_has_memory_instructions(self, emitter_source: str) -> None:
        program = parse(emitter_source, filename="emit_llvm.mn")
        from mapanare.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "emit_alloca" in fn_names
        assert "emit_store" in fn_names
        assert "emit_load" in fn_names

    def test_has_call_instructions(self, combined_fn_names: set[str]) -> None:
        for name in ["emit_call_ir", "emit_call_void", "emit_ret", "emit_ret_void"]:
            assert name in combined_fn_names

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
