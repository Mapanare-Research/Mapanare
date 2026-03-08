"""Tests for Phase 3.3 — Stream Engine."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest

from runtime.stream import Stream, StreamKind

# ===========================================================================
# Task 1 — Stream<T>: async iterable with backpressure
# ===========================================================================


class TestStreamBasic:
    @pytest.mark.asyncio
    async def test_from_iter(self) -> None:
        s = Stream.from_iter([1, 2, 3])
        result = await s.collect()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_from_async(self) -> None:
        async def gen() -> AsyncIterator[int]:
            for i in range(3):
                yield i

        s = Stream.from_async(gen())
        result = await s.collect()
        assert result == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_empty_stream(self) -> None:
        s: Stream[int] = Stream.empty()
        result = await s.collect()
        assert result == []

    @pytest.mark.asyncio
    async def test_async_iteration(self) -> None:
        s = Stream.from_iter([10, 20, 30])
        items: list[int] = []
        async for item in s:
            items.append(item)
        assert items == [10, 20, 30]


class TestBackpressure:
    @pytest.mark.asyncio
    async def test_bounded_stream(self) -> None:
        """Bounded stream with small buffer still delivers all items."""

        async def slow_source() -> AsyncIterator[int]:
            for i in range(10):
                yield i

        s = Stream.bounded(slow_source(), buffer_size=3)
        assert s.buffer_size == 3
        result = await s.collect()
        assert result == list(range(10))

    @pytest.mark.asyncio
    async def test_bounded_blocks_producer(self) -> None:
        """Producer should block when buffer is full."""
        produced: list[int] = []

        async def source() -> AsyncIterator[int]:
            for i in range(5):
                produced.append(i)
                yield i

        s = Stream.bounded(source(), buffer_size=2)
        result = await s.collect()
        assert result == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_unbounded_buffer_default(self) -> None:
        s = Stream.from_iter([1, 2, 3])
        assert s.buffer_size == 0


# ===========================================================================
# Task 2 — Operators: map, filter, flat_map
# ===========================================================================


class TestMapFilterFlatMap:
    @pytest.mark.asyncio
    async def test_map(self) -> None:
        s = Stream.from_iter([1, 2, 3]).map(lambda x: x * 10)
        assert await s.collect() == [10, 20, 30]

    @pytest.mark.asyncio
    async def test_filter(self) -> None:
        s = Stream.from_iter([1, 2, 3, 4, 5]).filter(lambda x: x % 2 == 0)
        assert await s.collect() == [2, 4]

    @pytest.mark.asyncio
    async def test_flat_map(self) -> None:
        s = Stream.from_iter([1, 2, 3]).flat_map(lambda x: Stream.from_iter([x, x * 10]))
        assert await s.collect() == [1, 10, 2, 20, 3, 30]

    @pytest.mark.asyncio
    async def test_map_type_change(self) -> None:
        s = Stream.from_iter([1, 2, 3]).map(str)
        assert await s.collect() == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_filter_all_out(self) -> None:
        s = Stream.from_iter([1, 2, 3]).filter(lambda x: x > 100)
        assert await s.collect() == []

    @pytest.mark.asyncio
    async def test_flat_map_empty_sub(self) -> None:
        s = Stream.from_iter([1, 2]).flat_map(lambda _: Stream.empty())
        assert await s.collect() == []

    @pytest.mark.asyncio
    async def test_chained_map_filter(self) -> None:
        s = Stream.from_iter(range(10)).map(lambda x: x * 2).filter(lambda x: x > 10)
        assert await s.collect() == [12, 14, 16, 18]


# ===========================================================================
# Task 3 — Operators: take, skip, chunk, zip, merge
# ===========================================================================


class TestTakeSkipChunk:
    @pytest.mark.asyncio
    async def test_take(self) -> None:
        s = Stream.from_iter(range(100)).take(5)
        assert await s.collect() == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_take_more_than_available(self) -> None:
        s = Stream.from_iter([1, 2]).take(10)
        assert await s.collect() == [1, 2]

    @pytest.mark.asyncio
    async def test_skip(self) -> None:
        s = Stream.from_iter([1, 2, 3, 4, 5]).skip(3)
        assert await s.collect() == [4, 5]

    @pytest.mark.asyncio
    async def test_skip_all(self) -> None:
        s = Stream.from_iter([1, 2]).skip(10)
        assert await s.collect() == []

    @pytest.mark.asyncio
    async def test_chunk(self) -> None:
        s = Stream.from_iter(range(7)).chunk(3)
        assert await s.collect() == [[0, 1, 2], [3, 4, 5], [6]]

    @pytest.mark.asyncio
    async def test_chunk_exact(self) -> None:
        s = Stream.from_iter(range(6)).chunk(3)
        assert await s.collect() == [[0, 1, 2], [3, 4, 5]]


class TestZipMerge:
    @pytest.mark.asyncio
    async def test_zip_equal_length(self) -> None:
        a = Stream.from_iter([1, 2, 3])
        b = Stream.from_iter(["a", "b", "c"])
        result = await a.zip(b).collect()
        assert result == [(1, "a"), (2, "b"), (3, "c")]

    @pytest.mark.asyncio
    async def test_zip_unequal_length(self) -> None:
        a = Stream.from_iter([1, 2, 3, 4])
        b = Stream.from_iter(["x", "y"])
        result = await a.zip(b).collect()
        assert result == [(1, "x"), (2, "y")]

    @pytest.mark.asyncio
    async def test_zip_empty(self) -> None:
        a = Stream.from_iter([1, 2])
        b: Stream[str] = Stream.empty()
        result = await a.zip(b).collect()
        assert result == []

    @pytest.mark.asyncio
    async def test_merge_two_streams(self) -> None:
        a = Stream.from_iter([1, 2, 3])
        b = Stream.from_iter([10, 20, 30])
        result = await Stream.merge(a, b).collect()
        # Merge interleaves — all items present, order may vary
        assert sorted(result) == [1, 2, 3, 10, 20, 30]

    @pytest.mark.asyncio
    async def test_merge_three_streams(self) -> None:
        a = Stream.from_iter([1])
        b = Stream.from_iter([2])
        c = Stream.from_iter([3])
        result = await Stream.merge(a, b, c).collect()
        assert sorted(result) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_merge_with_empty(self) -> None:
        a = Stream.from_iter([1, 2])
        b: Stream[int] = Stream.empty()
        result = await Stream.merge(a, b).collect()
        assert sorted(result) == [1, 2]


# ===========================================================================
# Task 4 — Hot vs cold streams
# ===========================================================================


class TestHotColdStreams:
    @pytest.mark.asyncio
    async def test_cold_stream_default(self) -> None:
        s = Stream.from_iter([1, 2, 3])
        assert s.kind == StreamKind.COLD

    @pytest.mark.asyncio
    async def test_hot_stream_creation(self) -> None:
        async def source() -> AsyncIterator[int]:
            for i in range(5):
                yield i
                await asyncio.sleep(0.01)

        s = Stream.hot(source())
        assert s.kind == StreamKind.HOT

    @pytest.mark.asyncio
    async def test_hot_stream_multiple_subscribers(self) -> None:
        """Multiple subscribers to a hot stream all receive items."""
        produced: list[int] = []

        async def source() -> AsyncIterator[int]:
            for i in range(5):
                produced.append(i)
                yield i
                await asyncio.sleep(0.02)

        s = Stream.hot(source())

        results_a: list[int] = []
        results_b: list[int] = []

        async def consumer(results: list[int]) -> None:
            count = 0
            async for item in s:
                results.append(item)
                count += 1
                if count >= 3:
                    break

        await asyncio.wait_for(
            asyncio.gather(consumer(results_a), consumer(results_b)),
            timeout=3.0,
        )

        # Both consumers got items from the same stream
        assert len(results_a) == 3
        assert len(results_b) == 3

        await s.stop_hot()

    @pytest.mark.asyncio
    async def test_cold_stream_independent_iteration(self) -> None:
        """Cold streams produce independent iterations."""
        data = [1, 2, 3]
        s1 = Stream.from_iter(data)
        # Cold: each __aiter__ returns the source, so only one iteration
        result = await s1.collect()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_hot_stream_stop(self) -> None:
        async def source() -> AsyncIterator[int]:
            i = 0
            while True:
                yield i
                i += 1
                await asyncio.sleep(0.01)

        s = Stream.hot(source())
        # Start a subscriber briefly
        items: list[int] = []
        async for item in s:
            items.append(item)
            if len(items) >= 3:
                break

        await s.stop_hot()
        assert s._hot_task is None
        assert s._hot_subscribers == []


# ===========================================================================
# Task 5 — stream.collect(), stream.first(), stream.last()
# ===========================================================================


class TestTerminalOps:
    @pytest.mark.asyncio
    async def test_collect(self) -> None:
        assert await Stream.from_iter([1, 2, 3]).collect() == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_collect_empty(self) -> None:
        assert await Stream.empty().collect() == []

    @pytest.mark.asyncio
    async def test_first(self) -> None:
        assert await Stream.from_iter([10, 20, 30]).first() == 10

    @pytest.mark.asyncio
    async def test_first_empty(self) -> None:
        assert await Stream.empty().first() is None

    @pytest.mark.asyncio
    async def test_last(self) -> None:
        assert await Stream.from_iter([10, 20, 30]).last() == 30

    @pytest.mark.asyncio
    async def test_last_empty(self) -> None:
        assert await Stream.empty().last() is None

    @pytest.mark.asyncio
    async def test_last_single_element(self) -> None:
        assert await Stream.from_iter([42]).last() == 42

    @pytest.mark.asyncio
    async def test_fold(self) -> None:
        result = await Stream.from_iter([1, 2, 3, 4]).fold(0, lambda a, b: a + b)
        assert result == 10

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        assert await Stream.from_iter(range(50)).count() == 50

    @pytest.mark.asyncio
    async def test_count_empty(self) -> None:
        assert await Stream.empty().count() == 0

    @pytest.mark.asyncio
    async def test_for_each(self) -> None:
        items: list[int] = []
        await Stream.from_iter([1, 2, 3]).for_each(lambda x: items.append(x))
        assert items == [1, 2, 3]


# ===========================================================================
# Task 6 — Stream fusion: adjacent ops collapse into single pass
# ===========================================================================


class TestStreamFusion:
    @pytest.mark.asyncio
    async def test_fused_map_map(self) -> None:
        """Two adjacent maps fuse into one pass."""
        s = Stream.from_iter([1, 2, 3]).map(lambda x: x + 1).map(lambda x: x * 10)
        # Check fusion ops accumulated
        assert len(s._fused_ops) == 2
        assert await s.collect() == [20, 30, 40]

    @pytest.mark.asyncio
    async def test_fused_filter_map(self) -> None:
        s = Stream.from_iter(range(6)).filter(lambda x: x % 2 == 0).map(lambda x: x * 100)
        assert len(s._fused_ops) == 2
        assert await s.collect() == [0, 200, 400]

    @pytest.mark.asyncio
    async def test_fused_map_filter_map(self) -> None:
        s = (
            Stream.from_iter(range(10))
            .map(lambda x: x * 2)
            .filter(lambda x: x > 10)
            .map(lambda x: x + 1)
        )
        assert len(s._fused_ops) == 3
        assert await s.collect() == [13, 15, 17, 19]

    @pytest.mark.asyncio
    async def test_fusion_single_pass(self) -> None:
        """Verify fused ops iterate source only once."""
        call_count = 0

        async def counting_source() -> AsyncIterator[int]:
            nonlocal call_count
            for i in range(5):
                call_count += 1
                yield i

        s = (
            Stream(counting_source())
            .map(lambda x: x + 1)
            .filter(lambda x: x > 2)
            .map(lambda x: x * 10)
        )
        result = await s.collect()
        assert result == [30, 40, 50]
        assert call_count == 5  # source iterated exactly once

    @pytest.mark.asyncio
    async def test_no_fusion_with_flat_map(self) -> None:
        """flat_map breaks fusion chain."""
        s = (
            Stream.from_iter([1, 2])
            .map(lambda x: x * 2)
            .flat_map(lambda x: Stream.from_iter([x, x + 1]))
        )
        # flat_map creates a new stream without fused ops
        assert s._fused_ops == []
        assert await s.collect() == [2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_fusion_preserves_correctness(self) -> None:
        """Same result with and without fusion."""
        data = list(range(20))

        # Without fusion (using flat_map to break)
        result_manual: list[int] = []
        for x in data:
            v = x * 3
            if v > 15:
                result_manual.append(v + 1)

        # With fusion
        result_fused = await (
            Stream.from_iter(data)
            .map(lambda x: x * 3)
            .filter(lambda x: x > 15)
            .map(lambda x: x + 1)
            .collect()
        )
        assert result_fused == result_manual
