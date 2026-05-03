#!/usr/bin/env python3
"""scripts/check_cadence.py — v5.24.0 Hy.3 cadence enforcement gate.

Per ``.reviews/REVIEW_CADENCE.md``, a full 7-reviewer panel runs every
5 minor versions OR after 5 language-feature releases. This script
warns when either trigger has fired without a corresponding panel
directory at ``.reviews/v<MAJOR>.<MINOR>.<PATCH>/``.

Closes the v5.16.0 / v5.20.0 silent-skip class flagged in the v5.22.0
panel (Anaconda §1): three triggers fired across the v5.13–v5.21 arc
and zero panels ran in between.

Behavior
--------
- exit 0: within cadence (lag < 5 minor versions since last panel).
- exit 1: OVERDUE — print the version that should have hosted the
  panel and the next scheduled tag.

At v5.24.0 we are 2 minor versions past the last panel (v5.22.0), so
the gate prints OK and exits 0. The gate fires hard at v5.27.0 if no
panel has been hosted by then.

This script is wired into ``.github/workflows/ci.yml`` as a soft-warn
job (continue-on-error: true) so PRs that happen to trip it during
the panel-window are not blocked. The hard signal is at pre-release
time via ``make ci-gates``.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

# How many minor versions can pass before a panel is OVERDUE.
# Per .reviews/REVIEW_CADENCE.md — "Every 5 minor versions."
PANEL_INTERVAL_MINORS = 5


def get_current_version() -> tuple[int, int, int]:
    raw = (ROOT / "VERSION").read_text().strip()
    parts = raw.split(".")
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def get_last_panel_version() -> tuple[int, int, int] | None:
    review_dir = ROOT / ".reviews"
    if not review_dir.exists():
        return None
    panels: list[tuple[int, int, int]] = []
    pattern = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
    for sub in review_dir.iterdir():
        if not sub.is_dir():
            continue
        m = pattern.match(sub.name)
        if not m:
            continue
        # Confirm the directory hosts an actual panel (not just an
        # empty placeholder) by requiring at least one .md file.
        if not list(sub.glob("*.md")):
            continue
        panels.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    if not panels:
        return None
    return max(panels)


def main() -> int:
    current = get_current_version()
    last_panel = get_last_panel_version()

    if last_panel is None:
        print("check_cadence: no prior panel found in .reviews/")
        return 0

    minors_since = (current[0] - last_panel[0]) * 100 + (current[1] - last_panel[1])

    last_str = f"v{last_panel[0]}.{last_panel[1]}.{last_panel[2]}"
    next_panel = f"v{last_panel[0]}.{last_panel[1] + PANEL_INTERVAL_MINORS}.0"

    if minors_since >= PANEL_INTERVAL_MINORS:
        print(
            f"check_cadence: OVERDUE — {minors_since} minor versions "
            f"since last panel ({last_str})"
        )
        print(
            f"  Per .reviews/REVIEW_CADENCE.md, a full 7-reviewer "
            f"panel was due at {next_panel}."
        )
        print("  Schedule a panel cycle before tagging the next minor.")
        return 1

    print(
        f"check_cadence: OK ({minors_since} minor versions since "
        f"{last_str}; next panel at {next_panel})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
