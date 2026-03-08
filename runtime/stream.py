"""Mapanare stream runtime -- async stream with operators, backpressure, and fusion."""

from __future__ import annotations

import asyncio
import enum
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Generic,
    Iterable,
    TypeVar,
)

T = TypeVar("T")
U = TypeVar("U")


# ---------------------------------------------------------------------------
# Stream kind
# ---------------------------------------------------------------------------


class StreamKind(enum.Enum):
    """Whether a stream is cold (restarts per consumer) or hot (shared)."""

    COLD = "cold"
    HOT = "hot"


# ---------------------------------------------------------------------------
# Fused operation layer
# ---------------------------------------------------------------------------


class _FusedOp:
    """Base for fused operations that can be collapsed into a single pass."""

    pass


class _MapOp(_FusedOp):
    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self.fn = fn


class _FilterOp(_FusedOp):
    def __init__(self, fn: Callable[[Any], bool]) -> None:
        self.fn = fn


# ---------------------------------------------------------------------------
# Stream
# ---------------------------------------------------------------------------


class Stream(Generic[T]):
    """Async stream that wraps an async iterator with composable operators.

    Supports backpressure via bounded internal buffers, hot/cold semantics,
    and stream fusion for adjacent map/filter operations.
    """

    def __init__(
        self,
        source: AsyncIterator[T],
        *,
        buffer_size: int = 0,
        kind: StreamKind = StreamKind.COLD,
    ) -> None:
        self._source = source
        self._buffer_size = buffer_size
        self._kind = kind
        self._fused_ops: list[_FusedOp] = []

        # Hot stream state
        self._hot_subscribers: list[asyncio.Queue[T]] = []
        self._hot_task: asyncio.Task[None] | None = None

    def __aiter__(self) -> AsyncIterator[T]:
        if self._fused_ops:
            return self._run_fused()
        if self._kind == StreamKind.HOT:
            return self._hot_iter()
        return self._source

    async def __anext__(self) -> T:
        return await self.__aiter__().__anext__()

    # -- Constructors -------------------------------------------------------

    @classmethod
    def from_iter(cls, iterable: Iterable[T], **kwargs: Any) -> Stream[T]:
        """Create a stream from a sync iterable."""

        async def _gen() -> AsyncIterator[T]:
            for item in iterable:
                yield item

        return cls(_gen(), **kwargs)

    @classmethod
    def from_async(cls, ait: AsyncIterator[T], **kwargs: Any) -> Stream[T]:
        """Wrap an existing async iterator."""
        return cls(ait, **kwargs)

    @classmethod
    def empty(cls) -> Stream[T]:
        """Create an empty stream."""

        async def _gen() -> AsyncIterator[T]:
            return
            yield  # make it a generator

        return cls(_gen())

    # -- Backpressure -------------------------------------------------------

    @property
    def buffer_size(self) -> int:
        """Return the backpressure buffer size (0 = unbounded)."""
        return self._buffer_size

    @classmethod
    def bounded(cls, source: AsyncIterator[T], buffer_size: int) -> Stream[T]:
        """Create a stream with bounded backpressure buffer."""
        queue: asyncio.Queue[T] = asyncio.Queue(maxsize=buffer_size)

        async def _buffered() -> AsyncIterator[T]:
            producer_done = asyncio.Event()

            async def _produce() -> None:
                try:
                    async for item in source:
                        await queue.put(item)
                finally:
                    producer_done.set()

            task = asyncio.ensure_future(_produce())
            try:
                while True:
                    if producer_done.is_set() and queue.empty():
                        break
                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=0.05)
                        yield item
                    except asyncio.TimeoutError:
                        if producer_done.is_set() and queue.empty():
                            break
            finally:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        return cls(_buffered(), buffer_size=buffer_size)

    # -- Hot streams --------------------------------------------------------

    @classmethod
    def hot(cls, source: AsyncIterator[T]) -> Stream[T]:
        """Create a hot stream that shares values across all subscribers."""
        stream = cls(source, kind=StreamKind.HOT)
        return stream

    def _start_hot(self) -> None:
        """Start the hot distribution loop if not already running."""
        if self._hot_task is not None:
            return

        async def _distribute() -> None:
            try:
                async for item in self._source:
                    for q in list(self._hot_subscribers):
                        try:
                            q.put_nowait(item)
                        except asyncio.QueueFull:
                            pass  # drop on backpressure
            except asyncio.CancelledError:
                pass

        self._hot_task = asyncio.ensure_future(_distribute())

    async def _hot_iter(self) -> AsyncIterator[T]:
        """Subscribe to a hot stream."""
        q: asyncio.Queue[T] = asyncio.Queue(
            maxsize=self._buffer_size if self._buffer_size > 0 else 0
        )
        self._hot_subscribers.append(q)
        self._start_hot()
        try:
            while True:
                item = await q.get()
                yield item
        finally:
            if q in self._hot_subscribers:
                self._hot_subscribers.remove(q)

    @property
    def kind(self) -> StreamKind:
        """Return whether this is a hot or cold stream."""
        return self._kind

    async def stop_hot(self) -> None:
        """Stop the hot distribution loop and clear subscribers."""
        if self._hot_task is not None:
            self._hot_task.cancel()
            try:
                await self._hot_task
            except asyncio.CancelledError:
                pass
            self._hot_task = None
        self._hot_subscribers.clear()

    # -- Operators (lazy, return new Stream) ---------------------------------

    def map(self, fn: Callable[[T], U]) -> Stream[U]:
        """Transform each element."""
        # Stream fusion: accumulate ops instead of nesting generators
        new_stream: Stream[U] = Stream(self._source, kind=self._kind)  # type: ignore[arg-type]
        new_stream._fused_ops = list(self._fused_ops) + [_MapOp(fn)]
        return new_stream

    def filter(self, fn: Callable[[T], bool]) -> Stream[T]:
        """Keep elements matching predicate."""
        new_stream: Stream[T] = Stream(self._source, kind=self._kind)
        new_stream._fused_ops = list(self._fused_ops) + [_FilterOp(fn)]
        return new_stream

    def flat_map(self, fn: Callable[[T], Stream[U]]) -> Stream[U]:
        """Map each element to a stream, then flatten."""
        parent = self

        async def _gen() -> AsyncIterator[U]:
            async for item in parent:
                sub = fn(item)
                async for sub_item in sub:
                    yield sub_item

        return Stream(_gen())

    def take(self, n: int) -> Stream[T]:
        """Emit only the first n elements."""
        parent = self

        async def _gen() -> AsyncIterator[T]:
            count = 0
            async for item in parent:
                if count >= n:
                    break
                yield item
                count += 1

        return Stream(_gen())

    def skip(self, n: int) -> Stream[T]:
        """Skip the first n elements."""
        parent = self

        async def _gen() -> AsyncIterator[T]:
            count = 0
            async for item in parent:
                if count >= n:
                    yield item
                count += 1

        return Stream(_gen())

    def chunk(self, size: int) -> Stream[list[T]]:
        """Group elements into chunks of given size."""
        parent = self

        async def _gen() -> AsyncIterator[list[T]]:
            buf: list[T] = []
            async for item in parent:
                buf.append(item)
                if len(buf) >= size:
                    yield buf
                    buf = []
            if buf:
                yield buf

        return Stream(_gen())

    def zip(self, other: Stream[U]) -> Stream[tuple[T, U]]:
        """Pair elements from two streams positionally."""
        parent = self

        async def _gen() -> AsyncIterator[tuple[T, U]]:
            it1 = parent.__aiter__()
            it2 = other.__aiter__()
            while True:
                try:
                    a = await it1.__anext__()
                except StopAsyncIteration:
                    break
                try:
                    b = await it2.__anext__()
                except StopAsyncIteration:
                    break
                yield (a, b)

        return Stream(_gen())

    @staticmethod
    def merge(*streams: Stream[T]) -> Stream[T]:
        """Interleave elements from multiple streams as they arrive."""

        async def _gen() -> AsyncIterator[T]:
            queue: asyncio.Queue[tuple[bool, T]] = asyncio.Queue()
            active = len(streams)

            async def _feed(s: Stream[T]) -> None:
                nonlocal active
                try:
                    async for item in s:
                        await queue.put((False, item))
                finally:
                    active -= 1
                    if active == 0:
                        await queue.put((True, None))  # type: ignore[arg-type]

            tasks = [asyncio.ensure_future(_feed(s)) for s in streams]
            try:
                while True:
                    done, item = await queue.get()
                    if done:
                        break
                    yield item
            finally:
                for t in tasks:
                    t.cancel()

        return Stream(_gen())

    # -- Terminal operators (consume the stream) ----------------------------

    async def collect(self) -> list[T]:
        """Collect all elements into a list."""
        result: list[T] = []
        async for item in self:
            result.append(item)
        return result

    async def first(self) -> T | None:
        """Get the first element, or None if empty."""
        async for item in self:
            return item
        return None

    async def last(self) -> T | None:
        """Get the last element, or None if empty."""
        result: T | None = None
        async for item in self:
            result = item
        return result

    async def fold(self, init: U, fn: Callable[[U, T], U]) -> U:
        """Reduce stream to a single value."""
        acc = init
        async for item in self:
            acc = fn(acc, item)
        return acc

    async def for_each(self, fn: Callable[[T], Any]) -> None:
        """Apply function to each element."""
        async for item in self:
            result = fn(item)
            if asyncio.iscoroutine(result):
                await result

    async def count(self) -> int:
        """Count elements in the stream."""
        n = 0
        async for _ in self:
            n += 1
        return n

    # -- Stream fusion internals --------------------------------------------

    async def _run_fused(self) -> AsyncIterator[T]:
        """Execute fused map/filter operations in a single pass."""
        ops = self._fused_ops
        async for item in self._source:
            val: Any = item
            skip = False
            for op in ops:
                if isinstance(op, _MapOp):
                    val = op.fn(val)
                elif isinstance(op, _FilterOp):
                    if not op.fn(val):
                        skip = True
                        break
            if not skip:
                yield val
