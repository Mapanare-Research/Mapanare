"""Tests for the Mapanare metrics module (mapanare/metrics.py).

Verifies:
  - Counter increment and collection
  - Histogram observation and collection
  - AgentMetricsRegistry collection
  - Prometheus exposition format
  - Metrics HTTP server
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from mapanare.metrics import (
    AgentMetricsRegistry,
    Counter,
    Histogram,
    get_metrics,
    start_metrics_server,
)

# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------


class TestCounter:
    def test_basic_increment(self) -> None:
        c = Counter("test_total", "A test counter")
        c.inc()
        c.inc(2.0)
        lines = c.collect()
        assert any("test_total 3" in line for line in lines)

    def test_labeled_counter(self) -> None:
        c = Counter("test_total", "A test counter", labels=["method"])
        c.inc(method="GET")
        c.inc(method="POST")
        c.inc(method="GET")
        lines = c.collect()
        text = "\n".join(lines)
        assert 'method="GET"' in text
        assert 'method="POST"' in text

    def test_collect_format(self) -> None:
        c = Counter("requests_total", "Total requests")
        c.inc()
        lines = c.collect()
        assert lines[0] == "# HELP requests_total Total requests"
        assert lines[1] == "# TYPE requests_total counter"


# ---------------------------------------------------------------------------
# Histogram
# ---------------------------------------------------------------------------


class TestHistogram:
    def test_basic_observe(self) -> None:
        h = Histogram("latency", "Latency", buckets=[0.01, 0.1, 1.0])
        h.observe(0.05)
        h.observe(0.5)
        h.observe(2.0)
        lines = h.collect()
        text = "\n".join(lines)
        assert "latency_bucket" in text
        assert "latency_sum" in text
        assert "latency_count" in text

    def test_labeled_histogram(self) -> None:
        h = Histogram("latency", "Latency", buckets=[0.1, 1.0], labels=["op"])
        h.observe(0.05, op="read")
        h.observe(0.5, op="write")
        lines = h.collect()
        text = "\n".join(lines)
        assert 'op="read"' in text
        assert 'op="write"' in text

    def test_collect_format(self) -> None:
        h = Histogram("duration", "Duration", buckets=[0.1])
        h.observe(0.05)
        lines = h.collect()
        assert lines[0] == "# HELP duration Duration"
        assert lines[1] == "# TYPE duration histogram"


# ---------------------------------------------------------------------------
# AgentMetricsRegistry
# ---------------------------------------------------------------------------


class TestAgentMetricsRegistry:
    def test_collect_all_empty(self) -> None:
        registry = AgentMetricsRegistry()
        output = registry.collect_all()
        assert "mapanare_agent_spawns_total" in output
        assert "mapanare_agent_messages_total" in output
        assert "mapanare_agent_errors_total" in output
        assert "mapanare_agent_stops_total" in output
        assert "mapanare_agent_handle_duration_seconds" in output

    def test_collect_after_recording(self) -> None:
        registry = AgentMetricsRegistry()
        registry.agent_spawns.inc(agent_type="Echo")
        registry.agent_messages.inc(agent_type="Echo")
        registry.agent_messages.inc(agent_type="Echo")
        registry.agent_latency.observe(0.001, agent_type="Echo")
        output = registry.collect_all()
        assert 'agent_type="Echo"' in output

    def test_global_registry(self) -> None:
        m = get_metrics()
        assert isinstance(m, AgentMetricsRegistry)


# ---------------------------------------------------------------------------
# Metrics HTTP server
# ---------------------------------------------------------------------------


class TestMetricsServer:
    def test_server_starts_and_serves(self) -> None:
        server = start_metrics_server(":0")  # Bind to random port
        port = server.server_address[1]
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=2)
            body = resp.read().decode("utf-8")
            assert "mapanare_agent_spawns_total" in body
            assert resp.status == 200
        finally:
            server.shutdown()

    def test_server_404_on_unknown_path(self) -> None:
        server = start_metrics_server(":0")
        port = server.server_address[1]
        try:
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/unknown", timeout=2)
            assert exc_info.value.code == 404
        finally:
            server.shutdown()
