#!/usr/bin/env python3
"""v4.105.0 Phase 5 — fail CI if a golden test regresses into the valgrind ERRORS bucket.

Compares a fresh valgrind summary TSV (produced by
``scripts/valgrind_all_goldens.sh``) against the committed baseline at
``docs/roadmap/v4/v4.105.0/artifacts/valgrind-summary.tsv``.

- A test that was CLEAN/WARNINGS_ONLY in the baseline and is now ERRORS
  is a **regression** — exit 1.
- A test that was ERRORS in the baseline and is now CLEAN/WARNINGS_ONLY
  is a **fix** — mention it and exit 0.
- Missing tests (present in baseline but not in fresh, or vice versa)
  are reported but are not failures; they indicate the corpus changed.

Usage:
    check_valgrind_baseline.py <fresh.tsv> <baseline.tsv>
"""

from __future__ import annotations

import sys
from pathlib import Path


def _load(path: Path) -> dict[str, str]:
    """Read a valgrind summary TSV, returning {test_name: class}."""
    out: dict[str, str] = {}
    with path.open() as f:
        header = f.readline().strip().split("\t")
        try:
            ti = header.index("test")
            ci = header.index("class")
        except ValueError:
            sys.exit(f"error: {path} missing 'test' or 'class' column")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(ti, ci):
                continue
            out[parts[ti]] = parts[ci]
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    fresh = _load(Path(sys.argv[1]))
    base = _load(Path(sys.argv[2]))

    regressions: list[tuple[str, str, str]] = []
    fixes: list[tuple[str, str, str]] = []
    for name in sorted(set(fresh) | set(base)):
        fc = fresh.get(name, "ABSENT")
        bc = base.get(name, "ABSENT")
        # A regression: fresh is ERRORS, baseline wasn't ERRORS.
        if fc == "ERRORS" and bc != "ERRORS":
            regressions.append((name, bc, fc))
        # A fix: fresh is not ERRORS, baseline was ERRORS.
        elif bc == "ERRORS" and fc not in {"ERRORS", "ABSENT"}:
            fixes.append((name, bc, fc))

    if fixes:
        print(f"valgrind FIXES ({len(fixes)}):")
        for name, bc, fc in fixes:
            print(f"  {name}: {bc} -> {fc}")

    if regressions:
        print(f"valgrind REGRESSIONS ({len(regressions)}) — FAIL:")
        for name, bc, fc in regressions:
            print(f"  {name}: {bc} -> {fc}")
        return 1

    fresh_err = sum(1 for v in fresh.values() if v == "ERRORS")
    base_err = sum(1 for v in base.values() if v == "ERRORS")
    print(f"valgrind baseline: {base_err} ERRORS (committed) | {fresh_err} ERRORS (fresh) — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
