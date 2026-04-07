"""Tests for the self-hosted Python transpiler (from_python.mn).

Verifies the module parses, compiles to MIR, and contains expected
infrastructure (tokenizer, parser, translation functions).
"""

from __future__ import annotations

from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
FROM_PYTHON_MN = SELF_DIR / "from_python.mn"


class TestFromPythonMnExists:
    """from_python.mn exists and has expected content."""

    def test_file_exists(self) -> None:
        assert FROM_PYTHON_MN.exists()

    def test_has_tokenizer(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn tokenize_python(" in src

    def test_has_py_token_struct(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "struct PyToken" in src

    def test_has_py_parser_struct(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "struct PyParser" in src

    def test_has_translate_python(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn translate_python(" in src

    def test_has_keyword_check(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn is_py_keyword(" in src

    def test_has_expression_translation(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn translate_py_expr(" in src

    def test_has_function_translation(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn translate_py_function(" in src

    def test_has_stdlib_shims(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "fn python_stdlib_shims(" in src

    def test_uses_transpiler_framework(self) -> None:
        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        assert "python_type_mappings()" in src
        assert "translate_stdlib_call(" in src
        assert "translate_type(" in src


class TestFromPythonMnCompiles:
    """from_python.mn compiles through the Python bootstrap."""

    def test_parse_succeeds(self) -> None:
        from mapanare.parser import parse

        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_python.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_ir_emission(self) -> None:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        src = FROM_PYTHON_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_python.mn")
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program)
        assert mir_module is not None
        assert len(mir_module.functions) > 0


class TestFromPythonMnInConcat:
    """from_python.mn is in the self-hosted build."""

    def test_in_module_order(self) -> None:
        concat_py = Path(__file__).resolve().parent.parent.parent / "scripts" / "concat_self.py"
        src = concat_py.read_text(encoding="utf-8")
        assert '"from_python.mn"' in src

    def test_mnc_all_contains_module(self) -> None:
        mnc_all = SELF_DIR / "mnc_all.mn"
        if mnc_all.exists():
            src = mnc_all.read_text(encoding="utf-8")
            assert "from_python.mn" in src
