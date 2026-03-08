"""Tests for the lock-free SPSC ring buffer (Phase 4.3, Task 2)."""

import pytest

from runtime.native_bridge import NATIVE_AVAILABLE, NativeRingBuffer

pytestmark = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="Native runtime not built",
)


class TestRingBufferCreate:
    """Ring buffer creation and capacity."""

    def test_create_default(self) -> None:
        rb = NativeRingBuffer(256)
        assert rb.capacity == 256  # 256 is already power of 2
        rb.destroy()

    def test_capacity_rounds_to_power_of_two(self) -> None:
        rb = NativeRingBuffer(100)
        assert rb.capacity == 128  # next power of 2 above 100
        rb.destroy()

    def test_capacity_one(self) -> None:
        rb = NativeRingBuffer(1)
        assert rb.capacity == 1
        rb.destroy()

    def test_capacity_three(self) -> None:
        rb = NativeRingBuffer(3)
        assert rb.capacity == 4
        rb.destroy()

    def test_starts_empty(self) -> None:
        rb = NativeRingBuffer(16)
        assert rb.is_empty
        assert not rb.is_full
        assert rb.size == 0
        rb.destroy()


class TestRingBufferPushPop:
    """Push and pop operations."""

    def test_push_pop_single(self) -> None:
        rb = NativeRingBuffer(16)
        assert rb.push(42)
        val = rb.pop()
        assert val == 42
        rb.destroy()

    def test_push_pop_fifo_order(self) -> None:
        rb = NativeRingBuffer(16)
        for i in range(1, 6):
            assert rb.push(i)
        for i in range(1, 6):
            assert rb.pop() == i
        rb.destroy()

    def test_pop_empty_returns_none(self) -> None:
        rb = NativeRingBuffer(16)
        assert rb.pop() is None
        rb.destroy()

    def test_push_full_returns_false(self) -> None:
        rb = NativeRingBuffer(4)
        for i in range(4):
            assert rb.push(i + 1)
        assert not rb.push(99)  # full
        rb.destroy()

    def test_size_tracking(self) -> None:
        rb = NativeRingBuffer(8)
        assert rb.size == 0
        rb.push(1)
        assert rb.size == 1
        rb.push(2)
        assert rb.size == 2
        rb.pop()
        assert rb.size == 1
        rb.pop()
        assert rb.size == 0
        rb.destroy()

    def test_full_and_empty_flags(self) -> None:
        rb = NativeRingBuffer(2)
        assert rb.is_empty
        rb.push(1)
        assert not rb.is_empty
        assert not rb.is_full
        rb.push(2)
        assert rb.is_full
        rb.pop()
        assert not rb.is_full
        rb.pop()
        assert rb.is_empty
        rb.destroy()

    def test_wraparound(self) -> None:
        """Push/pop past capacity to test index wrapping."""
        rb = NativeRingBuffer(4)
        for cycle in range(3):
            for i in range(4):
                assert rb.push(cycle * 10 + i)
            for i in range(4):
                assert rb.pop() == cycle * 10 + i
        rb.destroy()

    def test_many_items(self) -> None:
        rb = NativeRingBuffer(1024)
        for i in range(1, 1001):
            assert rb.push(i)
        assert rb.size == 1000
        for i in range(1, 1001):
            assert rb.pop() == i
        assert rb.is_empty
        rb.destroy()

    def test_push_zero_value(self) -> None:
        """Pushing 0 (NULL pointer) is a valid message."""
        rb = NativeRingBuffer(4)
        assert rb.push(0)
        val = rb.pop()
        assert val == 0
        rb.destroy()

    def test_interleaved_push_pop(self) -> None:
        rb = NativeRingBuffer(4)
        rb.push(1)
        rb.push(2)
        assert rb.pop() == 1
        rb.push(3)
        assert rb.pop() == 2
        assert rb.pop() == 3
        assert rb.is_empty
        rb.destroy()
