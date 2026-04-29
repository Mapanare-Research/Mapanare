"""v5.15.1 — Cross-bootstrap mirror for list/map comprehensions.

Re-runs the v5.15.0 ``tests/test_comprehensions.py`` cases through
``mnc-stage1`` (the self-hosted bootstrap) instead of the Python
bootstrap. Each case must produce stdout identical to what the Python
bootstrap produces.

The Python parser-only cases (``test_list_comp_parses_*``) succeed
implicitly: ``mnc-stage1 emit-llvm`` must successfully parse the
source to emit LLVM IR. The e2e cases drive a parse → lower → emit →
llc → clang → run pipeline and compare stdout.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
STAGE1 = REPO / "mapanare/self/mnc-stage1"
RUNTIME = REPO / "runtime/native/mapanare_core.c"


def _need(tool: str) -> None:
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not available")


def _stage1_compile_and_run(src: str) -> str:
    """Compile ``src`` via mnc-stage1 → llc → clang and run; return stdout."""
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} missing — run scripts/build_stage1.py")
    _need("llc")
    _need("clang")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        s = d / "p.s"
        exe = d / "p"
        emit = subprocess.run(
            [str(STAGE1), "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(REPO),
        )
        assert emit.returncode == 0, (
            f"mnc-stage1 emit-llvm failed:\nstderr:\n{emit.stderr.decode()}"
        )
        compile_s = subprocess.run(
            ["llc", "-relocation-model=pic", str(ll), "-o", str(s)],
            capture_output=True,
        )
        assert compile_s.returncode == 0, compile_s.stderr.decode()
        link = subprocess.run(
            [
                "clang",
                "-fPIE",
                str(s),
                str(RUNTIME),
                "-o",
                str(exe),
                "-lm",
                "-lpthread",
                "-ldl",
            ],
            capture_output=True,
        )
        assert link.returncode == 0, link.stderr.decode()
        run = subprocess.run([str(exe)], capture_output=True, timeout=30)
        return run.stdout.decode()


def _parses_via_stage1(src: str) -> None:
    """Parse-only sanity: stage1 emit-llvm must succeed."""
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} missing — run scripts/build_stage1.py")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        emit = subprocess.run(
            [str(STAGE1), "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(REPO),
        )
        assert emit.returncode == 0, (
            f"parse failed via mnc-stage1:\nstderr:\n{emit.stderr.decode()}"
        )
        # Don't assert no parse-error spew — emit-llvm prints warnings on
        # stderr but succeeds on the happy path. Just check the IR exists.
        assert ll.exists() and ll.stat().st_size > 0


# ---------------------------------------------------------------------------
# Parser parity (4 cases — mirrored from tests/test_comprehensions.py).
# ---------------------------------------------------------------------------


def test_list_comp_parses_simple_stage1() -> None:
    _parses_via_stage1("fn main() { let xs: List<Int> = [x * 2 for x in 0..3] }")


def test_list_comp_parses_with_filter_stage1() -> None:
    _parses_via_stage1(
        "fn main() { let ev: List<Int> = [x for x in 0..10 if x % 2 == 0] }"
    )


def test_list_comp_parses_nested_stage1() -> None:
    _parses_via_stage1(
        "fn main() { let p: List<Int> = [a * b for a in 1..3 for b in 1..3] }"
    )


def test_map_comp_parses_stage1() -> None:
    _parses_via_stage1(
        "fn main() { let m: Map<Int, Int> = #{ k: k * 2 for k in 0..5 } }"
    )


# ---------------------------------------------------------------------------
# E2E parity (5 cases — same source as v5.15.0; same expected output).
# ---------------------------------------------------------------------------


def test_list_comp_doubles_stage1() -> None:
    out = _stage1_compile_and_run("""
fn main() {
    let xs: List<Int> = [1, 2, 3, 4, 5]
    let doubled: List<Int> = [x * 2 for x in xs]
    print(str(len(doubled)))
    print(str(doubled[0]))
    print(str(doubled[4]))
}
""")
    assert out.splitlines() == ["5", "2", "10"]


def test_list_comp_filter_stage1() -> None:
    out = _stage1_compile_and_run("""
fn main() {
    let xs: List<Int> = [1, 2, 3, 4, 5]
    let evens: List<Int> = [x for x in xs if x % 2 == 0]
    print(str(len(evens)))
    print(str(evens[0]))
    print(str(evens[1]))
}
""")
    assert out.splitlines() == ["2", "2", "4"]


def test_list_comp_range_stage1() -> None:
    out = _stage1_compile_and_run("""
fn main() {
    let squares: List<Int> = [i * i for i in 0..5]
    print(str(len(squares)))
    print(str(squares[3]))
}
""")
    assert out.splitlines() == ["5", "9"]


def test_list_comp_nested_stage1() -> None:
    out = _stage1_compile_and_run("""
fn main() {
    let products: List<Int> = [a * b for a in 1..4 for b in 1..4]
    let mut total: Int = 0
    for i in 0..len(products) {
        total = total + products[i]
    }
    print(str(len(products)))
    print(str(total))
}
""")
    assert out.splitlines() == ["9", "36"]


def test_map_comp_doubles_stage1() -> None:
    out = _stage1_compile_and_run("""
fn main() {
    let doubled: Map<Int, Int> = #{ k: k * 2 for k in 0..5 }
    print(str(len(doubled)))
    print(str(doubled[3]))
}
""")
    assert out.splitlines() == ["5", "6"]


# ---------------------------------------------------------------------------
# IR shape parity (1 case — the comp lowers to ListPush + for-loop blocks).
# ---------------------------------------------------------------------------


def test_comp_emits_listpush_and_for_loop_stage1() -> None:
    """Sanity check: comprehension IR contains the same primitive ops a
    hand-written loop would emit (ListPush inside a for-loop). Mirrors
    the v5.15.0 ``test_comp_emits_listpush_and_for_loop`` Python case.
    """
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} missing")
    src = (
        "fn main() { let r: List<Int> = [x * 2 for x in 0..3]; "
        "print(str(len(r))) }"
    )
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        emit = subprocess.run(
            [str(STAGE1), "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(REPO),
        )
        assert emit.returncode == 0, emit.stderr.decode()
        ir = ll.read_text()
        assert "__mn_list_push" in ir
        assert "for_header" in ir
        assert "for_body" in ir
