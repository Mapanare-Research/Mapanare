"""Tests for Phase 1 — C Runtime Map (MnMap) implementation.

These tests compile and run the C runtime map functions via ctypes to verify
correctness of the Robin Hood hash table implementation without requiring
the full LLVM compilation pipeline.
"""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import tempfile

import pytest

_IS_WINDOWS = platform.system() == "Windows"

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "runtime", "native")
CORE_C = os.path.join(RUNTIME_DIR, "mapanare_core.c")


def _find_c_compiler() -> str | None:
    for cc in ["gcc", "cl"]:
        try:
            flag = "--version" if cc == "gcc" else "/?"
            result = subprocess.run([cc, flag], capture_output=True, timeout=10)
            if result.returncode == 0:
                return cc
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


_TMPDIR = None
_LIB = None
_COMPILE_ATTEMPTED = False


def _compile_runtime() -> ctypes.CDLL | None:
    global _TMPDIR
    cc = _find_c_compiler()
    if cc is None:
        return None

    _TMPDIR = tempfile.mkdtemp()

    if cc == "cl":
        lib_path = os.path.join(_TMPDIR, "mapanare_core.dll")
        cmd = [
            "cl",
            "/nologo",
            "/LD",
            f"/I{RUNTIME_DIR}",
            CORE_C,
            f"/Fe:{lib_path}",
            f"/Fo:{_TMPDIR}\\",
        ]
    else:
        ext = ".dll" if _IS_WINDOWS else ".so"
        lib_path = os.path.join(_TMPDIR, f"libmapanare_core{ext}")
        cmd = ["gcc", "-shared", "-O1", f"-I{RUNTIME_DIR}", CORE_C, "-o", lib_path]
        if not _IS_WINDOWS:
            cmd.insert(2, "-fPIC")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    try:
        return ctypes.CDLL(lib_path)
    except OSError:
        return None


def _get_lib() -> ctypes.CDLL:
    global _LIB, _COMPILE_ATTEMPTED
    if not _COMPILE_ATTEMPTED:
        _COMPILE_ATTEMPTED = True
        _LIB = _compile_runtime()
    if _LIB is None:
        pytest.skip("C compiler not available or compilation failed")
    return _LIB


def _fn(lib, name):
    """Get a C function by name, avoiding Python name mangling of __ prefixes."""
    return getattr(lib, name)


def _setup_map_fns(lib):
    """Set up function signatures for map operations."""
    fn = _fn(lib, "__mn_map_new")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.c_int64]

    fn = _fn(lib, "__mn_map_set")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_get")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_del")
    fn.restype = ctypes.c_int64
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_len")
    fn.restype = ctypes.c_int64
    fn.argtypes = [ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_contains")
    fn.restype = ctypes.c_int64
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_iter_new")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_iter_next")
    fn.restype = ctypes.c_int64
    fn.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]

    fn = _fn(lib, "__mn_map_iter_free")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p]

    fn = _fn(lib, "__mn_map_free")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p]


# Convenience wrappers
def _map_new(lib, ks=8, vs=8, kt=0):
    return _fn(lib, "__mn_map_new")(ks, vs, kt)


def _map_set(lib, m, k, v):
    return _fn(lib, "__mn_map_set")(m, ctypes.byref(k), ctypes.byref(v))


def _map_get(lib, m, k):
    return _fn(lib, "__mn_map_get")(m, ctypes.byref(k))


def _map_del(lib, m, k):
    return _fn(lib, "__mn_map_del")(m, ctypes.byref(k))


def _map_len(lib, m):
    return _fn(lib, "__mn_map_len")(m)


def _map_contains(lib, m, k):
    return _fn(lib, "__mn_map_contains")(m, ctypes.byref(k))


def _map_free(lib, m):
    return _fn(lib, "__mn_map_free")(m)


# ===========================================================================
# Test: Hash functions
# ===========================================================================


class TestHashFunctions:
    """Task 10: Hash functions."""

    def test_hash_int_deterministic(self):
        lib = _get_lib()
        fn = _fn(lib, "__mn_hash_int")
        fn.restype = ctypes.c_uint64
        fn.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        val = ctypes.c_int64(42)
        h1 = fn(ctypes.byref(val))
        h2 = fn(ctypes.byref(val))
        assert h1 == h2

    def test_hash_int_different_values(self):
        lib = _get_lib()
        fn = _fn(lib, "__mn_hash_int")
        fn.restype = ctypes.c_uint64
        fn.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        v1 = ctypes.c_int64(1)
        v2 = ctypes.c_int64(2)
        h1 = fn(ctypes.byref(v1))
        h2 = fn(ctypes.byref(v2))
        assert h1 != h2

    def test_hash_float_deterministic(self):
        lib = _get_lib()
        fn = _fn(lib, "__mn_hash_float")
        fn.restype = ctypes.c_uint64
        fn.argtypes = [ctypes.POINTER(ctypes.c_double)]
        val = ctypes.c_double(3.14)
        h1 = fn(ctypes.byref(val))
        h2 = fn(ctypes.byref(val))
        assert h1 == h2


# ===========================================================================
# Test: Map operations
# ===========================================================================


class TestMapOperations:
    """Tasks 1-9: Map creation, set, get, del, len, contains, iteration."""

    def setup_method(self):
        lib = _get_lib()
        _setup_map_fns(lib)

    def test_map_new_and_len(self):
        lib = _get_lib()
        m = _map_new(lib)
        assert m is not None
        assert _map_len(lib, m) == 0
        _map_free(lib, m)

    def test_map_set_and_get(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(42)
        val = ctypes.c_int64(100)
        _map_set(lib, m, key, val)
        assert _map_len(lib, m) == 1

        result_ptr = _map_get(lib, m, key)
        assert result_ptr is not None
        result = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
        assert result == 100
        _map_free(lib, m)

    def test_map_update_existing_key(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(1)
        _map_set(lib, m, key, ctypes.c_int64(10))
        _map_set(lib, m, key, ctypes.c_int64(20))
        assert _map_len(lib, m) == 1
        result_ptr = _map_get(lib, m, key)
        result = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
        assert result == 20
        _map_free(lib, m)

    def test_map_get_missing_key(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(999)
        assert _map_get(lib, m, key) is None
        _map_free(lib, m)

    def test_map_contains(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(5)
        assert _map_contains(lib, m, key) == 0
        _map_set(lib, m, key, ctypes.c_int64(50))
        assert _map_contains(lib, m, key) == 1
        _map_free(lib, m)

    def test_map_del(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(7)
        _map_set(lib, m, key, ctypes.c_int64(70))
        assert _map_len(lib, m) == 1
        assert _map_del(lib, m, key) == 1
        assert _map_len(lib, m) == 0
        assert _map_get(lib, m, key) is None
        _map_free(lib, m)

    def test_map_del_missing_key(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(999)
        assert _map_del(lib, m, key) == 0
        _map_free(lib, m)

    def test_map_many_entries(self):
        lib = _get_lib()
        m = _map_new(lib)
        n = 50
        for i in range(n):
            _map_set(lib, m, ctypes.c_int64(i), ctypes.c_int64(i * 10))
        assert _map_len(lib, m) == n
        for i in range(n):
            key = ctypes.c_int64(i)
            result_ptr = _map_get(lib, m, key)
            assert result_ptr is not None, f"Key {i} not found"
            result = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
            assert result == i * 10
        _map_free(lib, m)

    def test_map_iterator(self):
        lib = _get_lib()
        m = _map_new(lib)
        entries = {1: 10, 2: 20, 3: 30}
        for k, v in entries.items():
            _map_set(lib, m, ctypes.c_int64(k), ctypes.c_int64(v))

        it = _fn(lib, "__mn_map_iter_new")(m)
        found = {}
        key_out = ctypes.c_void_p()
        val_out = ctypes.c_void_p()

        while _fn(lib, "__mn_map_iter_next")(it, ctypes.byref(key_out), ctypes.byref(val_out)):
            k = ctypes.cast(key_out, ctypes.POINTER(ctypes.c_int64)).contents.value
            v = ctypes.cast(val_out, ctypes.POINTER(ctypes.c_int64)).contents.value
            found[k] = v

        assert found == entries
        _fn(lib, "__mn_map_iter_free")(it)
        _map_free(lib, m)

    def test_map_delete_and_reinsert(self):
        lib = _get_lib()
        m = _map_new(lib)
        key = ctypes.c_int64(42)
        _map_set(lib, m, key, ctypes.c_int64(100))
        _map_del(lib, m, key)
        _map_set(lib, m, key, ctypes.c_int64(200))
        assert _map_len(lib, m) == 1
        result_ptr = _map_get(lib, m, key)
        result = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
        assert result == 200
        _map_free(lib, m)
