"""Mapanare deployment runtime -- health checks, readiness probes, graceful shutdown."""

from __future__ import annotations

import asyncio
import json
import signal
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

from runtime.agent import AgentRegistry, AgentState, global_registry

# ---------------------------------------------------------------------------
# Health Check Server
# ---------------------------------------------------------------------------


class _HealthStatus:
    """Tracks application health and readiness state."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or global_registry
        self._started_at = time.time()
        self._custom_checks: dict[str, bool] = {}

    @property
    def is_healthy(self) -> bool:
        """Liveness: the process is alive and responding."""
        return True

    @property
    def is_ready(self) -> bool:
        """Readiness: all registered agents are initialized and running."""
        names = self._registry.list()
        if not names:
            # No agents registered yet — not ready
            return False
        for name in names:
            handle = self._registry.get(name)
            if handle is None:
                return False
            state = handle._agent.state
            if state not in (AgentState.RUNNING, AgentState.PAUSED):
                return False
        # Check custom readiness conditions
        for _name, ok in self._custom_checks.items():
            if not ok:
                return False
        return True

    def set_check(self, name: str, ok: bool) -> None:
        """Register a custom readiness check."""
        self._custom_checks[name] = ok

    def remove_check(self, name: str) -> None:
        """Remove a custom readiness check."""
        self._custom_checks.pop(name, None)

    def status_dict(self) -> dict[str, Any]:
        """Return health status as a dictionary."""
        names = self._registry.list()
        agents: dict[str, str] = {}
        for name in names:
            handle = self._registry.get(name)
            if handle is not None:
                agents[name] = handle._agent.state.value
        return {
            "healthy": self.is_healthy,
            "ready": self.is_ready,
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "agents": agents,
            "checks": dict(self._custom_checks),
        }


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for /health and /ready endpoints."""

    health_status: _HealthStatus

    def do_GET(self) -> None:
        if self.path == "/health":
            self._respond(200 if self.health_status.is_healthy else 503)
        elif self.path == "/ready":
            self._respond(200 if self.health_status.is_ready else 503)
        elif self.path == "/status":
            body = json.dumps(self.health_status.status_dict())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def _respond(self, code: int) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        status = self.health_status.status_dict()
        self.wfile.write(json.dumps(status).encode())

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress default request logging
        pass


class HealthServer:
    """HTTP server for health check and readiness probe endpoints."""

    def __init__(
        self,
        addr: str = ":8080",
        registry: AgentRegistry | None = None,
    ) -> None:
        self._registry = registry or global_registry
        self.status = _HealthStatus(self._registry)
        host, _, port_str = addr.rpartition(":")
        host = host or "0.0.0.0"
        port = int(port_str) if port_str else 8080

        handler_class = type(
            "_BoundHealthHandler",
            (_HealthHandler,),
            {"health_status": self.status},
        )
        self._server = HTTPServer((host, port), handler_class)
        self._thread: Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        return self._server.server_address  # type: ignore[return-value]

    def start(self) -> None:
        """Start the health server in a background thread."""
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Shutdown the health server."""
        self._server.shutdown()
        if self._thread:
            self._thread.join(timeout=5.0)


# ---------------------------------------------------------------------------
# Graceful Shutdown
# ---------------------------------------------------------------------------


class GracefulShutdown:
    """Handles SIGTERM/SIGINT with agent mailbox draining."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        drain_timeout: float = 30.0,
        health_server: HealthServer | None = None,
    ) -> None:
        self._registry = registry or global_registry
        self._drain_timeout = drain_timeout
        self._health_server = health_server
        self._shutting_down = False

    def install(self) -> None:
        """Install signal handlers for SIGTERM and SIGINT."""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._signal_handler)
        else:
            signal.signal(signal.SIGTERM, self._sync_signal_handler)
            signal.signal(signal.SIGINT, self._sync_signal_handler)

    def _signal_handler(self) -> None:
        """Async-safe signal handler (Unix)."""
        if self._shutting_down:
            return
        self._shutting_down = True
        asyncio.ensure_future(self._shutdown())

    def _sync_signal_handler(self, signum: int, frame: Any) -> None:
        """Sync signal handler (Windows)."""
        if self._shutting_down:
            return
        self._shutting_down = True
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._shutdown())
        except RuntimeError:
            # No running loop — force exit
            sys.exit(0)

    async def _shutdown(self) -> None:
        """Drain agent mailboxes and stop all agents."""
        names = self._registry.list()

        # Phase 1: Drain mailboxes (wait for queues to empty)
        deadline = time.monotonic() + self._drain_timeout
        for name in names:
            handle = self._registry.get(name)
            if handle is None:
                continue
            agent = handle._agent
            while time.monotonic() < deadline:
                total_pending = 0
                for ch in agent._inputs.values():
                    total_pending += ch.qsize()
                if total_pending == 0:
                    break
                await asyncio.sleep(0.05)

        # Phase 2: Stop all agents
        await self._registry.stop_all()

        # Phase 3: Stop health server if running
        if self._health_server:
            self._health_server.stop()

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down

    async def shutdown(self) -> None:
        """Programmatic shutdown (for testing or direct use)."""
        self._shutting_down = True
        await self._shutdown()
