"""v5.45.0 Ts.2.B — tensor.view() through the Python LLVM emitter.

End-to-end: `.view(shape)` on a builtin Tensor compiles, links, and
runs. Verifies the new `__mn_tensor_view` C runtime export wires up
correctly.

This module is the Phase 2 baseline. Phase 5 self-host mirror unlocks
the same surface through stage1; Phase 6 adds the aliasing-write test
once semantic inference lets users write `view[i, j] = val` (multi-
index requires TENSOR type, not UNKNOWN, so semantic.py must infer
TENSOR for `.view()` / `.reshape()` results — that ships alongside
the self-host mirror).

Falsifiability — revert mapanare/lower.py:4060-4076 (the view +
reshape unified branch) and `test_view_basic_via_python_emitter`
fails: lower falls through to generic-method-call which emits an
unresolved `view` symbol; clang link fails.

Revert mapanare/emit_llvm_text.py:393-398 (drop the `__mn_tensor_view`
entry from `_RUNTIME_FN_ATTRS`) and the IR will still compile —
nounwind is a hint, not a correctness invariant — but the IR is no
longer documented as nounwind. Test does not lock this directly.

Revert mapanare/emit_llvm_text.py:3955-3970 (the unified call-emit
branch) and `test_view_ir_no_noalias` fails: the call falls back to
the generic emit path which does not understand __mn_tensor_view,
producing an unresolved symbol.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT_FOR_HELPER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT_FOR_HELPER / "tests"))
from _link_compat import darwin_link_extras  # noqa: E402

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
) -> str:
    """Compile via Python LLVM emitter; link with libmapanare_rt; run."""
    src_path = tmp_path / "view_test.mn"
    src_path.write_text(src)
    ll_path = tmp_path / "view_test.ll"
    bin_path = tmp_path / "view_test"
    env = os.environ.copy()
    env["MAPANARE_RELEASE"] = "1"  # silence dev-mode banner
    subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(src_path), "-o", str(ll_path)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )
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
            *darwin_link_extras(),
            "-o",
            str(bin_path),
        ],
        check=True,
        capture_output=True,
    )
    result = subprocess.run([str(bin_path)], capture_output=True, text=True, check=True)
    return result.stdout


def test_view_basic_via_python_emitter(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """`.view([2, 3])` on a 6-element 1D tensor produces a 2x3 view
    that aliases the source's data. Reads through the view return the
    original values. The view's metadata (rank, shape, size) reflect
    the new shape."""
    src = textwrap.dedent("""\
        fn main():
            let a = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
            let v = a.view([2, 3])
            print(str(tensor_rank(v)))
            print(str(tensor_size(v)))
            print(str(tensor_shape_dim(v, 0)))
            print(str(tensor_shape_dim(v, 1)))
            print(str(tensor_get_f64(v, 0)))
            print(str(tensor_get_f64(v, 5)))
        """)
    out = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert out.splitlines() == ["2", "6", "2", "3", "1", "6"]


def test_reshape_aliases_after_v5_45_0(
    runtime_archive: Path, clang_bin: str, tmp_path: Path
) -> None:
    """`.reshape()` at v5.45.0 routes through view (alias semantics).
    Surface API unchanged; result shares parent's data. The Phase 0
    audit confirmed zero production callers relied on v5.41.0 copy
    semantics, so this is breaking only in theory.

    Verified indirectly here: read-through-result and read-through-
    parent both return the correct values; aliasing-after-write is
    deferred to Phase 6 (needs semantic.py multi-index inference)."""
    src = textwrap.dedent("""\
        fn main():
            let a = Tensor<Float>[10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
            let r = a.reshape([3, 2])
            print(str(tensor_rank(r)))
            print(str(tensor_get_f64(r, 0)))
            print(str(tensor_get_f64(r, 5)))
            print(str(tensor_get_f64(a, 0)))
            print(str(tensor_get_f64(a, 5)))
        """)
    out = _emit_link_run(src, runtime_archive, clang_bin, tmp_path)
    assert out.splitlines() == ["2", "10", "60", "10", "60"]


def test_view_ir_no_noalias(runtime_archive: Path, tmp_path: Path) -> None:
    """The IR call to __mn_tensor_view must NOT carry `noalias` —
    the result aliases the parent's data buffer. Same invariant for
    __mn_tensor_reshape after the v5.45.0 swap."""
    src = textwrap.dedent("""\
        fn main():
            let a = Tensor<Float>[1.0, 2.0, 3.0, 4.0]
            let v = a.view([2, 2])
            print(str(tensor_size(v)))
            let r = a.reshape([4])
            print(str(tensor_size(r)))
        """)
    src_path = tmp_path / "view_ir.mn"
    src_path.write_text(src)
    ll_path = tmp_path / "view_ir.ll"
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
    # Declarations must not carry noalias return attribute.
    assert (
        "noalias ptr @__mn_tensor_view" not in ir
    ), "view declaration must not carry noalias — view aliases parent's data buffer"
    assert (
        "noalias ptr @__mn_tensor_reshape" not in ir
    ), "reshape declaration must not carry noalias post-v5.45.0 alias swap"
    # Call sites must use plain `call ptr`, not `call noalias ptr`.
    for line in ir.splitlines():
        if "@__mn_tensor_view" in line and "call" in line:
            assert "noalias" not in line, f"view call site must not carry noalias: {line!r}"
        if "@__mn_tensor_reshape" in line and "call" in line:
            assert "noalias" not in line, f"reshape call site must not carry noalias: {line!r}"


def test_view_size_mismatch_aborts(runtime_archive: Path, clang_bin: str, tmp_path: Path) -> None:
    """`.view()` with element count != parent's size aborts at
    runtime with a structured error message. Matches the v5.41.0
    reshape size-mismatch behavior."""
    src = textwrap.dedent("""\
        fn main():
            let a = Tensor<Float>[1.0, 2.0, 3.0, 4.0]
            let v = a.view([3, 3])
            print(str(tensor_size(v)))
        """)
    src_path = tmp_path / "view_mismatch.mn"
    src_path.write_text(src)
    ll_path = tmp_path / "view_mismatch.ll"
    bin_path = tmp_path / "view_mismatch"
    env = os.environ.copy()
    env["MAPANARE_RELEASE"] = "1"
    subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", str(src_path), "-o", str(ll_path)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "clang",
            str(ll_path),
            "-L",
            str(runtime_archive.parent),
            "-lmapanare_rt",
            "-lm",
            "-lpthread",
            "-ldl",
            *darwin_link_extras(),
            "-o",
            str(bin_path),
        ],
        check=True,
        capture_output=True,
    )
    result = subprocess.run([str(bin_path)], capture_output=True, text=True)
    assert result.returncode != 0, "size mismatch must abort"
    assert (
        "tensor view" in result.stderr.lower()
    ), f"expected structured tensor-view error in stderr; got: {result.stderr!r}"
    assert (
        "size 4" in result.stderr and "size 9" in result.stderr
    ), f"expected explicit source/target sizes in error; got: {result.stderr!r}"
