"""Benchmark isolation harness for reliable, reproducible measurements.

Techniques applied (standalone mode):
- GC disabled during timed sections (eliminates GC pause noise)
- Warmup runs (stabilizes CPython adaptive interpreter, PEP 659)
- Multiple samples with median (resistant to OS scheduler spikes)
- IQR outlier removal (drops GC/scheduler anomalies)
- Fresh event loop per async benchmark (no state leakage)

When called from within a running event loop (e.g. pytest-asyncio), falls back
to a single direct await with basic GC isolation (test mode).
"""

from __future__ import annotations

import asyncio
import gc
import statistics
import time


def _iqr_clean(raw: list[float]) -> list[float]:
    """Remove outliers using IQR method."""
    if len(raw) < 4:
        return raw
    q1, _, q3 = statistics.quantiles(raw, n=4)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [t for t in raw if lo <= t <= hi]


def _has_running_loop() -> bool:
    """Check if there's already a running asyncio event loop (e.g. pytest)."""
    try:
        loop = asyncio.get_running_loop()
        return loop is not None
    except RuntimeError:
        return False


async def isolated_async_bench(
    coro_fn: object,
    *,
    warmup: int = 2,
    samples: int = 7,
) -> float:
    """Run async benchmark with isolation. Loop-aware.

    In standalone mode: fresh event loop per sample, GC disabled, median of N.
    In test mode (running loop): single await with GC disabled.
    """
    fn = coro_fn  # type: ignore[assignment]

    if _has_running_loop():
        # Test mode — can't create new loops, just time a single run
        gc.collect()
        gc.disable()
        t0 = time.perf_counter()
        await fn()
        t1 = time.perf_counter()
        gc.enable()
        return t1 - t0

    # Standalone mode — full isolation
    for _ in range(warmup):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(fn())
        loop.close()

    raw: list[float] = []
    for _ in range(samples):
        gc.collect()
        gc.disable()
        loop = asyncio.new_event_loop()
        t0 = time.perf_counter()
        loop.run_until_complete(fn())
        t1 = time.perf_counter()
        gc.enable()
        loop.close()
        raw.append(t1 - t0)

    return statistics.median(_iqr_clean(raw))


def isolated_sync_bench(
    fn: object,
    *,
    warmup: int = 2,
    samples: int = 7,
) -> float:
    """Run sync benchmark with isolation. GC disabled, median of N."""
    callable_fn = fn  # type: ignore[assignment]

    for _ in range(warmup):
        callable_fn()

    raw: list[float] = []
    for _ in range(samples):
        gc.collect()
        gc.disable()
        t0 = time.perf_counter()
        callable_fn()
        t1 = time.perf_counter()
        gc.enable()
        raw.append(t1 - t0)

    return statistics.median(_iqr_clean(raw))
