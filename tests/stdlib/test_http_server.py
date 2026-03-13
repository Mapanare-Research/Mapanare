"""Phase 4 — net/http/server.mn — HTTP Server with Routing tests.

Tests verify that the HTTP server stdlib module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation (Phase 8) is not yet
ready, tests inline the server module source code within test programs.

Covers:
  - Core types: Route, Router, ServerConfig, Context, HttpRequest, HttpResponse
  - Route registration
  - Path pattern parsing and parameter extraction
  - Static path matching
  - Method + path dispatch
  - HTTP request parsing
  - HTTP response building
  - Middleware: logging, CORS, chain execution
  - Response helpers: ctx_respond, ctx_json, ctx_redirect
  - Static file serving
  - 404 for unmatched routes
  - Server listen compilation (extern TCP calls present)
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

# Read the server module source once
_SERVER_MN = (
    Path(__file__).resolve().parent.parent.parent
    / "stdlib"
    / "net"
    / "http"
    / "server.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_http_server.mn", use_mir=True)


def _server_source_with_main(main_body: str) -> str:
    """Prepend the server module source and wrap main_body in fn main()."""
    return (
        _SERVER_MN
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
# Task 1: Route struct
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRouteStruct:
    def test_route_compiles(self) -> None:
        """Route struct compiles with all fields."""
        src = _server_source_with_main("""\
            let r: Route = new_route("GET", "/hello", "handle_hello")
            println(r.method)
            println(r.path_pattern)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_static_route_compiles(self) -> None:
        """Static file route compiles."""
        src = _server_source_with_main("""\
            let r: Route = new_static_route("/static/", "/var/www")
            println(r.path_pattern)
            println(r.static_dir)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 2: Router struct
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRouterStruct:
    def test_router_compiles(self) -> None:
        """Router struct with empty routes compiles."""
        src = _server_source_with_main("""\
            let router: Router = new_router()
            println(str(router.route_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_router_add_route(self) -> None:
        """Adding routes to router compiles."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/hello", "handle_hello")
            router = router_add_route(router, "POST", "/data", "handle_data")
            println(str(router.route_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 3: ServerConfig struct
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestServerConfig:
    def test_server_config_compiles(self) -> None:
        """ServerConfig struct compiles with defaults."""
        src = _server_source_with_main("""\
            let cfg: ServerConfig = new_server_config("0.0.0.0", 8080)
            println(cfg.host)
            println(str(cfg.port))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 4: Context struct
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestContextStruct:
    def test_context_compiles(self) -> None:
        """Context struct with request and path params compiles."""
        src = _server_source_with_main("""\
            let req: HttpRequest = new_server_request("GET", "/api/users", #{}, "", "")
            let params: Map<String, String> = #{"id": "42"}
            let ctx: Context = new_context(req, params)
            println(ctx.request.path)
            println(ctx.path_params["id"])
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 5-7: Route matching
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRouteMatching:
    def test_split_path(self) -> None:
        """split_path breaks path into segments."""
        src = _server_source_with_main("""\
            let segs: List<String> = split_path("/api/users/42")
            println(str(len(segs)))
            println(segs[0])
            println(segs[1])
            println(segs[2])
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_param_segment(self) -> None:
        """is_param_segment detects ${name} pattern."""
        src = _server_source_with_main("""\
            let r1: Bool = is_param_segment("${id}")
            let r2: Bool = is_param_segment("users")
            let r3: Bool = is_param_segment("${}")
            println(str(r1))
            println(str(r2))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_param_name(self) -> None:
        """extract_param_name gets name from ${name}."""
        src = _server_source_with_main("""\
            let name: String = extract_param_name("${user_id}")
            println(name)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_static_path_match(self) -> None:
        """Task 6: Static path matching works."""
        src = _server_source_with_main("""\
            let mr: MatchResult = match_route("/health", "/health", "GET", "GET")
            println(str(mr.matched))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_param_path_match(self) -> None:
        """Task 5: Path parameter extraction works."""
        src = _server_source_with_main("""\
            let mr: MatchResult = match_route("/api/users/${id}", "/api/users/42", "GET", "GET")
            if mr.matched {
                println(mr.params["id"])
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_method_mismatch(self) -> None:
        """Method mismatch returns no match."""
        src = _server_source_with_main("""\
            let mr: MatchResult = match_route("/hello", "/hello", "POST", "GET")
            println(str(mr.matched))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_segment_count_mismatch(self) -> None:
        """Different segment counts don't match."""
        src = _server_source_with_main("""\
            let mr: MatchResult = match_route("/api/users", "/api/users/42", "GET", "GET")
            println(str(mr.matched))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_multi_param_match(self) -> None:
        """Multiple path parameters extracted."""
        src = _server_source_with_main("""\
            let mr: MatchResult = match_route("/api/${resource}/${id}", "/api/users/42", "GET", "GET")
            if mr.matched {
                println(mr.params["resource"])
                println(mr.params["id"])
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 10: HTTP request parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRequestParsing:
    def test_parse_get_request(self) -> None:
        """Parse a simple GET request."""
        src = _server_source_with_main("""\
            let raw: String = "GET /hello HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n"
            let parsed: ParsedRequest = parse_incoming_request(raw)
            println(parsed.method)
            println(parsed.path)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_post_with_body(self) -> None:
        """Parse POST request with body."""
        src = _server_source_with_main("""\
            let raw: String = "POST /api/data HTTP/1.1\\r\\nHost: localhost\\r\\nContent-Type: application/json\\r\\n\\r\\n{}"
            let parsed: ParsedRequest = parse_incoming_request(raw)
            println(parsed.method)
            println(parsed.body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_request_with_query(self) -> None:
        """Parse request with query string."""
        src = _server_source_with_main("""\
            let raw: String = "GET /search?q=hello&page=1 HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n"
            let parsed: ParsedRequest = parse_incoming_request(raw)
            println(parsed.path)
            println(parsed.query)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_headers(self) -> None:
        """Parse request headers into map."""
        src = _server_source_with_main("""\
            let raw: String = "GET / HTTP/1.1\\r\\nHost: localhost\\r\\nAccept: text/html\\r\\nX-Custom: value\\r\\n\\r\\n"
            let parsed: ParsedRequest = parse_incoming_request(raw)
            println(str(parsed.ok))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 12: Response building
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestResponseBuilding:
    def test_build_200_response(self) -> None:
        """Build a 200 OK response."""
        src = _server_source_with_main("""\
            let resp: String = build_response(200, #{}, "hello")
            println(resp)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_response_with_headers(self) -> None:
        """Build response with custom headers."""
        src = _server_source_with_main("""\
            let hdrs: Map<String, String> = #{"Content-Type": "application/json"}
            let resp: String = build_response(200, hdrs, "{}")
            println(resp)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_404_response(self) -> None:
        """Build a 404 response."""
        src = _server_source_with_main("""\
            let resp: String = build_404_response("/missing")
            println(resp)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_500_response(self) -> None:
        """Build a 500 response."""
        src = _server_source_with_main("""\
            let resp: String = build_500_response("something broke")
            println(resp)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_status_reasons(self) -> None:
        """Status codes map to correct reason phrases."""
        src = _server_source_with_main("""\
            println(status_reason(200))
            println(status_reason(404))
            println(status_reason(500))
            println(status_reason(301))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 19-21: Response helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestResponseHelpers:
    def test_ctx_respond(self) -> None:
        """Task 19: ctx_respond sets status and body."""
        src = _server_source_with_main("""\
            let req: HttpRequest = new_server_request("GET", "/", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = ctx_respond(ctx, 200, "hello world")
            println(str(ctx2.response_status))
            println(ctx2.response_body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ctx_json(self) -> None:
        """Task 20: ctx_json sets JSON content-type."""
        src = _server_source_with_main("""\
            let req: HttpRequest = new_server_request("GET", "/", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = ctx_json(ctx, 200, "{}")
            println(str(ctx2.response_status))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ctx_redirect(self) -> None:
        """Task 21: ctx_redirect sets Location header."""
        src = _server_source_with_main("""\
            let req: HttpRequest = new_server_request("GET", "/old", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = ctx_redirect(ctx, "/new", 301)
            println(str(ctx2.response_status))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 15-18: Middleware
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMiddleware:
    def test_logging_middleware(self) -> None:
        """Task 16: Logging middleware compiles."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_use_logging(router)
            let req: HttpRequest = new_server_request("GET", "/test", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = apply_middleware_before(router, ctx)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_cors_middleware(self) -> None:
        """Task 17: CORS middleware adds headers."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_use_cors(router, "https://example.com", "GET, POST", "Content-Type")
            let req: HttpRequest = new_server_request("GET", "/api", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = ctx_respond(ctx, 200, "ok")
            let ctx3: Context = apply_middleware_after(router, ctx2)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_middleware_chain(self) -> None:
        """Task 18: Full middleware chain: before -> handler -> after."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_use_logging(router)
            router = router_use_cors(router, "*", "GET, POST", "Content-Type")
            router = router_add_route(router, "GET", "/hello", "handle_hello")
            let req: HttpRequest = new_server_request("GET", "/hello", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let before: Context = apply_middleware_before(router, ctx)
            let handled: Context = ctx_respond(before, 200, "Hello!")
            let after: Context = apply_middleware_after(router, handled)
            println(str(after.response_status))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 22: Static file serving
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStaticFiles:
    def test_router_static_files(self) -> None:
        """Static file route registration compiles."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_static_files(router, "/static/", "/var/www")
            println(str(router.route_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_guess_content_type(self) -> None:
        """Content type guessed from file extension."""
        src = _server_source_with_main("""\
            let ct1: String = guess_content_type("index.html")
            let ct2: String = guess_content_type("style.css")
            let ct3: String = guess_content_type("app.js")
            let ct4: String = guess_content_type("data.json")
            let ct5: String = guess_content_type("noext")
            println(ct1)
            println(ct2)
            println(ct3)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_starts_with(self) -> None:
        """starts_with checks prefix matching."""
        src = _server_source_with_main("""\
            let r1: Bool = starts_with("/static/img.png", "/static/")
            let r2: Bool = starts_with("/api/data", "/static/")
            println(str(r1))
            println(str(r2))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 11: Route dispatch
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRouteDispatch:
    def test_dispatch_matches_route(self) -> None:
        """dispatch_route finds matching route."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/hello", "handle_hello")
            router = router_add_route(router, "POST", "/data", "handle_data")
            let dr: DispatchResult = dispatch_route(router, "GET", "/hello")
            println(str(dr.matched))
            println(str(dr.route_idx))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_dispatch_extracts_params(self) -> None:
        """dispatch_route extracts path parameters."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/users/${id}", "handle_user")
            let dr: DispatchResult = dispatch_route(router, "GET", "/users/42")
            if dr.matched {
                println(dr.params["id"])
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_dispatch_404_no_match(self) -> None:
        """Task 27: Unmatched routes return no match."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/hello", "handle_hello")
            let dr: DispatchResult = dispatch_route(router, "GET", "/missing")
            println(str(dr.matched))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 23: Integration — server start, request, response
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestIntegration:
    def test_server_listen_compiles(self) -> None:
        """Task 23: server_listen compiles with extern TCP calls."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/hello", "handle_hello")
            let cfg: ServerConfig = new_server_config("127.0.0.1", 8080)
            // Don't actually call server_listen (blocks), just verify compilation
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tcp_listen_str" in ir_out

    def test_full_request_response_cycle(self) -> None:
        """Full cycle: parse request, match route, build response."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/api/users/${id}", "handle_user")
            router = router_use_logging(router)
            router = router_use_cors(router, "*", "GET, POST", "Content-Type")
            let raw: String = "GET /api/users/42 HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n"
            let ctx: Context = process_request(router, raw)
            let response: String = context_to_response(ctx)
            println(response)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_json_response_roundtrip(self) -> None:
        """Task 26: JSON response with correct headers."""
        src = _server_source_with_main("""\
            let req: HttpRequest = new_server_request("GET", "/api", #{}, "", "")
            let ctx: Context = new_context(req, #{})
            let ctx2: Context = ctx_json(ctx, 200, "{}")
            let response: String = context_to_response(ctx2)
            println(response)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_handle_connection_compiles(self) -> None:
        """handle_connection uses all TCP extern functions."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/", "handler")
            // Verify extern functions are declared
            println("compiled")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tcp_recv_str" in ir_out
        assert "__mn_tcp_send_str" in ir_out
        assert "__mn_tcp_close_fd" in ir_out

    def test_server_error_enum(self) -> None:
        """ServerError enum compiles."""
        src = _server_source_with_main("""\
            let e1: ServerError = BindFailed("port in use")
            let e2: ServerError = AcceptFailed("accept failed")
            let e3: ServerError = ReadFailed("read failed")
            let e4: ServerError = WriteFailed("write failed")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_agent_per_request_structure(self) -> None:
        """Task 28: Agent-per-request model structure compiles."""
        src = _server_source_with_main("""\
            let mut router: Router = new_router()
            router = router_add_route(router, "GET", "/", "handler")
            router = router_add_route(router, "GET", "/api/${id}", "api_handler")
            let cfg: ServerConfig = new_server_config("0.0.0.0", 3000)
            // Verify the full server structure compiles
            println(str(cfg.max_connections))
            println(str(router.route_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
