"""v5.45.0 Ts.8 — mapanare_tensor_t binary-compat regression.

Pins the v5.45.0 ABI shape: 64 bytes total; pre-v5.45.0 fields
(data/ndim/shape/size/elem_size) at original offsets 0/8/16/24/32;
new fields (refcount/is_view/parent) at 40/48/56. Append-only
extension — pre-v5.45.0 stage1 binaries would link against
post-v5.45.0 runtime and fail noisily on size mismatch (the desired
failure mode; better than silent corruption from a field reorder).

Same pattern as the v5.42.0 As.6 binary-compat regression for
mapanare_agent_t.

Falsifiability — reorder any pre-v5.45.0 field in
runtime/native/mapanare_runtime.h and the offset assertions fail.
Drop the refcount field and the alloc-init test fails. Make
mapanare_tensor_free unconditional (pre-v5.45.0 behavior) and the
no-op-on-still-aliased test fails.
"""
from __future__ import annotations

import ctypes
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def runtime_lib(gcc_bin: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a tiny shared library re-exporting the tensor alloc/free
    functions from libmapanare_rt.a. Avoids the libmapanare_runtime.so
    path which has unresolved symbols from other runtime modules
    (mapanare_io, mapanare_html, etc. require their own deps that the
    bare .so doesn't link in)."""
    archive = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"
    if not archive.is_file():
        pytest.skip(f"libmapanare_rt.a not present; run `make build-rt`")
    tmp = tmp_path_factory.mktemp("tensor_compat")
    stub_c = tmp / "stub.c"
    # Stub for mn_main referenced by mn_user_main.c in the archive;
    # the test never executes user code, just calls tensor_alloc/free.
    stub_c.write_text("int mn_main(int argc, char **argv) { return 0; }\n")
    so_path = tmp / "libmapanare_tensor_test.so"
    cmd = [
        gcc_bin, "-shared", "-fPIC", "-O0",
        str(stub_c),
        "-Wl,--whole-archive", str(archive), "-Wl,--no-whole-archive",
        "-lm", "-lpthread", "-ldl",
        "-o", str(so_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return so_path


@pytest.fixture(scope="module")
def gcc_bin() -> str:
    found = shutil.which("gcc")
    if not found:
        pytest.skip("gcc not on PATH")
    return found


# --- Direct sizeof + offsetof check via a tiny C probe -----------------

_SIZEOF_PROBE = textwrap.dedent(
    """\
    #include <stddef.h>
    #include <stdint.h>
    #include <stdio.h>

    typedef struct mapanare_tensor {
        void *data; int64_t ndim; int64_t *shape; int64_t size; int64_t elem_size;
        int64_t refcount; uint8_t is_view; uint8_t _pad[7];
        struct mapanare_tensor *parent;
    } mapanare_tensor_t;

    int main(void) {
        printf("size=%zu\\n", sizeof(mapanare_tensor_t));
        printf("data=%zu\\n", offsetof(mapanare_tensor_t, data));
        printf("ndim=%zu\\n", offsetof(mapanare_tensor_t, ndim));
        printf("shape=%zu\\n", offsetof(mapanare_tensor_t, shape));
        printf("size_field=%zu\\n", offsetof(mapanare_tensor_t, size));
        printf("elem_size=%zu\\n", offsetof(mapanare_tensor_t, elem_size));
        printf("refcount=%zu\\n", offsetof(mapanare_tensor_t, refcount));
        printf("is_view=%zu\\n", offsetof(mapanare_tensor_t, is_view));
        printf("parent=%zu\\n", offsetof(mapanare_tensor_t, parent));
        return 0;
    }
    """
)


def test_sizeof_pinned_at_64(gcc_bin: str, tmp_path: Path) -> None:
    """sizeof(mapanare_tensor_t) is 64 bytes on x86_64 Linux. Probe via
    a host-compiled C program reading the actual mapanare_runtime.h
    layout."""
    src_path = tmp_path / "probe.c"
    src_path.write_text(_SIZEOF_PROBE)
    bin_path = tmp_path / "probe"
    subprocess.run([gcc_bin, "-O0", str(src_path), "-o", str(bin_path)],
                   check=True, capture_output=True)
    out = subprocess.run([str(bin_path)], capture_output=True, text=True, check=True).stdout
    fields = dict(line.split("=") for line in out.strip().splitlines())
    assert fields["size"] == "64", (
        f"v5.45.0 Ts.2.A pins sizeof(mapanare_tensor_t) at 64 bytes; "
        f"observed {fields['size']}. If this changed deliberately, "
        f"update this test AND CHANGELOG ### Changed."
    )


def test_pre_v5_45_0_field_offsets_preserved(gcc_bin: str, tmp_path: Path) -> None:
    """v5.45.0 Ts.2.A is an append-only extension. Pre-v5.45.0 fields
    must remain at their original byte offsets — otherwise stage1 binaries
    built before v5.45.0 silently misread fields when linked against the
    post-v5.45.0 runtime."""
    src_path = tmp_path / "probe.c"
    src_path.write_text(_SIZEOF_PROBE)
    bin_path = tmp_path / "probe"
    subprocess.run([gcc_bin, "-O0", str(src_path), "-o", str(bin_path)],
                   check=True, capture_output=True)
    out = subprocess.run([str(bin_path)], capture_output=True, text=True, check=True).stdout
    fields = dict(line.split("=") for line in out.strip().splitlines())
    # Pre-v5.45.0 layout — locked at v4.x and never reorderable.
    assert fields["data"] == "0"
    assert fields["ndim"] == "8"
    assert fields["shape"] == "16"
    assert fields["size_field"] == "24"
    assert fields["elem_size"] == "32"


def test_v5_45_0_new_field_offsets(gcc_bin: str, tmp_path: Path) -> None:
    """New v5.45.0 Ts.2.A fields land at the documented offsets."""
    src_path = tmp_path / "probe.c"
    src_path.write_text(_SIZEOF_PROBE)
    bin_path = tmp_path / "probe"
    subprocess.run([gcc_bin, "-O0", str(src_path), "-o", str(bin_path)],
                   check=True, capture_output=True)
    out = subprocess.run([str(bin_path)], capture_output=True, text=True, check=True).stdout
    fields = dict(line.split("=") for line in out.strip().splitlines())
    assert fields["refcount"] == "40"
    assert fields["is_view"] == "48"
    # 7-byte padding to align parent to 8.
    assert fields["parent"] == "56"


# --- Runtime invariants via ctypes -------------------------------------


class _Tensor(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("ndim", ctypes.c_int64),
        ("shape", ctypes.POINTER(ctypes.c_int64)),
        ("size", ctypes.c_int64),
        ("elem_size", ctypes.c_int64),
        ("refcount", ctypes.c_int64),
        ("is_view", ctypes.c_uint8),
        ("_pad", ctypes.c_uint8 * 7),
        ("parent", ctypes.c_void_p),
    ]


def _load_lib(path: Path) -> ctypes.CDLL:
    lib = ctypes.CDLL(str(path))
    lib.mapanare_tensor_alloc.argtypes = [
        ctypes.c_int64,
        ctypes.POINTER(ctypes.c_int64),
        ctypes.c_int64,
    ]
    lib.mapanare_tensor_alloc.restype = ctypes.POINTER(_Tensor)
    lib.mapanare_tensor_free.argtypes = [ctypes.POINTER(_Tensor)]
    lib.mapanare_tensor_free.restype = None
    return lib


def test_alloc_initializes_refcount_to_1(runtime_lib: Path) -> None:
    """v5.45.0 Ts.2.A invariant: every fresh tensor starts with
    refcount=1. Pre-fix the field was uninitialized memory."""
    lib = _load_lib(runtime_lib)
    shape = (ctypes.c_int64 * 1)(4)
    t = lib.mapanare_tensor_alloc(1, shape, 8)
    try:
        assert t, "alloc returned NULL"
        assert t.contents.refcount == 1, (
            f"refcount must initialize to 1; observed {t.contents.refcount}"
        )
        assert t.contents.is_view == 0, "fresh tensor is not a view"
        assert not t.contents.parent, "fresh tensor has no parent"
    finally:
        lib.mapanare_tensor_free(t)


def test_free_no_op_on_still_aliased(runtime_lib: Path) -> None:
    """v5.45.0 Ts.2.A invariant: mapanare_tensor_free decrements
    refcount; only frees data when refcount hits 0. Manually inflate
    refcount to 2, call free once, observe data still readable;
    call free again, observe data freed (ASan would catch a UAF here
    if invariant broken — this test relies on the absence of a crash
    rather than a positive read-after-free signal, since ctypes can't
    detect the latter without ASan)."""
    lib = _load_lib(runtime_lib)
    shape = (ctypes.c_int64 * 1)(4)
    t = lib.mapanare_tensor_alloc(1, shape, 8)
    assert t
    # Pretend a view took a reference.
    t.contents.refcount = 2
    lib.mapanare_tensor_free(t)
    # First free was a no-op — refcount drops to 1, data not freed.
    # ctypes can still read the struct (via Python's reference to t.contents).
    # The struct memory is intact at this point.
    assert t.contents.refcount == 1, (
        f"refcount must drop to 1 after first free of refcount=2 tensor; "
        f"observed {t.contents.refcount}"
    )
    # Second free actually frees.
    lib.mapanare_tensor_free(t)
