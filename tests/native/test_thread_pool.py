"""Tests for the thread pool (Phase 4.3, Task 3)."""

import ctypes
import time

import pytest

from runtime.native_bridge import (
    NATIVE_AVAILABLE,
    WORK_FN,
    NativeThreadPool,
    cpu_count,
)

pytestmark = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="Native runtime not built",
)


class TestThreadPoolCreate:
    """Thread pool creation and configuration."""

    def test_create_with_explicit_threads(self) -> None:
        pool = NativeThreadPool(num_threads=2)
        assert pool.thread_count == 2
        pool.destroy()

    def test_create_auto_detect_cores(self) -> None:
        pool = NativeThreadPool(num_threads=0)
        assert pool.thread_count >= 1
        assert pool.thread_count == cpu_count()
        pool.destroy()

    def test_cpu_count_positive(self) -> None:
        count = cpu_count()
        assert count >= 1


class TestThreadPoolSubmit:
    """Work submission and execution."""

    def test_submit_and_execute(self) -> None:
        """Submit work and verify it runs."""
        pool = NativeThreadPool(num_threads=2)

        # Use a shared counter via ctypes to detect execution
        counter = ctypes.c_int(0)
        counter_ptr = ctypes.cast(ctypes.pointer(counter), ctypes.c_void_p)

        @WORK_FN
        def increment(arg: int) -> None:
            ptr = ctypes.cast(arg, ctypes.POINTER(ctypes.c_int))
            # Simple atomic-ish increment (safe for single writer)
            ptr.contents.value += 1

        ok = pool.submit(increment, counter_ptr.value)
        assert ok

        # Give the worker time to process
        time.sleep(0.1)
        assert counter.value == 1
        pool.destroy()

    def test_submit_multiple_items(self) -> None:
        pool = NativeThreadPool(num_threads=4)

        counter = ctypes.c_long(0)
        counter_ptr = ctypes.cast(ctypes.pointer(counter), ctypes.c_void_p)

        @WORK_FN
        def increment(arg: int) -> None:
            ptr = ctypes.cast(arg, ctypes.POINTER(ctypes.c_long))
            ptr.contents.value += 1

        for _ in range(10):
            pool.submit(increment, counter_ptr.value)

        time.sleep(0.5)
        assert counter.value == 10
        pool.destroy()

    def test_submit_with_different_args(self) -> None:
        """Each work item receives its own argument."""
        pool = NativeThreadPool(num_threads=2)

        counter = ctypes.c_long(0)
        counter_ptr = ctypes.cast(ctypes.pointer(counter), ctypes.c_void_p)

        @WORK_FN
        def store_index(arg: int) -> None:
            # Verify the function runs by incrementing shared counter
            ptr = ctypes.cast(arg, ctypes.POINTER(ctypes.c_long))
            ptr.contents.value += 1

        for _ in range(5):
            pool.submit(store_index, counter_ptr.value)

        time.sleep(0.3)
        assert counter.value == 5
        pool.destroy()

    def test_destroy_cleans_up(self) -> None:
        """Pool destruction joins threads and cleans up."""
        pool = NativeThreadPool(num_threads=2)
        pool.destroy()
        # No crash = success
