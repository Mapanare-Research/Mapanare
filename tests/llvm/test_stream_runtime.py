"""Tests for Phase 3 — C Runtime Stream (MnStream) implementation.

These tests compile and run the C runtime stream functions via ctypes to verify
correctness of the lazy stream system: from_list, map, filter, take, skip,
collect, fold, bounded backpressure, and chained pipelines.
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
    """Get a C function by name."""
    return getattr(lib, name)


# ctypes struct matching MnList layout: { char* data, i64 len, i64 cap, i64 elem_size }
class MnList(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_char_p),
        ("len", ctypes.c_int64),
        ("cap", ctypes.c_int64),
        ("elem_size", ctypes.c_int64),
    ]


# Map function type: void (*)(void *out, const void *in, void *user_data)
MAP_FN_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)

# Filter function type: int64_t (*)(const void *elem, void *user_data)
FILTER_FN_TYPE = ctypes.CFUNCTYPE(ctypes.c_int64, ctypes.c_void_p, ctypes.c_void_p)

# Fold function type: void (*)(void *acc, const void *elem, void *user_data)
FOLD_FN_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)


def _setup_stream_fns(lib):
    """Set up function signatures for stream operations."""
    fn = _fn(lib, "__mn_stream_from_list")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.POINTER(MnList), ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_map")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, MAP_FN_TYPE, ctypes.c_void_p, ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_filter")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, FILTER_FN_TYPE, ctypes.c_void_p]

    fn = _fn(lib, "__mn_stream_take")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_skip")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_collect")
    fn.restype = MnList
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_fold")
    fn.restype = None
    fn.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int64,
        FOLD_FN_TYPE,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]

    fn = _fn(lib, "__mn_stream_next")
    fn.restype = ctypes.c_int64
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_stream_bounded")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int64, ctypes.c_int64]

    fn = _fn(lib, "__mn_stream_free")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p]

    # List helpers
    fn = _fn(lib, "__mn_list_new")
    fn.restype = MnList
    fn.argtypes = [ctypes.c_int64]

    fn = _fn(lib, "__mn_list_push")
    fn.restype = None
    fn.argtypes = [ctypes.POINTER(MnList), ctypes.c_void_p]

    fn = _fn(lib, "__mn_list_get")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.POINTER(MnList), ctypes.c_int64]


def _make_int_list(lib, values: list[int]) -> MnList:
    """Create an MnList of int64 values."""
    lst = _fn(lib, "__mn_list_new")(8)
    for v in values:
        val = ctypes.c_int64(v)
        _fn(lib, "__mn_list_push")(ctypes.byref(lst), ctypes.byref(val))
    return lst


def _list_to_ints(lib, lst: MnList) -> list[int]:
    """Read all int64 values from an MnList."""
    result = []
    for i in range(lst.len):
        ptr = _fn(lib, "__mn_list_get")(ctypes.byref(lst), i)
        val = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
        result.append(val)
    return result


# ===========================================================================
# Test: Stream from list and collect
# ===========================================================================


class TestStreamFromList:
    """Tasks 1-2, 7, 9: Stream creation, next, collect."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_from_list_and_collect(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [10, 20, 30])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        result = _fn(lib, "__mn_stream_collect")(stream, 8)
        assert _list_to_ints(lib, result) == [10, 20, 30]
        _fn(lib, "__mn_stream_free")(stream)

    def test_empty_list(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        result = _fn(lib, "__mn_stream_collect")(stream, 8)
        assert result.len == 0
        _fn(lib, "__mn_stream_free")(stream)

    def test_next_pulls_elements(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        out = ctypes.c_int64(0)
        assert _fn(lib, "__mn_stream_next")(stream, ctypes.byref(out)) == 1
        assert out.value == 1
        assert _fn(lib, "__mn_stream_next")(stream, ctypes.byref(out)) == 1
        assert out.value == 2
        assert _fn(lib, "__mn_stream_next")(stream, ctypes.byref(out)) == 1
        assert out.value == 3
        assert _fn(lib, "__mn_stream_next")(stream, ctypes.byref(out)) == 0

        _fn(lib, "__mn_stream_free")(stream)

    def test_single_element(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [42])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        result = _fn(lib, "__mn_stream_collect")(stream, 8)
        assert _list_to_ints(lib, result) == [42]
        _fn(lib, "__mn_stream_free")(stream)


# ===========================================================================
# Test: Stream map
# ===========================================================================


class TestStreamMap:
    """Task 3: Lazy map transform."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_map_double(self):
        """Map each element to x * 2."""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def double_fn(out, inp, user_data):
            val = ctypes.cast(inp, ctypes.POINTER(ctypes.c_int64)).contents.value
            result = ctypes.c_int64(val * 2)
            ctypes.memmove(out, ctypes.byref(result), 8)

        map_cb = MAP_FN_TYPE(double_fn)
        mapped = _fn(lib, "__mn_stream_map")(stream, map_cb, None, 8)
        result = _fn(lib, "__mn_stream_collect")(mapped, 8)
        assert _list_to_ints(lib, result) == [2, 4, 6, 8, 10]

        _fn(lib, "__mn_stream_free")(mapped)
        _fn(lib, "__mn_stream_free")(stream)
        _ = map_cb

    def test_map_empty(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def identity_fn(out, inp, user_data):
            ctypes.memmove(out, inp, 8)

        map_cb = MAP_FN_TYPE(identity_fn)
        mapped = _fn(lib, "__mn_stream_map")(stream, map_cb, None, 8)
        result = _fn(lib, "__mn_stream_collect")(mapped, 8)
        assert result.len == 0

        _fn(lib, "__mn_stream_free")(mapped)
        _fn(lib, "__mn_stream_free")(stream)
        _ = map_cb


# ===========================================================================
# Test: Stream filter
# ===========================================================================


class TestStreamFilter:
    """Task 4: Lazy filter."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_filter_even(self):
        """Keep only even numbers."""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5, 6])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def is_even(elem, user_data):
            val = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            return 1 if val % 2 == 0 else 0

        pred_cb = FILTER_FN_TYPE(is_even)
        filtered = _fn(lib, "__mn_stream_filter")(stream, pred_cb, None)
        result = _fn(lib, "__mn_stream_collect")(filtered, 8)
        assert _list_to_ints(lib, result) == [2, 4, 6]

        _fn(lib, "__mn_stream_free")(filtered)
        _fn(lib, "__mn_stream_free")(stream)
        _ = pred_cb

    def test_filter_none_pass(self):
        """Filter removes all elements."""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 3, 5])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def is_even(elem, user_data):
            val = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            return 1 if val % 2 == 0 else 0

        pred_cb = FILTER_FN_TYPE(is_even)
        filtered = _fn(lib, "__mn_stream_filter")(stream, pred_cb, None)
        result = _fn(lib, "__mn_stream_collect")(filtered, 8)
        assert result.len == 0

        _fn(lib, "__mn_stream_free")(filtered)
        _fn(lib, "__mn_stream_free")(stream)
        _ = pred_cb


# ===========================================================================
# Test: Stream take
# ===========================================================================


class TestStreamTake:
    """Task 5: Take first N elements."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_take_3(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [10, 20, 30, 40, 50])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        taken = _fn(lib, "__mn_stream_take")(stream, 3)
        result = _fn(lib, "__mn_stream_collect")(taken, 8)
        assert _list_to_ints(lib, result) == [10, 20, 30]
        _fn(lib, "__mn_stream_free")(taken)
        _fn(lib, "__mn_stream_free")(stream)

    def test_take_more_than_available(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        taken = _fn(lib, "__mn_stream_take")(stream, 10)
        result = _fn(lib, "__mn_stream_collect")(taken, 8)
        assert _list_to_ints(lib, result) == [1, 2]
        _fn(lib, "__mn_stream_free")(taken)
        _fn(lib, "__mn_stream_free")(stream)

    def test_take_zero(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        taken = _fn(lib, "__mn_stream_take")(stream, 0)
        result = _fn(lib, "__mn_stream_collect")(taken, 8)
        assert result.len == 0
        _fn(lib, "__mn_stream_free")(taken)
        _fn(lib, "__mn_stream_free")(stream)


# ===========================================================================
# Test: Stream skip
# ===========================================================================


class TestStreamSkip:
    """Task 6: Skip first N elements."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_skip_2(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [10, 20, 30, 40, 50])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        skipped = _fn(lib, "__mn_stream_skip")(stream, 2)
        result = _fn(lib, "__mn_stream_collect")(skipped, 8)
        assert _list_to_ints(lib, result) == [30, 40, 50]
        _fn(lib, "__mn_stream_free")(skipped)
        _fn(lib, "__mn_stream_free")(stream)

    def test_skip_all(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        skipped = _fn(lib, "__mn_stream_skip")(stream, 5)
        result = _fn(lib, "__mn_stream_collect")(skipped, 8)
        assert result.len == 0
        _fn(lib, "__mn_stream_free")(skipped)
        _fn(lib, "__mn_stream_free")(stream)


# ===========================================================================
# Test: Stream fold
# ===========================================================================


class TestStreamFold:
    """Task 8: Fold (reduce) stream."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_fold_sum(self):
        """Sum all elements."""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def sum_fn(acc, elem, user_data):
            acc_ptr = ctypes.cast(acc, ctypes.POINTER(ctypes.c_int64))
            elem_val = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            acc_ptr.contents.value += elem_val

        fold_cb = FOLD_FN_TYPE(sum_fn)
        init = ctypes.c_int64(0)
        out = ctypes.c_int64(0)
        _fn(lib, "__mn_stream_fold")(
            stream, ctypes.byref(init), 8, fold_cb, None, ctypes.byref(out)
        )
        assert out.value == 15

        _fn(lib, "__mn_stream_free")(stream)
        _ = fold_cb

    def test_fold_product(self):
        """Product of all elements."""
        lib = _get_lib()
        lst = _make_int_list(lib, [2, 3, 4])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def mul_fn(acc, elem, user_data):
            acc_ptr = ctypes.cast(acc, ctypes.POINTER(ctypes.c_int64))
            elem_val = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            acc_ptr.contents.value *= elem_val

        fold_cb = FOLD_FN_TYPE(mul_fn)
        init = ctypes.c_int64(1)
        out = ctypes.c_int64(0)
        _fn(lib, "__mn_stream_fold")(
            stream, ctypes.byref(init), 8, fold_cb, None, ctypes.byref(out)
        )
        assert out.value == 24

        _fn(lib, "__mn_stream_free")(stream)
        _ = fold_cb


# ===========================================================================
# Test: Stream bounded (backpressure)
# ===========================================================================


class TestStreamBounded:
    """Task 10: Bounded stream with backpressure."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_bounded_collects_all(self):
        """Bounded stream should still yield all elements."""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        bounded = _fn(lib, "__mn_stream_bounded")(stream, 3, 8)
        result = _fn(lib, "__mn_stream_collect")(bounded, 8)
        assert _list_to_ints(lib, result) == [1, 2, 3, 4, 5]
        _fn(lib, "__mn_stream_free")(bounded)
        _fn(lib, "__mn_stream_free")(stream)

    def test_bounded_capacity_1(self):
        lib = _get_lib()
        lst = _make_int_list(lib, [10, 20, 30])
        stream = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        bounded = _fn(lib, "__mn_stream_bounded")(stream, 1, 8)
        result = _fn(lib, "__mn_stream_collect")(bounded, 8)
        assert _list_to_ints(lib, result) == [10, 20, 30]
        _fn(lib, "__mn_stream_free")(bounded)
        _fn(lib, "__mn_stream_free")(stream)


# ===========================================================================
# Test: Chained pipelines
# ===========================================================================


class TestStreamPipeline:
    """Combined: filter |> map |> take |> collect."""

    def setup_method(self):
        lib = _get_lib()
        _setup_stream_fns(lib)

    def test_filter_then_map(self):
        """[1..6] |> filter(>2) |> map(*10) |> collect() == [30, 40, 50, 60]"""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5, 6])
        s = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def gt2(elem, ud):
            v = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            return 1 if v > 2 else 0

        pred_cb = FILTER_FN_TYPE(gt2)
        s = _fn(lib, "__mn_stream_filter")(s, pred_cb, None)

        def mul10(out, inp, ud):
            v = ctypes.cast(inp, ctypes.POINTER(ctypes.c_int64)).contents.value
            r = ctypes.c_int64(v * 10)
            ctypes.memmove(out, ctypes.byref(r), 8)

        map_cb = MAP_FN_TYPE(mul10)
        s = _fn(lib, "__mn_stream_map")(s, map_cb, None, 8)

        result = _fn(lib, "__mn_stream_collect")(s, 8)
        assert _list_to_ints(lib, result) == [30, 40, 50, 60]
        _ = pred_cb, map_cb

    def test_skip_filter_take(self):
        """[1..10] |> skip(2) |> filter(odd) |> take(3) |> collect() == [3, 5, 7]"""
        lib = _get_lib()
        lst = _make_int_list(lib, list(range(1, 11)))
        s = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)
        s = _fn(lib, "__mn_stream_skip")(s, 2)

        def is_odd(elem, ud):
            v = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            return 1 if v % 2 != 0 else 0

        pred_cb = FILTER_FN_TYPE(is_odd)
        s = _fn(lib, "__mn_stream_filter")(s, pred_cb, None)
        s = _fn(lib, "__mn_stream_take")(s, 3)

        result = _fn(lib, "__mn_stream_collect")(s, 8)
        assert _list_to_ints(lib, result) == [3, 5, 7]
        _ = pred_cb

    def test_map_filter_fold(self):
        """[1..5] |> map(*2) |> filter(>4) |> fold(+, 0) == 6+8+10 = 24"""
        lib = _get_lib()
        lst = _make_int_list(lib, [1, 2, 3, 4, 5])
        s = _fn(lib, "__mn_stream_from_list")(ctypes.byref(lst), 8)

        def double(out, inp, ud):
            v = ctypes.cast(inp, ctypes.POINTER(ctypes.c_int64)).contents.value
            r = ctypes.c_int64(v * 2)
            ctypes.memmove(out, ctypes.byref(r), 8)

        map_cb = MAP_FN_TYPE(double)
        s = _fn(lib, "__mn_stream_map")(s, map_cb, None, 8)

        def gt4(elem, ud):
            v = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            return 1 if v > 4 else 0

        pred_cb = FILTER_FN_TYPE(gt4)
        s = _fn(lib, "__mn_stream_filter")(s, pred_cb, None)

        def sum_fn(acc, elem, ud):
            acc_ptr = ctypes.cast(acc, ctypes.POINTER(ctypes.c_int64))
            v = ctypes.cast(elem, ctypes.POINTER(ctypes.c_int64)).contents.value
            acc_ptr.contents.value += v

        fold_cb = FOLD_FN_TYPE(sum_fn)
        init = ctypes.c_int64(0)
        out = ctypes.c_int64(0)
        _fn(lib, "__mn_stream_fold")(s, ctypes.byref(init), 8, fold_cb, None, ctypes.byref(out))
        assert out.value == 24
        _ = map_cb, pred_cb, fold_cb
