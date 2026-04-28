#!/usr/bin/env python3
"""v5.0.6 An.10 — deterministic test counter.

Walks `tests/` and counts every `def test_*(` declaration. Wired into
`make count-tests` so release-note deltas are authoritative rather
than hand-counted.

Why: at v4.144.0, a release note claimed "+27 tests" while Anaconda's
count showed +34 actually landed. Hand-counting across parameterized
classes, conftest fixtures, and skip-markers is unreliable. This
script counts by signature, one number, no ambiguity.

Usage:
    python scripts/count_tests.py              # print total
    python scripts/count_tests.py --by-dir     # group by top-level dir
    python scripts/count_tests.py --path tests/parser  # scope a subtree
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_TEST_ROOT = ROOT / "tests"
TEST_RE = re.compile(r"^\s*def\s+test_\w+\s*\(", re.MULTILINE)


def count_tests(root: pathlib.Path) -> tuple[int, dict[str, int]]:
    """Return (total, by-top-level-dir) tuple."""
    total = 0
    by_dir: dict[str, int] = defaultdict(int)
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        n = len(TEST_RE.findall(py.read_text(encoding="utf-8", errors="replace")))
        total += n
        # Group by first directory under `tests/`
        try:
            rel = py.relative_to(root)
            bucket = rel.parts[0] if len(rel.parts) > 1 else "_root"
        except ValueError:
            bucket = "_other"
        by_dir[bucket] += n
    return total, dict(by_dir)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--path",
        type=pathlib.Path,
        default=DEFAULT_TEST_ROOT,
        help=f"tests directory (default: {DEFAULT_TEST_ROOT})",
    )
    ap.add_argument(
        "--by-dir",
        action="store_true",
        help="print per-subdirectory breakdown",
    )
    args = ap.parse_args()

    if not args.path.exists():
        print(f"error: path not found: {args.path}", file=sys.stderr)
        return 2

    total, by_dir = count_tests(args.path)
    if args.by_dir:
        width = max((len(k) for k in by_dir), default=0)
        for bucket in sorted(by_dir):
            print(f"{bucket:<{width}}  {by_dir[bucket]:>5d}")
        print("-" * (width + 7))
    print(total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
