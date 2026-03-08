"""Tests for benchmark suites (Phase 4.5).

Runs benchmarks with small N to verify correctness. Not meant to measure perf.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Agent benchmarks
# ---------------------------------------------------------------------------


class TestAgentBenchmarks:
    @pytest.mark.asyncio
    async def test_single_agent_benchmark(self) -> None:
        from benchmarks.bench_agents import _bench_single_agent

        result = await _bench_single_agent(100)
        assert result.name == "single_agent"
        assert result.messages == 100
        assert result.agents == 1
        assert result.elapsed_s > 0
        assert result.messages_per_sec > 0

    @pytest.mark.asyncio
    async def test_agent_chain_benchmark(self) -> None:
        from benchmarks.bench_agents import _bench_agent_chain

        result = await _bench_agent_chain(100, chain_length=3)
        assert result.name == "agent_chain_3"
        assert result.messages == 100
        assert result.agents == 3
        assert result.elapsed_s > 0

    @pytest.mark.asyncio
    async def test_fan_out_benchmark(self) -> None:
        from benchmarks.bench_agents import _bench_fan_out

        result = await _bench_fan_out(50, fan_width=2)
        assert result.name == "fan_out_2"
        assert result.messages == 100  # 50 * 2
        assert result.agents == 2

    @pytest.mark.asyncio
    async def test_run_agent_benchmarks(self) -> None:
        from benchmarks.bench_agents import run_agent_benchmarks

        results = await run_agent_benchmarks(n_messages=100)
        assert len(results) == 4  # single, chain-3, chain-5, fan-out
        for r in results:
            assert r.elapsed_s > 0
            assert r.messages_per_sec > 0


# ---------------------------------------------------------------------------
# Stream benchmarks
# ---------------------------------------------------------------------------


class TestStreamBenchmarks:
    @pytest.mark.asyncio
    async def test_map_pipeline(self) -> None:
        from benchmarks.bench_streams import _bench_map_pipeline

        result = await _bench_map_pipeline(1000)
        assert result.name == "map_pipeline"
        assert result.items == 1000
        assert result.elapsed_s > 0

    @pytest.mark.asyncio
    async def test_filter_pipeline(self) -> None:
        from benchmarks.bench_streams import _bench_filter_pipeline

        result = await _bench_filter_pipeline(1000)
        assert result.name == "filter_pipeline"
        assert result.items == 1000

    @pytest.mark.asyncio
    async def test_map_filter_pipeline(self) -> None:
        from benchmarks.bench_streams import _bench_map_filter_pipeline

        result = await _bench_map_filter_pipeline(1000)
        assert result.name == "map_filter_pipeline"

    @pytest.mark.asyncio
    async def test_chained_maps(self) -> None:
        from benchmarks.bench_streams import _bench_chained_maps

        result = await _bench_chained_maps(1000, chain_length=3)
        assert result.name == "chained_maps_3"
        assert result.items == 1000

    @pytest.mark.asyncio
    async def test_take(self) -> None:
        from benchmarks.bench_streams import _bench_take

        result = await _bench_take(1000, take_count=100)
        assert result.name == "take_100_from_1000"
        assert result.items == 1000

    @pytest.mark.asyncio
    async def test_fold(self) -> None:
        from benchmarks.bench_streams import _bench_fold

        result = await _bench_fold(1000)
        assert result.name == "fold_sum"

    @pytest.mark.asyncio
    async def test_run_stream_benchmarks(self) -> None:
        from benchmarks.bench_streams import run_stream_benchmarks

        results = await run_stream_benchmarks(n_items=1000)
        assert len(results) == 7
        for r in results:
            assert r.elapsed_s > 0


# ---------------------------------------------------------------------------
# Comparison benchmarks
# ---------------------------------------------------------------------------


class TestComparisonBenchmarks:
    @pytest.mark.asyncio
    async def test_message_passing_comparison(self) -> None:
        from benchmarks.bench_compare import _asyncio_message_passing, _mapanare_message_passing

        mn = await _mapanare_message_passing(100)
        asyncio_baseline = await _asyncio_message_passing(100)
        assert mn > 0
        assert asyncio_baseline > 0

    @pytest.mark.asyncio
    async def test_stream_map_comparison(self) -> None:
        from benchmarks.bench_compare import _asyncio_stream_map, _mapanare_stream_map

        mn = await _mapanare_stream_map(1000)
        asyncio_baseline = await _asyncio_stream_map(1000)
        assert mn > 0
        assert asyncio_baseline > 0

    @pytest.mark.asyncio
    async def test_run_comparison(self) -> None:
        from benchmarks.bench_compare import run_comparison

        results = await run_comparison(n_messages=100, n_items=1000)
        assert len(results) == 4
        for r in results:
            assert r.mapanare_elapsed_s > 0
            assert r.asyncio_elapsed_s > 0
            assert r.mapanare_vs_asyncio > 0

    @pytest.mark.asyncio
    async def test_rust_baselines_without_file(self) -> None:
        from benchmarks.bench_compare import _load_rust_baselines

        baselines = _load_rust_baselines()
        # Without the file, should return empty dict
        assert isinstance(baselines, dict)


# ---------------------------------------------------------------------------
# Benchmark result dataclasses
# ---------------------------------------------------------------------------


class TestBenchmarkResults:
    def test_agent_result_fields(self) -> None:
        from benchmarks.bench_agents import BenchmarkResult

        r = BenchmarkResult(
            name="test",
            messages=100,
            agents=1,
            elapsed_s=0.5,
            messages_per_sec=200,
            avg_latency_us=5000,
        )
        assert r.name == "test"
        assert r.messages_per_sec == 200

    def test_stream_result_fields(self) -> None:
        from benchmarks.bench_streams import BenchmarkResult

        r = BenchmarkResult(
            name="test",
            items=1000,
            elapsed_s=0.1,
            items_per_sec=10000,
            avg_latency_us=100,
        )
        assert r.items == 1000

    def test_comparison_result_fields(self) -> None:
        from benchmarks.bench_compare import ComparisonResult

        r = ComparisonResult(
            workload="test",
            mapanare_elapsed_s=0.1,
            asyncio_elapsed_s=0.2,
            rust_elapsed_s=None,
            mapanare_vs_asyncio=2.0,
            mapanare_vs_rust=None,
        )
        assert r.mapanare_vs_asyncio == 2.0
        assert r.mapanare_vs_rust is None
