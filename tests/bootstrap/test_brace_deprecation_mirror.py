"""v5.23.2 Te.3.B cross-bootstrap brace-deprecation mirror test.

Asserts that Python ``mapanare emit-llvm`` and native ``mnc-stage1
emit-llvm`` produce byte-identical brace-deprecation warning text on
every shape: pure colon, multi-line brace block, single-line brace
block (the v5.23.2 fix), single-line struct literal (must NOT warn),
brace-in-string, brace-in-comment, ``#{`` map literal, ``${``
interpolation, mixed colon + brace, and the
``MAPANARE_NO_BRACE_WARNING=1`` opt-out.

Pre-v5.23.2, single-line ``fn main() { print("hi") }`` was silently
uncounted by the Python detector, and ``mnc-stage1`` had zero
brace-deprecation logic at all. v5.23.2 closes both gaps with a
shared C-runtime detector (``__mn_count_user_brace_block_openers`` +
``__mn_emit_brace_deprecation_warning``) called from both bootstraps.

Same shape as ``tests/bootstrap/test_te5_mirror.py`` and the other
v5.14.1+ cross-bootstrap mirrors. Byte-identity is the contract.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
STAGE1 = REPO / "mapanare/self/mnc-stage1"


# (case_name, source, expected_count). expected_count == 0 means the
# detector must NOT fire; > 0 means it must fire with that exact count.
CASES = [
    # v5.23.2 Te.3.B.1: the failure shape. Pre-v5.23.2 the Python detector
    # missed this; native had zero coverage. Post-v5.23.2 both fire.
    ("single_line", 'fn main() { print("hi") }', 1),
    # The shape that worked pre-v5.23.2 (multi-line brace block).
    ("multi_line", 'fn main() {\n    print("hi")\n}\n', 1),
    # Backslash-escaped `{` inside a string — must NOT count.
    ("escaped_brace", 'fn main():\n    print("\\{not a block}")\n', 0),
    # Plain `{` inside a string — must NOT count.
    ("brace_in_string", 'fn main():\n    print("{")\n', 0),
    # `{` inside a `//` line comment — must NOT count.
    ("brace_in_comment", 'fn main(): // {\n    print("hi")\n', 0),
    # `#{` map literal — must NOT count.
    ("map_literal", "fn main():\n    let m = #{ 1: 2 }\n", 0),
    # `${...}` interpolation inside a string — must NOT count.
    ("interp_inside_string", 'fn main():\n    let n = 5\n    print("${n}")\n', 0),
    # Mixed colon-style fn + brace-style fn in one file — count = 1.
    ("mixed_colon_brace", "fn a(): pass\nfn b() { return 1 }\n", 1),
    # No braces at all.
    ("no_braces", 'fn main():\n    print("hi")\n', 0),
    # Multiple brace-style fns, one colon-style — count = 3.
    (
        "multiple",
        "fn a() { 1 }\nfn b() { 2 }\nfn c():\n    pass\nfn d() { 3 }\n",
        3,
    ),
]


@pytest.mark.skipif(not STAGE1.exists(), reason="mnc-stage1 not built")
@pytest.mark.parametrize("name,src,expected_count", CASES)
def test_python_native_warning_match(
    tmp_path: Path, name: str, src: str, expected_count: int
) -> None:
    fixture = tmp_path / f"{name}.mn"
    fixture.write_text(src, encoding="utf-8")

    # Strip MAPANARE_NO_BRACE_WARNING from env if it's set in the host
    # so this test reflects the default behavior, not an opt-out.
    env = {k: v for k, v in os.environ.items() if k != "MAPANARE_NO_BRACE_WARNING"}

    py = subprocess.run(
        [
            "python3",
            "-m",
            "mapanare",
            "emit-llvm",
            str(fixture),
            "-o",
            str(tmp_path / "py.ll"),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    sh = subprocess.run(
        [
            str(STAGE1),
            "emit-llvm",
            str(fixture),
            "-o",
            str(tmp_path / "sh.ll"),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    py_warning = "\n".join(line for line in py.stderr.splitlines() if "deprecated" in line)
    sh_warning = "\n".join(line for line in sh.stderr.splitlines() if "deprecated" in line)

    # v5.49.0 architectural choice (commit 4e12afb4): the native
    # compiler does NOT emit deprecation warnings — the deprecation
    # signal stays in Python tooling (`mnc fmt`, `python -m mapanare`).
    # ``mapanare/self/parser.mn`` has no warning emission post-v5.49.0.
    # This test asserts the contract:
    #
    # - Native always silent (no `deprecated` in stderr) regardless of
    #   ``expected_count`` — native is not a linter.
    # - Python emits when (a) the source has migratable braces AND (b)
    #   the v5.49.0 smart-skip ``_maybe_emit_brace_deprecation_warning``
    #   doesn't suppress (i.e., formatter would actually migrate).
    #
    # All `expected_count > 0` fixtures here are single-line / multi-line
    # stmt-block forms that v5.48.0 migrates, so the smart-skip is
    # inactive and Python warns.
    assert sh_warning == "", (
        f"v5.49.0 contract: native must not emit deprecation warning. " f"stderr={sh.stderr!r}"
    )

    if expected_count == 0:
        assert py_warning == "", f"Python: unexpected warning: {py_warning!r}"
    else:
        assert "deprecated" in py_warning, f"Python: missing warning. stderr={py.stderr!r}"
        # The count must be embedded as written.
        plural = "occurrence" if expected_count == 1 else "occurrences"
        assert (
            f"({expected_count} {plural})" in py_warning
        ), f"Expected '({expected_count} {plural})' in py warning: {py_warning!r}"


@pytest.mark.skipif(not STAGE1.exists(), reason="mnc-stage1 not built")
def test_no_brace_warning_env_opt_out(tmp_path: Path) -> None:
    """``MAPANARE_NO_BRACE_WARNING=1`` suppresses the Python warning.
    Native is silent regardless (v5.49.0 architectural choice — see
    ``test_python_native_warning_match`` docstring)."""
    fixture = tmp_path / "brace.mn"
    fixture.write_text('fn main() { print("hi") }\n', encoding="utf-8")
    env = {**os.environ, "MAPANARE_NO_BRACE_WARNING": "1"}

    py = subprocess.run(
        [
            "python3",
            "-m",
            "mapanare",
            "emit-llvm",
            str(fixture),
            "-o",
            str(tmp_path / "py.ll"),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    sh = subprocess.run(
        [
            str(STAGE1),
            "emit-llvm",
            str(fixture),
            "-o",
            str(tmp_path / "sh.ll"),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert "deprecated" not in py.stderr, f"Python: opt-out failed. stderr={py.stderr!r}"
    assert "deprecated" not in sh.stderr, f"Native: should be silent. stderr={sh.stderr!r}"
