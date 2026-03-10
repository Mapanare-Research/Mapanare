"""Tests for Phase 1.5 — README & Manifesto."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MANIFESTO = ROOT / "docs" / "manifesto.md"


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def _manifesto_text() -> str:
    return MANIFESTO.read_text(encoding="utf-8")


# ── Task 1: README with one-liner, code sample, install instructions, roadmap link ──


class TestREADMEExists:
    def test_readme_file_exists(self) -> None:
        assert README.exists(), "README.md must exist"

    def test_readme_is_not_empty(self) -> None:
        assert len(_readme_text().strip()) > 100, "README.md must have substantial content"


class TestREADMEOneLiner:
    def test_has_title(self) -> None:
        text = _readme_text()
        assert "# Mapanare" in text, "README must have '# Mapanare' title"

    def test_has_one_liner_description(self) -> None:
        text = _readme_text()
        assert "AI-native" in text, "README must describe Mapanare as AI-native"
        assert (
            "compiled" in text or "programming language" in text
        ), "README must mention it is a compiled programming language"


class TestREADMECodeSample:
    def test_has_mapanare_code_block(self) -> None:
        text = _readme_text()
        assert "```mn" in text, "README must have a Mapanare code sample"

    def test_code_sample_shows_agent(self) -> None:
        text = _readme_text()
        assert "agent" in text, "Code sample should demonstrate an agent"

    def test_code_sample_shows_spawn(self) -> None:
        text = _readme_text()
        assert "spawn" in text, "Code sample should show spawning an agent"

    def test_code_sample_shows_top_level_statements(self) -> None:
        text = _readme_text()
        assert "spawn" in text and "print" in text, "Code sample should show top-level statements"


class TestREADMEInstallInstructions:
    def test_has_installation_section(self) -> None:
        text = _readme_text()
        assert (
            "## Installation" in text or "## Install" in text
        ), "README must have an Installation section"

    def test_has_git_clone(self) -> None:
        text = _readme_text()
        assert "git clone" in text, "Install instructions must include git clone"

    def test_has_make_install(self) -> None:
        text = _readme_text()
        assert "make install" in text, "Install instructions must include make install"


class TestREADMERoadmapLink:
    def test_has_roadmap_section(self) -> None:
        text = _readme_text()
        assert "## Roadmap" in text, "README must have a Roadmap section"

    def test_mentions_current_version(self) -> None:
        text = _readme_text()
        assert "v0.3.0" in text, "README roadmap must mention current version"

    def test_links_to_changelog(self) -> None:
        text = _readme_text()
        assert "CHANGELOG" in text, "README must link to CHANGELOG"


class TestREADMEDocLinks:
    def test_links_to_spec(self) -> None:
        text = _readme_text()
        assert "SPEC.md" in text, "README must link to SPEC.md"

    def test_links_to_contributing(self) -> None:
        text = _readme_text()
        assert "CONTRIBUTING.md" in text, "README must link to CONTRIBUTING.md"

    def test_links_to_manifesto(self) -> None:
        text = _readme_text()
        assert "manifesto" in text.lower(), "README must link to the manifesto"

    def test_has_license_section(self) -> None:
        text = _readme_text()
        assert "MIT" in text, "README must mention MIT license"


# ── Task 2: Mapanare manifesto ("Why Mapanare Exists") ──


class TestManifestoExists:
    def test_manifesto_file_exists(self) -> None:
        assert MANIFESTO.exists(), "docs/manifesto.md must exist"

    def test_manifesto_is_substantial(self) -> None:
        text = _manifesto_text()
        word_count = len(text.split())
        assert (
            word_count >= 300
        ), f"Manifesto must be substantial (got {word_count} words, need >= 300)"


class TestManifestoContent:
    def test_has_title(self) -> None:
        text = _manifesto_text()
        assert "Why Mapanare Exists" in text, "Manifesto must have 'Why Mapanare Exists' title"

    def test_has_problem_section(self) -> None:
        text = _manifesto_text()
        assert "Problem" in text, "Manifesto must describe the problem"

    def test_has_vision_section(self) -> None:
        text = _manifesto_text()
        assert "Vision" in text, "Manifesto must describe the vision"

    def test_discusses_python_limitations(self) -> None:
        text = _manifesto_text()
        assert "Python" in text, "Manifesto should discuss Python's limitations for AI"

    def test_discusses_agents(self) -> None:
        text = _manifesto_text()
        assert "agent" in text.lower(), "Manifesto must discuss agents as a core concept"

    def test_discusses_signals(self) -> None:
        text = _manifesto_text()
        assert "signal" in text.lower(), "Manifesto must discuss reactive signals"

    def test_discusses_tensors(self) -> None:
        text = _manifesto_text()
        assert "tensor" in text.lower(), "Manifesto must discuss tensors"

    def test_discusses_pipe_operator(self) -> None:
        text = _manifesto_text()
        assert (
            "|>" in text or "pipeline" in text.lower()
        ), "Manifesto must discuss pipelines or pipe operator"

    def test_has_invitation_or_call_to_action(self) -> None:
        text = _manifesto_text()
        assert (
            "open source" in text.lower() or "contribution" in text.lower()
        ), "Manifesto must invite contributions"

    def test_discusses_compilation_approach(self) -> None:
        text = _manifesto_text()
        assert (
            "transpiler" in text.lower() or "LLVM" in text or "compile" in text.lower()
        ), "Manifesto must discuss the compilation approach"


# ── Task 3: Roadmap progress section in README ──


class TestREADMERoadmapProgress:
    def test_roadmap_mentions_next_milestone(self) -> None:
        text = _readme_text()
        assert "v0.4.0" in text or "Next" in text, "Roadmap must mention next milestone"

    def test_roadmap_has_version_description(self) -> None:
        text = _readme_text()
        # The roadmap section should describe what the current version achieved
        assert "v0.3.0" in text, "Roadmap must describe the current version"
