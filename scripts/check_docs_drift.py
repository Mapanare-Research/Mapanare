#!/usr/bin/env python3
"""scripts/check_docs_drift.py — v4.31.0 Phase 3.2.

Extracts every Mapanare code block from ``docs/SPEC.md``,
``docs/cookbook.md``, ``docs/reference.md``, and
``docs/getting-started.md``, and feeds each one through the Mapanare
parser. Any block that does not parse is a documentation drift bug —
the SPEC promises syntax the parser does not accept.

Why this script exists
----------------------

The v4.26.0 seven-reviewer panel flagged docs drift as a parallel
failure mode to the hollow-features regression. The SPEC was 26
versions stale at v4.26.0; multiple code blocks used syntax that had
been removed or renamed since v3.47.0. Readers following the SPEC got
parse errors on their first sample program.

Scope
-----

- A *code block* is an RFC 7763 fenced block introduced by a line
  starting with ``` ``` ``` and a language tag of ``mn`` or
  ``mapanare``. Anything else (``` ```python ```, ``` ```bash ```,
  etc.) is skipped.
- Blocks marked with an HTML comment ``<!-- pseudo -->`` on the line
  immediately above the opening fence are skipped. Use this for
  intentionally-illustrative pseudocode.
- Blocks marked with ``<!-- expect-error -->`` must NOT parse — they
  pin the negative examples, e.g. "here is the rejected syntax."

The script reports the file, the line number of the opening fence,
and the parser error. Exit code 0 on clean, 1 on any failure.

Usage
-----

    python3 scripts/check_docs_drift.py
    python3 scripts/check_docs_drift.py docs/SPEC.md
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_DOCS = (
    "docs/SPEC.md",
    "docs/cookbook.md",
    "docs/reference.md",
    "docs/getting-started.md",
)

_MN_LANGS = {"mn", "mapanare", "mapa"}

_PSEUDO_MARKER = "<!-- pseudo -->"
_EXPECT_ERROR_MARKER = "<!-- expect-error -->"


def _extract_blocks(path: Path) -> list[tuple[int, str, bool]]:
    """Return a list of ``(start_line, source, expect_error)`` tuples.

    ``start_line`` is 1-indexed and points at the opening fence.
    ``expect_error`` is ``True`` if the block is marked with the
    ``<!-- expect-error -->`` comment.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[int, str, bool]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped.startswith("```"):
            i += 1
            continue
        lang = stripped[3:].strip().split()[0] if len(stripped) > 3 else ""
        if lang not in _MN_LANGS:
            i += 1
            continue

        # Peek upward for the pseudo / expect-error markers.
        look_back = max(0, i - 3)
        above = "\n".join(lines[look_back:i])
        if _PSEUDO_MARKER in above:
            i += 1
            continue
        expect_error = _EXPECT_ERROR_MARKER in above

        # Consume until the closing fence.
        j = i + 1
        body: list[str] = []
        while j < len(lines) and not lines[j].strip().startswith("```"):
            body.append(lines[j])
            j += 1
        blocks.append((i + 1, "\n".join(body), expect_error))
        i = j + 1
    return blocks


def _parse_block(source: str) -> tuple[bool, str]:
    """Return ``(ok, error_message)``. ``ok`` is True on clean parse."""
    from mapanare.parser import ParseError, parse

    try:
        parse(source, filename="<docs>")
        return True, ""
    except ParseError as exc:
        return False, str(exc)
    except Exception as exc:  # pragma: no cover — parser internals
        return False, f"{type(exc).__name__}: {exc}"


def check_file(path: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    blocks = _extract_blocks(path)
    for start_line, source, expect_error in blocks:
        ok, err = _parse_block(source)
        if expect_error:
            if ok:
                violations.append(
                    (
                        path,
                        start_line,
                        "block marked <!-- expect-error --> parsed cleanly",
                    )
                )
        else:
            if not ok:
                first_err = err.splitlines()[0] if err else "parse error"
                violations.append((path, start_line, first_err))
    return violations


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv[1:]] if len(argv) > 1 else [Path(p) for p in DEFAULT_DOCS]
    total_violations = 0
    total_blocks = 0
    checked_files = 0
    for path in files:
        if not path.exists():
            print(f"warning: {path} does not exist, skipping", file=sys.stderr)
            continue
        checked_files += 1
        blocks = _extract_blocks(path)
        total_blocks += len(blocks)
        viols = check_file(path)
        for p, lineno, msg in viols:
            print(f"{p}:{lineno}: docs drift — {msg}")
        total_violations += len(viols)

    if total_violations:
        print("")
        print(
            f"check_docs_drift: {total_violations} docs drift violation(s) "
            f"across {checked_files} file(s) ({total_blocks} block(s) checked).",
            file=sys.stderr,
        )
        print(
            "If a block is intentionally illustrative, prefix it with "
            "``<!-- pseudo -->`` on the line immediately above the "
            "opening fence. If it is a negative example (rejected "
            "syntax), use ``<!-- expect-error -->``.",
            file=sys.stderr,
        )
        return 1

    print(f"check_docs_drift: clean ({total_blocks} block(s) across " f"{checked_files} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
