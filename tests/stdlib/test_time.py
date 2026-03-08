"""Tests for mapanare.time -- timer signals, debounce, throttle."""

from __future__ import annotations

import asyncio
import time

from stdlib.time import (
    Debounce,
    Stopwatch,
    Throttle,
    TimerSignal,
    delay,
    interval,
)

# ---------------------------------------------------------------------------
# TimerSignal tests
# ---------------------------------------------------------------------------


class TestTimerSignal:
    async def test_timer_ticks(self) -> None:
        timer = TimerSignal(0.05)
        assert timer.value == 0
        await timer.start()
        await asyncio.sleep(0.18)
        await timer.stop()
        assert timer.value >= 2

    async def test_timer_stop(self) -> None:
        timer = TimerSignal(0.05)
        await timer.start()
        await asyncio.sleep(0.12)
        await timer.stop()
        val = timer.value
        await asyncio.sleep(0.12)
        assert timer.value == val  # no more ticks

    async def test_timer_start_idempotent(self) -> None:
        timer = TimerSignal(0.05)
        await timer.start()
        await timer.start()  # second start is no-op
        await asyncio.sleep(0.08)
        await timer.stop()
        assert timer.value >= 1

    async def test_timer_on_change(self) -> None:
        timer = TimerSignal(0.05)
        values: list[int] = []
        timer.on_change(lambda v: values.append(v))
        await timer.start()
        await asyncio.sleep(0.18)
        await timer.stop()
        assert len(values) >= 2


# ---------------------------------------------------------------------------
# Interval stream tests
# ---------------------------------------------------------------------------


class TestInterval:
    async def test_interval_with_count(self) -> None:
        s = interval(0.03, count=3)
        items = await s.collect()
        assert items == [0, 1, 2]

    async def test_interval_take(self) -> None:
        s = interval(0.03).take(4)
        items = await s.collect()
        assert items == [0, 1, 2, 3]


# ---------------------------------------------------------------------------
# Delay tests
# ---------------------------------------------------------------------------


class TestDelay:
    async def test_delay(self) -> None:
        t0 = time.monotonic()
        await delay(0.05)
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.04


# ---------------------------------------------------------------------------
# Debounce tests
# ---------------------------------------------------------------------------


class TestDebounce:
    async def test_debounce_fires_after_silence(self) -> None:
        results: list[str] = []
        db = Debounce(0.08, callback=lambda v: results.append(v))
        db("a")
        db("b")
        db("c")
        await asyncio.sleep(0.15)
        assert results == ["c"]

    async def test_debounce_resets_on_call(self) -> None:
        results: list[str] = []
        db = Debounce(0.1, callback=lambda v: results.append(v))
        db("first")
        await asyncio.sleep(0.05)
        db("second")  # resets the timer
        await asyncio.sleep(0.05)
        assert results == []  # not yet fired
        await asyncio.sleep(0.1)
        assert results == ["second"]

    async def test_debounce_cancel(self) -> None:
        results: list[int] = []
        db = Debounce(0.05, callback=lambda v: results.append(v))
        db(42)
        db.cancel()
        await asyncio.sleep(0.1)
        assert results == []


# ---------------------------------------------------------------------------
# Throttle tests
# ---------------------------------------------------------------------------


class TestThrottle:
    async def test_throttle_first_fires_immediately(self) -> None:
        results: list[str] = []
        th = Throttle(0.5, callback=lambda v: results.append(v))
        th("a")
        assert results == ["a"]

    async def test_throttle_drops_rapid_calls(self) -> None:
        results: list[str] = []
        th = Throttle(0.1, callback=lambda v: results.append(v))
        th("a")  # fires immediately
        th("b")  # queued
        th("c")  # replaces b
        assert results == ["a"]
        await asyncio.sleep(0.15)
        assert results == ["a", "c"]

    async def test_throttle_cancel(self) -> None:
        results: list[int] = []
        th = Throttle(0.1, callback=lambda v: results.append(v))
        th(1)  # fires immediately
        th(2)  # queued
        th.cancel()
        await asyncio.sleep(0.15)
        assert results == [1]


# ---------------------------------------------------------------------------
# Stopwatch tests
# ---------------------------------------------------------------------------


class TestStopwatch:
    def test_stopwatch_basic(self) -> None:
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        elapsed = sw.stop()
        assert elapsed >= 0.04

    def test_stopwatch_elapsed_while_running(self) -> None:
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        assert sw.elapsed >= 0.04
        sw.stop()

    def test_stopwatch_reset(self) -> None:
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        sw.reset()
        assert sw.elapsed < 0.01

    def test_stopwatch_pause_resume(self) -> None:
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        e1 = sw.stop()
        time.sleep(0.05)
        sw.start()  # resume
        time.sleep(0.05)
        e2 = sw.stop()
        assert e2 >= e1 + 0.04

    def test_stopwatch_chaining(self) -> None:
        sw = Stopwatch().start()
        assert sw.elapsed >= 0
        sw.stop()
