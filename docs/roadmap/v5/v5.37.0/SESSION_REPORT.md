# v5.37.0 SESSION REPORT — Ht.\* HTTP App / router / middleware / streaming encoders

**Tagline.** Fourth release in the stdlib gap-close arc. Ships an
opt-in `App` container with path-pattern routing (`:name` parameters,
`*name` wildcards), a registration-table middleware list (Logger,
Cors, BodyLimit, RequestId, Custom), and RFC 7230 §4.1 chunked
transfer + Server-Sent Events encoders. Zero compiler edits. Zero
`mapanare/self/*.mn` source touches. Strict 3-stage fixed point
preserved at v5.36.0's 241,898 lines / 0 diff (32-release strict
streak from v5.7.1). Goldens 95/95.

**Decision.** Ship as v5.37.0 with explicit deviations from PROMPT
(closure-chain middleware → registration table; trie → ordered list
of compiled patterns; new `ws.mn` file → documentation of existing
`stdlib/net/websocket.mn` integration; bounded-RSS streamer → wire-
format encoders). Ht.5 (typed handler shorthand) deferred to v5.38.0+
pending Js.4.B drop-glue fix.

## Phase 0 — pre-flight findings (load-bearing)

Three blockers surfaced at Phase 0; all resolved before code shipped:

1. **Js.4 `from_json<T>` SEGV at runtime** (carry from v5.36.0,
   documented in that release's CHANGELOG as Js.4.B). Ht.5 cannot
   build on a broken serde. **→ Ht.5 deferred to v5.38.0+.**

2. **Function-value parameter invocation broken in both backends.**
   Spike `fn apply(f: fn(Int) -> Int, x: Int) -> Int { da f(x) }`:
   - Native `mnc-stage1`: emits invalid IR — `use of undefined
     value '%add_one0'` at the indirect-call site.
   - Python LLVM emitter: emits IR that links cleanly but **segfaults
     at runtime** on the indirect call.
   Same root cause as v5.35.0's deferred
   `transaction<T>(f: fn() -> Result<T, SqlError>)` shape — Mapanare's
   stdlib has no precedent for invoking fn-value parameters.
   **→ Ht.2 redesigned as a registration-table middleware** (variants
   instead of closures). User-extensible via `Custom(name)` dispatched
   through a string-keyed switch.

3. **Existing `stdlib/net/websocket.mn` already has a complete RFC
   6455 server-side implementation** — `ws_accept_upgrade`,
   `ws_recv_full` with fragmentation, masking, control-frame size
   cap, UTF-8 validation, `wss://` over TLS, `ws_echo_loop`. The
   PROMPT's net-new `stdlib/net/http/ws.mn` would have duplicated
   functionality. **→ Ht.3 ships as documentation only.** Autobahn
   fixture corpus deferred to v5.38.0+ (Ht.3.B).

Baseline GREEN: `make ci-gates` clean (9 sub-gates), goldens 95/95
in 11.5s, fixed-point STRICT (241,898 lines / 0 diff).

## What shipped

### Ht.1 — path-pattern router

`stdlib/net/http/router.mn` — single-file module per the v5.34.0 /
v5.35.0 stdlib pattern.

**Types.** `App { routes: List<RouteEntry>, middlewares:
List<Middleware>, route_count: Int }`. `RouteEntry { method, pattern,
segs: List<CompiledSeg>, handler: String, specificity:
Int, insertion_order: Int }`. `CompiledSeg { kind: Int, text:
String }` (kind 0=literal, 1=`:name`, 2=`*name`).

**Match.** `MatchedRoute { matched: Bool, handler: String, params_kv:
List<String>, method_allowed: Bool }`. `params_kv` is alternating
key/value as a List<String>, not a `Map<String, String>` — the v5.x
map-in-returned-payload drop-glue bug frees Maps before the caller
reads them. Lookup via `match_param(m, name)` /
`match_has_param(m, name)`.

**Priority.** Insertion is sorted on registration: literal segments
score 2, parameters score 1, wildcards score 0. Higher specificity
wins. Insertion order tie-breaks within the same specificity class.
Locked with `t_literal_beats_param` (registers `:id` first, request
to `/users/me` hits the literal handler) and
`t_param_beats_wildcard`.

### Ht.2 — registration-table middleware

`Middleware` enum variants:

```mn
| Logger
| Cors(String, String, String)        // origins, methods, headers
| BodyLimit(Int)
| RequestId
| Custom(String)
```

`app_use(app, mw) -> App` appends. `app_run_before(app, req) ->
MwOutcome` walks the chain, applying pre-handler effects; returns
either `MwContinue(req')` (transformed request) or
`MwShortCircuit(resp)` (skip rest of chain + handler).
`app_run_after(app, req, resp) -> Response` applies post-handler
effects.

**Short-circuit semantics — locked with explicit test.**
`app.use(BodyLimit(8))` against a 39-byte body returns
`MwShortCircuit(413 response)`. Verified that subsequent
`MwContinue`-only middleware (Logger, RequestId) do not run.

### Ht.4 — streaming encoders

`stdlib/net/http/streaming.mn`. Encoders, not bounded-RSS streamer
(see Deviations).

**Chunked.** `chunked_encode_one(payload)` returns
`{hex_size}\r\n{payload}\r\n`. `chunked_encode(chunks)` concatenates
non-empty chunks and appends `0\r\n\r\n` terminator.
`build_chunked_response(status, headers, chunks)` returns the
complete HTTP/1.1 response with status line + headers + body.
Auto-injects `Transfer-Encoding: chunked`; drops any pre-existing
`Content-Length` (RFC 7230 §3.3.1 — they cannot coexist).
`int_to_hex(n)` lowercase-hex helper.

**SSE.** `SseLite { id, event_type, data, retry_ms }` builder type.
`sse_lite_encode(event)` produces wire-format with one `data:` line
per `\n`-separated line of the data payload. Empty
`id`/`event_type`/`retry_ms<=0` fields are omitted.
`sse_lite_encode_stream(events, default_retry_ms)` adds an
optional top-of-stream `retry: N\n\n` reconnect hint.
`sse_response_headers()` returns the standard SSE header shape.

### Ht.6 — pytest harness + .mn test files

`tests/stdlib/test_http_router.py` mirrors v5.34/v5.35
test_time_dt.py / test_sq_sqlite.py: parameterized over three
`.mn` test files; each is concatenated with `router.mn` (and
`streaming.mn` for the streaming case), compiled via the Python
LLVM emitter, linked against `libmapanare_rt.a`, run, and asserted
to print `PASSED`.

| File | Cases | Coverage |
| --- | --: | --- |
| `stdlib/net/http/tests/test_router.mn` | 12 | literal / param / two-param / wildcard / priority overlap (literal > param, param > wildcard) / method dispatch / 404 / 405 / `app_pick` |
| `stdlib/net/http/tests/test_middleware.mn` | 6 | body-limit short-circuit + pass-through, request-id mint + preserve, CORS post-handler injection, request-id post-handler echo |
| `stdlib/net/http/tests/test_streaming.mn` | 11 | hex boundary / chunked one+multi+empty-skip+terminator / response strips Content-Length / SSE single+multiline+id+event+retry / stream with default retry / response headers shape |

**29 assertions across 3 files. 3/3 pytest GREEN in 4.97s.**

### Ht.7 — walkthrough example

`examples/http/router_walkthrough.mn` exercises all four sections —
routing, middleware, chunked encoding, SSE — at the data-structure
level. Compiles + runs via the same router + streaming concatenation
harness. Printed output documents:

- Route table dispatch (literal beats param; param beats wildcard;
  405 vs 404 distinction).
- `RequestId` minting a 32-char hex id, `BodyLimit` short-circuiting
  to 413, `Cors` injecting `Access-Control-Allow-Origin: *` post-
  handler.
- Chunked-response head layout
  (`HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type:
  text/plain\r\n\r\n`).
- SSE wire format for a 2-event stream with id / event / multiline
  data fields.

### Ht.8 — cookbook

`docs/stdlib/http.md`. Covers quick reference, path patterns,
middleware (built-ins + Custom extension via
`dispatch_custom_middleware_before`), alternating-kv header API,
chunked encoding, SSE, streaming-aware logger pattern, WebSocket
integration via `stdlib/net/websocket.mn`, migration table from
legacy `Router` to new `App`, and explicit "what's NOT in v5.37.0"
section listing every deferred item.

## Deviations from PROMPT (load-bearing)

1. **Middleware as registration table, not closure chain** (Ht.2).
   PROMPT specified `type Middleware = fn(Request, Next) ->
   Response`. Indirect fn-value calls broken in both backends —
   see Phase 0 finding 2. Registration-table form ships today;
   closure-chain shape is a v5.38.0+ candidate when indirect
   fn-value calls land. User extension via `Custom(name)` +
   user-written `dispatch_custom_middleware_before(name, req)`
   switch.

2. **Ordered list of compiled patterns, not recursive trie** (Ht.1).
   Functionally equivalent — same API surface, same priority rule
   (literal > parameter > wildcard), same big-O on small route
   counts. The deviation removes a recursion risk in the MIR
   lowerer that the v5.37.0 release scope did not budget for.

3. **Ht.3 ships as documentation only.** Existing
   `stdlib/net/websocket.mn` has a complete RFC 6455 server
   implementation. New `stdlib/net/http/ws.mn` would duplicate
   working code. Cookbook in `docs/stdlib/http.md` shows the
   integration path. Autobahn fixture corpus deferred to v5.38.0+
   (Ht.3.B).

4. **Ht.4 ships encoders, not bounded-RSS streamer.** Existing
   `__mn_tcp_send_str(fd, data: String)` C-runtime export takes a
   whole string. A real bounded-RSS streaming writer needs
   `__mn_tcp_send_bytes(fd, ptr, len)` plus a chunk-pump driver
   loop. Encoders ship today; pump driver is v5.38.0 (Ht.4.B).
   The wire format is identical, so encoders compose forward
   without API churn.

5. **Ht.5 deferred to v5.38.0+** pending Js.4.B drop-glue fix.
   `from_json::<T>` builds but SEGVs at runtime in field
   extraction (v5.36.0 carry). Without working `from_json::<T>`,
   the typed-handler-shorthand auto-deserialization has no
   mechanism.

6. **Single-file modules** instead of directory layouts. Mirrors
   v5.34.0 / v5.35.0 pattern: cross-module function calls have
   known mangling/extern-propagation limitations. Tests run via
   concatenation harness.

7. **Headers as List<String> alternating-kv** instead of
   `Map<String, String>`. Same v5.x map drop-glue motivation as
   `MatchedRoute.params_kv`. Helpers `hdr_get` / `hdr_set` /
   `hdr_has` provide Map-style operations on top of the list.

## Bug-class workarounds documented during the work

Five v5.x carry-forward LOWs surfaced and were worked around in the
authoring cycle. All are documented in CHANGELOG `### Changed` and
the source-file preambles:

| Symptom | Workaround |
| --- | --- |
| Multi-line struct literal `new Foo {\n a: 1,\n b: 2\n}` rejected by parser | Write all `new Foo { ... }` literals on a single line. |
| `for x in some_list` not lowered (lower.mn:3458 — runtime `__iter_*` shims only know about ranges) | Use index-based `let mut i = 0; while i < len(xs) { let x = xs[i]; ... i = i + 1 }`. Map iteration via Spanish `cada k en map` works. |
| `segs = segs + [cur]; cur = ""; cur += ch` corrupts the appended list element via aliasing | Snapshot via `let snap: String = cur + ""` before appending. The `+ ""` routes through `__mn_str_concat` which allocates a fresh buffer. |
| `Map<String, String>` field in returned struct / enum payload freed by drop-glue before caller reads (`__mn_map_get` invalid read on freed memory) | Replace with `List<String>` alternating key/value. Lookup helpers `hdr_get` / `match_param`. |
| Function-value parameter invocation segfaults / produces invalid IR | Use registration-table dispatch (variants + named-handler switch) instead of closure chains. |

## Verification

```
$ make ci-gates                      # 9 sub-gates GREEN
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
  All 95 tests passed in 11.5s
$ python3 scripts/build_stage1.py    # rebuild stage1 post-bump
$ bash scripts/verify_fixed_point.sh
  ✓ FIXED POINT REACHED  stage2.ll == stage3.ll (241,898 lines, 0 diff)
$ python3 -m pytest tests/stdlib/test_http_router.py -v
  3 passed in 4.97s
```

## Source delta

| File | Status | LOC |
| --- | --- | --: |
| `stdlib/net/http/router.mn` | new | ~600 |
| `stdlib/net/http/streaming.mn` | new | ~250 |
| `stdlib/net/http/tests/test_router.mn` | new | ~140 |
| `stdlib/net/http/tests/test_middleware.mn` | new | ~120 |
| `stdlib/net/http/tests/test_streaming.mn` | new | ~140 |
| `tests/stdlib/test_http_router.py` | new | ~110 |
| `examples/http/router_walkthrough.mn` | new | ~150 |
| `docs/stdlib/http.md` | new | ~360 |
| `CHANGELOG.md` | filled v5.37.0 section | ~180 |
| `CLAUDE.md` | release notes entry | ~40 |
| `docs/SPEC.md` | header re-sync to v5.37.0 cut | ~14 |
| `VERSION`, README badges en/es/pt/zh-CN | bump_version.py mechanical | ~5 |

**~2,100 LOC total.** Substantial contribution but well below the
prompt's ~1,500 LOC `.mn` headline (the headline assumed all of
Ht.1–Ht.5 + Autobahn fixtures ships; v5.37.0 ships ~1,150 LOC `.mn`
with deferrals + ~960 LOC docs/tests/examples/changelog).

## Aggregate state entering v5.38.0

- **0 HIGH**.
- **2 MEDIUM**: Ht.5 typed handler waits on Js.4.B; macOS notarization
  carry from v5.33.0 Nu.2.
- **~7 LOW**: Ht.3.B Autobahn fixture corpus, Ht.4.B bounded-RSS
  streaming writer (needs `__mn_tcp_send_bytes` C export),
  closure-chain middleware (waits on indirect fn-value calls),
  native `Bytes` type, `Map<String, String>` drop-glue, plus the
  v5.36.0+ carry items.

Cadence: panel rule informational-only since v5.33.2 Cd.\*; lead
drives review timing.

## Tag policy

Per project memory: tag waits for explicit lead approval. v5.37.0
ships on `dev` at this commit; tag and push happen on lead's call.
