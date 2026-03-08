"""Benchmark: stream pipeline 1M items (Phase 4.5).

Measures throughput of the Mapanare stream engine processing large data volumes
through various operator combinations.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    items: int
    elapsed_s: float
    items_per_sec: float
    avg_latency_us: float


async def _bench_map_pipeline(n_items: int) -> BenchmarkResult:
    """Benchmark: map transformation over N items."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))
    mapped = stream.map(lambda x: x * 2)

    start = time.perf_counter()
    result = await mapped.collect()
    elapsed = time.perf_counter() - start

    assert len(result) == n_items

    return BenchmarkResult(
        name="map_pipeline",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=n_items / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_items * 1_000_000) if n_items > 0 else 0,
    )


async def _bench_filter_pipeline(n_items: int) -> BenchmarkResult:
    """Benchmark: filter over N items (keep ~50%)."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))
    filtered = stream.filter(lambda x: x % 2 == 0)

    start = time.perf_counter()
    result = await filtered.collect()
    elapsed = time.perf_counter() - start

    assert len(result) == n_items // 2

    return BenchmarkResult(
        name="filter_pipeline",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=n_items / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_items * 1_000_000) if n_items > 0 else 0,
    )


async def _bench_map_filter_pipeline(n_items: int) -> BenchmarkResult:
    """Benchmark: map then filter over N items."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))
    pipeline = stream.map(lambda x: x * 3).filter(lambda x: x % 2 == 0)

    start = time.perf_counter()
    await pipeline.collect()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="map_filter_pipeline",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=n_items / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_items * 1_000_000) if n_items > 0 else 0,
    )


async def _bench_chained_maps(n_items: int, chain_length: int) -> BenchmarkResult:
    """Benchmark: N chained map operations."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))
    pipeline = stream
    for _ in range(chain_length):
        pipeline = pipeline.map(lambda x: x + 1)

    start = time.perf_counter()
    result = await pipeline.collect()
    elapsed = time.perf_counter() - start

    assert len(result) == n_items

    return BenchmarkResult(
        name=f"chained_maps_{chain_length}",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=n_items / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_items * 1_000_000) if n_items > 0 else 0,
    )


async def _bench_take(n_items: int, take_count: int) -> BenchmarkResult:
    """Benchmark: take first N items from large stream."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))
    pipeline = stream.take(take_count)

    start = time.perf_counter()
    result = await pipeline.collect()
    elapsed = time.perf_counter() - start

    assert len(result) == take_count

    return BenchmarkResult(
        name=f"take_{take_count}_from_{n_items}",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=take_count / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / take_count * 1_000_000) if take_count > 0 else 0,
    )


async def _bench_fold(n_items: int) -> BenchmarkResult:
    """Benchmark: fold/reduce over N items."""
    from runtime.stream import Stream

    stream = Stream.from_iter(range(n_items))

    start = time.perf_counter()
    result = await stream.fold(0, lambda acc, x: acc + x)
    elapsed = time.perf_counter() - start

    expected = n_items * (n_items - 1) // 2
    assert result == expected

    return BenchmarkResult(
        name="fold_sum",
        items=n_items,
        elapsed_s=elapsed,
        items_per_sec=n_items / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_items * 1_000_000) if n_items > 0 else 0,
    )


async def run_stream_benchmarks(
    n_items: int = 1_000_000,
) -> list[BenchmarkResult]:
    """Run all stream pipeline benchmarks."""
    results: list[BenchmarkResult] = []

    results.append(await _bench_map_pipeline(n_items))
    results.append(await _bench_filter_pipeline(n_items))
    results.append(await _bench_map_filter_pipeline(n_items))
    results.append(await _bench_chained_maps(n_items, chain_length=5))
    results.append(await _bench_chained_maps(n_items, chain_length=10))
    results.append(await _bench_take(n_items, take_count=1000))
    results.append(await _bench_fold(n_items))

    return results


def main() -> None:
    """CLI entry point for stream benchmarks."""
    results = asyncio.run(run_stream_benchmarks())
    print("\n=== Stream Pipeline 1M Items Benchmark ===\n")
    for r in results:
        print(f"  {r.name}:")
        print(f"    Items:        {r.items:,}")
        print(f"    Elapsed:      {r.elapsed_s:.3f}s")
        print(f"    Throughput:   {r.items_per_sec:,.0f} items/sec")
        print(f"    Avg latency:  {r.avg_latency_us:.2f} µs")
        print()

    out = [asdict(r) for r in results]
    with open("benchmarks/results_streams.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Results written to benchmarks/results_streams.json")


if __name__ == "__main__":
    main()
