"""Phase 5 — net/websocket.mn — WebSocket Client + Server tests.

Tests verify that the WebSocket stdlib module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation (Phase 8) is not yet
ready, tests inline the websocket module source code within test programs.

Covers:
  - Core types: WsMessage, WsConnection, WsError
  - URL parsing (ws:// and wss://)
  - WebSocket key generation and accept key computation
  - Frame encoding/decoding helpers
  - Bitwise operations (XOR, OR, AND)
  - Client connect compilation
  - Server upgrade compilation
  - Send/receive compilation
  - Close handshake compilation
  - Echo loop compilation
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
# Helpers
# ---------------------------------------------------------------------------

# Read the websocket module source once
_WS_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "net" / "websocket.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_websocket.mn", use_mir=True)


def _ws_source_with_main(main_body: str) -> str:
    """Prepend the websocket module source and wrap main_body in fn main()."""
    return _WS_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Task 1: WsMessage enum
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsMessage:
    def test_text_variant_compiles(self) -> None:
        """WsMessage::Text variant compiles."""
        src = _ws_source_with_main('let msg: WsMessage = Text("hello")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_binary_variant_compiles(self) -> None:
        """WsMessage::Binary variant compiles."""
        src = _ws_source_with_main('let msg: WsMessage = Binary("data")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ping_variant_compiles(self) -> None:
        """WsMessage::Ping variant compiles."""
        src = _ws_source_with_main('let msg: WsMessage = Ping("")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pong_variant_compiles(self) -> None:
        """WsMessage::Pong variant compiles."""
        src = _ws_source_with_main('let msg: WsMessage = Pong("")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_close_variant_compiles(self) -> None:
        """WsMessage::Close variant compiles."""
        src = _ws_source_with_main('let msg: WsMessage = Close(1000, "bye")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 2: WsConnection struct
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsConnection:
    def test_connection_compiles(self) -> None:
        """WsConnection struct compiles with all fields."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_server_connection_compiles(self) -> None:
        """Server-side WsConnection compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, true)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 3: WsError enum
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsError:
    def test_handshake_failed_compiles(self) -> None:
        """WsError::HandshakeFailed variant compiles."""
        src = _ws_source_with_main('let e: WsError = HandshakeFailed("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_connection_closed_compiles(self) -> None:
        """WsError::ConnectionClosed variant compiles."""
        src = _ws_source_with_main('let e: WsError = ConnectionClosed("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_invalid_frame_compiles(self) -> None:
        """WsError::InvalidFrame variant compiles."""
        src = _ws_source_with_main('let e: WsError = InvalidFrame("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_protocol_error_compiles(self) -> None:
        """WsError::ProtocolError variant compiles."""
        src = _ws_source_with_main('let e: WsError = ProtocolError("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_failed_compiles(self) -> None:
        """WsError::SendFailed variant compiles."""
        src = _ws_source_with_main('let e: WsError = SendFailed("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_recv_failed_compiles(self) -> None:
        """WsError::RecvFailed variant compiles."""
        src = _ws_source_with_main('let e: WsError = RecvFailed("test")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsUrlParsing:
    def test_ws_url_compiles(self) -> None:
        """Parse ws:// URL compiles."""
        src = _ws_source_with_main("""\
            let u: WsUrl = parse_ws_url("ws://example.com/ws")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_wss_url_compiles(self) -> None:
        """Parse wss:// URL compiles."""
        src = _ws_source_with_main("""\
            let u: WsUrl = parse_ws_url("wss://example.com/ws")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_url_with_port_compiles(self) -> None:
        """Parse URL with explicit port compiles."""
        src = _ws_source_with_main("""\
            let u: WsUrl = parse_ws_url("ws://localhost:8080/chat")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 5+6: WebSocket key generation and accept key
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsHandshakeKeys:
    def test_generate_ws_key_compiles(self) -> None:
        """Generate WebSocket key (random + base64) compiles."""
        src = _ws_source_with_main("""\
            let key: String = generate_ws_key()
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_compute_accept_key_compiles(self) -> None:
        """Compute accept key (SHA-1 + base64) compiles."""
        src = _ws_source_with_main("""\
            let accept: String = compute_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_guid_compiles(self) -> None:
        """WebSocket GUID constant compiles."""
        src = _ws_source_with_main("""\
            let guid: String = ws_guid()
            print(guid)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Bitwise operations
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBitwiseOps:
    def test_xor_bytes_compiles(self) -> None:
        """XOR bytes helper compiles."""
        src = _ws_source_with_main("""\
            let result: Int = xor_bytes(170, 85)
            print(str(result))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bitor_compiles(self) -> None:
        """Bitwise OR helper compiles."""
        src = _ws_source_with_main("""\
            let result: Int = bitor(128, 1)
            print(str(result))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bitand_compiles(self) -> None:
        """Bitwise AND helper compiles."""
        src = _ws_source_with_main("""\
            let result: Int = bitand(255, 15)
            print(str(result))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 13: Frame encoding
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFrameEncoding:
    def test_ws_frame_struct_compiles(self) -> None:
        """WsFrame struct compiles."""
        src = _ws_source_with_main("""\
            let frame: WsFrame = new_ws_frame(true, 1, false, "", "hello")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_send_frame_text_compiles(self) -> None:
        """Build send frame for text compiles."""
        src = _ws_source_with_main("""\
            let frame: String = build_send_frame(1, "hello", true)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_send_frame_no_mask_compiles(self) -> None:
        """Build send frame without mask (server mode) compiles."""
        src = _ws_source_with_main("""\
            let frame: String = build_send_frame(1, "hello", false)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_frame_compiles(self) -> None:
        """encode_frame compiles."""
        src = _ws_source_with_main("""\
            let frame: WsFrame = new_ws_frame(true, 1, false, "", "test")
            let encoded: String = encode_frame(frame)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 14: Frame decoding
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFrameDecoding:
    def test_decode_frame_compiles(self) -> None:
        """decode_frame compiles."""
        src = _ws_source_with_main("""\
            let raw: String = "AB"
            let result: FrameDecodeResult = decode_frame(raw)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_frame_decode_result_fields_compile(self) -> None:
        """FrameDecodeResult field access compiles."""
        src = _ws_source_with_main("""\
            let raw: String = "ABCDEFGHIJKLMNOP"
            let result: FrameDecodeResult = decode_frame(raw)
            if result.ok {
                print("decoded")
            } else {
                print(result.error_msg)
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 9: Masking
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMasking:
    def test_apply_mask_compiles(self) -> None:
        """apply_mask compiles."""
        src = _ws_source_with_main("""\
            let masked: String = apply_mask("hello", "ABCD")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 4: ws_connect
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsConnect:
    def test_ws_connect_compiles(self) -> None:
        """ws_connect to ws:// URL compiles (extern TCP calls present)."""
        src = _ws_source_with_main("""\
            let r: Result<WsConnection, WsError> = ws_connect("ws://echo.example.com/ws")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        # Verify extern declarations are present
        assert "__mn_tcp_connect_str" in ir_out

    def test_wss_connect_compiles(self) -> None:
        """ws_connect to wss:// URL compiles with TLS externs."""
        src = _ws_source_with_main("""\
            let r: Result<WsConnection, WsError> = ws_connect("wss://echo.example.com/ws")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tls_connect_str" in ir_out


# ---------------------------------------------------------------------------
# Task 7: ws_send
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsSend:
    def test_send_text_compiles(self) -> None:
        """ws_send with Text message compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_send(conn, Text("hello"))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_binary_compiles(self) -> None:
        """ws_send with Binary message compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_send(conn, Binary("data"))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_ping_compiles(self) -> None:
        """ws_send with Ping message compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_send(conn, Ping(""))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 8: ws_recv
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsRecv:
    def test_recv_compiles(self) -> None:
        """ws_recv compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<WsMessage, WsError> = ws_recv(conn)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 10: is_websocket_upgrade
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWebSocketUpgradeDetection:
    def test_is_websocket_upgrade_compiles(self) -> None:
        """is_websocket_upgrade compiles."""
        src = _ws_source_with_main("""\
            let mut headers: Map<String, String> = #{}
            headers["upgrade"] = "websocket"
            headers["connection"] = "upgrade"
            headers["sec-websocket-key"] = "dGhlIHNhbXBsZSBub25jZQ=="
            let result: Bool = is_websocket_upgrade(headers)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 11: ws_accept_upgrade (server handshake)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsAcceptUpgrade:
    def test_accept_upgrade_compiles(self) -> None:
        """ws_accept_upgrade compiles (extern TCP send present)."""
        src = _ws_source_with_main("""\
            let mut headers: Map<String, String> = #{}
            headers["sec-websocket-key"] = "dGhlIHNhbXBsZSBub25jZQ=="
            let r: Result<WsConnection, WsError> = ws_accept_upgrade(5, headers)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tcp_send_str" in ir_out


# ---------------------------------------------------------------------------
# Task 17: ws_close
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWsClose:
    def test_close_compiles(self) -> None:
        """ws_close compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_close(conn, 1000, "bye")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 16: Ping/Pong
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPingPong:
    def test_send_ping_compiles(self) -> None:
        """Sending Ping message compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_send(conn, Ping("ping-data"))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_pong_compiles(self) -> None:
        """Sending Pong message compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<Int, WsError> = ws_send(conn, Pong("pong-data"))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Echo loop (integration pattern)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEchoLoop:
    def test_echo_loop_compiles(self) -> None:
        """ws_echo_loop compiles (full server-side echo pattern)."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, true)
            let r: Result<Int, WsError> = ws_echo_loop(conn)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 25: Server upgrade integration with HTTP
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestServerUpgradeIntegration:
    def test_full_server_upgrade_flow_compiles(self) -> None:
        """Complete server-side upgrade flow compiles."""
        src = _ws_source_with_main("""\
            let mut headers: Map<String, String> = #{}
            headers["upgrade"] = "websocket"
            headers["connection"] = "upgrade"
            headers["sec-websocket-key"] = "dGhlIHNhbXBsZSBub25jZQ=="
            if is_websocket_upgrade(headers) {
                let r: Result<WsConnection, WsError> = ws_accept_upgrade(5, headers)
                match r {
                    Ok(conn) => {
                        print("upgraded")
                    },
                    Err(e) => {
                        print("failed")
                    }
                }
            }
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 15: Fragmentation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFragmentation:
    def test_continuation_frame_struct_compiles(self) -> None:
        """WsConnection fragmentation fields compile."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let fb: String = conn.frag_buffer
            let fo: Int = conn.frag_opcode
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_send_fragmented_compiles(self) -> None:
        """ws_send_fragmented compiles with text message."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let m: WsMessage = Text("hello world long msg")
            let r: Result<Int, WsError> = ws_send_fragmented(conn, m, 10)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_send_fragmented_binary_compiles(self) -> None:
        """ws_send_fragmented compiles with binary message."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let m: WsMessage = Binary("binary-data")
            let r: Result<Int, WsError> = ws_send_fragmented(conn, m, 5)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_send_fragmented_server_no_mask_compiles(self) -> None:
        """ws_send_fragmented from server (no masking) compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, true)
            let r: Result<Int, WsError> = ws_send_fragmented(conn, Text("server message"), 4)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_recv_full_compiles(self) -> None:
        """ws_recv_full (fragmented reassembly) compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let r: Result<WsMessage, WsError> = ws_recv_full(conn)
            match r {
                Ok(msg) => {
                    match msg {
                        Text(data) => { print(data) },
                        Binary(data) => { print("binary") },
                        Ping(data) => { print("ping") },
                        Pong(data) => { print("pong") },
                        Close(code, reason) => { print("close") }
                    }
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ws_recv_full_server_side_compiles(self) -> None:
        """ws_recv_full from server-side connection compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, true)
            let r: Result<WsMessage, WsError> = ws_recv_full(conn)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Crypto extern declarations
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCryptoExterns:
    def test_sha1_extern_present(self) -> None:
        """SHA-1 extern declaration present in compiled IR."""
        src = _ws_source_with_main('print("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_sha1_str" in ir_out

    def test_base64_extern_present(self) -> None:
        """Base64 extern declaration present in compiled IR."""
        src = _ws_source_with_main('print("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_base64_encode_str" in ir_out

    def test_random_bytes_extern_present(self) -> None:
        """Random bytes extern declaration present in compiled IR."""
        src = _ws_source_with_main('print("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_random_bytes_str" in ir_out


# ---------------------------------------------------------------------------
# Header extraction helper
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHeaderExtraction:
    def test_extract_header_compiles(self) -> None:
        """extract_header compiles."""
        src = _ws_source_with_main("""\
            let resp: String = "HTTP/1.1 101\\r\\nUpgrade: websocket\\r\\n\\r\\n"
            let val: String = extract_header(resp, "upgrade")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 20-26: Full integration test patterns (compile-only)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestIntegrationPatterns:
    def test_client_connect_send_recv_close_compiles(self) -> None:
        """Full client flow: connect → send → recv → close compiles."""
        src = _ws_source_with_main("""\
            let r: Result<WsConnection, WsError> = ws_connect("ws://echo.example.com/ws")
            match r {
                Ok(conn) => {
                    let sr: Result<Int, WsError> = ws_send(conn, Text("hello"))
                    let mr: Result<WsMessage, WsError> = ws_recv(conn)
                    let cr: Result<Int, WsError> = ws_close(conn, 1000, "done")
                    print("done")
                },
                Err(e) => {
                    print("failed")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_server_upgrade_echo_compiles(self) -> None:
        """Server upgrade + echo loop compiles."""
        src = _ws_source_with_main("""\
            let mut headers: Map<String, String> = #{}
            headers["sec-websocket-key"] = "dGhlIHNhbXBsZSBub25jZQ=="
            let r: Result<WsConnection, WsError> = ws_accept_upgrade(5, headers)
            match r {
                Ok(conn) => {
                    let er: Result<Int, WsError> = ws_echo_loop(conn)
                    print("echo done")
                },
                Err(e) => {
                    print("upgrade failed")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_recv_text_round_trip_compiles(self) -> None:
        """Text send/recv round-trip pattern compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let sr: Result<Int, WsError> = ws_send(conn, Text("hello world"))
            let mr: Result<WsMessage, WsError> = ws_recv(conn)
            match mr {
                Ok(msg) => {
                    match msg {
                        Text(data) => { print(data) },
                        Binary(data) => { print("binary") },
                        Ping(data) => { print("ping") },
                        Pong(data) => { print("pong") },
                        Close(code, reason) => { print("close") }
                    }
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_send_recv_binary_compiles(self) -> None:
        """Binary send/recv pattern compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let sr: Result<Int, WsError> = ws_send(conn, Binary("binary-data"))
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ping_pong_round_trip_compiles(self) -> None:
        """Ping/pong round-trip pattern compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let pr: Result<Int, WsError> = ws_send(conn, Ping("test"))
            let mr: Result<WsMessage, WsError> = ws_recv(conn)
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_close_handshake_compiles(self) -> None:
        """Close handshake pattern compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let cr: Result<Int, WsError> = ws_close(conn, 1000, "normal closure")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_fragmented_send_recv_round_trip_compiles(self) -> None:
        """Task 26: Fragmented message send + reassembly recv compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let msg: WsMessage = Text("a long message that needs frag")
            let sr: Result<Int, WsError> = ws_send_fragmented(conn, msg, 8)
            let mr: Result<WsMessage, WsError> = ws_recv_full(conn)
            match mr {
                Ok(msg) => {
                    match msg {
                        Text(data) => { print(data) },
                        Binary(data) => { print("binary") },
                        Ping(data) => { print("ping") },
                        Pong(data) => { print("pong") },
                        Close(code, reason) => { print("close") }
                    }
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "ws_send_fragmented" in ir_out
        assert "ws_recv_full" in ir_out

    def test_close_with_custom_code_compiles(self) -> None:
        """Close with custom code (e.g., 1001 going away) compiles."""
        src = _ws_source_with_main("""\
            let conn: WsConnection = new_ws_connection(5, 0, false, false)
            let cr: Result<Int, WsError> = ws_close(conn, 1001, "going away")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_full_server_echo_with_fragmentation_compiles(self) -> None:
        """Server upgrade + fragmented echo pattern compiles."""
        src = _ws_source_with_main("""\
            let mut headers: Map<String, String> = #{}
            headers["sec-websocket-key"] = "dGhlIHNhbXBsZSBub25jZQ=="
            let r: Result<WsConnection, WsError> = ws_accept_upgrade(5, headers)
            match r {
                Ok(conn) => {
                    let mr: Result<WsMessage, WsError> = ws_recv_full(conn)
                    match mr {
                        Ok(msg) => {
                            let sr: Result<Int, WsError> = ws_send_fragmented(conn, msg, 1024)
                            print("echoed")
                        },
                        Err(e) => { print("recv error") }
                    }
                },
                Err(e) => { print("upgrade failed") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
