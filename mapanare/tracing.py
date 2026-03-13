"""Mapanare tracing -- OpenTelemetry-compatible span management for agent operations.

Provides a lightweight tracing API that works standalone (in-memory span collection)
and optionally exports via OTLP when opentelemetry-sdk is installed.

Trace points:
  - agent.spawn: agent lifecycle start
  - agent.send: message sent to agent
  - agent.receive: message received by agent
  - agent.handle: message processing (child of receive)
  - agent.stop: agent lifecycle end
  - agent.pause / agent.resume: state transitions
"""

from __future__ import annotations

import enum
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Span status
# ---------------------------------------------------------------------------


class SpanStatus(enum.Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


# ---------------------------------------------------------------------------
# Span — a single trace span
# ---------------------------------------------------------------------------


@dataclass
class Span:
    """A single trace span representing an operation."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time_ns: int = 0
    end_time_ns: int = 0
    status: SpanStatus = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ns(self) -> int:
        if self.end_time_ns and self.start_time_ns:
            return self.end_time_ns - self.start_time_ns
        return 0

    @property
    def duration_ms(self) -> float:
        return self.duration_ns / 1_000_000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp_ns": time.time_ns(),
                "attributes": attributes or {},
            }
        )

    def set_status(self, status: SpanStatus, description: str = "") -> None:
        self.status = status
        if description:
            self.attributes["status.description"] = description

    def end(self) -> None:
        if self.end_time_ns == 0:
            self.end_time_ns = time.time_ns()
        if self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK
        _global_tracer.record_span(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time_ns": self.start_time_ns,
            "end_time_ns": self.end_time_ns,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
        }


# ---------------------------------------------------------------------------
# Trace context — thread-local span stack
# ---------------------------------------------------------------------------


_trace_context = threading.local()


def _current_span() -> Span | None:
    stack: list[Span] = getattr(_trace_context, "span_stack", [])
    return stack[-1] if stack else None


def _push_span(span: Span) -> None:
    if not hasattr(_trace_context, "span_stack"):
        _trace_context.span_stack = []
    _trace_context.span_stack.append(span)


def _pop_span() -> Span | None:
    stack: list[Span] = getattr(_trace_context, "span_stack", [])
    return stack.pop() if stack else None


# ---------------------------------------------------------------------------
# SpanContext — context manager for spans
# ---------------------------------------------------------------------------


class SpanContext:
    """Context manager that creates and manages a span."""

    def __init__(self, span: Span) -> None:
        self.span = span

    def __enter__(self) -> Span:
        _push_span(self.span)
        return self.span

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        _pop_span()
        if exc_type is not None:
            self.span.set_status(SpanStatus.ERROR, str(exc_val))
        self.span.end()


# ---------------------------------------------------------------------------
# Tracer — creates spans and collects them
# ---------------------------------------------------------------------------


class Tracer:
    """Creates and collects trace spans.

    When tracing is disabled (the default), all operations are no-ops.
    When enabled, spans are collected in memory and optionally exported via OTLP.
    """

    def __init__(self) -> None:
        self._enabled = False
        self._spans: list[Span] = []
        self._lock = threading.Lock()
        self._exporter: SpanExporter | None = None
        self._service_name = "mapanare"

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self, service_name: str = "mapanare") -> None:
        self._enabled = True
        self._service_name = service_name

    def disable(self) -> None:
        self._enabled = False

    def set_exporter(self, exporter: SpanExporter) -> None:
        self._exporter = exporter

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        parent: Span | None = None,
    ) -> SpanContext:
        if not self._enabled:
            # Return a no-op span context
            noop = Span(name=name, trace_id="", span_id="")
            return _NoOpSpanContext(noop)

        current = parent or _current_span()
        trace_id = current.trace_id if current else uuid.uuid4().hex
        parent_id = current.span_id if current else None

        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_id,
            start_time_ns=time.time_ns(),
            attributes=attributes or {},
        )
        span.set_attribute("service.name", self._service_name)
        return SpanContext(span)

    def record_span(self, span: Span) -> None:
        if not self._enabled:
            return
        with self._lock:
            self._spans.append(span)
        if self._exporter is not None:
            self._exporter.export([span])

    def get_spans(self) -> list[Span]:
        with self._lock:
            return list(self._spans)

    def clear_spans(self) -> None:
        with self._lock:
            self._spans.clear()

    def flush(self) -> None:
        if self._exporter is not None:
            with self._lock:
                spans = list(self._spans)
            if spans:
                self._exporter.export(spans)


class _NoOpSpanContext(SpanContext):
    """No-op span context when tracing is disabled."""

    def __enter__(self) -> Span:
        return self.span

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Span exporters
# ---------------------------------------------------------------------------


class SpanExporter:
    """Base class for span exporters."""

    def export(self, spans: list[Span]) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        pass


class ConsoleExporter(SpanExporter):
    """Exports spans to stderr for debugging."""

    def export(self, spans: list[Span]) -> None:
        import sys

        for span in spans:
            dur = f"{span.duration_ms:.2f}ms" if span.duration_ms else "?"
            parent = f" parent={span.parent_span_id}" if span.parent_span_id else ""
            attrs = ""
            filtered = {
                k: v
                for k, v in span.attributes.items()
                if k not in ("service.name", "status.description")
            }
            if filtered:
                attrs = " " + " ".join(f"{k}={v}" for k, v in filtered.items())
            print(
                f"[trace] {span.name} {dur} status={span.status.value}{parent}{attrs}",
                file=sys.stderr,
            )


class OTLPExporter(SpanExporter):
    """Exports spans via OTLP/HTTP (JSON).

    Sends spans to an OTLP-compatible collector (Jaeger, Grafana Tempo, etc.).
    Falls back to no-op if the endpoint is unreachable.
    """

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
        )
        self._traces_url = f"{self._endpoint}/v1/traces"

    def export(self, spans: list[Span]) -> None:
        import json
        import urllib.error
        import urllib.request

        resource_spans = self._build_otlp_payload(spans)
        payload = json.dumps(resource_spans).encode("utf-8")

        req = urllib.request.Request(
            self._traces_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                pass
        except (urllib.error.URLError, OSError):
            pass  # Silently skip if collector is unreachable

    def _build_otlp_payload(self, spans: list[Span]) -> dict[str, Any]:
        service_name = "mapanare"
        if spans:
            service_name = spans[0].attributes.get("service.name", "mapanare")

        otlp_spans = []
        for span in spans:
            otlp_attrs = [
                {"key": k, "value": {"stringValue": str(v)}} for k, v in span.attributes.items()
            ]
            otlp_events = [
                {
                    "name": ev["name"],
                    "timeUnixNano": str(ev["timestamp_ns"]),
                    "attributes": [
                        {"key": k, "value": {"stringValue": str(v)}}
                        for k, v in ev.get("attributes", {}).items()
                    ],
                }
                for ev in span.events
            ]
            otlp_span: dict[str, Any] = {
                "traceId": span.trace_id,
                "spanId": span.span_id,
                "name": span.name,
                "kind": 1,  # SPAN_KIND_INTERNAL
                "startTimeUnixNano": str(span.start_time_ns),
                "endTimeUnixNano": str(span.end_time_ns),
                "attributes": otlp_attrs,
                "events": otlp_events,
                "status": {"code": 1 if span.status == SpanStatus.OK else 2},
            }
            if span.parent_span_id:
                otlp_span["parentSpanId"] = span.parent_span_id
            otlp_spans.append(otlp_span)

        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": service_name}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "mapanare.tracing", "version": "0.7.0"},
                            "spans": otlp_spans,
                        }
                    ],
                }
            ]
        }


# ---------------------------------------------------------------------------
# Global tracer instance
# ---------------------------------------------------------------------------

_global_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    return _global_tracer


def enable_tracing(
    service_name: str = "mapanare",
    exporter: str = "console",
    otlp_endpoint: str | None = None,
) -> None:
    """Enable tracing with the specified exporter.

    Args:
        service_name: Service name for trace identification.
        exporter: Exporter type: "console", "otlp", or "none".
        otlp_endpoint: OTLP collector endpoint (default: http://localhost:4318).
    """
    _global_tracer.enable(service_name)

    if exporter == "console":
        _global_tracer.set_exporter(ConsoleExporter())
    elif exporter == "otlp":
        _global_tracer.set_exporter(OTLPExporter(endpoint=otlp_endpoint))
    # "none" = in-memory only, no exporter


def disable_tracing() -> None:
    """Disable tracing."""
    _global_tracer.disable()
