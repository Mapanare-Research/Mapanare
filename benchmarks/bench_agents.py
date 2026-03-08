"""Benchmark: multi-agent message passing (Phase 4.5).

Measures throughput of the Mapanare agent runtime by sending N messages
through chains of agents with varying topologies.
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
    messages: int
    agents: int
    elapsed_s: float
    messages_per_sec: float
    avg_latency_us: float


async def _bench_single_agent(n_messages: int) -> BenchmarkResult:
    """Benchmark: single agent processing N messages via channels."""
    from runtime.agent import Channel

    inbox: Channel[int] = Channel(maxsize=1024)
    outbox: Channel[int] = Channel(maxsize=1024)
    processed = 0

    async def agent_loop() -> None:
        nonlocal processed
        while processed < n_messages:
            try:
                msg = await asyncio.wait_for(inbox.receive(), timeout=0.05)
                processed += 1
                await outbox.send(msg)
            except asyncio.TimeoutError:
                continue

    task = asyncio.create_task(agent_loop())

    start = time.perf_counter()
    for i in range(n_messages):
        await inbox.send(i)
    while processed < n_messages:
        await asyncio.sleep(0.001)
    elapsed = time.perf_counter() - start

    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    return BenchmarkResult(
        name="single_agent",
        messages=n_messages,
        agents=1,
        elapsed_s=elapsed,
        messages_per_sec=n_messages / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_messages * 1_000_000) if n_messages > 0 else 0,
    )


async def _bench_agent_chain(n_messages: int, chain_length: int) -> BenchmarkResult:
    """Benchmark: chain of agents passing messages through."""
    from runtime.agent import Channel

    channels: list[Channel[int]] = [Channel(maxsize=1024) for _ in range(chain_length + 1)]
    completed = 0

    async def relay(idx: int) -> None:
        nonlocal completed
        count = 0
        while count < n_messages:
            try:
                msg = await asyncio.wait_for(channels[idx].receive(), timeout=0.05)
                await channels[idx + 1].send(msg)
                count += 1
                if idx == chain_length - 1:
                    completed += 1
            except asyncio.TimeoutError:
                continue

    tasks = [asyncio.create_task(relay(i)) for i in range(chain_length)]

    start = time.perf_counter()
    for i in range(n_messages):
        await channels[0].send(i)
    while completed < n_messages:
        await asyncio.sleep(0.001)
    elapsed = time.perf_counter() - start

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    total_hops = n_messages * chain_length
    return BenchmarkResult(
        name=f"agent_chain_{chain_length}",
        messages=n_messages,
        agents=chain_length,
        elapsed_s=elapsed,
        messages_per_sec=total_hops / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / n_messages * 1_000_000) if n_messages > 0 else 0,
    )


async def _bench_fan_out(n_messages: int, fan_width: int) -> BenchmarkResult:
    """Benchmark: one producer fanning out to N consumers."""
    from runtime.agent import Channel

    channels: list[Channel[int]] = [Channel(maxsize=1024) for _ in range(fan_width)]
    total_received = 0

    async def consumer(ch: Channel[int]) -> None:
        nonlocal total_received
        count = 0
        while count < n_messages:
            try:
                await asyncio.wait_for(ch.receive(), timeout=0.05)
                count += 1
                total_received += 1
            except asyncio.TimeoutError:
                continue

    tasks = [asyncio.create_task(consumer(ch)) for ch in channels]

    start = time.perf_counter()
    for i in range(n_messages):
        for ch in channels:
            await ch.send(i)
    expected = n_messages * fan_width
    while total_received < expected:
        await asyncio.sleep(0.001)
    elapsed = time.perf_counter() - start

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    return BenchmarkResult(
        name=f"fan_out_{fan_width}",
        messages=n_messages * fan_width,
        agents=fan_width,
        elapsed_s=elapsed,
        messages_per_sec=(n_messages * fan_width) / elapsed if elapsed > 0 else 0,
        avg_latency_us=(elapsed / (n_messages * fan_width) * 1_000_000) if n_messages > 0 else 0,
    )


async def run_agent_benchmarks(
    n_messages: int = 10_000,
) -> list[BenchmarkResult]:
    """Run all agent message-passing benchmarks."""
    results: list[BenchmarkResult] = []

    results.append(await _bench_single_agent(n_messages))
    results.append(await _bench_agent_chain(n_messages, chain_length=3))
    results.append(await _bench_agent_chain(n_messages, chain_length=5))
    results.append(await _bench_fan_out(n_messages // 10, fan_width=4))

    return results


def main() -> None:
    """CLI entry point for agent benchmarks."""
    results = asyncio.run(run_agent_benchmarks())
    print("\n=== Multi-Agent Message Passing Benchmark ===\n")
    for r in results:
        print(f"  {r.name}:")
        print(f"    Messages:     {r.messages:,}")
        print(f"    Agents:       {r.agents}")
        print(f"    Elapsed:      {r.elapsed_s:.3f}s")
        print(f"    Throughput:   {r.messages_per_sec:,.0f} msg/sec")
        print(f"    Avg latency:  {r.avg_latency_us:.1f} µs")
        print()

    # Write JSON results
    out = [asdict(r) for r in results]
    with open("benchmarks/results_agents.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Results written to benchmarks/results_agents.json")


if __name__ == "__main__":
    main()
