"""Mapanare runtime package -- agent, signal, stream, and type primitives."""

from runtime.agent import (
    AgentBase,
    AgentGroup,
    AgentHandle,
    AgentMetrics,
    AgentRegistry,
    AgentState,
    Channel,
    RestartPolicy,
    SupervisionStrategy,
    global_registry,
)
from runtime.result import Err, Ok, Some, _EarlyReturn, unwrap_or_return
from runtime.signal import Signal, SignalChangeStream, batch
from runtime.stream import Stream, StreamKind

__all__ = [
    "AgentBase",
    "AgentGroup",
    "AgentHandle",
    "AgentMetrics",
    "AgentRegistry",
    "AgentState",
    "Channel",
    "Err",
    "Ok",
    "RestartPolicy",
    "Signal",
    "SignalChangeStream",
    "Some",
    "Stream",
    "StreamKind",
    "batch",
    "SupervisionStrategy",
    "_EarlyReturn",
    "global_registry",
    "unwrap_or_return",
]
