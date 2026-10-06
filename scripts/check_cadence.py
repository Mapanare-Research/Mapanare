#!/usr/bin/env python3
"""scripts/check_cadence.py — informational panel-cadence reminder.

History
-------
v5.24.0 Hy.3 introduced this script as an enforcing gate that exited
1 when ≥5 minor versions had passed since the last panel directory
under ``.reviews/``. By v5.33.1 the gate was firing on every push
(5 minors past the v5.28.0 panel) and blocking CI.

v5.33.2 Cd.1 demotes the gate to **informational only**: the script
ALWAYS exits 0. It still prints a REMINDER line in CI logs when the
lag is past the threshold so the cadence stays visible — but the
lead drives review timing, not a script. See
``feedback_no_forced_cadence_gates`` in user memory for the
rationale.

Behavior
--------
- exit 0 always.
- ``OK`` line if within cadence (lag < 5 minor versions).
- ``REMINDER`` line if past threshold — informational only; never
  fails CI, never blocks a release.
- ``no prior panel`` line if no panel history found.

Distinction from other gates: doc-drift / changelog-honesty /
fixed-point line-count gates ENFORCE artifact correctness and stay
hard. This one tracks a human scheduling decision, so it's a
reminder, not a gate.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

# How many minor versions can pass before the REMINDER kicks in.
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
        print("check_cadence: no prior panel found in .reviews/ (informational)")
        return 0

    minors_since = (current[0] - last_panel[0]) * 100 + (current[1] - last_panel[1])

    last_str = f"v{last_panel[0]}.{last_panel[1]}.{last_panel[2]}"
    next_panel = f"v{last_panel[0]}.{last_panel[1] + PANEL_INTERVAL_MINORS}.0"

    if minors_since >= PANEL_INTERVAL_MINORS:
        print(
            f"check_cadence: REMINDER — {minors_since} minor versions "
            f"since last panel ({last_str})"
        )
        print(
            f"  Per .reviews/REVIEW_CADENCE.md, a full 7-reviewer "
            f"panel was suggested at {next_panel}."
        )
        print("  Informational only — lead drives review timing.")
        return 0

    print(
        f"check_cadence: OK ({minors_since} minor versions since "
        f"{last_str}; next reminder at {next_panel})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
