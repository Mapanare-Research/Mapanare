"""Tests verifying doc/code consistency (Phase 3.4).

These tests ensure the README feature status table and SPEC.md claims
match what the compiler actually supports.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import textwrap

from mapanare.cli import _compile_source, cmd_repl
from mapanare.parser import parse

ROOT = pathlib.Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _compiles_to_python(source: str) -> str:
    """Compile Mapanare source to Python, return Python code."""
    return _compile_source(source, "<test>")


def _compiles_and_runs(source: str) -> str:
    """Compile and run, returning stdout."""
    python_code = _compile_source(source, "<test>")
    result = subprocess.run(
        [sys.executable, "-c", python_code],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Runtime error: {result.stderr}"
    return result.stdout.strip()


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


class TestFeatureTableAccuracy:
    """Verify every entry in README feature status table is accurate."""

    def test_functions_closures_lambdas(self) -> None:
        """Functions, closures, lambdas: Yes/Yes/Stable."""
        out = _compiles_and_runs(textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int { return a + b }
            fn main() {
                let f = (x) => x * 2
                print(add(1, 2))
                print(f(5))
            }
        """))
        assert "3" in out
        assert "10" in out

    def test_structs_enums_match(self) -> None:
        """Structs, enums, pattern matching: Yes/Yes/Stable."""
        out = _compiles_and_runs(textwrap.dedent("""\
            enum Shape {
                Circle(Float),
                Rect(Float, Float)
            }

            fn main() {
                let s = Shape_Circle(3.0)
                match s {
                    Shape_Circle(r) => { print("circle") },
                    Shape_Rect(w, h) => { print("rect") },
                    _ => { print("other") }
                }
            }
        """))
        assert "circle" in out

    def test_control_flow(self) -> None:
        """if/else, for..in, while: Yes/Yes/Stable."""
        out = _compiles_and_runs(textwrap.dedent("""\
            fn main() {
                if true { print("yes") } else { print("no") }
                for i in 0..3 { print(str(i)) }
                let mut c = 0
                while c < 2 { c += 1 }
                print(str(c))
            }
        """))
        assert "yes" in out
        assert "2" in out

    def test_result_option(self) -> None:
        """Result/Option + ? operator: Yes/Partial/Stable."""
        out = _compiles_and_runs(textwrap.dedent("""\
            fn main() {
                let x: Option<Int> = Some(42)
                match x {
                    Some(v) => { print(str(v)) },
                    None => { print("none") }
                }
            }
        """))
        assert "42" in out

    def test_lists(self) -> None:
        """Lists: Yes/Partial/Stable."""
        out = _compiles_and_runs(textwrap.dedent("""\
            fn main() {
                let mut items: List<Int> = []
                items.push(1)
                items.push(2)
                print(str(items.length()))
                print(str(items[0]))
            }
        """))
        assert "2" in out
        assert "1" in out


# ---------------------------------------------------------------------------
# Task 2: REPL exists and is functional
# ---------------------------------------------------------------------------


class TestREPLExists:
    """Verify REPL is implemented (was listed as 'Planned')."""

    def test_repl_command_exists(self) -> None:
        """cmd_repl function exists in cli.py."""
        assert callable(cmd_repl)

    def test_repl_registered_in_argparser(self) -> None:
        """'repl' subcommand is registered in the CLI."""
        from mapanare.cli import build_parser

        parser = build_parser()
        assert "repl" in parser._subparsers._group_actions[0].choices


# ---------------------------------------------------------------------------
# Task 3: Maps/Dicts exist (were listed as 'Planned')
# ---------------------------------------------------------------------------


class TestMapsExist:
    """Verify Dictionaries/Maps are implemented (was listed as 'Planned')."""

    def test_map_literal_parses(self) -> None:
        """Map literal syntax parses (uses #{ } syntax)."""
        assert _parses('let m = #{"a": 1, "b": 2}')

    def test_map_literal_compiles(self) -> None:
        """Map literal compiles to Python."""
        code = _compiles_to_python(textwrap.dedent("""\
            fn main() {
                let m = #{"a": 1, "b": 2}
            }
        """))
        assert "m" in code

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
        """SPEC Appendix C notes module system is implemented."""
        spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "RFC 0003" in spec
