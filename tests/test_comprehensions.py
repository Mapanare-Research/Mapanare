"""v5.15.0 Te.2.B/C — list and map comprehensions.

These tests run through the **Python bootstrap only**. The stage1
mirror for comprehensions is deferred to v5.15.1 (mirroring the
v5.14.0 → v5.14.1 colon-block split). Implicit-return and terse
lambdas already mirror at v5.15.0 and are covered by the golden
corpus.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from mapanare.parser import parse

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_list_comp_parses_simple() -> None:
    src = "fn main() { let xs: List<Int> = [x * 2 for x in 0..3] }"
    program = parse(src)
    assert program.definitions[0].name == "main"


def test_list_comp_parses_with_filter() -> None:
    src = "fn main() { let ev: List<Int> = [x for x in 0..10 if x % 2 == 0] }"
    program = parse(src)
    assert program.definitions[0].name == "main"


def test_list_comp_parses_nested() -> None:
    src = "fn main() { let p: List<Int> = [a * b for a in 1..3 for b in 1..3] }"
    program = parse(src)
    assert program.definitions[0].name == "main"


def test_map_comp_parses() -> None:
    src = "fn main() { let m: Map<Int, Int> = #{ k: k * 2 for k in 0..5 } }"
    program = parse(src)
    assert program.definitions[0].name == "main"


# ---------------------------------------------------------------------------
# End-to-end execution via LLVM backend
# ---------------------------------------------------------------------------


def _compile_and_run(src: str) -> str:
    """Compile ``src`` through the Python bootstrap → LLVM IR → native
    binary, run it, and return stdout. Skips when clang or llc is
    unavailable in the runner environment.
    """
    if subprocess.run(["which", "clang"], capture_output=True).returncode != 0:
        pytest.skip("clang not available")
    if subprocess.run(["which", "llc"], capture_output=True).returncode != 0:
        pytest.skip("llc not available")
    repo = Path(__file__).resolve().parent.parent
    runtime = repo / "runtime/native/mapanare_core.c"
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        s = d / "p.s"
        exe = d / "p"
        emit = subprocess.run(
            ["python3", "-m", "mapanare", "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(repo),
        )
        assert emit.returncode == 0, emit.stderr.decode()
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
                str(runtime),
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


def test_list_comp_doubles() -> None:
    out = _compile_and_run("""
fn main() {
    let xs: List<Int> = [1, 2, 3, 4, 5]
    let doubled: List<Int> = [x * 2 for x in xs]
    print(str(len(doubled)))
    print(str(doubled[0]))
    print(str(doubled[4]))
}
""")
    assert out.splitlines() == ["5", "2", "10"]


def test_list_comp_filter() -> None:
    out = _compile_and_run("""
fn main() {
    let xs: List<Int> = [1, 2, 3, 4, 5]
    let evens: List<Int> = [x for x in xs if x % 2 == 0]
    print(str(len(evens)))
    print(str(evens[0]))
    print(str(evens[1]))
}
""")
    assert out.splitlines() == ["2", "2", "4"]


def test_list_comp_range() -> None:
    out = _compile_and_run("""
fn main() {
    let squares: List<Int> = [i * i for i in 0..5]
    print(str(len(squares)))
    print(str(squares[3]))
}
""")
    assert out.splitlines() == ["5", "9"]


def test_list_comp_nested() -> None:
    out = _compile_and_run("""
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


def test_map_comp_doubles() -> None:
    out = _compile_and_run("""
fn main() {
    let doubled: Map<Int, Int> = #{ k: k * 2 for k in 0..5 }
    print(str(len(doubled)))
    print(str(doubled[3]))
}
""")
    assert out.splitlines() == ["5", "6"]


# ---------------------------------------------------------------------------
# IR equivalence: comprehension ≡ hand-written loop (modulo SSA names).
# ---------------------------------------------------------------------------


def _emit_ir(src: str) -> str:
    repo = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as td:
        mn = Path(td) / "p.mn"
        ll = Path(td) / "p.ll"
        mn.write_text(src)
        r = subprocess.run(
            ["python3", "-m", "mapanare", "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(repo),
        )
        assert r.returncode == 0, r.stderr.decode()
        return ll.read_text()


def test_comp_emits_listpush_and_for_loop() -> None:
    """Sanity check: the comprehension's IR contains the same primitive
    operations a hand-written loop would emit (ListInit + ListPush
    inside a for-loop). Exact SSA-name parity is covered indirectly by
    the e2e tests above producing identical output to manual loops.
    """
    ir = _emit_ir("fn main() { let r: List<Int> = [x * 2 for x in 0..3]; print(str(len(r))) }")
    assert "__mn_list_push" in ir
    assert "for_header" in ir
    assert "for_body" in ir
