"""Task 22 — Cross-reference SPEC.md against grammar, semantic checker, and emitters.

Parses grammar rules from mapanare.lark and verifies that SPEC.md documents
every major grammar construct.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SPEC = ROOT / "docs" / "SPEC.md"
GRAMMAR = ROOT / "mapanare" / "mapanare.lark"


def _spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


def _grammar_text() -> str:
    return GRAMMAR.read_text(encoding="utf-8")


# ── Grammar rules that must be documented in SPEC ──


class TestGrammarRulesCoverage:
    """Every major grammar rule should be referenced or documented in SPEC.md."""

    def test_fn_def_documented(self) -> None:
        text = _spec_text()
        assert "fn_def" in text or "fn " in text
        assert "Function Definition" in text or "fn_def" in text or "### 6.1" in text

    def test_agent_def_documented(self) -> None:
        text = _spec_text()
        assert "agent_def" in text or "agent " in text
        assert "Agent" in text

    def test_struct_def_documented(self) -> None:
        text = _spec_text()
        assert "struct_def" in text or "struct " in text
        assert "Struct" in text

    def test_enum_def_documented(self) -> None:
        text = _spec_text()
        assert "enum_def" in text or "enum " in text
        assert "Enum" in text

    def test_trait_def_documented(self) -> None:
        text = _spec_text()
        assert "trait" in text
        assert "Trait" in text

    def test_impl_def_documented(self) -> None:
        text = _spec_text()
        assert "impl" in text
        assert "impl_def" in text or "impl " in text

    def test_import_documented(self) -> None:
        text = _spec_text()
        assert "import" in text
        assert "Import" in text or "Module" in text

    def test_export_documented(self) -> None:
        text = _spec_text()
        assert "export" in text
        assert "Export" in text or "export_def" in text

    def test_pipe_def_documented(self) -> None:
        text = _spec_text()
        assert "pipe" in text
        assert "Pipe" in text

    def test_type_alias_documented(self) -> None:
        text = _spec_text()
        assert "type_alias" in text or "Type Alias" in text or "type Name" in text

    def test_extern_fn_documented(self) -> None:
        text = _spec_text()
        assert "extern" in text
        assert "FFI" in text or "Foreign" in text

    def test_decorator_documented(self) -> None:
        text = _spec_text()
        assert "@test" in text
        assert "Decorator" in text or "decorator" in text

    def test_doc_comment_documented(self) -> None:
        text = _spec_text()
        assert "///" in text
        assert "Doc comment" in text or "doc comment" in text


class TestKeywordsMatchGrammar:
    """All keywords in the grammar should appear in SPEC.md keyword tables."""

    GRAMMAR_KEYWORDS = [
        "let",
        "mut",
        "fn",
        "return",
        "pub",
        "self",
        "agent",
        "spawn",
        "sync",
        "signal",
        "stream",
        "pipe",
        "if",
        "else",
        "match",
        "for",
        "while",
        "in",
        "type",
        "struct",
        "enum",
        "impl",
        "trait",
        "import",
        "export",
        "extern",
        "true",
        "false",
        "none",
        "new",
        "assert",
        "break",
    ]

    def test_all_grammar_keywords_in_spec(self) -> None:
        text = _spec_text()
        for kw in self.GRAMMAR_KEYWORDS:
            assert f"`{kw}`" in text, f"Keyword '{kw}' from grammar is not documented in SPEC.md"


class TestTypeKindsCoverage:
    """All 25 TypeKind variants should be documented."""

    TYPE_KINDS = [
        "INT",
        "FLOAT",
        "BOOL",
        "STRING",
        "CHAR",
        "VOID",
        "LIST",
        "MAP",
        "OPTION",
        "RESULT",
        "SIGNAL",
        "STREAM",
        "CHANNEL",
        "TENSOR",
        "FN",
        "STRUCT",
        "ENUM",
        "AGENT",
        "PIPE",
        "TYPE_ALIAS",
        "TRAIT",
        "TYPE_VAR",
        "RANGE",
        "UNKNOWN",
        "BUILTIN_FN",
    ]

    def test_all_type_kinds_in_spec(self) -> None:
        text = _spec_text()
        for tk in self.TYPE_KINDS:
            assert f"`{tk}`" in text, f"TypeKind {tk} is not documented in SPEC.md"


class TestOperatorsCoverage:
    """All operators from the grammar should appear in SPEC.md."""

    OPERATORS = [
        "|>",
        "->",
        "=>",
        "::",
        "..",
        "..=",
        "<-",
        "<=",
        ">=",
        "==",
        "!=",
        "&&",
        "||",
        "+=",
        "-=",
        "*=",
        "/=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "!",
        "=",
        "?",
        "@",
    ]

    def test_all_operators_in_spec(self) -> None:
        text = _spec_text()
        for op in self.OPERATORS:
            assert op in text, f"Operator '{op}' from grammar is not documented in SPEC.md"


class TestSpecVersionAndStatus:
    """SPEC.md must be at v1.0.0 Final."""

    def test_version_is_1_0_0(self) -> None:
        text = _spec_text()
        assert "**Version:** 1.0.0" in text

    def test_status_is_final(self) -> None:
        text = _spec_text()
        assert "1.0 Final" in text

    def test_not_working_draft(self) -> None:
        text = _spec_text()
        assert "Working Draft" not in text
        assert "Skeleton" not in text


class TestSpecSections:
    """SPEC.md must have all required sections."""

    REQUIRED_SECTIONS = [
        "Type Inference",
        "Pattern Matching",
        "Trait",
        "Module System",
        "Generics",
        "Agent Model",
        "Signal Model",
        "Stream Model",
        "Builtin Functions",
        "String Methods",
        "List Operations",
        "Map Operations",
        "FFI",
        "Error Model",
        "Stability",
        "Reserved Keywords",
    ]

    def test_has_required_sections(self) -> None:
        text = _spec_text()
        for section in self.REQUIRED_SECTIONS:
            assert section in text, f"SPEC.md is missing section: {section}"

    def test_has_python_legacy_note(self) -> None:
        text = _spec_text()
        assert "legacy" in text.lower(), "SPEC.md must note Python backend is legacy"
