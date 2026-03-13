"""Phase 9 — Integration tests for v0.9.0 stdlib modules.

Verifies that stdlib modules can be combined in realistic scenarios and
compile to valid LLVM IR. Tests inline module sources since they validate
compilation, not runtime behavior (no network needed).

Covers:
  - Task 2: HTTP client → HTTP server round-trip (single binary)
  - Task 3: JSON decode → process → JSON encode round-trip
  - Task 4: CSV read → filter stream → CSV write
  - Task 5: WebSocket client ↔ server echo
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Helpers — read stdlib sources once
# ---------------------------------------------------------------------------

_STDLIB = Path(__file__).resolve().parent.parent.parent / "stdlib"

_JSON_MN = (_STDLIB / "encoding" / "json.mn").read_text(encoding="utf-8")
_CSV_MN = (_STDLIB / "encoding" / "csv.mn").read_text(encoding="utf-8")
_HTTP_MN = (_STDLIB / "net" / "http.mn").read_text(encoding="utf-8")
_SERVER_MN = (_STDLIB / "net" / "http" / "server.mn").read_text(encoding="utf-8")
_WS_MN = (_STDLIB / "net" / "websocket.mn").read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_integration.mn", use_mir=True)


def _with_main(modules: str, main_body: str) -> str:
    """Combine module sources with a main function."""
    return modules + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Task 2: HTTP client → HTTP server round-trip
#
# Note: http.mn and server.mn both define HttpRequest/HttpResponse, so they
# cannot be combined in a single compilation unit without Phase 8 namespacing.
# We test each module separately and verify the round-trip patterns compile.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHttpRoundTrip:
    def test_client_request_response_compiles(self) -> None:
        """HTTP client: build request, parse response flow."""
        src = _with_main(
            _HTTP_MN,
            """\
            let req: HttpRequest = new_http_request(GET(), "http://localhost:8080/api")
            let raw_resp: String = "HTTP/1.1 200 OK\\r\\nContent-Length: 5\\r\\n\\r\\nhello"
            let result: Result<HttpResponse, HttpError> = parse_raw_response(raw_resp)
            match result {
                Ok(resp) => { println(str(resp.status_code) + " " + resp.body) },
                Err(e) => { println("error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_server_request_response_compiles(self) -> None:
        """HTTP server: parse request, build response flow."""
        src = _with_main(
            _SERVER_MN,
            """\
            let raw: String = "GET /api/data HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n"
            let resp: String = build_response(200, #{}, "hello world")
            println(resp)
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_server_route_dispatch_compiles(self) -> None:
        """Router dispatch + response building compiles."""
        src = _with_main(
            _SERVER_MN,
            """\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/api/health", "handle_health")
            router = router_add_route(router, "POST", "/api/data", "handle_data")
            let mr: MatchResult = match_route("/api/health", "/api/health", "GET", "GET")
            let resp: String = build_response(200, #{}, "ok")
            println(resp)
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_client_convenience_methods_compile(self) -> None:
        """HTTP client convenience functions (get/post) compile."""
        src = _with_main(
            _HTTP_MN,
            """\
            let result: Result<HttpResponse, HttpError> = get("http://localhost:8080/health")
            println("compiled")
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 3: JSON decode → process → JSON encode round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestJsonRoundTrip:
    def test_decode_encode_string(self) -> None:
        """JSON string round-trip: decode then encode."""
        src = _with_main(
            _JSON_MN,
            """\
            let src: String = "\\"hello world\\""
            let result: Result<JsonValue, JsonError> = decode(src)
            match result {
                Ok(val) => {
                    let output: String = encode(val)
                    println(output)
                },
                Err(e) => { println(e.message) }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_process_encode_number(self) -> None:
        """Decode JSON number, process it, encode result."""
        src = _with_main(
            _JSON_MN,
            """\
            let src: String = "42"
            let result: Result<JsonValue, JsonError> = decode(src)
            match result {
                Ok(val) => {
                    let encoded: String = encode(val)
                    println(encoded)
                },
                Err(e) => { println("error: " + e.message) }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_encode_pretty(self) -> None:
        """Decode JSON array and pretty-print."""
        src = _with_main(
            _JSON_MN,
            """\
            let src: String = "[1, 2, 3]"
            let result: Result<JsonValue, JsonError> = decode(src)
            match result {
                Ok(val) => {
                    let pretty: String = encode_pretty(val, 2)
                    println(pretty)
                },
                Err(e) => { println("error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_object_encode(self) -> None:
        """Decode JSON object and re-encode."""
        src = _with_main(
            _JSON_MN,
            """\
            let src: String = "{\\"name\\": \\"mapanare\\", \\"version\\": 9}"
            let result: Result<JsonValue, JsonError> = decode(src)
            match result {
                Ok(val) => {
                    let output: String = encode(val)
                    println(output)
                },
                Err(e) => { println("parse error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_null_round_trip(self) -> None:
        """Null value round-trip: encode then decode."""
        src = _with_main(
            _JSON_MN,
            """\
            let v: JsonValue = Null()
            let encoded: String = encode(v)
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bool_round_trip(self) -> None:
        """Bool value round-trip."""
        src = _with_main(
            _JSON_MN,
            """\
            let v: JsonValue = Bool(true)
            let encoded: String = encode(v)
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_nested_structure_round_trip(self) -> None:
        """Nested JSON structure decode+encode round-trip."""
        src = _with_main(
            _JSON_MN,
            """\
            let src: String = "{\\"users\\": [1, 2], \\"active\\": true}"
            let result: Result<JsonValue, JsonError> = decode(src)
            match result {
                Ok(val) => {
                    let back: String = encode(val)
                    println(back)
                },
                Err(e) => { println("fail") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 4: CSV read → filter → CSV write
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCsvPipeline:
    def test_parse_and_to_string_round_trip(self) -> None:
        """CSV parse then to_string round-trip."""
        src = _with_main(
            _CSV_MN,
            """\
            let csv_data: String = "name,age\\nAlice,30\\nBob,25"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            match result {
                Ok(table) => {
                    let output: String = to_string(table, ",", "\\"")
                    println(output)
                },
                Err(e) => { println("error: " + e.message) }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_with_config(self) -> None:
        """Parse CSV with custom config."""
        src = _with_main(
            _CSV_MN,
            """\
            let csv_data: String = "name,age\\nAlice,30\\nBob,25"
            let config: CsvConfig = default_csv_config()
            let result: Result<CsvTable, CsvError> = parse_with(csv_data, config)
            match result {
                Ok(table) => { println("rows parsed") },
                Err(e) => { println("error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_access_headers(self) -> None:
        """Parse CSV and access header row."""
        src = _with_main(
            _CSV_MN,
            """\
            let csv_data: String = "id,name,score\\n1,Alice,95\\n2,Bob,87"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            match result {
                Ok(table) => {
                    let h: List<String> = table.headers
                    let r: List<List<String>> = table.rows
                    println("headers: " + str(len(h)) + " rows: " + str(len(r)))
                },
                Err(e) => { println("error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_quoted_fields(self) -> None:
        """CSV with quoted fields parses correctly."""
        src = _with_main(
            _CSV_MN,
            """\
            let csv_data: String = "name,bio\\n\\"Alice\\",\\"likes, commas\\""
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            match result {
                Ok(table) => {
                    let output: String = to_string(table, ",", "\\"")
                    println(output)
                },
                Err(e) => { println("error") }
            }
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 5: WebSocket client ↔ server echo
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWebSocketEcho:
    def test_ws_types_compile(self) -> None:
        """WebSocket message and connection types compile."""
        src = _with_main(
            _WS_MN,
            """\
            let msg: WsMessage = Text("hello")
            println("compiled")
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_frame_encode_compiles(self) -> None:
        """Frame building and encoding compiles."""
        src = _with_main(
            _WS_MN,
            """\
            let frame_data: String = build_send_frame(1, "test message", true)
            println("frame built, len=" + str(len(frame_data)))
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_upgrade_detection_compiles(self) -> None:
        """WebSocket upgrade detection compiles."""
        src = _with_main(
            _WS_MN,
            """\
            let headers: Map<String, String> = #{"Upgrade": "websocket", "Connection": "Upgrade"}
            let is_upgrade: Bool = is_websocket_upgrade(headers)
            println("upgrade=" + str(is_upgrade))
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_masking_compiles(self) -> None:
        """WebSocket masking operations compile."""
        src = _with_main(
            _WS_MN,
            """\
            let mask: String = "abcd"
            let data: String = "hello"
            let masked: String = apply_mask(data, mask)
            let unmasked: String = apply_mask(masked, mask)
            println("ok")
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_handshake_key_compiles(self) -> None:
        """WebSocket accept key computation compiles."""
        src = _with_main(
            _WS_MN,
            """\
            let key: String = "dGVzdA=="
            let accept: String = compute_accept_key(key)
            println("accept=" + accept)
        """,
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out
