"""v5.16.0 — Cross-bootstrap mirror for string interpolation.

Re-runs the Phase 0 case matrix through ``mnc-stage1`` (the
self-hosted bootstrap) instead of the Python bootstrap, asserting
that each case produces stdout identical to the Python compiler.

Closes the v5.15.0-prep audit divergence: native ``mnc-stage1``
``"${name}"`` previously errored with "Undefined variable 'name}'".
After v5.16.0, both compilers lex / parse / lower interpolation the
same way and emit IR that runs to identical stdout.
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
    """Compile ``src`` via mnc-stage1 → clang and run; return stdout."""
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} missing — run scripts/build_stage1.py")
    _need("clang")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        exe = d / "p"
        emit = subprocess.run(
            [str(STAGE1), "emit-llvm", str(mn), "-o", str(ll)],
            capture_output=True,
            cwd=str(REPO),
        )
        assert emit.returncode == 0, (
            f"mnc-stage1 emit-llvm failed:\nstderr:\n{emit.stderr.decode()}"
        )
        link = subprocess.run(
            [
                "clang",
                "-o",
                str(exe),
                str(ll),
                str(RUNTIME),
                "-lm",
                "-lpthread",
            ],
            capture_output=True,
        )
        assert link.returncode == 0, link.stderr.decode()
        run = subprocess.run([str(exe)], capture_output=True)
        return run.stdout.decode()


def _python_compile_and_run(src: str) -> str:
    """Compile ``src`` via the Python bootstrap → clang and run."""
    _need("clang")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mn = d / "p.mn"
        mn.write_text(src)
        ll = d / "p.ll"
        exe = d / "p"
        emit = subprocess.run(
            [
                "python3",
                "-m",
                "mapanare",
                "emit-llvm",
                str(mn),
                "-o",
                str(ll),
            ],
            capture_output=True,
            cwd=str(REPO),
        )
        assert emit.returncode == 0, emit.stderr.decode()
        link = subprocess.run(
            [
                "clang",
                "-o",
                str(exe),
                str(ll),
                str(RUNTIME),
                "-lm",
                "-lpthread",
            ],
            capture_output=True,
        )
        assert link.returncode == 0, link.stderr.decode()
        run = subprocess.run([str(exe)], capture_output=True)
        return run.stdout.decode()


CASES = {
    "plain": 'fn main() {\n    print("hello")\n}\n',
    "var": (
        "fn main() {\n"
        '    let n: String = "world"\n'
        '    print("hi ${n}")\n'
        "}\n"
    ),
    "int": (
        "fn main() {\n"
        "    let n: Int = 42\n"
        '    print("n=${n}")\n'
        "}\n"
    ),
    "float": (
        "fn main() {\n"
        "    let f: Float = 3.14\n"
        '    print("f=${f}")\n'
        "}\n"
    ),
    "bool": (
        "fn main() {\n"
        "    let b: Bool = true\n"
        '    print("b=${b}")\n'
        "}\n"
    ),
    "method": (
        "fn main() {\n"
        '    let s: String = "hi"\n'
        '    print("${s.to_upper()}")\n'
        "}\n"
    ),
    "arith": (
        "fn main() {\n"
        '    print("sum=${1 + 2}")\n'
        "}\n"
    ),
    "multi": (
        "fn main() {\n"
        "    let a: Int = 1\n"
        "    let b: Int = 2\n"
        '    print("${a} and ${b}")\n'
        "}\n"
    ),
    "mixed": (
        "fn main() {\n"
        "    let x: Int = 7\n"
        '    print("[${x}] done")\n'
        "}\n"
    ),
    "escaped": (
        "fn main() {\n"
        '    print("\\${not_a_var}")\n'
        "}\n"
    ),
}


@pytest.mark.parametrize("case_name", sorted(CASES.keys()))
def test_string_interp_mirrors_python(case_name: str) -> None:
    """Native mnc-stage1 stdout must match Python bootstrap stdout."""
    src = CASES[case_name]
    py_out = _python_compile_and_run(src)
    nat_out = _stage1_compile_and_run(src)
    assert py_out == nat_out, (
        f"divergence on case {case_name!r}:\n"
        f"  python: {py_out!r}\n"
        f"  native: {nat_out!r}"
    )
