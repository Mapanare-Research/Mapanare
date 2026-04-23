#!/usr/bin/env python3
"""v5.4.2 Phase 5: baseline-comparison gate for the LSan golden sweep.

Reads two TSVs:
  1. The run's summary (default: /tmp/asan-leak/asan-leak-summary.tsv).
  2. The committed baseline (docs/roadmap/v5/v5.4.2/baseline/
     asan-leak-baseline.tsv).

Exits 0 iff, for every golden that is CLEAN or LEAK in both files:
  - A CLEAN-in-baseline golden remains CLEAN in the run.
  - A LEAK-in-baseline golden's leak_count does NOT exceed baseline.
  - A LEAK-in-baseline golden may improve (fewer leaks, or CLEAN).

Exits non-zero on any regression. New goldens (not in baseline) are
allowed if CLEAN, flagged if LEAK (the baseline must be updated).

COMPILE_FAIL / LINK_FAIL / RUN_FAIL classes are informational only —
they live in the UAF / pytest gates, not this leak gate. RUN_FAIL is
treated as ERROR (the harness couldn't execute the golden at all,
which likely masked a real leak).

Usage:
    python3 scripts/check_leak_summary.py [RUN_TSV] [BASELINE_TSV]
"""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_RUN = pathlib.Path("/tmp/asan-leak/asan-leak-summary.tsv")
DEFAULT_BASELINE = (
    ROOT / "docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv"
)


def load_tsv(path: pathlib.Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        sys.exit(f"ERROR: {path} not found")
    out: dict[str, dict[str, str]] = {}
    with path.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[row["test"]] = row
    return out


def main() -> int:
    run_path = pathlib.Path(
        sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RUN
    )
    baseline_path = pathlib.Path(
        sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASELINE
    )

    run = load_tsv(run_path)
    baseline = load_tsv(baseline_path)

    regressions: list[str] = []
    improvements: list[str] = []
    unknown: list[str] = []

    def _int(v: str) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    for name, row in sorted(run.items()):
        cls = row["class"]
        leaks = _int(row.get("leak_count", "0"))

        base_row = baseline.get(name)
        if base_row is None:
            # New golden — allowed only if CLEAN (or a known fail class)
            if cls == "LEAK":
                regressions.append(
                    f"  NEW LEAK (not in baseline): {name} "
                    f"({leaks} leaks, {row.get('leak_bytes')} bytes)"
                )
            continue

        base_cls = base_row["class"]
        base_leaks = _int(base_row.get("leak_count", "0"))

        if cls == "RUN_FAIL":
            regressions.append(
                f"  RUN_FAIL: {name} — run harness couldn't execute "
                "(masked leak check)"
            )
            continue

        # Regression: was CLEAN, now LEAK.
        if base_cls == "CLEAN" and cls == "LEAK":
            regressions.append(
                f"  REGRESSED CLEAN→LEAK: {name} "
                f"({leaks} leaks, {row.get('leak_bytes')} bytes)"
            )
            continue

        # Regression: was LEAK N, now LEAK > N.
        if base_cls == "LEAK" and cls == "LEAK" and leaks > base_leaks:
            regressions.append(
                f"  WORSENED LEAK: {name} "
                f"({base_leaks} → {leaks} leaks)"
            )
            continue

        # Improvement: was LEAK, now CLEAN.
        if base_cls == "LEAK" and cls == "CLEAN":
            improvements.append(
                f"  FIXED: {name} (baseline: {base_leaks} leaks)"
            )

        # Improvement: was LEAK N, now LEAK < N.
        if base_cls == "LEAK" and cls == "LEAK" and leaks < base_leaks:
            improvements.append(
                f"  IMPROVED: {name} ({base_leaks} → {leaks} leaks)"
            )

    # Check for goldens in baseline but missing from run.
    for name in sorted(set(baseline) - set(run)):
        unknown.append(f"  MISSING FROM RUN: {name}")

    print(f"Run TSV:      {run_path}")
    print(f"Baseline TSV: {baseline_path}")
    print()

    if improvements:
        print("Improvements (baseline needs update):")
        for line in improvements:
            print(line)
        print()

    if unknown:
        print("Unknowns:")
        for line in unknown:
            print(line)
        print()

    if regressions:
        print("=== FAIL: leak regressions ===")
        for line in regressions:
            print(line)
        print()
        print(
            f"  {len(regressions)} regression(s) — "
            "leak-check gate rejects this run."
        )
        return 1

    print("=== PASS: no leak regressions vs baseline ===")
    if improvements:
        print(
            "  NOTE: consider updating "
            "docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv "
            "to lock in the improvements."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
