"""Tests for VSCode extension — syntax highlighting, snippets, extension manifest."""

import json
import os

import pytest

EDITORS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "editors", "vscode")


# ===========================================================================
# Task 4: VSCode .mn syntax highlighting
# ===========================================================================


class TestTextMateGrammar:
    """Validate the TextMate grammar for Mapanare syntax highlighting."""

    @pytest.fixture
    def grammar(self) -> dict:
        path = os.path.join(EDITORS_DIR, "syntaxes", "mapanare.tmLanguage.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_grammar_is_valid_json(self, grammar: dict) -> None:
        assert isinstance(grammar, dict)

    def test_grammar_scope_name(self, grammar: dict) -> None:
        assert grammar["scopeName"] == "source.mapanare"

    def test_grammar_name(self, grammar: dict) -> None:
        assert grammar["name"] == "Mapanare"

    def test_grammar_file_types(self, grammar: dict) -> None:
        assert "mn" in grammar["fileTypes"]

    def test_grammar_has_patterns(self, grammar: dict) -> None:
        assert "patterns" in grammar
        assert len(grammar["patterns"]) > 0

    def test_grammar_has_repository(self, grammar: dict) -> None:
        assert "repository" in grammar

    def test_grammar_has_comments_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "comments" in repo
        patterns = repo["comments"]["patterns"]
        scopes = [p.get("name", "") for p in patterns]
        assert any("comment.line" in s for s in scopes)
        assert any("comment.block" in s for s in scopes)

    def test_grammar_has_strings_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "strings" in repo

    def test_grammar_has_numbers_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "numbers" in repo
        patterns = repo["numbers"]["patterns"]
        names = [p.get("name", "") for p in patterns]
        assert any("hex" in n for n in names)
        assert any("float" in n for n in names)
        assert any("integer" in n for n in names)

    def test_grammar_has_keywords_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "keywords" in repo
        patterns = repo["keywords"]["patterns"]
        all_matches = " ".join(p.get("match", "") for p in patterns)
        for kw in ["fn", "let", "agent", "pipe", "if", "match", "for", "spawn", "signal"]:
            assert kw in all_matches, f"keyword '{kw}' missing"

    def test_grammar_has_types_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "types" in repo
        patterns = repo["types"]["patterns"]
        all_matches = " ".join(p.get("match", "") for p in patterns)
        for t in ["Int", "Float", "Bool", "String"]:
            assert t in all_matches, f"type '{t}' missing"

    def test_grammar_has_operators_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "operators" in repo

    def test_grammar_has_decorators_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "decorators" in repo

    def test_grammar_has_function_definition_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "function-definition" in repo

    def test_grammar_has_agent_definition_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "agent-definition" in repo

    def test_grammar_has_pipe_definition_rule(self, grammar: dict) -> None:
        repo = grammar["repository"]
        assert "pipe-definition" in repo


# ===========================================================================
# Task 5: VSCode LSP integration
# ===========================================================================


class TestExtensionManifest:
    """Validate the VSCode extension package.json."""

    @pytest.fixture
    def manifest(self) -> dict:
        path = os.path.join(EDITORS_DIR, "package.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_manifest_is_valid_json(self, manifest: dict) -> None:
        assert isinstance(manifest, dict)

    def test_manifest_name(self, manifest: dict) -> None:
        assert manifest["name"] == "mapanare"

    def test_manifest_has_engine(self, manifest: dict) -> None:
        assert "vscode" in manifest["engines"]

    def test_manifest_has_language_contribution(self, manifest: dict) -> None:
        langs = manifest["contributes"]["languages"]
        assert len(langs) == 1
        assert langs[0]["id"] == "mapanare"
        assert ".mn" in langs[0]["extensions"]

    def test_manifest_has_grammar_contribution(self, manifest: dict) -> None:
        grammars = manifest["contributes"]["grammars"]
        assert len(grammars) == 1
        assert grammars[0]["language"] == "mapanare"
        assert grammars[0]["scopeName"] == "source.mapanare"

    def test_manifest_has_snippet_contribution(self, manifest: dict) -> None:
        snippets = manifest["contributes"]["snippets"]
        assert len(snippets) == 1
        assert snippets[0]["language"] == "mapanare"

    def test_manifest_has_lsp_dependency(self, manifest: dict) -> None:
        deps = manifest.get("dependencies", {})
        assert "vscode-languageclient" in deps

    def test_manifest_has_lsp_config(self, manifest: dict) -> None:
        props = manifest["contributes"]["configuration"]["properties"]
        assert "mapanare.lsp.enabled" in props
        assert "mapanare.lsp.path" in props


# ===========================================================================
# Task 6: VSCode `mapa run` from command palette
# ===========================================================================


class TestCommandPalette:
    """Validate command palette commands in extension manifest."""

    @pytest.fixture
    def manifest(self) -> dict:
        path = os.path.join(EDITORS_DIR, "package.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_run_command_registered(self, manifest: dict) -> None:
        commands = manifest["contributes"]["commands"]
        cmd_ids = [c["command"] for c in commands]
        assert "mapanare.run" in cmd_ids

    def test_check_command_registered(self, manifest: dict) -> None:
        commands = manifest["contributes"]["commands"]
        cmd_ids = [c["command"] for c in commands]
        assert "mapanare.check" in cmd_ids

    def test_compile_command_registered(self, manifest: dict) -> None:
        commands = manifest["contributes"]["commands"]
        cmd_ids = [c["command"] for c in commands]
        assert "mapanare.compile" in cmd_ids

    def test_fmt_command_registered(self, manifest: dict) -> None:
        commands = manifest["contributes"]["commands"]
        cmd_ids = [c["command"] for c in commands]
        assert "mapanare.fmt" in cmd_ids

    def test_restart_lsp_command_registered(self, manifest: dict) -> None:
        commands = manifest["contributes"]["commands"]
        cmd_ids = [c["command"] for c in commands]
        assert "mapanare.restartLsp" in cmd_ids

    def test_run_command_has_palette_entry(self, manifest: dict) -> None:
        palette = manifest["contributes"]["menus"]["commandPalette"]
        palette_cmds = [e["command"] for e in palette]
        assert "mapanare.run" in palette_cmds

    def test_run_command_scoped_to_mapanare(self, manifest: dict) -> None:
        palette = manifest["contributes"]["menus"]["commandPalette"]
        run_entry = next(e for e in palette if e["command"] == "mapanare.run")
        assert "mapanare" in run_entry["when"]


# ===========================================================================
# Task 7: VSCode snippets for agent, pipe, fn
# ===========================================================================


class TestSnippets:
    """Validate VSCode snippets for Mapanare."""

    @pytest.fixture
    def snippets(self) -> dict:
        path = os.path.join(EDITORS_DIR, "snippets", "mapanare.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_snippets_is_valid_json(self, snippets: dict) -> None:
        assert isinstance(snippets, dict)

    def test_fn_snippet_exists(self, snippets: dict) -> None:
        assert "Function" in snippets
        assert snippets["Function"]["prefix"] == "fn"
        body = "\n".join(snippets["Function"]["body"])
        assert "fn" in body

    def test_agent_snippet_exists(self, snippets: dict) -> None:
        assert "Agent" in snippets
        assert snippets["Agent"]["prefix"] == "agent"
        body = "\n".join(snippets["Agent"]["body"])
        assert "agent" in body
        assert "input" in body
        assert "output" in body

    def test_pipe_snippet_exists(self, snippets: dict) -> None:
        assert "Pipe" in snippets
        assert snippets["Pipe"]["prefix"] == "pipe"
        body = "\n".join(snippets["Pipe"]["body"])
        assert "pipe" in body
        assert "|>" in body

    def test_struct_snippet_exists(self, snippets: dict) -> None:
        assert "Struct" in snippets
        assert snippets["Struct"]["prefix"] == "struct"

    def test_enum_snippet_exists(self, snippets: dict) -> None:
        assert "Enum" in snippets
        assert snippets["Enum"]["prefix"] == "enum"

    def test_let_snippet_exists(self, snippets: dict) -> None:
        assert "Let Binding" in snippets
        assert snippets["Let Binding"]["prefix"] == "let"

    def test_match_snippet_exists(self, snippets: dict) -> None:
        assert "Match Expression" in snippets
        assert snippets["Match Expression"]["prefix"] == "match"

    def test_for_snippet_exists(self, snippets: dict) -> None:
        assert "For Loop" in snippets
        assert snippets["For Loop"]["prefix"] == "for"

    def test_spawn_snippet_exists(self, snippets: dict) -> None:
        assert "Spawn Agent" in snippets
        assert snippets["Spawn Agent"]["prefix"] == "spawn"

    def test_main_snippet_exists(self, snippets: dict) -> None:
        assert "Main Function" in snippets
        assert snippets["Main Function"]["prefix"] == "main"

    def test_impl_snippet_exists(self, snippets: dict) -> None:
        assert "Impl Block" in snippets
        assert snippets["Impl Block"]["prefix"] == "impl"

    def test_all_snippets_have_body(self, snippets: dict) -> None:
        for name, snippet in snippets.items():
            assert "body" in snippet, f"Snippet '{name}' missing body"
            assert isinstance(snippet["body"], list), f"Snippet '{name}' body should be a list"
            assert len(snippet["body"]) > 0, f"Snippet '{name}' has empty body"

    def test_all_snippets_have_prefix(self, snippets: dict) -> None:
        for name, snippet in snippets.items():
            assert "prefix" in snippet, f"Snippet '{name}' missing prefix"

    def test_all_snippets_have_description(self, snippets: dict) -> None:
        for name, snippet in snippets.items():
            assert "description" in snippet, f"Snippet '{name}' missing description"


# ===========================================================================
# Language configuration
# ===========================================================================


class TestLanguageConfiguration:
    """Validate language-configuration.json."""

    @pytest.fixture
    def config(self) -> dict:
        path = os.path.join(EDITORS_DIR, "language-configuration.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_config_is_valid_json(self, config: dict) -> None:
        assert isinstance(config, dict)

    def test_config_has_comments(self, config: dict) -> None:
        assert config["comments"]["lineComment"] == "//"
        assert config["comments"]["blockComment"] == ["/*", "*/"]

    def test_config_has_brackets(self, config: dict) -> None:
        assert len(config["brackets"]) >= 3

    def test_config_has_auto_closing_pairs(self, config: dict) -> None:
        assert len(config["autoClosingPairs"]) >= 4
