"""Benchmark: compare Mapanare runtime vs Python asyncio and Rust baselines.

Runs identical workloads using:
  1. Mapanare runtime (agents + streams)
  2. Pure Python asyncio (baseline)
  3. Rust reference (read from pre-computed results if available)

Uses isolation harness for reliable measurements.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from benchmarks.isolate import isolated_async_bench, isolated_sync_bench


@dataclass
class ComparisonResult:
    """Result comparing Mapanare vs a baseline."""

    workload: str
    mapanare_elapsed_s: float
    asyncio_elapsed_s: float
    rust_elapsed_s: float | None
    mapanare_vs_asyncio: float  # speedup factor
    mapanare_vs_rust: float | None


# ---------------------------------------------------------------------------
# Python asyncio baseline workloads
# ---------------------------------------------------------------------------


async def _asyncio_message_passing(n_messages: int) -> float:
    """Baseline: pure asyncio queue message passing."""

    async def run() -> None:
        q_in: asyncio.Queue[int] = asyncio.Queue(maxsize=1024)
        q_out: asyncio.Queue[int] = asyncio.Queue(maxsize=1024)
        done = asyncio.Event()

        async def worker() -> None:
            count = 0
            while count < n_messages:
                msg = await q_in.get()
                await q_out.put(msg)
                count += 1
            done.set()

        async def drain() -> None:
            drained = 0
            while drained < n_messages:
                await q_out.get()
                drained += 1

        task = asyncio.create_task(worker())
        drain_task = asyncio.create_task(drain())
        for i in range(n_messages):
            await q_in.put(i)
        await done.wait()
        await task
        drain_task.cancel()
        try:
            await drain_task
        except asyncio.CancelledError:
            pass

    return await isolated_async_bench(run)


async def _asyncio_stream_map(n_items: int) -> float:
    """Baseline: pure Python list map (simulating stream pipeline)."""

    def run() -> None:
        data = list(range(n_items))
        result = [x * 2 for x in data]
        assert len(result) == n_items

    return isolated_sync_bench(run)


async def _asyncio_stream_filter(n_items: int) -> float:
    """Baseline: pure Python list filter."""

    def run() -> None:
        data = list(range(n_items))
        result = [x for x in data if x % 2 == 0]
        assert len(result) == n_items // 2

    return isolated_sync_bench(run)


async def _asyncio_stream_map_filter(n_items: int) -> float:
    """Baseline: pure Python map then filter."""

    def run() -> None:
        data = list(range(n_items))
        mapped = [x * 3 for x in data]
        _ = [x for x in mapped if x % 2 == 0]

    return isolated_sync_bench(run)


# ---------------------------------------------------------------------------
# Mapanare runtime workloads
# ---------------------------------------------------------------------------


async def _mapanare_message_passing(n_messages: int) -> float:
    """Mapanare: agent channel message passing."""
    from runtime.agent import Channel

    async def run() -> None:
        ch_in: Channel[int] = Channel(maxsize=1024)
        ch_out: Channel[int] = Channel(maxsize=1024)
        done = asyncio.Event()

        async def worker() -> None:
            count = 0
            while count < n_messages:
                msg = await ch_in.receive()
                await ch_out.send(msg)
                count += 1
            done.set()

        async def drain() -> None:
            drained = 0
            while drained < n_messages:
                await ch_out.receive()
                drained += 1

        task = asyncio.create_task(worker())
        drain_task = asyncio.create_task(drain())
        for i in range(n_messages):
            await ch_in.send(i)
        await done.wait()
        task.cancel()
        drain_task.cancel()
        await asyncio.gather(task, drain_task, return_exceptions=True)

    return await isolated_async_bench(run)


async def _mapanare_stream_map(n_items: int) -> float:
    """Mapanare: stream map pipeline."""
    from runtime.stream import Stream

    async def run() -> None:
        stream = Stream.from_iter(range(n_items))
        result = await stream.map(lambda x: x * 2).collect()
        assert len(result) == n_items

    return await isolated_async_bench(run)


async def _mapanare_stream_filter(n_items: int) -> float:
    """Mapanare: stream filter pipeline."""
    from runtime.stream import Stream

    async def run() -> None:
        stream = Stream.from_iter(range(n_items))
        result = await stream.filter(lambda x: x % 2 == 0).collect()
        assert len(result) == n_items // 2

    return await isolated_async_bench(run)


async def _mapanare_stream_map_filter(n_items: int) -> float:
    """Mapanare: stream map+filter pipeline."""
    from runtime.stream import Stream

    async def run() -> None:
        stream = Stream.from_iter(range(n_items))
        await stream.map(lambda x: x * 3).filter(lambda x: x % 2 == 0).collect()

    return await isolated_async_bench(run)


# ---------------------------------------------------------------------------
# Rust reference results (pre-computed)
# ---------------------------------------------------------------------------

_RUST_RESULTS_PATH = Path(__file__).parent / "rust_baseline.json"


def _load_rust_baselines() -> dict[str, float]:
    """Load pre-computed Rust benchmark baselines if available."""
    if _RUST_RESULTS_PATH.exists():
        with open(_RUST_RESULTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Comparison runner
# ---------------------------------------------------------------------------


async def run_comparison(
    n_messages: int = 10_000,
    n_items: int = 1_000_000,
) -> list[ComparisonResult]:
    """Run comparative benchmarks."""
    rust = _load_rust_baselines()
    results: list[ComparisonResult] = []

    # Message passing
    mapanare_mp = await _mapanare_message_passing(n_messages)
    asyncio_mp = await _asyncio_message_passing(n_messages)
    rust_mp = rust.get("message_passing")
    results.append(
        ComparisonResult(
            workload="message_passing",
            mapanare_elapsed_s=mapanare_mp,
            asyncio_elapsed_s=asyncio_mp,
            rust_elapsed_s=rust_mp,
            mapanare_vs_asyncio=asyncio_mp / mapanare_mp if mapanare_mp > 0 else 0,
            mapanare_vs_rust=rust_mp / mapanare_mp if rust_mp and mapanare_mp > 0 else None,
        )
    )

    # Stream map
    mapanare_sm = await _mapanare_stream_map(n_items)
    asyncio_sm = await _asyncio_stream_map(n_items)
    rust_sm = rust.get("stream_map")
    results.append(
        ComparisonResult(
            workload="stream_map",
            mapanare_elapsed_s=mapanare_sm,
            asyncio_elapsed_s=asyncio_sm,
            rust_elapsed_s=rust_sm,
            mapanare_vs_asyncio=asyncio_sm / mapanare_sm if mapanare_sm > 0 else 0,
            mapanare_vs_rust=rust_sm / mapanare_sm if rust_sm and mapanare_sm > 0 else None,
        )
    )

    # Stream filter
    mapanare_sf = await _mapanare_stream_filter(n_items)
    asyncio_sf = await _asyncio_stream_filter(n_items)
    rust_sf = rust.get("stream_filter")
    results.append(
        ComparisonResult(
            workload="stream_filter",
            mapanare_elapsed_s=mapanare_sf,
            asyncio_elapsed_s=asyncio_sf,
            rust_elapsed_s=rust_sf,
            mapanare_vs_asyncio=asyncio_sf / mapanare_sf if mapanare_sf > 0 else 0,
            mapanare_vs_rust=rust_sf / mapanare_sf if rust_sf and mapanare_sf > 0 else None,
        )
    )

    # Stream map+filter
    mapanare_smf = await _mapanare_stream_map_filter(n_items)
    asyncio_smf = await _asyncio_stream_map_filter(n_items)
    rust_smf = rust.get("stream_map_filter")
    results.append(
        ComparisonResult(
            workload="stream_map_filter",
            mapanare_elapsed_s=mapanare_smf,
            asyncio_elapsed_s=asyncio_smf,
            rust_elapsed_s=rust_smf,
            mapanare_vs_asyncio=asyncio_smf / mapanare_smf if mapanare_smf > 0 else 0,
            mapanare_vs_rust=rust_smf / mapanare_smf if rust_smf and mapanare_smf > 0 else None,
        )
    )

    return results


def main() -> None:
    """CLI entry point for comparative benchmarks."""
    results = asyncio.run(run_comparison())
    print("\n=== Mapanare vs Python asyncio vs Rust ===\n")
    hdr = (
        f"  {'Workload':<25s} {'Mapanare (s)':>10s} {'asyncio (s)':>12s}"
        f" {'Rust (s)':>10s} {'vs asyncio':>11s} {'vs Rust':>9s}"
    )
    print(hdr)
    print("  " + "-" * 77)
    for r in results:
        rust_s = f"{r.rust_elapsed_s:.4f}" if r.rust_elapsed_s is not None else "N/A"
        rust_x = f"{r.mapanare_vs_rust:.2f}x" if r.mapanare_vs_rust is not None else "N/A"
        row = (
            f"  {r.workload:<25s} {r.mapanare_elapsed_s:>10.4f}"
            f" {r.asyncio_elapsed_s:>12.4f} {rust_s:>10s}"
            f" {r.mapanare_vs_asyncio:>10.2f}x {rust_x:>9s}"
        )
        print(row)
    print()

    out = [asdict(r) for r in results]
    with open("benchmarks/results_comparison.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Results written to benchmarks/results_comparison.json")


if __name__ == "__main__":
    main()
