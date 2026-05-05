# v5.43.0 — Phase 0 PRE-PHASE AUDIT

**Status:** AUDIT — surfaces PLAN/PROMPT premise mismatches that
need lead alignment before Phase 1.

---

## Pre-flight (passed)

- `VERSION` = `5.42.0` ✓
- `git status --short` = `M AGENTS.md`, `M CLAUDE.md` (matches the
  release-prep working-tree pattern) ✓
- `make ci-gates` — all 9 sub-gates GREEN at HEAD ✓
- `python3 -m pytest tests/stdlib/test_supervisor.py -v` — **9/9
  PASSED in 3.39s** (v5.42.0 supervision suite intact). The
  PROMPT's "Phase 0 expects 9/9 GREEN" gate is met.
- v5.42.0 SESSION_REPORT closeout per CLAUDE.md: STRICT 3-stage
  fixed point at 242,338 lines / 0 diff; goldens 96/96.

---

## Existing network runtime (confirmed)

The PROMPT's premise that "the C runtime already has substantial
network infrastructure" is **correct** — and richer than the
PROMPT enumerates.

### TCP, in `runtime/native/mapanare_io.c`

Public surface (`MN_IO_EXPORT` linkage):

- `__mn_tcp_connect(host*, port) -> fd`            (line 126)
- `__mn_tcp_listen(host*, port, backlog) -> fd`    (line 159)
- `__mn_tcp_accept(listen_fd) -> fd`               (line 204)
- `__mn_tcp_send(fd, buf, len)`                    (line 214)
- `__mn_tcp_recv(fd, buf, len)`                    (line 225)
- `__mn_tcp_close(fd)`                             (line 236)
- `__mn_tcp_set_timeout(fd, ms)`                   (line 241)

MnString-wrapped variants (Mapanare-callable):

- `__mn_tcp_connect_str(MnString host, port) -> fd`  (line 903)
- `__mn_tcp_send_str(fd, MnString data) -> bytes`    (line 911)
- `__mn_tcp_recv_str(fd, max_len) -> MnString`       (line 917)
- `__mn_tcp_close_fd(fd)`                            (line 933)

**Gap:** there are **no MnString-form `__mn_tcp_listen_str` /
`__mn_tcp_accept_str`** wrappers. Da.8 likely needs `_str`
listen/accept variants to keep the call-shape symmetric with the
rest of the network surface, OR `stdlib/agent/node.mn` calls the
raw `int64_t` variants directly with explicit MnString → C string
conversion at the boundary. Pick one; document.

### TLS, in `runtime/native/mapanare_io.c` (dlopen OpenSSL)

Function pointers loaded at first use (line 283-294, plus
`__mn_tls_*` exports line 416-480, 938-969):

- `__mn_tls_init() -> int`                         (line 416)
- `__mn_tls_connect(fd, hostname*) -> ctx`         (line 420)
- `__mn_tls_read(ctx, buf, len)`                   (line 464)
- `__mn_tls_write(ctx, buf, len)`                  (line 472)
- `__mn_tls_close(ctx)`                            (line 480)
- `__mn_tls_connect_str(fd, MnString hostname)`    (line 938)
- `__mn_tls_write_str(ctx, MnString data)`         (line 946)
- `__mn_tls_read_str(ctx, max_len) -> MnString`    (line 952)
- `__mn_tls_close_fd(ctx, fd)`                     (line 969)

### Event loop, also in `mapanare_io.c`

The PROMPT speculates about a separate `runtime/native/mapanare_event_loop.{c,h}` and asks Phase 0 to verify
the filename. **It is not a separate file.** The event loop lives
inside `mapanare_io.c` (line 619+) with the cross-platform
multiplexer (epoll on Linux line 73; kqueue on macOS at compile
time; select fallback). Public surface in `mapanare_io.h`:

- `MnEventLoop` opaque type                        (line 165)
- `__mn_event_loop_new() -> MnEventLoop *`         (line 188)
- `__mn_event_loop_add_fd(loop, fd, events, user_data)`  (line 193)
- `__mn_event_loop_remove_fd(loop, fd)`            (line 199)
- `__mn_event_loop_run(loop)`                      (line 203)
- `__mn_event_loop_run_once(loop, timeout_ms)`     (line 208)
- `__mn_event_loop_stop(loop)`                     (line 212)
- `__mn_event_loop_free(loop)`                     (line 215)

Da.8 hooks listener sockets into this existing loop. The PROMPT's
guidance ("don't introduce a second loop") is structurally
correct.

---

## **PREMISE ERROR (load-bearing) — server-side TLS is NOT
implemented at HEAD**

**This is the biggest finding of Phase 0 and needs lead
alignment before Phase 1.**

The PLAN says: *"`tls://host:port/agent-id` for TLS"*.
The PROMPT says: *"TLS via the existing dlopen pattern. ... Server
cert via `MAPANARE_NODE_CERT` + `_KEY` env."*

Both presume **server-side** TLS is part of the existing dlopen
plumbing. It is not. The OpenSSL function pointers loaded at
`mapanare_io.c:283-294` are exclusively client-side:

```
fn_TLS_client_method, SSL_CTX_new, SSL_new, SSL_set_fd,
SSL_connect, SSL_read, SSL_write, SSL_shutdown,
SSL_CTX_set_default_verify_paths
```

**Missing for server-side TLS:**

- `TLS_server_method` (or `TLS_method` for both)
- `SSL_accept`
- `SSL_CTX_use_certificate_file` / `_chain_file`
- `SSL_CTX_use_PrivateKey_file`
- `SSL_CTX_check_private_key`

Confirmed by grep: `grep -n "SSL_accept\|SSL_CTX_use_certificate"
runtime/native/mapanare_io.{c,h}` returns **zero matches**.

**`stdlib/net/websocket.mn` confirms this gap indirectly** — the
file calls `__mn_tls_connect` for `wss://` but only as a *client*
(line 39 imports `__mn_base64_encode_str`; the upgrade handshake
flow is server-side over plaintext TCP only — `wss://` listener
support would have surfaced the same gap and is not present).

### Three options for v5.43.0

**Option A — defer `tls://` to v5.43.1.**
v5.43.0 ships `tcp://` only; `tls://` URL parses but `node_listen`
returns `NetworkError::TlsServerNotYetImplemented`. Client-side
TLS connect *to* a `tls://` listener is incoherent without a
listener, so `RemoteAgent::connect("tls://...")` also returns the
same error. Da.4 grammar reserves the slot. Da.10 doc explicitly
calls this out as v5.43.1 work.
- **Cost:** rescopes Da.8 down (~50 LOC less C), no new dlopen
  symbols.
- **Risk:** users who deploy across machines without a VPN have
  no encryption story until v5.43.1. The manifesto-arc closure
  headline is dampened ("distributed agents — but plaintext
  only").

**Option B — expand v5.43.0 to include server-side TLS.**
Add the 5 missing OpenSSL function pointers to the dlopen path
in `mapanare_io.c`; new `__mn_tls_accept(fd, ssl_ctx)` export;
new `__mn_tls_server_ctx_new(cert_path, key_path)` export. Da.8
budget grows from ~250 LOC C to ~330 LOC C. New test fixture:
self-signed cert generated at test setup (mkcert or openssl
shell-out).
- **Cost:** +1.5h on Da.8; +1 test case (TLS handshake); + a
  one-time self-signed-cert fixture in CI.
- **Benefit:** v5.43.0 ships the headline as PROMPT intends.

**Option C — Option A but document `tls://` as a downstream
package.**
Same as A but explicit: Mapanare's distributed-agents v0 is
plaintext + HMAC-only; TLS is provided by deploying the runtime
behind a TLS-terminating proxy (stunnel, haproxy, nginx) for
v0. v5.44.0+ revisits.
- **Cost:** zero v5.43.0 work; cleanest scope.
- **Risk:** "deploy a sidecar proxy" is friction the manifesto
  doesn't want to ask of users.

**Recommendation (mine, pending lead):** Option B. The PROMPT
explicitly puts security as a gate ("HMAC keying is mandatory
... reject unsigned messages before any deserialization runs");
shipping plaintext-only undermines that gate. ~80 LOC C is
within the Da.8 budget (PLAN allotted 4h; spike says 5.5h is
realistic with TLS server). Self-signed cert in CI is a 4-line
shell setup. **But this is the lead's call.**

---

## Existing supervision substrate (v5.42.0, confirmed healthy)

Public surface in `runtime/native/mapanare_runtime.h`:

- `mapanare_agent_set_parent(child, parent)`       (line 356-357)
- `mapanare_agent_set_on_exit(child, ...)`         (line 363)
- `mapanare_agent_set_exit_reason(self, kind, reason*)` (line 373)
- `mapanare_agent_get_exit_reason(child, kind_out, reason_out)`
  (line 380)
- `mapanare_exit_reason_kind_t` enum:
  `NORMAL | SHUTDOWN | KILLED | CRASHED`            (line 183)
- `mapanare_agent_t.last_exit_kind` field          (line 283)
- `mapanare_agent_t.last_exit_reason[256]`         (line 284)

The static C trampoline `__mn_supervisor_install_child_hook`
(per v5.42.0 SESSION_REPORT) routes child exits through the
supervisor inbox. **Da.6 must reuse this exact path** for remote
`ChildExited` frames — synthesize a local `__mn_child_exit_msg_t`
and route through the same mechanism rather than inventing a
parallel one.

`mapanare_agent_t` is **984 bytes on x86_64 Linux** post-v5.42.0
(488 → 984 with append-only extension). Any further field
additions in v5.43.0 must:
1. Be append-only (no insertion in the middle).
2. Be locked with the v5.41.0/v5.42.0 binary-compat regression
   test pattern at `tests/runtime/test_agent_struct_compat.py`.
3. Likely **be unnecessary**: per-connection state should live
   in `mn_node_conn_t` (Da.8) and in a `Map<agent_id, RemoteState>`
   on the `NodeHandle`, not on `mapanare_agent_t`.

`stdlib/agent/supervisor.mn` (419 LOC) is the v5.42.0 strategy
library. Da.6 supervision interop **plugs into it** by feeding
synthesized `ChildExitedMsg` shapes; do not fork or extend the
strategy library itself.

---

## Existing framing precedent

`stdlib/net/websocket.mn` (1167 LOC) implements RFC 6455 framing
on top of TCP/TLS. Structural patterns directly applicable to
Da.2:

- `WsFrame` struct with opcode + masked + mask_key + payload +
  payload_len fields                                (line 463)
- `encode_frame(frame) -> String`                   (line 475)
- `decode_frame(raw) -> FrameDecodeResult`          (line 553)
- Variable-length-prefix shape (1 byte / 2 byte / 8 byte
  payload-length encoding) — Da.2 simplifies to fixed 4-byte
  prefix
- Control frames + size cap + UTF-8 validation

Da.2's framing is structurally simpler (fixed length-prefix; no
masking on the wire — HMAC instead; control frames Ping/Pong
modeled the same way). **Read this file before drafting Da.2;
do not fork it.**

---

## Existing crypto stdlib (v5.39.0, confirmed)

`stdlib/crypto.mn` (line 70-460) — single-file module per
v5.x convention. Da.2 uses:

- `hmac_sha256(key, data) -> String`               (line 97; hex)
- `hmac_sha256_raw(key, data) -> String`           (line 102; raw bytes)
- `random_bytes(n) -> List<Int>`                   (line 280)
- `constant_time_eq(a, b) -> Bool`                 (line 360)

**Da.2 must use `_raw` + `constant_time_eq`** (not hex `_str` +
`==`) — timing-side-channel-safe HMAC compare is the load-bearing
security invariant.

---

## Da.\* item-by-item

| ID | Status | Notes |
|---|---|---|
| **Da.1** RemoteAgent<T> | NEW | ~250 LOC `stdlib/agent/remote.mn` |
| **Da.2** wire protocol | NEW | ~250 LOC `stdlib/agent/remote_proto.mn`. Frame layout fixed at PLAN; v1 byte permanent |
| **Da.3** Node server | NEW | ~300 LOC `stdlib/agent/node.mn`; per-connection state machine |
| **Da.4** URL parsing | NEW | ~80 LOC `stdlib/agent/url.mn`; reject `unix://` at runtime in v5.43.0 |
| **Da.5** heartbeats | NEW | ~150 LOC inside `node.mn`; per-connection Ping/Pong; env-configurable |
| **Da.6** supervision interop | PARTIAL | v5.42.0 substrate ships; need to route remote `ChildExited` through it; new `RemoteExitReason` enum |
| **Da.7** tests | NEW | ~600 LOC `.mn` + new pytest harness mirroring `tests/stdlib/test_supervisor.py` shape; 10 cases |
| **Da.8** runtime | PARTIAL/EXPANDED | TCP + event loop + client-TLS already shipped; **server-side TLS gap (see above)**; new `mapanare_node.c` ~250 LOC + ~80 LOC if Option B chosen |
| **Da.9** examples | NEW | ~200 LOC across two `.mn` files |
| **Da.10** docs | NEW | ~300 LOC `docs/stdlib/agent.md` extension |

---

## Compiler edits

**None expected.** v5.43.0 is pure stdlib + C runtime work. STRICT
3-stage fixed point preserved by construction iff
`mapanare/self/*.mn` is not touched. (The PROMPT's risk #6 is
correct: stage2 + stage3 must remain green through the new
stdlib; verify after each phase.)

## New C runtime exports estimated

- `__mn_node_accept(listen_fd) -> mn_node_conn_t *` (Da.8)
- `__mn_node_connect(host, port, tls, key) -> mn_node_conn_t *` (Da.8)
- `__mn_node_send_frame(c, msg_type, payload, len)`              (Da.8)
- `__mn_node_recv_frame(c, *out_msg_type, *out_payload, *out_len)` (Da.8)
- `__mn_node_close(c)`                                            (Da.8)

If Option B (server-side TLS) chosen, +2:

- `__mn_tls_server_ctx_new(cert_path, key_path) -> ctx`
- `__mn_tls_accept(fd, ctx) -> ssl_ctx`

**Total: 5–7 new C runtime exports.** Within v5.42.0's "4 new C
runtime exports" precedent for substrate-level releases. The
existing `mapanare_runtime.c` ABI is untouched (no new fields on
`mapanare_agent_t`); v5.42.0's binary-compat regression test
keeps passing trivially.

---

## Wire-format permanence — open questions for lead

PLAN frame layout: `[u32 length][u8 version=1][u8 msg_type]
[u64 sequence][16 bytes HMAC-SHA256 truncated][JSON payload]`.

Decisions to lock in PLAN before Phase 2 drafts encode/decode:

1. **Endianness:** PROMPT mentions `u32_be` and `u64_be`
   (network byte order) implicitly. Lock as **big-endian** for
   `length` and `sequence`. Document.
2. **`length` semantics:** PROMPT says "length covers everything
   after itself (version through end of payload)". Lock that.
   Means `length = 1 + 1 + 8 + 16 + payload_len`.
3. **Length cap:** PROMPT says "100 MB DoS guard". Lock as
   constant `MAPANARE_NODE_MAX_FRAME_BYTES = 100 * 1024 * 1024`.
4. **HMAC truncation:** 16 bytes (per PLAN + RFC 4868 minimum
   for SHA-256 truncated to ½). Lock with key length floor:
   `MAPANARE_NODE_KEY` must be **≥ 32 bytes** hex-encoded
   (= 64 hex chars). Reject shorter at `node_listen`/
   `remote_agent_connect`.
5. **`msg_type` enum** (PLAN values, lock append-only):
   `1 = Send | 2 = Reply | 3 = Ping | 4 = Pong | 5 =
   ChildExited | 6 = ProtoError`. Reserve 7-15 for v1.x; 16+
   require v2 frame.
6. **Payload encoding for control frames:** Ping/Pong have
   *empty string* payload (not `null`, not JSON `{}`). Saves
   bandwidth on the hot path. Document.
7. **`sequence` wraparound:** u64 monotonic per-connection.
   Wrap is theoretically possible but practically never (~146
   billion years at 4 GHz frame-issue rate). Document as "do
   not handle wraparound; if you somehow exhaust u64,
   disconnect."

---

## Recommendation summary for lead

1. **Bless or modify Option B** (server-side TLS, +1.5h on
   Da.8). My read: ship it. Plaintext-only undermines the
   security gate.
2. **Confirm the 7 wire-format invariants above** (endianness,
   length semantics, cap, HMAC truncation + key floor, msg_type
   numbers, payload-empty-for-control, no-wraparound).
3. **Confirm cadence:** v5.43.0 is the largest single release
   in v5.x and ships across 2 sessions per PLAN. The PROMPT's
   7-phase plan totals ~26h. Phase 1 (Da.8) is the longest
   single phase at 5h. Reasonable to split as session 1 =
   Phases 1+2+3 (Da.8 + Da.2 + Da.3 + Da.1 = wire + transport +
   surface), session 2 = Phases 4+5+6+7 (heartbeats +
   supervision interop + tests + examples + docs + bump).

---

## STOP CONDITIONS for Phase 1 entry

- [ ] Lead chooses Option A / B / C for `tls://`.
- [ ] Lead confirms (or modifies) the 7 wire-format invariants.
- [ ] Lead confirms session-split cadence.

Phase 1 cannot proceed until all three are answered, because:
- Da.8 C-runtime scope depends on TLS option.
- Da.2 framing implementation hard-codes the wire format.
- Multi-session work needs an agreed checkpoint shape.
