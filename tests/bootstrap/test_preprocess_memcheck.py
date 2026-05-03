"""v5.25.0 Pv.2 — preprocess valgrind smoke.

Runs ``mnc-stage1 preprocess`` on three fixtures (brace-only,
colon-only, mixed) under valgrind. Locks the brace-only fast-path
contract in ``runtime/native/mapanare_core.c::__mn_indent_to_braces``
against MnString-aliasing regressions: pre-fix (commit ``9dcbbb5``),
the fast path returned the **input MnString aliased**, and every
caller treated the result as a separately drop-tracked String.
Function-end drop glue freed the same buffer twice. Surfaces only
under valgrind / ASan — the user-visible symptom was either silent
heap corruption or an opaque crash near the end of compilation.

This test is **falsifiable**: replace the fast-path body with the
old aliasing return (``return source;`` instead of
``__mn_str_from_parts(src, n_src);``) and the brace-only fixture
flips RED with an ``Invalid free`` referencing
``__mn_indent_to_braces`` in the call chain.

Round-trip evidence (v5.25.0 author):
    # Edit runtime/native/mapanare_core.c::__mn_indent_to_braces
    # fast-path: ``return source;`` instead of fresh-copy.
    make build-rt && python3 scripts/build_stage1.py
    pytest tests/bootstrap/test_preprocess_memcheck.py -v   # FAIL
    # Restore fresh-copy:
    make build-rt && python3 scripts/build_stage1.py
    pytest tests/bootstrap/test_preprocess_memcheck.py -v   # PASS

**Why we don't use ``--error-exitcode=1`` directly:** ``mnc-stage1``
has a pre-existing single-shot leak from ``__mn_argv`` (~71 bytes,
known and tracked since v5.23.1 Mb.3). That leak is bounded — it
fires once per process — and is unrelated to the
``__mn_indent_to_braces`` lifecycle class this test locks. Mirroring
the v5.23.1 ``sanitizer-mnc-stage1`` workflow we run valgrind, accept
the exit code, and grep specifically for the regression signatures
we care about.

Skip-on-no-valgrind: hosts without valgrind (Windows native, fresh
macOS) skip with a marker; CI's Linux-pytest job covers the contract.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STAGE1 = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"


FIXTURES = [
    ("brace_only", "fn main() { print(1) }\n"),
    ("colon_only", "fn main():\n    print(1)\n"),
    ("mixed", "fn outer() {\n    fn inner():\n        print(1)\n}\n"),
]


# Error signatures that indicate a real regression (not the known
# __mn_argv leak). Any of these in valgrind stderr fails the test.
HEAP_ERROR_PATTERNS = (
    "Invalid free",
    "Invalid read",
    "Invalid write",
    "Use of uninitialised value",
    "Mismatched free",
    "double free",
    "heap-use-after-free",
)


@pytest.mark.parametrize("name,src", FIXTURES, ids=[n for n, _ in FIXTURES])
def test_preprocess_no_memory_errors(name, src, tmp_path):
    """``mnc-stage1 preprocess`` must not produce any heap error or
    leak attributable to ``__mn_indent_to_braces`` on the fixture.

    Two assertions, in order:
      1. No generic heap-error pattern appears in stderr (catches
         the v5.25.0 fast-path double-free regression).
      2. No leak chain references ``__mn_indent_to_braces`` itself
         (mirrors v5.23.1 Mb.3's sanitizer-mnc-stage1 grep pattern;
         catches future MnString lifecycle regressions in the
         indent preprocessor whether they manifest as a leak or a
         heap error).
    """
    if shutil.which("valgrind") is None:
        pytest.skip("valgrind not installed")
    if not STAGE1.exists():
        pytest.skip(f"mnc-stage1 not built (expected at {STAGE1})")

    inp = tmp_path / f"{name}.mn"
    inp.write_text(src)

    cmd = [
        "valgrind",
        "--leak-check=full",
        "--show-leak-kinds=definite",
        "--track-origins=yes",
        "--num-callers=20",
        "--quiet",
        str(STAGE1),
        "preprocess",
        str(inp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    err = r.stderr

    # Assertion 1: no generic heap errors (pre-fix, brace-only would
    # surface ``Invalid free`` here from the double-drop of the
    # aliased MnString).
    found = [pat for pat in HEAP_ERROR_PATTERNS if pat in err]
    if found:
        pytest.fail(
            f"valgrind reported heap errors on fixture {name!r}: "
            f"{found!r}\n"
            f"--- stderr ---\n{err}\n"
            f"Command: {' '.join(cmd)}"
        )

    # Assertion 2: no error chain references the indent preprocessor.
    if "__mn_indent_to_braces" in err:
        pytest.fail(
            f"valgrind error chain references __mn_indent_to_braces "
            f"on fixture {name!r} — likely V.9 / Pv.2 regression.\n"
            f"--- stderr ---\n{err}\n"
            f"Command: {' '.join(cmd)}"
        )
