"""Tests for mapanare.http -- HTTP client/server agents."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from stdlib.http import (
    HttpClientAgent,
    HttpRequest,
    HttpResponse,
    HttpServerAgent,
)

# ---------------------------------------------------------------------------
# HttpRequest / HttpResponse data types
# ---------------------------------------------------------------------------


class TestHttpRequest:
    def test_create_request(self) -> None:
        req = HttpRequest(method="GET", url="http://example.com")
        assert req.method == "GET"
        assert req.url == "http://example.com"
        assert req.headers == {}
        assert req.body == ""

    def test_request_with_body(self) -> None:
        req = HttpRequest(method="POST", url="/api", body='{"key": "val"}')
        assert req.body == '{"key": "val"}'

    def test_request_with_headers(self) -> None:
        req = HttpRequest(method="GET", url="/", headers={"X-Token": "abc"})
        assert req.headers["X-Token"] == "abc"


class TestHttpResponse:
    def test_ok_response(self) -> None:
        resp = HttpResponse(status=200, body="OK")
        assert resp.ok is True

    def test_error_response(self) -> None:
        resp = HttpResponse(status=404, body="Not Found")
        assert resp.ok is False

    def test_json_response(self) -> None:
        resp = HttpResponse(status=200, body='{"name": "mapanare"}')
        data = resp.json()
        assert data["name"] == "mapanare"

    def test_status_ranges(self) -> None:
        assert HttpResponse(status=200).ok is True
        assert HttpResponse(status=201).ok is True
        assert HttpResponse(status=299).ok is True
        assert HttpResponse(status=300).ok is False
        assert HttpResponse(status=500).ok is False


# ---------------------------------------------------------------------------
# HttpClientAgent tests (with local test server)
# ---------------------------------------------------------------------------


class _TestHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for testing."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"path": self.path}).encode())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        self.send_response(201)
        self.end_headers()
        self.wfile.write(json.dumps({"echo": body}).encode())

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def test_server() -> tuple[HTTPServer, int]:
    """Start a local HTTP server for testing."""
    server = HTTPServer(("127.0.0.1", 0), _TestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, port  # type: ignore[misc]
    server.shutdown()


class TestHttpClientAgent:
    async def test_get_request(self, test_server: tuple[HTTPServer, int]) -> None:
        _, port = test_server
        agent = HttpClientAgent(timeout=5.0)
        req = HttpRequest(method="GET", url=f"http://127.0.0.1:{port}/hello")
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, agent._do_request, req)
        assert resp.status == 200
        assert resp.json()["path"] == "/hello"

    async def test_post_request(self, test_server: tuple[HTTPServer, int]) -> None:
        _, port = test_server
        agent = HttpClientAgent(timeout=5.0)
        req = HttpRequest(
            method="POST",
            url=f"http://127.0.0.1:{port}/data",
            body="payload",
        )
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, agent._do_request, req)
        assert resp.status == 201
        assert resp.json()["echo"] == "payload"

    async def test_connection_error(self) -> None:
        agent = HttpClientAgent(timeout=1.0)
        req = HttpRequest(method="GET", url="http://127.0.0.1:1/nope")
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, agent._do_request, req)
        assert resp.status == 0  # connection error

    async def test_agent_spawn_and_handle(self, test_server: tuple[HTTPServer, int]) -> None:
        _, port = test_server
        handle = await HttpClientAgent.spawn(timeout=5.0)
        req = HttpRequest(method="GET", url=f"http://127.0.0.1:{port}/test")
        await handle._agent._inputs["inp"].send(req)
        await asyncio.sleep(0.3)
        out_ch = handle._agent._outputs["out"]
        resp = await asyncio.wait_for(out_ch.receive(), timeout=2.0)
        assert isinstance(resp, HttpResponse)
        assert resp.status == 200
        await handle.stop()


# ---------------------------------------------------------------------------
# HttpServerAgent tests
# ---------------------------------------------------------------------------


class TestHttpServerAgent:
    async def test_server_starts_and_stops(self) -> None:
        def handler(req: HttpRequest) -> HttpResponse:
            return HttpResponse(status=200, body="pong")

        handle = await HttpServerAgent.spawn(host="127.0.0.1", port=0, handler=handler)
        await asyncio.sleep(0.2)
        await handle.stop()
        # Just verify it didn't crash

    async def test_server_with_handler(self) -> None:
        calls: list[str] = []

        def handler(req: HttpRequest) -> HttpResponse:
            calls.append(req.method)
            return HttpResponse(status=200, body="handled")

        # Use a specific port for this test
        port = 18923
        handle = await HttpServerAgent.spawn(host="127.0.0.1", port=port, handler=handler)
        await asyncio.sleep(0.3)

        # Send a request to the server
        client = HttpClientAgent(timeout=2.0)
        req = HttpRequest(method="GET", url=f"http://127.0.0.1:{port}/test")
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, client._do_request, req)

        assert resp.status == 200
        assert resp.body == "handled"
        assert "GET" in calls
        await handle.stop()
