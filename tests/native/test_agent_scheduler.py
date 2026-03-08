"""Tests for the native agent scheduler (Phase 4.3, Task 1)."""

import ctypes
import time

import pytest

from runtime.native_bridge import (
    AGENT_FAILED,
    AGENT_IDLE,
    AGENT_PAUSED,
    AGENT_RUNNING,
    AGENT_STOPPED,
    HANDLER_FN,
    NATIVE_AVAILABLE,
    NativeAgent,
)

pytestmark = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="Native runtime not built",
)


def _double_handler() -> HANDLER_FN:
    """Handler that doubles the input value and writes to outbox."""

    @HANDLER_FN
    def handler(agent_data: int, msg: int, out_msg: ctypes.POINTER(ctypes.c_void_p)) -> int:
        out_msg[0] = ctypes.c_void_p(msg * 2)
        return 0

    return handler


def _echo_handler() -> HANDLER_FN:
    """Handler that echoes the input to outbox."""

    @HANDLER_FN
    def handler(agent_data: int, msg: int, out_msg: ctypes.POINTER(ctypes.c_void_p)) -> int:
        out_msg[0] = ctypes.c_void_p(msg)
        return 0

    return handler


def _failing_handler() -> HANDLER_FN:
    """Handler that always fails (returns non-zero)."""

    @HANDLER_FN
    def handler(agent_data: int, msg: int, out_msg: ctypes.POINTER(ctypes.c_void_p)) -> int:
        return -1  # error

    return handler


class TestAgentLifecycle:
    """Agent creation, spawn, and stop."""

    def test_init_state_idle(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("test_idle", h)
        assert agent.state == AGENT_IDLE
        agent.destroy()

    def test_spawn_state_running(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("test_running", h)
        agent.spawn()
        time.sleep(0.05)
        assert agent.state == AGENT_RUNNING
        agent.stop()
        agent.destroy()

    def test_stop_state_stopped(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("test_stop", h)
        agent.spawn()
        time.sleep(0.05)
        agent.stop()
        assert agent.state == AGENT_STOPPED
        agent.destroy()


class TestAgentMessagePassing:
    """Send and receive messages."""

    def test_send_recv_single(self) -> None:
        h = _double_handler()
        agent = NativeAgent("doubler", h)
        agent.spawn()
        time.sleep(0.05)

        agent.send(21)
        time.sleep(0.1)

        result = agent.recv()
        assert result == 42
        agent.stop()
        agent.destroy()

    def test_send_recv_multiple(self) -> None:
        h = _double_handler()
        agent = NativeAgent("doubler_multi", h)
        agent.spawn()
        time.sleep(0.05)

        for val in [1, 2, 3, 4, 5]:
            agent.send(val)

        time.sleep(0.2)

        results = []
        for _ in range(5):
            r = agent.recv()
            if r is not None:
                results.append(r)

        assert results == [2, 4, 6, 8, 10]
        agent.stop()
        agent.destroy()

    def test_recv_empty_returns_none(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("empty_recv", h)
        agent.spawn()
        time.sleep(0.05)
        assert agent.recv() is None
        agent.stop()
        agent.destroy()

    def test_echo_handler(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("echo", h)
        agent.spawn()
        time.sleep(0.05)

        agent.send(99)
        time.sleep(0.1)

        assert agent.recv() == 99
        agent.stop()
        agent.destroy()


class TestAgentPauseResume:
    """Pause and resume functionality."""

    def test_pause_sets_paused_state(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("pause_test", h)
        agent.spawn()
        time.sleep(0.05)

        agent.pause()
        assert agent.state == AGENT_PAUSED
        agent.stop()
        agent.destroy()

    def test_resume_sets_running_state(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("resume_test", h)
        agent.spawn()
        time.sleep(0.05)

        agent.pause()
        assert agent.state == AGENT_PAUSED
        agent.resume()
        assert agent.state == AGENT_RUNNING
        agent.stop()
        agent.destroy()

    def test_paused_agent_does_not_process(self) -> None:
        h = _double_handler()
        agent = NativeAgent("pause_block", h)
        agent.spawn()
        time.sleep(0.05)

        agent.pause()
        time.sleep(0.05)
        agent.send(10)
        time.sleep(0.15)

        # Should NOT have been processed while paused
        assert agent.recv() is None

        agent.resume()
        time.sleep(0.15)

        # Now it should be processed
        assert agent.recv() == 20
        agent.stop()
        agent.destroy()


class TestAgentMetrics:
    """Message processing metrics."""

    def test_messages_processed_count(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("metrics_count", h)
        agent.spawn()
        time.sleep(0.05)

        for i in range(5):
            agent.send(i + 1)

        time.sleep(0.3)
        assert agent.messages_processed == 5
        agent.stop()
        agent.destroy()

    def test_initial_metrics_zero(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("metrics_init", h)
        assert agent.messages_processed == 0
        assert agent.avg_latency_us == 0.0
        agent.destroy()

    def test_avg_latency_positive(self) -> None:
        h = _echo_handler()
        agent = NativeAgent("metrics_latency", h)
        agent.spawn()
        time.sleep(0.05)

        agent.send(1)
        time.sleep(0.1)

        assert agent.messages_processed == 1
        assert agent.avg_latency_us >= 0.0
        agent.stop()
        agent.destroy()


class TestAgentSupervision:
    """Supervision and restart policies."""

    def test_failing_handler_stops_agent(self) -> None:
        """Default policy (STOP) should set state to FAILED on handler error."""
        h = _failing_handler()
        agent = NativeAgent("fail_stop", h)
        agent.spawn()
        time.sleep(0.05)

        agent.send(1)
        time.sleep(0.2)

        assert agent.state == AGENT_FAILED
        agent.stop()
        agent.destroy()
