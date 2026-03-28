"""mapanare.time -- timer signals, debounce, throttle."""

from __future__ import annotations

import asyncio
import time as _time
from typing import Any, Callable, Generic, TypeVar

from runtime.signal import Signal
from runtime.stream import Stream

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Timer signal -- emits tick count at regular intervals
# ---------------------------------------------------------------------------


class TimerSignal(Signal[int]):
    """A signal that increments at a fixed interval.

    The value is the number of ticks elapsed since start.
    """

    def __init__(self, interval_seconds: float) -> None:
        super().__init__(0)
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the timer."""
        if self._task is not None:
            return

        async def _tick() -> None:
            count = 0
            while True:
                await asyncio.sleep(self._interval)
                count += 1
                self.value = count

        self._task = asyncio.ensure_future(_tick())

    async def stop(self) -> None:
        """Stop the timer."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# ---------------------------------------------------------------------------
# Interval stream -- emits values at regular intervals
# ---------------------------------------------------------------------------


def interval(seconds: float, count: int | None = None) -> Stream[int]:
    """Create a stream that emits incrementing integers at fixed intervals.

    Args:
        seconds: Interval between emissions.
        count: Optional max number of emissions (None = infinite).
    """

    async def _gen() -> Any:
        i = 0
        while count is None or i < count:
            await asyncio.sleep(seconds)
            yield i
            i += 1

    return Stream(_gen())


# ---------------------------------------------------------------------------
# Delay
# ---------------------------------------------------------------------------


async def delay(seconds: float) -> None:
    """Async sleep for the given number of seconds."""
    await asyncio.sleep(seconds)


# ---------------------------------------------------------------------------
# Debounce -- waits for silence before emitting
# ---------------------------------------------------------------------------


class Debounce(Generic[T]):
    """Debounce wrapper: only fires callback after ``wait`` seconds of silence.

    Usage::

        db = Debounce(0.3, callback=my_fn)
        db(value1)  # starts timer
        db(value2)  # resets timer
        # after 0.3s of no calls, my_fn(value2) fires
    """

    def __init__(self, wait: float, callback: Callable[[T], Any]) -> None:
        self._wait = wait
        self._callback = callback
        self._task: asyncio.Task[None] | None = None
        self._last_value: T | None = None

    def __call__(self, value: T) -> None:
        self._last_value = value
        if self._task is not None:
            self._task.cancel()

        async def _fire() -> None:
            await asyncio.sleep(self._wait)
            self._callback(self._last_value)  # type: ignore[arg-type]

        self._task = asyncio.ensure_future(_fire())

    def cancel(self) -> None:
        """Cancel any pending debounced call."""
        if self._task is not None:
            self._task.cancel()
            self._task = None


# ---------------------------------------------------------------------------
# Throttle -- emits at most once per interval
# ---------------------------------------------------------------------------


class Throttle(Generic[T]):
    """Throttle wrapper: fires at most once per ``interval`` seconds.

    The first call fires immediately. Subsequent calls within the interval
    are dropped; the last value in each interval is emitted when the interval
    expires.

    Usage::

        th = Throttle(1.0, callback=my_fn)
        th(v1)  # fires immediately
        th(v2)  # queued
        th(v3)  # replaces v2
        # after 1.0s, my_fn(v3) fires
    """

    def __init__(self, interval_seconds: float, callback: Callable[[T], Any]) -> None:
        self._interval = interval_seconds
        self._callback = callback
        self._last_call: float = 0.0
        self._pending: T | None = None
        self._has_pending = False
        self._task: asyncio.Task[None] | None = None

    def __call__(self, value: T) -> None:
        now = _time.monotonic()
        elapsed = now - self._last_call

        if elapsed >= self._interval:
            self._last_call = now
            self._callback(value)
        else:
            self._pending = value
            self._has_pending = True
            if self._task is None:
                remaining = self._interval - elapsed

                async def _trailing() -> None:
                    await asyncio.sleep(remaining)
                    if self._has_pending:
                        self._last_call = _time.monotonic()
                        self._has_pending = False
                        self._callback(self._pending)  # type: ignore[arg-type]
                    self._task = None

                self._task = asyncio.ensure_future(_trailing())

    def cancel(self) -> None:
        """Cancel any pending throttled call."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._has_pending = False


# ---------------------------------------------------------------------------
# Stopwatch
# ---------------------------------------------------------------------------


class Stopwatch:
    """Simple monotonic stopwatch for measuring elapsed time."""

    def __init__(self) -> None:
        self._start: float | None = None
        self._elapsed: float = 0.0
        self._running = False

    def start(self) -> Stopwatch:
        """Start or resume the stopwatch."""
        if not self._running:
            self._start = _time.monotonic()
            self._running = True
        return self

    def stop(self) -> float:
        """Stop and return elapsed seconds."""
        if self._running and self._start is not None:
            self._elapsed += _time.monotonic() - self._start
            self._running = False
            self._start = None
        return self._elapsed

    def reset(self) -> None:
        """Reset elapsed time to zero."""
        self._elapsed = 0.0
        self._start = _time.monotonic() if self._running else None

    @property
    def elapsed(self) -> float:
        """Current elapsed seconds."""
        if self._running and self._start is not None:
            return self._elapsed + (_time.monotonic() - self._start)
        return self._elapsed
