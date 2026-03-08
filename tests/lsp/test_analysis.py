"""Tests for mapa.lsp.analysis — symbol extraction, hover, go-to-def, find-refs, completion."""

from mapa.lsp.analysis import (
    DocumentAnalysis,
    analyze_document,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

URI = "file:///test.mn"


def _analyze(source: str) -> tuple:
    """Parse + analyze source, return (analysis, errors)."""
    return analyze_document(URI, source)


def _must_analyze(source: str) -> DocumentAnalysis:
    """Analyze source and assert no fatal parse errors; return analysis."""
    analysis, errors = _analyze(source)
    assert analysis is not None, f"parse failed: {errors}"
    return analysis


# ===========================================================================
# Task 1: LSP — hover, go-to definition, find references
# ===========================================================================


class TestSymbolExtraction:
    """Test that symbols are extracted from various AST constructs."""

    def test_fn_def_symbol(self) -> None:
        src = "fn greet(name: String) -> String { return name }"
        a = _must_analyze(src)
        assert "greet" in a.symbols
        assert a.symbols["greet"].kind == "function"
        assert "fn greet" in a.symbols["greet"].detail

    def test_agent_def_symbol(self) -> None:
        src = """
agent Echo {
    input msg: String
    output reply: String

    fn handle(msg: String) -> String {
        return msg
    }
}
"""
        a = _must_analyze(src)
        assert "Echo" in a.symbols
        assert a.symbols["Echo"].kind == "agent"

    def test_struct_def_symbol(self) -> None:
        src = "struct Point { x: Float, y: Float }"
        a = _must_analyze(src)
        assert "Point" in a.symbols
        assert a.symbols["Point"].kind == "struct"
        assert "Point.x" in a.symbols
        assert "Point.y" in a.symbols

    def test_enum_def_symbol(self) -> None:
        src = "enum Color { Red, Green, Blue }"
        a = _must_analyze(src)
        assert "Color" in a.symbols
        assert a.symbols["Color"].kind == "enum"
        assert "Red" in a.symbols
        assert a.symbols["Red"].kind == "enum_variant"

    def test_pipe_def_symbol(self) -> None:
        src = """
fn tokenize(x: String) -> String { return x }
fn parse(x: String) -> String { return x }
pipe Compiler { tokenize |> parse }
"""
        a = _must_analyze(src)
        assert "Compiler" in a.symbols
        assert a.symbols["Compiler"].kind == "pipe"
        assert "tokenize |> parse" in a.symbols["Compiler"].detail

    def test_let_binding_symbol(self) -> None:
        src = """
fn main() {
    let x: Int = 42
    let mut y: String = "hello"
}
"""
        a = _must_analyze(src)
        assert "x" in a.symbols
        assert a.symbols["x"].kind == "variable"
        assert "y" in a.symbols
        assert "mut" in a.symbols["y"].detail

    def test_type_alias_symbol(self) -> None:
        src = "type Age = Int"
        a = _must_analyze(src)
        assert "Age" in a.symbols
        assert a.symbols["Age"].kind == "type_alias"

    def test_impl_methods_extracted(self) -> None:
        src = "struct Foo { x: Int } impl Foo { fn bar() -> Int { return 0 } }"
        a = _must_analyze(src)
        assert "bar" in a.symbols
        assert a.symbols["bar"].kind == "function"

    def test_pub_fn_signature(self) -> None:
        src = "pub fn add(a: Int, b: Int) -> Int { return a }"
        a = _must_analyze(src)
        assert "pub fn add" in a.symbols["add"].detail

    def test_generic_fn_signature(self) -> None:
        src = "fn identity<T>(x: T) -> T { return x }"
        a = _must_analyze(src)
        assert "<T>" in a.symbols["identity"].detail

    def test_export_def_extracts_inner(self) -> None:
        src = "export fn helper() -> Int { return 1 }"
        a = _must_analyze(src)
        assert "helper" in a.symbols

    def test_param_extracted(self) -> None:
        src = "fn foo(bar: Int) -> Int { return bar }"
        a = _must_analyze(src)
        assert "bar" in a.symbols
        assert a.symbols["bar"].kind == "param"


class TestHover:
    """Test hover info at cursor positions."""

    def test_hover_on_fn_name(self) -> None:
        src = "fn greet(name: String) -> String { return name }"
        a = _must_analyze(src)
        # "greet" is at line 0 (0-based), some column
        hover = a.hover_at(0, 3)  # 'g' of 'greet'
        assert hover is not None
        assert "fn greet" in hover

    def test_hover_on_builtin(self) -> None:
        src = """
fn main() {
    print("hello")
}
"""
        a = _must_analyze(src)
        hover = a.hover_at(2, 4)  # 'print'
        assert hover is not None
        assert "print" in hover

    def test_hover_on_primitive_type(self) -> None:
        src = "fn foo(x: Int) -> Int { return x }"
        a = _must_analyze(src)
        hover = a.hover_at(0, 10)  # 'Int'
        assert hover is not None
        assert "Int" in hover

    def test_hover_returns_none_on_empty(self) -> None:
        src = "fn foo() {}"
        a = _must_analyze(src)
        hover = a.hover_at(5, 0)  # out of range
        assert hover is None


class TestGoToDefinition:
    """Test go-to-definition for identifiers."""

    def test_goto_def_fn(self) -> None:
        src = """fn greet() -> Int { return 0 }
fn main() {
    greet()
}
"""
        a = _must_analyze(src)
        # Reference to "greet" is at line 2
        loc = a.definition_at(2, 4)
        assert loc is not None
        assert loc.line == 0  # defined on first line

    def test_goto_def_variable(self) -> None:
        src = """
fn main() {
    let x: Int = 42
    let y: Int = x
}
"""
        a = _must_analyze(src)
        # "x" reference at line 3
        loc = a.definition_at(3, 17)
        assert loc is not None

    def test_goto_def_returns_none_for_unknown(self) -> None:
        src = "fn main() {}"
        a = _must_analyze(src)
        loc = a.definition_at(0, 50)
        assert loc is None


class TestFindReferences:
    """Test find-references for symbols."""

    def test_find_refs_fn(self) -> None:
        src = """fn greet() -> Int { return 0 }
fn main() {
    greet()
}
"""
        a = _must_analyze(src)
        # Find references to "greet"
        refs = a.references_at(0, 3)  # on the definition
        assert len(refs) >= 1  # at least the def itself

    def test_find_refs_variable(self) -> None:
        src = """
fn main() {
    let x: Int = 42
    let y: Int = x
    let z: Int = x
}
"""
        a = _must_analyze(src)
        refs = a.references_at(2, 8)  # on 'x' definition
        assert len(refs) >= 1

    def test_find_refs_empty_for_unknown(self) -> None:
        src = "fn main() {}"
        a = _must_analyze(src)
        refs = a.references_at(0, 50)
        assert refs == []


# ===========================================================================
# Task 2: LSP — real-time diagnostics
# ===========================================================================


class TestDiagnostics:
    """Test that parse and semantic errors are returned as diagnostics."""

    def test_parse_error_returns_diagnostic(self) -> None:
        src = "fn {{"  # invalid syntax
        analysis, errors = _analyze(src)
        assert len(errors) > 0
        assert errors[0].message  # has a message

    def test_semantic_error_undefined_variable(self) -> None:
        src = """
fn main() {
    let x: Int = unknown_var
}
"""
        analysis, errors = _analyze(src)
        # Should have a semantic error for undefined 'unknown_var'
        assert any("unknown_var" in e.message or "undefined" in e.message.lower() for e in errors)

    def test_clean_source_no_errors(self) -> None:
        src = """
fn main() {
    let x: Int = 42
    let y: Int = x
}
"""
        analysis, errors = _analyze(src)
        assert analysis is not None
        assert len(errors) == 0

    def test_error_has_line_and_column(self) -> None:
        src = "fn {{"
        _, errors = _analyze(src)
        assert len(errors) > 0
        assert errors[0].line > 0 or errors[0].column > 0

    def test_multiple_semantic_errors(self) -> None:
        src = """
fn main() {
    let x: Int = a
    let y: Int = b
}
"""
        _, errors = _analyze(src)
        assert len(errors) >= 2  # both 'a' and 'b' are undefined


# ===========================================================================
# Task 3: LSP — autocomplete
# ===========================================================================


class TestCompletion:
    """Test autocompletion candidates."""

    def test_completions_include_defined_fn(self) -> None:
        src = "fn greet() -> Int { return 0 }"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        labels = [i.label for i in items]
        assert "greet" in labels

    def test_completions_include_keywords(self) -> None:
        src = "fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        labels = [i.label for i in items]
        assert "fn" in labels
        assert "let" in labels
        assert "agent" in labels
        assert "match" in labels

    def test_completions_include_builtins(self) -> None:
        src = "fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        labels = [i.label for i in items]
        assert "print" in labels
        assert "println" in labels
        assert "len" in labels

    def test_completions_include_types(self) -> None:
        src = "fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        labels = [i.label for i in items]
        assert "Int" in labels
        assert "String" in labels
        assert "Option" in labels
        assert "Result" in labels

    def test_completions_include_agents(self) -> None:
        src = """
agent Echo {
    input msg: String
    output reply: String

    fn handle(msg: String) -> String {
        return msg
    }
}
fn main() {}
"""
        a = _must_analyze(src)
        items = a.completions_at(9, 0)
        labels = [i.label for i in items]
        assert "Echo" in labels

    def test_completions_include_structs(self) -> None:
        src = "struct Point { x: Float, y: Float } fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 40)
        labels = [i.label for i in items]
        assert "Point" in labels

    def test_completion_item_has_kind(self) -> None:
        src = "fn greet() -> Int { return 0 }"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        fn_item = next(i for i in items if i.label == "greet")
        assert fn_item.kind == "function"

    def test_completion_item_has_detail(self) -> None:
        src = "fn greet() -> Int { return 0 }"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        fn_item = next(i for i in items if i.label == "greet")
        assert "fn greet" in fn_item.detail


# ===========================================================================
# LSP Server integration (basic smoke tests)
# ===========================================================================


class TestLSPServer:
    """Basic smoke tests for the LSP server module."""

    def test_server_importable(self) -> None:
        from mapa.lsp.server import server

        assert server is not None
        assert server.name == "mapanare-lsp"

    def test_completion_kind_mapping(self) -> None:
        from lsprotocol import types as lsp

        from mapa.lsp.server import _map_completion_kind

        assert _map_completion_kind("function") == lsp.CompletionItemKind.Function
        assert _map_completion_kind("variable") == lsp.CompletionItemKind.Variable
        assert _map_completion_kind("keyword") == lsp.CompletionItemKind.Keyword
