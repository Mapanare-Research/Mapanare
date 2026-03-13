"""Tests for v0.6.0 release — MIR pipeline, bootstrap freeze, version bump."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestVersion:
    def test_version_file_reads_current(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        assert version in ("0.6.0", "0.7.0"), f"VERSION should be 0.6.0 or 0.7.0, got {version}"

    def test_changelog_has_060_entry(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.6.0]" in text, "CHANGELOG.md must have a 0.6.0 entry"

    def test_changelog_has_mir_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "MIR pipeline" in text, "CHANGELOG 0.6.0 should mention MIR pipeline"


class TestBootstrapSnapshot:
    def test_bootstrap_directory_exists(self) -> None:
        assert (ROOT / "bootstrap").is_dir()

    def test_bootstrap_has_mir_modules(self) -> None:
        bootstrap = ROOT / "bootstrap"
        assert (bootstrap / "mir.py").exists(), "bootstrap must include mir.py"
        assert (bootstrap / "mir_builder.py").exists(), "bootstrap must include mir_builder.py"
        assert (bootstrap / "lower.py").exists(), "bootstrap must include lower.py"
        assert (bootstrap / "mir_opt.py").exists(), "bootstrap must include mir_opt.py"
        assert (bootstrap / "emit_llvm_mir.py").exists(), "bootstrap must include emit_llvm_mir.py"
        assert (
            bootstrap / "emit_python_mir.py"
        ).exists(), "bootstrap must include emit_python_mir.py"

    def test_bootstrap_has_core_modules(self) -> None:
        bootstrap = ROOT / "bootstrap"
        for name in [
            "parser.py",
            "ast_nodes.py",
            "semantic.py",
            "emit_llvm.py",
            "emit_python.py",
            "optimizer.py",
            "cli.py",
            "types.py",
        ]:
            assert (bootstrap / name).exists(), f"bootstrap must include {name}"

    def test_bootstrap_has_grammar(self) -> None:
        assert (ROOT / "bootstrap" / "mapanare.lark").exists()

    def test_bootstrap_has_makefile(self) -> None:
        assert (ROOT / "bootstrap" / "Makefile").exists()

    def test_bootstrap_readme_mentions_060(self) -> None:
        text = (ROOT / "bootstrap" / "README.md").read_text(encoding="utf-8")
        assert "v0.6.0" in text, "bootstrap README must reference v0.6.0"

    def test_bootstrap_snapshot_matches_source(self) -> None:
        """Key compiler modules in bootstrap/ should match mapanare/."""
        for name in ["parser.py", "ast_nodes.py", "semantic.py", "mir.py", "lower.py"]:
            bootstrap_text = (ROOT / "bootstrap" / name).read_text(encoding="utf-8")
            source_text = (ROOT / "mapanare" / name).read_text(encoding="utf-8")
            assert bootstrap_text == source_text, f"bootstrap/{name} does not match mapanare/{name}"


class TestSpecMIR:
    def test_spec_has_mir_section(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "MIR" in text, "SPEC.md must mention MIR"

    def test_spec_has_mir_instructions(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "SSA" in text, "SPEC.md MIR section should mention SSA"
        assert (
            "Basic block" in text or "basic block" in text
        ), "SPEC.md MIR section should mention basic blocks"

    def test_spec_version_is_current(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert (
            "**Version:** 0.6.0" in text or "**Version:** 0.7.0" in text
        ), "SPEC.md version should be 0.6.0 or 0.7.0"


class TestRoadmap:
    def test_roadmap_has_060_released(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert "v0.6.0" in text, "ROADMAP.md must mention v0.6.0"

    def test_roadmap_architecture_has_mir(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert "MIR" in text, "ROADMAP architecture diagram should include MIR"


class TestReadme:
    def test_readme_version_badge(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert (
            "version-0.6.0" in text or "version-0.7.0" in text
        ), "README version badge should show 0.6.0 or 0.7.0"

    def test_readme_architecture_has_mir(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "MIR Lowering" in text, "README architecture table should include MIR Lowering"
        assert "MIR Optimizer" in text, "README architecture table should include MIR Optimizer"
