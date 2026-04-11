#!/usr/bin/env python3
"""scripts/check_silent_skips.py — v4.29.0 CI gate.

Every ``pytest.mark.skip`` / ``pytest.mark.xfail`` in ``tests/`` must have a
tracking version (``vN.N.N``) either inside the marker's ``reason=`` string
or in a comment on one of the five lines immediately preceding the marker.

A silent skip is a test that does not exist. The v4.18.0–v4.26.0 hollow-
features regression shipped because 79 ``extern "Python" fn`` tests had been
silently ``xfail``'d since v4.2.0; the v4.26.0 seven-reviewer panel flagged
this as the single biggest class of process failure in the release. This
gate stops the next silent skip at PR time.

Rules
-----
- ``pytest.mark.skipif`` is **conditional** and allowed with no comment.
  Environment gates (``HAS_LLVMLITE``, ``mnc-stage1 not built``, etc.)
  are first-class and do not need tracking.
- ``pytest.mark.skip`` and ``pytest.mark.xfail`` (unconditional) **must**
  mention a tracking version in the form ``vN.N.N`` (e.g. ``v4.30.0``)
  **either** in the ``reason=...`` literal **or** in a comment on one of
  the five lines immediately above the marker.
- Assignment-form markers (``X = pytest.mark.xfail(...)``) are checked
  at the assignment site, not at each usage. A named marker is a single
  tracking obligation, not N.
- The ``scripts/`` directory is excluded (this file is itself a script).

Exit 0 on clean; exit 1 on violations with file:line and the rule that
failed printed one per line.

Usage
-----
    python3 scripts/check_silent_skips.py tests/
    python3 scripts/check_silent_skips.py tests/ tests/llvm/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Match a tracking version anywhere: v4.29.0, v4.30.0-rc1, v5.0, v12.3.4.
VERSION_RE = re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b", re.IGNORECASE)

# Lines we scan for the marker itself. We only flag unconditional
# skip/xfail. ``skipif`` is conditional and allowed.
MARKER_RE = re.compile(
    r"""
    (?:@)?                              # optional decorator prefix
    pytest\.mark\.
    (?P<kind>skip|xfail)                # unconditional only
    \s*\(                               # opening paren (required — rules out
                                        # bare ``pytest.mark.skip`` as a
                                        # module-level attribute reference)
    """,
    re.VERBOSE,
)

# How many lines above a marker to scan for a tracking comment.
COMMENT_CONTEXT = 5


def _marker_has_version(lines: list[str], start_idx: int) -> tuple[bool, str]:
    """Return (has_version, where) for the marker that starts at ``start_idx``.

    Scans from ``start_idx`` until the balanced ``)`` closing the marker, so
    the reason string (which may span several lines) counts as part of the
    marker. Also checks ``COMMENT_CONTEXT`` lines above the marker for a
    ``# ... vN.N.N ...`` comment.
    """
    # Balanced-paren scan forward from start_idx.
    depth = 0
    end_idx = start_idx
    in_string = False
    string_char = ""
    started = False
    for i in range(start_idx, len(lines)):
        line = lines[i]
        j = 0
        while j < len(line):
            c = line[j]
            if in_string:
                if c == "\\":
                    j += 2
                    continue
                if c == string_char:
                    in_string = False
                j += 1
                continue
            if c in ('"', "'"):
                # Triple-string handling: treat ''' and """ as a block.
                if line[j : j + 3] in ('"""', "'''"):
                    triple = line[j : j + 3]
                    # Look for closing triple on this or later lines.
                    k = j + 3
                    found = False
                    ii = i
                    while ii < len(lines):
                        rest = lines[ii][k:] if ii == i else lines[ii]
                        pos = rest.find(triple)
                        if pos != -1:
                            if ii == i:
                                j = k + pos + 3
                            else:
                                # Skip to that line; continue outer loop.
                                i = ii  # noqa: PLW2901 — intentional
                                line = lines[i]
                                j = pos + 3
                            found = True
                            break
                        ii += 1
                    if not found:
                        # Malformed; bail out of this marker.
                        return False, ""
                    continue
                in_string = True
                string_char = c
                j += 1
                continue
            if c == "(":
                depth += 1
                started = True
            elif c == ")":
                depth -= 1
                if started and depth == 0:
                    end_idx = i
                    body = "\n".join(lines[start_idx : end_idx + 1])
                    if VERSION_RE.search(body):
                        return True, "reason-or-args"
                    # Check preceding comment window.
                    lo = max(0, start_idx - COMMENT_CONTEXT)
                    for k in range(lo, start_idx):
                        stripped = lines[k].strip()
                        if stripped.startswith("#") and VERSION_RE.search(stripped):
                            return True, f"comment-above:L{k + 1}"
                    return False, ""
            j += 1
    # Never closed — treat as no version (caller reports it).
    return False, ""


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return a list of ``(lineno, kind, context)`` for each silent skip."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    lines = text.splitlines()
    violations: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        m = MARKER_RE.search(line)
        if not m:
            continue
        # Quick filter: skipif is conditional and allowed.
        if re.search(r"pytest\.mark\.skipif\b", line):
            continue
        ok, _where = _marker_has_version(lines, i)
        if not ok:
            kind = m.group("kind")
            snippet = line.strip()[:80]
            violations.append((i + 1, kind, snippet))
    return violations


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: check_silent_skips.py <dir> [<dir> ...]",
            file=sys.stderr,
        )
        return 2

    roots = [Path(a) for a in argv[1:]]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            print(f"error: {root} does not exist", file=sys.stderr)
            return 2
        if root.is_file():
            files.append(root)
        else:
            files.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)

    total_violations = 0
    for path in sorted(files):
        for lineno, kind, snippet in scan_file(path):
            total_violations += 1
            print(
                f"{path}:{lineno}: silent pytest.mark.{kind} — "
                f"no tracking version (vN.N.N) in reason or preceding comment"
            )
            print(f"    {snippet}")

    if total_violations:
        print("")
        print(
            f"check_silent_skips: {total_violations} silent skip(s) found. "
            "Add a comment like ``# v4.30.0: reason this test is skipped`` "
            "immediately above the marker, OR include the tracking version "
            "in the marker's reason= string.",
            file=sys.stderr,
        )
        return 1

    print("check_silent_skips: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
