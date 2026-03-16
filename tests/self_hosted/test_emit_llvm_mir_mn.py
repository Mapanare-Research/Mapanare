"""Tests for the self-hosted emit_llvm.mn module (MIR-based).

Validates that emit_llvm.mn:
1. Imports lower.mn (MIR types) instead of ast
2. Has all MIR instruction handlers
3. Has the emit_mir_module public API
4. Has type resolution from MIR types to LLVM types
5. Passes structural validation
"""

from __future__ import annotations

from pathlib import Path

import pytest

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
EMIT_LLVM_MN = SELF_DIR / "emit_llvm.mn"


@pytest.fixture
def emit_llvm_source() -> str:
    """Read the emit_llvm.mn source file."""
    assert EMIT_LLVM_MN.exists(), f"emit_llvm.mn not found at {EMIT_LLVM_MN}"
    return EMIT_LLVM_MN.read_text(encoding="utf-8")


# ===================================================================
# Structural validation
# ===================================================================


class TestEmitLlvmMnStructure:
    """Validate the structure of the MIR-based emit_llvm.mn."""

    def test_file_exists(self) -> None:
        assert EMIT_LLVM_MN.exists()

    def test_minimum_line_count(self, emit_llvm_source: str) -> None:
        """emit_llvm.mn should be at least 1000 lines."""
        lines = emit_llvm_source.strip().split("\n")
        assert len(lines) >= 1000, f"emit_llvm.mn has only {len(lines)} lines (expected >= 1000)"

    def test_imports_lower_not_ast(self, emit_llvm_source: str) -> None:
        """MIR-based emitter should import lower, not ast."""
        assert "import self::lower" in emit_llvm_source
        assert "import self::ast" not in emit_llvm_source

    def test_has_emit_state(self, emit_llvm_source: str) -> None:
        assert "struct EmitState" in emit_llvm_source

    def test_has_public_api(self, emit_llvm_source: str) -> None:
        assert "fn emit_mir_module" in emit_llvm_source


# ===================================================================
# MIR type resolution
# ===================================================================


class TestEmitLlvmMnTypeResolution:
    """Ensure emit_llvm.mn resolves MIR types to LLVM types."""

    def test_has_resolve_mir_type(self, emit_llvm_source: str) -> None:
        assert "fn resolve_mir_type" in emit_llvm_source

    @pytest.mark.parametrize(
        "llvm_type_fn",
        [
            "llvm_int",
            "llvm_float",
            "llvm_bool",
            "llvm_char",
            "llvm_void",
            "llvm_string",
            "llvm_ptr",
        ],
    )
    def test_has_llvm_type_fn(self, emit_llvm_source: str, llvm_type_fn: str) -> None:
        assert f"fn {llvm_type_fn}" in emit_llvm_source

    @pytest.mark.parametrize(
        "composite_fn",
        [
            "llvm_option_type",
            "llvm_result_type",
            "llvm_tensor_type",
            "llvm_list_type",
            "llvm_map_type",
        ],
    )
    def test_has_composite_type_fn(self, emit_llvm_source: str, composite_fn: str) -> None:
        assert f"fn {composite_fn}" in emit_llvm_source


# ===================================================================
# LLVM IR instruction builders
# ===================================================================


class TestEmitLlvmMnInstructionBuilders:
    """Ensure all LLVM IR string builders are present."""

    @pytest.mark.parametrize(
        "builder_fn",
        [
            "emit_alloca",
            "emit_store",
            "emit_load",
            "emit_add",
            "emit_sub",
            "emit_mul",
            "emit_sdiv",
            "emit_srem",
            "emit_fadd",
            "emit_fsub",
            "emit_fmul",
            "emit_fdiv",
            "emit_frem",
            "emit_fneg",
            "emit_neg",
            "emit_not",
            "emit_icmp",
            "emit_fcmp",
            "emit_br",
            "emit_cbranch",
            "emit_ret",
            "emit_ret_void",
            "emit_gep",
            "emit_insertvalue",
            "emit_extractvalue",
            "emit_bitcast",
        ],
    )
    def test_has_builder(self, emit_llvm_source: str, builder_fn: str) -> None:
        assert f"fn {builder_fn}" in emit_llvm_source


# ===================================================================
# MIR instruction handlers
# ===================================================================


class TestEmitLlvmMnMirHandlers:
    """Ensure emit_llvm.mn handles all MIR instruction types."""

    def test_has_emit_mir_instruction(self, emit_llvm_source: str) -> None:
        assert "fn emit_mir_instruction" in emit_llvm_source

    @pytest.mark.parametrize(
        "handler_fn",
        [
            "emit_const",
            "emit_copy",
            "emit_cast",
            "emit_binop",
            "emit_unaryop",
            "emit_struct_init",
            "emit_field_get",
            "emit_field_set",
            "emit_list_init",
            "emit_index_get",
            "emit_index_set",
            "emit_map_init",
            "emit_enum_init",
            "emit_enum_tag",
            "emit_enum_payload",
            "emit_wrap_some",
            "emit_wrap_none",
            "emit_wrap_ok",
            "emit_wrap_err",
            "emit_unwrap",
            "emit_mir_call",
            "emit_mir_return",
            "emit_mir_switch",
            "emit_agent_spawn",
            "emit_agent_send",
            "emit_agent_sync",
            "emit_signal_init",
            "emit_signal_get",
            "emit_signal_set",
            "emit_stream_op",
            "emit_interp_concat",
            "emit_mir_phi",
        ],
    )
    def test_has_handler(self, emit_llvm_source: str, handler_fn: str) -> None:
        assert f"fn {handler_fn}" in emit_llvm_source


# ===================================================================
# MIR walking functions
# ===================================================================


class TestEmitLlvmMnMirWalking:
    """Ensure emit_llvm.mn walks MIR structures correctly."""

    def test_has_emit_mir_basic_block(self, emit_llvm_source: str) -> None:
        assert "fn emit_mir_basic_block" in emit_llvm_source

    def test_has_emit_mir_function(self, emit_llvm_source: str) -> None:
        assert "fn emit_mir_function" in emit_llvm_source

    def test_has_register_mir_struct(self, emit_llvm_source: str) -> None:
        assert "fn register_mir_struct" in emit_llvm_source

    def test_has_register_mir_enum(self, emit_llvm_source: str) -> None:
        assert "fn register_mir_enum" in emit_llvm_source

    def test_has_declare_mir_extern(self, emit_llvm_source: str) -> None:
        assert "fn declare_mir_extern" in emit_llvm_source


# ===================================================================
# Built-in function support
# ===================================================================


class TestEmitLlvmMnBuiltins:
    """Ensure emit_llvm.mn handles built-in function calls."""

    @pytest.mark.parametrize(
        "builtin_fn",
        [
            "emit_builtin_print",
            "emit_builtin_println",
            "emit_builtin_len",
            "emit_builtin_tostring",
        ],
    )
    def test_has_builtin(self, emit_llvm_source: str, builtin_fn: str) -> None:
        assert f"fn {builtin_fn}" in emit_llvm_source


# ===================================================================
# Runtime declarations
# ===================================================================


class TestEmitLlvmMnRuntime:
    """Ensure runtime function declarations are present."""

    def test_has_declare_all_runtime(self, emit_llvm_source: str) -> None:
        assert "fn declare_all_runtime" in emit_llvm_source

    @pytest.mark.parametrize(
        "runtime_fn",
        [
            "__mn_str_concat",
            "__mn_str_eq",
            "__mn_str_len",
            "__mn_str_println",
            "__mn_str_from_int",
            "__mn_list_new",
            "__mn_list_push",
            "__mn_list_get",
            "__mn_list_len",
            "__mn_panic",
            "__mn_agent_spawn",
            "__mn_signal_new",
        ],
    )
    def test_declares_runtime_fn(self, emit_llvm_source: str, runtime_fn: str) -> None:
        assert runtime_fn in emit_llvm_source


# ===================================================================
# BinOp coverage — all operators mapped
# ===================================================================


class TestEmitLlvmMnBinOpCoverage:
    """Ensure all BinOp variants are handled in emit_binop."""

    @pytest.mark.parametrize(
        "variant",
        ["add", "sub", "mul", "div", "mod", "eq", "ne", "lt", "gt", "le", "ge", "and", "or"],
    )
    def test_binop_variant(self, emit_llvm_source: str, variant: str) -> None:
        # Check that the variant appears in emit_binop's string dispatch
        assert f'op_str == "{variant}"' in emit_llvm_source
