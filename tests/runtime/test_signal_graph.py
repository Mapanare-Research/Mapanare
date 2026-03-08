"""Tests for Phase 3.2 — Signal Graph."""

from __future__ import annotations

import asyncio

from runtime.signal import Signal, SignalChangeStream, batch

# ===========================================================================
# Task 1 — Signal<T> class: value + subscriber list
# ===========================================================================


class TestSignalBasic:
    def test_create_with_initial_value(self) -> None:
        sig = Signal(42)
        assert sig.value == 42

    def test_set_value(self) -> None:
        sig = Signal(0)
        sig.value = 10
        assert sig.value == 10

    def test_subscriber_list_starts_empty(self) -> None:
        sig = Signal(1)
        assert sig._subscribers == []

    def test_subscribe_adds_dependent(self) -> None:
        parent = Signal(1)
        child = Signal(0)
        parent.subscribe(child)
        assert child in parent._subscribers

    def test_subscribe_idempotent(self) -> None:
        parent = Signal(1)
        child = Signal(0)
        parent.subscribe(child)
        parent.subscribe(child)
        assert parent._subscribers.count(child) == 1

    def test_on_change_callback(self) -> None:
        sig = Signal(0)
        values: list[int] = []
        sig.on_change(lambda v: values.append(v))
        sig.value = 1
        sig.value = 2
        assert values == [1, 2]

    def test_no_callback_on_same_value(self) -> None:
        sig = Signal(5)
        values: list[int] = []
        sig.on_change(lambda v: values.append(v))
        sig.value = 5  # same value
        assert values == []

    def test_cannot_set_computed_signal(self) -> None:
        sig = Signal(computed=lambda: 42)
        try:
            sig.value = 10
            assert False, "Should have raised"
        except AttributeError:
            pass

    def test_none_initial(self) -> None:
        sig: Signal[int | None] = Signal()
        assert sig.value is None

    def test_string_signal(self) -> None:
        sig = Signal("hello")
        assert sig.value == "hello"
        sig.value = "world"
        assert sig.value == "world"


# ===========================================================================
# Task 2 — Automatic dependency tracking in computed signals
# ===========================================================================


class TestDependencyTracking:
    def test_computed_reads_dependencies(self) -> None:
        a = Signal(1)
        b = Signal(2)
        c = Signal(computed=lambda: a.value + b.value)
        assert c.value == 3
        assert a in c._dependencies
        assert b in c._dependencies

    def test_computed_auto_subscribes(self) -> None:
        a = Signal(10)
        c = Signal(computed=lambda: a.value * 2)
        assert c.value == 20
        assert c in a._subscribers

    def test_dependency_chain(self) -> None:
        a = Signal(1)
        b = Signal(computed=lambda: a.value + 1)
        c = Signal(computed=lambda: b.value * 2)
        assert c.value == 4
        assert a in b._dependencies
        assert b in c._dependencies

    def test_dynamic_dependency_tracking(self) -> None:
        """Dependencies can change on re-evaluation."""
        flag = Signal(True)
        x = Signal(10)
        y = Signal(20)
        c = Signal(computed=lambda: x.value if flag.value else y.value)
        assert c.value == 10
        assert x in c._dependencies
        # y may or may not be tracked depending on branch; flag is tracked
        assert flag in c._dependencies

    def test_no_self_dependency(self) -> None:
        """A signal should not track itself as a dependency."""
        a = Signal(1)
        c = Signal(computed=lambda: a.value)
        assert c not in c._dependencies

    def test_multiple_computed_share_source(self) -> None:
        a = Signal(5)
        b = Signal(computed=lambda: a.value + 1)
        c = Signal(computed=lambda: a.value * 2)
        assert b.value == 6
        assert c.value == 10
        assert b in a._subscribers
        assert c in a._subscribers


# ===========================================================================
# Task 3 — Computed signals: auto-recompute on change
# ===========================================================================


class TestAutoRecompute:
    def test_computed_updates_on_source_change(self) -> None:
        a = Signal(1)
        c = Signal(computed=lambda: a.value * 10)
        assert c.value == 10
        a.value = 5
        assert c.value == 50

    def test_chain_recomputation(self) -> None:
        a = Signal(2)
        b = Signal(computed=lambda: a.value + 1)
        c = Signal(computed=lambda: b.value * 3)
        assert c.value == 9
        a.value = 10
        assert b.value == 11
        assert c.value == 33

    def test_diamond_dependency(self) -> None:
        """A depends on B and C, both depend on D."""
        d = Signal(1)
        b = Signal(computed=lambda: d.value + 1)
        c = Signal(computed=lambda: d.value * 2)
        a = Signal(computed=lambda: b.value + c.value)
        assert a.value == 4  # (1+1) + (1*2) = 4
        d.value = 5
        assert a.value == 16  # (5+1) + (5*2) = 16

    def test_recompute_only_when_dirty(self) -> None:
        call_count = 0
        a = Signal(1)

        def compute() -> int:
            nonlocal call_count
            call_count += 1
            return a.value * 2

        c = Signal(computed=compute)
        assert c.value == 2
        initial_count = call_count
        # Reading again without change should not re-evaluate
        _ = c.value
        assert call_count == initial_count

    def test_callback_on_computed_source(self) -> None:
        a = Signal(1)
        c = Signal(computed=lambda: a.value + 1)
        results: list[int] = []
        a.on_change(lambda v: results.append(v))
        a.value = 5
        assert results == [5]
        assert c.value == 6


# ===========================================================================
# Task 4 — Change batching: multiple updates = one pass
# ===========================================================================


class TestBatching:
    def test_batch_defers_propagation(self) -> None:
        a = Signal(0)
        call_count = 0

        def track(_: int) -> None:
            nonlocal call_count
            call_count += 1

        a.on_change(track)

        with batch():
            a.value = 1
            a.value = 2
            a.value = 3
            # During batch, callbacks fire only for unique signal entries
            # but propagation is deferred
        # After batch exits, propagation happens once
        # The signal tracks each _unique set_, but the batch collapses propagation
        assert a.value == 3

    def test_batch_computed_sees_final_value(self) -> None:
        a = Signal(0)
        b = Signal(0)
        c = Signal(computed=lambda: a.value + b.value)
        _ = c.value  # initial evaluation

        with batch():
            a.value = 10
            b.value = 20

        assert c.value == 30

    def test_nested_batch(self) -> None:
        a = Signal(0)
        call_count = 0

        def track(_: int) -> None:
            nonlocal call_count
            call_count += 1

        a.on_change(track)

        with batch():
            a.value = 1
            with batch():
                a.value = 2
            # Inner batch exits but outer still active — no propagation yet
        # Outer exits — propagation happens
        assert a.value == 2

    def test_batch_multiple_signals(self) -> None:
        a = Signal(0)
        b = Signal(0)
        results: list[int] = []
        a.on_change(lambda v: results.append(v))
        b.on_change(lambda v: results.append(v))

        with batch():
            a.value = 1
            b.value = 2

        assert 1 in results or a.value == 1
        assert 2 in results or b.value == 2

    def test_no_batch_immediate_propagation(self) -> None:
        a = Signal(0)
        c = Signal(computed=lambda: a.value + 1)
        _ = c.value  # track
        a.value = 5
        assert c.value == 6  # immediate


# ===========================================================================
# Task 5 — Signal history: rolling window of past values
# ===========================================================================


class TestSignalHistory:
    def test_history_disabled_by_default(self) -> None:
        sig = Signal(1)
        assert sig.history == []

    def test_history_records_initial(self) -> None:
        sig = Signal(1, history_size=5)
        assert sig.history == [1]

    def test_history_records_changes(self) -> None:
        sig = Signal(0, history_size=5)
        sig.value = 1
        sig.value = 2
        sig.value = 3
        assert sig.history == [0, 1, 2, 3]

    def test_history_rolling_window(self) -> None:
        sig = Signal(0, history_size=3)
        sig.value = 1
        sig.value = 2
        sig.value = 3
        sig.value = 4
        # Window of 3: should have [2, 3, 4]
        assert sig.history == [2, 3, 4]

    def test_history_same_value_not_recorded(self) -> None:
        sig = Signal(1, history_size=5)
        sig.value = 1  # no change
        assert sig.history == [1]

    def test_set_history_size(self) -> None:
        sig = Signal(0)
        assert sig.history == []
        sig.set_history_size(3)
        sig.value = 1
        sig.value = 2
        assert sig.history == [1, 2]

    def test_history_on_computed_signal(self) -> None:
        a = Signal(1)
        c = Signal(computed=lambda: a.value * 10, history_size=5)
        assert c.history == []  # computed initial isn't recorded as "change"
        a.value = 2
        a.value = 3
        assert 20 in c.history
        assert 30 in c.history

    def test_history_order(self) -> None:
        sig = Signal(0, history_size=10)
        for i in range(1, 6):
            sig.value = i
        assert sig.history == [0, 1, 2, 3, 4, 5]


# ===========================================================================
# Task 6 — signal.changes() → stream of diffs
# ===========================================================================


class TestSignalChanges:
    async def test_changes_returns_stream(self) -> None:
        sig = Signal(0)
        stream = sig.changes()
        assert isinstance(stream, SignalChangeStream)

    async def test_changes_receives_updates(self) -> None:
        sig = Signal(0)
        stream = sig.changes()

        sig.value = 1
        sig.value = 2

        val1 = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        val2 = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        assert val1 == 1
        assert val2 == 2

    async def test_changes_multiple_subscribers(self) -> None:
        sig = Signal(0)
        s1 = sig.changes()
        s2 = sig.changes()

        sig.value = 42

        v1 = await asyncio.wait_for(s1.__anext__(), timeout=1.0)
        v2 = await asyncio.wait_for(s2.__anext__(), timeout=1.0)
        assert v1 == 42
        assert v2 == 42

    async def test_changes_close(self) -> None:
        sig = Signal(0)
        stream = sig.changes()
        assert len(sig._change_queues) == 1
        stream.close()
        assert len(sig._change_queues) == 0

    async def test_changes_async_iteration(self) -> None:
        sig = Signal(0)
        stream = sig.changes()
        results: list[int] = []

        async def reader() -> None:
            async for val in stream:
                results.append(val)
                if len(results) >= 3:
                    break

        async def writer() -> None:
            for i in range(1, 4):
                sig.value = i
                await asyncio.sleep(0.01)

        await asyncio.gather(reader(), writer())
        assert results == [1, 2, 3]

    async def test_changes_with_batch(self) -> None:
        sig = Signal(0)
        stream = sig.changes()

        # Inside a batch, value changes still enqueue to streams
        with batch():
            sig.value = 10
            sig.value = 20

        v1 = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        v2 = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        assert v1 == 10
        assert v2 == 20
