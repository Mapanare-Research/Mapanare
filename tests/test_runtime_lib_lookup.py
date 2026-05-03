"""v5.25.0 Pv.1 — runtime-lib lookup regression test.

Locks the contract that ``mapanare.test_runner._find_runtime_lib()``
returns a path that **exists** AND that clang can **link against**.
Pre-fix (commit ``9dcbbb5``), the candidate name list still mentioned
``libmapanare_core.*`` — names no current build target produces.
``_find_runtime_lib`` silently returned ``None``; ``mapanare test``
shipped clang invocations with no runtime archive; the linker failed
on ``__mn_str_eq`` only on fresh-checkout CI. A stale local
``libmapanare_core.so`` from a v3.x checkout masked the bug on the
developer machine.

This test is **falsifiable**: stash the fix in
``mapanare/test_runner.py`` (the candidate-name list edit) and the
test goes red. The defensive sweep at the top of the test deletes any
stale ``libmapanare_core.*`` shadows so the lookup cannot quietly
fall back to a v3.x leftover.

Round-trip evidence (v5.25.0 author):
    git stash push -- mapanare/test_runner.py
    pytest tests/test_runtime_lib_lookup.py -v   # FAIL
    git stash pop
    pytest tests/test_runtime_lib_lookup.py -v   # PASS
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from mapanare.test_runner import _find_runtime_lib

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = REPO_ROOT / "runtime" / "native"

# Tiny IR fragment that references __mn_str_eq — link must resolve it
# against whatever archive _find_runtime_lib() returns.
SMOKE_IR = """\
; ModuleID = 'pv1_smoke'
target triple = "x86_64-unknown-linux-gnu"

%MnString = type { ptr, i64, i64 }

declare i64 @__mn_str_eq(%MnString, %MnString)

define i32 @main() {
  ret i32 0
}
"""


@pytest.fixture
def clean_legacy_shadows():
    """Sweep ``libmapanare_core.*`` from the candidate dirs.

    No current build target produces these names; any file matching
    that glob is a v3.x-era leftover that would mask a regression in
    ``_find_runtime_lib``. Restore is not needed — the file shouldn't
    exist in the first place.
    """
    candidates = [
        RUNTIME_DIR,
        REPO_ROOT / "mapanare" / "runtime" / "native",
    ]
    removed = []
    for d in candidates:
        if not d.is_dir():
            continue
        for stale in d.glob("libmapanare_core.*"):
            stale.unlink()
            removed.append(str(stale))
    yield removed


def test_find_runtime_lib_returns_existing_path(clean_legacy_shadows):
    """_find_runtime_lib must return a real file, not a stale name."""
    lib = _find_runtime_lib()
    assert lib is not None, (
        "_find_runtime_lib() returned None — the candidate-name list "
        "no longer matches what `make build-rt` produces. Re-check "
        "mapanare/test_runner.py against runtime/native/Makefile."
    )
    p = Path(lib)
    assert p.is_file(), f"resolved path does not exist: {lib}"


def test_find_runtime_lib_resolves_canonical_name(clean_legacy_shadows):
    """The resolved name must contain ``rt`` or ``runtime``.

    Defends against a future mis-edit re-introducing
    ``libmapanare_core.*`` candidates: the v3.x name has neither
    substring and would fail this assertion.
    """
    lib = _find_runtime_lib()
    assert lib is not None
    name = Path(lib).name
    assert "rt" in name or "runtime" in name, (
        f"unexpected archive name resolved: {name}. Expected one of "
        "libmapanare_rt.a / libmapanare_runtime.{so,dylib,dll}."
    )


def test_runtime_lib_links_against_mn_str_eq(tmp_path, clean_legacy_shadows):
    """clang must link a tiny IR fragment that references __mn_str_eq.

    This is the end-to-end signal the test is locking: the archive
    that ``_find_runtime_lib`` resolved actually exports the symbols
    ``mapanare test`` invocations link against. A test that just
    asserts ``_find_runtime_lib() is not None`` would not catch
    a regression where the lookup pointed at an empty or stale
    archive — this one does.
    """
    if shutil.which("clang") is None:
        pytest.skip("clang not installed")

    lib = _find_runtime_lib()
    assert lib is not None, "lookup returned None — see preceding tests"

    ir = tmp_path / "smoke.ll"
    ir.write_text(SMOKE_IR)
    out = tmp_path / "smoke"

    r = subprocess.run(
        ["clang", str(ir), str(lib), "-lm", "-lpthread", "-o", str(out)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, (
        f"clang link against {lib} failed:\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )
    assert out.is_file()
