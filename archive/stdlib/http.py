"""mapanare.http -- HTTP client/server agents."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from runtime.agent import AgentBase, AgentState

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class HttpRequest:
    """Represents an HTTP request."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""


@dataclass
class HttpResponse:
    """Represents an HTTP response."""

    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self) -> Any:
        return json.loads(self.body)


# ---------------------------------------------------------------------------
# HTTP client agent
# ---------------------------------------------------------------------------


class HttpClientAgent(AgentBase):
    """Agent that sends HTTP requests and returns responses.

    Receives ``HttpRequest`` objects and sends back ``HttpResponse`` objects.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        super().__init__()
        self._timeout = timeout
        self._register_input("inp")
        self._register_output("out")

    async def handle(self, value: Any) -> Any:
        if not isinstance(value, HttpRequest):
            raise TypeError(f"HttpClientAgent expects HttpRequest, got {type(value)}")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._do_request, value)
        return response

    def _do_request(self, req: HttpRequest) -> HttpResponse:
        """Execute HTTP request synchronously (run in executor)."""
        try:
            stdlib_req = Request(
                req.url,
                data=req.body.encode("utf-8") if req.body else None,
                headers=req.headers,
                method=req.method,
            )
            with urlopen(stdlib_req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
                headers = dict(resp.headers.items())
                return HttpResponse(status=resp.status, headers=headers, body=body)
        except HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return HttpResponse(status=e.code, body=body)
        except URLError as e:
            return HttpResponse(status=0, body=str(e.reason))


# ---------------------------------------------------------------------------
# HTTP server agent
# ---------------------------------------------------------------------------


class HttpServerAgent(AgentBase):
    """Agent that runs an HTTP server and forwards requests.

    Each incoming HTTP request is sent as an ``HttpRequest`` to the output channel.
    Responses can be sent back by providing a handler function.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        handler: Callable[[HttpRequest], HttpResponse] | None = None,
    ) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._handler = handler or self._default_handler
        self._server: HTTPServer | None = None
        self._register_output("out")

    @staticmethod
    def _default_handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body="OK")

    async def _run(self) -> None:
        self._running = True
        self._state = AgentState.RUNNING
        await self.on_init()

        handler_fn = self._handler

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self._handle_request("GET")

            def do_POST(self) -> None:
                self._handle_request("POST")

            def do_PUT(self) -> None:
                self._handle_request("PUT")

            def do_DELETE(self) -> None:
                self._handle_request("DELETE")

            def _handle_request(self, method: str) -> None:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
                headers = {k: v for k, v in self.headers.items()}

                req = HttpRequest(
                    method=method,
                    url=self.path,
                    headers=headers,
                    body=body,
                )

                resp = handler_fn(req)

                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                if resp.body:
                    self.wfile.write(resp.body.encode("utf-8"))

            def log_message(self, format: str, *args: Any) -> None:
                pass  # Suppress default logging

        loop = asyncio.get_event_loop()

        def _serve() -> None:
            self._server = HTTPServer((self._host, self._port), _Handler)
            self._server.timeout = 0.5
            while self._running:
                self._server.handle_request()

        server_task = loop.run_in_executor(None, _serve)

        try:
            while self._running:
                await self._pause_event.wait()
                if not self._running:
                    break
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            if self._server:
                self._server.server_close()
            try:
                await server_task
            except Exception:
                pass

        if self._state != AgentState.FAILED:
            self._state = AgentState.STOPPED
        await self.on_stop()


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


async def get(
    url: str, headers: dict[str, str] | None = None, timeout: float = 30.0
) -> HttpResponse:
    """Send an HTTP GET request."""
    req = HttpRequest(method="GET", url=url, headers=headers or {})
    loop = asyncio.get_event_loop()
    agent = HttpClientAgent(timeout=timeout)
    return await loop.run_in_executor(None, agent._do_request, req)


async def post(
    url: str,
    body: str = "",
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> HttpResponse:
    """Send an HTTP POST request."""
    req = HttpRequest(method="POST", url=url, headers=headers or {}, body=body)
    loop = asyncio.get_event_loop()
    agent = HttpClientAgent(timeout=timeout)
    return await loop.run_in_executor(None, agent._do_request, req)
