# `stdlib/net/http/router.mn` — App, Router, Middleware

Reference for v5.37.0 Ht.1 + Ht.2 + Ht.4 (router, middleware, streaming
encoders).

`stdlib/net/http/router.mn` ships an opt-in `App` container that bundles
a path-pattern router with a registration-table middleware list. The
legacy `stdlib/net/http/server.mn` `Router` (string-named handlers,
`${name}` syntax) is preserved unchanged — existing apps keep working.

## Quick reference

| Symbol | What it does |
| --- | --- |
| `new_app() -> App` | Empty app — no routes, no middleware. |
| `app_get(app, "/path", "handler_name") -> App` | Register a GET handler. (`app_post`, `app_put`, `app_delete`, `app_patch`, `app_head`, `app_options` for the other verbs.) |
| `app_use(app, mw) -> App` | Append a middleware to the chain. |
| `app_match(app, method, path) -> MatchedRoute` | Resolve a request to a handler name + bound params. |
| `app_pick(app, method, path) -> DispatchPick` | Convenience: returns either `Picked(MatchedRoute)` or `Default(Response)` (404 / 405). |
| `match_param(m, "name") -> String` | Look up a bound path parameter. |
| `mw_logger() / mw_cors(...) / mw_body_limit(n) / mw_request_id() / mw_custom("name")` | Built-in middleware constructors. |

## Path patterns

Three segment kinds:

- **Literal** — `/users` matches exactly `users`.
- **Parameter** — `:id` matches one segment, binds the segment text to
  parameter name `id`. Lookup via `match_param(m, "id")`.
- **Wildcard** — `*path` captures the rest of the request path
  (including `/`s). Must be terminal.

Priority on overlap: **literal > parameter > wildcard**. The router
sorts on registration-time specificity (literal segments score 2,
parameters 1, wildcards 0). Registration order tie-breaks within the
same specificity class.

```mn
let mut app: App = new_app()
app = app_get(app, "/users/me", "h_me")          // specificity 4
app = app_get(app, "/users/:id", "h_id")         // specificity 3
app = app_get(app, "/static/*path", "h_static")  // specificity 2

// A request to /users/me hits h_me.
// A request to /users/42 hits h_id, with params_kv ["id", "42"].
// A request to /static/css/main.css hits h_static, with
//   params_kv ["path", "css/main.css"].
```

## Middleware

Built-in middleware variants:

```mn
| Logger
| Cors(origins, methods, headers)
| BodyLimit(max_bytes)
| RequestId
| Custom(name)
```

Each has well-defined pre-handler and/or post-handler effects:

| Middleware | Pre-handler | Post-handler |
| --- | --- | --- |
| `Logger` | logs `[http] METHOD PATH` | logs `[http] -> STATUS` |
| `Cors(o, m, h)` | (no-op) | injects `Access-Control-Allow-{Origin,Methods,Headers}` |
| `BodyLimit(n)` | short-circuits with **413** when `len(req.body) > n` | (no-op) |
| `RequestId` | mints a 32-char hex id when `req.request_id` is empty | echoes `X-Request-Id: <id>` |
| `Custom(name)` | application-supplied (see below) | application-supplied |

Wire them up:

```mn
let mut app: App = new_app()
app = app_use(app, mw_request_id())
app = app_use(app, mw_logger())
app = app_use(app, mw_body_limit(1048576))
app = app_use(app, mw_cors("*", "GET, POST, OPTIONS", "Content-Type, Authorization"))
app = app_get(app, "/api/users/:id", "get_user")
```

### Short-circuit semantics

A middleware that returns a `MwShortCircuit(response)` from
`app_run_before` bypasses the rest of the chain AND the handler. The
short-circuit response is what gets written. Example:

```mn
let req: Request = new_request("POST", "/upload", "...giant body...")
let outcome: MwOutcome = app_run_before(app, req)
match outcome {
    MwContinue(req2) => {
        // Run handler, then app_run_after.
        let resp: Response = my_handler_dispatch(req2)
        let final: Response = app_run_after(app, req2, resp)
        // Write `final` to socket.
    },
    MwShortCircuit(resp) => {
        // Write `resp` directly. Handler never runs. Subsequent
        // middleware never runs.
        let final: Response = app_run_after(app, req, resp)
        // (After-chain still runs so logging / CORS etc. still get to
        // observe the short-circuit response.)
    }
}
```

### Custom middleware

Mapanare's stdlib does not support invoking function-value parameters
in v5.37.0 (see CHANGELOG deviation note). The user-extensible
middleware path is the **registration table**: `Custom(name)`
delegates dispatch to a user-written switch keyed by string name.
Apps that don't use `Custom` need not implement anything.

```mn
fn dispatch_custom_middleware_before(name: String, req: Request) -> MwOutcome {
    if name == "auth" {
        if req_has_valid_token(req) == false {
            return MwShortCircuit(response_text(401, "Unauthorized"))
        }
        return MwContinue(req)
    }
    return MwContinue(req)
}
```

## Headers — alternating-kv lists

Both `Request.headers` and the header field of every `Response` variant
are `List<String>` in alternating key/value form (`["Content-Type",
"application/json", "Cache-Control", "no-cache"]`).

This is a v5.x deviation from `Map<String, String>` for header storage.
The Map form is currently affected by a drop-glue bug that frees maps
stored in returned struct/enum payloads before the caller can read
them (see CHANGELOG `### Changed`). Lists pass through correctly.

Use the `hdr_get` / `hdr_set` / `hdr_has` helpers:

```mn
let h: List<String> = ["Content-Type", "text/plain"]
let v: String = hdr_get(h, "Content-Type")  // "text/plain"
let h2: List<String> = hdr_set(h, "Content-Type", "application/json")
```

For Responses:

```mn
let r: Response = response_text(200, "hi")
let r2: Response = response_with_header(r, "X-Foo", "bar")
let v: String = response_get_header(r2, "X-Foo")  // "bar"
```

## Streaming responses

`stdlib/net/http/streaming.mn` ships chunked-encoding and SSE
encoders. The encoders produce wire-format strings; an HTTP server
loop (e.g. one built on top of `stdlib/net/http/server.mn`'s TCP
primitives) writes the resulting string to the client socket.

### Chunked transfer encoding

```mn
let chunks: List<String> = ["first chunk", "second chunk", "third"]
let h: List<String> = ["Content-Type", "text/plain"]
let wire: String = build_chunked_response(200, h, chunks)

// `wire` is a complete HTTP/1.1 response:
//   HTTP/1.1 200 OK
//   Transfer-Encoding: chunked
//   Content-Type: text/plain
//
//   b\r\n
//   first chunk\r\n
//   c\r\n
//   second chunk\r\n
//   5\r\n
//   third\r\n
//   0\r\n
//   \r\n
__mn_tcp_send_str(client_fd, wire)
```

`build_chunked_response` automatically:

- adds `Transfer-Encoding: chunked`
- drops any pre-existing `Content-Length` (cannot coexist with chunked
  per RFC 7230 §3.3.1)
- skips zero-length chunks (they would prematurely terminate the body)

### Server-Sent Events

```mn
let mut e1: SseLite = new_sse_lite("hello")
e1 = sse_lite_with_id(e1, "1")
let mut e2: SseLite = new_sse_lite("world")
e2 = sse_lite_with_type(e2, "greeting")
let events: List<SseLite> = [e1, e2]
let body: String = sse_lite_encode_stream(events, 3000)

// body is:
//   retry: 3000
//
//   id: 1
//   data: hello
//
//   event: greeting
//   data: world
//
let h: List<String> = sse_response_headers()
// h = ["Content-Type", "text/event-stream",
//      "Cache-Control", "no-cache",
//      "X-Accel-Buffering", "no"]
```

Multi-line `data` payloads emit one `data:` prefix per line (per the
SSE spec — `\n` in the payload is the line separator).

### Streaming-aware logger

A logger middleware that records response sizes must NOT buffer
streamed responses. Pattern-match on the Response variant:

```mn
fn record_size(resp: Response) {
    match resp {
        ResponseBody(_, _, body) => { print("body=" + rt_int_to_str(len(body))) },
        ResponseStream(_, _, _) => { print("stream started") },
        ResponseSse(_, _, _) => { print("sse stream started") }
    }
}
```

The built-in `Logger` middleware records only `[http] -> STATUS` and
deliberately does not measure body size — pattern-matching across the
three variants is left to application code.

### v5.37.0 streaming deviation

v5.37.0 ships *encoders* (produce wire-format strings) rather than a
true bounded-RSS streaming writer. The existing TCP send primitive
`__mn_tcp_send_str(fd, data: String)` accepts whole strings; a real
streaming writer needs `__mn_tcp_send_bytes(fd, ptr, len)` plus a
chunk-pump driver. That C-runtime addition is deferred to v5.38.0
(Ht.4.B). Encoders compose cleanly: the wire format is identical;
only the driver loop changes.

## WebSocket

WebSocket support is **already present** in `stdlib/net/websocket.mn`
(client + server, RFC 6455, masking, fragmentation, ping/pong,
graceful close, `wss://` over TLS). v5.37.0 documents the integration
path; no new `stdlib/net/http/ws.mn` file ships (would have been a
duplicate). The Autobahn fixture corpus is deferred to v5.38.0 (Ht.3.B).

### Server upgrade flow

Concatenate `stdlib/net/websocket.mn` into your application. The HTTP
server's request handler dispatches the upgrade:

```mn
// In your handle_request body, after parsing the Request:
if is_websocket_upgrade(parsed_headers_map) {
    let upgrade: Result<WsConnection, WsError> = ws_accept_upgrade(client_fd, parsed_headers_map)
    match upgrade {
        Ok(conn) => {
            // Run an echo loop, or your own message-pump:
            let r: Result<Int, WsError> = ws_echo_loop(conn)
        },
        Err(e) => {
            // Respond 400 Bad Request — handshake failed.
        }
    }
    return  // socket has been promoted to WebSocket; do NOT write an HTTP response.
}
// ... otherwise continue with normal HTTP routing.
```

`is_websocket_upgrade` validates the `Upgrade: websocket` +
`Connection: Upgrade` + `Sec-WebSocket-Version: 13` headers.
`ws_accept_upgrade` computes the `Sec-WebSocket-Accept` reply (SHA-1
of client key + magic GUID, base64-encoded), writes the 101 Switching
Protocols response, and returns a `WsConnection` you can `ws_recv` /
`ws_send` against.

### Frame parser

`stdlib/net/websocket.mn` handles:

- Masking (server-side: client→server frames are XOR-masked with a
  4-byte key; server→client frames are sent unmasked).
- Fragmentation (`ws_recv_full` defragments TEXT/BINARY messages
  spanning multiple CONTINUATION frames).
- Control-frame size cap (PING/PONG/CLOSE payload ≤125 bytes; larger
  closes the connection with code 1002 Protocol Error).
- UTF-8 validation in TEXT messages (rejected at message boundary
  with code 1007).

### `wss://`

The TLS path is wired through the same OpenSSL-via-dlopen surface as
the HTTPS client. Pass a TLS-wrapped fd into `ws_accept_upgrade`; the
return `WsConnection.is_tls=true` carries the TLS context for
subsequent `ws_send` / `ws_recv` calls.

## What's NOT in v5.37.0

Tracked for v5.38.0+:

- **Ht.3.B** — Autobahn RFC 6455 fixture corpus (~50 cases). Existing
  WebSocket implementation passes manual smoke; fixture-locked
  conformance is deferred. The frame parser is in production use; the
  v5.37.0 release notes do not claim "RFC-conformant" without the
  fixture suite.
- **Ht.4.B** — bounded-RSS streaming writer. Encoders ship today;
  pump driver waits on `__mn_tcp_send_bytes(fd, ptr, len)` C-runtime
  addition.
- **Ht.5** — typed handler shorthand (`fn(req, body: T) -> Response`
  with auto-deserialization via Js.4 `from_json<T>`). Blocked on
  Js.4.B — `from_json<T>` builds but SEGVs at runtime in field
  extraction. Lifts when v5.36.x ships the drop-glue fix.
- **Closure-chain middleware** (`type Middleware = fn(Request, Next)
  -> Response`). Blocked on indirect calls through fn-typed
  parameters segfaulting in the Python LLVM emitter / producing
  invalid IR in stage1. Same root cause as v5.35.0's deferred
  `transaction<T>(f: fn() -> ...)` shape. The registration-table
  shape ships today and stays back-compat when the closure form
  lands.
- **HTTP/2, HTTP/3** — downstream packages.
- **Session / cookie / CSRF / OAuth** — also downstream packages on
  top of v5.37.0's primitives.

## Migration from `stdlib/net/http/server.mn`

The legacy `Router` / `match_route` / `${name}` API in
`stdlib/net/http/server.mn` is **untouched**. Existing pytest coverage
in `tests/stdlib/test_http_server.py` keeps passing. v5.37.0's `App`
is a separate, opt-in surface — pick whichever fits your code:

| Concern | `server.mn` Router (legacy) | `router.mn` App (v5.37.0) |
| --- | --- | --- |
| Path syntax | `/users/${id}` | `/users/:id` and `/static/*path` |
| Handler dispatch | string-named (`handler_name: String`) | string-named (same — no fn-values yet) |
| Method dispatch | per-route + a 4-flag pattern matcher | proper method table on each pattern |
| Middleware | `has_logging` + `has_cors` flags on Router | `Middleware` enum + `app_use` chain |
| Headers | `Map<String, String>` | `List<String>` alternating-kv |
| Streaming | (none) | `chunked_encode` + SSE encoders |
| Param lookup | `mr.params["id"]` (Map) | `match_param(m, "id")` (List<String> kv) |

Both surfaces coexist in the same project. There is no automatic
bridge between them; if you want CORS preflights from `App` and
static-file serving from the legacy `Router`, you compose them at the
`handle_connection` layer manually.
