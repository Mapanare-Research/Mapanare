"""v5.21.1 — Cross-bootstrap mirror for Te.6 chained comparisons.

Re-runs each of the four v5.21.0 chained-cmp goldens
(``tests/golden/92…95``) plus six hand-rolled inline cases through
both the Python bootstrap and the self-hosted ``mnc-stage1``, and
asserts byte-identical stdout. Acts as a regression guard for
v5.22.0+ panel verification of Te.6 once-evaluation and
precedence-merge behavior.

Each case:
- Python: ``python3 -m mapanare emit-llvm <src> -o <ll>``
- Native: ``mnc-stage1 emit-llvm <src> -o <ll>``
- Both LLs are linked with libmapanare_rt.a and run; outputs compared.

Mirror of ``tests/bootstrap/test_te5_mirror.py``.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
STAGE1 = REPO / "mapanare/self/mnc-stage1"
RT_A = REPO / "runtime/native/libmapanare_rt.a"

GOLDENS = [
    "92_chained_cmp_simple",
    "93_chained_cmp_4",
    "94_chained_cmp_mixed",
    "95_chained_cmp_side_effect",
]

INLINE_CASES = [
    (
        "chained_eq",
        """fn main():
    let r: Bool = 5 == 5 == 5
    print(str(r))
""",
    ),
    (
        "mixed_eq_cmp",
        """fn main():
    let a: Int = 1
    let b: Int = 1
    let c: Int = 2
    let r: Bool = a == b < c
    print(str(r))
""",
    ),
    (
        "non_trivial_middle",
        """fn middle(c: Int) -> Int:
    return c + 1

fn check(c: Int) -> Bool:
    return 0 < middle(c) < 10

fn main():
    print(str(check(4)))
    print(str(check(-1)))
    print(str(check(99)))
""",
    ),
    (
        "chain_in_if",
        """fn main():
    let x: Int = 5
    if 0 < x < 10:
        print("ok")
""",
    ),
    (
        "chain_in_let_typed",
        """fn main():
    let r: Bool = 1 < 2 < 3
    print(str(r))
""",
    ),
    (
        "chain_le_lt_mix",
        """fn main():
    let x: Int = 5
    let r: Bool = 0 <= x < 10
    print(str(r))
""",
    ),
]


def _need(tool: str) -> None:
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not available")


def _golden_path(stem: str) -> Path:
    return REPO / "tests/golden" / f"{stem}.mn"


def _compile_and_run(ll_emitter: list[str], src: Path, workdir: Path) -> str:
    """Run ``ll_emitter <src> -o <ll>`` then link with runtime + execute."""
    _need("clang")
    if not RT_A.exists():
        pytest.skip(f"{RT_A} missing — run `make build-rt`")
    ll = workdir / (src.stem + ".ll")
    binp = workdir / src.stem
    emit = subprocess.run(
        ll_emitter + [str(src), "-o", str(ll)],
        capture_output=True,
        cwd=str(REPO),
    )
    assert emit.returncode == 0, (
        f"emit failed for {src.name}:\n"
        f"cmd: {' '.join(ll_emitter)}\n"
        f"stderr:\n{emit.stderr.decode()}"
    )
    link = subprocess.run(
        [
            "clang",
            str(ll),
            str(RT_A),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(binp),
        ],
        capture_output=True,
    )
    assert link.returncode == 0, link.stderr.decode()
    run = subprocess.run([str(binp)], capture_output=True, timeout=30)
    return run.stdout.decode()


def _python_run(src: Path, workdir: Path) -> str:
    return _compile_and_run(
        ["python3", "-m", "mapanare", "emit-llvm"],
        src,
        workdir,
    )


def _stage1_run(src: Path, workdir: Path) -> str:
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} missing — run scripts/build_stage1.py")
    return _compile_and_run(
        [str(STAGE1), "emit-llvm"],
        src,
        workdir,
    )


@pytest.mark.parametrize("stem", GOLDENS)
def test_chained_cmp_golden_byte_identical(stem: str) -> None:
    """Each chained-cmp golden must produce identical stdout via Python
    and native. Specifically, golden 95 verifies the once-evaluation
    semantics of side-effecting middle terms — the load-bearing test."""
    src = _golden_path(stem)
    if not src.exists():
        pytest.skip(f"{src} not found")
    with tempfile.TemporaryDirectory() as td:
        py_out = _python_run(src, Path(td))
    with tempfile.TemporaryDirectory() as td2:
        nat_out = _stage1_run(src, Path(td2))
    assert py_out == nat_out, (
        f"divergence on {stem}:\n"
        f"  python: {py_out!r}\n"
        f"  native: {nat_out!r}"
    )


@pytest.mark.parametrize("name,source", INLINE_CASES, ids=[c[0] for c in INLINE_CASES])
def test_chained_cmp_inline_byte_identical(name: str, source: str) -> None:
    """Hand-rolled cases covering chain shapes not present in the goldens:
    chained ``==``, mixed eq+ordering (post-v5.21.0 precedence merge),
    non-trivial middle term (cross-checks once-eval IR shape between
    bootstraps), chain in if-condition position, typed-let chain, and
    half-open-range mixed ``<=``/``<`` form."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        src = d / f"{name}.mn"
        src.write_text(source)
        py_out = _python_run(src, Path(td))
    with tempfile.TemporaryDirectory() as td2:
        d2 = Path(td2)
        src2 = d2 / f"{name}.mn"
        src2.write_text(source)
        nat_out = _stage1_run(src2, Path(td2))
    assert py_out == nat_out, (
        f"divergence on {name}:\n"
        f"  python: {py_out!r}\n"
        f"  native: {nat_out!r}"
    )
