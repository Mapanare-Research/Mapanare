"""v5.41.0 Ts.1 — tensor.reshape end-to-end through the LLVM backend.

Closes part 1 of the v5.x tensor parity gap. The `Tensor` type's
`reshape(shape)` method now compiles through both the Python
bootstrap emitter and the self-hosted compiler (`mnc-stage1`),
links against `libmapanare_rt.a`, and produces correct output
end-to-end.

v5.41.0 ships **copy semantics** — `__mn_tensor_reshape` allocates
a fresh tensor and memcpys the source data. Mutations to either
tensor are independent. v5.41.1 will swap to refcount-based
aliasing (the `noalias` attribute on the C export will drop at
that release); the user-visible surface and these tests stay
unchanged.

Mutable views and stepped slices are deferred to v5.41.1.

Falsifiability anchor: reverting either the Python lower branch
(`_lower_method_call` in `mapanare/lower.py`) or the self-host
lower branch (`lower_method_call` in `mapanare/self/lower.mn`)
makes `test_reshape_via_python_emitter` or `test_reshape_via_stage1`
respectively fail because the `t.reshape(...)` call falls into
the generic-method-call path which has no matching runtime fn.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"
STAGE1 = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

GOLDEN = GOLDEN_DIR / "96_tensor_reshape.mn"

EXPECTED_OUTPUT = """\
2
6
2
3
1
6
1
6
10
40
60
4
3
1
12
2
100
400
3
12
1
12
1
1
"""


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    if not RT_ARCHIVE.exists():
        pytest.skip(f"{RT_ARCHIVE} not built; run `make build-rt` first")
    return RT_ARCHIVE


@pytest.fixture(scope="module")
def clang_bin() -> str:
    path = shutil.which("clang")
    if path is None:
        pytest.skip("clang not on PATH")
    return path


@pytest.fixture(scope="module")
def llvm_as_bin() -> str:
    path = shutil.which("llvm-as")
    if path is None:
        pytest.skip("llvm-as not on PATH")
    return path


def _link_and_run(ir_path: Path, runtime: Path, clang: str, tmp_path: Path) -> str:
    bc = tmp_path / "out.bc"
    exe = tmp_path / "out.bin"
    llvm_as = shutil.which("llvm-as")
    assert llvm_as is not None, "llvm-as required"
    subprocess.run([llvm_as, str(ir_path), "-o", str(bc)], check=True, timeout=30)
    subprocess.run(
        [clang, str(bc), str(runtime), "-lm", "-lpthread", "-ldl", "-o", str(exe)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    res = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, f"runtime failed: stderr={res.stderr}"
    return res.stdout


def test_reshape_via_python_emitter(runtime_archive: Path, clang_bin: str, tmp_path: Path) -> None:
    """End-to-end via the Python bootstrap LLVM emitter.

    Falsifiability: revert the reshape branch in
    `mapanare/lower.py::_lower_method_call`. The call falls through
    to the generic method dispatch; the linker fails because
    there is no `reshape` symbol exported by the runtime.
    """
    ir_path = tmp_path / "out.ll"
    res = subprocess.run(
        [
            "python3",
            "-m",
            "mapanare",
            "emit-llvm",
            str(GOLDEN),
            "-o",
            str(ir_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    assert res.returncode == 0, f"emit-llvm failed: {res.stderr}"
    ir = ir_path.read_text()
    assert "__mn_tensor_reshape" in ir, (
        "expected `__mn_tensor_reshape` call in emitted IR; "
        "Python lowering branch may be broken."
    )
    out = _link_and_run(ir_path, runtime_archive, clang_bin, tmp_path)
    assert out == EXPECTED_OUTPUT, f"output mismatch:\n{out!r}\nexpected:\n{EXPECTED_OUTPUT!r}"


def test_reshape_via_stage1(runtime_archive: Path, clang_bin: str, tmp_path: Path) -> None:
    """End-to-end through `mnc-stage1` (self-hosted compiler).

    Locks the lower + emit pair in `mapanare/self/lower.mn` and
    `mapanare/self/emit_llvm.mn`. Falsifiability: revert the
    reshape branch in either file; the stage1 binary produces
    IR that either references an undeclared symbol or routes
    through the generic-call path, both of which fail link.
    """
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} not built; run `python3 scripts/build_stage1.py` first")
    ir_path = tmp_path / "stage1.ll"
    res = subprocess.run(
        [str(STAGE1), "emit-llvm", str(GOLDEN)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"mnc-stage1 emit-llvm failed: {res.stderr}"
    ir_path.write_text(res.stdout)
    assert "__mn_tensor_reshape" in res.stdout, (
        "expected `__mn_tensor_reshape` call in stage1 IR; "
        "self-host lowering branch may be broken."
    )
    out = _link_and_run(ir_path, runtime_archive, clang_bin, tmp_path)
    assert out == EXPECTED_OUTPUT, f"output mismatch:\n{out!r}\nexpected:\n{EXPECTED_OUTPUT!r}"


def test_reshape_size_mismatch_aborts(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """Mismatched-size reshape aborts with a structured message.

    `__mn_tensor_reshape` validates total element count and aborts
    via fprintf+abort (exit 134) if the new shape's product
    differs from the source size. Lock that contract here so the
    error path doesn't silently regress to NULL-deref or wrong
    behavior.
    """
    src = tmp_path / "abort.mn"
    src.write_text("""fn main():
    let t = Tensor<Float>[1.0, 2.0, 3.0]
    let r = t.reshape([2, 2])
    print(str(tensor_size(r)))
""")
    ir_path = tmp_path / "abort.ll"
    res = subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(src), "-o", str(ir_path)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    assert res.returncode == 0, f"emit-llvm failed: {res.stderr}"
    bc = tmp_path / "abort.bc"
    exe = tmp_path / "abort.bin"
    llvm_as = shutil.which("llvm-as")
    subprocess.run([llvm_as, str(ir_path), "-o", str(bc)], check=True, timeout=30)
    subprocess.run(
        [
            clang_bin,
            str(bc),
            str(runtime_archive),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(exe),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    res2 = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
    assert res2.returncode != 0, "expected non-zero exit on size mismatch"
    assert (
        "tensor reshape" in res2.stderr
    ), f"expected structured abort message, got stderr={res2.stderr!r}"
    assert (
        "cannot reshape size 3" in res2.stderr
    ), f"expected size diagnostic, got stderr={res2.stderr!r}"
