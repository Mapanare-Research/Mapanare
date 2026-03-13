# Mapanare v0.9.0 — "Connected"

> v0.8.0 closed the LLVM backend gap and expanded the C runtime with networking,
> file I/O, and event loop primitives. v0.9.0 builds on that foundation to give
> Mapanare programs the ability to **talk to the outside world** — with stdlib
> modules written in `.mn`, compiled natively. No Python at runtime.
>
> Core theme: **Native stdlib in Mapanare. One import, one module, no fragmentation.**

---

## Scope Rules

1. **Stdlib in `.mn`** — every new module is written in Mapanare and compiled via LLVM
2. **C runtime as foundation** — OS-level primitives (sockets, TLS, file I/O) from v0.8.0 Phase 6; everything above is pure Mapanare
3. **No Python runtime** — stdlib modules must NOT depend on Python runtime packages
4. **Cross-module compilation** — LLVM must resolve imports across `.mn` files and link into a single binary
5. **Test natively** — every test runs on the LLVM backend, not Python
6. **One import, done** — each module covers its full domain (no `requests` vs `urllib3` vs `httpx` fragmentation)

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Estimated Effort |
|-------|------|--------|-----------------|
| 1 | `encoding/json.mn` — JSON Parser/Serializer | `Not Started` | Large — recursive descent parser, typed deser, streaming |
| 2 | `encoding/csv.mn` — CSV Parser | `Not Started` | Medium — delimiter-based parser, Dato integration |
| 3 | `net/http.mn` — Unified HTTP Client | `Not Started` | X-Large — full HTTP/1.1 client on C runtime TCP/TLS |
| 4 | `net/http/server.mn` — HTTP Server with Routing | `Not Started` | X-Large — route dispatch, middleware, agent-per-request |
| 5 | `net/websocket.mn` — WebSocket Client + Server | `Not Started` | Large — RFC 6455, upgrade from HTTP server |
| 6 | `crypto.mn` — Cryptographic Primitives | `Not Started` | Medium — FFI to OpenSSL/libsodium |
| 7 | `text/regex.mn` — Regular Expressions | `Not Started` | Large — NFA/DFA engine or PCRE2 FFI |
| 8 | Cross-Module LLVM Compilation | `Not Started` | X-Large — multi-file LLVM linking, import resolution |
| 9 | Validation & Release | `Not Started` | Medium — integration tests, benchmarks, docs |

---

## Phase 1 — `encoding/json.mn` — JSON Parser/Serializer
**Priority:** CRITICAL — JSON is the foundation for HTTP, config, and data interchange

A recursive descent JSON parser written entirely in Mapanare. No external dependencies.
Uses C runtime string primitives from v0.8.0.

### Core Types

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `JsonValue` enum: `Null`, `Bool(Bool)`, `Int(Int)`, `Float(Float)`, `Str(String)`, `Array(List<JsonValue>)`, `Object(Map<String, JsonValue>)` | `[ ]` | Tagged union, recursive |
| 2 | Define `JsonError` struct: `message: String`, `line: Int`, `col: Int` | `[ ]` | Position tracking for diagnostics |

### Parser

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3 | Implement JSON lexer: tokenize `{`, `}`, `[`, `]`, `:`, `,`, strings, numbers, `true`, `false`, `null` | `[ ]` | Character-by-character, handle escape sequences |
| 4 | `json.decode_value(input: String, pos: Int) -> Result<(JsonValue, Int), JsonError>` | `[ ]` | Recursive descent: dispatch on first char |
| 5 | Parse string values with escape handling (`\"`, `\\`, `\/`, `\n`, `\t`, `\uXXXX`) | `[ ]` | Unicode escape → UTF-8 encoding |
| 6 | Parse number values (integer + float, sign, exponent notation) | `[ ]` | `1`, `-3.14`, `2.5e10` |
| 7 | Parse arrays: `[value, value, ...]` | `[ ]` | Recursive via `decode_value` |
| 8 | Parse objects: `{"key": value, ...}` | `[ ]` | Keys must be strings |
| 9 | Whitespace handling (spaces, tabs, newlines between tokens) | `[ ]` | Skip helper function |
| 10 | Top-level `json.decode(input: String) -> Result<JsonValue, JsonError>` | `[ ]` | Calls `decode_value`, verifies no trailing content |

### Typed Deserialization

| # | Task | Status | Notes |
|---|------|--------|-------|
| 11 | `json.decode_to<T>(input: String) -> Result<T, JsonError>` — struct deserialization | `[ ]` | Requires compile-time struct field introspection |
| 12 | `json.decode_to<List<T>>(input: String)` — typed array deserialization | `[ ]` | Recursive type param handling |
| 13 | Handle `Option<T>` fields (missing key → `None`, `null` → `None`) | `[ ]` | |

### Serializer

| # | Task | Status | Notes |
|---|------|--------|-------|
| 14 | `json.encode(value: JsonValue) -> String` — serialize to JSON string | `[ ]` | Recursive, escape special chars |
| 15 | `json.encode_pretty(value: JsonValue, indent: Int) -> String` — pretty-print | `[ ]` | Indentation tracking per nesting level |
| 16 | `json.encode_struct<T>(value: T) -> String` — serialize struct to JSON | `[ ]` | Field name → JSON key |

### Streaming Parser

| # | Task | Status | Notes |
|---|------|--------|-------|
| 17 | `json.stream_parse(input: String) -> Stream<JsonEvent>` — SAX-style events | `[ ]` | Events: `StartObject`, `EndObject`, `StartArray`, `EndArray`, `Key(String)`, `Value(JsonValue)` |
| 18 | Memory-efficient: does not build full tree for streaming use | `[ ]` | Uses stream primitives from v0.8.0 |

### Schema Validation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 19 | `json.validate(value: JsonValue, schema: JsonSchema) -> Result<Void, List<JsonError>>` | `[ ]` | Type checks, required fields, min/max |
| 20 | Define `JsonSchema` struct: type constraints, required fields, nested schemas | `[ ]` | Subset of JSON Schema spec |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 21 | Parse primitives: `null`, `true`, `false`, integers, floats, strings | `[ ]` | |
| 22 | Parse nested structures: arrays of objects, objects with arrays | `[ ]` | |
| 23 | Parse edge cases: empty object `{}`, empty array `[]`, unicode escapes | `[ ]` | |
| 24 | Error cases: unterminated string, trailing comma, invalid number | `[ ]` | |
| 25 | Round-trip: `decode(encode(value)) == value` for all JSON types | `[ ]` | |
| 26 | Streaming parser produces correct event sequence | `[ ]` | |
| 27 | Typed deserialization into Mapanare structs | `[ ]` | |
| 28 | Performance: parse 1MB JSON file under reasonable time | `[ ]` | Benchmark vs Python json module |

**Done when:** `let data = json.decode("{\"name\": \"Mapanare\", \"version\": 9}"); println(data["name"])`
compiles and runs natively via LLVM. Round-trip encode/decode preserves values.

---

## Phase 2 — `encoding/csv.mn` — CSV Parser
**Priority:** MEDIUM — enables Dato integration, data processing workflows

### Parser

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `CsvRow` type: `List<String>` | `[ ]` | |
| 2 | Define `CsvTable` struct: `headers: List<String>`, `rows: List<CsvRow>` | `[ ]` | |
| 3 | Define `CsvError` struct: `message: String`, `line: Int` | `[ ]` | |
| 4 | Define `CsvConfig` struct: `delimiter: String`, `quote: String`, `has_headers: Bool` | `[ ]` | Default: comma, double-quote, true |
| 5 | `csv.read(path: String) -> Result<CsvTable, CsvError>` — read file, parse all rows | `[ ]` | Uses `__mn_file_open`/`__mn_file_read` from C runtime |
| 6 | `csv.read_with(path: String, config: CsvConfig) -> Result<CsvTable, CsvError>` | `[ ]` | Custom delimiter/quoting |
| 7 | Handle quoted fields with embedded delimiters and newlines | `[ ]` | RFC 4180 compliance |
| 8 | Handle escaped quotes (`""` inside quoted field) | `[ ]` | |

### Writer

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | `csv.write(data: CsvTable, path: String) -> Result<Void, CsvError>` | `[ ]` | Quote fields containing delimiter/newline |
| 10 | `csv.write_with(data: CsvTable, path: String, config: CsvConfig) -> Result<Void, CsvError>` | `[ ]` | Custom delimiter |

### Streaming

| # | Task | Status | Notes |
|---|------|--------|-------|
| 11 | `csv.stream_rows(path: String) -> Stream<Result<CsvRow, CsvError>>` | `[ ]` | Line-by-line, constant memory |
| 12 | Stream integration: `csv.stream_rows(path) \|> filter(pred) \|> collect()` | `[ ]` | Pipe operator with CSV |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 13 | Parse basic CSV with headers | `[ ]` | |
| 14 | Parse with custom delimiter (TSV, pipe-separated) | `[ ]` | |
| 15 | Handle quoted fields, embedded commas, embedded newlines | `[ ]` | |
| 16 | Write and re-read round-trip | `[ ]` | |
| 17 | Stream large file without loading entire file into memory | `[ ]` | |
| 18 | Error on malformed CSV (unclosed quote, inconsistent columns) | `[ ]` | |

**Done when:** `let table = csv.read("data.csv"); println(table.rows[0][0])` compiles and runs natively.
Dato package can use `encoding/csv.mn` as its CSV backend.

---

## Phase 3 — `net/http.mn` — Unified HTTP Client
**Priority:** CRITICAL — HTTP is the backbone of modern software; unblocks AI, web, and API use cases

One import. Full HTTP/1.1 client. Built on C runtime TCP + TLS from v0.8.0 Phase 6.

### Core Types

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `HttpMethod` enum: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS` | `[ ]` | |
| 2 | Define `HttpRequest` struct: method, url, headers (`Map<String, String>`), body (`Option<String>`), timeout_ms | `[ ]` | |
| 3 | Define `HttpResponse` struct: status_code, headers, body, elapsed_ms | `[ ]` | |
| 4 | Define `HttpError` enum: `ConnectionFailed`, `Timeout`, `TlsError`, `InvalidUrl`, `TooManyRedirects` | `[ ]` | |
| 5 | Define `HttpConfig` struct: timeout, max_redirects, verify_ssl, user_agent | `[ ]` | Sensible defaults |

### URL Parsing

| # | Task | Status | Notes |
|---|------|--------|-------|
| 6 | Parse URL: scheme, host, port, path, query string | `[ ]` | Manual parser, no external lib |
| 7 | URL encoding/decoding (percent-encoding) | `[ ]` | |
| 8 | Query parameter builder: `Map<String, String>` → `?key=value&...` | `[ ]` | |

### Request Execution

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | `http.get(url: String) -> Result<HttpResponse, HttpError>` | `[ ]` | Convenience wrapper |
| 10 | `http.post(url: String, body: String) -> Result<HttpResponse, HttpError>` | `[ ]` | Content-Type: application/json default |
| 11 | `http.request(req: HttpRequest) -> Result<HttpResponse, HttpError>` | `[ ]` | Full control |
| 12 | Build raw HTTP/1.1 request: `METHOD path HTTP/1.1\r\nHost: ...\r\n\r\nbody` | `[ ]` | Manual string construction |
| 13 | Send via `__mn_tcp_connect` + `__mn_tcp_send` (plain) or `__mn_tls_connect` + `__mn_tls_write` (HTTPS) | `[ ]` | Scheme-based dispatch |
| 14 | Parse HTTP/1.1 response: status line, headers, body | `[ ]` | Chunked transfer decoding |
| 15 | Content-Length body reading | `[ ]` | |
| 16 | Chunked transfer-encoding decoding | `[ ]` | |

### Features

| # | Task | Status | Notes |
|---|------|--------|-------|
| 17 | Redirect following (301, 302, 307, 308) with max_redirects limit | `[ ]` | |
| 18 | Timeout support via `__mn_tcp_set_timeout` | `[ ]` | |
| 19 | Custom headers | `[ ]` | |
| 20 | JSON body helpers: `http.post_json(url, data: JsonValue)` | `[ ]` | Depends on Phase 1 `json.encode` |
| 21 | Response body as JSON: `response.json() -> Result<JsonValue, JsonError>` | `[ ]` | Depends on Phase 1 `json.decode` |
| 22 | Request fingerprinting: unique trace hash per request | `[ ]` | SHA-256 of method+url+timestamp; foundation for crawler/security tools |

### Connection Management

| # | Task | Status | Notes |
|---|------|--------|-------|
| 23 | Connection pooling: reuse TCP connections to same host:port | `[ ]` | Map<String, List<fd>> keyed by host:port |
| 24 | Keep-alive support (`Connection: keep-alive` header) | `[ ]` | |
| 25 | Pool cleanup: close idle connections after timeout | `[ ]` | |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 26 | GET request to HTTP endpoint | `[ ]` | Can use local test server or httpbin |
| 27 | GET request to HTTPS endpoint | `[ ]` | TLS verification |
| 28 | POST with JSON body | `[ ]` | |
| 29 | Custom headers sent and received | `[ ]` | |
| 30 | Redirect following | `[ ]` | |
| 31 | Timeout handling | `[ ]` | |
| 32 | Error handling: connection refused, DNS failure | `[ ]` | |
| 33 | Response JSON parsing | `[ ]` | |
| 34 | Request fingerprint uniqueness | `[ ]` | |

**Done when:** `let resp = http.get("https://httpbin.org/get"); println(resp.body)` compiles and runs natively.
POST with JSON body works. HTTPS with TLS works.

---

## Phase 4 — `net/http/server.mn` — HTTP Server with Routing
**Priority:** HIGH — enables web applications, API servers, and the agent-per-request model

### Core Types

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `Route` struct: method, path_pattern, handler_fn | `[ ]` | |
| 2 | Define `Router` struct: routes list, middleware chain | `[ ]` | |
| 3 | Define `ServerConfig` struct: host, port, max_connections, read_timeout | `[ ]` | |
| 4 | Define `Context` struct: request, path_params (`Map<String, String>`), response_builder | `[ ]` | |

### Route Matching

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5 | Path pattern parsing: `/api/users/${id}` extracts `id` param | `[ ]` | Segment-by-segment matching |
| 6 | Static path matching: `/health`, `/api/v1/status` | `[ ]` | |
| 7 | Method + path dispatch to handler function | `[ ]` | Linear scan (sufficient for v0.9.0) |

### Server Loop

| # | Task | Status | Notes |
|---|------|--------|-------|
| 8 | `server.listen(config: ServerConfig, router: Router) -> Result<Void, ServerError>` | `[ ]` | Main accept loop |
| 9 | Accept connections via `__mn_tcp_listen` + `__mn_tcp_accept` | `[ ]` | |
| 10 | Parse incoming HTTP request (reuse Phase 3 parser) | `[ ]` | |
| 11 | Route dispatch: match request to handler, extract path params | `[ ]` | |
| 12 | Build and send HTTP response: status line, headers, body | `[ ]` | |
| 13 | Agent-per-request: spawn handler agent for each connection | `[ ]` | Uses agent system from v0.8.0 |
| 14 | Graceful connection close | `[ ]` | |

### Middleware

| # | Task | Status | Notes |
|---|------|--------|-------|
| 15 | Define `Middleware` trait: `fn handle(ctx: Context, next: fn(Context) -> Response) -> Response` | `[ ]` | |
| 16 | Logging middleware: log method, path, status, elapsed | `[ ]` | |
| 17 | CORS middleware: configurable origins, methods, headers | `[ ]` | |
| 18 | Middleware chain execution (outer → inner → handler → inner → outer) | `[ ]` | |

### Response Helpers

| # | Task | Status | Notes |
|---|------|--------|-------|
| 19 | `ctx.respond(status: Int, body: String)` | `[ ]` | |
| 20 | `ctx.json(status: Int, data: JsonValue)` | `[ ]` | Sets Content-Type: application/json |
| 21 | `ctx.redirect(url: String, status: Int)` | `[ ]` | 301/302 |
| 22 | Static file serving: `router.static_files(prefix: String, dir: String)` | `[ ]` | Uses `__mn_file_read` |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 23 | Start server, send request via http client, verify response | `[ ]` | Integration with Phase 3 |
| 24 | Path parameter extraction | `[ ]` | |
| 25 | Middleware chain execution order | `[ ]` | |
| 26 | JSON response round-trip | `[ ]` | |
| 27 | 404 for unmatched routes | `[ ]` | |
| 28 | Agent-per-request: concurrent connections handled | `[ ]` | |

**Done when:** A `.mn` program can start an HTTP server, register routes with path params,
apply middleware, and respond to requests — all compiled natively.

---

## Phase 5 — `net/websocket.mn` — WebSocket Client + Server
**Priority:** MEDIUM — enables real-time applications, chat, live data feeds

### Core Types

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `WsMessage` enum: `Text(String)`, `Binary(List<Int>)`, `Ping`, `Pong`, `Close(Int, String)` | `[ ]` | |
| 2 | Define `WsConnection` struct: fd, state, is_server | `[ ]` | |
| 3 | Define `WsError` enum: `HandshakeFailed`, `ConnectionClosed`, `InvalidFrame`, `ProtocolError` | `[ ]` | |

### Client

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4 | `ws.connect(url: String) -> Result<WsConnection, WsError>` | `[ ]` | HTTP upgrade handshake |
| 5 | Generate WebSocket key, send Upgrade request | `[ ]` | Base64-encoded random key |
| 6 | Validate server Sec-WebSocket-Accept response | `[ ]` | SHA-1 + Base64 of key + GUID |
| 7 | `ws.send(conn: WsConnection, msg: WsMessage) -> Result<Void, WsError>` | `[ ]` | Frame encoding |
| 8 | `ws.recv(conn: WsConnection) -> Result<WsMessage, WsError>` | `[ ]` | Frame decoding |
| 9 | Client-side masking (RFC 6455 requirement) | `[ ]` | XOR mask on payload |

### Server

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | WebSocket upgrade from HTTP server route | `[ ]` | Detect `Upgrade: websocket` header |
| 11 | Server handshake: compute accept key, send 101 response | `[ ]` | |
| 12 | Server-side frame handling (no masking on server→client) | `[ ]` | |

### Frame Protocol

| # | Task | Status | Notes |
|---|------|--------|-------|
| 13 | Frame encoding: opcode, payload length, mask, payload | `[ ]` | Supports 7-bit, 16-bit, 64-bit length |
| 14 | Frame decoding: read header, determine length, unmask | `[ ]` | |
| 15 | Fragmentation: split large messages into continuation frames | `[ ]` | |
| 16 | Ping/pong handling (auto-respond to pings) | `[ ]` | |
| 17 | Close handshake: send close frame, wait for response, shutdown | `[ ]` | |

### Channel Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| 18 | Map WebSocket connection to typed channel: `Channel<WsMessage>` | `[ ]` | Natural fit with agent channels |
| 19 | Agent-based WebSocket handler: spawn agent per connection | `[ ]` | |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 20 | Client connect to echo WebSocket server | `[ ]` | |
| 21 | Send/receive text messages | `[ ]` | |
| 22 | Send/receive binary messages | `[ ]` | |
| 23 | Ping/pong round-trip | `[ ]` | |
| 24 | Close handshake | `[ ]` | |
| 25 | Server-side: upgrade from HTTP, echo messages back | `[ ]` | Integration with Phase 4 |
| 26 | Fragmented message reassembly | `[ ]` | |

**Done when:** `let conn = ws.connect("ws://echo.example.com"); ws.send(conn, Text("hello")); let msg = ws.recv(conn)`
works natively. Server-side upgrade from HTTP server works.

---

## Phase 6 — `crypto.mn` — Cryptographic Primitives
**Priority:** MEDIUM — needed for WebSocket handshake (SHA-1), JWT, request fingerprinting

FFI to OpenSSL/libsodium for the heavy lifting. Mapanare wrapper for ergonomic API.

### Hashing

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | C runtime: `__mn_sha1(data, len, out)` | `[ ]` | Needed for WebSocket accept key |
| 2 | C runtime: `__mn_sha256(data, len, out)` | `[ ]` | General purpose hashing |
| 3 | C runtime: `__mn_sha512(data, len, out)` | `[ ]` | |
| 4 | `crypto.sha256(input: String) -> String` (hex digest) | `[ ]` | Mapanare wrapper |
| 5 | `crypto.sha512(input: String) -> String` (hex digest) | `[ ]` | |

### HMAC

| # | Task | Status | Notes |
|---|------|--------|-------|
| 6 | C runtime: `__mn_hmac_sha256(key, key_len, data, data_len, out)` | `[ ]` | |
| 7 | `crypto.hmac_sha256(key: String, data: String) -> String` | `[ ]` | |

### Encoding

| # | Task | Status | Notes |
|---|------|--------|-------|
| 8 | `crypto.base64_encode(input: String) -> String` | `[ ]` | Pure Mapanare or C runtime |
| 9 | `crypto.base64_decode(input: String) -> Result<String, CryptoError>` | `[ ]` | |
| 10 | `crypto.hex_encode(input: String) -> String` | `[ ]` | |
| 11 | `crypto.hex_decode(input: String) -> Result<String, CryptoError>` | `[ ]` | |

### JWT

| # | Task | Status | Notes |
|---|------|--------|-------|
| 12 | `crypto.jwt_encode(payload: JsonValue, secret: String) -> String` | `[ ]` | HS256 algorithm |
| 13 | `crypto.jwt_decode(token: String, secret: String) -> Result<JsonValue, CryptoError>` | `[ ]` | Verify signature + decode |
| 14 | `crypto.jwt_verify(token: String, secret: String) -> Bool` | `[ ]` | Signature check only |

### Random

| # | Task | Status | Notes |
|---|------|--------|-------|
| 15 | C runtime: `__mn_random_bytes(buf, len)` | `[ ]` | `/dev/urandom` or `CryptGenRandom` |
| 16 | `crypto.random_bytes(n: Int) -> List<Int>` | `[ ]` | |
| 17 | `crypto.random_hex(n: Int) -> String` | `[ ]` | n bytes → 2n hex chars |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 18 | SHA-256 of known input matches expected hash | `[ ]` | Test vectors from NIST |
| 19 | HMAC-SHA256 test vectors | `[ ]` | |
| 20 | Base64 encode/decode round-trip | `[ ]` | |
| 21 | JWT encode/decode round-trip with signature verification | `[ ]` | |
| 22 | Random bytes: correct length, non-zero entropy | `[ ]` | |
| 23 | Link against OpenSSL at build time (`-lssl -lcrypto`) | `[ ]` | Build system integration |

**Done when:** `let hash = crypto.sha256("hello"); let token = crypto.jwt_encode(payload, secret)`
works natively. WebSocket handshake can use SHA-1 + Base64 from this module.

---

## Phase 7 — `text/regex.mn` — Regular Expressions
**Priority:** MEDIUM — essential for data cleaning, crawling, security scanning

### Strategy Decision

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Decide: pure Mapanare NFA/DFA engine vs FFI to PCRE2 | `[ ]` | PCRE2 FFI recommended for v0.9.0; pure engine is a v1.x project |

### C Runtime (PCRE2 FFI path)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2 | C runtime: `__mn_regex_compile(pattern, len) -> regex_ptr` | `[ ]` | `pcre2_compile` wrapper |
| 3 | C runtime: `__mn_regex_match(regex, subject, len) -> match_data_ptr` | `[ ]` | `pcre2_match` wrapper |
| 4 | C runtime: `__mn_regex_get_group(match_data, group_idx) -> {start, end}` | `[ ]` | Capture group extraction |
| 5 | C runtime: `__mn_regex_free(regex_ptr)` | `[ ]` | Cleanup |
| 6 | Link against PCRE2 at build time (`-lpcre2-8`) | `[ ]` | |

### Mapanare API

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Define `Match` struct: `start: Int`, `end: Int`, `text: String`, `groups: List<Option<String>>` | `[ ]` | |
| 8 | Define `Regex` struct: compiled pattern handle | `[ ]` | |
| 9 | `regex.compile(pattern: String) -> Result<Regex, RegexError>` | `[ ]` | |
| 10 | `regex.match(pattern: String, text: String) -> Option<Match>` | `[ ]` | First match |
| 11 | `regex.find_all(pattern: String, text: String) -> List<Match>` | `[ ]` | All non-overlapping matches |
| 12 | `regex.replace(pattern: String, text: String, replacement: String) -> String` | `[ ]` | First occurrence |
| 13 | `regex.replace_all(pattern: String, text: String, replacement: String) -> String` | `[ ]` | All occurrences |
| 14 | `regex.split(pattern: String, text: String) -> List<String>` | `[ ]` | Split by pattern |
| 15 | `regex.is_match(pattern: String, text: String) -> Bool` | `[ ]` | Quick boolean check |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 16 | Match simple patterns: literals, `.`, `*`, `+`, `?` | `[ ]` | |
| 17 | Character classes: `[a-z]`, `[^0-9]`, `\d`, `\w`, `\s` | `[ ]` | |
| 18 | Capture groups: `(\d+)-(\d+)` extracts both groups | `[ ]` | |
| 19 | `find_all` returns all matches | `[ ]` | |
| 20 | `replace_all` substitutes correctly | `[ ]` | |
| 21 | `split` by pattern | `[ ]` | |
| 22 | Error on invalid regex pattern | `[ ]` | |

**Done when:** `let m = regex.match("(\\d+)-(\\d+)", "date: 2026-03"); println(m.groups[0])` → `"2026"`
works natively.

---

## Phase 8 — Cross-Module LLVM Compilation
**Priority:** CRITICAL — without this, stdlib modules can't import each other

Currently the LLVM backend compiles single `.mn` files. Stdlib modules need to import
each other (`net/http.mn` imports `encoding/json.mn` and `crypto.mn`). This phase
makes multi-file LLVM compilation work.

### Import Resolution

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Resolve `import encoding::json` to `stdlib/encoding/json.mn` | `[ ]` | Module path → file path mapping |
| 2 | Parse and type-check imported modules | `[ ]` | Reuse existing semantic checker |
| 3 | Build dependency graph across modules | `[ ]` | Topological sort for compilation order |
| 4 | Detect and report circular dependencies | `[ ]` | |

### LLVM Linking

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5 | Compile each module to its own LLVM IR module | `[ ]` | Separate `ir.Module` per file |
| 6 | Declare external functions for cross-module calls | `[ ]` | `declare` for imported symbols |
| 7 | Link multiple LLVM modules into a single executable | `[ ]` | `llvmlite` module linking or `llvm-link` |
| 8 | Handle name mangling for module-scoped symbols | `[ ]` | `module_name::function_name` → mangled symbol |
| 9 | Export `pub` declarations, hide non-`pub` symbols | `[ ]` | Internal vs external linkage |

### Type Sharing

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | Struct types defined in one module, used in another | `[ ]` | Shared type definitions across modules |
| 11 | Enum types shared across modules | `[ ]` | |
| 12 | Trait implementations resolved across module boundaries | `[ ]` | |
| 13 | Generic instantiation across modules | `[ ]` | Monomorphize at link time or per-module |

### CLI Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| 14 | `mapanare build` compiles all imported modules transitively | `[ ]` | Follow imports, compile dependency graph |
| 15 | Incremental compilation: skip unchanged modules | `[ ]` | Hash-based change detection |
| 16 | Stdlib path configuration: `--stdlib-path` or default location | `[ ]` | |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 17 | Two-file compilation: `a.mn` imports `b.mn`, calls function from b | `[ ]` | |
| 18 | Three-level chain: `a` imports `b` imports `c` | `[ ]` | |
| 19 | Circular dependency detection and error | `[ ]` | |
| 20 | Struct defined in module A, used in module B | `[ ]` | |
| 21 | Stdlib module import: `import encoding::json` | `[ ]` | |
| 22 | `pub` visibility enforced: non-pub symbols not accessible | `[ ]` | |

**Done when:** `import encoding::json; let data = json.decode(input)` compiles to a single native
binary via LLVM. Multiple stdlib modules can import each other.

---

## Phase 9 — Validation & Release
**Priority:** MEDIUM — wrap up the release

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run full test suite on LLVM backend — confirm all stdlib tests pass natively | `[ ]` | |
| 2 | Integration test: HTTP client → HTTP server round-trip in single native binary | `[ ]` | |
| 3 | Integration test: JSON decode → process → JSON encode round-trip | `[ ]` | |
| 4 | Integration test: CSV read → filter stream → CSV write | `[ ]` | |
| 5 | Integration test: WebSocket client ↔ server echo | `[ ]` | |
| 6 | Update Dato package to use `encoding/csv.mn` and `encoding/json.mn` | `[ ]` | |
| 7 | Performance benchmarks: native stdlib vs Python stdlib equivalents | `[ ]` | |
| 8 | Write CHANGELOG entry for v0.9.0 | `[ ]` | |
| 9 | Bump VERSION to 0.9.0 | `[ ]` | |
| 10 | Update ROADMAP.md with v0.9.0 completion | `[ ]` | |
| 11 | Update SPEC.md with stdlib module documentation | `[ ]` | |
| 12 | Update README feature status table | `[ ]` | |
| 13 | Update `mapanare.dev` website with v0.9.0 release notes | `[ ]` | |

**Done when:** VERSION reads `0.9.0`. All stdlib modules compile natively and pass tests.
A Mapanare program can make HTTP requests, serve HTTP, parse JSON, read CSV, use WebSockets,
hash data, and match regex — all without Python.

---

## What v0.9.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| Language freeze | v1.0.0 | Still evolving |
| Self-hosted fixed-point | v1.0.0 | Needs cross-module compilation stability |
| AI/LLM drivers | v1.1.0 | Needs HTTP client first (built in this version) |
| Database drivers | v1.2.0 | Needs stable stdlib |
| Web crawler | v1.3.0 | Needs HTTP + regex from this version |
| Vulnerability scanner | v1.3.0 | Needs HTTP + regex + crawler |
| YAML/TOML parsers | v1.2.0 | Lower priority than JSON/CSV |
| Filesystem operations | v1.2.0 | Basic file I/O in C runtime; full fs module later |
| GPU / WASM / mobile targets | v2.0.0 | Long-term |

---

## Dependency Chain (within v0.9.0)

```
Phase 1 (JSON) ──────┬──→ Phase 3 (HTTP Client) ──→ Phase 4 (HTTP Server) ──→ Phase 5 (WebSocket)
                      │                                       │
Phase 2 (CSV)         │                                       │
                      │                                       │
Phase 6 (Crypto) ─────┤  (needed by WebSocket handshake + JWT)
                      │
Phase 7 (Regex)       │  (independent, but useful for HTTP parsing)
                      │
Phase 8 (Cross-Module LLVM) ──→ links all modules together
                      │
                      └──→ Phase 9 (Validation & Release)
```

---

## Success Criteria for v0.9.0

v0.9.0 ships when ALL of the following are true:

1. **JSON works natively:** Parse and serialize JSON in `.mn`, compiled to native binary.
2. **HTTP client works natively:** GET/POST to HTTPS endpoints, parse JSON responses.
3. **HTTP server works natively:** Route dispatch, middleware, agent-per-request model.
4. **WebSocket works natively:** Client and server, text and binary frames.
5. **Crypto available:** SHA-256, HMAC, Base64, JWT — no Python dependencies.
6. **Regex available:** Pattern matching via PCRE2 FFI.
7. **Cross-module compilation:** `import encoding::json` resolves and links at LLVM level.
8. **No Python at runtime:** Every stdlib module compiles and runs without Python.
9. **Integration tests pass:** Client↔server round-trip, JSON round-trip, CSV pipeline.
10. **All v0.8.0 tests still pass:** No regressions.

---

## Priority Order

If time is limited, ship in this order:

1. **Phase 8** (Cross-module LLVM — unlocks everything else)
2. **Phase 1** (JSON — used by HTTP, config, data interchange)
3. **Phase 3** (HTTP client — backbone of modern software)
4. **Phase 6** (Crypto — needed by WebSocket + JWT)
5. **Phase 4** (HTTP server — enables web apps)
6. **Phase 5** (WebSocket — real-time apps)
7. **Phase 7** (Regex — data processing, security)
8. **Phase 2** (CSV — data workflows)
9. **Phase 9** (Release — ceremonial once the rest lands)

---

## Context Recovery

If you are **running low on context** or about to lose track mid-phase, **immediately** add a handoff entry below before the context dies. The next session reads this section first.

**Format per entry:**

```
### Phase X — [Name] (YYYY-MM-DD)
**Status:** Complete | Partial | Failed
**Completed:** task 1, task 2, ...
**Remaining:** task 3 (specific details), task 4 (blocker: reason)
**Files modified:** path/to/file — what changed
**Notes:** decisions, gotchas, anything the next session needs
```

Also update the task statuses in the phase table above to match your actual progress. Partial progress committed > lost progress.

---

*"A language that can't talk to the network is a language that talks to itself."*
