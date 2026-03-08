"""Tests for the native backpressure system (Phase 4.3, Task 4)."""

import pytest

from runtime.native_bridge import NATIVE_AVAILABLE, NativeBackpressure

pytestmark = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="Native runtime not built",
)


class TestBackpressureInit:
    """Backpressure initialization."""

    def test_init_zero_pending(self) -> None:
        bp = NativeBackpressure(100)
        assert bp.pending == 0

    def test_init_not_overloaded(self) -> None:
        bp = NativeBackpressure(100)
        assert not bp.is_overloaded

    def test_init_zero_pressure(self) -> None:
        bp = NativeBackpressure(100)
        assert bp.pressure == pytest.approx(0.0)


class TestBackpressureIncDec:
    """Increment and decrement counters."""

    def test_increment_increases_pending(self) -> None:
        bp = NativeBackpressure(100)
        bp.increment()
        assert bp.pending == 1
        bp.increment()
        assert bp.pending == 2

    def test_decrement_decreases_pending(self) -> None:
        bp = NativeBackpressure(100)
        bp.increment()
        bp.increment()
        bp.increment()
        bp.decrement()
        assert bp.pending == 2

    def test_increment_to_capacity_sets_overloaded(self) -> None:
        bp = NativeBackpressure(3)
        bp.increment()
        bp.increment()
        assert not bp.is_overloaded
        bp.increment()  # pending == 3 == capacity
        assert bp.is_overloaded

    def test_decrement_below_capacity_clears_overloaded(self) -> None:
        bp = NativeBackpressure(3)
        for _ in range(3):
            bp.increment()
        assert bp.is_overloaded
        bp.decrement()  # pending == 2 < 3
        assert not bp.is_overloaded

    def test_overloaded_above_capacity(self) -> None:
        bp = NativeBackpressure(2)
        bp.increment()
        bp.increment()
        assert bp.is_overloaded
        bp.increment()  # pending == 3 > cap 2
        assert bp.is_overloaded


class TestBackpressurePressure:
    """Pressure ratio (0.0 to 1.0)."""

    def test_pressure_at_zero(self) -> None:
        bp = NativeBackpressure(10)
        assert bp.pressure == pytest.approx(0.0)

    def test_pressure_at_half(self) -> None:
        bp = NativeBackpressure(10)
        for _ in range(5):
            bp.increment()
        assert bp.pressure == pytest.approx(0.5)

    def test_pressure_at_full(self) -> None:
        bp = NativeBackpressure(10)
        for _ in range(10):
            bp.increment()
        assert bp.pressure == pytest.approx(1.0)

    def test_pressure_capped_at_one(self) -> None:
        bp = NativeBackpressure(5)
        for _ in range(10):
            bp.increment()
        assert bp.pressure == pytest.approx(1.0)

    def test_pressure_quarter(self) -> None:
        bp = NativeBackpressure(100)
        for _ in range(25):
            bp.increment()
        assert bp.pressure == pytest.approx(0.25)
