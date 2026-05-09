"""v5.50.x — find_clang() must probe ``<exe_dir>/sdk/bin/clang.exe``.

Origin: ``mnc.exe run hello.mn`` failed on the Windows SDK smoke step
(``publish.yml:604``) with ``error: clang not found``. The publish
workflow strips ``$env:PATH`` to ``C:\\Windows\\System32;C:\\Windows``
and expects the bundled SDK at ``dist/mapanare/sdk/bin/clang.exe`` to
be discovered without PATH cooperation.

The bug: ``mapanare/self/main.mn::find_clang()`` only probed
``<exe_dir>/llvm/clang.exe`` (the legacy v5.10.0 layout). The v5.12.0
SDK split (commit ``72d4cdaf``) moved the bundled clang to
``<exe_dir>/sdk/bin/clang.exe``. ``mapanare/toolchain.py`` was
updated for the new layout but the self-host ``find_clang()`` was
not. Native ``mnc.exe`` therefore fell through to ``"clang"`` (PATH
lookup) and reported ``not found``.

Fix: ``find_clang()`` now probes in toolchain.py-mirrored priority:

  1. ``<exe_dir>/sdk/bin/{clang.exe,clang}``     (v5.12.0 SDK split)
  2. ``<exe_dir>/llvm/bin/{clang.exe,clang}``    (v5.11.0 layout)
  3. ``<exe_dir>/llvm/{clang.exe,clang}``        (legacy v5.10.0)
  4. ``"clang"``                                 (PATH fallback)

This test is a source-level contract gate. It is the cheapest
falsifiability anchor: revert any of the new probes and the test
fails immediately, before any rebuild or CI cycle. The test is
intentionally positioned at the source level rather than at the
IR / binary level because:

  - ``find_clang()`` is .mn code, not C — there is no C-runtime
    mirror to gate at the IR layer.
  - The smoke step at ``publish.yml:604`` is the load-bearing
    end-to-end falsifiability anchor for the full toolchain. This
    test catches the regression before publish.yml runs, on every
    pytest pass, in <1 ms.

Falsifiability round-trip (locked by docstring): delete any of
the four ``sdk_bin_*`` or ``llvm_bin_*`` branches in
``mapanare/self/main.mn::find_clang`` → this test FAILs.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_MN = REPO_ROOT / "mapanare" / "self" / "main.mn"
MNC_ALL_MN = REPO_ROOT / "mapanare" / "self" / "mnc_all.mn"


def _extract_find_clang_body(text: str) -> str:
    """Slice the ``fn find_clang() -> String:`` body out of source."""
    m = re.search(r"^fn find_clang\(\) -> String:\n", text, flags=re.MULTILINE)
    assert m, "find_clang function header not found"
    start = m.end()
    rest = text[start:]
    # Body ends at the next top-level ``fn `` (no leading whitespace).
    next_fn = re.search(r"^fn ", rest, flags=re.MULTILINE)
    end = next_fn.start() if next_fn else len(rest)
    return rest[:end]


_REQUIRED_PROBE_PATHS = (
    '"/sdk/bin/clang.exe"',
    '"/sdk/bin/clang"',
    '"/llvm/bin/clang.exe"',
    '"/llvm/bin/clang"',
    '"/llvm/clang.exe"',
    '"/llvm/clang"',
)


def test_find_clang_probes_sdk_bin_in_main_mn() -> None:
    """Every required probe path must appear inside the ``find_clang``
    body in ``mapanare/self/main.mn``.
    """
    body = _extract_find_clang_body(MAIN_MN.read_text(encoding="utf-8"))
    missing = [p for p in _REQUIRED_PROBE_PATHS if p not in body]
    assert not missing, (
        f"find_clang() in main.mn missing probe paths: {missing}\n"
        "Probe order must mirror mapanare/toolchain.py::_bundled_sdk_candidates "
        "(sdk/bin → llvm/bin → legacy llvm). Pre-v5.50.x only probed "
        "<exe_dir>/llvm/clang.exe — clean-PATH `mnc.exe run` failed in CI."
    )


def test_find_clang_probes_sdk_bin_in_mnc_all() -> None:
    """The concatenated ``mnc_all.mn`` must also carry the new probe
    paths. ``mnc_all.mn`` is the build input for ``mnc-stage1``; if
    ``main.mn`` is updated but ``mnc_all.mn`` is not regenerated via
    ``bash scripts/concat_self.sh``, the stage1 binary keeps the old
    behavior. This test catches that drift.
    """
    body = _extract_find_clang_body(MNC_ALL_MN.read_text(encoding="utf-8"))
    missing = [p for p in _REQUIRED_PROBE_PATHS if p not in body]
    assert not missing, (
        f"find_clang() in mnc_all.mn missing probe paths: {missing}\n"
        "Run `bash scripts/concat_self.sh` after editing main.mn so "
        "the stage1 build picks up the change."
    )


def test_find_clang_probe_priority_order_in_main_mn() -> None:
    """SDK probes must come before legacy ``llvm/`` probes. The
    v5.12.0 SDK is the one we ship; if the legacy probe matches first
    on a system that has both (e.g. dev workspace + bundled SDK),
    we want the SDK clang since that's the one we tested against.
    """
    body = _extract_find_clang_body(MAIN_MN.read_text(encoding="utf-8"))
    sdk_pos = body.index('"/sdk/bin/clang.exe"')
    legacy_pos = body.index('"/llvm/clang.exe"')
    assert sdk_pos < legacy_pos, (
        "find_clang() must probe sdk/bin/clang.exe BEFORE legacy llvm/clang.exe; "
        "priority inverted — SDK bundle would lose to a stale legacy LLVM dir."
    )


_REQUIRED_ARCHIVE_PROBES = (
    '"/sdk/lib/mapanare/libmapanare_rt.a"',
    '"/lib/mapanare/libmapanare_rt.a"',
    '"runtime/native/libmapanare_rt.a"',
)


def test_find_runtime_archive_probes_sdk_install_in_main_mn() -> None:
    """v5.51.x — `find_runtime_archive()` must probe the v5.12.0 SDK
    install layout (`<exe_dir>/sdk/lib/mapanare/libmapanare_rt.a`) and
    the Linux/macOS install layout (`<exe_dir>/lib/mapanare/...`)
    before the dev-workspace fallback. Pre-fix every link site
    hardcoded the dev-relative path which doesn't exist in fresh CI
    checkouts (libmapanare_rt.a is gitignored), so the publish.yml
    `build-cli` Windows smoke link-step failed even after the v5.51.x
    Wn.5/Wn.6 fixes unblocked clang discovery + temp-path emission.
    """
    text = MAIN_MN.read_text(encoding="utf-8")
    m = re.search(r"^fn find_runtime_archive\(\) -> String:\n", text, flags=re.MULTILINE)
    assert m, "find_runtime_archive function not defined in main.mn"
    start = m.end()
    rest = text[start:]
    next_fn = re.search(r"^fn ", rest, flags=re.MULTILINE)
    body = rest[: next_fn.start() if next_fn else len(rest)]
    missing = [p for p in _REQUIRED_ARCHIVE_PROBES if p not in body]
    assert not missing, (
        f"find_runtime_archive() in main.mn missing probe paths: {missing}\n"
        "Probe order: <exe_dir>/sdk/lib/mapanare/ → <exe_dir>/lib/mapanare/ "
        "→ dev-workspace runtime/native/ fallback. Without the SDK probe, "
        "fresh installs cannot link `mnc run`."
    )


def test_link_with_runtime_uses_clang_not_gcc() -> None:
    """v5.51.x — `link_with_runtime` must invoke clang, not gcc. gcc
    is not on PATH on the windows-latest runner image (only clang from
    the bundled llvm-mingw SDK is staged). Pre-fix the function
    hardcoded `gcc` and `-no-pie -rdynamic` (Linux-only flags clang+lld
    rejects on Windows). On Linux, find_clang() returns the same
    behavior as the pre-fix gcc invocation since clang accepts
    -no-pie -rdynamic on Linux too.
    """
    text = MAIN_MN.read_text(encoding="utf-8")
    m = re.search(
        r"^fn link_with_runtime\([^)]*\) -> Int:\n", text, flags=re.MULTILINE
    )
    assert m, "link_with_runtime function not defined in main.mn"
    start = m.end()
    rest = text[start:]
    next_fn = re.search(r"^fn ", rest, flags=re.MULTILINE)
    body = rest[: next_fn.start() if next_fn else len(rest)]
    assert "find_clang()" in body, (
        "link_with_runtime() must use find_clang() not literal `gcc`. "
        "On Windows the runner image has no gcc on PATH; only the "
        "bundled SDK clang resolves."
    )
    assert "__mn_host_is_windows" in body, (
        "link_with_runtime() must skip -no-pie / -rdynamic on Windows "
        "(clang+lld rejects them). Use __mn_host_is_windows() to gate "
        "the Linux-only flag block."
    )
    assert "find_runtime_archive()" in body, (
        "link_with_runtime() must use find_runtime_archive() so SDK "
        "installs can locate the bundled archive."
    )


def test_find_clang_python_self_host_priority_match() -> None:
    """The Python ``mapanare.toolchain._bundled_sdk_candidates`` and
    the self-host ``find_clang()`` must agree on probe order.
    Otherwise ``mapanare`` (Python entrypoint) and ``mnc.exe``
    (native binary) discover different compilers on the same install.
    """
    import mapanare.toolchain as toolchain

    py_candidates = toolchain._bundled_sdk_candidates(Path("/install"))
    py_order = [str(p).replace("\\", "/") for p in py_candidates]
    assert py_order == [
        "/install/sdk/bin",
        "/install/llvm/bin",
        "/install/toolchain/bin",
    ], f"toolchain.py priority changed; update self-host find_clang too:\n{py_order}"

    body = _extract_find_clang_body(MAIN_MN.read_text(encoding="utf-8"))
    sdk_pos = body.index('"/sdk/bin/clang.exe"')
    llvm_bin_pos = body.index('"/llvm/bin/clang.exe"')
    legacy_pos = body.index('"/llvm/clang.exe"')
    assert sdk_pos < llvm_bin_pos < legacy_pos, (
        "self-host find_clang() probe order must mirror toolchain.py: "
        "sdk/bin > llvm/bin > legacy llvm/. Drift between the two means "
        "Python `mapanare` and native `mnc.exe` resolve clang differently."
    )
