"""Tests verifying doc/code consistency (Phase 3.4).

These tests ensure the README feature status table and SPEC.md claims
match what the compiler actually supports.
"""

from __future__ import annotations

import pathlib
import textwrap

from mapanare.parser import parse

ROOT = pathlib.Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _parses(source: str) -> bool:
    """Check that Mapanare source parses successfully."""
    try:
        parse(source, filename="<test>")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Task 1: Feature status table entries match reality
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Task 3: Maps/Dicts exist (were listed as 'Planned')
# ---------------------------------------------------------------------------


class TestMapsExist:
    """Verify Dictionaries/Maps are implemented (was listed as 'Planned')."""

    def test_map_literal_parses(self) -> None:
        """Map literal syntax parses (uses #{ } syntax)."""
        assert _parses('let m = #{"a": 1, "b": 2}')

    def test_map_literal_compiles(self) -> None:
        """Map literal compiles (parser + semantic)."""
        from mapanare.semantic import check_or_raise

        source = textwrap.dedent("""\
            fn main() {
                let m = #{"a": 1, "b": 2}
            }
        """)
        ast = parse(source, filename="<test>")
        check_or_raise(ast, filename="<test>")

    def test_map_in_ast_nodes(self) -> None:
        """MapLiteral and MapEntry exist in AST."""
        from mapanare.ast_nodes import MapEntry, MapLiteral

        assert MapLiteral is not None
        assert MapEntry is not None

    def test_map_in_grammar(self) -> None:
        """map_lit rule exists in grammar."""
        grammar_path = ROOT / "mapanare" / "mapanare.lark"
        grammar = grammar_path.read_text(encoding="utf-8")
        assert "map_lit" in grammar


# ---------------------------------------------------------------------------
# Task 4: SPEC.md claims verified
# ---------------------------------------------------------------------------


class TestSpecAccuracy:
    """Verify key SPEC.md claims are accurate."""

    def test_traits_in_grammar(self) -> None:
        """trait and impl Trait for Type are in grammar."""
        assert _parses(textwrap.dedent("""\
            trait Greetable {
                fn greet(self) -> String
            }
        """))

    def test_impl_trait_parses(self) -> None:
        """impl Trait for Type syntax parses."""
        assert _parses(textwrap.dedent("""\
            struct Dog { name: String }
            trait Greetable {
                fn greet(self) -> String
            }
            impl Greetable for Dog {
                fn greet(self) -> String { return "woof" }
            }
        """))

    def test_import_parses(self) -> None:
        """import syntax parses (module system is implemented)."""
        assert _parses("import std::math")

    def test_pub_visibility_parses(self) -> None:
        """pub visibility modifier parses."""
        assert _parses("pub fn add(a: Int, b: Int) -> Int { return a + b }")

    def test_char_literal_parses(self) -> None:
        """Char literal exists in grammar (listed in SPEC type table)."""
        assert _parses("let c = 'a'")

    def test_map_type_in_spec(self) -> None:
        """Map<K, V> type listed in SPEC — grammar supports map literals."""
        assert _parses('let m = #{"key": 42}')


# ---------------------------------------------------------------------------
# Task 5: No stale aspirational claims remain
# ---------------------------------------------------------------------------


class TestNoStaleAspirations:
    """Verify aspirational claims have been removed or labeled."""

    def test_no_ownership_based_in_spec(self) -> None:
        """'ownership-based' wording removed from SPEC (done in Phase 1.1)."""
        spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "ownership-based" not in spec.lower()

    def test_spec_documents_string_interpolation(self) -> None:
        """SPEC documents string interpolation as implemented (v0.5.0+)."""
        spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "${expr}" in spec or "string interpolation" in spec.lower()

    def test_readme_repl_not_planned(self) -> None:
        """README no longer says REPL is 'Planned'."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "REPL" in line and "interactive" in line:
                assert "Planned" not in line, "REPL should not be listed as Planned"
                assert "Yes" in line or "Experimental" in line
                break

    def test_readme_maps_not_planned(self) -> None:
        """README no longer says Dictionaries/Maps is 'Planned'."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "Dictionaries/Maps" in line:
                assert "Planned" not in line, "Maps should not be listed as Planned"
                assert "Stable" in line
                break

    def test_readme_agents_llvm_not_no(self) -> None:
        """README no longer says Agents LLVM is 'No'."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "Agents" in line and "spawn" in line:
                assert "| No |" not in line, "Agents LLVM should not be listed as No"
                break

    def test_readme_roadmap_phase1_complete(self) -> None:
        """README roadmap table shows Phase 1 as Complete."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "Foundation Fixes" in line:
                assert "Complete" in line, "Phase 1 should show Complete"
                break

    def test_readme_roadmap_phase2_complete(self) -> None:
        """README roadmap table shows Phase 2 as Complete."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "Three Pillars" in line:
                assert "Complete" in line, "Phase 2 should show Complete"
                break

    def test_readme_gpu_section_labeled_experimental(self) -> None:
        """README GPU & Tensors section is labeled as experimental."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for line in readme.splitlines():
            if "GPU & Tensors" in line:
                assert "Experimental" in line or "Planned" in line
                break

    def test_spec_grammar_includes_traits(self) -> None:
        """SPEC grammar summary includes trait_def."""
        spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "trait_def" in spec

    def test_spec_appendix_c_modules_implemented(self) -> None:
        """SPEC documents the module system (was Appendix C, now Section 8)."""
        spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "Module System" in spec
