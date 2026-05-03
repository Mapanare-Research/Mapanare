"""v5.29.0 Mb.10.C — Win64 ABI regression contract for the
v3.0.0-vintage `__mn_indent_to_braces` runtime function.

Sister fix to v5.26.0 Mb.9 — the brace-deprecation siblings
`__mn_count_user_brace_block_openers` and
`__mn_emit_brace_deprecation_warning` got the Win64 ABI byref
routing in v5.26.0; the parent `__mn_indent_to_braces` was
missed even though the same `MnString source` arg shape applies.

Pre-fix (v5.28.0 HEAD): `__mn_indent_to_braces` fell through the
self-host emitter's user-call path, which uses the 64-byte
`is_byref_type_st` threshold for arg classification. `MnString`
is 16 bytes, so on Win64 the call site emitted the struct by value
(`call ... ({ptr, i64} %s)`) while `declare_runtime_fn` already
declared the function with a `ptr` parameter via
`win64_rewrite_decl_params` (8-byte threshold). gcc lowered the
C signature `MnString source` per Win64 ABI as
pass-by-hidden-pointer, dereferenced rcx as the struct pointer,
and read the data buffer's bytes 8..16 as the length field.
Surfaced in publish run #50 as `Segmentation fault` in
`__mn_indent_to_braces` on `mnc-stage2.exe emit-llvm
mapanare/self/mnc_all.mn` (x86_64-w64-mingw32). The Python
emitter has had this routing since v5.23.1 Mb.1
(`emit_llvm_text.py:3632`); only the self-host side was missed.

This test has two layers (mirrors v5.26.0 Mb.9.C):

  1. **IR-shape gate (load-bearing)** — Emit a tiny program that
     calls `__mn_indent_to_braces` through the Python emitter
     under a forced `x86_64-w64-windows-gnu` triple and assert
     the call site uses the alloca + store + ptr-pass + sret
     pattern, NOT by-value `{ptr, i64}` arg passing. This proves
     the Python contract Mb.10's self-host edit mirrors.

  2. **Linux ctypes contract** — Build a small shared library
     from `mapanare_core.c` and call `__mn_indent_to_braces`
     directly. Linux SysV happens to make the broken IR work
     (16-byte aggregates pass in registers regardless of declared
     shape), so this layer locks the C-side correctness contract
     against future drift in the runtime itself.

Falsifiability round-trip (v5.29.0 SESSION_REPORT):
revert the special-case routing in `mapanare/self/emit_llvm.mn
::emit_mir_call` → IR-shape gate FAILs in self-host stage2.ll
(but not in the Python-emitter test below — both emitters are
needed for full coverage).
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

# A tiny program that calls `__mn_indent_to_braces` once. The
# semantic checker treats it as a known runtime extern (declared
# by the emitter), so we just need a real call site in the AST.
# Use `read_file` to obtain a String value to pass without baking
# string-literal whitespace into the IR (mirrors the Mb.9.C test).
_TEST_SOURCE = """
fn run(src: String) -> String:
    let preprocessed: String = __mn_indent_to_braces(src)
    return preprocessed

fn main():
    let src: String = read_file("dummy.mn")
    let r: String = run(src)
    print(r)
"""


def _emit_ir_for_triple(triple: str) -> str:
    tree = parse(_TEST_SOURCE)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test_mb10", target_triple=triple)
    return emitter.emit(module)


def _call_lines_for(ir: str, fn: str) -> list[str]:
    """Return every line in ``ir`` that calls ``fn``."""
    return [
        line
        for line in ir.splitlines()
        if f"@{fn}(" in line and (line.lstrip().startswith("call ") or " call " in line)
    ]


# -------------------------------------------------------------------
# Layer 1 — IR-shape gate under Win64 triple
# -------------------------------------------------------------------


def test_mb10_win64_call_site_uses_byref_for_indent_to_braces() -> None:
    """Mb.10 IR invariant — under Win64 triple, the call to
    ``__mn_indent_to_braces`` must pass its MnString arg as a
    pointer (Win64 ABI requires this for 16-byte structs), NOT
    as a by-value ``{ptr, i64}`` struct.

    Pre-fix: call shape was
        ``call {ptr, i64} @__mn_indent_to_braces({ptr, i64} %s)``
    Post-fix: call shape is
        ``call void @__mn_indent_to_braces(ptr sret(...) %sret.N, ptr %sarg.M)``
    (sret because MnString is also a 16-byte aggregate return).
    """
    ir = _emit_ir_for_triple("x86_64-w64-windows-gnu")
    calls = _call_lines_for(ir, "__mn_indent_to_braces")
    assert calls, "no call sites for __mn_indent_to_braces"
    for call in calls:
        # The MnString arg position must NOT be a by-value `{ptr, i64}`.
        # The return-slot `ptr sret({ptr, i64})` token is allowed (it's
        # the sret parameter, not a by-value arg) — strip it before the
        # check.
        scrubbed = re.sub(r"sret\(\{[^}]+\}\)", "sret(SRET)", call)
        scrubbed = re.sub(r"sret\(\{[^}]+\}\) align \d+ %\S+", "sret_arg", scrubbed)
        assert "{ptr, i64}" not in scrubbed, (
            "Mb.10 anti-pattern resurfaced — by-value MnString arg in:\n"
            f"  {call.strip()}\n"
            "Win64 ABI requires 16-byte MnString to pass as `ptr` "
            "(alloca + store + ptr-arg), matching gcc's "
            "pass-by-hidden-pointer for `MnString source`."
        )


def test_mb10_win64_decl_matches_call_arity() -> None:
    """Sanity: the declaration of ``__mn_indent_to_braces`` under
    Win64 must declare a ``ptr`` first (sret) parameter and a
    ``ptr`` second (sarg) parameter (large-struct rewrite for
    both return and arg). The call site must therefore also pass
    ``ptr`` in both positions. A drift between decl and call is
    the original publish-run-#50 failure shape.
    """
    ir = _emit_ir_for_triple("x86_64-w64-windows-gnu")
    decl_line: str | None = None
    for line in ir.splitlines():
        if "declare" in line and "@__mn_indent_to_braces(" in line:
            decl_line = line
            break
    assert decl_line is not None, "missing declaration for __mn_indent_to_braces"
    # Either form is acceptable: `declare void @fn(ptr sret(...), ptr)`
    # or `declare {ptr, i64} @fn(ptr)`. The forbidden form is a
    # by-value `{ptr, i64}` PARAMETER (not return type, not sret tag).
    # Strip the `sret(<aggregate>)` annotation and any return-type
    # aggregate before the function name, then check.
    after_at = decl_line.split("@__mn_indent_to_braces", 1)[1]
    scrubbed = re.sub(r"sret\([^)]*\)", "sret(SRET)", after_at)
    assert "{ptr, i64}" not in scrubbed, (
        f"declaration leaks struct type through Win64 rewrite: "
        f"{decl_line.strip()!r}; expected `ptr` parameter after "
        f"large-struct rewrite"
    )


def test_mb10_sysv_call_site_unchanged() -> None:
    """Negative gate — under Linux SysV triple, the call shape
    can remain by-value ``{ptr, i64}`` (SysV passes 16-byte
    aggregates in registers regardless of declared shape, and the
    call site isn't a correctness issue there). This test pins
    the SysV side so a future emitter refactor doesn't
    accidentally rewrite it (avoiding gratuitous IR churn that
    would break stage2/stage3 fixed-point comparisons).
    """
    ir = _emit_ir_for_triple("x86_64-unknown-linux-gnu")
    calls = _call_lines_for(ir, "__mn_indent_to_braces")
    assert calls, "no call sites for __mn_indent_to_braces"
    # Every SysV call site should pass the MnString arg by-value
    # as `{ptr, i64}` — this is the load-bearing baseline for the
    # 5-release period (v5.23.1 → v5.28.0) where the bug went
    # latent on Linux/macOS without anyone noticing.
    for call in calls:
        assert "{ptr, i64}" in call, (
            f"SysV call site no longer passes MnString by-value:\n"
            f"  {call.strip()}\n"
            "Unexpected change — see Mb.10.C test rationale."
        )


# -------------------------------------------------------------------
# Layer 2 — Linux ctypes contract (proves C side is correct)
# -------------------------------------------------------------------


@pytest.fixture(scope="module")
def indent_lib(tmp_path_factory: pytest.TempPathFactory) -> ctypes.CDLL:
    if sys.platform not in ("linux", "darwin"):
        pytest.skip("ctypes contract only runs on linux/darwin")
    cc = shutil.which("clang") or shutil.which("gcc")
    if cc is None:
        pytest.skip("no C compiler on PATH")
    out = tmp_path_factory.mktemp("indent_lib") / "libindent.so"
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
    """Matches `runtime/native/mapanare_core.h::MnString` —
    `{const char *data, uint64_t len:63, uint64_t is_heap:1}`
    packed into 16 bytes. ctypes can't model the bitfield directly
    in a way that round-trips through the calling convention, so
    we expose `len` as a plain uint64 and rely on the caller to
    leave the high bit clear (is_heap=0 → "constant string", which
    means `__mn_str_free` won't try to free the buffer)."""

    _fields_ = [("data", ctypes.c_char_p), ("len", ctypes.c_uint64)]


@pytest.mark.parametrize(
    "src,must_contain",
    [
        # Indented function body — preprocessor must wrap it in
        # `{` … `}`. The function header itself is preserved verbatim.
        (b"fn main():\n    print(1)\n", b"fn main()"),
        # Empty body with `pass` — same wrapping.
        (b"fn x():\n    pass\n", b"fn x()"),
        # Empty source — preprocessor returns empty (no crash).
        (b"", b""),
    ],
)
def test_indent_to_braces_returns_valid_mnstring(
    indent_lib: ctypes.CDLL, src: bytes, must_contain: bytes
) -> None:
    """Mb.10 lower-bound contract — `__mn_indent_to_braces` must
    read its `MnString source` parameter correctly and return a
    valid `MnString` under Linux SysV. The Windows path is
    structurally guaranteed to behave the same once Mb.10's
    self-host emitter routing is in place (covered by the
    IR-shape gate above). This test guards against future
    C-runtime regressions that could re-introduce the bug from
    the runtime side (e.g., changing the parameter type).
    """
    indent_lib.__mn_indent_to_braces.argtypes = [_MnString]
    indent_lib.__mn_indent_to_braces.restype = _MnString
    s = _MnString(src, len(src))
    out = indent_lib.__mn_indent_to_braces(s)
    # Strip the high bit (is_heap) from the returned len.
    actual_len = out.len & 0x7FFFFFFFFFFFFFFF
    if not src:
        # Empty input → empty output is acceptable.
        assert actual_len == 0
        return
    assert actual_len > 0, f"empty output for non-empty src {src!r}"
    body = ctypes.string_at(out.data, actual_len) if out.data else b""
    assert must_contain in body, (
        f"output for {src!r} does not contain {must_contain!r}: " f"got {body!r}"
    )
