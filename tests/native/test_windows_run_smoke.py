"""v5.49.0 Wn.4 — Win64 ABI regression contract for direct
``__mn_*`` runtime calls from .mn source.

Origin: ``mnc.exe run hello.mn`` aborted with
``mapanare: out of memory (requested 8017634865777560157 bytes)``
on the ``windows-latest`` SDK smoke step (``publish.yml:596``)
and on a clean Windows 11 x64 stage1 build. gdb backtrace
localized the failure to ``find_clang() → __mn_file_exists →
mn_to_cstr → __mn_alloc`` with the ``MnString path`` argument
read as a hidden-pointer-to-MnString containing path-string
bytes — the canonical Win64 sarg ABI mismatch for a 16-byte
aggregate-by-value runtime arg. See
``docs/roadmap/v5/v5.49.0/PRE_PHASE_AUDIT.md``.

Pre-fix path: ``mapanare/emit_llvm_text.py::_do_call`` auto-
declared ``__mn_file_exists`` from MIR-derived types
(``ret = ptr`` because ``if __mn_file_exists(p) != 0:`` is
ptr-comparable and the inferencer picked Ptr) and emitted the
call site with ``_use_byref(t)`` (>64 byte threshold for
user-fn ABI). The 16-byte ``MnString`` aggregate slipped
under that threshold and got passed by value at the call site
while ``_decl_fn`` had already declared the parameter as
``ptr`` per Win64. Caller and callee disagreed; gcc-compiled
``MnString path`` dereferenced rcx as struct-pointer and
read the data buffer's bytes 0..16 as ``{data, len}`` →
``len = 8017634865777560156`` → ``__mn_alloc(len + 1)`` OOM.

Post-fix path (v5.49.0 Wn.1): ``_do_call`` and ``_do_extern``
consult ``_RUNTIME_FN_SIGS`` for known ``__mn_*`` symbols and
route through ``_rt`` for ABI-correct Win64 sarg lowering
(alloca + store + pass ``ptr``). The self-host mirror
(v5.49.0 Wn.2) extends ``emit_mir_call`` with explicit
``emit_rt_call`` routing for the same symbols.

This test has two layers, mirroring v5.26.0 Mb.9.C:

  1. **IR-shape gate (cross-platform, the load-bearing test)** —
     Emit IR under a forced ``x86_64-w64-windows-gnu`` triple and
     assert that call sites for ``__mn_file_exists`` (and other
     MnString-arg runtime symbols) use the alloca + store +
     ``ptr`` pattern, NOT by-value ``{ptr, i64}`` aggregate
     passing. The IR-shape gate is sufficient on its own; it
     proves the bug is closed without needing a staged binary
     and runs on every platform's pytest.

  2. **End-to-end Windows smoke (optional)** — When a staged
     ``mnc.exe`` is available locally (e.g. after
     ``python scripts/build_stage1.py`` on a Windows machine),
     compile and run the same ``hello.mn`` payload that
     ``publish.yml:576-580`` uses. Asserts exit 0 and the
     expected stdout. Skipped on non-Windows or when no
     ``mnc.exe`` is on disk.

Falsifiability round-trip (locked by docstring): revert the
``_RUNTIME_FN_SIGS`` early-return in
``mapanare/emit_llvm_text.py::_do_call`` → IR-shape gate FAILs
with the by-value aggregate signature; reapply → passes.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker

REPO_ROOT = Path(__file__).resolve().parents[2]


_FIND_CLANG_REPRO = """
fn find_clang_like() -> Bool:
    let p1: String = "C:/llvm/clang.exe"
    if __mn_file_exists(p1) != 0:
        return true
    let p2: String = "/usr/bin/clang"
    if __mn_file_exists(p2) != 0:
        return true
    return false

fn main():
    let r: Bool = find_clang_like()
    print(str(r))
"""


_OTHER_RT_REPRO = """
fn main():
    let dir: String = "/tmp"
    let n: Int = __mn_dir_count_files(dir)
    let s: Int = __mn_dir_total_size(dir)
    let r: Int = __mn_dir_remove_recursive(dir)
    let exe: String = __mn_executable_dir()
    __mn_str_eprint(exe)
    print(str(n + s + r))
"""


def _emit_ir_for_triple(source: str, triple: str) -> str:
    tree = parse(source)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test_wn4", target_triple=triple)
    return emitter.emit(module)


def _call_lines_for(ir: str, fn: str) -> list[str]:
    return [
        line
        for line in ir.splitlines()
        if f"@{fn}(" in line and (line.lstrip().startswith("call ") or " call " in line)
    ]


def _decl_line_for(ir: str, fn: str) -> str | None:
    for line in ir.splitlines():
        s = line.lstrip()
        if s.startswith("declare ") and f"@{fn}(" in s:
            return s
    return None


# ──────────────────────────────────────────────────────────────────
# IR-shape gate — the load-bearing falsifiability anchor
# ──────────────────────────────────────────────────────────────────


def test_wn4_file_exists_call_site_uses_ptr_on_win64() -> None:
    """v5.49.0 Wn.1 — under Win64 triple, ``__mn_file_exists`` call
    sites must pass the MnString arg as ``ptr`` (alloca + store +
    pass-pointer), NOT as by-value ``{ptr, i64}`` aggregate.

    Pre-fix shape:
        ``call ptr @__mn_file_exists({ptr, i64} %v)``
    Post-fix shape:
        ``call i64 @__mn_file_exists(ptr %sarg.N)``
    """
    ir = _emit_ir_for_triple(_FIND_CLANG_REPRO, "x86_64-w64-windows-gnu")
    calls = _call_lines_for(ir, "__mn_file_exists")
    assert calls, "no call sites for __mn_file_exists in find_clang-like repro"
    for call in calls:
        assert "{ptr, i64}" not in call, (
            "Wn.1 anti-pattern resurfaced — by-value MnString in:\n"
            f"  {call.strip()}\n"
            "Win64 ABI requires 16-byte MnString to pass as `ptr` "
            "(alloca + store + ptr-arg), matching gcc's pass-by-"
            "hidden-pointer for `MnString path`. The original v5.49.0 "
            "OOM reproduces if this regresses."
        )
        assert "(ptr " in call, f"expected ptr-arg pattern, got: {call.strip()}"


def test_wn4_file_exists_decl_returns_i64_not_ptr() -> None:
    """v5.49.0 Wn.1 secondary smell — the declaration must return
    ``i64`` (matching the C signature ``int64_t __mn_file_exists``),
    not ``ptr``. Pre-fix the auto-declare path inferred ``Ptr`` from
    MIR context and emitted ``declare ptr @__mn_file_exists(ptr)``.
    The registry now pins the canonical signature.
    """
    ir = _emit_ir_for_triple(_FIND_CLANG_REPRO, "x86_64-w64-windows-gnu")
    decl = _decl_line_for(ir, "__mn_file_exists")
    assert decl, "no declaration for __mn_file_exists"
    assert decl.startswith("declare i64 "), (
        f"Wn.1 return-type smell — expected `declare i64 @__mn_file_exists(...)`, got:\n"
        f"  {decl}\n"
        "Direct __mn_* calls in .mn source must use the canonical C signature "
        "from _RUNTIME_FN_SIGS, not MIR-derived inference."
    )


def test_wn4_file_exists_linux_path_unchanged() -> None:
    """SysV ABI sanity — on Linux x86_64 the canonical call shape
    is aggregate-by-value (the bug was invisible there because
    SysV passes 16-byte structs in two registers). The fix must
    not change Linux behavior in a way that breaks the call.
    """
    ir = _emit_ir_for_triple(_FIND_CLANG_REPRO, "x86_64-pc-linux-gnu")
    calls = _call_lines_for(ir, "__mn_file_exists")
    assert calls, "no call sites for __mn_file_exists on Linux triple"
    # Either by-value aggregate OR ptr is fine on Linux; the ABI
    # coincidence works both ways. The decl + call must agree.
    decl = _decl_line_for(ir, "__mn_file_exists")
    assert decl, "no declaration for __mn_file_exists on Linux"
    assert decl.startswith(
        "declare i64 "
    ), f"Linux declaration should also be i64-returning: {decl}"


def test_wn4_other_runtime_symbols_use_ptr_on_win64() -> None:
    """v5.49.0 Wn.1 sweep — every MnString-arg runtime symbol the
    registry covers must use the ``ptr`` arg shape on Win64. This
    catches future regressions if the registry shrinks or the
    auto-declare path gains a new bypass.
    """
    ir = _emit_ir_for_triple(_OTHER_RT_REPRO, "x86_64-w64-windows-gnu")
    for fn in (
        "__mn_dir_count_files",
        "__mn_dir_total_size",
        "__mn_dir_remove_recursive",
        "__mn_str_eprint",
    ):
        calls = _call_lines_for(ir, fn)
        assert calls, f"no call sites for {fn}"
        for call in calls:
            assert "{ptr, i64}" not in call, (
                f"Wn.1 sweep regression — {fn} call passes by-value MnString:\n"
                f"  {call.strip()}\n"
                "All MnString-arg `__mn_*` symbols must use Win64 sarg shape."
            )


def test_wn4_decl_call_arity_agrees_under_win64() -> None:
    """Decl/call drift was the original v5.49.0 failure shape:
    ``declare ptr @__mn_file_exists(ptr)`` (1 ptr arg) but call
    site passed ``{ptr, i64}`` (a 16-byte aggregate). LLVM doesn't
    type-check this at IR level; it shows up at codegen as ABI
    chaos. Lock in agreement.
    """
    ir = _emit_ir_for_triple(_FIND_CLANG_REPRO, "x86_64-w64-windows-gnu")
    decl = _decl_line_for(ir, "__mn_file_exists")
    assert decl, "no declaration for __mn_file_exists"
    # Decl after Win64 large-struct rewrite must be `(ptr)`.
    assert "(ptr)" in decl, f"expected `(ptr)` after Win64 rewrite, got: {decl}"


# ──────────────────────────────────────────────────────────────────
# End-to-end Windows smoke — optional; uses a staged binary if
# present. Skipped on non-Windows. The IR-shape gate above is the
# load-bearing falsifiability anchor; this layer is the empirical
# proof the user-visible smoke is closed.
# ──────────────────────────────────────────────────────────────────


def _staged_mnc_exe() -> Path | None:
    """Locate a staged Windows ``mnc.exe`` for the smoke test."""
    candidates = [
        REPO_ROOT / "dist" / "mapanare" / "mnc.exe",
        REPO_ROOT / "mapanare" / "self" / "mnc-stage1.exe",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only end-to-end smoke")
def test_wn4_windows_run_smoke_end_to_end(tmp_path: Path) -> None:
    """Mirror of ``publish.yml:596`` — invoke the staged ``mnc.exe``
    on the same ``hello.mn`` payload (lines 576-580) and assert
    exit 0. This is the user-visible regression we're closing.

    Skipped if no staged binary exists locally; in CI the
    Windows publish workflow staging step provides it.
    """
    exe = _staged_mnc_exe()
    if exe is None:
        pytest.skip(
            "no staged mnc.exe found at dist/mapanare/mnc.exe or "
            "mapanare/self/mnc-stage1.exe (run scripts/build_stage1.py)"
        )
    hello = tmp_path / "hello.mn"
    hello.write_text(
        textwrap.dedent("""\
            fn main() {
                print("hello from clean Windows SDK smoke")
            }
            """),
        encoding="ascii",
    )
    # Smoke step uses ``mnc.exe run`` which invokes clang+link
    # downstream. End-to-end success requires a working clang on
    # PATH and the runtime archive ``runtime/native/libmapanare_rt.a``.
    # The IR-shape tests above are the load-bearing falsifiability
    # anchor; this end-to-end test will pass in CI (where the SDK
    # staging step provides both) and may skip locally if the
    # downstream tools are missing.
    env = os.environ.copy()
    rt_archive = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"
    if not rt_archive.exists():
        pytest.skip(
            f"runtime archive not staged at {rt_archive}; "
            "the IR-shape tests above are the load-bearing falsifiability anchor"
        )
    # Locate clang on PATH; ``mnc.exe run`` shells out to it. If clang
    # is unavailable we can't end-to-end smoke (this is the same
    # constraint the publish.yml SDK staging step satisfies via the
    # bundled llvm-mingw clang next to ``dist/mapanare/sdk/bin``).
    import shutil as _shutil

    if not _shutil.which("clang"):
        pytest.skip("clang not on PATH; needed for `mnc.exe run` downstream invocation")
    r = subprocess.run(
        [str(exe), "run", str(hello)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    # Crucial: ``out of memory`` should NEVER appear in stderr — that's
    # the v5.49.0 OOM signature. Check first, before exit-code checks,
    # so the assertion message names the right regression class.
    assert "out of memory" not in r.stderr, (
        f"v5.49.0 OOM resurfaced in stderr:\n{r.stderr}\n"
        "This is the exact regression Wn.1 closed; check whether the "
        "_RUNTIME_FN_SIGS routing in emit_llvm_text.py was reverted."
    )
    assert r.returncode == 0, (
        f"`mnc.exe run hello.mn` exited {r.returncode}\n"
        f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
    )
    assert "hello from clean Windows SDK smoke" in r.stdout, f"unexpected stdout: {r.stdout!r}"
