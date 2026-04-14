#!/usr/bin/env python3
"""v4.105.0 Phase 5 — fail CI if a golden test regresses into the ASan ASAN_ERROR bucket.

Compares a fresh ASan summary TSV (produced by
``scripts/run_asan_goldens.sh``) against the committed baseline at
``docs/roadmap/v4/v4.105.0/artifacts/asan-summary.tsv``.

- A test that was CLEAN in the baseline and is now ASAN_ERROR is a
  **regression** — exit 1.
- A test that was ASAN_ERROR in the baseline and is now CLEAN is a
  **fix** — mention it and exit 0.

Usage:
    check_asan_baseline.py <fresh.tsv> <baseline.tsv>
"""
from __future__ import annotations

import sys
from pathlib import Path


def _load(path: Path) -> dict[str, str]:
    """Read the ASan summary TSV, returning {test_name: class}."""
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
        if fc == "ASAN_ERROR" and bc != "ASAN_ERROR":
            regressions.append((name, bc, fc))
        elif bc == "ASAN_ERROR" and fc not in {"ASAN_ERROR", "ABSENT"}:
            fixes.append((name, bc, fc))

    if fixes:
        print(f"ASan FIXES ({len(fixes)}):")
        for name, bc, fc in fixes:
            print(f"  {name}: {bc} -> {fc}")

    if regressions:
        print(f"ASan REGRESSIONS ({len(regressions)}) — FAIL:")
        for name, bc, fc in regressions:
            print(f"  {name}: {bc} -> {fc}")
        return 1

    fresh_err = sum(1 for v in fresh.values() if v == "ASAN_ERROR")
    base_err = sum(1 for v in base.values() if v == "ASAN_ERROR")
    print(f"ASan baseline: {base_err} ERRORS (committed) | {fresh_err} ERRORS (fresh) — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
