"""Tests for Phase 1.4 — Language Spec Skeleton (SPEC.md)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "SPEC.md"


def _spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


# ── Task 1: Language goals and non-goals ──


class TestGoalsAndNonGoals:
    def test_spec_file_exists(self) -> None:
        assert SPEC.exists(), "SPEC.md must exist"

    def test_has_goals_section(self) -> None:
        text = _spec_text()
        assert "### Goals" in text, "SPEC.md must have a Goals section"

    def test_has_non_goals_section(self) -> None:
        text = _spec_text()
        assert "### Non-Goals" in text, "SPEC.md must have a Non-Goals section"

    def test_goals_has_ai_native(self) -> None:
        text = _spec_text()
        assert "AI-native" in text, "Goals must mention AI-native primitives"

    def test_goals_has_compiled(self) -> None:
        text = _spec_text()
        assert "Compiled" in text or "compiled" in text, "Goals must mention compilation"

    def test_goals_has_type_safe(self) -> None:
        text = _spec_text()
        assert (
            "Type-safe" in text or "type inference" in text.lower()
        ), "Goals must mention type safety"

    def test_goals_has_concurrency(self) -> None:
        text = _spec_text()
        assert (
            "agent" in text.lower() and "message passing" in text.lower()
        ), "Goals must mention agent concurrency"

    def test_goals_has_reactive(self) -> None:
        text = _spec_text()
        assert (
            "signal" in text.lower() and "reactive" in text.lower()
        ), "Goals must mention reactive signals"

    def test_goals_has_pipeline(self) -> None:
        text = _spec_text()
        assert "|>" in text, "Goals must mention pipe operator"

    def test_goals_has_ml_ready(self) -> None:
        text = _spec_text()
        assert "Tensor" in text, "Goals must mention tensors / ML-ready"

    def test_non_goals_has_not_systems_lang(self) -> None:
        text = _spec_text()
        assert (
            "Not a general-purpose systems language" in text
        ), "Non-goals must state not a systems language"

    def test_non_goals_has_not_interpreted(self) -> None:
        text = _spec_text()
        assert "Not interpreted" in text, "Non-goals must state not interpreted"

    def test_non_goals_has_no_gc(self) -> None:
        text = _spec_text()
        assert (
            "garbage collector" in text.lower() or "No garbage" in text
        ), "Non-goals must mention no GC in native mode"

    def test_non_goals_has_no_oop(self) -> None:
        text = _spec_text()
        assert (
            "No OOP" in text or "no classes" in text.lower() or "No OOP" in text
        ), "Non-goals must state no OOP class hierarchies"


# ── Task 2: Primitive types ──


class TestPrimitiveTypes:
    EXPECTED_TYPES = [
        "Int",
        "Float",
        "Bool",
        "String",
        "Char",
        "Void",
        "Option<T>",
        "Result<T, E>",
        "Tensor<T>[shape]",
        "List<T>",
        "Map<K, V>",
        "Signal<T>",
        "Stream<T>",
        "Channel<T>",
    ]

    def test_has_primitive_types_section(self) -> None:
        text = _spec_text()
        assert "Primitive Types" in text, "SPEC.md must have a Primitive Types section"

    def test_all_primitive_types_documented(self) -> None:
        text = _spec_text()
        for t in self.EXPECTED_TYPES:
            # Check that the type name appears in a table row (backtick-wrapped)
            assert f"`{t}`" in text, f"Primitive type {t} must be documented in SPEC.md"

    def test_each_type_has_description(self) -> None:
        text = _spec_text()
        for t in self.EXPECTED_TYPES:
            # Each type row should have a pipe-separated description
            pattern = rf"\|\s*`{re.escape(t)}`\s*\|.*\S.*\|"
            assert re.search(pattern, text), f"Primitive type {t} must have a non-empty description"

    def test_has_numeric_literals(self) -> None:
        text = _spec_text()
        assert "Numeric Literals" in text, "SPEC.md must document numeric literals"

    def test_has_string_literals(self) -> None:
        text = _spec_text()
        assert "String Literals" in text, "SPEC.md must document string literals"


# ── Task 3: Keywords ──


class TestKeywords:
    EXPECTED_KEYWORDS = [
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
        "in",
        "type",
        "struct",
        "enum",
        "impl",
        "import",
        "export",
        "true",
        "false",
        "none",
    ]

    def test_has_keywords_section(self) -> None:
        text = _spec_text()
        assert (
            "## 3. Keywords" in text or "Keywords" in text
        ), "SPEC.md must have a Keywords section"

    def test_all_keywords_documented(self) -> None:
        text = _spec_text()
        for kw in self.EXPECTED_KEYWORDS:
            assert f"`{kw}`" in text, f"Keyword '{kw}' must be documented in SPEC.md"

    def test_keyword_categories_present(self) -> None:
        text = _spec_text()
        categories = [
            "Bindings and Mutability",
            "Functions and Definitions",
            "Agents and Concurrency",
            "Reactive and Streaming",
            "Control Flow",
            "Types and Data",
            "Modules",
            "Literals",
        ]
        for cat in categories:
            assert cat in text, f"Keyword category '{cat}' must be in SPEC.md"


# ── Task 4: Example programs ──


class TestExamplePrograms:
    def test_has_examples_section(self) -> None:
        text = _spec_text()
        assert "Example Programs" in text, "SPEC.md must have Example Programs section"

    def test_has_hello_world(self) -> None:
        text = _spec_text()
        assert "Hello World" in text, "SPEC.md must have Hello World example"
        assert 'print("Hello, Mapanare!")' in text, "Hello World must print to stdout"
        assert "fn main()" in text, "Hello World must define main function"

    def test_has_agent_example(self) -> None:
        text = _spec_text()
        assert "Agent Definition" in text, "SPEC.md must have Agent Definition example"
        assert "agent Greeter" in text, "Agent example must define Greeter agent"
        assert "spawn Greeter" in text, "Agent example must spawn the agent"
        assert "sync" in text, "Agent example must use sync"

    def test_has_pipeline_example(self) -> None:
        text = _spec_text()
        assert "Pipeline" in text, "SPEC.md must have Pipeline example"
        assert "pipe ClassifyText" in text, "Pipeline example must define a pipe"
        assert "|>" in text, "Pipeline example must use pipe operator"

    def test_examples_have_behavior_docs(self) -> None:
        text = _spec_text()
        assert text.count("**Behavior:**") >= 3, "Each example must have a Behavior description"


# ── Task 5: Type system ──


class TestTypeSystem:
    def test_has_type_system_section(self) -> None:
        text = _spec_text()
        assert "Type System" in text, "SPEC.md must have a Type System section"

    def test_has_type_inference(self) -> None:
        text = _spec_text()
        assert "inference" in text.lower(), "Type system must discuss type inference"

    def test_has_generics(self) -> None:
        text = _spec_text()
        assert (
            "Generic Types" in text or "### Generic" in text
        ), "Type system must document generics"
        assert "identity<T>" in text, "Generics must show a generic function example"
        assert "Pair<A, B>" in text, "Generics must show a generic struct example"

    def test_has_option_type(self) -> None:
        text = _spec_text()
        assert (
            "### Option Type" in text or "Option Type" in text
        ), "Type system must document Option<T>"
        assert "Some(" in text, "Option must show Some variant"
        assert "None" in text, "Option must show None variant"

    def test_has_result_type(self) -> None:
        text = _spec_text()
        assert (
            "### Result Type" in text or "Result Type" in text
        ), "Type system must document Result<T, E>"
        assert "Ok(" in text, "Result must show Ok variant"
        assert "Err(" in text, "Result must show Err variant"
        assert "?" in text, "Result must document ? operator for error propagation"

    def test_has_struct_types(self) -> None:
        text = _spec_text()
        assert "Struct Types" in text, "Type system must document struct types"
        assert "struct Point" in text, "Structs must show a struct example"

    def test_has_enum_types(self) -> None:
        text = _spec_text()
        assert "Enum Types" in text, "Type system must document enum types"
        assert "enum Shape" in text, "Enums must show an enum example"
        assert "exhaustive" in text.lower(), "Enums must mention exhaustive matching"

    def test_has_type_aliases(self) -> None:
        text = _spec_text()
        assert "Type Aliases" in text, "Type system must document type aliases"

    def test_has_agent_types(self) -> None:
        text = _spec_text()
        assert "Agent Types" in text, "Type system must document agent types"

    def test_has_tensor_types(self) -> None:
        text = _spec_text()
        assert "Tensor Types" in text, "Type system must document tensor types"
        assert (
            "shape mismatch" in text.lower() or "COMPILE ERROR" in text
        ), "Tensors must show compile-time shape checking"


# ── Task 6: RFC 0001 ──


class TestRFC0001:
    RFC_PATH = ROOT / "rfcs" / "0001-agent-syntax.md"

    def test_rfc_file_exists(self) -> None:
        assert self.RFC_PATH.exists(), "rfcs/0001-agent-syntax.md must exist"

    def test_rfc_has_title(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "RFC 0001" in text or "Agent Syntax" in text, "RFC must have a title"

    def test_rfc_has_summary(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "Summary" in text, "RFC must have a Summary section"

    def test_rfc_has_motivation(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "Motivation" in text, "RFC must have a Motivation section"

    def test_rfc_has_detailed_design(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "Design" in text or "Proposal" in text, "RFC must have a Detailed Design section"

    def test_rfc_has_agent_keyword(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "agent" in text.lower(), "RFC must discuss agent syntax"

    def test_rfc_has_code_examples(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "```mn" in text, "RFC must include Mapanare code examples"

    def test_rfc_has_alternatives(self) -> None:
        text = self.RFC_PATH.read_text(encoding="utf-8")
        assert "Alternative" in text, "RFC must discuss alternatives considered"
