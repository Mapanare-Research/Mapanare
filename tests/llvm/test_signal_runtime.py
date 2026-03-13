"""Tests for Phase 2 — C Runtime Signal (MnSignal) implementation.

These tests compile and run the C runtime signal functions via ctypes to verify
correctness of the reactive signal system: dependency tracking, computed signals,
subscriber notification, batched updates, and topological propagation.
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


def _setup_signal_fns(lib):
    """Set up function signatures for signal operations."""
    fn = _fn(lib, "__mn_signal_new")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    fn = _fn(lib, "__mn_signal_get")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p]

    fn = _fn(lib, "__mn_signal_set")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_signal_subscribe")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_signal_unsubscribe")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    fn = _fn(lib, "__mn_signal_batch_begin")
    fn.restype = None
    fn.argtypes = []

    fn = _fn(lib, "__mn_signal_batch_end")
    fn.restype = None
    fn.argtypes = []

    fn = _fn(lib, "__mn_signal_free")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p]

    # Computed signal function type: void (*)(void *out_ptr, void *user_data)
    COMPUTE_FN_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)

    fn = _fn(lib, "__mn_signal_computed")
    fn.restype = ctypes.c_void_p
    fn.argtypes = [
        COMPUTE_FN_TYPE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int64,
        ctypes.c_int64,
    ]

    # Callback function type: void (*)(void *value, void *user_data)
    CB_FN_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)

    fn = _fn(lib, "__mn_signal_on_change")
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p, CB_FN_TYPE, ctypes.c_void_p]

    return COMPUTE_FN_TYPE, CB_FN_TYPE


# Convenience wrappers


def _signal_new(lib, value: int) -> ctypes.c_void_p:
    val = ctypes.c_int64(value)
    return _fn(lib, "__mn_signal_new")(ctypes.byref(val), 8)


def _signal_get_int(lib, sig) -> int:
    ptr = _fn(lib, "__mn_signal_get")(sig)
    return ctypes.cast(ptr, ctypes.POINTER(ctypes.c_int64)).contents.value


def _signal_set_int(lib, sig, value: int):
    val = ctypes.c_int64(value)
    _fn(lib, "__mn_signal_set")(sig, ctypes.byref(val))


def _signal_free(lib, sig):
    _fn(lib, "__mn_signal_free")(sig)


# ===========================================================================
# Test: Signal creation and basic get/set
# ===========================================================================


class TestSignalBasic:
    """Tasks 1-4: Signal creation, get, set."""

    def setup_method(self):
        lib = _get_lib()
        _setup_signal_fns(lib)

    def test_signal_new_and_get(self):
        lib = _get_lib()
        sig = _signal_new(lib, 42)
        assert sig is not None
        assert _signal_get_int(lib, sig) == 42
        _signal_free(lib, sig)

    def test_signal_set_and_get(self):
        lib = _get_lib()
        sig = _signal_new(lib, 10)
        assert _signal_get_int(lib, sig) == 10
        _signal_set_int(lib, sig, 20)
        assert _signal_get_int(lib, sig) == 20
        _signal_free(lib, sig)

    def test_signal_set_same_value_no_crash(self):
        """Setting the same value should be a no-op (no propagation)."""
        lib = _get_lib()
        sig = _signal_new(lib, 5)
        _signal_set_int(lib, sig, 5)  # Same value
        assert _signal_get_int(lib, sig) == 5
        _signal_free(lib, sig)

    def test_signal_multiple_sets(self):
        lib = _get_lib()
        sig = _signal_new(lib, 0)
        for i in range(1, 20):
            _signal_set_int(lib, sig, i)
            assert _signal_get_int(lib, sig) == i
        _signal_free(lib, sig)


# ===========================================================================
# Test: Computed signals
# ===========================================================================


class TestSignalComputed:
    """Task 5: Computed signals with auto-recomputation."""

    def setup_method(self):
        lib = _get_lib()
        self.COMPUTE_FN_TYPE, self.CB_FN_TYPE = _setup_signal_fns(lib)

    def test_computed_basic(self):
        """Computed signal reads dependency and produces derived value."""
        lib = _get_lib()

        a = _signal_new(lib, 5)

        # Computed: double the value of `a`
        # We pass `a` as user_data so the compute fn can read it
        def double_fn(out_ptr, user_data):
            a_sig = ctypes.c_void_p(user_data)
            val = _signal_get_int(lib, a_sig.value)
            result = ctypes.c_int64(val * 2)
            ctypes.memmove(out_ptr, ctypes.byref(result), 8)

        compute_fn = self.COMPUTE_FN_TYPE(double_fn)
        deps = (ctypes.c_void_p * 1)(a)

        b = _fn(lib, "__mn_signal_computed")(
            compute_fn,
            ctypes.c_void_p(a),
            ctypes.cast(deps, ctypes.c_void_p),
            1,
            8,
        )

        # Initial value: 5 * 2 = 10
        assert _signal_get_int(lib, b) == 10

        # Update a → b should auto-recompute
        _signal_set_int(lib, a, 7)
        assert _signal_get_int(lib, b) == 14

        _signal_free(lib, b)
        _signal_free(lib, a)
        # Keep references alive
        _ = compute_fn, deps

    def test_computed_chain(self):
        """Computed signal chain: a → b → c."""
        lib = _get_lib()

        a = _signal_new(lib, 3)

        # b = a * 2
        def double_fn(out_ptr, user_data):
            a_sig = ctypes.c_void_p(user_data)
            val = _signal_get_int(lib, a_sig.value)
            result = ctypes.c_int64(val * 2)
            ctypes.memmove(out_ptr, ctypes.byref(result), 8)

        compute_b = self.COMPUTE_FN_TYPE(double_fn)
        deps_b = (ctypes.c_void_p * 1)(a)
        b = _fn(lib, "__mn_signal_computed")(
            compute_b,
            ctypes.c_void_p(a),
            ctypes.cast(deps_b, ctypes.c_void_p),
            1,
            8,
        )

        # c = b + 1
        def plus_one_fn(out_ptr, user_data):
            b_sig = ctypes.c_void_p(user_data)
            val = _signal_get_int(lib, b_sig.value)
            result = ctypes.c_int64(val + 1)
            ctypes.memmove(out_ptr, ctypes.byref(result), 8)

        compute_c = self.COMPUTE_FN_TYPE(plus_one_fn)
        deps_c = (ctypes.c_void_p * 1)(b)
        c = _fn(lib, "__mn_signal_computed")(
            compute_c,
            ctypes.c_void_p(b),
            ctypes.cast(deps_c, ctypes.c_void_p),
            1,
            8,
        )

        # a=3, b=6, c=7
        assert _signal_get_int(lib, c) == 7

        # Update a=5 → b=10, c=11
        _signal_set_int(lib, a, 5)
        assert _signal_get_int(lib, b) == 10
        assert _signal_get_int(lib, c) == 11

        _signal_free(lib, c)
        _signal_free(lib, b)
        _signal_free(lib, a)
        _ = compute_b, compute_c, deps_b, deps_c


# ===========================================================================
# Test: Subscribe / Unsubscribe
# ===========================================================================


class TestSignalSubscribe:
    """Tasks 6, 8: Subscribe and unsubscribe."""

    def setup_method(self):
        lib = _get_lib()
        _setup_signal_fns(lib)

    def test_subscribe_duplicate_ignored(self):
        """Subscribing the same signal twice should not cause double notification."""
        lib = _get_lib()
        a = _signal_new(lib, 1)
        b = _signal_new(lib, 0)
        _fn(lib, "__mn_signal_subscribe")(a, b)
        _fn(lib, "__mn_signal_subscribe")(a, b)  # Duplicate
        # Should not crash
        _signal_set_int(lib, a, 2)
        _signal_free(lib, b)
        _signal_free(lib, a)

    def test_unsubscribe(self):
        """After unsubscribe, dependent should not be notified."""
        lib = _get_lib()
        a = _signal_new(lib, 1)
        b = _signal_new(lib, 0)
        _fn(lib, "__mn_signal_subscribe")(a, b)
        _fn(lib, "__mn_signal_unsubscribe")(a, b)
        # b should not be in a's subscriber list anymore
        _signal_set_int(lib, a, 99)
        # No crash = success (b is not dirty-marked)
        _signal_free(lib, b)
        _signal_free(lib, a)


# ===========================================================================
# Test: Batching
# ===========================================================================


class TestSignalBatch:
    """Task 7: Batch begin/end."""

    def setup_method(self):
        lib = _get_lib()
        self.COMPUTE_FN_TYPE, self.CB_FN_TYPE = _setup_signal_fns(lib)

    def test_batch_defers_propagation(self):
        """Inside a batch, propagation is deferred until batch_end."""
        lib = _get_lib()

        a = _signal_new(lib, 1)

        # Track callback invocations
        call_count = ctypes.c_int64(0)

        def on_change_cb(value_ptr, user_data):
            ptr = ctypes.cast(user_data, ctypes.POINTER(ctypes.c_int64))
            ptr.contents.value += 1

        cb = self.CB_FN_TYPE(on_change_cb)
        _fn(lib, "__mn_signal_on_change")(a, cb, ctypes.byref(call_count))

        # Start batch
        _fn(lib, "__mn_signal_batch_begin")()
        _signal_set_int(lib, a, 10)
        _signal_set_int(lib, a, 20)

        # Callback should not have fired yet
        assert call_count.value == 0

        # End batch — should fire callback once
        _fn(lib, "__mn_signal_batch_end")()
        assert call_count.value == 1
        assert _signal_get_int(lib, a) == 20

        _signal_free(lib, a)
        _ = cb

    def test_nested_batch(self):
        """Nested batches only propagate when outermost ends."""
        lib = _get_lib()
        a = _signal_new(lib, 0)

        call_count = ctypes.c_int64(0)

        def on_change_cb(value_ptr, user_data):
            ptr = ctypes.cast(user_data, ctypes.POINTER(ctypes.c_int64))
            ptr.contents.value += 1

        cb = self.CB_FN_TYPE(on_change_cb)
        _fn(lib, "__mn_signal_on_change")(a, cb, ctypes.byref(call_count))

        _fn(lib, "__mn_signal_batch_begin")()
        _signal_set_int(lib, a, 1)
        _fn(lib, "__mn_signal_batch_begin")()  # Nested
        _signal_set_int(lib, a, 2)
        _fn(lib, "__mn_signal_batch_end")()  # Inner end
        assert call_count.value == 0  # Still deferred
        _fn(lib, "__mn_signal_batch_end")()  # Outer end
        assert call_count.value == 1

        _signal_free(lib, a)
        _ = cb


# ===========================================================================
# Test: Topological propagation / diamond dependency
# ===========================================================================


class TestSignalTopological:
    """Task 9: Topological sort prevents glitches."""

    def setup_method(self):
        lib = _get_lib()
        self.COMPUTE_FN_TYPE, self.CB_FN_TYPE = _setup_signal_fns(lib)

    def test_diamond_dependency(self):
        """Diamond: a → b, a → c, b+c → d. d should see consistent values.

        a = signal(1)
        b = computed { a * 2 }     → 2
        c = computed { a + 10 }    → 11
        d = computed { b + c }     → 13
        Set a = 5: b=10, c=15, d=25
        """
        lib = _get_lib()

        a = _signal_new(lib, 1)

        # b = a * 2
        def b_fn(out_ptr, user_data):
            val = _signal_get_int(lib, ctypes.c_void_p(user_data).value)
            r = ctypes.c_int64(val * 2)
            ctypes.memmove(out_ptr, ctypes.byref(r), 8)

        cb_fn = self.COMPUTE_FN_TYPE(b_fn)
        deps_b = (ctypes.c_void_p * 1)(a)
        b = _fn(lib, "__mn_signal_computed")(
            cb_fn,
            ctypes.c_void_p(a),
            ctypes.cast(deps_b, ctypes.c_void_p),
            1,
            8,
        )

        # c = a + 10
        def c_fn(out_ptr, user_data):
            val = _signal_get_int(lib, ctypes.c_void_p(user_data).value)
            r = ctypes.c_int64(val + 10)
            ctypes.memmove(out_ptr, ctypes.byref(r), 8)

        cc_fn = self.COMPUTE_FN_TYPE(c_fn)
        deps_c = (ctypes.c_void_p * 1)(a)
        c = _fn(lib, "__mn_signal_computed")(
            cc_fn,
            ctypes.c_void_p(a),
            ctypes.cast(deps_c, ctypes.c_void_p),
            1,
            8,
        )

        # d = b + c — needs both b and c as user_data
        # Pack b and c into a struct
        class BCPair(ctypes.Structure):
            _fields_ = [("b", ctypes.c_void_p), ("c", ctypes.c_void_p)]

        bc = BCPair(b=b, c=c)

        def d_fn(out_ptr, user_data):
            pair = ctypes.cast(user_data, ctypes.POINTER(BCPair)).contents
            bval = _signal_get_int(lib, pair.b)
            cval = _signal_get_int(lib, pair.c)
            r = ctypes.c_int64(bval + cval)
            ctypes.memmove(out_ptr, ctypes.byref(r), 8)

        cd_fn = self.COMPUTE_FN_TYPE(d_fn)
        deps_d = (ctypes.c_void_p * 2)(b, c)
        d = _fn(lib, "__mn_signal_computed")(
            cd_fn,
            ctypes.cast(ctypes.byref(bc), ctypes.c_void_p),
            ctypes.cast(deps_d, ctypes.c_void_p),
            2,
            8,
        )

        # Initial: a=1, b=2, c=11, d=13
        assert _signal_get_int(lib, b) == 2
        assert _signal_get_int(lib, c) == 11
        assert _signal_get_int(lib, d) == 13

        # Update: a=5 → b=10, c=15, d=25
        _signal_set_int(lib, a, 5)
        assert _signal_get_int(lib, b) == 10
        assert _signal_get_int(lib, c) == 15
        assert _signal_get_int(lib, d) == 25

        _signal_free(lib, d)
        _signal_free(lib, c)
        _signal_free(lib, b)
        _signal_free(lib, a)
        _ = cb_fn, cc_fn, cd_fn, deps_b, deps_c, deps_d, bc


# ===========================================================================
# Test: Callbacks
# ===========================================================================


class TestSignalCallbacks:
    """Task 6 (extended): on_change callbacks."""

    def setup_method(self):
        lib = _get_lib()
        self.COMPUTE_FN_TYPE, self.CB_FN_TYPE = _setup_signal_fns(lib)

    def test_on_change_called(self):
        lib = _get_lib()
        a = _signal_new(lib, 0)

        values_seen = []

        def cb(value_ptr, user_data):
            val = ctypes.cast(value_ptr, ctypes.POINTER(ctypes.c_int64)).contents.value
            values_seen.append(val)

        callback = self.CB_FN_TYPE(cb)
        _fn(lib, "__mn_signal_on_change")(a, callback, None)

        _signal_set_int(lib, a, 10)
        _signal_set_int(lib, a, 20)

        assert values_seen == [10, 20]
        _signal_free(lib, a)
        _ = callback


# ===========================================================================
# Test: Signal free / cleanup
# ===========================================================================


class TestSignalFree:
    """Signal cleanup removes subscriptions from dependencies."""

    def setup_method(self):
        lib = _get_lib()
        self.COMPUTE_FN_TYPE, self.CB_FN_TYPE = _setup_signal_fns(lib)

    def test_free_computed_unsubscribes(self):
        lib = _get_lib()
        a = _signal_new(lib, 5)

        def double_fn(out_ptr, user_data):
            val = _signal_get_int(lib, ctypes.c_void_p(user_data).value)
            r = ctypes.c_int64(val * 2)
            ctypes.memmove(out_ptr, ctypes.byref(r), 8)

        compute_fn = self.COMPUTE_FN_TYPE(double_fn)
        deps = (ctypes.c_void_p * 1)(a)
        b = _fn(lib, "__mn_signal_computed")(
            compute_fn,
            ctypes.c_void_p(a),
            ctypes.cast(deps, ctypes.c_void_p),
            1,
            8,
        )

        _signal_free(lib, b)

        # After freeing b, setting a should not crash
        _signal_set_int(lib, a, 99)
        assert _signal_get_int(lib, a) == 99
        _signal_free(lib, a)
        _ = compute_fn, deps
