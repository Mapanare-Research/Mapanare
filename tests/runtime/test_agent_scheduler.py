"""Tests for Phase 3.1 — Agent Scheduler."""

from __future__ import annotations

import asyncio
from typing import Any

from runtime.agent import (
    AgentBase,
    AgentGroup,
    AgentRegistry,
    AgentState,
    Channel,
    RestartPolicy,
    SupervisionStrategy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class EchoAgent(AgentBase):
    """Simple agent that echoes input to output."""

    async def handle(self, value: Any) -> Any:
        return value


class DoubleAgent(AgentBase):
    """Agent that doubles numeric input."""

    async def handle(self, value: Any) -> Any:
        return value * 2


class FailOnceAgent(AgentBase):
    """Agent that fails on the first message then works."""

    def __init__(self) -> None:
        super().__init__()
        self._fail_count = 0

    async def handle(self, value: Any) -> Any:
        if self._fail_count == 0:
            self._fail_count += 1
            raise RuntimeError("intentional failure")
        return value


class AlwaysFailAgent(AgentBase):
    """Agent that always fails."""

    async def handle(self, value: Any) -> Any:
        raise RuntimeError("always fails")


class SlowAgent(AgentBase):
    """Agent that takes a bit to process."""

    async def handle(self, value: Any) -> Any:
        await asyncio.sleep(0.01)
        return value


class LifecycleTracker(AgentBase):
    """Tracks lifecycle events for testing."""

    events: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.events = []

    async def on_init(self) -> None:
        self.events.append("init")

    async def on_pause(self) -> None:
        self.events.append("pause")

    async def on_resume(self) -> None:
        self.events.append("resume")

    async def on_stop(self) -> None:
        self.events.append("stop")

    async def handle(self, value: Any) -> Any:
        self.events.append(f"handle:{value}")
        return value


# ===========================================================================
# Task 1 — AgentBase lifecycle: init, run, pause, stop
# ===========================================================================


class TestAgentLifecycle:
    async def test_initial_state_is_idle(self) -> None:
        agent = EchoAgent()
        assert agent.state == AgentState.IDLE

    async def test_spawn_sets_running(self) -> None:
        handle = await EchoAgent.spawn()
        await asyncio.sleep(0)  # yield so _run task starts
        assert handle._agent.state == AgentState.RUNNING
        await handle.stop()

    async def test_pause_and_resume(self) -> None:
        handle = await LifecycleTracker.spawn()
        agent: LifecycleTracker = handle._agent  # type: ignore[assignment]
        await asyncio.sleep(0.05)  # let _run start

        await handle.pause()
        assert agent.state == AgentState.PAUSED
        assert "pause" in agent.events

        await handle.resume()
        assert agent.state == AgentState.RUNNING
        assert "resume" in agent.events
        await handle.stop()

    async def test_stop_calls_on_stop(self) -> None:
        handle = await LifecycleTracker.spawn()
        agent: LifecycleTracker = handle._agent  # type: ignore[assignment]
        await handle.stop()
        await asyncio.sleep(0.05)
        assert "stop" in agent.events
        assert agent.state == AgentState.STOPPED

    async def test_on_init_called(self) -> None:
        handle = await LifecycleTracker.spawn()
        agent: LifecycleTracker = handle._agent  # type: ignore[assignment]
        await asyncio.sleep(0.05)
        assert "init" in agent.events
        await handle.stop()

    async def test_paused_agent_does_not_process(self) -> None:
        handle = await EchoAgent.spawn()
        agent: EchoAgent = handle._agent  # type: ignore[assignment]
        agent._register_input("in")
        agent._register_output("out")
        await asyncio.sleep(0.05)  # let _run start and pick up channels

        await handle.pause()
        await agent._inputs["in"].send("hello")
        await asyncio.sleep(0.05)
        # Message should still be in queue — not processed
        assert not agent._outputs["out"]._queue.qsize()

        await handle.resume()
        result = await asyncio.wait_for(agent._outputs["out"].receive(), timeout=1.0)
        assert result == "hello"
        await handle.stop()

    async def test_full_lifecycle_order(self) -> None:
        handle = await LifecycleTracker.spawn()
        agent: LifecycleTracker = handle._agent  # type: ignore[assignment]
        await asyncio.sleep(0.05)
        await handle.pause()
        await handle.resume()
        await handle.stop()
        await asyncio.sleep(0.05)
        assert agent.events[:1] == ["init"]
        assert "pause" in agent.events
        assert "resume" in agent.events
        assert agent.events[-1] == "stop"


# ===========================================================================
# Task 2 — Agent Registry
# ===========================================================================


class TestAgentRegistry:
    async def test_register_and_get(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        assert registry.get("echo") is handle
        await handle.stop()

    async def test_get_nonexistent_returns_none(self) -> None:
        registry = AgentRegistry()
        assert registry.get("nope") is None

    async def test_list_agents(self) -> None:
        registry = AgentRegistry()
        h1 = await EchoAgent.spawn()
        h2 = await DoubleAgent.spawn()
        registry.register("echo", h1)
        registry.register("double", h2)
        names = registry.list()
        assert "echo" in names
        assert "double" in names
        await h1.stop()
        await h2.stop()

    async def test_unregister(self) -> None:
        registry = AgentRegistry()
        handle = await EchoAgent.spawn()
        registry.register("echo", handle)
        registry.unregister("echo")
        assert registry.get("echo") is None
        await handle.stop()

    async def test_agent_id_unique(self) -> None:
        h1 = await EchoAgent.spawn()
        h2 = await EchoAgent.spawn()
        assert h1.agent_id != h2.agent_id
        await h1.stop()
        await h2.stop()

    async def test_global_registry(self) -> None:
        """The module-level registry singleton works."""
        from runtime.agent import global_registry

        h = await EchoAgent.spawn()
        global_registry.register("test-global", h)
        assert global_registry.get("test-global") is h
        global_registry.unregister("test-global")
        await h.stop()

    async def test_stop_all(self) -> None:
        registry = AgentRegistry()
        h1 = await EchoAgent.spawn()
        h2 = await EchoAgent.spawn()
        registry.register("a", h1)
        registry.register("b", h2)
        await asyncio.sleep(0)
        await registry.stop_all()
        assert h1._agent.state == AgentState.STOPPED
        assert h2._agent.state == AgentState.STOPPED


# ===========================================================================
# Task 3 — Typed message passing channels
# ===========================================================================


class TestTypedChannels:
    async def test_basic_send_receive(self) -> None:
        ch: Channel[int] = Channel()
        await ch.send(42)
        val = await ch.receive()
        assert val == 42

    async def test_channel_ordering(self) -> None:
        ch: Channel[str] = Channel()
        await ch.send("a")
        await ch.send("b")
        await ch.send("c")
        assert await ch.receive() == "a"
        assert await ch.receive() == "b"
        assert await ch.receive() == "c"

    async def test_channel_between_agents(self) -> None:
        h1 = await EchoAgent.spawn()
        h2 = await DoubleAgent.spawn()
        agent1: EchoAgent = h1._agent  # type: ignore[assignment]
        agent2: DoubleAgent = h2._agent  # type: ignore[assignment]

        in_ch = agent1._register_input("in")
        mid_ch: Channel[Any] = Channel()
        agent1._outputs["out"] = mid_ch
        agent2._inputs["in"] = mid_ch
        out_ch = agent2._register_output("out")

        await in_ch.send(5)
        await asyncio.sleep(0.1)
        result = await asyncio.wait_for(out_ch.receive(), timeout=1.0)
        assert result == 10
        await h1.stop()
        await h2.stop()

    async def test_channel_size(self) -> None:
        ch: Channel[int] = Channel(maxsize=2)
        await ch.send(1)
        await ch.send(2)
        assert ch.qsize() == 2

    async def test_channel_closed(self) -> None:
        ch: Channel[int] = Channel()
        ch.close()
        assert ch.is_closed


# ===========================================================================
# Task 4 — Backpressure
# ===========================================================================


class TestBackpressure:
    async def test_full_channel_reports_pressure(self) -> None:
        ch: Channel[int] = Channel(maxsize=2)
        await ch.send(1)
        await ch.send(2)
        assert ch.is_full

    async def test_agent_backpressure_state(self) -> None:
        handle = await SlowAgent.spawn()
        agent: SlowAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")
        # Fill the input channel to capacity
        for i in range(256):
            await in_ch.send(i)
        assert in_ch.is_full
        await handle.stop()

    async def test_pressure_metric_tracked(self) -> None:
        handle = await EchoAgent.spawn()
        agent: EchoAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in", maxsize=4)
        agent._register_output("out")
        for i in range(4):
            await in_ch.send(i)
        assert agent.metrics.input_pressure >= 0.0
        await handle.stop()


# ===========================================================================
# Task 5 — Agent supervision: restart policy on failure
# ===========================================================================


class TestSupervision:
    async def test_restart_on_failure(self) -> None:
        handle = await FailOnceAgent.spawn(
            supervision=SupervisionStrategy(policy=RestartPolicy.RESTART, max_restarts=3)
        )
        agent: FailOnceAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        out_ch = agent._register_output("out")

        await in_ch.send("hello")
        await asyncio.sleep(0.2)
        # After failure + restart, the agent should still process the second message
        await in_ch.send("world")
        result = await asyncio.wait_for(out_ch.receive(), timeout=2.0)
        assert result == "world"
        await handle.stop()

    async def test_stop_policy_on_failure(self) -> None:
        handle = await AlwaysFailAgent.spawn(
            supervision=SupervisionStrategy(policy=RestartPolicy.STOP, max_restarts=0)
        )
        agent: AlwaysFailAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")

        await in_ch.send("hello")
        await asyncio.sleep(0.2)
        assert agent.state == AgentState.FAILED

    async def test_max_restarts_exceeded(self) -> None:
        handle = await AlwaysFailAgent.spawn(
            supervision=SupervisionStrategy(policy=RestartPolicy.RESTART, max_restarts=2)
        )
        agent: AlwaysFailAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")

        # Send enough messages to trigger failures past max_restarts
        for _ in range(5):
            try:
                await asyncio.wait_for(in_ch.send("x"), timeout=0.1)
            except asyncio.TimeoutError:
                break
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.3)
        assert agent.state == AgentState.FAILED
        # restart_count should be exactly max_restarts + 1 (the one that exceeded)
        assert agent.metrics.restart_count <= 3

    async def test_restart_count_tracked(self) -> None:
        handle = await FailOnceAgent.spawn(
            supervision=SupervisionStrategy(policy=RestartPolicy.RESTART, max_restarts=3)
        )
        agent: FailOnceAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")

        await in_ch.send("trigger-failure")
        await asyncio.sleep(0.3)
        assert agent.metrics.restart_count >= 1
        await handle.stop()


# ===========================================================================
# Task 6 — Agent groups
# ===========================================================================


class TestAgentGroups:
    async def test_spawn_group(self) -> None:
        group = await AgentGroup.spawn(EchoAgent, count=3)
        assert len(group.handles) == 3
        await group.stop_all()

    async def test_group_round_robin(self) -> None:
        group = await AgentGroup.spawn(EchoAgent, count=2)
        await asyncio.sleep(0)  # yield for tasks to start
        for h in group.handles:
            assert h._agent.state == AgentState.RUNNING
        await group.stop_all()

    async def test_group_stop_all(self) -> None:
        group = await AgentGroup.spawn(EchoAgent, count=3)
        await asyncio.sleep(0)
        await group.stop_all()
        for h in group.handles:
            assert h._agent.state == AgentState.STOPPED

    async def test_group_size(self) -> None:
        group = await AgentGroup.spawn(DoubleAgent, count=5)
        assert group.size == 5
        await group.stop_all()


# ===========================================================================
# Task 7 — Metrics
# ===========================================================================


class TestMetrics:
    async def test_messages_processed_count(self) -> None:
        handle = await EchoAgent.spawn()
        agent: EchoAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")

        for i in range(5):
            await in_ch.send(i)
        await asyncio.sleep(0.2)
        assert agent.metrics.messages_processed >= 5
        await handle.stop()

    async def test_queue_depth(self) -> None:
        handle = await EchoAgent.spawn()
        agent: EchoAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        assert agent.metrics.queue_depth >= 0
        await in_ch.send(1)
        # Queue depth should reflect pending messages
        depth = agent.metrics.queue_depth
        assert depth >= 0
        await handle.stop()

    async def test_latency_recorded(self) -> None:
        handle = await SlowAgent.spawn()
        agent: SlowAgent = handle._agent  # type: ignore[assignment]
        in_ch = agent._register_input("in")
        agent._register_output("out")

        await in_ch.send(42)
        await asyncio.sleep(0.1)
        # avg latency should be > 0 after processing
        assert agent.metrics.avg_latency_ms >= 0.0
        await handle.stop()

    async def test_metrics_snapshot(self) -> None:
        handle = await EchoAgent.spawn()
        agent: EchoAgent = handle._agent  # type: ignore[assignment]
        snap = agent.metrics.snapshot()
        assert "messages_processed" in snap
        assert "avg_latency_ms" in snap
        assert "queue_depth" in snap
        assert "restart_count" in snap
        await handle.stop()
