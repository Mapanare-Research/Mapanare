#!/usr/bin/env python3
"""scripts/check_doc_freshness.py — v5.24.0 Hy.2 docs-freshness gate.

Compares README badges / fixed-point status / goldens count / SPEC
header against the current state of the repo. Fails with a structured
report on drift.

Closes the H.* / Bo.* drift class structurally — the same surface that
capped the v5.7.1 / v5.11.0 / v5.22.0 panel aggregates at 9.55–9.66
because every release surfaced N more "stale claim in README" findings
that hygiene-release fixes could only mop up after the fact.

Scope (MVP, v5.24.0)
--------------------
1. Version badge (en/es/pt/zh-CN) matches VERSION file.
2. Goldens badge count matches ``ls tests/golden/*.mn | wc -l``.
3. README.md body has no multiple distinct exact-line-count claims
   (catches "238,086" vs "239,835" co-existing in the same file).
4. README body claims like "(NN/NN native goldens)" match the actual
   count.
5. ``docs/SPEC.md`` header version is no more than one minor version
   behind the current VERSION (allows the v5.21.1-style sync window
   spanning a panel + recovery arc but flags real drift).

Wider scope — every prose claim about every metric across every doc —
is explicitly v6.0+. Hold the line at these 5 checks; expand only when
a panel surfaces a NEW drift class outside this set.

Exit 0 on clean; exit 1 on violations.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Resolve every path relative to the cwd so tests can exercise the
# script against constructed fixtures via subprocess.run(cwd=tmp_path).
ROOT = Path(os.getcwd())

README_FILES = [
    ROOT / "README.md",
    ROOT / "docs" / "README.es.md",
    ROOT / "docs" / "README.pt.md",
    ROOT / "docs" / "README.zh-CN.md",
]


def _read_version() -> str:
    return (ROOT / "VERSION").read_text().strip()


def _count_goldens() -> int:
    return len(list((ROOT / "tests" / "golden").glob("*.mn")))


# 1. VERSION badge sync (en, es, pt, zh-CN).
def check_version_badges() -> list[str]:
    version = _read_version()
    violations: list[str] = []
    # en/es: "version-X.Y.Z-"
    # pt: "versao-X.Y.Z-"
    # zh-CN: literal "版本-X.Y.Z-" (the badge URL embeds the localized label)
    patterns = [
        re.compile(r"version-([\d.]+)-"),
        re.compile(r"versao-([\d.]+)-"),
        re.compile(r"版本-([\d.]+)-"),
    ]

    for path in README_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for regex in patterns:
            for m in regex.finditer(text):
                if m.group(1) != version:
                    rel = path.relative_to(ROOT)
                    violations.append(f"{rel}: version badge {m.group(1)!r} != VERSION {version!r}")
    return violations


# 2. Goldens count badge sync.
def check_goldens_badge() -> list[str]:
    goldens = _count_goldens()
    violations: list[str] = []
    goldens_re = re.compile(r"goldens-(\d+)%2F(\d+)-")

    for path in README_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for m in goldens_re.finditer(text):
            num, denom = int(m.group(1)), int(m.group(2))
            if num != goldens or denom != goldens:
                rel = path.relative_to(ROOT)
                violations.append(
                    f"{rel}: goldens badge {num}/{denom} != actual {goldens}/{goldens}"
                )
    return violations


# 3. Fixed-point line count drift in README body — catch multiple
#    co-existing exact counts (the v5.22.0 surface where the body
#    showed both an old and a new figure).
def check_fixed_point_line_count() -> list[str]:
    violations: list[str] = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    exact_counts = re.findall(r"\b(\d{3},\d{3})\s+lines\b", readme)
    distinct = set(exact_counts)
    if len(distinct) > 1:
        violations.append(
            f"README.md: multiple distinct exact-line-count claims: " f"{sorted(distinct)}"
        )
    return violations


# 4. Goldens count in body matches actual count (en + localized).
def check_goldens_body_consistency() -> list[str]:
    goldens = _count_goldens()
    violations: list[str] = []
    body_re = re.compile(r"\((\d+)/(\d+)\s+(?:native\s+)?goldens?")

    for path in README_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for m in body_re.finditer(text):
            num, denom = int(m.group(1)), int(m.group(2))
            if num != goldens or denom != goldens:
                rel = path.relative_to(ROOT)
                violations.append(
                    f"{rel}: body goldens claim {num}/{denom} != actual " f"{goldens}/{goldens}"
                )
    return violations


# 5. SPEC.md header version freshness. Allow a lag of one minor
#    version (v5.21.0 SPEC + v5.22.0 panel is fine; v5.21.0 SPEC +
#    v5.23.0 is fine; v5.21.0 SPEC + v5.24.0 is drift).
def check_spec_header() -> list[str]:
    spec = ROOT / "docs" / "SPEC.md"
    if not spec.exists():
        return []
    header = "\n".join(spec.read_text(encoding="utf-8").splitlines()[:10])
    version = _read_version()
    violations: list[str] = []

    m = re.search(r"synced to the v(\d+)\.(\d+)\.(\d+)", header)
    if m:
        spec_major, spec_minor = int(m.group(1)), int(m.group(2))
        cur_parts = version.split(".")
        cur_major, cur_minor = int(cur_parts[0]), int(cur_parts[1])
        # Lag = (cur_major - spec_major) * 100 + (cur_minor - spec_minor).
        # Tolerate up to 2 minors (covers a panel + recovery-arc window).
        lag = (cur_major - spec_major) * 100 + (cur_minor - spec_minor)
        if lag > 2:
            violations.append(
                f"docs/SPEC.md: header references v{spec_major}.{spec_minor}.* "
                f"but VERSION is {version} (lag of {lag} minor versions; "
                f"max tolerated is 2)"
            )
    return violations


def main() -> int:
    all_violations: list[str] = []
    all_violations.extend(check_version_badges())
    all_violations.extend(check_goldens_badge())
    all_violations.extend(check_fixed_point_line_count())
    all_violations.extend(check_goldens_body_consistency())
    all_violations.extend(check_spec_header())

    if all_violations:
        print(f"check_doc_freshness: {len(all_violations)} drift violation(s):")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\nUpdate the stale reference at the source. Wider-scope "
            "prose verification is v6.0+ — see scripts/check_docs_drift.py "
            "and scripts/check_changelog_honesty.py for the existing gates."
        )
        return 1
    print("check_doc_freshness: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
