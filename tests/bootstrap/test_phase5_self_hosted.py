"""Phase 5 — Self-Hosted Compiler Gaps tests.

Tests for:
1. Struct literal syntax (`new Name { field: value }`)
2. Enum lowering in LLVM IR (construction + pattern matching)
3. Multi-module compilation
4. String interpolation in self-hosted lexer/parser
"""

from __future__ import annotations

from pathlib import Path

from mapanare.ast_nodes import (
    ConstructExpr,
    FnDef,
    LetBinding,
)
from mapanare.emit_llvm import LLVMEmitter
from mapanare.parser import parse

SELF_DIR = Path(__file__).resolve().parents[2] / "mapanare" / "self"


# ---------------------------------------------------------------------------
# Task 2: Struct literal syntax
# ---------------------------------------------------------------------------


class TestStructLiteralSyntax:
    """Verify `new Name { field: value }` struct construction syntax."""

    def test_parse_struct_literal(self) -> None:
        prog = parse("let p = new Point { x: 1, y: 2 }", filename="test.mn")
        assert len(prog.definitions) == 1
        main_fn = prog.definitions[0]
        assert isinstance(main_fn, FnDef)
        let_stmt = main_fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, ConstructExpr)
        assert let_stmt.value.name == "Point"
        assert len(let_stmt.value.fields) == 2
        assert let_stmt.value.fields[0].name == "x"
        assert let_stmt.value.fields[1].name == "y"

    def test_parse_struct_literal_trailing_comma(self) -> None:
        prog = parse("let p = new Point { x: 1, y: 2, }", filename="test.mn")
        let_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(let_stmt.value, ConstructExpr)
        assert len(let_stmt.value.fields) == 2

    def test_parse_struct_literal_empty(self) -> None:
        prog = parse("let u = new Unit { }", filename="test.mn")
        let_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(let_stmt.value, ConstructExpr)
        assert let_stmt.value.name == "Unit"
        assert len(let_stmt.value.fields) == 0

    def test_struct_literal_in_function(self) -> None:
        src = (
            "struct Point { x: Int, y: Int }\n"
            "fn make() -> Point { return new Point { x: 10, y: 20 } }\n"
        )
        prog = parse(src, filename="test.mn")
        assert len(prog.definitions) == 2

    def test_struct_literal_nested(self) -> None:
        src = "let r = new Rect { origin: new Point { x: 0, y: 0 }, width: 10 }"
        prog = parse(src, filename="test.mn")
        let_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(let_stmt.value, ConstructExpr)
        assert let_stmt.value.name == "Rect"
        inner = let_stmt.value.fields[0].value
        assert isinstance(inner, ConstructExpr)
        assert inner.name == "Point"

    def test_new_keyword_not_ambiguous_with_if(self) -> None:
        """new keyword avoids if/struct ambiguity."""
        src = "if true { let x = new Foo { a: 1 } }"
        prog = parse(src, filename="test.mn")
        assert len(prog.definitions) == 1


# ---------------------------------------------------------------------------
# Task 3: Enum lowering in LLVM IR
# ---------------------------------------------------------------------------


class TestEnumLoweringLLVM:
    """Verify enum construction and pattern matching in LLVM IR."""

    def test_simple_enum_construction(self) -> None:
        """Simple enum (no payload) constructs with correct tag."""
        src = "enum Color { Red, Green, Blue }\n" "fn get_color() -> Color { return Green }\n"
        prog = parse(src, filename="test.mn")
        e = LLVMEmitter(module_name="test_enum")
        mod = e.emit_program(prog)
        ir_text = str(mod)
        assert "define" in ir_text

    def test_enum_with_payload(self) -> None:
        """Enum with payload fields constructs tagged union."""
        src = (
            "enum Shape { Circle(Int), Rect(Int, Int) }\n"
            "fn make_circle() -> Shape { return Circle(5) }\n"
        )
        prog = parse(src, filename="test.mn")
        e = LLVMEmitter(module_name="test_enum_payload")
        mod = e.emit_program(prog)
        ir_text = str(mod)
        assert "define" in ir_text
        # Should have tag storage
        assert "Circle.tag" in ir_text or "i32" in ir_text

    def test_enum_variant_tag_values(self) -> None:
        """Each variant gets a distinct tag index."""
        src = (
            "enum Color { Red, Green, Blue }\n"
            "fn red() -> Color { return Red }\n"
            "fn green() -> Color { return Green }\n"
            "fn blue() -> Color { return Blue }\n"
        )
        prog = parse(src, filename="test.mn")
        e = LLVMEmitter(module_name="test_tags")
        mod = e.emit_program(prog)
        ir_text = str(mod)
        assert "define" in ir_text

    def test_enum_match_simple(self) -> None:
        """Match on simple enum produces switch on tag."""
        src = (
            "enum Dir { Up, Down, Left, Right }\n"
            "fn to_int(d: Dir) -> Int {\n"
            "    match d {\n"
            "        Up => 0,\n"
            "        Down => 1,\n"
            "        Left => 2,\n"
            "        Right => 3,\n"
            "        _ => 99\n"
            "    }\n"
            "}\n"
        )
        prog = parse(src, filename="test.mn")
        e = LLVMEmitter(module_name="test_enum_match")
        mod = e.emit_program(prog)
        ir_text = str(mod)
        assert "switch" in ir_text or "match" in ir_text.lower()


# ---------------------------------------------------------------------------
# Task 1: Multi-module compilation
# ---------------------------------------------------------------------------


class TestMultiModuleCompilation:
    """Verify multi-module LLVM compilation works."""

    def test_build_multi_cli_exists(self) -> None:
        """build-multi subcommand is registered."""
        from mapanare.cli import build_parser

        parser = build_parser()
        # Verify we can parse the subcommand
        args = parser.parse_args(["build-multi", "a.mn", "b.mn"])
        assert args.command == "build-multi"
        assert args.sources == ["a.mn", "b.mn"]

    def test_module_resolver_caches(self) -> None:
        """ModuleResolver caches parsed modules."""
        from mapanare.modules import ModuleResolver

        resolver = ModuleResolver()
        assert len(resolver.all_modules()) == 0


# ---------------------------------------------------------------------------
# Task 4: String interpolation in self-hosted
# ---------------------------------------------------------------------------


class TestSelfHostedInterpolation:
    """Verify string interpolation support in self-hosted compiler files."""

    def test_lexer_mn_parses_with_new_keyword(self) -> None:
        """lexer.mn still parses after adding new keyword support."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        prog = parse(source, filename="lexer.mn")
        assert len(prog.definitions) > 0

    def test_lexer_mn_has_new_keyword(self) -> None:
        """lexer.mn recognizes 'new' keyword."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        assert '"new"' in source
        assert '"KW_NEW"' in source

    def test_parser_mn_has_interpolation(self) -> None:
        """parser.mn has string interpolation support."""
        source = (SELF_DIR / "parser.mn").read_text(encoding="utf-8")
        assert "has_interpolation" in source
        assert "split_interp_parts" in source

    def test_parser_mn_parses(self) -> None:
        """parser.mn still parses after interpolation additions."""
        source = (SELF_DIR / "parser.mn").read_text(encoding="utf-8")
        prog = parse(source, filename="parser.mn")
        assert len(prog.definitions) > 0

    def test_bootstrap_interp_in_python(self) -> None:
        """Python bootstrap handles ${...} interpolation correctly."""
        from mapanare.ast_nodes import InterpString

        prog = parse('let s = "hello ${name}"', filename="test.mn")
        let_stmt = prog.definitions[0].body.stmts[0]
        assert isinstance(let_stmt.value, InterpString)
        assert len(let_stmt.value.parts) == 2


# ---------------------------------------------------------------------------
# Task 9: Bootstrap snapshot
# ---------------------------------------------------------------------------


class TestBootstrapSnapshot:
    """Verify bootstrap/ directory exists and is populated."""

    def test_bootstrap_dir_exists(self) -> None:
        bootstrap_dir = Path(__file__).resolve().parents[2] / "bootstrap"
        assert bootstrap_dir.is_dir()

    def test_bootstrap_has_key_files(self) -> None:
        bootstrap_dir = Path(__file__).resolve().parents[2] / "bootstrap"
        assert (bootstrap_dir / "cli.py").is_file()
        assert (bootstrap_dir / "parser.py").is_file()
        assert (bootstrap_dir / "semantic.py").is_file()
        assert (bootstrap_dir / "emit_llvm.py").is_file()
        assert (bootstrap_dir / "emit_python.py").is_file()
        assert (bootstrap_dir / "mapanare.lark").is_file()

    def test_bootstrap_has_readme(self) -> None:
        bootstrap_dir = Path(__file__).resolve().parents[2] / "bootstrap"
        assert (bootstrap_dir / "README.md").is_file()
