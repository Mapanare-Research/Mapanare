"""v5.25.0 Pv.6 — publish-pipeline smoke fixture parse gate.

Locks every ``.mn`` fixture authored inline in
``.github/workflows/publish.yml`` against a parse-time regression.

Closes the publish-run-#48 failure mode: the Hy.5 (v5.24.0) Linux +
macOS tarball-smoke jobs authored ``fn main(): print("...")`` —
single-line colon syntax that was the v5.14.0 SPEC §1009 forward
promise but was rescoped to v6.0 by v5.21.1 H.4. The fixture parsed
on no shipping release and broke on every publish until v5.25.0
fixed it.

This test extracts every inline ``.mn`` fixture from publish.yml
(four shapes: ``echo`` single-quoted, ``printf`` with ``\\n``
escapes, PowerShell here-string, and the bash heredoc form
reserved for future workflow edits) and parses each through
``mapanare.parser.parse``. Any future fixture authored against an
unshipped feature trips the gate at PR time.

Falsifiability: stash the v5.25.0 publish.yml edit and the test
fails with the same parse error as publish run #48. Restore and
the test passes.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from mapanare.parser import parse

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "publish.yml"

# --- bash echo: ``echo '<body>' > <name>.mn``
ECHO_RE = re.compile(
    r"echo\s+'([^']*)'\s*>\s*(\S+\.mn)\b",
)

# --- bash printf: ``printf '<body with \n escapes>' [\n] > <name>.mn``.
# The ``\\?\s*\n?`` block accepts both inline and line-continued forms.
PRINTF_RE = re.compile(
    r"printf\s+'([^']*)'\s*\\?\s*\n?\s*>\s*(\S+\.mn)\b",
)

# --- PowerShell here-string: ``@" ... "@ | Out-File <name>.mn``
PWSH_RE = re.compile(
    r'@"\s*\n(.*?)\n\s*"@\s*\|\s*Out-File\s+(\S+\.mn)\b',
    re.DOTALL,
)

# --- bash heredoc: ``cat > <name>.mn <<EOF ... EOF`` (none today,
# locked for future workflow edits).
HEREDOC_RE = re.compile(
    r"cat\s*>\s*(\S+\.mn)\s*<<['\"]?(\w+)['\"]?\s*\n(.*?)\n\s*\2\b",
    re.DOTALL,
)


def _decode_printf_escapes(s: str) -> str:
    """Translate the escape sequences printf actually honors here.

    Only ``\\n`` and ``\\t`` are used in current fixtures; expand the
    table only when a fixture requires it (Pv.6 mvp scope).
    """
    return s.replace(r"\n", "\n").replace(r"\t", "\t")


def _extract_fixtures(src: str) -> list[tuple[str, str]]:
    """Return ``[(target_name, mn_body), ...]`` for every fixture.

    Each shape matched separately so a malformed match in one form
    does not silently swallow another.
    """
    fixtures: list[tuple[str, str]] = []

    for body, target in ECHO_RE.findall(src):
        fixtures.append((target, body + "\n"))

    for body, target in PRINTF_RE.findall(src):
        fixtures.append((target, _decode_printf_escapes(body)))

    for body, target in PWSH_RE.findall(src):
        # PowerShell here-strings preserve indentation as written —
        # YAML's leading column has been baked into the body. Dedent
        # so the .mn parser sees column-0 ``fn``.
        fixtures.append((target, textwrap.dedent(body) + "\n"))

    for target, _label, body in HEREDOC_RE.findall(src):
        fixtures.append((target, textwrap.dedent(body) + "\n"))

    return fixtures


def test_fixtures_are_extractable():
    """Sanity: at least one fixture must be found.

    A regex update that silently drops every fixture would otherwise
    pass the parse loop trivially. This guards against that class.
    """
    src = WORKFLOW.read_text()
    fixtures = _extract_fixtures(src)
    assert fixtures, (
        "No .mn fixtures extracted from publish.yml — regex stale? "
        "Check ECHO_RE / PRINTF_RE / PWSH_RE / HEREDOC_RE."
    )
    # As of v5.25.0: 1 PowerShell + 1 echo + 2 printf + 1 PowerShell = 5.
    # If this drops below 4 a pattern likely regressed — investigate.
    assert len(fixtures) >= 4, (
        f"only {len(fixtures)} fixture(s) extracted; expected >= 4 "
        f"(2 PowerShell + 1 echo + 2 printf). Targets: "
        f"{[t for t, _ in fixtures]}"
    )


def test_every_publish_smoke_fixture_parses():
    """Every inline .mn fixture must parse via the Python bootstrap."""
    src = WORKFLOW.read_text()
    fixtures = _extract_fixtures(src)
    failures: list[str] = []
    for target, body in fixtures:
        try:
            parse(body, filename=target)
        except Exception as e:  # noqa: BLE001 — surface any parse failure
            failures.append(
                f"{target!r} would fail at publish-time:\n"
                f"---\n{body}---\n→ {type(e).__name__}: {e}"
            )
    if failures:
        pytest.fail("publish.yml has unparseable .mn fixture(s):\n\n" + "\n\n".join(failures))
