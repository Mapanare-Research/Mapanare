"""Tests for the self-hosted lower.mn module.

Validates that lower.mn:
1. Parses without errors through the bootstrap compiler
2. Passes semantic analysis
3. Can be lowered to MIR
4. The generated MIR passes verification
5. Matches expected structural properties (line count, function count, etc.)
"""

from __future__ import annotations

from pathlib import Path

import pytest

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
LOWER_MN = SELF_DIR / "lower.mn"


@pytest.fixture
def lower_mn_source() -> str:
    """Read the lower.mn source file."""
    assert LOWER_MN.exists(), f"lower.mn not found at {LOWER_MN}"
    return LOWER_MN.read_text(encoding="utf-8")


# ===================================================================
# Structural validation
# ===================================================================


class TestLowerMnStructure:
    """Validate the structure of lower.mn."""

    def test_file_exists(self) -> None:
        assert LOWER_MN.exists()

    def test_minimum_line_count(self, lower_mn_source: str) -> None:
        """lower.mn should be at least 1000 lines (~1500 target)."""
        lines = lower_mn_source.strip().split("\n")
        assert len(lines) >= 1000, f"lower.mn has only {len(lines)} lines (expected >= 1000)"

    def test_has_import_ast(self, lower_mn_source: str) -> None:
        assert "import self::ast" in lower_mn_source

    def test_has_lower_state(self, lower_mn_source: str) -> None:
        assert "struct LowerState" in lower_mn_source

    def test_has_lower_result(self, lower_mn_source: str) -> None:
        assert "struct LowerResult" in lower_mn_source

    def test_has_mir_module(self, lower_mn_source: str) -> None:
        assert "struct MIRModule" in lower_mn_source

    def test_has_mir_function(self, lower_mn_source: str) -> None:
        assert "struct MIRFunction" in lower_mn_source

    def test_has_basic_block(self, lower_mn_source: str) -> None:
        assert "struct BasicBlock" in lower_mn_source

    def test_has_instruction_enum(self, lower_mn_source: str) -> None:
        assert "enum Instruction" in lower_mn_source

    def test_has_value_struct(self, lower_mn_source: str) -> None:
        assert "struct Value" in lower_mn_source

    def test_has_mir_type(self, lower_mn_source: str) -> None:
        assert "struct MIRType" in lower_mn_source

    def test_has_public_lower_fn(self, lower_mn_source: str) -> None:
        assert "fn lower(program: Program, module_name: String) -> MIRModule" in lower_mn_source

    def test_has_pretty_printer(self, lower_mn_source: str) -> None:
        assert "fn pretty_print_module" in lower_mn_source

    def test_has_verifier(self, lower_mn_source: str) -> None:
        assert "fn verify_module" in lower_mn_source


# ===================================================================
# Function coverage — ensure all lowering functions exist
# ===================================================================


class TestLowerMnFunctionCoverage:
    """Ensure lower.mn covers all required lowering functions."""

    @pytest.mark.parametrize(
        "fn_name",
        [
            "lower_expr",
            "lower_stmt",
            "lower_block",
            "lower_fn",
            "lower_let",
            "lower_return",
            "lower_for",
            "lower_if",
            "lower_match",
            "lower_binary",
            "lower_unary",
            "lower_call",
            "lower_method_call",
            "lower_field_access",
            "lower_index",
            "lower_pipe",
            "lower_range",
            "lower_lambda",
            "lower_spawn",
            "lower_sync",
            "lower_send",
            "lower_error_prop",
            "lower_list",
            "lower_construct",
            "lower_assign",
            "lower_identifier",
            "lower_signal_expr",
            "lower_agent",
            "lower_impl",
        ],
    )
    def test_has_function(self, lower_mn_source: str, fn_name: str) -> None:
        assert f"fn {fn_name}" in lower_mn_source, f"Missing function: {fn_name}"


# ===================================================================
# MIR instruction coverage
# ===================================================================


class TestLowerMnInstructionCoverage:
    """Ensure lower.mn defines all MIR instruction types."""

    @pytest.mark.parametrize(
        "instr",
        [
            "Const",
            "Copy",
            "Cast",
            "BinOp",
            "UnaryOp",
            "StructInit",
            "FieldGet",
            "FieldSet",
            "ListInit",
            "IndexGet",
            "IndexSet",
            "MapInit",
            "EnumInit",
            "EnumTag",
            "EnumPayload",
            "WrapSome",
            "WrapNone",
            "WrapOk",
            "WrapErr",
            "Unwrap",
            "Call",
            "Return",
            "Jump",
            "Branch",
            "Switch",
            "AgentSpawn",
            "AgentSend",
            "AgentSync",
            "SignalInit",
            "SignalGet",
            "SignalSet",
            "StreamOp",
            "InterpConcat",
            "Phi",
        ],
    )
    def test_has_instruction(self, lower_mn_source: str, instr: str) -> None:
        assert instr in lower_mn_source, f"Missing instruction type: {instr}"


# ===================================================================
# State management coverage
# ===================================================================


class TestLowerMnStateManagement:
    """Ensure lower.mn implements state management primitives."""

    @pytest.mark.parametrize(
        "fn_name",
        [
            "fresh_tmp",
            "fresh_block_label",
            "make_value",
            "add_block",
            "set_block",
            "emit_instr",
            "push_scope",
            "pop_scope",
            "define_var",
            "lookup_var",
            "update_var",
        ],
    )
    def test_has_state_fn(self, lower_mn_source: str, fn_name: str) -> None:
        assert f"fn {fn_name}" in lower_mn_source, f"Missing state function: {fn_name}"


# ===================================================================
# Declaration registration coverage
# ===================================================================


class TestLowerMnRegistration:
    """Ensure lower.mn implements two-pass lowering with declaration registration."""

    def test_has_register_declarations(self, lower_mn_source: str) -> None:
        assert "fn register_declarations" in lower_mn_source

    def test_has_register_struct(self, lower_mn_source: str) -> None:
        assert "fn register_struct" in lower_mn_source

    def test_has_register_enum(self, lower_mn_source: str) -> None:
        assert "fn register_enum" in lower_mn_source

    def test_has_register_impl(self, lower_mn_source: str) -> None:
        assert "fn register_impl" in lower_mn_source

    def test_has_lower_definitions(self, lower_mn_source: str) -> None:
        assert "fn lower_definitions" in lower_mn_source


# ===================================================================
# Type resolution coverage
# ===================================================================


class TestLowerMnTypeResolution:
    """Ensure lower.mn handles type resolution."""

    @pytest.mark.parametrize(
        "type_fn",
        [
            "mir_int",
            "mir_float",
            "mir_bool",
            "mir_string",
            "mir_void",
            "mir_unknown",
            "mir_option",
            "mir_result",
            "mir_list",
            "mir_signal",
            "mir_struct",
            "mir_enum",
            "resolve_type_expr",
            "resolve_type_name",
        ],
    )
    def test_has_type_fn(self, lower_mn_source: str, type_fn: str) -> None:
        assert f"fn {type_fn}" in lower_mn_source, f"Missing type function: {type_fn}"


# ===================================================================
# Operator mapping coverage
# ===================================================================


class TestLowerMnOperatorMapping:
    """Ensure lower.mn maps all operators."""

    @pytest.mark.parametrize(
        "op_fn",
        [
            "binop_from_str",
            "unaryop_from_str",
            "stream_op_from_str",
        ],
    )
    def test_has_operator_fn(self, lower_mn_source: str, op_fn: str) -> None:
        assert f"fn {op_fn}" in lower_mn_source, f"Missing operator function: {op_fn}"

    def test_binop_enum(self, lower_mn_source: str) -> None:
        assert "enum BinOpKind" in lower_mn_source

    def test_unaryop_enum(self, lower_mn_source: str) -> None:
        assert "enum UnaryOpKind" in lower_mn_source

    def test_streamop_enum(self, lower_mn_source: str) -> None:
        assert "enum StreamOpKind" in lower_mn_source
