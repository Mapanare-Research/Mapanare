"""Mapanare agent runtime -- base class, registry, groups, and supervision."""

from __future__ import annotations

import asyncio
import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from mapanare.metrics import get_metrics
from mapanare.tracing import get_tracer

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Agent States
# ---------------------------------------------------------------------------


class AgentState(enum.Enum):
    """Lifecycle states of an agent."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Restart / Supervision
# ---------------------------------------------------------------------------


class RestartPolicy(enum.Enum):
    """What to do when an agent's handler raises."""

    STOP = "stop"
    RESTART = "restart"


@dataclass
class SupervisionStrategy:
    """Configuration for agent failure recovery."""

    policy: RestartPolicy = RestartPolicy.STOP
    max_restarts: int = 0


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class AgentMetrics:
    """Runtime metrics for an agent."""

    messages_processed: int = 0
    total_latency_ms: float = 0.0
    restart_count: int = 0
    _agent: AgentBase | None = field(default=None, repr=False)

    @property
    def avg_latency_ms(self) -> float:
        if self.messages_processed == 0:
            return 0.0
        return self.total_latency_ms / self.messages_processed

    @property
    def queue_depth(self) -> int:
        if self._agent is None:
            return 0
        total = 0
        for ch in self._agent._inputs.values():
            total += ch.qsize()
        return total

    @property
    def input_pressure(self) -> float:
        """Fraction of input capacity used (0.0–1.0)."""
        if self._agent is None:
            return 0.0
        total_size = 0
        total_used = 0
        for ch in self._agent._inputs.values():
            total_size += ch._queue.maxsize
            total_used += ch.qsize()
        if total_size == 0:
            return 0.0
        return total_used / total_size

    def snapshot(self) -> dict[str, Any]:
        return {
            "messages_processed": self.messages_processed,
            "avg_latency_ms": self.avg_latency_ms,
            "queue_depth": self.queue_depth,
            "restart_count": self.restart_count,
        }


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------


class Channel(Generic[T]):
    """Typed async channel for agent communication."""

    def __init__(self, maxsize: int = 256) -> None:
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize=maxsize)
        self._closed = False

    async def send(self, value: T) -> None:
        """Send a value into the channel."""
        if self._closed:
            raise RuntimeError("Cannot send on a closed channel")
        await self._queue.put(value)

    async def receive(self) -> T:
        """Receive a value from the channel."""
        return await self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()

    @property
    def is_full(self) -> bool:
        return self._queue.full()

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True

    def qsize(self) -> int:
        return self._queue.qsize()


# ---------------------------------------------------------------------------
# AgentHandle
# ---------------------------------------------------------------------------


class AgentHandle:
    """Handle returned by spawning an agent, exposes input/output channels."""

    def __init__(self, agent: AgentBase, agent_id: str | None = None) -> None:
        self._agent = agent
        self.agent_id = agent_id or agent._id
        # Expose input/output channels as attributes
        for name, ch in agent._inputs.items():
            setattr(self, name, ch)
        for name, ch in agent._outputs.items():
            setattr(self, name, ch)

    async def stop(self) -> None:
        """Stop the agent."""
        await self._agent.stop()

    async def pause(self) -> None:
        """Pause the agent."""
        await self._agent.pause()

    async def resume(self) -> None:
        """Resume a paused agent."""
        await self._agent.resume()


# ---------------------------------------------------------------------------
# AgentBase
# ---------------------------------------------------------------------------


class AgentBase:
    """Base class for all Mapanare agents compiled to Python."""

    _inputs: dict[str, Channel[Any]]
    _outputs: dict[str, Channel[Any]]
    _task: asyncio.Task[None] | None
    _state: AgentState
    _supervision: SupervisionStrategy
    _metrics: AgentMetrics
    _id: str

    def __init__(self) -> None:
        self._inputs = {}
        self._outputs = {}
        self._task = None
        self._running = False
        self._state = AgentState.IDLE
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._supervision = SupervisionStrategy()
        self._id = uuid.uuid4().hex[:12]
        self._metrics = AgentMetrics(_agent=self)

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def metrics(self) -> AgentMetrics:
        return self._metrics

    def _register_input(self, name: str, maxsize: int = 256) -> Channel[Any]:
        ch: Channel[Any] = Channel(maxsize=maxsize)
        self._inputs[name] = ch
        return ch

    def _register_output(self, name: str, maxsize: int = 256) -> Channel[Any]:
        ch: Channel[Any] = Channel(maxsize=maxsize)
        self._outputs[name] = ch
        return ch

    async def _run(self) -> None:
        """Main agent loop — receives from first input, calls handle, sends to first output."""
        self._running = True
        self._state = AgentState.RUNNING
        await self.on_init()

        restart_count = 0

        while self._running:
            try:
                # Wait if paused
                await self._pause_event.wait()
                if not self._running:
                    break

                # Re-read channel names each iteration so channels registered
                # after spawn are picked up.
                input_names = list(self._inputs.keys())
                output_names = list(self._outputs.keys())

                if input_names:
                    try:
                        value = await asyncio.wait_for(
                            self._inputs[input_names[0]].receive(), timeout=0.05
                        )
                    except asyncio.TimeoutError:
                        continue

                    tracer = get_tracer()
                    with tracer.start_span(
                        "agent.handle",
                        attributes={
                            "agent.id": self._id,
                            "agent.type": type(self).__name__,
                        },
                    ) as handle_span:
                        t0 = time.monotonic()
                        result = await self.handle(value)
                        elapsed_ms = (time.monotonic() - t0) * 1000
                        self._metrics.messages_processed += 1
                        self._metrics.total_latency_ms += elapsed_ms
                        handle_span.set_attribute("agent.handle.latency_ms", elapsed_ms)
                        metrics = get_metrics()
                        metrics.agent_messages.inc(agent_type=type(self).__name__)
                        metrics.agent_latency.observe(
                            elapsed_ms / 1000, agent_type=type(self).__name__
                        )

                    if output_names and result is not None:
                        with tracer.start_span(
                            "agent.send",
                            attributes={
                                "agent.id": self._id,
                                "agent.channel": output_names[0],
                            },
                        ):
                            await self._outputs[output_names[0]].send(result)
                else:
                    await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                break
            except Exception:
                get_metrics().agent_errors.inc(agent_type=type(self).__name__)
                # Supervision
                if self._supervision.policy == RestartPolicy.RESTART:
                    restart_count += 1
                    self._metrics.restart_count = restart_count
                    if restart_count > self._supervision.max_restarts:
                        self._state = AgentState.FAILED
                        self._running = False
                        break
                    # Continue the loop (restart)
                    continue
                else:
                    self._state = AgentState.FAILED
                    self._running = False
                    break

        if self._state != AgentState.FAILED:
            self._state = AgentState.STOPPED
        await self.on_stop()

    async def handle(self, value: Any) -> Any:
        """Override in subclass — handles incoming messages."""
        return None

    async def on_init(self) -> None:
        """Lifecycle hook: called when agent starts."""

    async def on_pause(self) -> None:
        """Lifecycle hook: called when agent pauses."""

    async def on_resume(self) -> None:
        """Lifecycle hook: called when agent resumes."""

    async def on_stop(self) -> None:
        """Lifecycle hook: called when agent stops."""

    async def pause(self) -> None:
        """Pause the agent — it will stop processing until resumed."""
        if self._state == AgentState.RUNNING:
            tracer = get_tracer()
            with tracer.start_span("agent.pause", attributes={"agent.id": self._id}):
                self._state = AgentState.PAUSED
                self._pause_event.clear()
                await self.on_pause()

    async def resume(self) -> None:
        """Resume a paused agent."""
        if self._state == AgentState.PAUSED:
            tracer = get_tracer()
            with tracer.start_span("agent.resume", attributes={"agent.id": self._id}):
                self._state = AgentState.RUNNING
                await self.on_resume()
                self._pause_event.set()

    async def stop(self) -> None:
        tracer = get_tracer()
        with tracer.start_span("agent.stop", attributes={"agent.id": self._id}):
            get_metrics().agent_stops.inc(agent_type=type(self).__name__)
            self._running = False
            self._pause_event.set()  # Unblock if paused so _run can exit
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            # Ensure on_stop runs and state is set even if task was cancelled
            # before the _run cleanup path executed.
            if self._state not in (AgentState.STOPPED, AgentState.FAILED):
                self._state = AgentState.STOPPED
                await self.on_stop()

    @classmethod
    async def spawn(
        cls,
        *args: Any,
        supervision: SupervisionStrategy | None = None,
        **kwargs: Any,
    ) -> AgentHandle:
        """Create and start the agent, return a handle."""
        tracer = get_tracer()
        agent = cls(*args, **kwargs)
        if supervision is not None:
            agent._supervision = supervision

        with tracer.start_span(
            "agent.spawn",
            attributes={
                "agent.id": agent._id,
                "agent.type": cls.__name__,
                "agent.supervision.policy": agent._supervision.policy.value,
            },
        ):
            agent._task = asyncio.create_task(agent._run())
            get_metrics().agent_spawns.inc(agent_type=cls.__name__)

        return AgentHandle(agent)


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------


class AgentRegistry:
    """Track running agents by name."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentHandle] = {}

    def register(self, name: str, handle: AgentHandle) -> None:
        self._agents[name] = handle

    def get(self, name: str) -> AgentHandle | None:
        return self._agents.get(name)

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def list(self) -> list[str]:
        return list(self._agents.keys())

    async def stop_all(self) -> None:
        for handle in self._agents.values():
            await handle.stop()


global_registry = AgentRegistry()


# ---------------------------------------------------------------------------
# Agent Groups
# ---------------------------------------------------------------------------


class AgentGroup:
    """Spawn N instances of the same agent type."""

    def __init__(self, handles: list[AgentHandle]) -> None:
        self.handles = handles

    @property
    def size(self) -> int:
        return len(self.handles)

    @classmethod
    async def spawn(
        cls,
        agent_cls: type[AgentBase],
        count: int,
        *,
        supervision: SupervisionStrategy | None = None,
    ) -> AgentGroup:
        handles = []
        for _ in range(count):
            h = await agent_cls.spawn(supervision=supervision)
            handles.append(h)
        return cls(handles)

    async def stop_all(self) -> None:
        for h in self.handles:
            await h.stop()
