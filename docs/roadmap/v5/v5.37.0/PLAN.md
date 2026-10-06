# v5.37.0 — Ht.\* — HTTP server completeness

**Status:** PLANNING
**Type:** Stdlib polish + new features. Builds on the existing
HTTP server in `stdlib/http/` and the native TCP/TLS runtime.
**Breaking:** No, except that route-handler signatures may need
small adjustments (covered by formatter migration).
**Prerequisite:** v5.36.0 shipped (JSON serde — needed for
auto-deserialize of request bodies into typed handler params).
**Estimated effort:** 1–2 sessions. ~1500 LOC `.mn`.

---

## Why this exists

The existing HTTP server module accepts connections, parses
requests, and writes responses, but it's missing the features
real apps need:

1. **Routing.** Currently a flat `if path == "/foo"` chain in
   user code. No path parameters, no wildcards, no method
   dispatch.
2. **Middleware.** No way to compose cross-cutting concerns
   (logging, auth, rate-limiting, body parsing).
3. **WebSockets.** No upgrade support. Real-time apps can't ship.
4. **Streaming responses.** Server reads/writes whole
   request/response into memory; can't stream a large file or a
   generated event stream.

This is item #4 of the stdlib gap-close arc and the largest
single stdlib release in v5.x — HTTP is a wide surface.

---

## Goals

1. **Ht.1** — Router with path parameters and wildcards:
   `router.get("/users/:id", handler)`, `router.post("/upload/*",
   handler)`.
2. **Ht.2** — Middleware chain: `app.use(logger).use(auth).get(...)`.
   Type signature: `fn(Request, Next) -> Response`.
3. **Ht.3** — WebSocket upgrade and bidirectional message API.
4. **Ht.4** — Streaming responses: `Response::stream(stream:
   Stream<Bytes>)` for chunked encoding; `Response::sse(stream:
   Stream<SseEvent>)` for Server-Sent Events.
5. **Ht.5** — Typed handler shorthand: `app.post("/users",
   fn(req: Request, body: User) -> Response { ... })` —
   auto-deserialize body via Js.4 reflection serde.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ht.1** | HIGH | **Router in `stdlib/http/router.mn`.** Trie-based path matcher. Path patterns: literal segments (`/users`), parameters (`/users/:id`), wildcards (`/static/*path`). Method dispatch: `router.get / post / put / delete / patch / head / options`. `router.match(method, path)` returns `Option<(Handler, Map<String, String>)>` for the param bindings. ~400 LOC. | 5h |
| **Ht.2** | HIGH | **Middleware in `stdlib/http/middleware.mn`.** `type Middleware = fn(Request, Next) -> Response` where `Next = fn(Request) -> Response`. App composition: `app.use(m1).use(m2).get(path, handler)` builds a chain that calls `m1(req, fn(r){m2(r, fn(r2){handler(r2)})})`. Built-in middlewares: `logger`, `cors`, `body_limit`, `request_id`. ~250 LOC. | 4h |
| **Ht.3** | HIGH | **WebSocket support in `stdlib/http/ws.mn`.** RFC 6455 frame format. Server-side: `ws_upgrade(req: Request) -> Result<WebSocket, HttpError>`. `WebSocket` API: `send_text / send_binary / send_ping / receive() -> Result<WsMessage, _> / close()`. Use existing TLS sockets for `wss://`. ~500 LOC including handshake + frame parsing. | 6h |
| **Ht.4** | MEDIUM | **Streaming responses in `stdlib/http/response.mn`.** `Response::stream(stream: Stream<Bytes>)` writes chunked transfer encoding. `Response::sse(stream: Stream<SseEvent>)` writes Server-Sent Events with proper `Content-Type: text/event-stream`, `data: ...\n\n` framing, optional `id:` and `event:` fields. ~150 LOC. | 2h |
| **Ht.5** | MEDIUM | **Typed handler shorthand.** Compiler/parser sugar: when a handler signature is `fn(req: Request, body: T) -> Response` and `T != Unit`, auto-deserialize JSON body via Js.4. Errors return `400 Bad Request` automatically. Detected at handler registration time, not call site (lookup table indexed by handler-type-signature). ~80 LOC `.mn` + ~30 LOC compiler glue. | 2h |
| **Ht.6** | HIGH (gate) | **Tests in `stdlib/http/tests/`.** Integration tests starting a server on a random port and hitting it with the existing HTTP client: `test_router.mn` (matches param/wildcard/method), `test_middleware.mn` (chain order, short-circuit), `test_websocket.mn` (echo server with text + binary frames + ping/pong + close), `test_streaming.mn` (chunked encoding, SSE), `test_typed_handler.mn` (good body, malformed body returns 400). | 4h |
| **Ht.7** | LOW | **Examples** at `examples/http/`. Update existing demo to use new router/middleware. Add `examples/http/websocket-chat.mn` (multi-client chat over WebSocket) and `examples/http/sse-stream.mn` (server-sent event firehose). | 2h |
| **Ht.8** | LOW | **Doc page** at `docs/stdlib/http.md`. Cookbook covering all the patterns. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.36.0 HEAD clean; Js.4 reflection
  serde verified working.
- **Phase 1** — Ht.1 router. Self-contained; build tests against
  it before middleware lands.
- **Phase 2** — Ht.2 middleware. Tests against the trivial chain.
- **Phase 3** — Ht.3 WebSocket. Largest single item.
- **Phase 4** — Ht.4 streaming.
- **Phase 5** — Ht.5 typed handler sugar.
- **Phase 6** — Ht.6 round out tests; Ht.7 examples; Ht.8 docs.
- **Phase 7** — Bump + tag.

---

## Out of scope

- **HTTP/2 and HTTP/3.** Specific user demand can drive these
  later; HTTP/1.1 covers nearly all current use cases.
- **Compiled router optimization (regex / radix trie).** Trie of
  path segments is fast enough for v5.x; serious benchmarking
  later if needed.
- **Built-in session / cookie management.** Downstream package
  territory; stdlib ships request/response only.
- **Built-in CSRF / auth.** Downstream packages.
- **Server framework on top.** Like Express middleware ecosystem;
  downstream.
- **Tn.1 / older carries** — assumed closed by v5.35.x; if not,
  this release is blocked.

---

## Risk

1. **WebSocket frame parser bugs.** RFC 6455 has gotchas —
   masking, fragmentation, control-frame size limits, UTF-8
   validation in TEXT frames. Mitigation: Ht.3 tests use the
   Autobahn test suite subset (or hand-port relevant cases) —
   ~50 fixture-driven cases covering edges.
2. **Middleware short-circuit semantics.** A middleware that
   returns a Response without calling `next` should bypass the
   rest of the chain. Mitigation: explicit test in Ht.6 (auth
   middleware that returns 401 without calling next; downstream
   handler is never invoked).
3. **Router trie corner cases.** Overlapping patterns
   (`/users/:id` and `/users/me`) — `me` should win as a literal,
   `:id` matches everything else. Mitigation: priority is
   "literal > parameter > wildcard"; document and lock with
   tests.
4. **Streaming responses + middleware.** A logger middleware
   that records response status + size needs to handle streams
   without buffering them. Mitigation: middleware sees a
   `Response::Stream` variant explicitly; logger records "stream
   started" / "stream ended N bytes" rather than buffering.

---

## Success criteria

- ✅ `app.get("/users/:id", handler)` routes correctly with
  param binding.
- ✅ Middleware chain composes; `app.use(logger).use(auth)` calls
  in registration order; auth short-circuit prevents handler.
- ✅ WebSocket echo server passes a smoke test with text +
  binary frames, ping/pong, clean close.
- ✅ Server-Sent Events demo streams 1000 events without
  buffering.
- ✅ Typed handler sugar: POST with valid JSON body deserializes
  to `User` struct; malformed body returns 400.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "no production HTTP story" gap. Real apps can ship.

**Inherits to v5.38.0:**
- macOS notarization, named-tzdb, Pg/MySQL drivers (LOW).
- HTTP/2 + HTTP/3 (new LOW; demand-driven).
- Session / cookie / CSRF / auth (downstream package
  candidates).
