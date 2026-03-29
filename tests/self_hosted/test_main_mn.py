"""Tests for the self-hosted main.mn module.

Validates that main.mn:
1. Wires the full pipeline: parse → check → lower → emit_llvm
2. Imports all required modules including lower.mn
3. Has compile and compile_and_print functions
"""

from __future__ import annotations

from pathlib import Path

import pytest

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
MAIN_MN = SELF_DIR / "main.mn"


@pytest.fixture
def main_mn_source() -> str:
    """Read the main.mn source file."""
    assert MAIN_MN.exists(), f"main.mn not found at {MAIN_MN}"
    return MAIN_MN.read_text(encoding="utf-8")


class TestMainMnStructure:
    """Validate the structure of main.mn."""

    def test_file_exists(self) -> None:
        assert MAIN_MN.exists()

    def test_imports_all_modules(self, main_mn_source: str) -> None:
        """main.mn should import all 5 compiler modules."""
        assert "import self::ast" in main_mn_source
        assert "import self::parser" in main_mn_source
        assert "import self::semantic" in main_mn_source
        assert "import self::lower" in main_mn_source
        assert "import self::emit_llvm" in main_mn_source

    def test_has_compile_fn(self, main_mn_source: str) -> None:
        assert "fn compile(source: String, filename: String) -> CompileResult" in main_mn_source

    def test_has_compile_and_print_fn(self, main_mn_source: str) -> None:
        assert "fn compile_and_print" in main_mn_source

    def test_has_version_fn(self, main_mn_source: str) -> None:
        assert "fn version()" in main_mn_source

    def test_has_format_error_fn(self, main_mn_source: str) -> None:
        assert "fn format_error" in main_mn_source


class TestMainMnPipeline:
    """Validate the pipeline wiring in main.mn."""

    def test_calls_lower(self, main_mn_source: str) -> None:
        """compile() should call lower() to produce MIR."""
        assert "lower(program" in main_mn_source

    def test_calls_emit(self, main_mn_source: str) -> None:
        """compile() should call emit_mir_module()."""
        assert "emit_mir_module(" in main_mn_source

    def test_pipeline_order(self, main_mn_source: str) -> None:
        """Pipeline should be: parse → check → lower → emit_mir_module."""
        src = main_mn_source
        parse_pos = src.index("parse(source")
        check_pos = src.index("check(program")
        lower_pos = src.index("lower(program")
        emit_pos = src.index("emit_mir_module(")
        assert parse_pos < check_pos < lower_pos < emit_pos

    def test_version_string(self, main_mn_source: str) -> None:
        """Version should be 2.0.1."""
        assert "2.0.1" in main_mn_source


class TestMainMnCompileResult:
    """Validate the CompileResult struct."""

    def test_has_compile_result(self, main_mn_source: str) -> None:
        assert "struct CompileResult" in main_mn_source

    def test_compile_result_has_success(self, main_mn_source: str) -> None:
        assert "success: Bool" in main_mn_source

    def test_compile_result_has_ir_text(self, main_mn_source: str) -> None:
        assert "ir_text: String" in main_mn_source

    def test_compile_result_has_errors(self, main_mn_source: str) -> None:
        assert "errors: List<SemanticError>" in main_mn_source
