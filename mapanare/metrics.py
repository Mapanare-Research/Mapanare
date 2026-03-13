"""Mapanare metrics -- Prometheus-compatible metrics for agent operations.

Provides counters and histograms for agent lifecycle events, served via
a lightweight HTTP endpoint in Prometheus exposition format.

No external dependencies -- uses only the Python stdlib.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ---------------------------------------------------------------------------
# Metric types
# ---------------------------------------------------------------------------


class Counter:
    """A monotonically increasing counter."""

    def __init__(self, name: str, help_text: str, labels: list[str] | None = None) -> None:
        self.name = name
        self.help_text = help_text
        self._labels = labels or []
        self._values: dict[tuple[str, ...], float] = {}
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, **label_values: str) -> None:
        key = tuple(label_values.get(lbl, "") for lbl in self._labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def collect(self) -> list[str]:
        lines: list[str] = []
        lines.append(f"# HELP {self.name} {self.help_text}")
        lines.append(f"# TYPE {self.name} counter")
        with self._lock:
            if not self._values:
                lines.append(f"{self.name} 0")
            for key, val in self._values.items():
                if self._labels:
                    label_str = ",".join(f'{lbl}="{v}"' for lbl, v in zip(self._labels, key))
                    lines.append(f"{self.name}{{{label_str}}} {val}")
                else:
                    lines.append(f"{self.name} {val}")
        return lines


class Histogram:
    """A histogram with configurable buckets."""

    def __init__(
        self,
        name: str,
        help_text: str,
        buckets: list[float] | None = None,
        labels: list[str] | None = None,
    ) -> None:
        self.name = name
        self.help_text = help_text
        self._labels = labels or []
        self._buckets = buckets or [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 5.0]
        # key -> (bucket_counts, sum, count)
        self._data: dict[tuple[str, ...], tuple[list[int], float, int]] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, **label_values: str) -> None:
        key = tuple(label_values.get(lbl, "") for lbl in self._labels)
        with self._lock:
            if key not in self._data:
                self._data[key] = ([0] * len(self._buckets), 0.0, 0)
            buckets, total, count = self._data[key]
            for i, bound in enumerate(self._buckets):
                if value <= bound:
                    buckets[i] += 1
            self._data[key] = (buckets, total + value, count + 1)

    def collect(self) -> list[str]:
        lines: list[str] = []
        lines.append(f"# HELP {self.name} {self.help_text}")
        lines.append(f"# TYPE {self.name} histogram")
        with self._lock:
            for key, (buckets, total, count) in self._data.items():
                label_prefix = ""
                if self._labels:
                    label_prefix = ",".join(f'{lbl}="{v}"' for lbl, v in zip(self._labels, key))
                cumulative = 0
                for i, bound in enumerate(self._buckets):
                    cumulative += buckets[i]
                    le_label = f'le="{bound}"'
                    if label_prefix:
                        lines.append(
                            f"{self.name}_bucket{{{label_prefix},{le_label}}} {cumulative}"
                        )
                    else:
                        lines.append(f"{self.name}_bucket{{{le_label}}} {cumulative}")
                inf_label = 'le="+Inf"'
                if label_prefix:
                    lines.append(f"{self.name}_bucket{{{label_prefix},{inf_label}}} {count}")
                    lines.append(f"{self.name}_sum{{{label_prefix}}} {total}")
                    lines.append(f"{self.name}_count{{{label_prefix}}} {count}")
                else:
                    lines.append(f"{self.name}_bucket{{{inf_label}}} {count}")
                    lines.append(f"{self.name}_sum {total}")
                    lines.append(f"{self.name}_count {count}")
        return lines


# ---------------------------------------------------------------------------
# Agent metrics registry
# ---------------------------------------------------------------------------


class AgentMetricsRegistry:
    """Pre-defined Prometheus metrics for Mapanare agent operations."""

    def __init__(self) -> None:
        self.agent_spawns = Counter(
            "mapanare_agent_spawns_total",
            "Total number of agent spawn operations",
            labels=["agent_type"],
        )
        self.agent_messages = Counter(
            "mapanare_agent_messages_total",
            "Total number of messages processed by agents",
            labels=["agent_type"],
        )
        self.agent_errors = Counter(
            "mapanare_agent_errors_total",
            "Total number of agent handler errors",
            labels=["agent_type"],
        )
        self.agent_stops = Counter(
            "mapanare_agent_stops_total",
            "Total number of agent stop operations",
            labels=["agent_type"],
        )
        self.agent_latency = Histogram(
            "mapanare_agent_handle_duration_seconds",
            "Duration of agent message handling in seconds",
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            labels=["agent_type"],
        )

    def collect_all(self) -> str:
        lines: list[str] = []
        counters: list[Counter] = [
            self.agent_spawns,
            self.agent_messages,
            self.agent_errors,
            self.agent_stops,
        ]
        for counter in counters:
            lines.extend(counter.collect())
            lines.append("")
        lines.extend(self.agent_latency.collect())
        lines.append("")
        return "\n".join(lines) + "\n"


# Global metrics registry
_metrics_registry = AgentMetricsRegistry()


def get_metrics() -> AgentMetricsRegistry:
    """Get the global agent metrics registry."""
    return _metrics_registry


# ---------------------------------------------------------------------------
# Prometheus HTTP endpoint
# ---------------------------------------------------------------------------


class _MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves Prometheus metrics."""

    registry: AgentMetricsRegistry = _metrics_registry

    def do_GET(self) -> None:
        if self.path == "/metrics" or self.path == "/":
            body = self.registry.collect_all().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress HTTP request logging


def start_metrics_server(addr: str = ":9090") -> HTTPServer:
    """Start a Prometheus metrics HTTP server in a background thread.

    Args:
        addr: Listen address in host:port format (e.g. ":9090", "0.0.0.0:9090").

    Returns:
        The HTTPServer instance.
    """
    host = ""
    port = 9090
    if addr.startswith(":"):
        port = int(addr[1:])
    elif ":" in addr:
        host, port_str = addr.rsplit(":", 1)
        port = int(port_str)
    else:
        port = int(addr)

    server = HTTPServer((host, port), _MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
