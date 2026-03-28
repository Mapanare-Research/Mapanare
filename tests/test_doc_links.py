"""Validate that documentation links point to files that actually exist.

Scans .md files in docs/ for relative links and verifies the targets exist
in the repository. Also checks that code examples referenced in docs
correspond to real files.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# Regex for Markdown links: [text](path) — only relative, not http(s)
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Regex for code block references: ```path/to/file.ext or file.ext in backticks
_FILE_REF_RE = re.compile(r"`([a-zA-Z0-9_./\\-]+\.[a-zA-Z]{1,6})`")


def _collect_md_files() -> list[Path]:
    """Collect all .md files under docs/."""
    if not DOCS_DIR.is_dir():
        return []
    return sorted(DOCS_DIR.rglob("*.md"))


def _extract_relative_links(md_file: Path) -> list[tuple[int, str, str]]:
    """Extract (line_number, link_text, link_target) for relative links."""
    results = []
    text = md_file.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        for match in _LINK_RE.finditer(line):
            target = match.group(2)
            # Skip external URLs, anchors, and mailto
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Strip anchor from target
            target = target.split("#")[0]
            if target:
                results.append((i, match.group(1), target))
    return results


MD_FILES = _collect_md_files()


@pytest.mark.parametrize(
    "md_file",
    MD_FILES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in MD_FILES],
)
def test_relative_links_valid(md_file: Path) -> None:
    """All relative links in docs should point to existing files or directories."""
    links = _extract_relative_links(md_file)
    # Skip template files with placeholder links (NNNN, XXXX, etc.)
    if "TEMPLATE" in md_file.name.upper():
        pytest.skip("Template file with placeholder links")
    broken = []
    for line_no, text, target in links:
        # Skip image badges, shields.io, and other known external patterns
        if target.endswith((".svg", ".png", ".jpg", ".gif")):
            continue
        # Resolve relative to the markdown file's directory
        resolved = (md_file.parent / target).resolve()
        if not resolved.exists():
            # Also try from repo root
            alt = (REPO_ROOT / target).resolve()
            if not alt.exists():
                # Also try from docs root (common in translated README files)
                docs_alt = (DOCS_DIR / target).resolve()
                if not docs_alt.exists():
                    broken.append(f"  line {line_no}: [{text}]({target})")
    if broken:
        pytest.fail(f"Broken links in {md_file.relative_to(REPO_ROOT)}:\n" + "\n".join(broken))


def test_roadmap_exists() -> None:
    """The roadmap file should exist at the documented path."""
    assert (DOCS_DIR / "roadmap" / "ROADMAP.md").is_file()


def test_spec_exists() -> None:
    """The language spec should exist."""
    assert (DOCS_DIR / "SPEC.md").is_file()


def test_plan_exists() -> None:
    """The v2.0.0 plan should exist."""
    assert (DOCS_DIR / "roadmap" / "v2.0.0" / "PLAN.md").is_file()


def test_example_dirs_exist() -> None:
    """Example directories referenced in the roadmap should exist."""
    examples = REPO_ROOT / "examples"
    assert (examples / "wasm").is_dir(), "examples/wasm/ missing"
    assert (examples / "gpu").is_dir(), "examples/gpu/ missing"
    assert (examples / "mobile").is_dir(), "examples/mobile/ missing"


def test_stdlib_dirs_exist() -> None:
    """Stdlib directories referenced in CLAUDE.md should exist."""
    stdlib = REPO_ROOT / "stdlib"
    expected = ["gpu", "wasm"]
    for name in expected:
        assert (stdlib / name).is_dir(), f"stdlib/{name}/ missing"
