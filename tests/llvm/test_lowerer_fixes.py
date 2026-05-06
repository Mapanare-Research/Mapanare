"""v5.46.0 Lf.\\* — regression locks for the v5.43.0 lowerer-bug closeout.

This module locks the three (Lf.1 + Lf.2 + Lf.3) v5.x lowerer bugs that
the v5.43.0 SESSION_REPORT documented and worked around with the flat-
tuple ``(ok: Bool, value, err_kind: Int, err_msg: String)`` shape.
Phase 0 audit (``docs/roadmap/v5/v5.46.0/PRE_PHASE_AUDIT.md``)
established that all three trace to **one** root cause in the Python
bootstrap lowerer ``mapanare/lower.py`` ``Ok``/``Err`` constructor
branches: when the enclosing function returns ``Result<T, E>`` with
non-trivial ``T``, the ``WrapErr`` literal defaults the Ok side to
``Int`` (8 bytes), produces a small (e.g. 32-byte) Result struct, and
the function body stores it into the ``__sret__`` slot sized for the
real (e.g. 88-byte) ``Result<T, E>``. The trailing bytes stay zero,
and downstream consumers read the Err's variant tag from the wrong
offset — symptoms range from silent variant-tag corruption (Lf.1) to
IR-validation failure (Lf.2) to silent no-fire on the nested match
(Lf.3). The self-host (``mapanare/self/lower.mn``) had the v5.26.1
Eu.2 fix already; v5.46.0 backports the same logic into Python.

**Falsifiability protocol (per case):**

1. Pre-fix: revert the v5.46.0 fix in ``mapanare/lower.py`` (the
   ``err_default_ti`` / ``ok_default_ti`` branches consulting
   ``self._fn.return_type``). The corresponding test case fails with
   the documented signature.
2. Re-apply the fix; the test passes again.
3. Round-trip locked: the IR signature in each case (e.g.
   ``%ok.NN`` typed as ``i64`` instead of the struct shape) is
   recorded in ``PRE_PHASE_AUDIT.md`` IR-level diagnosis.

The pytest harness compiles each case via the **Python bootstrap**
``python3 -m mapanare emit-llvm`` (NOT the self-hosted stage1, which
already produces correct output and so cannot exercise the bug),
links against ``runtime/native/libmapanare_rt.a``, runs the binary,
and asserts on stdout.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME_LIB = ROOT / "runtime" / "native" / "libmapanare_rt.a"


def _emit_link_run(src: Path, tmp_path: Path) -> tuple[int, str, str]:
    """Compile ``src`` via Python bootstrap, link, run. Return (rc, stdout, stderr).

    Uses ``python3 -m mapanare emit-llvm`` (NOT mnc-stage1) because the
    bug was Python-bootstrap-only at v5.45.0 HEAD. The self-host stage1
    already had the v5.26.1 Eu.2 fix and produced correct output for
    all three Lf cases.
    """
    ll_path = tmp_path / f"{src.stem}.ll"
    bin_path = tmp_path / src.stem
    emit = subprocess.run(
        [
            sys.executable,
            "-m",
            "mapanare",
            "emit-llvm",
            str(src),
            "-o",
            str(ll_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
        env={**os.environ, "MAPANARE_RELEASE": "1"},
    )
    if emit.returncode != 0:
        return (emit.returncode, emit.stdout, "EMIT-FAIL: " + emit.stderr)

    clang = shutil.which("clang") or "clang"
    link = subprocess.run(
        [
            clang,
            str(ll_path),
            str(RUNTIME_LIB),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if link.returncode != 0:
        return (link.returncode, "", "LINK-FAIL: " + link.stderr)

    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return (run.returncode, run.stdout, run.stderr)


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
def test_lf1_complex_result_destructure(tmp_path: Path) -> None:
    """Lf.1: Result<NodeHandle, NetworkError> destructure preserves Err tag.

    Before the v5.46.0 fix the small Result<Int, NetworkError> wrap
    shape (32 bytes) was stored into an 88-byte sret slot; the
    NetworkError tag at big-layout offset 72 read zero (= BadUrl) for
    every constructed variant. Post-fix, kind reads correctly.

    Falsifiability: revert ``mapanare/lower.py`` ``Err``-branch
    ``ok_default_ti = self._fn.return_type.type_info.args[0]``; this
    test prints "k=1" instead of "k=3" / "k=5".
    """
    rc, out, err = _emit_link_run(
        ROOT / "tests" / "golden" / "100_result_complex_destructure.mn",
        tmp_path,
    )
    assert rc == 0, f"Lf.1 binary exited {rc}\nstdout:{out}\nstderr:{err}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines == ["k=3", "k=5"], (
        f"Lf.1 output mismatch — pre-fix this would have been ['k=1', 'k=1'] "
        f"due to Err tag corruption.\nGot: {lines}"
    )


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
def test_lf2_match_rewrap_propagation(tmp_path: Path) -> None:
    """Lf.2: variant rewrap through match preserves tag across hops.

    Before the v5.46.0 fix this program failed at IR validation
    (``'%ok.NN' defined with type 'i64' but expected '{ ... }'``)
    because the rewrap chain inherited the small Result<Int, ?> shape
    from the buggy WrapErr while the destructure expected the real
    Result<NodeHandle, NetworkError> shape.

    Falsifiability: revert the fix; emit-llvm produces invalid IR that
    fails ``clang`` link with the recorded error signature.
    """
    rc, out, err = _emit_link_run(
        ROOT / "tests" / "golden" / "101_match_rewrap_propagation.mn",
        tmp_path,
    )
    assert rc == 0, f"Lf.2 binary exited {rc}\nstdout:{out}\nstderr:{err}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines == ["k=2"], (
        f"Lf.2 output mismatch — pre-fix this would have failed at IR "
        f"validation (link error) or printed wrong tag.\nGot: {lines}"
    )


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
def test_lf3_nested_15arm_match(tmp_path: Path) -> None:
    """Lf.3: nested 15-arm match on Err(e) fires the correct inner arm.

    Before the v5.46.0 fix this program produced **silent no-fire** —
    empty output — because the corrupt NetworkError tag matched no
    inner arm. The bug was always Lf.1's wrap-shape mismatch upstream;
    the 15-arm threshold was a red herring.

    Falsifiability: revert the fix; this test sees empty stdout (none
    of the expected k=3/k=12/k=15 lines).
    """
    rc, out, err = _emit_link_run(
        ROOT / "tests" / "golden" / "102_nested_15arm_match.mn",
        tmp_path,
    )
    assert rc == 0, f"Lf.3 binary exited {rc}\nstdout:{out}\nstderr:{err}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines == ["k=3", "k=12", "k=15"], (
        f"Lf.3 output mismatch — pre-fix this would have been [] "
        f"(silent no-fire on the nested match).\nGot: {lines}"
    )


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
@pytest.mark.parametrize("ok_type", ["Int", "String"])
def test_lf1_regression_trivial_ok_unchanged(tmp_path: Path, ok_type: str) -> None:
    """Lf.1 regression: Result<Int, E> and Result<String, E> still work.

    The v5.46.0 fix consults ``self._fn.return_type`` only when the
    function returns Result<T, E>; the args[0]-derived ok_ti remains
    the source of truth for the actual wrapped value. This test
    exercises the same Err-wrap pattern with trivial Ok types and
    confirms no regression.
    """
    src = tmp_path / f"trivial_{ok_type.lower()}.mn"
    src.write_text(f"""
pub tipo NE {{
    | BadUrl(String)
    | NoKey(String)
}}

fn ne_kind(e: NE) -> Int {{
    pon mut k: Int = 0
    match e {{
        BadUrl(s) => {{ k = 1 }},
        NoKey(s) => {{ k = 2 }}
    }}
    da k
}}

fn make() -> Result<{ok_type}, NE> {{
    da Err(NoKey("test"))
}}

fn main() -> Int {{
    pon r: Result<{ok_type}, NE> = make()
    match r {{
        Ok(_) => {{ print("FAIL Ok") }},
        Err(e) => {{ print("k=" + str(ne_kind(e))) }}
    }}
    da 0
}}
""")
    rc, out, err = _emit_link_run(src, tmp_path)
    assert rc == 0, f"trivial-Ok regression ({ok_type}) failed: rc={rc}\n{err}"
    assert "k=2" in out, f"trivial-Ok regression ({ok_type}) wrong output: {out!r}"



# ---------------------------------------------------------------------------
# v5.47.0 Cl.1 (Lf.4) — variant-name collision regression
# ---------------------------------------------------------------------------
#
# Two enums declaring a variant of the same name (e.g. NetworkError::
# TransportLost + ExitReason::TransportLost). Pre-fix the semantic
# checker rejected `pon n: NetworkError = TransportLost("net")` with a
# Type-mismatch error because variant lookup picked the last-registered
# enum's variant. Post-fix both Python bootstrap (mapanare/semantic.py
# multimap + expected_type context) and self-host stage1 (mapanare/
# self/semantic.mn mirror + mapanare/self/lower.mn LowerState
# expected_enum_name hint) accept and dispatch correctly.
#
# Falsifiability:
#   - Revert mapanare/semantic.py _variant_alternatives lookup → semantic
#     check fails with "Type mismatch: declared type NetworkError but
#     initial value is ExitReason".
#   - Revert mapanare/self/lower.mn enum_has_variant hint check → stage1
#     produces wrong-shape IR (`store %enum.ExitReason ... ptr ...
#     <NetworkError-shaped slot>`).


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
def test_lf4_variant_name_collision(tmp_path: Path) -> None:
    """Lf.4: declared-type-aware constructor disambiguation.

    Pre-fix: `pon n: NetworkError = TransportLost("net")` rejected
    with "Type mismatch: declared type NetworkError but initial
    value is ExitReason". Post-fix: compiles, dispatches correctly.
    """
    rc, out, err = _emit_link_run(
        ROOT / "tests" / "golden" / "103_variant_name_collision.mn",
        tmp_path,
    )
    assert rc == 0, f"Lf.4 binary exited {rc}\nstdout:{out}\nstderr:{err}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines == ["net=1", "exit=10", "net2=2", "exit2=20"], (
        f"Lf.4 output mismatch — pre-fix this would have been a "
        f"semantic-check rejection (no IR emitted).\nGot: {lines}"
    )


@pytest.mark.skipif(not RUNTIME_LIB.exists(), reason="libmapanare_rt.a not built")
@pytest.mark.parametrize("variant_idx", [0, 1])
def test_lf4_minimal_pair(tmp_path: Path, variant_idx: int) -> None:
    """Lf.4 minimal pair — two enums, one shared variant name.

    Each iteration constructs the same variant-name through a
    different declared-type. Both must dispatch to the right arm.
    """
    src = tmp_path / f"lf4_min_{variant_idx}.mn"
    src.write_text("""
pub tipo A {
    | X(String)
    | Ay(String)
}
pub tipo B {
    | X(String)
    | Bee(String)
}

fn from_a(a: A) -> Int {
    match a {
        X(s) => { da 100 },
        Ay(s) => { da 200 }
    }
}

fn from_b(b: B) -> Int {
    match b {
        X(s) => { da 1000 },
        Bee(s) => { da 2000 }
    }
}

fn main() -> Int {
    pon a: A = X("from-a")
    pon b: B = X("from-b")
    print("a=" + str(from_a(a)))
    print("b=" + str(from_b(b)))
    da 0
}
""")
    rc, out, err = _emit_link_run(src, tmp_path)
    assert rc == 0, f"Lf.4 minimal failed: rc={rc}\n{err}"
    assert "a=100" in out and "b=1000" in out, (
        f"Lf.4 minimal-pair dispatch wrong: {out!r}"
    )
