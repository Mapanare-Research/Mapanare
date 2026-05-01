#!/usr/bin/env python3
"""Single-shot version bump across every release-relevant surface.

Replaces the manual sweep that used to require editing six files in
five different places, with three different label keys for the badge
across four locale variants. v5.11.2 burned a CI iteration on me
missing two of the four locales (`versao-` / `版本-`).

Surfaces handled:

1. ``VERSION``                   — the source of truth.
2. ``README.md``                 — `version-X.Y.Z` badge.
3. ``docs/README.es.md``         — `version-X.Y.Z` badge (Spanish).
4. ``docs/README.pt.md``         — `versao-X.Y.Z` badge (Portuguese).
5. ``docs/README.zh-CN.md``      — `版本-X.Y.Z` badge (Chinese).
6. ``CHANGELOG.md``              — new ``## [<new>] - <today>``
                                   section between [Unreleased]
                                   and the most recent release;
                                   ``[Unreleased]`` link rebased to
                                   the new version; new comparison
                                   link inserted.

Surfaces NOT handled (intentionally):

- ``pyproject.toml``  — reads version dynamically from VERSION.
- Test count badges  — the actual count is computed from pytest;
                       require running pytest to know the truth.
                       Run ``pytest --collect-only`` and update the
                       badge by hand if drift matters.
- Roadmap / SESSION_REPORT       — historical references, must NOT
                                   be retroactively rewritten.

Usage:
    scripts/bump_version.py 5.11.3
    scripts/bump_version.py 5.11.3 --dry-run
    scripts/bump_version.py 5.11.3 --date 2026-04-29

The CHANGELOG section is created with empty ``### Added`` /
``### Changed`` / ``### Fixed`` placeholders. Fill them in before
committing.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (path, current-badge-regex, replacement-template) tuples for the
# four README badge locales. The Portuguese and Chinese badges use
# localized label keys (`versao-`, `版本-`) instead of `version-`,
# which is exactly the shape that bit me on v5.11.2.
README_BADGES = [
    (
        REPO_ROOT / "README.md",
        re.compile(r"badge/version-\d+\.\d+\.\d+(?:[-.\w]*)-blue"),
        "badge/version-{ver}-blue",
    ),
    (
        REPO_ROOT / "docs/README.es.md",
        re.compile(r"badge/version-\d+\.\d+\.\d+(?:[-.\w]*)-blue"),
        "badge/version-{ver}-blue",
    ),
    (
        REPO_ROOT / "docs/README.pt.md",
        re.compile(r"badge/versao-\d+\.\d+\.\d+(?:[-.\w]*)-blue"),
        "badge/versao-{ver}-blue",
    ),
    (
        REPO_ROOT / "docs/README.zh-CN.md",
        re.compile(r"badge/版本-\d+\.\d+\.\d+(?:[-.\w]*)-blue"),
        "badge/版本-{ver}-blue",
    ),
]

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-.\w]*)?$")

# v5.23.0 RC.3: keep the goldens badge in lockstep with the actual count
# in tests/golden/. Same shape as the version-badge sweep — single regex
# applied to all 4 README locales (the badge label is in English in every
# locale because shields.io has no localization for "goldens").
_GOLDENS_BADGE_RE = re.compile(r"badge/goldens-\d+%2F\d+-brightgreen")
_GOLDEN_DIR = REPO_ROOT / "tests" / "golden"


def _count_goldens() -> int:
    if not _GOLDEN_DIR.exists():
        return 0
    return len(list(_GOLDEN_DIR.glob("*.mn")))


def _read_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(text):
        raise SystemExit(f"VERSION at {path} is malformed: {text!r}")
    return text


def _semver_tuple(v: str) -> tuple[int, int, int]:
    parts = v.split("-", 1)[0].split(".")
    return tuple(int(x) for x in parts[:3])  # type: ignore[return-value]


def _check_increasing(old: str, new: str) -> None:
    if _semver_tuple(new) <= _semver_tuple(old):
        raise SystemExit(
            f"refusing to bump non-forward: {old} -> {new}. " f"Use --force if you really mean it."
        )


def _bump_version_file(new: str, *, dry_run: bool) -> tuple[Path, bool]:
    path = REPO_ROOT / "VERSION"
    new_content = new + "\n"
    if path.read_text(encoding="utf-8") == new_content:
        return (path, False)
    if not dry_run:
        path.write_text(new_content, encoding="utf-8")
    return (path, True)


def _bump_readme_badge(
    path: Path, regex: re.Pattern[str], template: str, new: str, *, dry_run: bool
) -> tuple[Path, bool]:
    if not path.exists():
        return (path, False)
    text = path.read_text(encoding="utf-8")
    replacement = template.format(ver=new)
    new_text, n = regex.subn(replacement, text)
    if n == 0 or new_text == text:
        return (path, False)
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return (path, True)


def _bump_goldens_badge(path: Path, count: int, *, dry_run: bool) -> tuple[Path, bool]:
    if not path.exists():
        return (path, False)
    text = path.read_text(encoding="utf-8")
    replacement = f"badge/goldens-{count}%2F{count}-brightgreen"
    new_text, n = _GOLDENS_BADGE_RE.subn(replacement, text)
    if n == 0 or new_text == text:
        return (path, False)
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return (path, True)


CHANGELOG_NEW_SECTION = """## [{new}] - {date}

### Added

### Changed

### Fixed

"""

# Compare-link patterns at the bottom of CHANGELOG.md.
UNRELEASED_LINK_RE = re.compile(
    r"^\[Unreleased\]:\s*(\S+)/compare/v(\d+\.\d+\.\d+(?:[-.\w]*)?)\.\.\.HEAD\s*$",
    re.MULTILINE,
)


def _bump_changelog(
    old: str, new: str, date: str, *, dry_run: bool
) -> tuple[Path, bool, list[str]]:
    """Insert a new version section + comparison links.

    Returns (path, modified, warnings).
    """
    path = REPO_ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    warnings: list[str] = []

    # 1. Insert a new ## [X.Y.Z] section right after ## [Unreleased].
    unreleased_marker = "## [Unreleased]\n"
    if unreleased_marker not in text:
        # Tolerate a trailing blank line variation.
        unreleased_marker_alt = "## [Unreleased]\r\n"
        if unreleased_marker_alt in text:
            text = text.replace(unreleased_marker_alt, unreleased_marker)
        else:
            raise SystemExit(
                "CHANGELOG.md: cannot find ``## [Unreleased]`` header; " "manual fix required"
            )
    new_section = CHANGELOG_NEW_SECTION.format(new=new, date=date)
    # Avoid double-insertion if the script is rerun.
    if f"## [{new}]" in text:
        warnings.append(f"CHANGELOG.md already has a section for [{new}]; not re-inserting")
    else:
        text = text.replace(
            unreleased_marker,
            unreleased_marker + "\n" + new_section,
            1,
        )

    # 2. Update the [Unreleased] comparison link to compare from the new tag.
    m = UNRELEASED_LINK_RE.search(text)
    if not m:
        warnings.append(
            "CHANGELOG.md: ``[Unreleased]: ...compare/vX.Y.Z...HEAD`` link "
            "not found in expected shape; comparison links not rewritten"
        )
    else:
        url_base = m.group(1)
        prev_unrel_anchor = m.group(2)
        if prev_unrel_anchor != old:
            warnings.append(
                f"CHANGELOG.md: ``[Unreleased]`` was anchored at v{prev_unrel_anchor}, "
                f"not v{old}; rebasing anyway"
            )
        new_unreleased = f"[Unreleased]: {url_base}/compare/v{new}...HEAD"
        text = UNRELEASED_LINK_RE.sub(new_unreleased, text, count=1)

        # 3. Insert a comparison link for the new version right after [Unreleased].
        new_link = f"[{new}]: {url_base}/compare/v{old}...v{new}"
        if f"[{new}]:" in text:
            warnings.append(
                f"CHANGELOG.md already has a comparison link for [{new}]; " "not re-inserting"
            )
        else:
            text = text.replace(
                new_unreleased,
                new_unreleased + "\n" + new_link,
                1,
            )

    if text == path.read_text(encoding="utf-8"):
        return (path, False, warnings)
    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return (path, True, warnings)


def _print_diff_summary(
    changes: list[tuple[Path, bool]], warnings: list[str], *, dry_run: bool
) -> None:
    label = "Would update" if dry_run else "Updated"
    skipped = "Would skip" if dry_run else "Skipped"
    for path, modified in changes:
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        if modified:
            print(f"  [{label}] {rel}")
        else:
            print(f"  [{skipped}] {rel} (no change needed or pattern not found)")
    for w in warnings:
        print(f"  WARNING: {w}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("new_version", help="New version, e.g. 5.11.3")
    ap.add_argument("--dry-run", action="store_true", help="Preview only; touch nothing")
    ap.add_argument(
        "--date",
        default=datetime.date.today().isoformat(),
        help="Release date for the CHANGELOG section (default: today)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Allow non-forward bumps (e.g. for retracting a release)",
    )
    args = ap.parse_args()

    new = args.new_version.lstrip("v")
    if not VERSION_RE.match(new):
        raise SystemExit(f"new_version {new!r} is not a valid semver-shaped string")

    old = _read_version(REPO_ROOT / "VERSION")
    if not args.force:
        _check_increasing(old, new)

    print(f"bump_version: {old} -> {new} ({'dry-run' if args.dry_run else 'live'})")
    changes: list[tuple[Path, bool]] = []
    warnings: list[str] = []

    changes.append(_bump_version_file(new, dry_run=args.dry_run))
    for path, regex, template in README_BADGES:
        changes.append(_bump_readme_badge(path, regex, template, new, dry_run=args.dry_run))

    # v5.23.0 RC.3: goldens badge sweep, parallel to the version-badge sweep.
    goldens_count = _count_goldens()
    print(f"  goldens count: {goldens_count} (from tests/golden/*.mn)")
    for path, _, _ in README_BADGES:
        changes.append(_bump_goldens_badge(path, goldens_count, dry_run=args.dry_run))

    cl_path, cl_modified, cl_warnings = _bump_changelog(old, new, args.date, dry_run=args.dry_run)
    changes.append((cl_path, cl_modified))
    warnings.extend(cl_warnings)

    _print_diff_summary(changes, warnings, dry_run=args.dry_run)

    print()
    print("Next steps:")
    print(f"  1. Fill in the new ## [{new}] section in CHANGELOG.md.")
    print("  2. python3 scripts/check_changelog_honesty.py    # verify claims")
    print("  3. git diff                                      # review")
    print("  4. git add -p && git commit                      # stage selectively")
    print("  5. git tag v{new} && git push --tags             # only when ready".format(new=new))
    if args.dry_run:
        print()
        print("DRY-RUN: no files were modified. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
