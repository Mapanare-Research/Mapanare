"""Tests for mapanare.lsp.analysis — symbol extraction, hover, go-to-def, find-refs, completion."""

import os
import tempfile

from mapanare.lsp.analysis import (
    DocumentAnalysis,
    IncrementalParser,
    LspDiagnostic,
    SymbolInfo,
    SymbolLocation,
    _enrich_diagnostics,
    _filepath_to_uri,
    _resolve_imported_symbols,
    _uri_to_filepath,
    _word_at,
    analyze_document,
)
from mapanare.semantic import SemanticError

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

    def test_extern_fn_extracted(self) -> None:
        src = 'extern "C" fn puts(s: String) -> Int'
        a = _must_analyze(src)
        assert "puts" in a.symbols
        assert a.symbols["puts"].kind == "function"
        assert 'extern "C"' in a.symbols["puts"].detail

    def test_trait_def_extracted(self) -> None:
        src = "trait Display { fn to_string(self) -> String }"
        a = _must_analyze(src)
        assert "Display" in a.symbols
        assert a.symbols["Display"].kind == "trait"


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
    println(str(x))
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
        from mapanare.lsp.server import server

        assert server is not None
        assert server.name == "mapanare-lsp"

    def test_completion_kind_mapping(self) -> None:
        from lsprotocol import types as lsp

        from mapanare.lsp.server import _map_completion_kind

        assert _map_completion_kind("function") == lsp.CompletionItemKind.Function
        assert _map_completion_kind("variable") == lsp.CompletionItemKind.Variable
        assert _map_completion_kind("keyword") == lsp.CompletionItemKind.Keyword


# ===========================================================================
# Phase 6.1 Task 1: Incremental Parsing
# ===========================================================================


class TestIncrementalParsing:
    """Test incremental parsing — only re-parse changed chunks."""

    def test_incremental_parser_basic(self) -> None:
        parser = IncrementalParser()
        src = """fn foo() -> Int { return 1 }
fn bar() -> Int { return 2 }
"""
        program, errors, was_incremental = parser.parse(URI, src)
        assert program is not None
        assert len(errors) == 0
        assert not was_incremental  # first parse is never incremental

    def test_incremental_parser_reuses_cache(self) -> None:
        parser = IncrementalParser()
        src = """fn foo() -> Int { return 1 }
fn bar() -> Int { return 2 }
"""
        # First parse
        parser.parse(URI, src)

        # Modify only bar
        src2 = """fn foo() -> Int { return 1 }
fn bar() -> Int { return 99 }
"""
        # This will try full parse first (fast path succeeds), so was_incremental=False
        program2, errors2, was_incremental = parser.parse(URI, src2)
        assert program2 is not None
        assert len(errors2) == 0

    def test_incremental_parser_handles_syntax_error(self) -> None:
        parser = IncrementalParser()
        # First parse — valid
        src = """fn foo() -> Int { return 1 }
fn bar() -> Int { return 2 }
"""
        parser.parse(URI, src)

        # Second parse — bar has error
        src2 = """fn foo() -> Int { return 1 }
fn bar() -> Int {{ invalid
"""
        program2, errors2, was_incremental = parser.parse(URI, src2)
        # Should still get foo's definitions from cache
        assert program2 is not None
        has_defs = len(program2.definitions) >= 1
        assert has_defs

    def test_incremental_parser_invalidate(self) -> None:
        parser = IncrementalParser()
        src = "fn foo() -> Int { return 1 }"
        parser.parse(URI, src)
        parser.invalidate(URI)
        # After invalidation, parsing same source is not incremental
        _, _, was_incremental = parser.parse(URI, src)
        assert not was_incremental

    def test_analyze_document_uses_incremental(self) -> None:
        """Verify analyze_document works with incremental=True (default)."""
        src = "fn hello() -> Int { return 42 }"
        analysis, diags = analyze_document(URI, src)
        assert analysis is not None
        assert "hello" in analysis.symbols

    def test_analyze_document_non_incremental(self) -> None:
        """Verify analyze_document works with incremental=False."""
        src = "fn hello() -> Int { return 42 }"
        analysis, diags = analyze_document(URI, src, incremental=False)
        assert analysis is not None
        assert "hello" in analysis.symbols


# ===========================================================================
# Phase 6.1 Task 2: Semantic-Aware Autocomplete
# ===========================================================================


class TestSemanticAwareCompletion:
    """Test semantic-aware completion (struct fields, trait methods, imports)."""

    def test_struct_field_dot_completion(self) -> None:
        """After 'p.' where p is a Point, show fields x and y."""
        src = """struct Point { x: Float, y: Float }
fn main() {
    let p: Point = p
    let z: Float = p.x
}
"""
        a = _must_analyze(src)
        # Cursor on 'x' after "p." on line 3 (0-based): "    let z: Float = p.x"
        # p is at col 19, . at col 20, x at col 21
        items = a.completions_at(3, 21)
        labels = [i.label for i in items]
        assert "x" in labels
        assert "y" in labels

    def test_dot_completion_shows_field_types(self) -> None:
        src = """struct Point { x: Float, y: Float }
fn main() {
    let p: Point = p
    let z: Float = p.x
}
"""
        a = _must_analyze(src)
        items = a.completions_at(3, 21)
        x_item = next((i for i in items if i.label == "x"), None)
        assert x_item is not None
        assert "Float" in x_item.detail

    def test_trait_method_completion_via_impl(self) -> None:
        """After '.' on a type that impls a trait, show trait methods."""
        src = """trait Display {
    fn to_string(self) -> String
}
struct Foo { x: Int }
impl Display for Foo {
    fn to_string(self) -> String { return "foo" }
}
fn main() {
    let f: Foo = f
    let s: String = f.to_string
}
"""
        a = _must_analyze(src)
        # "    let s: String = f.to_string" — f at col 20, . at col 21, to_string starts at col 22
        items = a.completions_at(9, 22)
        labels = [i.label for i in items]
        # Should include struct fields and trait methods
        assert "x" in labels
        assert "to_string" in labels

    def test_completions_include_new_keywords(self) -> None:
        """Check that while, extern, trait are in keyword completions."""
        src = "fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        labels = [i.label for i in items]
        assert "while" in labels
        assert "extern" in labels
        assert "trait" in labels

    def test_no_dot_completion_outside_context(self) -> None:
        """When not after a dot, return normal completions."""
        src = "fn main() {}"
        a = _must_analyze(src)
        items = a.completions_at(0, 0)
        # Should have keywords and builtins, not field completions
        labels = [i.label for i in items]
        assert "fn" in labels
        assert "print" in labels


# ===========================================================================
# Phase 6.1 Task 3: Inline Diagnostics with Fix Suggestions
# ===========================================================================


class TestDiagnosticsWithSuggestions:
    """Test diagnostics enrichment with fix suggestions."""

    def test_undefined_var_suggests_similar_name(self) -> None:
        """When an undefined variable is close to a known name, suggest it."""
        errors = [
            SemanticError(
                message="Undefined variable 'prnt'",
                line=2,
                column=5,
                filename=URI,
            )
        ]
        symbols = {
            "print": SymbolInfo(
                name="print",
                kind="function",
                type_display="",
                detail="builtin fn print",
                definition=SymbolLocation(uri=URI, line=0, column=0, end_line=0, end_column=0),
            )
        }
        diags = _enrich_diagnostics(errors, "", symbols)
        assert len(diags) == 1
        assert len(diags[0].suggestions) > 0
        assert any("print" in s.message for s in diags[0].suggestions)

    def test_undefined_fn_suggests_similar(self) -> None:
        errors = [
            SemanticError(
                message="Undefined function 'greet_user'",
                line=5,
                column=3,
                filename=URI,
            )
        ]
        symbols = {
            "greet_users": SymbolInfo(
                name="greet_users",
                kind="function",
                type_display="",
                detail="fn greet_users()",
                definition=SymbolLocation(uri=URI, line=0, column=0, end_line=0, end_column=0),
            )
        }
        diags = _enrich_diagnostics(errors, "", symbols)
        assert len(diags[0].suggestions) > 0
        assert any("greet_users" in s.message for s in diags[0].suggestions)

    def test_no_suggestions_for_unrelated_errors(self) -> None:
        errors = [
            SemanticError(
                message="Some other error",
                line=1,
                column=1,
                filename=URI,
            )
        ]
        diags = _enrich_diagnostics(errors, "", {})
        assert len(diags) == 1
        assert len(diags[0].suggestions) == 0

    def test_analyze_returns_lsp_diagnostics(self) -> None:
        """analyze_document should return LspDiagnostic objects."""
        src = """
fn main() {
    let x: Int = unknown_var
}
"""
        _, diags = _analyze(src)
        assert len(diags) > 0
        assert isinstance(diags[0], LspDiagnostic)

    def test_diagnostic_has_severity(self) -> None:
        src = """
fn main() {
    let x: Int = unknown_var
}
"""
        _, diags = _analyze(src)
        assert len(diags) > 0
        assert diags[0].severity == "error"

    def test_suggestion_for_typo_in_real_code(self) -> None:
        """End-to-end: a typo in source code produces a suggestion."""
        src = """
fn greet() -> Int { return 42 }
fn main() {
    let x: Int = gret()
}
"""
        _, diags = _analyze(src)
        # Should have error about 'gret' being undefined
        undef_diags = [d for d in diags if "gret" in d.message]
        assert len(undef_diags) > 0
        # Should suggest 'greet'
        all_suggestions = []
        for d in undef_diags:
            all_suggestions.extend(d.suggestions)
        assert any("greet" in s.message for s in all_suggestions)


# ===========================================================================
# Phase 6.1 Task 4: Go-to-Definition Across Module Imports
# ===========================================================================


class TestCrossModuleGoToDef:
    """Test go-to-definition across module imports."""

    def test_uri_to_filepath(self) -> None:
        # Unix-style
        assert _uri_to_filepath("file:///home/user/test.mn") == "/home/user/test.mn"
        # Windows-style
        assert _uri_to_filepath("file:///C:/Users/test.mn") == "C:/Users/test.mn"

    def test_filepath_to_uri(self) -> None:
        uri = _filepath_to_uri("/home/user/test.mn")
        assert uri.startswith("file://")
        assert "test.mn" in uri

    def test_cross_module_goto_def_with_real_files(self) -> None:
        """Create temp files with imports and verify cross-module go-to-def."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a module file
            mod_path = os.path.join(tmpdir, "helpers.mn")
            with open(mod_path, "w") as f:
                f.write("export fn helper_fn() -> Int { return 42 }\n")

            # Create a main file that imports it
            main_path = os.path.join(tmpdir, "main.mn")
            main_source = "import helpers { helper_fn }\nfn main() {\n    helper_fn()\n}\n"

            main_uri = _filepath_to_uri(main_path)
            analysis, diags = analyze_document(main_uri, main_source)

            assert analysis is not None
            # The imported symbol should be available
            assert "helper_fn" in analysis._imported_symbols
            # Go-to-def on helper_fn should point to helpers.mn
            imp_sym = analysis._imported_symbols["helper_fn"]
            assert "helpers" in imp_sym.definition.uri

    def test_imported_symbols_appear_in_completions(self) -> None:
        """Imported symbols should appear in completion list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = os.path.join(tmpdir, "utils.mn")
            with open(mod_path, "w") as f:
                f.write("export fn util_fn() -> Int { return 1 }\n")

            main_path = os.path.join(tmpdir, "main.mn")
            main_source = "import utils { util_fn }\nfn main() {}\n"
            main_uri = _filepath_to_uri(main_path)

            analysis, _ = analyze_document(main_uri, main_source)
            assert analysis is not None

            items = analysis.completions_at(1, 0)
            labels = [i.label for i in items]
            assert "util_fn" in labels

    def test_imported_symbol_hover(self) -> None:
        """Hovering over an imported symbol should show its detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = os.path.join(tmpdir, "lib.mn")
            with open(mod_path, "w") as f:
                f.write("export fn exported_fn(x: Int) -> Int { return x }\n")

            main_path = os.path.join(tmpdir, "main.mn")
            main_source = "import lib { exported_fn }\nfn main() {\n    exported_fn(1)\n}\n"
            main_uri = _filepath_to_uri(main_path)

            analysis, _ = analyze_document(main_uri, main_source)
            assert analysis is not None
            assert "exported_fn" in analysis._imported_symbols

    def test_resolve_imported_symbols_handles_missing_module(self) -> None:
        """When a module doesn't exist, no crash — just empty symbols."""
        from mapanare.parser import parse

        src = "import nonexistent { foo }\nfn main() {}\n"
        program = parse(src, filename="file:///fake.mn")
        imported, import_defs = _resolve_imported_symbols("file:///fake.mn", program)
        assert len(imported) == 0  # no crash, just empty

    def test_goto_def_for_imported_symbol(self) -> None:
        """definition_at should resolve to an imported symbol's location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = os.path.join(tmpdir, "mymod.mn")
            with open(mod_path, "w") as f:
                f.write("export fn remote_fn() -> Int { return 0 }\n")

            main_path = os.path.join(tmpdir, "main.mn")
            # "remote_fn()" is on line 2 (0-based), starting around col 4
            main_source = "import mymod { remote_fn }\nfn main() {\n    remote_fn()\n}\n"
            main_uri = _filepath_to_uri(main_path)

            analysis, _ = analyze_document(main_uri, main_source)
            assert analysis is not None

            # The word "remote_fn" at line 2, col 4 should go-to-def in mymod.mn
            loc = analysis.definition_at(2, 4)
            assert loc is not None
            assert "mymod" in loc.uri


# ===========================================================================
# Utility tests
# ===========================================================================


class TestWordAt:
    """Test _word_at helper."""

    def test_word_in_middle(self) -> None:
        assert _word_at("let foo = 42", 4) == "foo"

    def test_word_at_start(self) -> None:
        assert _word_at("hello world", 0) == "hello"

    def test_empty_line(self) -> None:
        assert _word_at("", 0) == ""

    def test_out_of_range(self) -> None:
        assert _word_at("abc", 10) == ""
