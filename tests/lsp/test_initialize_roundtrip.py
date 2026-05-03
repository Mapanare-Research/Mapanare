"""LSP initialize round-trip smoke test.

v5.18.0 Mc.1 success criterion #1: ``mnc lsp`` runs and ``initialize``
round-trips correctly. We spawn the server subprocess, send a real
``initialize`` request over stdio with LSP framing, and verify the
response includes a ``capabilities`` object.

Marked slow because it boots a subprocess; runs in <1s in practice.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _frame(payload: dict) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _read_message(stdout) -> dict:
    """Read one LSP-framed JSON message from a stream."""
    header_lines: list[bytes] = []
    while True:
        line = stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout before sending headers")
        if line in (b"\r\n", b"\n"):
            break
        header_lines.append(line)
    length = 0
    for h in header_lines:
        if h.lower().startswith(b"content-length:"):
            length = int(h.split(b":", 1)[1].strip())
    if not length:
        raise RuntimeError(f"missing content-length: {header_lines!r}")
    body = stdout.read(length)
    return json.loads(body.decode("utf-8"))


def test_initialize_roundtrip() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "mapanare", "lsp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    try:
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": None,
                "capabilities": {},
            },
        }
        assert proc.stdin is not None
        proc.stdin.write(_frame(init_request))
        proc.stdin.flush()

        assert proc.stdout is not None
        response = _read_message(proc.stdout)

        assert response["id"] == 1, response
        assert "result" in response, response
        assert "capabilities" in response["result"], response

        # Send shutdown + exit so the process winds down cleanly.
        proc.stdin.write(_frame({"jsonrpc": "2.0", "id": 2, "method": "shutdown"}))
        proc.stdin.flush()
        _ = _read_message(proc.stdout)
        proc.stdin.write(_frame({"jsonrpc": "2.0", "method": "exit"}))
        proc.stdin.flush()
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
