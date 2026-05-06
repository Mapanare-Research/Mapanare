"""v5.45.0 Ts.3.B — `t[start..end:step]` end-to-end through Python emitter.

Covers:
- step=2 picks every other element (basic case)
- step=3 with non-multiple range (size = ceil((end-start)/step))
- step=1 equivalent to non-stepped slice (regression baseline)
- step ≤ 0 literal rejected at lower time with diagnostic
- step ≤ 0 non-literal aborted at runtime
- 2D tensor with mixed stepped + non-stepped axes

Falsifiability — revert mapanare/lower.py::_lower_tensor_slice (the
v5.45.0 step-aware branch reverting to v4.45.0 single-fn shape) and
the call falls back to __mn_tensor_slice which lacks the steps
array; multi-stepped tests would either silently produce wrong
results or fail to compile.

Revert mapanare/emit_llvm_text.py::__mn_tensor_step_slice handler
and the link fails with an unresolved symbol from the lowered Call.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    archive = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"
    if not archive.is_file():
        pytest.skip(f"libmapanare_rt.a not present at {archive}; run `make build-rt`")
    return archive


@pytest.fixture(scope="module")
def clang_bin() -> str:
    found = shutil.which("clang")
    if not found:
        pytest.skip("clang not on PATH")
    return found


def _emit_link_run(
    src: str,
    runtime_archive: Path,
    clang_bin: str,
    tmp_path: Path,
    expect_compile_error: bool = False,
) -> tuple[str, str, int]:
    src_path = tmp_path / "step_test.mn"
    src_path.write_text(src)
    ll_path = tmp_path / "step_test.ll"
    bin_path = tmp_path / "step_test"
    env = os.environ.copy()
    env["MAPANARE_RELEASE"] = "1"
    emit = subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(src_path), "-o", str(ll_path)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if expect_compile_error:
        return emit.stdout, emit.stderr, emit.returncode
    assert emit.returncode == 0, f"emit-llvm failed: {emit.stderr}"
    subprocess.run(
        [
            clang_bin,
            str(ll_path),
            "-L",
            str(runtime_archive.parent),
            "-lmapanare_rt",
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        check=True,
        capture_output=True,
    )
    result = subprocess.run([str(bin_path)], capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def test_step_2_basic(runtime_archive: Path, clang_bin: str, tmp_path: Path) -> None:
    """`t[0..6:2]` on a 6-element 1D tensor returns 3 elements: 0, 2, 4."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
            let s = t[0..6:2]
            print(str(tensor_size(s)))
            print(str(tensor_get_f64(s, 0)))
            print(str(tensor_get_f64(s, 1)))
            print(str(tensor_get_f64(s, 2)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert rc == 0, f"runtime err: {err}"
    assert out.splitlines() == ["3", "1", "3", "5"]


def test_step_3_non_multiple(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """`t[0..6:3]` returns 2 elements: ceil(6/3) = 2 (indices 0 and 3)."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
            let s = t[0..6:3]
            print(str(tensor_size(s)))
            print(str(tensor_get_f64(s, 0)))
            print(str(tensor_get_f64(s, 1)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert rc == 0
    assert out.splitlines() == ["2", "10", "40"]


def test_step_1_equivalent_to_unstepped(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """`t[0..4:1]` and `t[0..4]` produce the same elements (step=1 is
    pass-through). Lower picks __mn_tensor_step_slice for the explicit
    step=1 form even though it's redundant."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0, 4.0]
            let stepped = t[0..4:1]
            let plain = t[0..4]
            print(str(tensor_size(stepped)))
            print(str(tensor_size(plain)))
            print(str(tensor_get_f64(stepped, 0)))
            print(str(tensor_get_f64(stepped, 3)))
            print(str(tensor_get_f64(plain, 0)))
            print(str(tensor_get_f64(plain, 3)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert rc == 0
    assert out.splitlines() == ["4", "4", "1", "4", "1", "4"]


def test_step_zero_literal_rejected_at_lower(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """Literal step=0 raises a clear lower-time error. Reverse iteration
    (negative step) is reserved for v6.0; step=0 would loop forever."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0]
            let s = t[0..3:0]
            print(str(tensor_size(s)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path, expect_compile_error=True)
    assert rc != 0
    assert "positive integer step" in err
    assert "got 0" in err


def test_step_negative_literal_rejected_at_lower(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """Literal step=-1 raises a clear lower-time error."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0]
            let s = t[0..3:-1]
            print(str(tensor_size(s)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path, expect_compile_error=True)
    assert rc != 0
    assert "positive integer step" in err


def test_step_negative_non_literal_aborts_at_runtime(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """Non-literal step that evaluates negative aborts at runtime with a
    structured diagnostic. Lower-time rejection only catches literals;
    runtime is the backstop."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0]
            let mut k = 1
            k = k - 5
            let s = t[0..3:k]
            print(str(tensor_size(s)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert rc != 0, "negative runtime step must abort"
    assert "tensor step slice" in err.lower()
    assert "step must be positive" in err.lower()


def test_2d_mixed_axes(runtime_archive: Path, clang_bin: str, tmp_path: Path) -> None:
    """2D tensor [[1,2,3,4],[5,6,7,8]] sliced as `[:, 0..4:2]`:
    columns 0 and 2 from both rows -> [[1,3],[5,7]]."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]
            let s = t[0..2, 0..4:2]
            print(str(tensor_rank(s)))
            print(str(tensor_shape_dim(s, 0)))
            print(str(tensor_shape_dim(s, 1)))
            print(str(tensor_size(s)))
            print(str(tensor_get_f64(s, 0)))
            print(str(tensor_get_f64(s, 1)))
            print(str(tensor_get_f64(s, 2)))
            print(str(tensor_get_f64(s, 3)))
        """
    )
    out, err, rc = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert rc == 0, f"runtime err: {err}"
    assert out.splitlines() == ["2", "2", "2", "4", "1", "3", "5", "7"]


def test_step_slice_ir_shape_no_noalias(
    runtime_archive: Path, tmp_path: Path
) -> None:
    """The IR for stepped-slice calls is `call ptr @__mn_tensor_step_slice`
    with no `noalias` attribute (consistent with v5.45.0 conservative
    omission across tensor-producing exports)."""
    src = textwrap.dedent(
        """\
        fn main():
            let t = Tensor<Float>[1.0, 2.0, 3.0, 4.0]
            let s = t[0..4:2]
            print(str(tensor_size(s)))
        """
    )
    src_path = tmp_path / "step_ir.mn"
    src_path.write_text(src)
    ll_path = tmp_path / "step_ir.ll"
    env = os.environ.copy()
    env["MAPANARE_RELEASE"] = "1"
    subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(src_path), "-o", str(ll_path)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )
    ir = ll_path.read_text()
    assert "noalias ptr @__mn_tensor_step_slice" not in ir, (
        "step_slice declaration must not carry noalias"
    )
    for line in ir.splitlines():
        if "@__mn_tensor_step_slice" in line and "call" in line:
            assert "noalias" not in line, (
                f"step_slice call must not carry noalias: {line!r}"
            )
    # Sanity: the call site must exist and reference the export.
    assert "@__mn_tensor_step_slice(" in ir
