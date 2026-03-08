"""Mapanare signal runtime -- reactive Signal graph with dependency tracking."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Dependency tracking context
# ---------------------------------------------------------------------------

_tracking_stack: list[Signal[Any]] = []
"""Stack of computed signals currently being evaluated.

When a computed signal evaluates its function, it pushes itself here.
Any signal whose ``.value`` is read during that evaluation registers
itself as a dependency of the top-of-stack computed signal.
"""


def _current_tracker() -> Signal[Any] | None:
    return _tracking_stack[-1] if _tracking_stack else None


# ---------------------------------------------------------------------------
# Batching context
# ---------------------------------------------------------------------------

_batch_depth: int = 0
_batch_pending: set[Signal[Any]] = set()
"""Signals whose value changed inside a ``batch()`` block.

Propagation is deferred until the outermost ``batch()`` exits.
"""


class batch:  # noqa: N801 — lowercase for ``with batch():`` usage
    """Context manager that batches multiple signal updates into one propagation pass.

    Usage::

        with batch():
            sig_a.value = 1
            sig_b.value = 2
        # subscribers notified once here
    """

    def __enter__(self) -> batch:
        global _batch_depth
        _batch_depth += 1
        return self

    def __exit__(self, *_: Any) -> None:
        global _batch_depth
        _batch_depth -= 1
        if _batch_depth == 0:
            pending = list(_batch_pending)
            _batch_pending.clear()
            for sig in pending:
                sig._propagate()


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------


class Signal(Generic[T]):
    """Reactive signal that holds a value and notifies dependents on change.

    Supports:
    - Plain value signals: ``Signal(10)``
    - Computed signals with automatic dependency tracking
    - Subscriber callbacks
    - Rolling history window
    - Change streams via ``.changes()``
    """

    def __init__(
        self,
        initial: T | None = None,
        *,
        computed: Callable[[], T] | None = None,
        history_size: int = 0,
    ) -> None:
        self._computed = computed
        self._subscribers: list[Signal[Any]] = []
        self._callbacks: list[Callable[[T], Any]] = []
        self._dirty = True
        self._history: deque[T] = deque(maxlen=history_size if history_size > 0 else None)
        self._history_enabled = history_size > 0
        self._change_queues: list[asyncio.Queue[T]] = []

        # Dependency tracking for computed signals
        self._dependencies: list[Signal[Any]] = []

        if computed is not None:
            self._raw: T | None = None
            # Initial evaluation to discover dependencies
            self._evaluate()
        else:
            self._raw = initial
            self._dirty = False
            if self._history_enabled and initial is not None:
                self._history.append(initial)

    # -- Dependency tracking helpers ----------------------------------------

    def _evaluate(self) -> None:
        """Evaluate the computed function while tracking dependencies."""
        if self._computed is None:
            return

        # Clear old dependencies
        for dep in self._dependencies:
            if self in dep._subscribers:
                dep._subscribers.remove(self)
        self._dependencies.clear()

        # Track reads
        _tracking_stack.append(self)
        try:
            self._raw = self._computed()
        finally:
            _tracking_stack.pop()
        self._dirty = False

    def _register_dependency(self, source: Signal[Any]) -> None:
        """Record *source* as a dependency of this computed signal."""
        if source not in self._dependencies:
            self._dependencies.append(source)
            source.subscribe(self)

    # -- Public API ---------------------------------------------------------

    @property
    def value(self) -> T:
        """Get the current value, recomputing if dirty."""
        tracker = _current_tracker()
        if tracker is not None and tracker is not self:
            tracker._register_dependency(self)

        if self._computed is not None and self._dirty:
            self._evaluate()

        return self._raw  # type: ignore[return-value]

    @value.setter
    def value(self, new_value: T) -> None:
        """Set the value and notify dependents."""
        if self._computed is not None:
            raise AttributeError("Cannot set value of a computed signal")
        old = self._raw
        self._raw = new_value
        if old != new_value:
            if self._history_enabled:
                self._history.append(new_value)
            # Push to change streams
            for q in self._change_queues:
                q.put_nowait(new_value)
            if _batch_depth > 0:
                _batch_pending.add(self)
            else:
                self._propagate()

    def _propagate(self) -> None:
        """Notify subscribers and fire callbacks."""
        for sub in list(self._subscribers):
            sub._dirty = True
            if sub._computed is not None:
                sub._evaluate()
                # Record history/changes for computed signals too
                if sub._history_enabled and sub._raw is not None:
                    sub._history.append(sub._raw)
                for q in sub._change_queues:
                    q.put_nowait(sub._raw)
            sub._propagate()
        for cb in self._callbacks:
            cb(self._raw)  # type: ignore[arg-type]

    def subscribe(self, dependent: Signal[Any]) -> None:
        """Register a dependent signal."""
        if dependent not in self._subscribers:
            self._subscribers.append(dependent)

    def on_change(self, callback: Callable[[T], Any]) -> None:
        """Register a callback invoked with the new value on every change."""
        self._callbacks.append(callback)

    # -- History ------------------------------------------------------------

    def set_history_size(self, size: int) -> None:
        """Enable or resize the rolling history window."""
        self._history_enabled = size > 0
        new_deque: deque[T] = deque(self._history, maxlen=size if size > 0 else None)
        self._history = new_deque

    @property
    def history(self) -> list[T]:
        """Return the rolling window of past values (oldest first)."""
        return list(self._history)

    # -- Change stream ------------------------------------------------------

    def changes(self) -> SignalChangeStream[T]:
        """Return an async stream of value changes (diffs)."""
        q: asyncio.Queue[T] = asyncio.Queue()
        self._change_queues.append(q)
        return SignalChangeStream(self, q)


# ---------------------------------------------------------------------------
# SignalChangeStream
# ---------------------------------------------------------------------------


class SignalChangeStream(Generic[T]):
    """Async iterator that yields each new value of a signal as it changes."""

    def __init__(self, signal: Signal[T], queue: asyncio.Queue[T]) -> None:
        self._signal = signal
        self._queue = queue

    def __aiter__(self) -> SignalChangeStream[T]:
        return self

    async def __anext__(self) -> T:
        return await self._queue.get()

    def close(self) -> None:
        """Detach from the signal."""
        if self._queue in self._signal._change_queues:
            self._signal._change_queues.remove(self._queue)
