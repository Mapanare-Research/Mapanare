"""Tests for three-stage bootstrap verification (Phase 3).

Validates the self-hosted compiler modules can be parsed by the bootstrap
compiler and tracks progress toward full compilation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.parser import parse

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
ALL_MODULES = [
    "ast.mn",
    "lexer.mn",
    "parser.mn",
    "semantic.mn",
    "mir.mn",
    "lower_state.mn",
    "lower.mn",
    "emit_llvm_ir.mn",
    "emit_llvm.mn",
    "main.mn",
]


# ===================================================================
# Parse verification — all 7 modules parse without errors
# ===================================================================


class TestBootstrapParse:
    """All self-hosted modules must parse through the bootstrap compiler."""

    @pytest.mark.parametrize("module_name", ALL_MODULES)
    def test_module_parses(self, module_name: str) -> None:
        path = SELF_DIR / module_name
        assert path.exists(), f"{module_name} not found"
        source = path.read_text(encoding="utf-8")
        ast = parse(source, filename=str(path))
        assert ast is not None
        assert len(ast.definitions) > 0


# ===================================================================
# Module import graph — verify import structure
# ===================================================================


class TestBootstrapImports:
    """Verify the import graph of self-hosted modules."""

    def test_main_imports_all(self) -> None:
        source = (SELF_DIR / "main.mn").read_text(encoding="utf-8")
        assert "import self::ast" in source
        assert "import self::parser" in source
        assert "import self::semantic" in source
        assert "import self::lower" in source
        assert "import self::emit_llvm" in source

    def test_emit_llvm_imports_mir(self) -> None:
        source = (SELF_DIR / "emit_llvm.mn").read_text(encoding="utf-8")
        assert "import self::mir" in source

    def test_lower_imports_ast(self) -> None:
        source = (SELF_DIR / "lower.mn").read_text(encoding="utf-8")
        assert "import self::ast" in source

    def test_lower_imports_mir(self) -> None:
        source = (SELF_DIR / "lower.mn").read_text(encoding="utf-8")
        assert "import self::mir" in source


# ===================================================================
# Module resolution — self:: prefix handling
# ===================================================================


class TestSelfModuleResolution:
    """Verify the module resolver handles self:: imports."""

    def test_self_import_resolution(self) -> None:
        from mapanare.modules import ModuleResolver

        resolver = ModuleResolver()
        source_dir = str(SELF_DIR)

        # self::ast should resolve to ast.mn in the same directory
        result = resolver.resolve_path(["self", "ast"], source_dir)
        assert result is not None
        assert result.endswith("ast.mn")
        assert "self" + "/" + "self" not in result.replace("\\", "/")

    @pytest.mark.parametrize("module", ["ast", "lexer", "parser", "semantic", "mir", "lower_state", "lower", "emit_llvm_ir", "emit_llvm"])
    def test_resolves_all_self_modules(self, module: str) -> None:
        from mapanare.modules import ModuleResolver

        resolver = ModuleResolver()
        result = resolver.resolve_path(["self", module], str(SELF_DIR))
        assert result is not None, f"Failed to resolve self::{module}"


# ===================================================================
# Module line counts — track self-hosted compiler size
# ===================================================================


class TestBootstrapModuleSizes:
    """Track self-hosted compiler module sizes."""

    def test_total_line_count(self) -> None:
        """All 7 modules combined should be substantial."""
        total = 0
        for name in ALL_MODULES:
            source = (SELF_DIR / name).read_text(encoding="utf-8")
            total += len(source.strip().split("\n"))
        # 7 modules: ast(256) + lexer(500) + parser(850) + semantic(800)
        # + lower(2629) + emit_llvm(1495) + main(81) ≈ 6600+
        assert total >= 5000, f"Total self-hosted lines: {total}"

    @pytest.mark.parametrize(
        "module_name,min_lines",
        [
            ("ast.mn", 200),
            ("lexer.mn", 400),
            ("parser.mn", 700),
            ("semantic.mn", 600),
            ("lower.mn", 1000),
            ("emit_llvm.mn", 1000),
            ("main.mn", 50),
        ],
    )
    def test_module_minimum_size(self, module_name: str, min_lines: int) -> None:
        source = (SELF_DIR / module_name).read_text(encoding="utf-8")
        lines = len(source.strip().split("\n"))
        assert lines >= min_lines, f"{module_name}: {lines} lines (expected >= {min_lines})"
