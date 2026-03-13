"""Tests for the Mapanare tracing module (mapanare/tracing.py).

Verifies:
  - Span creation and lifecycle
  - Parent-child relationships
  - Trace context (thread-local span stack)
  - Console exporter output
  - OTLP payload format
  - Global tracer enable/disable
  - No-op behavior when disabled
  - Agent instrumentation emits spans
"""

from __future__ import annotations

import asyncio

import pytest

from mapanare.tracing import (
    ConsoleExporter,
    OTLPExporter,
    Span,
    SpanStatus,
    Tracer,
    _current_span,
    _pop_span,
    _push_span,
    disable_tracing,
    enable_tracing,
    get_tracer,
)

# ---------------------------------------------------------------------------
# Span basics
# ---------------------------------------------------------------------------


class TestSpan:
    def test_span_creation(self) -> None:
        span = Span(name="test.op", trace_id="abc123", span_id="def456")
        assert span.name == "test.op"
        assert span.trace_id == "abc123"
        assert span.span_id == "def456"
        assert span.parent_span_id is None
        assert span.status == SpanStatus.UNSET

    def test_span_duration(self) -> None:
        span = Span(
            name="test.op",
            trace_id="abc",
            span_id="def",
            start_time_ns=1_000_000_000,
            end_time_ns=1_050_000_000,
        )
        assert span.duration_ns == 50_000_000
        assert span.duration_ms == 50.0

    def test_span_duration_zero_when_not_ended(self) -> None:
        span = Span(name="test.op", trace_id="abc", span_id="def")
        assert span.duration_ns == 0

    def test_set_attribute(self) -> None:
        span = Span(name="test.op", trace_id="abc", span_id="def")
        span.set_attribute("key", "value")
        assert span.attributes["key"] == "value"

    def test_add_event(self) -> None:
        span = Span(name="test.op", trace_id="abc", span_id="def")
        span.add_event("checkpoint", {"step": "1"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "checkpoint"
        assert span.events[0]["attributes"] == {"step": "1"}

    def test_set_status(self) -> None:
        span = Span(name="test.op", trace_id="abc", span_id="def")
        span.set_status(SpanStatus.ERROR, "something broke")
        assert span.status == SpanStatus.ERROR
        assert span.attributes["status.description"] == "something broke"

    def test_to_dict(self) -> None:
        span = Span(
            name="test.op",
            trace_id="abc",
            span_id="def",
            start_time_ns=100,
            end_time_ns=200,
        )
        span.set_status(SpanStatus.OK)
        d = span.to_dict()
        assert d["name"] == "test.op"
        assert d["trace_id"] == "abc"
        assert d["status"] == "ok"
        assert d["duration_ms"] == pytest.approx(0.0001)


# ---------------------------------------------------------------------------
# Trace context (thread-local)
# ---------------------------------------------------------------------------


class TestTraceContext:
    def test_push_pop_span(self) -> None:
        span = Span(name="test", trace_id="t1", span_id="s1")
        _push_span(span)
        assert _current_span() is span
        popped = _pop_span()
        assert popped is span
        assert _current_span() is None

    def test_nested_spans(self) -> None:
        parent = Span(name="parent", trace_id="t1", span_id="p1")
        child = Span(name="child", trace_id="t1", span_id="c1")
        _push_span(parent)
        _push_span(child)
        assert _current_span() is child
        _pop_span()
        assert _current_span() is parent
        _pop_span()


# ---------------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------------


class TestTracer:
    def test_disabled_by_default(self) -> None:
        tracer = Tracer()
        assert not tracer.enabled
        assert tracer.get_spans() == []

    def test_enable_disable(self) -> None:
        tracer = Tracer()
        tracer.enable()
        assert tracer.enabled
        tracer.disable()
        assert not tracer.enabled

    def test_start_span_when_disabled(self) -> None:
        tracer = Tracer()
        with tracer.start_span("noop") as span:
            span.set_attribute("key", "val")
        # No spans recorded
        assert tracer.get_spans() == []

    def test_start_span_when_enabled(self) -> None:
        tracer = Tracer()
        tracer.enable()
        # Temporarily replace global tracer
        import mapanare.tracing as tracing_mod

        old = tracing_mod._global_tracer
        tracing_mod._global_tracer = tracer
        try:
            with tracer.start_span("test.op", attributes={"k": "v"}) as span:
                assert span.name == "test.op"
                assert span.trace_id  # non-empty
                assert span.span_id  # non-empty
                assert span.attributes["k"] == "v"

            spans = tracer.get_spans()
            assert len(spans) == 1
            assert spans[0].name == "test.op"
            assert spans[0].status == SpanStatus.OK
        finally:
            tracing_mod._global_tracer = old

    def test_parent_child_spans(self) -> None:
        tracer = Tracer()
        tracer.enable()
        import mapanare.tracing as tracing_mod

        old = tracing_mod._global_tracer
        tracing_mod._global_tracer = tracer
        try:
            with tracer.start_span("parent") as parent:
                with tracer.start_span("child") as child:
                    assert child.parent_span_id == parent.span_id
                    assert child.trace_id == parent.trace_id

            spans = tracer.get_spans()
            assert len(spans) == 2
        finally:
            tracing_mod._global_tracer = old

    def test_span_error_on_exception(self) -> None:
        tracer = Tracer()
        tracer.enable()
        import mapanare.tracing as tracing_mod

        old = tracing_mod._global_tracer
        tracing_mod._global_tracer = tracer
        try:
            with pytest.raises(ValueError):
                with tracer.start_span("failing"):
                    raise ValueError("boom")
            spans = tracer.get_spans()
            assert len(spans) == 1
            assert spans[0].status == SpanStatus.ERROR
        finally:
            tracing_mod._global_tracer = old

    def test_clear_spans(self) -> None:
        tracer = Tracer()
        tracer.enable()
        import mapanare.tracing as tracing_mod

        old = tracing_mod._global_tracer
        tracing_mod._global_tracer = tracer
        try:
            with tracer.start_span("a"):
                pass
            assert len(tracer.get_spans()) == 1
            tracer.clear_spans()
            assert len(tracer.get_spans()) == 0
        finally:
            tracing_mod._global_tracer = old


# ---------------------------------------------------------------------------
# Console exporter
# ---------------------------------------------------------------------------


class TestConsoleExporter:
    def test_export_prints_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        exporter = ConsoleExporter()
        span = Span(
            name="test.op",
            trace_id="abc",
            span_id="def",
            start_time_ns=1_000_000_000,
            end_time_ns=1_010_000_000,
        )
        span.set_status(SpanStatus.OK)
        exporter.export([span])
        captured = capsys.readouterr()
        assert "[trace] test.op" in captured.err
        assert "10.00ms" in captured.err
        assert "status=ok" in captured.err


# ---------------------------------------------------------------------------
# OTLP exporter payload format
# ---------------------------------------------------------------------------


class TestOTLPExporter:
    def test_payload_format(self) -> None:
        exporter = OTLPExporter(endpoint="http://localhost:4318")
        span = Span(
            name="agent.spawn",
            trace_id="aaa",
            span_id="bbb",
            parent_span_id="ccc",
            start_time_ns=100,
            end_time_ns=200,
        )
        span.set_status(SpanStatus.OK)
        span.set_attribute("agent.id", "x123")

        payload = exporter._build_otlp_payload([span])
        assert "resourceSpans" in payload
        resource_spans = payload["resourceSpans"]
        assert len(resource_spans) == 1
        scope_spans = resource_spans[0]["scopeSpans"]
        assert len(scope_spans) == 1
        otlp_spans = scope_spans[0]["spans"]
        assert len(otlp_spans) == 1
        otlp_span = otlp_spans[0]
        assert otlp_span["name"] == "agent.spawn"
        assert otlp_span["traceId"] == "aaa"
        assert otlp_span["spanId"] == "bbb"
        assert otlp_span["parentSpanId"] == "ccc"


# ---------------------------------------------------------------------------
# Global tracer API
# ---------------------------------------------------------------------------


class TestGlobalTracer:
    def test_get_tracer_returns_singleton(self) -> None:
        t1 = get_tracer()
        t2 = get_tracer()
        assert t1 is t2

    def test_enable_disable_tracing(self) -> None:
        tracer = get_tracer()
        was_enabled = tracer.enabled
        try:
            enable_tracing(exporter="none")
            assert tracer.enabled
            disable_tracing()
            assert not tracer.enabled
        finally:
            if was_enabled:
                tracer.enable()
            else:
                tracer.disable()
            tracer.clear_spans()


# ---------------------------------------------------------------------------
# Agent instrumentation emits spans
# ---------------------------------------------------------------------------


class TestAgentTracing:
    @pytest.mark.asyncio
    async def test_spawn_emits_span(self) -> None:
        """Verify that spawning an agent creates an agent.spawn span."""
        import mapanare.tracing as tracing_mod
        from runtime.agent import AgentBase

        old = tracing_mod._global_tracer
        test_tracer = Tracer()
        test_tracer.enable()
        tracing_mod._global_tracer = test_tracer
        try:
            handle = await AgentBase.spawn()
            await handle.stop()

            spans = test_tracer.get_spans()
            span_names = [s.name for s in spans]
            assert "agent.spawn" in span_names
            assert "agent.stop" in span_names
        finally:
            tracing_mod._global_tracer = old

    @pytest.mark.asyncio
    async def test_handle_emits_span(self) -> None:
        """Verify that message handling creates an agent.handle span."""
        import mapanare.tracing as tracing_mod
        from runtime.agent import AgentBase

        class EchoAgent(AgentBase):
            async def handle(self, value: object) -> object:
                return value

        old = tracing_mod._global_tracer
        test_tracer = Tracer()
        test_tracer.enable()
        tracing_mod._global_tracer = test_tracer
        try:
            handle = await EchoAgent.spawn()
            # Register an input channel so the agent processes messages
            ch = handle._agent._register_input("inbox")
            await ch.send("hello")

            # Wait briefly for the agent to process
            await asyncio.sleep(0.2)
            await handle.stop()

            spans = test_tracer.get_spans()
            span_names = [s.name for s in spans]
            assert "agent.handle" in span_names
        finally:
            tracing_mod._global_tracer = old
