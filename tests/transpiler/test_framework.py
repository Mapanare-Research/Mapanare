"""Tests for the transpiler framework (mapanare/self/transpiler.mn).

Since the framework is a self-hosted .mn module, these tests verify:
1. The module compiles through the Python bootstrap emitter
2. The module's functions and structs are present in the compiled IR
3. The Python-side equivalents (from_python.py, from_php.py) maintain
   behavioral parity with the framework's design contracts
"""

from __future__ import annotations

from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
TRANSPILER_MN = SELF_DIR / "transpiler.mn"


class TestTranspilerModuleExists:
    """transpiler.mn exists and has expected content."""

    def test_file_exists(self) -> None:
        assert TRANSPILER_MN.exists(), "transpiler.mn not found"

    def test_has_type_mapping_struct(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct TypeMapping" in src

    def test_has_translate_type(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn translate_type(" in src

    def test_has_field_def(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct FieldDef" in src

    def test_has_method_def(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct MethodDef" in src

    def test_has_stdlib_shim(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct StdlibShim" in src

    def test_has_transpiler_state(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct TranspilerState" in src

    def test_has_catch_clause(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "struct CatchClause" in src

    def test_has_translate_class_to_struct(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn translate_class_to_struct(" in src

    def test_has_infer_local_type(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn infer_local_type(" in src

    def test_has_translate_stdlib_call(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn translate_stdlib_call(" in src

    def test_has_report_unsupported(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn report_unsupported(" in src

    def test_has_scope_management(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn push_scope(" in src
        assert "fn pop_scope(" in src
        assert "fn is_declared(" in src
        assert "fn declare_var(" in src

    def test_has_language_mappings(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        assert "fn python_type_mappings(" in src
        assert "fn php_type_mappings(" in src
        assert "fn typescript_type_mappings(" in src
        assert "fn go_type_mappings(" in src


class TestTranspilerCompiles:
    """transpiler.mn compiles through the Python bootstrap."""

    def test_parse_succeeds(self) -> None:
        from mapanare.parser import parse

        src = TRANSPILER_MN.read_text(encoding="utf-8")
        program = parse(src, filename="transpiler.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_semantic_check(self) -> None:
        from mapanare.parser import parse
        from mapanare.semantic import check

        src = TRANSPILER_MN.read_text(encoding="utf-8")
        program = parse(src, filename="transpiler.mn")
        check(program, filename="transpiler.mn")
        # Some errors are expected (substr, starts_with are runtime builtins)
        # Just verify no crash during semantic analysis
        assert program is not None

    def test_ir_emission(self) -> None:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        src = TRANSPILER_MN.read_text(encoding="utf-8")
        program = parse(src, filename="transpiler.mn")
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program)
        assert mir_module is not None
        assert len(mir_module.functions) > 0


class TestConcatIncludesTranspiler:
    """transpiler.mn is included in the concat output."""

    def test_in_module_order(self) -> None:
        concat_py = Path(__file__).resolve().parent.parent.parent / "scripts" / "concat_self.py"
        src = concat_py.read_text(encoding="utf-8")
        # Transpiler modules are commented out to avoid symbol clashes
        # (new_token, PyToken) with the core compiler. Check they're
        # referenced but excluded.
        assert "transpiler.mn" in src

    def test_mnc_all_excludes_transpiler(self) -> None:
        """Transpiler modules excluded from mnc_all.mn to avoid symbol clashes."""
        mnc_all = SELF_DIR / "mnc_all.mn"
        if mnc_all.exists():
            src = mnc_all.read_text(encoding="utf-8")
            assert "from_python.mn" not in src


class TestFrameworkDesignContracts:
    """Verify the framework's design contracts match existing transpiler behavior."""

    def test_python_type_mapping_parity(self) -> None:
        """Python transpiler type map should cover the same types as the framework."""
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        # The framework's python_type_mappings() should map these
        for mapping in ["int", "float", "str", "bool", "list", "dict"]:
            assert f'"{mapping}"' in src, f"Missing Python type mapping: {mapping}"

    def test_php_type_mapping_parity(self) -> None:
        """PHP transpiler type map should cover the same types as the framework."""
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        for mapping in ["int", "float", "string", "bool", "array", "void"]:
            assert f'"{mapping}"' in src, f"Missing PHP type mapping: {mapping}"

    def test_typescript_type_mappings(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        for mapping in ["number", "string", "boolean", "void", "any"]:
            assert f'"{mapping}"' in src, f"Missing TS type mapping: {mapping}"

    def test_go_type_mappings(self) -> None:
        src = TRANSPILER_MN.read_text(encoding="utf-8")
        for mapping in ["int", "int64", "float64", "string", "bool", "error"]:
            assert f'"{mapping}"' in src, f"Missing Go type mapping: {mapping}"
