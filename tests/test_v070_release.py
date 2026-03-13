"""Tests for v0.7.0 release — version bump, changelog, SPEC, ROADMAP, README updates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestVersion:
    def test_version_file_reads_070(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        assert version == "0.7.0", f"VERSION should be 0.7.0, got {version}"

    def test_changelog_has_070_entry(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.7.0]" in text, "CHANGELOG.md must have a 0.7.0 entry"

    def test_changelog_has_self_hosted_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert (
            "Self-hosted MIR lowering" in text
        ), "CHANGELOG 0.7.0 should mention self-hosted MIR lowering"

    def test_changelog_has_test_runner_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "test runner" in text, "CHANGELOG 0.7.0 should mention test runner"

    def test_changelog_has_tracing_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "tracing" in text.lower(), "CHANGELOG 0.7.0 should mention tracing"

    def test_changelog_has_dwarf_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "DWARF" in text, "CHANGELOG 0.7.0 should mention DWARF debug info"

    def test_changelog_has_deploy_mention(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "Deployment infrastructure" in text, "CHANGELOG 0.7.0 should mention deployment"

    def test_changelog_link_exists(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "[0.7.0]:" in text, "CHANGELOG must have comparison link for 0.7.0"


class TestSpec:
    def test_spec_version_is_070(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "**Version:** 0.7.0" in text, "SPEC.md version should be 0.7.0"

    def test_spec_has_testing_section(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "## 10. Testing" in text, "SPEC.md must have a Testing section"

    def test_spec_has_test_decorator(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "@test" in text, "SPEC.md Testing section should mention @test decorator"

    def test_spec_has_assert_statement(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "Assert Statement" in text or "assert" in text, "SPEC.md should document assert"

    def test_spec_has_observability_section(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "## 11. Observability" in text, "SPEC.md must have an Observability section"

    def test_spec_has_tracing_docs(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "--trace" in text, "SPEC.md should document --trace flag"

    def test_spec_has_metrics_docs(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "--metrics" in text, "SPEC.md should document --metrics flag"

    def test_spec_has_error_codes(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "MN-P" in text, "SPEC.md should document structured error codes"

    def test_spec_has_dwarf_docs(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "DWARF" in text, "SPEC.md should document DWARF debug info"

    def test_spec_has_deployment_section(self) -> None:
        text = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
        assert "## 12. Deployment" in text, "SPEC.md must have a Deployment section"


class TestRoadmap:
    def test_roadmap_has_070_released(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert "v0.7.0" in text, "ROADMAP.md must mention v0.7.0"

    def test_roadmap_has_070_in_release_history(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert "**v0.7.0**" in text, "ROADMAP.md release history should include v0.7.0"

    def test_roadmap_self_hosted_status_updated(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert (
            "8,288" in text or "7,500" in text
        ), "ROADMAP self-hosted status should reflect v0.7.0 line count"

    def test_roadmap_v070_section_marked_complete(self) -> None:
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        assert 'v0.7.0 — "Self-Standing"' in text, "ROADMAP should have v0.7.0 section"


class TestReadme:
    def test_readme_version_badge_070(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "version-0.7.0" in text, "README version badge should show 0.7.0"

    def test_readme_test_count_updated(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "2983" in text or "2,983" in text, "README should reflect updated test count"

    def test_readme_has_test_command(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "mapanare test" in text, "README CLI section should include mapanare test"

    def test_readme_has_deploy_command(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "mapanare deploy" in text, "README CLI section should include mapanare deploy"

    def test_readme_self_hosted_module_count(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "lower.mn" in text, "README self-hosted section should mention lower.mn"

    def test_readme_has_trace_flag(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "--trace" in text, "README should mention --trace flag"

    def test_readme_has_debug_flag(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "-g" in text, "README should mention -g debug flag"

    def test_readme_roadmap_v070_released(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        # Check that v0.7.0 is marked as released in the roadmap table
        lines = text.split("\n")
        for line in lines:
            if "v0.7.0" in line and "Released" in line:
                return
        raise AssertionError("README roadmap table should show v0.7.0 as Released")


class TestPlanStatus:
    def test_plan_phase_8_complete(self) -> None:
        text = (ROOT / "docs" / "PLAN-v0.7.0.md").read_text(encoding="utf-8")
        assert (
            "| 8 | v0.7.0 Release & Docs | `Complete`" in text
        ), "Phase 8 should be marked Complete"

    def test_plan_all_phase_8_tasks_done(self) -> None:
        text = (ROOT / "docs" / "PLAN-v0.7.0.md").read_text(encoding="utf-8")
        # Find Phase 8 section and check all tasks are [x]
        in_phase_8 = False
        for line in text.split("\n"):
            if "## Phase 8" in line:
                in_phase_8 = True
            elif in_phase_8 and line.startswith("## "):
                break
            elif in_phase_8 and "| " in line and "`[" in line:
                assert "`[x]`" in line, f"Phase 8 task not done: {line.strip()}"
