#!/usr/bin/env python3
"""scripts/check_changelog_honesty.py — v4.31.0 Phase 3.1.

Parses the most-recent ``CHANGELOG.md`` entry (the first `## [version]`
block under `## [Unreleased]`) and fact-checks every concrete claim it
makes against the source tree. The goal is narrow: catch entries that
mention test files or symbols that don't exist.

The v4.26.0 seven-reviewer panel flagged three CHANGELOG entries
(v4.18.0, v4.24.0, v4.25.0) that advertised "wired", "complete", or
"working" features whose implementations were stubs. The entries
referenced test files and symbols that either didn't exist at commit
time or were silently broken. This script closes that loop at PR time:
if the CHANGELOG names a path or a symbol, the script confirms the
path exists or the symbol is greppable.

Rules
-----

The script parses Markdown bullets inside the most recent version
block and looks for three categories of claim:

1. **Backticked path fragments that look like file paths.**
   Anything inside backticks that matches ``r"[\\w./-]+\\.(py|mn|c|h|ll|md|yml|toml|sh)"``
   is checked against ``os.path.exists``. Missing paths fail the check.
2. **Backticked symbols prefixed with ``__mn_`` or matching common C
   identifiers.** These are verified via ``git grep``. Missing symbols
   fail the check.
3. **Backticked references to pytest test IDs** (``tests/...::Class::method``).
   The file portion is checked; the class/method names are not parsed.

To opt a line out of checking, prefix the bullet with
``<!-- no-check -->`` as the first token of the bullet body. The script
treats that bullet as prose and skips all its backtick contents.

Usage
-----

    python3 scripts/check_changelog_honesty.py
    python3 scripts/check_changelog_honesty.py CHANGELOG.md

Exits 0 on clean, 1 on any mismatch. Intended to run from the repo
root in CI whenever ``CHANGELOG.md`` is modified.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Regex for a backticked chunk, preserving nesting with leading/trailing.
_BACKTICK = re.compile(r"`([^`]+)`")

# Markdown link ``[text](path)`` — used to extract link targets instead
# of checking the human-facing link text.
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# File extensions we care about (exist on disk).
_PATHY_EXT = {".py", ".mn", ".c", ".h", ".ll", ".md", ".yml", ".toml", ".sh", ".lark", ".wat"}

# Identifier prefixes we expect to be greppable in the source tree.
_SYMBOL_PREFIXES = ("__mn_", "mapanare_", "_mn_")

# Roots to search for bare-basename files (e.g. ``mir_opt.py`` → find
# ``mapanare/mir_opt.py``). Missing roots are skipped.
_SEARCH_ROOTS = (
    "mapanare",
    "runtime",
    "scripts",
    "tests",
    "docs",
    ".github",
    ".reviews",
    "examples",
    "stdlib",
)

# Where to search for symbols via ``git grep``.
_GREP_ROOTS = ("mapanare", "runtime", "scripts", "tests")

_OPT_OUT_TOKEN = "<!-- no-check -->"

# Section headers that imply every bullet is talking about something
# that no longer exists. Opt-out is automatic inside these sections.
_DELETION_SECTION_HEADERS = (
    "### Removed",
    "### Deleted",
    "### Deprecated",
)


def _read_changelog(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _find_latest_version_block(lines: list[str]) -> list[str] | None:
    """Return the lines of the most recent ``## [X.Y.Z]`` block.

    Skips the ``## [Unreleased]`` header if present; we only fact-check
    entries that name a version. Returns ``None`` if no version block
    is present.
    """
    in_block = False
    collected: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_block:
                return collected
            # Is this the start of a numbered version block?
            # Allows ``[4.31.0]``, ``[4.31.0-rc1]``, ``[4.31.0-test]``.
            if re.match(r"##\s+\[\d+\.\d+\.\d+[^\]]*\]", line):
                in_block = True
                collected.append(line)
                continue
            # Non-numbered ``## `` header — skip (e.g. Unreleased).
            continue
        if in_block:
            collected.append(line)
    return collected if collected else None


def _extract_backticked(line: str) -> list[str]:
    return _BACKTICK.findall(line)


def _is_pathy(text: str) -> bool:
    for ext in _PATHY_EXT:
        if text.endswith(ext) or ext + ":" in text:
            return True
    return False


def _looks_like_symbol(text: str) -> bool:
    if " " in text:
        return False
    if text.startswith(_SYMBOL_PREFIXES):
        return True
    return False


def _strip_trailing_punctuation(path: str) -> str:
    # Drop any trailing punctuation that might have slipped into the
    # backticks from sloppy prose ("in ``foo.py``, which does X").
    return path.rstrip(".,;:)!?")


def _normalise_path(raw: str) -> str:
    """Normalise a path fragment pulled out of backticks.

    Handles:
    - ``tests/foo.py::Class::method`` → ``tests/foo.py``
    - ``foo.py:123`` → ``foo.py``
    - ``foo.py:symbol_name`` → ``foo.py`` (the symbol side is not checked
      here; it's usually a class or method that the reader can find)
    - surrounding whitespace and punctuation
    """
    p = _strip_trailing_punctuation(raw.strip())
    if "::" in p:
        p = p.split("::", 1)[0]
    if ":" in p:
        head, _ = p.split(":", 1)
        p = head
    return p


def _path_exists(raw_path: str) -> bool:
    """Return True if ``raw_path`` is a real file in the repo.

    Tries three resolutions, in order:

    1. The literal path as given (relative to the repo root).
    2. ``./<path>`` — strips a leading ``./`` if present (common in
       Markdown link targets).
    3. Bare-basename fallback: if ``raw_path`` contains no directory
       separator, search for a file by that basename under
       ``_SEARCH_ROOTS``. This is what lets a prose mention of
       ``mir_opt.py`` resolve to ``mapanare/mir_opt.py``.
    """
    if Path(raw_path).exists():
        return True
    if raw_path.startswith("./") and Path(raw_path[2:]).exists():
        return True
    if "/" not in raw_path and "\\" not in raw_path:
        # Bare basename — look for it under each known root.
        for root in _SEARCH_ROOTS:
            root_path = Path(root)
            if not root_path.exists():
                continue
            for match in root_path.rglob(raw_path):
                if match.is_file():
                    return True
    return False


def _grep_symbol(name: str) -> bool:
    # v4.32.0 Phase 2.6 (Anaconda): fall back to ``grep -rl`` when ``.git``
    # is not present (e.g. Debian ``dpkg-buildpackage`` scrubs ``.git``
    # before running the test suite). ``git grep`` is still preferred
    # because it respects .gitignore and is faster on large trees.
    has_git = Path(".git").is_dir()
    for root in _GREP_ROOTS:
        if not Path(root).exists():
            continue
        if has_git:
            result = subprocess.run(
                ["git", "grep", "-l", name, root],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["grep", "-rl", name, root],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0 and result.stdout.strip():
            return True
    return False


def check(path: Path) -> int:
    lines = _read_changelog(path)
    block = _find_latest_version_block(lines)
    if block is None:
        print(f"{path}: no version block found; nothing to check", file=sys.stderr)
        return 0

    header = block[0] if block else "???"
    print(f"check_changelog_honesty: checking {header.strip()}")

    violations: list[tuple[str, str, str]] = []
    in_deletion_section = False

    for raw in block[1:]:
        # Section-level opt-out: bullets under a "### Removed" header
        # talk about things that no longer exist — we don't fact-check
        # them by file existence.
        stripped = raw.lstrip()
        if stripped.startswith("### "):
            in_deletion_section = any(stripped.startswith(h) for h in _DELETION_SECTION_HEADERS)
            continue

        # Skip block quotes and preformatted fenced blocks — those are
        # prose corrections, not claims about source state.
        if stripped.startswith(">"):
            continue
        if _OPT_OUT_TOKEN in raw:
            continue

        # Markdown links ``[text](path)``: prefer to check the link
        # target, not the link text. We rewrite the line by replacing
        # the match with the target only, so the backtick extractor
        # below only sees the target.
        for md_text, md_target in _MD_LINK.findall(raw):
            if _is_pathy(md_target):
                fs_path = _normalise_path(md_target)
                if not _path_exists(fs_path):
                    if "*" in fs_path or "?" in fs_path:
                        continue
                    violations.append((raw.strip(), fs_path, "path does not exist"))

        for hit in _extract_backticked(raw):
            hit = hit.strip()
            if not hit:
                continue

            if _is_pathy(hit):
                if in_deletion_section:
                    # Under ### Removed, missing paths are the expected
                    # state. Skip the existence check.
                    continue
                fs_path = _normalise_path(hit)
                if not _path_exists(fs_path):
                    # Allow some referenced paths that may be inside
                    # comments or grep patterns (e.g. ``tests/runtime/tsan/*``
                    # is a directory glob, not a file).
                    if "*" in fs_path or "?" in fs_path:
                        continue
                    violations.append((raw.strip(), fs_path, "path does not exist"))
                continue

            if _looks_like_symbol(hit):
                if in_deletion_section:
                    continue
                sym = hit.split("(", 1)[0].rstrip("*")  # drop fn-call parens
                if not _grep_symbol(sym):
                    violations.append((raw.strip(), sym, "symbol not found in source tree"))
                continue

    if violations:
        print("")
        print(f"check_changelog_honesty: {len(violations)} honesty violation(s):")
        for bullet, target, reason in violations:
            snippet = bullet[:80] + ("…" if len(bullet) > 80 else "")
            print(f"  - `{target}`: {reason}")
            print(f"    in: {snippet}")
        print("")
        print(
            "Every CHANGELOG claim must point to a file or symbol that "
            "exists in the tree at commit time. If the bullet is "
            "documenting a rename/removal, prefix it with "
            f"``{_OPT_OUT_TOKEN}`` to opt out.",
            file=sys.stderr,
        )
        return 1

    print("check_changelog_honesty: clean")
    return 0


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path("CHANGELOG.md")
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 2
    return check(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
