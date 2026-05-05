# v5.43.0 — Da.\* — distributed agents v0; manifesto arc CLOSED

**Status:** READY (not tagged)
**Date:** 2026-05-05
**Type:** Runtime + stdlib feature. Network-transparent `agent.send`
over TCP/TLS. Third and final manifesto-arc release after v5.40.0
`ask` and v5.42.0 As.\* supervision.
**Breaking:** No. Existing local-only `agent.send` semantics
preserved; remote agents use a new `RemoteAgent` type.

---

## Headline

After v5.43.0 the manifesto's "first-class agents" pitch is no
longer library-class-with-extra-steps — agents span machines.

```mn
let r = remote_agent_connect("tcp://10.0.0.7:9090/worker", key)
let payload: String = to_json::<Task>(my_task)
let r2 = remote_agent_send(r.handle, payload)
remote_agent_disconnect(r2.handle)
```

The same supervision semantics — a remote child can be supervised
by a local supervisor, transport failures become structured
`RemoteExitReason` values that the supervisor's strategy function
matches on.

**Manifesto arc CLOSED for v5.x.** With `ask` (v5.40.0) +
supervision (v5.42.0) + distributed (v5.43.0), agents have
production-grade primitives. v5.44.0 package-system runway begins;
v5.45.0 panel green-lights v6.0.

---

## What shipped

- `stdlib/agent/url.mn` — `AgentUrl`, `NetworkError` (15-variant
  enum spanning every reachable failure mode), `parse_agent_url`
  returning flat `UrlParseResult` (lowerer-bug workaround — see
  below)
- `stdlib/agent/remote_proto.mn` (~290 LOC) — `Frame`,
  `encode_frame`, `decode_frame`, `validate_key`, msg_type +
  wire-format constants. HMAC-SHA256 truncated to 16 bytes,
  timing-safe verify via `constant_time_eq`, replay rejection.
- `stdlib/agent/node.mn` (~340 LOC) — listener API:
  `node_listen` / `node_listen_tls` / `node_accept_one` /
  `node_shutdown`; per-connection state: `NodeConnection`,
  `conn_send_frame`, `conn_recv_frame`, `conn_close`. Plus
  `ne_kind` / `ne_msg` helpers for variant introspection from
  fn parameters.
- `stdlib/agent/remote.mn` (~225 LOC) — client API:
  `RemoteAgent`, `remote_agent_connect`, `remote_agent_send`,
  `remote_agent_recv`, `remote_agent_disconnect`,
  `remote_agent_ping`, `remote_agent_send_typed_msg`.
- `stdlib/agent/supervision.mn` (~410 LOC) — heartbeat +
  supervision interop: `RemoteExitReason` 3-variant enum,
  `ChildExitedMsg` encode/decode for MSG=5 frames,
  `classify_remote_exit` bridging to v5.42.0
  `supervisor_handle_exit`, synchronous
  `remote_agent_heartbeat_check`, env-driven config readers.
- `runtime/native/mapanare_node.{c,h}` (~360 LOC) — net-new
  transport layer. 5 public exports + 2 MnString TLS server
  wrappers.
- `runtime/native/mapanare_io.{c,h}` extensions (~95 LOC) —
  server-side TLS additions: 5 new dlopen symbols
  (`TLS_server_method`, `SSL_accept`,
  `SSL_CTX_use_certificate_file`,
  `SSL_CTX_use_PrivateKey_file`,
  `SSL_CTX_check_private_key`) + 3 new public exports
  (`__mn_tls_server_ctx_new`, `__mn_tls_server_ctx_free`,
  `__mn_tls_accept`).
- `runtime/native/mapanare_core.c` — `__mn_str_chr` extended
  from 0..127 to 0..255 (Da.0 latent-bug fix).
- `tests/stdlib/test_distributed_agents.py` — Da.7 link-and-run
  pytest harness mirroring v5.42.0 `test_supervisor.py` concat
  pattern.
- `stdlib/agent/tests/test_dist_*.mn` — 4 link-and-run cases
  covering the 10 PROMPT-spec Da.7 cases.
- `examples/agents/distributed_pool.mn` — coordinator + workers
  topology (110 LOC).
- `examples/agents/heartbeat_demo.mn` — supervision interop with
  all 3 RemoteExitReason variants (85 LOC).
- `docs/stdlib/agent.md` — Distributed-agents section appended
  (~210 LOC: URL syntax, key management, wire format, failure-
  mode matrix, 4 cookbook recipes, v5.43.x roadmap, performance
  notes, v0 caveat box).

---

## PROMPT/PLAN deviations (load-bearing)

### Da.8 — server-side TLS scope expansion

**Premise error.** PLAN/PROMPT both presumed server-side TLS was
in the existing dlopen pattern. Phase 0 audit
(`PRE_PHASE_AUDIT.md`) verified empirically — only client-side
symbols (`SSL_connect`, no `SSL_accept`). `grep "SSL_accept"
runtime/native/mapanare_io.{c,h}` returned zero matches.

**Three options surfaced for lead approval.** Option A defer
`tls://` to v5.43.1; Option B add the 5 missing dlopen symbols
+ 3 new exports; Option C ship `tcp://`-only and document
"deploy a TLS-terminating sidecar" as the v0 story.

**Option B chosen.** Plaintext-only would have undermined the
security gate the PROMPT itself names ("HMAC keying mandatory ...
reject before deserialize"). ~95 LOC C addition; tests still
green; no architectural concerns. Implementation pattern matches
the existing client-side dlopen plumbing — no second OpenSSL link
path.

### Da.1 — generic `RemoteAgent<T>` deferred

**Premise error.** PROMPT spec includes generic `RemoteAgent<T>`
with auto-`to_json::<T>(msg)` inside `remote_agent_send<T>`. This
requires the v5.40.0-deferred Ai.1 fix (`_specialize_fn` body-walk
to substitute nested generic `CallExpr.type_args` through
specialized function bodies). Without that fix, the inner
`to_json::<T>` substitutes T with the literal type-variable name,
producing wrong-type encode behavior.

**Workaround.** v5.43.0 takes the explicit-`to_json`-at-call-site
fallback the v5.40.0 PROMPT explicitly authorized under the same
conditions. The user writes:

```mn
let payload = to_json::<Task>(my_task)   // user-side type-specific
remote_agent_send(handle, payload)        // takes pre-encoded String
```

Loses the typing convenience but preserves correctness. v5.43.x
picks up generic surface once Ai.1 lands.

### Da.5 + Da.6 — async heartbeat + auto-routing deferred

**Premise.** PLAN scopes (a) per-connection async heartbeat task
that fires independently and invalidates in-flight handles on Pong
miss, (b) auto-routing of inbound `MSG_CHILD_EXITED` frames into a
parent supervisor's inbox.

**Deferred.** Both require dedicated agent-runtime threads or fn-
typed callbacks — paths v5.43.0 has not stress-tested at this
stage of the arc. Risk: shipping unstable async paths could
trigger STRICT 3-stage fixed-point regression. v5.43.0 ships:

- **Synchronous** `remote_agent_heartbeat_check(r)` primitive.
  User invokes at their own cadence (recommended:
  PING_INTERVAL_MS in a watcher loop).
- **Conversion helpers** that make user-side orchestration
  tractable: `encode_child_exited` / `decode_child_exited` /
  `classify_remote_exit`. The user-orchestrated pattern: read
  frame → decode → classify → call `supervisor_handle_exit` →
  act on RestartDecision.

v5.43.x adds the auto-route once the inbox bridge is wired to
v5.42.0's As.6 substrate, and adds the per-connection async timer
once nameless background tasks spawn reliably.

### Three v5.x lowerer bugs surfaced + worked around

All three documented in commit messages with falsifiability
repros. All three blocked Phase 3's planned `Result<T, NetworkError>`
API surface.

**Bug 1.** `Result<COMPLEX_OK, NetworkError>` destructure corrupts
the Err variant tag when Ok is a non-trivial struct. v5.36.0
Js.0.B class — Result wrap-shape mismatch. `Result<Int, X>` works
correctly; `Result<NodeHandle, X>` returns Err with tag=0
(BadUrl) regardless of constructed value. **Falsifiability
repro:** `/tmp/diag_node_listen.mn` flips kind 3 (correct) → kind
1 (broken) on a single Int → NodeHandle return-type swap.

**Bug 2.** `match Err(e) { da Err(e) }` propagation rewrap also
corrupts the variant tag — same root cause as Bug 1 plus an
additional rewrap step. Visible even when `Result<Int,
NetworkError>` if the rewrap happens.

**Bug 3.** Nested 15-arm match on a destructured `e` from outer
`Err(e)` silently fails to fire any inner arm. 3-arm and 10-arm
matches in the same position work; 15+-arm matches in this
position silently no-fire. Variant-name collision with another
in-scope enum (e.g. NetworkError vs RemoteExitReason both having
`TransportLost`) also triggers silent fall-through.

**Workaround.** Every public function returning a struct on
success uses a flat `(ok: Bool, value, err_kind: Int, err_msg:
String)` shape instead of `Result<T, NetworkError>`. The 15
NetworkError variants are encoded as integer kinds (1..15) at
the API boundary; the structured enum is preserved internally for
local matches over fn parameters (the only match-on-NetworkError
pattern that works reliably). Less elegant than `Result<T, E>` at
the call site but sidesteps all three bugs. v5.43.x picks up
`Result<T, NetworkError>` ergonomics once the lowerer fixes land.

**Tracked as v5.43.x candidate.** The lowerer fixes belong in
`mapanare/lower.py` near the v5.36.0 Js.0.B fix. Out of scope
here because (a) Phase 3 needed to ship the surface for Phases
4-7 to build on, (b) `lower.py` edits put STRICT 3-stage fixed
point at risk, (c) any compiler edit triggers self-host mirror
review.

### Variant rename: `TransportLost` → `RemoteUnreachable`

NetworkError already has `TransportLost` (Phase 1, url.mn). When
both enums are in scope under the concat-pattern, match arms
resolve "TransportLost" to the wrong enum's variant tag — the
v5.x lowerer disambiguates by name only at match-pattern
resolution. Same bug class as v5.39.7's variant-name collision
finding.

The semantic supervision distinction ("can't reach child" vs
"child crashed") is preserved; only the variant name differs.

---

## Da.0 — `__mn_str_chr` 0..127 → 0..255 (latent runtime bug)

`__mn_str_chr(int64_t code) -> MnString` in
`runtime/native/mapanare_core.c` accepted only 0..127. Per the
file-header note, Mapanare strings are explicitly byte arrays —
the 0..127 cap was defensive coding that confused
byte-strings-as-UTF-8.

**Symptom.** Any pure-Mapanare binary protocol producing header
bytes ≥ 128 silently became empty strings. Da.2 wire format
(version=1 + msg_type + u64 sequence_be — every byte except
sequence's low bytes can land in the 128..255 range) would have
been malformed without this fix.

**Latent.** `stdlib/net/websocket.mn` already implements RFC 6455
framing — but uses `str(byte0)` (decimal stringification, also
wrong for the wire) instead of `__mn_str_chr` and the websocket
tests are compile-only (never validate the wire format). The bug
class was hidden.

**Fix.** Extend range to 0..255. Use `__mn_str_from_parts` (with
explicit length) to preserve byte 0x00 (which `__mn_str_from_cstr`
would NUL-truncate). 23-LOC change in `mapanare_core.c`.

**Goldens 96/96 preserved post-fix.** No regressions on existing
ASCII users. The websocket.mn `str(byte)` decimal-stringification
bug is structurally adjacent but tracked separately as v5.44+;
v5.43.0 only fixes the runtime primitive.

---

## Test infrastructure

### `tests/stdlib/test_distributed_agents.py`

New pytest harness mirroring v5.42.0 `test_supervisor.py` concat
pattern exactly:
- Reads url + remote_proto + node + remote + supervisor +
  supervision modules in concat order.
- Prepends each test main body.
- Compiles via Python LLVM emitter + clang link against
  `libmapanare_rt.a`.
- Asserts "PASSED" + no "FAIL".

### 4 link-and-run cases at HEAD

| Case file                       | Da.7 cases covered   |
|---------------------------------|----------------------|
| `test_dist_proto.mn`            | 4 (HMAC tamper), 5 (replay) |
| `test_dist_url.mn`              | URL parsing surface  |
| `test_dist_node.mn`             | 1 (connect), 6 (network-loss simulation) |
| `test_dist_supervision.mn`      | 8 (remote crash), 9 (transport-loss), 10 (mixed local/remote tree) |

Cases 2 (basic send-receive) + 3 (1 MB round-trip) covered by
Phase 1 C smoke `/tmp/da8_smoke.c` (TSan-clean + ASan-clean).
Case 7 (ping-pong) covered by `remote_agent_heartbeat_check`
helper test in Phase 4.

**4/4 GREEN.** v5.42.0 supervision suite **9/9 GREEN.**

### Sanitizer + fuzz gates (UB-risk + network-risk tier)

- TSan run of `/tmp/da8_smoke.c` — **0 data races**.
- ASan run of `/tmp/da8_smoke.c` — **0 leaks**.
- Network fuzz `/tmp/da_fuzz.c` — 1000 iterations of randomized
  inputs (8 variants: oversize length, length=0, truncated reads,
  random body, sub-header, length-without-body, all-random,
  immediate close). **1001 accepts, 0 crashes, 0 hangs.** The
  DoS guard + length validation in `__mn_node_read_frame_str`
  held through every variant.
- Binary-compat regression
  `tests/runtime/test_agent_struct_compat.py` — **4/4 GREEN.**
  v5.43.0 adds zero new fields to `mapanare_agent_t`; binary
  compat trivially preserved by construction.

---

## Closeout checklist

- [x] STRICT 3-stage fixed point preserved (zero
  `mapanare/self/*.mn` source touches; verified via
  `verify_fixed_point.sh` post-bump)
- [x] Goldens 96/96 GREEN
- [x] `make ci-gates` GREEN (9 sub-gates)
- [x] `make lint` clean
- [x] Distributed-agents test suite 4/4 GREEN
- [x] Supervision suite 9/9 GREEN
- [x] Binary-compat 4/4 GREEN
- [x] TSan 0 races / ASan 0 leaks
- [x] Network fuzz 0 crashes / 1000 iter
- [x] `check_doc_freshness.py` GREEN (SPEC re-synced to v5.43.0)
- [x] `check_changelog_honesty.py` GREEN
- [x] Examples compile + run end-to-end

---

## Aggregate state entering v5.44.0

**0 HIGH** — manifesto arc CLOSED.

**3 MEDIUM:**
- Three v5.x lowerer bugs blocking ergonomic v5.43.x:
  Result<T, complex Err> wrap-shape mismatch, variant rewrap
  corruption, nested 15-arm match silent-no-fire. All have
  falsifiability repros at /tmp/diag_*.mn.
- macOS notarization carry from v5.33.0 Nu.2.
- Ai.1 `_specialize_fn` body-walk for generic stdlib functions
  calling generic intrinsics (carry from v5.40.0).

**~10 LOW:**
- Async per-connection heartbeat task
- Auto-route of MSG_CHILD_EXITED into supervisor inbox
- Generic RemoteAgent<T> with auto-to_json
- Service registry / discovery
- Replication / consensus / Raft
- mTLS with client certificates
- Dynamic key rotation
- Binary serde fast path
- IPv6 bracket URL syntax
- websocket.mn `str(byte)` decimal-stringification latent bug

---

## Manifesto arc CLOSED for v5.x

v5.40.0 + v5.42.0 + v5.43.0 ship the three pieces:

| Release  | Item       | Surface                                    |
|----------|------------|--------------------------------------------|
| v5.40.0  | Ai.\* `ask` | LLM call as a stdlib-level surface         |
| v5.42.0  | As.\* sup. | Erlang/OTP-style supervision strategies   |
| v5.43.0  | Da.\* dist.| Network-transparent agent.send             |

After v5.43.0 the manifesto's "first-class agents" pitch is
realized end-to-end. v5.44.0 begins the package-system runway;
v5.45.0 is the panel that green-lights v6.0.
