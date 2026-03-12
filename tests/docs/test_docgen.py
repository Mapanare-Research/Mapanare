"""Tests for doc comment parsing and HTML doc generation."""

import pytest

from mapanare.ast_nodes import DocComment, FnDef
from mapanare.docgen import extract_doc_items, generate_html
from mapanare.parser import parse


class TestDocCommentParsing:
    """Test that /// doc comments are parsed into DocComment AST nodes."""

    def test_doc_comment_on_function(self):
        source = '/// Adds two numbers.\nfn add(a: Int, b: Int) -> Int {\n    return a + b\n}'
        ast = parse(source, filename="test.mn")
        assert len(ast.definitions) == 1
        defn = ast.definitions[0]
        assert isinstance(defn, DocComment)
        assert defn.text == "Adds two numbers."
        assert isinstance(defn.definition, FnDef)
        assert defn.definition.name == "add"

    def test_multiline_doc_comment(self):
        source = '/// First line.\n/// Second line.\nfn foo() -> Int {\n    return 1\n}'
        ast = parse(source, filename="test.mn")
        defn = ast.definitions[0]
        assert isinstance(defn, DocComment)
        assert "First line." in defn.text
        assert "Second line." in defn.text

    def test_doc_comment_on_struct(self):
        source = '/// A 2D point.\nstruct Point {\n    x: Float,\n    y: Float,\n}'
        ast = parse(source, filename="test.mn")
        defn = ast.definitions[0]
        assert isinstance(defn, DocComment)
        assert defn.text == "A 2D point."

    def test_no_doc_comment_regular_function(self):
        source = 'fn add(a: Int, b: Int) -> Int {\n    return a + b\n}'
        ast = parse(source, filename="test.mn")
        assert len(ast.definitions) == 1
        assert isinstance(ast.definitions[0], FnDef)

    def test_regular_comment_ignored(self):
        source = '// Just a regular comment\nfn foo() -> Int {\n    return 1\n}'
        ast = parse(source, filename="test.mn")
        assert len(ast.definitions) == 1
        assert isinstance(ast.definitions[0], FnDef)

    def test_doc_comment_semantic_check(self):
        """Doc-commented definitions should pass semantic analysis."""
        from mapanare.semantic import check

        source = '/// Documented function.\nfn greet(name: String) -> String {\n    return name\n}'
        ast = parse(source, filename="test.mn")
        errors = check(ast, filename="test.mn")
        assert len(errors) == 0

    def test_doc_comment_python_emit(self):
        """Doc-commented definitions should emit valid Python."""
        from mapanare.emit_python import PythonEmitter
        from mapanare.semantic import check_or_raise

        source = '/// Adds two ints.\nfn add(a: Int, b: Int) -> Int {\n    return a + b\n}'
        ast = parse(source, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "def add(" in code


class TestDocGenerator:
    """Test HTML doc generation from doc items."""

    def test_extract_doc_items(self):
        source = '/// Adds two numbers.\nfn add(a: Int, b: Int) -> Int {\n    return a + b\n}'
        ast = parse(source, filename="test.mn")
        items = extract_doc_items(ast)
        assert len(items) == 1
        assert items[0].name == "add"
        assert items[0].kind == "function"
        assert items[0].doc == "Adds two numbers."

    def test_generate_html(self):
        source = '/// A helper function.\npub fn helper() -> Int {\n    return 42\n}'
        ast = parse(source, filename="test.mn")
        items = extract_doc_items(ast)
        html = generate_html(items, module_name="test")
        assert "<title>test" in html
        assert "helper" in html
        assert "A helper function." in html

    def test_empty_program_generates_html(self):
        source = 'fn main() {\n    println("hello")\n}'
        ast = parse(source, filename="test.mn")
        items = extract_doc_items(ast)
        html = generate_html(items, module_name="test")
        assert "<html" in html

    def test_extract_struct_doc(self):
        source = '/// A 2D point.\nstruct Point {\n    x: Float,\n    y: Float,\n}'
        ast = parse(source, filename="test.mn")
        items = extract_doc_items(ast)
        assert len(items) == 1
        assert items[0].kind == "struct"
        assert "Point" in items[0].signature

    def test_extract_enum_doc(self):
        source = '/// Represents a color.\nenum Color {\n    Red,\n    Green,\n    Blue,\n}'
        ast = parse(source, filename="test.mn")
        items = extract_doc_items(ast)
        assert len(items) == 1
        assert items[0].kind == "enum"


class TestDocCLI:
    """Test the mapanare doc CLI command."""

    def test_doc_subparser_exists(self):
        from mapanare.cli import build_parser

        parser = build_parser()
        # Should not raise
        args = parser.parse_args(["doc", "test.mn"])
        assert args.command == "doc"
        assert args.source == "test.mn"
