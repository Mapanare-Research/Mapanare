# Mapanare v1.3.0 — "Web Platform & Security"

> v1.2.0 gave Mapanare a complete data layer — SQL, KV, TOML, YAML, filesystem, Dato.
> v1.3.0 turns Mapanare into a weapon. A compiled web framework with session management
> and auth. A concurrent web crawler where every URL is an agent. A vulnerability scanner
> where every target is a supervised agent that reads YAML templates, fires requests, and
> matches responses — 100 targets in parallel, compiled to native code, no Python, no GIL.
>
> Core theme: **Build real web apps. Break real targets. Agents do the work.**

---

## Scope Rules

1. **All new modules are `.mn` files** — compiled via LLVM, native only
2. **Agents are the concurrency model** — no thread pools, no async/await wrappers; crawler agents, scanner agents, request agents
3. **YAML is the config language** — scan templates, crawl configs, server configs all use `encoding/yaml.mn` from v1.2.0
4. **Security by design** — scanner is for authorized testing only; rate limiting is mandatory, not optional
5. **Built on existing stdlib** — `net/http.mn`, `net/http/server.mn`, `net/websocket.mn`, `text/regex.mn`, `crypto.mn`, `encoding/json.mn`, `encoding/yaml.mn`, `fs.mn`
6. **`net/crawl` and `security/scan` are separate packages** — not monolith stdlib; installable via `mapanare pkg install`

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

| Phase | Name | Status | Effort | Platform |
|-------|------|--------|--------|----------|
| 1 | C Runtime: HTML Parser & OS Primitives | `Not Started` | Large | WSL/Linux |
| 2 | HTTP Server v2 — Sessions, Auth, SSE | `Not Started` | X-Large | Both |
| 3 | Template Engine | `Not Started` | Medium | Windows |
| 4 | `net/crawl` — Web Crawler | `Not Started` | X-Large | Both |
| 5 | `security/scan` — Vulnerability Scanner | `Not Started` | X-Large | Both |
| 6 | `security/fuzz` — Fuzzing Primitives | `Not Started` | Medium | Both |
| 7 | Integration Testing & Release | `Not Started` | Large | Both |

---

## Prerequisites (from v1.2.0)

| # | Prerequisite | Status | Notes |
|---|-------------|--------|-------|
| 1 | v1.2.0 released (Data & Storage: SQL, KV, TOML, YAML, fs, Dato) | `[ ]` | |
| 2 | `encoding/yaml.mn` stable — scanner templates are YAML | `[ ]` | 1,129 lines, v1.2.0 |
| 3 | `net/http.mn` — HTTP client with TLS | `[x]` | Since v0.9.0 |
| 4 | `net/http/server.mn` — HTTP server with routing, middleware, static files | `[x]` | 822 lines, v0.9.0 |
| 5 | `net/websocket.mn` — WebSocket client + server | `[x]` | Since v0.9.0 |
| 6 | `text/regex.mn` — PCRE2 regex via FFI | `[x]` | Since v0.9.0 |
| 7 | `crypto.mn` — SHA, HMAC, Base64, JWT, random | `[x]` | Since v0.9.0 |
| 8 | `fs.mn` — filesystem operations | `[ ]` | v1.2.0 |
| 9 | Agent system working on LLVM backend | `[x]` | Since v0.8.0 |

---

## Phase 1 — C Runtime: HTML Parser & OS Primitives
**Status:** `Not Started`
**Priority:** CRITICAL — crawler needs HTML parsing, scanner needs timing primitives
**Platform:** WSL/Linux
**Effort:** Large (1-2 weeks)

### HTML Parsing (lexbor via dlopen)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `__mn_html_parse(html: MnString) -> int64_t` — parse HTML, return document handle | `[ ]` | `runtime/native/mapanare_html.c`, `.h` | dlopen lexbor (`liblexbor.so`) |
| 2 | Add `__mn_html_query(doc, selector: MnString) -> int64_t` — CSS selector query, return collection handle | `[ ]` | `mapanare_html.c` | `lxb_css_selectors_find` |
| 3 | Add `__mn_html_collection_len(coll) -> int64_t` — number of matched elements | `[ ]` | `mapanare_html.c` | |
| 4 | Add `__mn_html_collection_get(coll, idx) -> int64_t` — get element at index | `[ ]` | `mapanare_html.c` | |
| 5 | Add `__mn_html_element_tag(elem) -> MnString` — tag name ("a", "div", etc.) | `[ ]` | `mapanare_html.c` | |
| 6 | Add `__mn_html_element_attr(elem, name: MnString) -> MnString` — attribute value | `[ ]` | `mapanare_html.c` | "href", "class", "id", etc. |
| 7 | Add `__mn_html_element_text(elem) -> MnString` — inner text content | `[ ]` | `mapanare_html.c` | |
| 8 | Add `__mn_html_element_html(elem) -> MnString` — outer HTML | `[ ]` | `mapanare_html.c` | |
| 9 | Add `__mn_html_free(doc)` — free document | `[ ]` | `mapanare_html.c` | |
| 10 | Add `__mn_html_collection_free(coll)` — free collection | `[ ]` | `mapanare_html.c` | |
| 11 | Implement dlopen strategy: `liblexbor.so` → `liblexbor.so.2` → `liblexbor.dylib` | `[ ]` | `mapanare_html.c` | Graceful fallback: returns empty/0 if not installed |

### Timing & Process Primitives

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 12 | Add `__mn_time_now_ms() -> int64_t` — current time in milliseconds | `[ ]` | `mapanare_io.c` | `clock_gettime(CLOCK_MONOTONIC)` / `GetTickCount64` |
| 13 | Add `__mn_time_now_unix() -> int64_t` — Unix epoch seconds | `[ ]` | `mapanare_io.c` | `time(NULL)` |
| 14 | Add `__mn_sleep_ms(ms: int64_t)` — sleep for N milliseconds | `[ ]` | `mapanare_io.c` | `usleep` / `Sleep` |
| 15 | Add `__mn_env_get(name: MnString) -> MnString` — read environment variable | `[ ]` | `mapanare_io.c` | `getenv` |

### URL Parsing Helpers (pure C, no external dep)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 16 | Add `__mn_url_parse_scheme(url: MnString) -> MnString` — "http", "https" | `[ ]` | `mapanare_io.c` | |
| 17 | Add `__mn_url_parse_host(url: MnString) -> MnString` | `[ ]` | `mapanare_io.c` | |
| 18 | Add `__mn_url_parse_port(url: MnString) -> int64_t` — 0 if not specified | `[ ]` | `mapanare_io.c` | |
| 19 | Add `__mn_url_parse_path(url: MnString) -> MnString` | `[ ]` | `mapanare_io.c` | |

### Build

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 20 | Create `runtime/native/build_html.py` — compile `mapanare_html.c` | `[ ]` | `runtime/native/build_html.py` | |
| 21 | Update `mapanare_io.c` with timing/env/URL functions | `[ ]` | `runtime/native/mapanare_io.c` | |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 22 | Test: HTML parse + query + extract attributes on sample HTML | `[ ]` | `tests/native/test_html_parser.py` | |
| 23 | Test: timing functions return reasonable values | `[ ]` | `tests/native/test_timing.py` | |
| 24 | Test: URL parsing for http, https, with/without port | `[ ]` | `tests/native/test_url_parse.py` | |
| 25 | Test: dlopen graceful fallback when lexbor not installed | `[ ]` | `tests/native/test_html_dlopen.py` | |

**Done when:** HTML can be parsed and queried via CSS selectors, timing primitives work,
URL parsing extracts scheme/host/port/path.

---

## Phase 2 — HTTP Server v2: Sessions, Auth, SSE
**Status:** `Not Started`
**Priority:** CRITICAL — every web app needs sessions and auth; SSE enables real-time dashboards
**Platform:** Both
**Effort:** X-Large (2+ weeks)

Extends the existing `net/http/server.mn` (822 lines) with production features.
The v1 server has routing, path params, middleware (logging, CORS), static files.
v2 adds what you need to build a real app.

### Cookie Handling

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `pub struct Cookie { name: String, value: String, path: String, domain: String, max_age: Int, secure: Bool, http_only: Bool, same_site: String }` | `[ ]` | `stdlib/net/http/cookie.mn` | |
| 2 | Implement `parse_cookies(header: String) -> List<Cookie>` — parse `Cookie:` request header | `[ ]` | `stdlib/net/http/cookie.mn` | `name=value; name2=value2` |
| 3 | Implement `set_cookie(cookie: Cookie) -> String` — build `Set-Cookie:` response header | `[ ]` | `stdlib/net/http/cookie.mn` | With Path, Domain, Max-Age, Secure, HttpOnly, SameSite |
| 4 | Implement `ctx_set_cookie(ctx: Context, cookie: Cookie) -> Context` — add Set-Cookie to response | `[ ]` | `stdlib/net/http/cookie.mn` | |
| 5 | Implement `ctx_get_cookie(ctx: Context, name: String) -> Option<String>` — read cookie from request | `[ ]` | `stdlib/net/http/cookie.mn` | |

### Session Management

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Define `pub struct Session { id: String, data: Map<String, String>, created_at: Int, expires_at: Int }` | `[ ]` | `stdlib/net/http/session.mn` | |
| 7 | Define `pub struct SessionStore { sessions: Map<String, Session>, cookie_name: String, max_age: Int }` | `[ ]` | `stdlib/net/http/session.mn` | In-memory store for v1.3; pluggable via KVStore in v1.4 |
| 8 | Implement `new_session_store(cookie_name: String, max_age: Int) -> SessionStore` | `[ ]` | `stdlib/net/http/session.mn` | |
| 9 | Implement `create_session(store: SessionStore) -> (SessionStore, Session)` — generate random ID, create session | `[ ]` | `stdlib/net/http/session.mn` | Uses `crypto.random_hex(16)` for session ID |
| 10 | Implement `get_session(store: SessionStore, id: String) -> Option<Session>` — look up by ID | `[ ]` | `stdlib/net/http/session.mn` | Returns None if expired or not found |
| 11 | Implement `set_session_value(session: Session, key: String, value: String) -> Session` | `[ ]` | `stdlib/net/http/session.mn` | |
| 12 | Implement `get_session_value(session: Session, key: String) -> Option<String>` | `[ ]` | `stdlib/net/http/session.mn` | |
| 13 | Implement `destroy_session(store: SessionStore, id: String) -> SessionStore` — remove session | `[ ]` | `stdlib/net/http/session.mn` | |
| 14 | Implement `session_middleware(store: SessionStore, ctx: Context) -> (SessionStore, Context)` — auto-load/create session from cookie | `[ ]` | `stdlib/net/http/session.mn` | Reads session cookie → loads or creates session → attaches to context |
| 15 | Implement `cleanup_expired(store: SessionStore) -> SessionStore` — remove expired sessions | `[ ]` | `stdlib/net/http/session.mn` | |

### Authentication Middleware

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 16 | Define `pub enum AuthResult { Authenticated(String), Denied(String) }` | `[ ]` | `stdlib/net/http/auth.mn` | String = user identifier |
| 17 | Implement `basic_auth(ctx: Context, check_fn_name: String) -> AuthResult` — parse `Authorization: Basic` header, decode base64, extract user:pass | `[ ]` | `stdlib/net/http/auth.mn` | |
| 18 | Implement `bearer_auth(ctx: Context) -> Option<String>` — extract Bearer token from Authorization header | `[ ]` | `stdlib/net/http/auth.mn` | |
| 19 | Implement `jwt_auth(ctx: Context, secret: String) -> AuthResult` — extract Bearer JWT, verify signature, return claims | `[ ]` | `stdlib/net/http/auth.mn` | Uses `crypto.jwt_decode` |
| 20 | Implement `cookie_auth(ctx: Context, session_store: SessionStore, required_key: String) -> AuthResult` — check session has required key | `[ ]` | `stdlib/net/http/auth.mn` | |
| 21 | Implement `auth_middleware(ctx: Context, method: String, config: String) -> Context` — dispatch to auth method, return 401 on failure | `[ ]` | `stdlib/net/http/auth.mn` | `method`: "basic", "bearer", "jwt", "cookie" |

### Rate Limiting

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 22 | Define `pub struct RateLimiter { window_ms: Int, max_requests: Int, counters: Map<String, Int>, timestamps: Map<String, Int> }` | `[ ]` | `stdlib/net/http/ratelimit.mn` | |
| 23 | Implement `new_rate_limiter(window_ms: Int, max_requests: Int) -> RateLimiter` | `[ ]` | `stdlib/net/http/ratelimit.mn` | |
| 24 | Implement `check_rate(limiter: RateLimiter, key: String, now_ms: Int) -> (RateLimiter, Bool)` — returns (updated limiter, allowed) | `[ ]` | `stdlib/net/http/ratelimit.mn` | Fixed window counter per key |
| 25 | Implement `rate_limit_middleware(limiter: RateLimiter, ctx: Context) -> (RateLimiter, Context)` — 429 Too Many Requests if exceeded | `[ ]` | `stdlib/net/http/ratelimit.mn` | Key = client IP from headers or socket |

### Server-Sent Events (SSE)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 26 | Define `pub struct SseEvent { event_type: String, data: String, id: String, retry: Int }` | `[ ]` | `stdlib/net/http/sse.mn` | |
| 27 | Implement `format_sse_event(evt: SseEvent) -> String` — format per SSE spec: `event: type\ndata: data\nid: id\n\n` | `[ ]` | `stdlib/net/http/sse.mn` | |
| 28 | Implement `sse_headers() -> Map<String, String>` — `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive` | `[ ]` | `stdlib/net/http/sse.mn` | |
| 29 | Implement `sse_send(fd: Int, evt: SseEvent) -> Result<Int, ServerError>` — send one event over open connection | `[ ]` | `stdlib/net/http/sse.mn` | Direct TCP write, no response buffering |
| 30 | Implement `sse_keepalive(fd: Int) -> Result<Int, ServerError>` — send `:keepalive\n\n` comment | `[ ]` | `stdlib/net/http/sse.mn` | Prevents proxy timeout |

### Request Body Parsing

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 31 | Implement `parse_form_urlencoded(body: String) -> Map<String, String>` | `[ ]` | `stdlib/net/http/body.mn` | `key=value&key2=value2`, URL-decode |
| 32 | Implement `parse_multipart(body: String, boundary: String) -> List<FormPart>` | `[ ]` | `stdlib/net/http/body.mn` | File uploads: `FormPart { name, filename, content_type, data }` |
| 33 | Implement `url_decode(s: String) -> String` — `%20` → space, `+` → space | `[ ]` | `stdlib/net/http/body.mn` | |
| 34 | Implement `url_encode(s: String) -> String` — space → `%20`, special chars → `%XX` | `[ ]` | `stdlib/net/http/body.mn` | |

### Server Configuration (YAML-based)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 35 | Define server config YAML format: `host`, `port`, `tls.cert`, `tls.key`, `session.max_age`, `cors.origins`, `rate_limit.window`, `rate_limit.max` | `[ ]` | `stdlib/net/http/config.mn` | |
| 36 | Implement `load_server_config(path: String) -> Result<ServerConfig, ServerError>` — parse YAML config | `[ ]` | `stdlib/net/http/config.mn` | Uses `encoding/yaml.mn` |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 37 | Test: cookie parse/set roundtrip | `[ ]` | `tests/stdlib/test_http_cookie.py` | |
| 38 | Test: session create/get/set/destroy lifecycle | `[ ]` | `tests/stdlib/test_http_session.py` | |
| 39 | Test: session expiry cleanup | `[ ]` | `tests/stdlib/test_http_session.py` | |
| 40 | Test: Basic auth header parsing + credential check | `[ ]` | `tests/stdlib/test_http_auth.py` | |
| 41 | Test: JWT auth verify + reject tampered token | `[ ]` | `tests/stdlib/test_http_auth.py` | |
| 42 | Test: Bearer token extraction | `[ ]` | `tests/stdlib/test_http_auth.py` | |
| 43 | Test: rate limiter allows within limit, blocks over limit | `[ ]` | `tests/stdlib/test_http_ratelimit.py` | |
| 44 | Test: SSE event formatting | `[ ]` | `tests/stdlib/test_http_sse.py` | |
| 45 | Test: form URL-encoded parsing | `[ ]` | `tests/stdlib/test_http_body.py` | |
| 46 | Test: multipart form parsing | `[ ]` | `tests/stdlib/test_http_body.py` | |
| 47 | Test: url_encode / url_decode roundtrip | `[ ]` | `tests/stdlib/test_http_body.py` | |
| 48 | Test: YAML server config loading | `[ ]` | `tests/stdlib/test_http_config.py` | |

**Done when:** Full web app stack works: session-authenticated endpoints, JWT-protected APIs,
rate limiting, SSE real-time events, file upload handling, YAML-based server config.

---

## Phase 3 — Template Engine
**Status:** `Not Started`
**Priority:** MEDIUM — server-side rendering for web apps; optional for API-only services
**Platform:** Windows (pure Mapanare)
**Effort:** Medium (3-5 days)

A minimal, compiled template engine. No Jinja complexity — just variable substitution,
conditionals, and loops. Templates compile to string-building functions.

### Core

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `pub struct TemplateContext { values: Map<String, String>, lists: Map<String, List<String>> }` | `[ ]` | `stdlib/net/http/template.mn` | |
| 2 | Implement `render(template: String, ctx: TemplateContext) -> Result<String, TemplateError>` | `[ ]` | `stdlib/net/http/template.mn` | |
| 3 | Implement variable substitution: `{{ name }}` → look up in ctx.values | `[ ]` | `stdlib/net/http/template.mn` | |
| 4 | Implement conditionals: `{% if show_nav %}...{% endif %}` — check if key exists and is "true" | `[ ]` | `stdlib/net/http/template.mn` | |
| 5 | Implement negation: `{% if not logged_in %}...{% endif %}` | `[ ]` | `stdlib/net/http/template.mn` | |
| 6 | Implement loops: `{% for item in items %}...{{ item }}...{% endfor %}` — iterate ctx.lists | `[ ]` | `stdlib/net/http/template.mn` | |
| 7 | Implement HTML escaping: `{{ name | escape }}` — escape `<>&"'` | `[ ]` | `stdlib/net/http/template.mn` | Default: raw. Pipe `escape` for safe output. |
| 8 | Implement template includes: `{% include "header.html" %}` — read file and inline | `[ ]` | `stdlib/net/http/template.mn` | Uses `fs.read_file` |
| 9 | Implement `render_file(path: String, ctx: TemplateContext) -> Result<String, TemplateError>` | `[ ]` | `stdlib/net/http/template.mn` | Load template from file, then render |
| 10 | Implement `ctx_html(ctx: Context, status: Int, template: String, tpl_ctx: TemplateContext) -> Context` — render template and respond with text/html | `[ ]` | `stdlib/net/http/template.mn` | Integration with server context |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 11 | Test: variable substitution | `[ ]` | `tests/stdlib/test_template.py` | |
| 12 | Test: conditionals (if, if not, nested) | `[ ]` | `tests/stdlib/test_template.py` | |
| 13 | Test: loops (for/endfor) | `[ ]` | `tests/stdlib/test_template.py` | |
| 14 | Test: HTML escaping | `[ ]` | `tests/stdlib/test_template.py` | |
| 15 | Test: include directive | `[ ]` | `tests/stdlib/test_template.py` | |
| 16 | Test: error on unclosed tags | `[ ]` | `tests/stdlib/test_template.py` | |
| 17 | Test: render_file end-to-end | `[ ]` | `tests/stdlib/test_template.py` | |

**Done when:** Template engine renders variables, conditionals, loops, includes, and escapes HTML.
Integrates with server Context for one-line HTML responses.

---

## Phase 4 — `net/crawl` — Web Crawler
**Status:** `Not Started`
**Priority:** HIGH — foundational for security scanner (Phase 5) and data collection
**Platform:** Both (external package: `github.com/Mapanare-Research/crawl`)
**Effort:** X-Large (2+ weeks)

A compiled, agent-parallel web crawler. Every URL is an agent. The frontier is a channel.
Rate limiting is per-domain. robots.txt is respected. This is not Scrapy — it's what
Scrapy would be if Python had agents, channels, and compiled to native code.

```
// This is what a crawler looks like in Mapanare:

let config = crawl.config("https://example.com", max_depth: 3, concurrency: 20)
let results = crawl.run(config)
    |> filter(fn(page) -> page.status == 200)
    |> map(fn(page) -> page.title + " - " + page.url)

// Or with custom extraction:
let config = crawl.config("https://shop.example.com", max_depth: 2, concurrency: 10)
let products = crawl.run(config)
    |> filter(fn(page) -> page.url.contains("/product/"))
    |> map(fn(page) -> crawl.select(page, "h1.product-name").text)
```

### Core Types

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `pub struct CrawlConfig { seed_urls: List<String>, max_depth: Int, concurrency: Int, delay_ms: Int, user_agent: String, respect_robots: Bool, max_pages: Int, allowed_domains: List<String>, timeout_ms: Int }` | `[ ]` | `crawl/src/config.mn` | |
| 2 | Define `pub struct Page { url: String, status: Int, headers: Map<String, String>, body: String, title: String, links: List<String>, depth: Int, elapsed_ms: Int }` | `[ ]` | `crawl/src/page.mn` | |
| 3 | Define `pub enum CrawlError { FetchFailed(String), ParseFailed(String), RobotsBlocked(String), Timeout(String), MaxDepth(String) }` | `[ ]` | `crawl/src/page.mn` | |
| 4 | Define `pub struct CrawlStats { pages_crawled: Int, pages_failed: Int, pages_skipped: Int, total_bytes: Int, elapsed_ms: Int }` | `[ ]` | `crawl/src/page.mn` | |

### URL Management

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Implement `parse_url(url: String) -> Url` — extract scheme, host, port, path, query, fragment | `[ ]` | `crawl/src/url.mn` | |
| 6 | Implement `normalize_url(base: String, relative: String) -> String` — resolve relative URLs against base | `[ ]` | `crawl/src/url.mn` | Handle `./`, `../`, `//`, absolute paths |
| 7 | Implement `same_domain(url1: String, url2: String) -> Bool` | `[ ]` | `crawl/src/url.mn` | |
| 8 | Implement `url_fingerprint(url: String) -> String` — normalize for dedup (strip fragment, sort query params) | `[ ]` | `crawl/src/url.mn` | |

### HTML Link Extraction

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Implement `extract_links(html: String, base_url: String) -> List<String>` — find all `<a href>` links | `[ ]` | `crawl/src/extract.mn` | Uses C runtime HTML parser if available, falls back to regex |
| 10 | Implement `extract_title(html: String) -> String` — extract `<title>` content | `[ ]` | `crawl/src/extract.mn` | |
| 11 | Implement `select(page: Page, selector: String) -> List<Element>` — CSS selector query on page body | `[ ]` | `crawl/src/extract.mn` | Uses C runtime `__mn_html_query` |
| 12 | Implement `Element.text() -> String`, `Element.attr(name) -> String`, `Element.html() -> String` | `[ ]` | `crawl/src/extract.mn` | |

### robots.txt

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 13 | Implement `parse_robots(content: String) -> RobotRules` — parse robots.txt per protocol | `[ ]` | `crawl/src/robots.mn` | Handle `User-agent`, `Disallow`, `Allow`, `Crawl-delay`, `Sitemap` |
| 14 | Implement `is_allowed(rules: RobotRules, user_agent: String, path: String) -> Bool` | `[ ]` | `crawl/src/robots.mn` | |
| 15 | Implement `fetch_robots(base_url: String) -> Result<RobotRules, CrawlError>` — GET /robots.txt | `[ ]` | `crawl/src/robots.mn` | Cache per domain |
| 16 | Implement `get_crawl_delay(rules: RobotRules, user_agent: String) -> Int` — ms delay | `[ ]` | `crawl/src/robots.mn` | |
| 17 | Implement `get_sitemaps(rules: RobotRules) -> List<String>` — extract sitemap URLs | `[ ]` | `crawl/src/robots.mn` | |

### Frontier & Deduplication

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 18 | Define `pub struct Frontier { queue: List<FrontierEntry>, seen: Map<String, Bool>, domain_last_fetch: Map<String, Int> }` | `[ ]` | `crawl/src/frontier.mn` | |
| 19 | Define `struct FrontierEntry { url: String, depth: Int, priority: Int }` | `[ ]` | `crawl/src/frontier.mn` | |
| 20 | Implement `frontier_add(f: Frontier, url: String, depth: Int) -> Frontier` — add if not seen | `[ ]` | `crawl/src/frontier.mn` | Dedup by URL fingerprint |
| 21 | Implement `frontier_next(f: Frontier, now_ms: Int) -> (Frontier, Option<FrontierEntry>)` — pop next URL respecting domain delay | `[ ]` | `crawl/src/frontier.mn` | |
| 22 | Implement `frontier_size(f: Frontier) -> Int` — remaining URLs | `[ ]` | `crawl/src/frontier.mn` | |

### Crawl Engine

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 23 | Implement `fetch_page(url: String, config: CrawlConfig) -> Result<Page, CrawlError>` — HTTP GET, parse response, extract links + title | `[ ]` | `crawl/src/engine.mn` | Uses `net/http.mn` |
| 24 | Implement `crawl(config: CrawlConfig) -> List<Page>` — synchronous crawl loop | `[ ]` | `crawl/src/engine.mn` | Frontier → fetch → extract links → add to frontier → repeat |
| 25 | Implement `crawl_stream(config: CrawlConfig) -> Stream<Page>` — streaming crawl, yields pages as discovered | `[ ]` | `crawl/src/engine.mn` | For large crawls |
| 26 | Implement domain rate limiting: track last fetch per domain, enforce delay | `[ ]` | `crawl/src/engine.mn` | |
| 27 | Implement depth limiting: stop adding URLs beyond max_depth | `[ ]` | `crawl/src/engine.mn` | |
| 28 | Implement page count limiting: stop after max_pages | `[ ]` | `crawl/src/engine.mn` | |

### Crawl Persistence

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 29 | Implement `save_state(frontier: Frontier, path: String) -> Result<Bool, CrawlError>` — serialize frontier to JSON | `[ ]` | `crawl/src/persist.mn` | Resume interrupted crawls |
| 30 | Implement `load_state(path: String) -> Result<Frontier, CrawlError>` — restore frontier | `[ ]` | `crawl/src/persist.mn` | |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 31 | Test: URL parsing — scheme, host, port, path, query | `[ ]` | `crawl/tests/test_url.py` | |
| 32 | Test: URL normalization — relative, absolute, `../`, `./` | `[ ]` | `crawl/tests/test_url.py` | |
| 33 | Test: link extraction from HTML | `[ ]` | `crawl/tests/test_extract.py` | |
| 34 | Test: robots.txt parsing — allow, disallow, crawl-delay | `[ ]` | `crawl/tests/test_robots.py` | |
| 35 | Test: frontier add/next/dedup | `[ ]` | `crawl/tests/test_frontier.py` | |
| 36 | Test: frontier domain delay enforcement | `[ ]` | `crawl/tests/test_frontier.py` | |
| 37 | Test: crawl state save/load roundtrip | `[ ]` | `crawl/tests/test_persist.py` | |

**Done when:** Crawler can start from seed URLs, respect robots.txt, extract links,
deduplicate, rate-limit per domain, and yield pages as a stream. State is persistent.

---

## Phase 5 — `security/scan` — Vulnerability Scanner
**Status:** `Not Started`
**Priority:** HIGH — the flagship security tool; proves Mapanare eats Python security tooling
**Platform:** Both (external package: `github.com/Mapanare-Research/scan`)
**Effort:** X-Large (2+ weeks)

A Nuclei-inspired, template-based vulnerability scanner written entirely in Mapanare.
Each target is a supervised agent. Templates are YAML. Matchers are compiled. 100 targets
in parallel, native code, no interpreter overhead.

**What makes this not just another Nuclei clone:**
- **Compiled** — matcher evaluation is native LLVM, not interpreted YAML at runtime
- **Agent-per-target** — supervised, auto-restart on failure, natural concurrency
- **Stream-native** — results stream as findings arrive, not batch after completion
- **Composable** — `scan(targets) |> filter(fn(f) -> f.severity == "HIGH") |> to_json("report.json")`
- **Crawler-integrated** — feed `net/crawl` output directly into scanner input

```
// Scan a target with all templates:
let findings = scan.run(
    targets: ["https://example.com"],
    templates: scan.load_templates("templates/"),
    concurrency: 50
)
findings |> filter(fn(f) -> f.severity == "HIGH" or f.severity == "CRITICAL")
         |> show()

// Crawl → scan pipeline:
let pages = crawl.run(crawl.config("https://target.com", max_depth: 2))
let urls = pages |> map(fn(p) -> p.url)
let findings = scan.run(targets: urls, templates: templates, concurrency: 100)
```

### Template System (YAML-based)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define template YAML schema: `id`, `info` (name, severity, tags, author), `requests` (method, path, headers, body), `matchers` (type, condition, values) | `[ ]` | `scan/src/template.mn` | |
| 2 | Define `pub struct ScanTemplate { id: String, name: String, severity: String, tags: List<String>, author: String, requests: List<TemplateRequest>, matchers: List<Matcher>, extractors: List<Extractor> }` | `[ ]` | `scan/src/template.mn` | |
| 3 | Define `pub struct TemplateRequest { method: String, path: String, headers: Map<String, String>, body: String, follow_redirects: Bool, max_redirects: Int }` | `[ ]` | `scan/src/template.mn` | |
| 4 | Implement `load_template(path: String) -> Result<ScanTemplate, ScanError>` — parse single YAML template file | `[ ]` | `scan/src/template.mn` | Uses `encoding/yaml.mn` |
| 5 | Implement `load_templates(dir: String) -> Result<List<ScanTemplate>, ScanError>` — load all `.yaml` files from directory | `[ ]` | `scan/src/template.mn` | Uses `fs.walk` + filter `.yaml` |
| 6 | Implement template variable interpolation: `{{BaseURL}}`, `{{Hostname}}`, `{{Port}}`, `{{Path}}` | `[ ]` | `scan/src/template.mn` | |

### Matcher System

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | Define `pub enum MatcherType { Status, Header, Body, Regex, ResponseTime, WordCount }` | `[ ]` | `scan/src/matcher.mn` | |
| 8 | Define `pub struct Matcher { matcher_type: MatcherType, condition: String, values: List<String>, negative: Bool }` | `[ ]` | `scan/src/matcher.mn` | `condition`: "and" (all must match) or "or" (any must match) |
| 9 | Implement `match_status(matcher: Matcher, status: Int) -> Bool` — status code in values list | `[ ]` | `scan/src/matcher.mn` | `values: ["200", "301"]` |
| 10 | Implement `match_header(matcher: Matcher, headers: Map<String, String>) -> Bool` — header contains value | `[ ]` | `scan/src/matcher.mn` | `values: ["X-Powered-By: PHP"]` |
| 11 | Implement `match_body(matcher: Matcher, body: String) -> Bool` — body contains all/any strings | `[ ]` | `scan/src/matcher.mn` | `values: ["wp-content", "WordPress"]` |
| 12 | Implement `match_regex(matcher: Matcher, body: String) -> Bool` — regex match on body | `[ ]` | `scan/src/matcher.mn` | Uses `text/regex.mn` |
| 13 | Implement `match_response_time(matcher: Matcher, elapsed_ms: Int) -> Bool` — response took > N ms | `[ ]` | `scan/src/matcher.mn` | For time-based blind detection |
| 14 | Implement `match_word_count(matcher: Matcher, body: String) -> Bool` — word count comparison | `[ ]` | `scan/src/matcher.mn` | |
| 15 | Implement `evaluate_matchers(matchers: List<Matcher>, response: ScanResponse) -> Bool` — AND/OR logic across matchers | `[ ]` | `scan/src/matcher.mn` | |

### Extractor System

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 16 | Define `pub enum ExtractorType { Regex, Header, JsonPath, XPath }` | `[ ]` | `scan/src/extractor.mn` | |
| 17 | Define `pub struct Extractor { extractor_type: ExtractorType, name: String, pattern: String, group: Int }` | `[ ]` | `scan/src/extractor.mn` | |
| 18 | Implement `extract_regex(ext: Extractor, body: String) -> List<String>` — capture groups from body | `[ ]` | `scan/src/extractor.mn` | |
| 19 | Implement `extract_header(ext: Extractor, headers: Map<String, String>) -> List<String>` | `[ ]` | `scan/src/extractor.mn` | |
| 20 | Implement `run_extractors(extractors: List<Extractor>, response: ScanResponse) -> Map<String, List<String>>` | `[ ]` | `scan/src/extractor.mn` | |

### Scan Engine

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 21 | Define `pub struct ScanConfig { targets: List<String>, templates: List<ScanTemplate>, concurrency: Int, timeout_ms: Int, rate_limit: Int, follow_redirects: Bool, proxy: String }` | `[ ]` | `scan/src/engine.mn` | |
| 22 | Define `pub struct ScanResponse { url: String, status: Int, headers: Map<String, String>, body: String, elapsed_ms: Int }` | `[ ]` | `scan/src/engine.mn` | |
| 23 | Define `pub struct Finding { template_id: String, template_name: String, severity: String, url: String, matched_at: String, evidence: String, extracted: Map<String, List<String>>, timestamp: Int }` | `[ ]` | `scan/src/engine.mn` | |
| 24 | Implement `send_request(target: String, req: TemplateRequest, config: ScanConfig) -> Result<ScanResponse, ScanError>` — execute HTTP request via `net/http.mn` | `[ ]` | `scan/src/engine.mn` | |
| 25 | Implement `scan_target(target: String, template: ScanTemplate, config: ScanConfig) -> List<Finding>` — send requests, evaluate matchers, collect findings | `[ ]` | `scan/src/engine.mn` | |
| 26 | Implement `scan(config: ScanConfig) -> List<Finding>` — run all templates against all targets | `[ ]` | `scan/src/engine.mn` | Sequential for v1.3.0 |
| 27 | Implement `scan_stream(config: ScanConfig) -> Stream<Finding>` — stream findings as they arrive | `[ ]` | `scan/src/engine.mn` | |

### Severity & Reporting

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 28 | Define severity levels: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | `[ ]` | `scan/src/report.mn` | |
| 29 | Implement `findings_summary(findings: List<Finding>) -> Map<String, Int>` — count by severity | `[ ]` | `scan/src/report.mn` | |
| 30 | Implement `to_json_report(findings: List<Finding>) -> String` — JSON report output | `[ ]` | `scan/src/report.mn` | |
| 31 | Implement `to_csv_report(findings: List<Finding>, path: String) -> Result<Bool, ScanError>` | `[ ]` | `scan/src/report.mn` | |
| 32 | Implement `show_findings(findings: List<Finding>)` — pretty-print to stdout with severity colors | `[ ]` | `scan/src/report.mn` | `[CRITICAL]`, `[HIGH]`, etc. |
| 33 | Implement `to_yaml_report(findings: List<Finding>) -> String` — YAML report | `[ ]` | `scan/src/report.mn` | |

### Request Fingerprinting

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 34 | Implement `fingerprint_request(method: String, url: String, headers: Map<String, String>, body: String) -> String` — SHA256 hash of request | `[ ]` | `scan/src/fingerprint.mn` | For dedup + audit trail |
| 35 | Implement `fingerprint_response(status: Int, headers: Map<String, String>, body: String) -> String` — SHA256 hash of response | `[ ]` | `scan/src/fingerprint.mn` | |

### Built-in Templates

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 36 | Template: `tech-detect/server-header.yaml` — detect server tech from Server/X-Powered-By headers | `[ ]` | `scan/templates/tech-detect/` | |
| 37 | Template: `tech-detect/cms-detect.yaml` — detect WordPress, Joomla, Drupal from body patterns | `[ ]` | `scan/templates/tech-detect/` | |
| 38 | Template: `misconfig/directory-listing.yaml` — detect open directory listings | `[ ]` | `scan/templates/misconfig/` | |
| 39 | Template: `misconfig/cors-misconfiguration.yaml` — detect permissive CORS | `[ ]` | `scan/templates/misconfig/` | |
| 40 | Template: `exposure/sensitive-files.yaml` — check for .env, .git/config, backup files | `[ ]` | `scan/templates/exposure/` | |
| 41 | Template: `exposure/error-pages.yaml` — detect verbose error pages leaking stack traces | `[ ]` | `scan/templates/exposure/` | |
| 42 | Template: `vuln/open-redirect.yaml` — test for open redirect via common params | `[ ]` | `scan/templates/vuln/` | |
| 43 | Template: `headers/security-headers.yaml` — check for missing CSP, HSTS, X-Frame-Options | `[ ]` | `scan/templates/headers/` | |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 44 | Test: YAML template parsing — all fields extracted correctly | `[ ]` | `scan/tests/test_template.py` | |
| 45 | Test: template variable interpolation | `[ ]` | `scan/tests/test_template.py` | |
| 46 | Test: status matcher — match/no-match | `[ ]` | `scan/tests/test_matcher.py` | |
| 47 | Test: body matcher — contains string, AND/OR logic | `[ ]` | `scan/tests/test_matcher.py` | |
| 48 | Test: regex matcher — pattern match on body | `[ ]` | `scan/tests/test_matcher.py` | |
| 49 | Test: header matcher — header value contains | `[ ]` | `scan/tests/test_matcher.py` | |
| 50 | Test: negative matcher — inverted logic | `[ ]` | `scan/tests/test_matcher.py` | |
| 51 | Test: extractor — regex capture groups | `[ ]` | `scan/tests/test_extractor.py` | |
| 52 | Test: scan_target with mock response — finding produced | `[ ]` | `scan/tests/test_engine.py` | |
| 53 | Test: JSON/CSV/YAML report generation | `[ ]` | `scan/tests/test_report.py` | |
| 54 | Test: request fingerprinting deterministic | `[ ]` | `scan/tests/test_fingerprint.py` | |
| 55 | Test: built-in templates parse without errors | `[ ]` | `scan/tests/test_builtin.py` | |

**Done when:** Scanner loads YAML templates, sends HTTP requests, evaluates matchers,
extracts evidence, produces findings with severity classification, and outputs
JSON/CSV/YAML reports. 8+ built-in templates ship with the package.

---

## Phase 6 — `security/fuzz` — Fuzzing Primitives
**Status:** `Not Started`
**Priority:** MEDIUM — useful for security testing, builds on scanner infrastructure
**Platform:** Both (external package: `github.com/Mapanare-Research/fuzz`)
**Effort:** Medium (3-5 days)

Mutation-based fuzzing primitives. Not coverage-guided (that requires LLVM sanitizer
integration, deferred to v2.0). Focus on HTTP parameter fuzzing using wordlists.

### Mutation Strategies

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Implement `mutate_string(input: String, strategy: String) -> List<String>` — apply mutation | `[ ]` | `fuzz/src/mutate.mn` | Strategies: "flip_case", "repeat", "truncate", "null_byte", "overflow", "unicode" |
| 2 | Implement `flip_case(input: String) -> String` — toggle ASCII case | `[ ]` | `fuzz/src/mutate.mn` | |
| 3 | Implement `repeat_string(input: String, n: Int) -> String` — repeat input N times | `[ ]` | `fuzz/src/mutate.mn` | Buffer overflow testing |
| 4 | Implement `null_byte_inject(input: String) -> String` — inject `\0` at various positions | `[ ]` | `fuzz/src/mutate.mn` | |
| 5 | Implement `boundary_values(input_type: String) -> List<String>` — common boundary values for type | `[ ]` | `fuzz/src/mutate.mn` | Int: 0, -1, MAX_INT, MIN_INT; String: empty, very long, unicode |

### Wordlists

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Implement `load_wordlist(path: String) -> Result<List<String>, FuzzError>` — load one word per line | `[ ]` | `fuzz/src/wordlist.mn` | |
| 7 | Implement `builtin_sqli() -> List<String>` — common SQL injection payloads | `[ ]` | `fuzz/src/wordlist.mn` | `' OR 1=1--`, `" OR ""="`, etc. |
| 8 | Implement `builtin_xss() -> List<String>` — common XSS payloads | `[ ]` | `fuzz/src/wordlist.mn` | `<script>alert(1)</script>`, `<img onerror=...>`, etc. |
| 9 | Implement `builtin_traversal() -> List<String>` — path traversal payloads | `[ ]` | `fuzz/src/wordlist.mn` | `../../etc/passwd`, `..%2f..%2f`, etc. |
| 10 | Implement `builtin_command_injection() -> List<String>` — command injection payloads | `[ ]` | `fuzz/src/wordlist.mn` | `; ls`, `| cat /etc/passwd`, `` `id` ``, etc. |

### HTTP Parameter Fuzzing

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 11 | Define `pub struct FuzzConfig { target_url: String, method: String, params: List<String>, wordlist: List<String>, headers: Map<String, String>, timeout_ms: Int, delay_ms: Int }` | `[ ]` | `fuzz/src/http_fuzz.mn` | |
| 12 | Define `pub struct FuzzResult { payload: String, param: String, status: Int, body_length: Int, elapsed_ms: Int, interesting: Bool }` | `[ ]` | `fuzz/src/http_fuzz.mn` | |
| 13 | Implement `fuzz_params(config: FuzzConfig) -> List<FuzzResult>` — fuzz each param with each payload | `[ ]` | `fuzz/src/http_fuzz.mn` | |
| 14 | Implement `detect_interesting(baseline: FuzzResult, current: FuzzResult) -> Bool` — compare status code, body length, response time vs baseline | `[ ]` | `fuzz/src/http_fuzz.mn` | Different status or significantly different body length = interesting |
| 15 | Implement `fuzz_report(results: List<FuzzResult>) -> String` — summarize interesting findings | `[ ]` | `fuzz/src/http_fuzz.mn` | |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 16 | Test: mutation strategies produce expected output | `[ ]` | `fuzz/tests/test_mutate.py` | |
| 17 | Test: boundary values for int, string types | `[ ]` | `fuzz/tests/test_mutate.py` | |
| 18 | Test: builtin wordlists are non-empty and contain expected payloads | `[ ]` | `fuzz/tests/test_wordlist.py` | |
| 19 | Test: load_wordlist from file | `[ ]` | `fuzz/tests/test_wordlist.py` | |
| 20 | Test: detect_interesting flags status code differences | `[ ]` | `fuzz/tests/test_http_fuzz.py` | |
| 21 | Test: fuzz_report summarizes findings | `[ ]` | `fuzz/tests/test_http_fuzz.py` | |

**Done when:** Fuzzer can mutate strings, load wordlists, fuzz HTTP parameters,
detect interesting responses, and produce reports. Built-in payloads for SQLi, XSS,
path traversal, and command injection ship with the package.

---

## Phase 7 — Integration Testing & Release
**Status:** `Not Started`
**Priority:** GATE
**Platform:** Both
**Effort:** Large (1-2 weeks)

### Cross-Module Integration

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | E2E: server with session auth → login → access protected endpoint → logout | `[ ]` | `tests/e2e/test_web_app.py` | |
| 2 | E2E: server with JWT auth → issue token → access API → reject expired | `[ ]` | `tests/e2e/test_web_app.py` | |
| 3 | E2E: server with rate limiting → normal requests pass → burst gets 429 | `[ ]` | `tests/e2e/test_web_app.py` | |
| 4 | E2E: server with SSE → client connects → server sends 5 events → client receives all | `[ ]` | `tests/e2e/test_web_app.py` | |
| 5 | E2E: template rendering → load template → render with context → verify HTML output | `[ ]` | `tests/e2e/test_web_app.py` | |
| 6 | E2E: crawl → scan pipeline — crawl local server, feed URLs to scanner | `[ ]` | `tests/e2e/test_crawl_scan.py` | |
| 7 | E2E: scanner with built-in templates against test server with known vulnerabilities | `[ ]` | `tests/e2e/test_crawl_scan.py` | |
| 8 | E2E: fuzzer against test endpoint, detect injected vulnerability | `[ ]` | `tests/e2e/test_fuzz.py` | |

### Security Audit

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Audit: session ID randomness — verify crypto-quality random | `[ ]` | (manual) | |
| 10 | Audit: cookie security — Secure, HttpOnly, SameSite defaults | `[ ]` | (manual) | |
| 11 | Audit: template engine XSS — escape filter prevents injection | `[ ]` | `tests/stdlib/test_template_security.py` | |
| 12 | Audit: scanner rate limiting — verify it cannot be used for DoS | `[ ]` | (manual) | Mandatory rate limit, no bypass |
| 13 | Audit: HTML parser C runtime — buffer overflow checks | `[ ]` | (manual) | |
| 14 | Audit: YAML template injection — scanner doesn't execute arbitrary code from templates | `[ ]` | `tests/e2e/test_template_safety.py` | |

### Performance Benchmarks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 15 | Benchmark: server request throughput (requests/sec) | `[ ]` | `benchmarks/bench_server.py` | |
| 16 | Benchmark: crawler pages/sec on local server | `[ ]` | `benchmarks/bench_crawl.py` | |
| 17 | Benchmark: scanner templates/sec evaluation | `[ ]` | `benchmarks/bench_scan.py` | |

### Documentation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 18 | Update `docs/stdlib.md` with server v2 modules | `[ ]` | `docs/stdlib.md` | |
| 19 | Write crawler package README with examples | `[ ]` | `crawl/README.md` | |
| 20 | Write scanner package README with template authoring guide | `[ ]` | `scan/README.md` | |
| 21 | Write fuzzer package README | `[ ]` | `fuzz/README.md` | |
| 22 | Update ROADMAP.md release history | `[ ]` | `docs/roadmap/ROADMAP.md` | |

### Pre-Release Checklist

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 23 | Full test suite green: `make test` — target 4,500+ tests | `[ ]` | | |
| 24 | Lint clean: `make lint` | `[ ]` | | |
| 25 | All security audit findings resolved | `[ ]` | | |
| 26 | CHANGELOG.md updated | `[ ]` | | |
| 27 | VERSION file bumped to `1.3.0` | `[ ]` | | |

### Release

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 28 | Tag `v1.3.0` on `main` | `[ ]` | | |
| 29 | GitHub Release | `[ ]` | | |
| 30 | PyPI release | `[ ]` | | |
| 31 | crawl package v1.0 release | `[ ]` | | |
| 32 | scan package v1.0 release | `[ ]` | | |
| 33 | fuzz package v1.0 release | `[ ]` | | |

**Done when:** Web framework, crawler, scanner, and fuzzer all work end-to-end.
Crawl → scan pipeline verified. Security audit clean. All packages released.

---

## Phase Dependencies

```
Phase 1 (C Runtime: HTML + timing) ──┬──→ Phase 4 (net/crawl) ──→ Phase 5 (security/scan)
                                      │                                    ↑
Phase 2 (Server v2) ─────────────────┤                           Phase 6 (security/fuzz)
                                      │                                    ↑
Phase 3 (Templates) ─────────────────┘                           Phase 7 (Integration)
                                                                           ↑
                                                                     All phases
```

### Priority Order

1. **Phase 1** — C Runtime (unblocks crawler HTML parsing)
2. **Phase 2** — Server v2 (sessions, auth — independent, biggest piece)
3. **Phase 3** — Templates (depends on server, small)
4. **Phase 4** — Crawler (depends on Phase 1 for HTML parsing)
5. **Phase 5** — Scanner (depends on Phase 4 for URL discovery)
6. **Phase 6** — Fuzzer (independent, can parallel with 4/5)
7. **Phase 7** — Integration + Release

### Parallelization Strategy

```
Week 1-2:  Phase 1 (WSL) + Phase 2 (Windows) — in parallel
Week 2-3:  Phase 3 (Windows) + Phase 2 continued
Week 3-5:  Phase 4 (crawler) + Phase 6 (fuzzer) — in parallel
Week 5-7:  Phase 5 (scanner, depends on crawler)
Week 7-8:  Phase 7 (integration + release)
```

---

## New Files Created by v1.3.0

### C Runtime
- `runtime/native/mapanare_html.c` — lexbor HTML parser bindings
- `runtime/native/mapanare_html.h` — Header
- `runtime/native/build_html.py` — Build script

### Stdlib Modules (all `.mn`)
- `stdlib/net/http/cookie.mn` — Cookie parsing/setting
- `stdlib/net/http/session.mn` — Session management
- `stdlib/net/http/auth.mn` — Authentication middleware (Basic, Bearer, JWT, cookie)
- `stdlib/net/http/ratelimit.mn` — Rate limiting
- `stdlib/net/http/sse.mn` — Server-Sent Events
- `stdlib/net/http/body.mn` — Request body parsing (form, multipart, URL encoding)
- `stdlib/net/http/config.mn` — YAML-based server config
- `stdlib/net/http/template.mn` — Template engine

### Crawler Package (`crawl/`)
- `crawl/src/config.mn`, `page.mn`, `url.mn`, `extract.mn`, `robots.mn`, `frontier.mn`, `engine.mn`, `persist.mn`

### Scanner Package (`scan/`)
- `scan/src/template.mn`, `matcher.mn`, `extractor.mn`, `engine.mn`, `report.mn`, `fingerprint.mn`
- `scan/templates/` — 8 built-in YAML scan templates

### Fuzzer Package (`fuzz/`)
- `fuzz/src/mutate.mn`, `wordlist.mn`, `http_fuzz.mn`

---

## Estimated Total Task Count

| Phase | Tasks | Tests | Total |
|-------|-------|-------|-------|
| 1: C Runtime | 21 | 4 | 25 |
| 2: Server v2 | 36 | 12 | 48 |
| 3: Templates | 10 | 7 | 17 |
| 4: Crawler | 30 | 7 | 37 |
| 5: Scanner | 35 | 12 | 47 |
| 6: Fuzzer | 15 | 6 | 21 |
| 7: Integration | 22 | 11 | 33 |
| **Total** | **169** | **59** | **228** |

---

## Context Recovery

| Date | Phase | Last Task | Next Task | Notes |
|------|-------|-----------|-----------|-------|
| | | | | |
