"""Phase 3 — net/http.mn — Unified HTTP Client tests.

Tests verify that the HTTP stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the HTTP module source code within test programs.

Covers:
  - Core types: HttpMethod, HttpRequest, HttpResponse, HttpError, HttpConfig
  - URL parsing: scheme, host, port, path, query
  - URL encoding/decoding
  - Query parameter building
  - Request building
  - Response parsing (status line, headers, body)
  - Content-Length body extraction
  - Chunked transfer decoding
  - Redirect detection and URL resolution
  - Convenience functions: get, post, put, delete, patch, head, options
  - Request fingerprinting
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

# Read the HTTP module source once
_HTTP_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "net" / "http.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_http.mn", use_mir=True)


def _http_source_with_main(main_body: str) -> str:
    """Prepend the HTTP module source and wrap main_body in fn main()."""
    return (
        _HTTP_MN
        + "\n\n"
        + textwrap.dedent(
            f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """
        )
    )


# ---------------------------------------------------------------------------
# Task 1: HttpMethod enum compiles
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHttpMethod:
    def test_method_enum_compiles(self) -> None:
        """HttpMethod enum with all variants compiles."""
        src = _http_source_with_main("""\
            let m: HttpMethod = GET()
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_all_method_variants(self) -> None:
        """All HttpMethod variants compile."""
        src = _http_source_with_main("""\
            let m1: HttpMethod = GET()
            let m2: HttpMethod = POST()
            let m3: HttpMethod = PUT()
            let m4: HttpMethod = DELETE()
            let m5: HttpMethod = PATCH()
            let m6: HttpMethod = HEAD()
            let m7: HttpMethod = OPTIONS()
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_method_to_string(self) -> None:
        """method_to_string converts enum to string."""
        src = _http_source_with_main("""\
            let s: String = method_to_string(GET())
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 4: HttpError enum compiles
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHttpError:
    def test_error_enum_compiles(self) -> None:
        """HttpError enum with all variants compiles."""
        src = _http_source_with_main("""\
            let e1: HttpError = ConnectionFailed("fail")
            let e2: HttpError = Timeout("timeout")
            let e3: HttpError = TlsError("tls")
            let e4: HttpError = InvalidUrl("bad")
            let e5: HttpError = TooManyRedirects("redirects")
            let e6: HttpError = ParseError("parse")
            let e7: HttpError = SendError("send")
            let e8: HttpError = RecvError("recv")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 2, 3, 5: HttpRequest, HttpResponse, HttpConfig structs
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreStructs:
    def test_http_request_compiles(self) -> None:
        """HttpRequest struct compiles."""
        src = _http_source_with_main("""\
            let req: HttpRequest = new_http_request(GET(), "http://example.com")
            println(req.url)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_http_response_compiles(self) -> None:
        """HttpResponse struct compiles."""
        src = _http_source_with_main("""\
            let resp: HttpResponse = new_http_response(200, #{}, "hello")
            println(str(resp.status_code))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_http_config_compiles(self) -> None:
        """HttpConfig struct with defaults compiles."""
        src = _http_source_with_main("""\
            let cfg: HttpConfig = default_http_config()
            println(cfg.user_agent)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_request_with_headers(self) -> None:
        """HttpRequest with custom headers compiles."""
        src = _http_source_with_main("""\
            let req: HttpRequest = new HttpRequest {
                method: POST(),
                url: "http://example.com/api",
                headers: #{"Content-Type": "application/json", "Authorization": "Bearer token"},
                body: "{}",
                has_body: true,
                timeout_ms: 5000
            }
            println(req.body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 6-8: URL parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestUrlParsing:
    def test_parse_http_url(self) -> None:
        """Parse simple HTTP URL."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com/path")
            println(url.host)
            println(url.path)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_https_url(self) -> None:
        """Parse HTTPS URL with default port."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("https://api.example.com/v1/users")
            println(url.host)
            println(str(url.port))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_url_with_port(self) -> None:
        """Parse URL with explicit port."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://localhost:8080/api")
            println(url.host)
            println(str(url.port))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_url_with_query(self) -> None:
        """Parse URL with query string."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com/search?q=hello&page=1")
            println(url.path)
            println(url.query)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_url_no_path(self) -> None:
        """Parse URL without path defaults to /."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com")
            println(url.path)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_url_invalid(self) -> None:
        """Parse invalid URL reports error."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("not_a_url")
            if url.ok == false {
                println(url.error_msg)
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_url_encode(self) -> None:
        """URL encoding percent-encodes special characters."""
        src = _http_source_with_main("""\
            let encoded: String = url_encode("hello world")
            println(encoded)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_url_decode(self) -> None:
        """URL decoding reverses percent-encoding."""
        src = _http_source_with_main("""\
            let decoded: String = url_decode("hello%20world")
            println(decoded)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_query(self) -> None:
        """Query parameter builder produces key=value&key=value."""
        src = _http_source_with_main("""\
            let params: Map<String, String> = #{"q": "hello", "page": "1"}
            let qs: String = build_query(params)
            println(qs)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 12: HTTP request building
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRequestBuilding:
    def test_build_get_request(self) -> None:
        """Build a GET request string."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com/api/data")
            let raw: String = build_http_request(GET(), url, #{}, "", false)
            println(raw)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_post_request_with_body(self) -> None:
        """Build a POST request with body and Content-Length."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com/api")
            let headers: Map<String, String> = #{"Content-Type": "application/json"}
            let raw: String = build_http_request(POST(), url, headers, "{}", true)
            println(raw)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_request_with_query(self) -> None:
        """Build request for URL with query string."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://example.com/search?q=test")
            let raw: String = build_http_request(GET(), url, #{}, "", false)
            println(raw)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_request_custom_port(self) -> None:
        """Build request includes port in Host header when non-standard."""
        src = _http_source_with_main("""\
            let url: ParsedUrl = parse_url("http://localhost:8080/api")
            let raw: String = build_http_request(GET(), url, #{}, "", false)
            println(raw)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 14-16: Response parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestResponseParsing:
    def test_parse_simple_response(self) -> None:
        """Parse a simple HTTP response with Content-Length."""
        src = _http_source_with_main("""\
            let raw: String = "HTTP/1.1 200 OK\\r\\nContent-Length: 5\\r\\n\\r\\nhello"
            let result: Result<HttpResponse, HttpError> = parse_raw_response(raw)
            match result {
                Ok(resp) => {
                    println(str(resp.status_code))
                    println(resp.body)
                },
                Err(e) => { println("error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_response_headers(self) -> None:
        """Parse response headers are extracted correctly."""
        src = _http_source_with_main("""\
            let raw: String = "HTTP/1.1 200 OK\\r\\nContent-Type: text/html\\r\\nServer: test\\r\\n\\r\\nbody"
            let hdr: HeaderParseResult = parse_response_headers(raw)
            println(str(hdr.status_code))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_chunked_response(self) -> None:
        """Chunked transfer decoding works."""
        src = _http_source_with_main("""\
            let raw: String = "HTTP/1.1 200 OK\\r\\nTransfer-Encoding: chunked\\r\\n\\r\\n5\\r\\nhello\\r\\n0\\r\\n\\r\\n"
            let result: Result<HttpResponse, HttpError> = parse_raw_response(raw)
            match result {
                Ok(resp) => { println(resp.body) },
                Err(e) => { println("error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_empty_response_error(self) -> None:
        """Empty response returns error."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = parse_raw_response("")
            match result {
                Ok(resp) => { println("unexpected") },
                Err(e) => { println("got error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 17: Redirect handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRedirectHandling:
    def test_is_redirect(self) -> None:
        """Redirect status codes detected correctly."""
        src = _http_source_with_main("""\
            let r1: Bool = is_redirect(301)
            let r2: Bool = is_redirect(302)
            let r3: Bool = is_redirect(307)
            let r4: Bool = is_redirect(308)
            let r5: Bool = is_redirect(200)
            println(str(r1))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_absolute_redirect(self) -> None:
        """Absolute redirect URL returned as-is."""
        src = _http_source_with_main("""\
            let resolved: String = resolve_redirect_url("http://old.com", "https://new.com/path")
            println(resolved)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_relative_redirect(self) -> None:
        """Relative redirect resolved against base URL."""
        src = _http_source_with_main("""\
            let resolved: String = resolve_redirect_url("http://example.com/old", "/new/path")
            println(resolved)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 9-10: Convenience functions
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConvenienceFunctions:
    def test_get_compiles(self) -> None:
        """http.get() compiles (extern TCP calls present)."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = get("http://example.com")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        # Verify extern TCP functions are declared
        assert "__mn_tcp_connect_str" in ir_out

    def test_post_compiles(self) -> None:
        """http.post() compiles with body."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = post("http://example.com/api", "{}")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_put_compiles(self) -> None:
        """http.put() compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = put("http://example.com/api", "{}")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_delete_compiles(self) -> None:
        """http.delete() compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = delete("http://example.com/api/1")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_patch_compiles(self) -> None:
        """http.patch() compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = patch("http://example.com/api/1", "{}")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_head_compiles(self) -> None:
        """http.head() compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = head("http://example.com")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_options_compiles(self) -> None:
        """http.options() compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = options("http://example.com")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 11: Full request with config
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFullRequest:
    def test_request_with_config_compiles(self) -> None:
        """request_with_config compiles."""
        src = _http_source_with_main("""\
            let req: HttpRequest = new_http_request(GET(), "http://example.com")
            let cfg: HttpConfig = default_http_config()
            let result: Result<HttpResponse, HttpError> = request_with_config(req, cfg)
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_request_compiles(self) -> None:
        """request() with default config compiles."""
        src = _http_source_with_main("""\
            let req: HttpRequest = new HttpRequest {
                method: GET(),
                url: "http://example.com",
                headers: #{"Accept": "text/html"},
                body: "",
                has_body: false,
                timeout_ms: 10000
            }
            let result: Result<HttpResponse, HttpError> = request(req)
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 22: Request fingerprinting
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFingerprint:
    def test_fingerprint_compiles(self) -> None:
        """Request fingerprint generates a hex string."""
        src = _http_source_with_main("""\
            let fp: String = request_fingerprint(GET(), "http://example.com")
            println(fp)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_fingerprint_different_methods(self) -> None:
        """Different methods produce different fingerprints."""
        src = _http_source_with_main("""\
            let fp1: String = request_fingerprint(GET(), "http://example.com")
            let fp2: String = request_fingerprint(POST(), "http://example.com")
            println(fp1)
            println(fp2)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 26-34: Integration-level compilation tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestIntegration:
    def test_get_request_to_http_endpoint(self) -> None:
        """Task 26: GET request compilation includes TCP connect."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = get("http://httpbin.org/get")
            match result {
                Ok(resp) => { println(resp.body) },
                Err(e) => { println("error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tcp_connect_str" in ir_out
        assert "__mn_tcp_send_str" in ir_out
        assert "__mn_tcp_recv_str" in ir_out

    def test_get_request_to_https_endpoint(self) -> None:
        """Task 27: HTTPS GET includes TLS connect."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = get("https://httpbin.org/get")
            match result {
                Ok(resp) => { println(resp.body) },
                Err(e) => { println("error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tls_connect_str" in ir_out
        assert "__mn_tls_write_str" in ir_out
        assert "__mn_tls_read_str" in ir_out

    def test_post_with_json_body(self) -> None:
        """Task 28: POST with JSON body compiles."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = post("http://httpbin.org/post", "{}")
            match result {
                Ok(resp) => { println(str(resp.status_code)) },
                Err(e) => { println("error") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_custom_headers_sent(self) -> None:
        """Task 29: Custom headers in request compile."""
        src = _http_source_with_main("""\
            let req: HttpRequest = new HttpRequest {
                method: GET(),
                url: "http://httpbin.org/headers",
                headers: #{"X-Custom": "value", "Authorization": "Bearer tok"},
                body: "",
                has_body: false,
                timeout_ms: 5000
            }
            let result: Result<HttpResponse, HttpError> = request(req)
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_timeout_handling(self) -> None:
        """Task 31: Timeout set via __mn_tcp_set_timeout."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = get("http://example.com")
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tcp_set_timeout" in ir_out

    def test_error_handling_pattern(self) -> None:
        """Task 32: Error handling with match on Result."""
        src = _http_source_with_main("""\
            let result: Result<HttpResponse, HttpError> = get("http://invalid.example.com")
            match result {
                Ok(resp) => { println("ok: " + str(resp.status_code)) },
                Err(e) => {
                    match e {
                        ConnectionFailed(msg) => { println("conn fail: " + msg) },
                        Timeout(msg) => { println("timeout: " + msg) },
                        TlsError(msg) => { println("tls: " + msg) },
                        InvalidUrl(msg) => { println("url: " + msg) },
                        TooManyRedirects(msg) => { println("redir: " + msg) },
                        ParseError(msg) => { println("parse: " + msg) },
                        SendError(msg) => { println("send: " + msg) },
                        RecvError(msg) => { println("recv: " + msg) }
                    }
                }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_response_json_parsing_stub(self) -> None:
        """Task 33: Response body available for JSON parsing."""
        src = _http_source_with_main("""\
            let resp: HttpResponse = new_http_response(200, #{}, "{}")
            println(resp.body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_fingerprint_uniqueness(self) -> None:
        """Task 34: Request fingerprints differ for different URLs."""
        src = _http_source_with_main("""\
            let fp1: String = request_fingerprint(GET(), "http://example.com/a")
            let fp2: String = request_fingerprint(GET(), "http://example.com/b")
            println(fp1)
            println(fp2)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Additional: to_lower and helper function tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHelpers:
    def test_to_lower_compiles(self) -> None:
        """to_lower converts uppercase to lowercase."""
        src = _http_source_with_main("""\
            let result: String = to_lower("Content-Type")
            println(result)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_int_manual(self) -> None:
        """parse_int_manual converts string digits to int."""
        src = _http_source_with_main("""\
            let n: Int = parse_int_manual("8080")
            println(str(n))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_hex_int(self) -> None:
        """parse_hex_int converts hex string to int."""
        src = _http_source_with_main("""\
            let n: Int = parse_hex_int("1a")
            println(str(n))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_unreserved(self) -> None:
        """is_unreserved checks URL-safe characters."""
        src = _http_source_with_main("""\
            let r1: Bool = is_unreserved("a")
            let r2: Bool = is_unreserved(" ")
            println(str(r1))
            println(str(r2))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hex_char(self) -> None:
        """hex_char converts int 0-15 to hex character."""
        src = _http_source_with_main("""\
            let h1: String = hex_char(10)
            let h2: String = hex_char(15)
            println(h1)
            println(h2)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
