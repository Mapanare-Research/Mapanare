"""v5.26.0 Mb.9.C — Win64 ABI regression contract for the
v5.23.2 Te.3.B.2 brace-deprecation runtime functions.

Pre-fix (v5.25.0 HEAD): `__mn_count_user_brace_block_openers`
and `__mn_emit_brace_deprecation_warning` fell through the
emitter's user-call path, which uses the 64-byte
`_use_byref` threshold for arg classification. `MnString` is
16 bytes, so on Win64 the call site emitted the struct by value
(`call ... ({ptr, i64} %s)`) while `_decl_fn` already declared
the function with a `ptr` parameter (8-byte threshold via
`_is_large_struct`). gcc lowered the C signature `MnString
source` per Win64 ABI as pass-by-hidden-pointer, dereferenced
rcx as the struct pointer, and read the data buffer's bytes
8..16 as the length field. This surfaced in publish run #48 as
`oom in count_user_brace_block_openers` with the length being
the bytes `"generate"` from `mnc_all.mn`'s `// Auto-generated:`
prelude.

This test has two layers:

  1. **IR-shape gate (the load-bearing test)** — Emit the brace
     functions under a forced `x86_64-w64-windows-gnu` triple
     and assert that the call site uses the alloca + store +
     ptr-pass pattern, NOT by-value struct passing. This
     directly proves the v5.26.0 Mb.9 fix.

  2. **Linux ctypes contract** — Call the C function via a
     dynamically-built shared library on Linux (where SysV
     ABI happens to match what the broken IR emitted, so the
     bug never manifested). This locks in the correctness
     contract the Windows path must match.

Falsifiability round-trip (documented in v5.26.0 SESSION_REPORT):
revert the special-case routing in `mapanare/emit_llvm_text.py
::_do_call` → IR-shape gate FAILs on both functions; reapply
→ both pass.
"""

from __future__ import annotations

import ctypes
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker

REPO_ROOT = Path(__file__).resolve().parents[2]
NATIVE_DIR = REPO_ROOT / "runtime" / "native"

# A tiny program that calls each function once. The semantic checker
# treats both as known runtime externs (declared by the emitter), so
# we just need real call sites in the AST. Argument types are
# String + Int respectively; we use `read_file` (returns String) to
# get a plausible value to pass without baking string-literal
# whitespace into the IR.
_TEST_SOURCE = """
fn run(src: String, fname: String) -> Int:
    let n: Int = __mn_count_user_brace_block_openers(src)
    if n > 0:
        __mn_emit_brace_deprecation_warning(fname, n)
    return n

fn main():
    let src: String = read_file("dummy.mn")
    let fname: String = "dummy.mn"
    let r: Int = run(src, fname)
    print(str(r))
"""


def _emit_ir_for_triple(triple: str) -> str:
    tree = parse(_TEST_SOURCE)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test_mb9", target_triple=triple)
    return emitter.emit(module)


def _call_lines_for(ir: str, fn: str) -> list[str]:
    """Return every line in ``ir`` that calls ``fn``."""
    return [
        line
        for line in ir.splitlines()
        if f"@{fn}(" in line and (line.lstrip().startswith("call ") or " call " in line)
    ]


def test_mb9_win64_call_site_uses_byref_for_count_fn() -> None:
    """Mb.9 IR invariant — under Win64 triple, the call to
    ``__mn_count_user_brace_block_openers`` must pass its
    MnString arg as a pointer (Win64 ABI requires this for
    16-byte structs), NOT as a by-value `{ptr, i64}` struct.

    Pre-fix: call shape was
        ``call i64 @...({ptr, i64} %s)``
    Post-fix: call shape is
        ``call i64 @...(ptr %sarg.N)``
    """
    ir = _emit_ir_for_triple("x86_64-w64-windows-gnu")
    calls = _call_lines_for(ir, "__mn_count_user_brace_block_openers")
    assert calls, "no call sites for __mn_count_user_brace_block_openers"
    for call in calls:
        assert "{ptr, i64}" not in call, (
            "Mb.9 anti-pattern resurfaced — by-value struct arg in:\n"
            f"  {call.strip()}\n"
            "Win64 ABI requires 16-byte MnString to pass as `ptr` "
            "(alloca + store + ptr-arg), matching gcc's "
            "pass-by-hidden-pointer for `MnString source`."
        )
        assert "ptr " in call, f"expected ptr-arg pattern, got: {call.strip()}"


def test_mb9_win64_call_site_uses_byref_for_emit_warning_fn() -> None:
    """Sister symbol — same contract for
    ``__mn_emit_brace_deprecation_warning``. Takes (MnString, i64);
    the MnString must be passed as ptr on Win64, the i64 as-is.
    """
    ir = _emit_ir_for_triple("x86_64-w64-windows-gnu")
    calls = _call_lines_for(ir, "__mn_emit_brace_deprecation_warning")
    assert calls, "no call sites for __mn_emit_brace_deprecation_warning"
    for call in calls:
        assert "{ptr, i64}" not in call, (
            "Mb.9 anti-pattern resurfaced (sister symbol) — by-value "
            "struct arg in:\n"
            f"  {call.strip()}"
        )


def test_mb9_decl_matches_call_arity_under_win64() -> None:
    """Sanity: the declaration of each function under Win64 must
    declare a `ptr` first parameter (large-struct rewrite). The
    call site must therefore also pass `ptr`. A drift between
    decl and call is the original publish-run-#48 failure shape.
    """
    ir = _emit_ir_for_triple("x86_64-w64-windows-gnu")
    decl_re = re.compile(
        r"^\s*declare\s+\S+\s+@(__mn_count_user_brace_block_openers|"
        r"__mn_emit_brace_deprecation_warning)\s*\((.*?)\)"
    )
    found: dict[str, str] = {}
    for line in ir.splitlines():
        m = decl_re.match(line)
        if m:
            found[m.group(1)] = m.group(2)
    assert (
        "__mn_count_user_brace_block_openers" in found
    ), "missing declaration for count_user_brace fn"
    assert (
        "__mn_emit_brace_deprecation_warning" in found
    ), "missing declaration for emit_brace_deprecation_warning"
    # First arg of each must be `ptr` (no struct type leaking through)
    for name, params in found.items():
        first = params.split(",")[0].strip()
        assert first == "ptr" or first.startswith("ptr "), (
            f"{name} declaration first param is {first!r}; "
            "expected `ptr` after Win64 large-struct rewrite"
        )


# -------------------------------------------------------------------
# Linux ctypes contract — proves the C side is correct (always has
# been). Builds a small shared library from mapanare_core.c via
# the project's existing build_native pattern. Skipped on Windows
# (the tests above already cover the IR side; running this on
# Windows would also pass post-fix and is informational).
# -------------------------------------------------------------------


_RT_LIB_NAME = {
    "linux": "libmapanare_brace_test.so",
    "darwin": "libmapanare_brace_test.dylib",
}.get(sys.platform.split("2")[0] if sys.platform.startswith("linux2") else sys.platform, None)


@pytest.fixture(scope="module")
def brace_lib(tmp_path_factory: pytest.TempPathFactory) -> ctypes.CDLL:
    if sys.platform not in ("linux", "darwin"):
        pytest.skip("ctypes contract only runs on linux/darwin")
    cc = shutil.which("clang") or shutil.which("gcc")
    if cc is None:
        pytest.skip("no C compiler on PATH")
    out = tmp_path_factory.mktemp("brace_lib") / "libbrace.so"
    src = NATIVE_DIR / "mapanare_core.c"
    if not src.exists():
        pytest.skip(f"{src} not found")
    cmd = [
        cc,
        "-O0",
        "-shared",
        "-fPIC",
        "-pthread",
        "-I",
        str(NATIVE_DIR),
        str(src),
        "-o",
        str(out),
    ]
    if sys.platform == "darwin":
        cmd.append("-dynamiclib")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        pytest.skip(f"could not build test runtime: {res.stderr[:500]}")
    return ctypes.CDLL(str(out))


class _MnString(ctypes.Structure):
    _fields_ = [("data", ctypes.c_char_p), ("len", ctypes.c_uint64)]


@pytest.mark.parametrize(
    "src,expected",
    [
        (b"fn main() { print(1) }", 1),
        (b"fn main():\n    print(1)\n", 0),
        (b"fn a() { } fn b() { }", 2),
        (b"// Auto-generated:\nfn main():\n    print(1)\n", 0),
    ],
)
def test_count_returns_expected_on_linux(brace_lib: ctypes.CDLL, src: bytes, expected: int) -> None:
    """Lower-bound contract — on Linux SysV ABI the function works
    correctly. The Windows path must produce identical results
    once Mb.9 is fixed.

    The fourth case (``// Auto-generated:`` prelude) is the exact
    shape that surfaced the publish-run-#48 OOM on Windows; on
    Linux it's always returned 0 because no `{`-block openers
    appear.
    """
    brace_lib.__mn_count_user_brace_block_openers.argtypes = [_MnString]
    brace_lib.__mn_count_user_brace_block_openers.restype = ctypes.c_int64
    s = _MnString(src, len(src))
    got = brace_lib.__mn_count_user_brace_block_openers(s)
    assert got == expected, f"count for {src!r} = {got}, expected {expected}"


def test_emit_warning_does_not_crash_on_linux(
    brace_lib: ctypes.CDLL, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sister symbol — must not crash when called. Set the
    suppression env var so test stderr stays clean.
    """
    monkeypatch.setenv("MAPANARE_NO_BRACE_WARNING", "1")
    brace_lib.__mn_emit_brace_deprecation_warning.argtypes = [_MnString, ctypes.c_int64]
    brace_lib.__mn_emit_brace_deprecation_warning.restype = None
    fn = _MnString(b"<test>", 6)
    brace_lib.__mn_emit_brace_deprecation_warning(fn, 3)
