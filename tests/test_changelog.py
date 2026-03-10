"""Tests for Phase 1.4 — CHANGELOG integrity."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION = ROOT / "VERSION"
README = ROOT / "README.md"


def _changelog_text() -> str:
    return CHANGELOG.read_text(encoding="utf-8")


def _version() -> str:
    return VERSION.read_text(encoding="utf-8").strip()


# ── Task 1 & 2: Backfill v0.1.0 and v0.2.0 entries ──


class TestChangelogEntries:
    def test_changelog_exists(self) -> None:
        assert CHANGELOG.exists(), "CHANGELOG.md must exist"

    def test_has_v010_entry(self) -> None:
        text = _changelog_text()
        assert "## [0.1.0]" in text, "CHANGELOG must have a v0.1.0 entry"

    def test_has_v020_entry(self) -> None:
        text = _changelog_text()
        assert "## [0.2.0]" in text, "CHANGELOG must have a v0.2.0 entry"

    def test_has_unreleased_section(self) -> None:
        text = _changelog_text()
        assert "## [Unreleased]" in text, "CHANGELOG must have an [Unreleased] section"

    def test_v010_has_content(self) -> None:
        text = _changelog_text()
        v010_idx = text.index("## [0.1.0]")
        section = text[v010_idx : v010_idx + 500]
        assert "### Added" in section, "v0.1.0 must have an Added section"
        assert "- " in section, "v0.1.0 must have list items"

    def test_v020_has_content(self) -> None:
        text = _changelog_text()
        v020_idx = text.index("## [0.2.0]")
        section = text[v020_idx : v020_idx + 500]
        assert "### Added" in section, "v0.2.0 must have an Added section"
        assert "- " in section, "v0.2.0 must have list items"


# ── Task 3: Keep a Changelog format ──


class TestChangelogFormat:
    def test_header_present(self) -> None:
        text = _changelog_text()
        assert "# Changelog" in text

    def test_keepachangelog_link(self) -> None:
        text = _changelog_text()
        assert "keepachangelog.com" in text

    def test_semver_link(self) -> None:
        text = _changelog_text()
        assert "semver.org" in text

    def test_uses_standard_categories(self) -> None:
        text = _changelog_text()
        # At least Added and Changed should appear
        assert "### Added" in text, "Must use '### Added' category"
        assert "### Changed" in text, "Must use '### Changed' category"

    def test_versions_in_descending_order(self) -> None:
        text = _changelog_text()
        versions = re.findall(r"## \[(\d+\.\d+\.\d+)\]", text)
        assert len(versions) >= 2, "Must have at least 2 versioned entries"
        # Versions should be in descending order
        for i in range(len(versions) - 1):
            parts_a = tuple(int(x) for x in versions[i].split("."))
            parts_b = tuple(int(x) for x in versions[i + 1].split("."))
            assert parts_a > parts_b, f"{versions[i]} should come before {versions[i+1]}"

    def test_comparison_links_at_bottom(self) -> None:
        text = _changelog_text()
        assert "[Unreleased]:" in text, "Must have comparison link for Unreleased"
        assert "[0.2.0]:" in text, "Must have comparison link for 0.2.0"
        assert "[0.1.0]:" in text, "Must have comparison link for 0.1.0"


# ── Task 4: Version consistency ──


class TestVersionConsistency:
    def test_version_file_matches_changelog(self) -> None:
        version = _version()
        text = _changelog_text()
        assert (
            f"## [{version}]" in text
        ), f"VERSION ({version}) must have a matching CHANGELOG entry"

    def test_readme_version_badge_matches(self) -> None:
        version = _version()
        readme = README.read_text(encoding="utf-8")
        assert (
            f"version-{version}" in readme
        ), f"README version badge must match VERSION file ({version})"

    def test_readme_roadmap_link_valid(self) -> None:
        readme = README.read_text(encoding="utf-8")
        # Should not reference a non-existent ROADMAP.md
        assert (
            "docs/ROADMAP.md" not in readme
        ), "README should not link to non-existent docs/ROADMAP.md"

    def test_roadmap_target_exists(self) -> None:
        readme = README.read_text(encoding="utf-8")
        # Extract the roadmap link target
        match = re.search(r"\[Roadmap\]\(([^)]+)\)", readme)
        if match:
            target = match.group(1)
            target_path = ROOT / target
            assert target_path.exists(), f"Roadmap link target '{target}' must exist"
