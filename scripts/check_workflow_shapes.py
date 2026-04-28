#!/usr/bin/env python3
"""Static lint for .github/workflows/*.yml — catches bug classes that
cost iteration time when caught only by Windows-runner CI.

Currently catches:

1. Bare-mnc-redirect (Pk.2.dx class).
   After v5.9.1 DX.5 made `mnc <file.mn>` compile-and-run by default,
   any workflow command of the shape

       <mnc-binary> <something>.mn > <something.ll>

   that omits the explicit `emit-llvm` subcommand will compile +
   execute the program and discard the IR. On Windows this manifests
   as `out of memory (requested 7011361785666170466 bytes)` — the
   no-args dispatch reads garbage path bytes as a size_t.

   This bug class burned two CI iterations during v5.11.2:
     - publish.yml:594 (Wb.1.dx stage2->stage3 self-validate)
     - publish.yml:733 (post-build smoke test)

   Both would have been caught here in <1s on the first push.

Wire-up: add as a step in ci.yml, AFTER the changelog honesty gate
and BEFORE any build steps. Runs in milliseconds.

Usage:
    python3 scripts/check_workflow_shapes.py
    python3 scripts/check_workflow_shapes.py --workflow .github/workflows/publish.yml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Subcommands that are safe before a .mn file argument. Anything else
# is the implicit-run dispatch and will misbehave under stdout
# redirect.
_SAFE_SUBCOMMANDS = (
    "emit-llvm",
    "emit-c",
    "emit-wasm",
    "emit-mir",
    "compile",
    "build",
    "run",
    "cache",
    "lsp",
    "fmt",
    "init",
    "check",
    "lint",
    "transpile",
    "bind",
    "doc",
    "test",
    "version",
    "--version",
    "--help",
    "-h",
    "help",
    "deploy",
    "migrate",
    "targets",
    "build-multi",
    "install",
    "publish",
    "search",
    "login",
)

# Tokens that look like an mnc binary invocation. Conservative — we
# look for the shape "<something containing 'mnc'><whitespace><.mn
# path>" in shell context.
_MNC_BINARY_RE = re.compile(
    r"""
    (?P<binary>
        (?:
            \./[^\s'"]*mnc[^\s'"]*       # ./mnc-stage1 / ./mnc.exe / ./mnc-win-x64.exe
            | \./[^\s'"]*\$\{\{\s*matrix\.artifact\s*\}\}[^\s'"]*  # ./${{ matrix.artifact }}
            | \./mapanare/self/mnc[^\s'"]*
        )
    )
    \s+
    (?P<args>[^>|;&\n]*?)               # everything between binary and redirect
    \s*>(?!\s*&)                        # stdout redirect (not 2>&1, not >>)
    \s*(?P<target>[^\s|;&\n]+)
    """,
    re.VERBOSE,
)

_MN_FILE_RE = re.compile(r"\b[\w./{}\-${}\\]+\.mn\b")


def _line_has_subcommand(args_segment: str) -> str | None:
    """Return the matched safe subcommand token, or None.

    The args_segment is everything between the mnc binary path and
    the `>` redirect. We tokenize on whitespace and check whether
    any token is a known subcommand. We require the subcommand to
    appear BEFORE any .mn file path in the token sequence — putting
    `emit-llvm` after the file is wrong.
    """
    tokens = args_segment.split()
    for tok in tokens:
        # Strip surrounding shell quotes that argparse-style splits keep.
        clean = tok.strip("'\"")
        if clean in _SAFE_SUBCOMMANDS:
            return clean
        if _MN_FILE_RE.search(clean):
            # Hit the .mn arg before any subcommand — implicit-run dispatch.
            return None
    return None


def _is_comment_line(line: str) -> bool:
    stripped = line.lstrip()
    # YAML key prefixes (`run: |` etc.) are followed by raw shell on
    # subsequent lines, but at this point we've been handed the raw
    # shell line via `_extract_shell_lines` below so we only need to
    # handle shell-level `#` comments.
    return stripped.startswith("#") or stripped.startswith("//")


def _scan_line(path: Path, lineno: int, line: str) -> list[tuple[Path, int, str, str]]:
    """Return a list of (path, lineno, line, reason) for any violations
    on this single shell line.
    """
    violations: list[tuple[Path, int, str, str]] = []
    if _is_comment_line(line):
        return violations
    if "<!-- no-check-shape -->" in line:
        return violations

    for m in _MNC_BINARY_RE.finditer(line):
        args = m.group("args")
        target = m.group("target")
        # If the redirect target isn't .ll-shaped or stdout-discard,
        # this is probably not "I want IR" — skip. Common cases:
        # `> /dev/null` (intentional discard, harmless), `> log.txt`
        # (logging). We only flag the IR-redirect shape.
        target_clean = target.strip("'\"")
        if not target_clean.endswith(".ll"):
            continue
        if not _MN_FILE_RE.search(args):
            # No .mn file in the args; not the shape we're checking.
            continue
        sub = _line_has_subcommand(args)
        if sub is None:
            violations.append(
                (
                    path,
                    lineno,
                    line.rstrip(),
                    "bare `mnc <file>.mn > out.ll` shape: post-v5.9.1 DX.5 "
                    "this compiles+runs the program and discards IR. Add the "
                    "explicit `emit-llvm` subcommand before the .mn file.",
                )
            )
    return violations


def _extract_shell_lines(yml_text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) tuples for lines that look like shell.

    We treat every non-blank line as potentially shell — the YAML
    parser doesn't help us much here because `run: |` blocks contain
    raw shell as YAML scalar contents. The regex-based scan is robust
    to both inline `run:` and block `run: |` shapes.
    """
    out: list[tuple[int, str]] = []
    for lineno, raw in enumerate(yml_text.splitlines(), start=1):
        if not raw.strip():
            continue
        out.append((lineno, raw))
    return out


def check_workflow(path: Path) -> list[tuple[Path, int, str, str]]:
    text = path.read_text(encoding="utf-8")
    violations: list[tuple[Path, int, str, str]] = []
    for lineno, line in _extract_shell_lines(text):
        violations.extend(_scan_line(path, lineno, line))
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--workflow",
        type=Path,
        default=None,
        help="Single workflow file to check (default: all .github/workflows/*.yml)",
    )
    args = ap.parse_args()

    if args.workflow:
        targets = [args.workflow]
    else:
        wf_dir = Path(".github/workflows")
        if not wf_dir.is_dir():
            print(
                f"check_workflow_shapes: {wf_dir} not found; nothing to check",
                file=sys.stderr,
            )
            return 0
        targets = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml"))

    all_violations: list[tuple[Path, int, str, str]] = []
    for path in targets:
        all_violations.extend(check_workflow(path))

    if not all_violations:
        print(f"check_workflow_shapes: {len(targets)} workflow(s) clean")
        return 0

    print(
        f"check_workflow_shapes: {len(all_violations)} violation(s) across "
        f"{len(targets)} workflow(s):",
        file=sys.stderr,
    )
    for path, lineno, line, reason in all_violations:
        snippet = line.strip()
        if len(snippet) > 110:
            snippet = snippet[:107] + "..."
        print(f"  {path}:{lineno}: {reason}", file=sys.stderr)
        print(f"    {snippet}", file=sys.stderr)
    print(
        "\nHint: add `emit-llvm` before the .mn file, OR add "
        "`<!-- no-check-shape -->` on the same line to opt out "
        "(if the implicit-run dispatch is intentional).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
