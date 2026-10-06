# v5.43.0 — Da.\* — distributed agents v0

**Status:** PLANNING
**Type:** Runtime + stdlib feature. Network-transparent
`agent.send()` over TCP/TLS. The most ambitious release in v5.x.
**Breaking:** No. Existing local-only `agent.send` semantics
preserved; remote agents use a new `RemoteAgent<T>` type.
**Prerequisite:** v5.42.0 shipped (supervision); v5.39.0 (crypto
for HMAC-signed messages); v5.37.0 (HTTP / TCP infrastructure).
**Estimated effort:** 2 sessions. ~1500 LOC `.mn` + ~400 LOC C
runtime extensions. The biggest single release in v5.x.

---

## Why this exists

Mapanare's manifesto says first-class agents. A first-class
agent that can only run inside a single OS process is *less*
than first-class — it's library-class with extra steps. Real
agent systems span machines.

v5.43.0 makes this work:

```mn
let worker = RemoteAgent::connect("tcp://10.0.0.7:9090/worker-1")
worker.send(Task { ... })   // exactly the same surface as local agent.send
```

The same `send` syntax, the same supervision semantics (a
remote child can be supervised by a local supervisor — the
runtime handles transport failures as exit reasons), the same
typed messages.

This is "distributed agents v0" — minimum viable. Static
discovery (you tell it the address), no replicated state, no
consensus. v5.43.0 ships transport + protocol; richer
distributed primitives are downstream packages.

---

## Goals

1. **Da.1** — `RemoteAgent<T>` type: typed handle to an agent
   on another node, addressable by URL.
2. **Da.2** — Wire protocol: length-prefixed, versioned,
   HMAC-signed messages over TCP/TLS.
3. **Da.3** — Node runtime: agent server that listens on a port,
   accepts connections, dispatches incoming messages to local
   agents.
4. **Da.4** — Static discovery: agent URL = `tcp://host:port/agent-id`
   or `tls://...`. No registry / DNS-SD in v5.43.0.
5. **Da.5** — Failure handling: heartbeats, transport failures
   become structured `RemoteExitReason` (network-loss, timeout,
   protocol-mismatch).
6. **Da.6** — Supervision interop: local supervisor can own a
   remote child; child-crash on the remote side propagates
   through the protocol.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Da.1** | HIGH | **`RemoteAgent<T>` type in `stdlib/agent/remote.mn`.** `RemoteAgent::connect(url: String) -> Result<RemoteAgent<T>, NetworkError>`. Wraps a TCP/TLS connection + agent-id; `send(msg: T)` serializes via Js.4 reflection serde, frames per Da.2, writes to the connection. `receive() -> Result<T, NetworkError>` reads + deserializes. | 4h |
| **Da.2** | HIGH | **Wire protocol** in `stdlib/agent/remote_proto.mn`. Frame: `[u32 length][u8 version=1][u8 msg_type][u64 sequence][16 bytes HMAC-SHA256 truncated][JSON payload]`. Message types: `Send`, `Reply`, `Ping`, `Pong`, `ChildExited`, `ProtoError`. HMAC computed with shared key from env (`MAPANARE_NODE_KEY`); reject unsigned or mis-signed messages. Sequence number prevents replay. | 4h |
| **Da.3** | HIGH | **Node server** in `stdlib/agent/node.mn`. `Node::listen(addr: String, key: Bytes) -> Result<NodeHandle, _>`. Accepts incoming connections, performs HMAC-keyed handshake, dispatches messages to local agents by id. `node.register(id: String, agent: AgentRef)` exposes a local agent over the network. | 5h |
| **Da.4** | HIGH | **URL parsing + transport selection** in `stdlib/agent/url.mn`. `tcp://host:port/agent-id` for plaintext; `tls://host:port/agent-id` for TLS; future `unix:///socket/path/agent-id` slot. Static only — no DNS-SD or registry in v5.43.0. | 1h |
| **Da.5** | HIGH | **Heartbeats + failure handling.** Each connection runs a background heartbeat task: send Ping every 10s, expect Pong within 5s. On miss: connection closed, all in-flight `RemoteAgent` handles error their next `send`/`receive` with `NetworkError::Timeout`. Configurable timeouts via env. ~150 LOC. | 3h |
| **Da.6** | HIGH | **Supervision interop.** When a local supervisor owns a `RemoteAgent` child, child-crash messages from the remote node become local `ExitReason::Crashed` events. Transport failure ≠ child crash semantically — `RemoteExitReason::TransportLost` is a distinct shape that the supervisor can match on. | 3h |
| **Da.7** | HIGH (gate) | **Tests in `stdlib/agent/tests/test_remote.mn`.** Integration tests start two `Node` instances on random localhost ports, register agents, exchange messages. 10 cases: connect, send-receive, large message (1 MB), bad HMAC rejection, replay-attack rejection, network-loss simulation, ping-pong heartbeat, supervised remote child + crash, supervised remote child + transport-loss, mixed local/remote supervision tree. | 5h |
| **Da.8** | MEDIUM | **Runtime additions.** `runtime/native/mapanare_node.c` — TCP accept loop integrating with the existing event loop (epoll/kqueue/IOCP); TLS handshake helper using the existing dlopen OpenSSL path. Per-connection state machine. ~250 LOC. | 4h |
| **Da.9** | LOW | **Examples** at `examples/agents/`. `examples/agents/distributed_pool.mn`: a coordinator on one node distributes work to workers on other nodes; `examples/agents/heartbeat_demo.mn`: 2 nodes, kill one, observe failure detection. | 2h |
| **Da.10** | LOW | **Doc page** at `docs/stdlib/agent.md` (extend). Distributed-agents section: URL syntax, key management, deployment patterns, failure modes. Note explicitly: "v0 — no registry, no replicated state, no consensus. Don't build a database with this." | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.42.0 HEAD clean. Confirm
  supervisor + crypto stdlibs are healthy.
- **Phase 1** — Da.8 runtime first (TCP accept loop + TLS).
- **Phase 2** — Da.2 wire protocol + Da.4 URL parsing
  (self-contained).
- **Phase 3** — Da.3 node server + Da.1 RemoteAgent surface.
- **Phase 4** — Da.5 heartbeats + Da.6 supervision interop.
- **Phase 5** — Da.7 tests (the gate).
- **Phase 6** — Da.9 examples + Da.10 docs.
- **Phase 7** — Bump + tag.

---

## Out of scope

- **Service registry / discovery.** etcd / consul / zookeeper
  integration is downstream package territory; v5.43.0 takes
  static URLs only.
- **Replication / consensus / Raft.** Distributed *state* is
  not what v5.43.0 ships; it ships distributed *messaging*.
  CRDTs / Raft are downstream.
- **Mesh routing / multi-hop.** Direct connections only.
- **Anycast / load-balancing across multiple nodes hosting
  same agent-id.** Need a registry first.
- **Dynamic key rotation.** Static `MAPANARE_NODE_KEY` only;
  rotation requires registry coordination.
- **mTLS with client certificates.** TLS server-side only in
  v5.43.0; mTLS deferred.
- **gRPC compatibility.** Custom protocol; gRPC interop is a
  separate library.

---

## Risk

1. **The wire protocol is permanent.** Once shipped, breaking
   the v1 protocol means breaking deployed Mapanare nodes.
   Mitigation: v1 = "minimum viable, can be deprecated"; the
   `version` byte in every frame allows graceful v2 introduction
   later. Document the v1 surface carefully so future v2
   migration is clean.
2. **TLS dependency expands attack surface.** Every Mapanare
   node listening on the network is now exploit-target.
   Mitigation: HMAC keying is mandatory (no anonymous nodes;
   key required to even handshake); reject unsigned messages
   before any deserialization happens.
3. **JSON serialization perf for large messages.** A 100 MB
   message goes through Js.4 reflection serde in both
   directions. Mitigation: documented limit; future v5.43.x can
   add binary serde fast path. v0 keeps it simple.
4. **Supervisor across network is subtle.** "Child crashed" vs
   "I can't reach child" are different decisions for the
   supervisor strategy. Mitigation: explicit `RemoteExitReason`
   variants force users to handle both cases; documented best
   practice is "always treat TransportLost as restartable, treat
   crashes per usual strategy."
5. **Test flakiness on localhost-only test infrastructure.**
   Tests start 2 nodes on random ports; port conflicts,
   teardown races. Mitigation: each test gets its own
   `TempDirAndPort` fixture with retry-on-bind-fail.
6. **Self-host parser/lower scope.** Adding `RemoteAgent<T>` as
   a generic stdlib type doesn't require compiler edits, but
   the URL string handling and TLS plumbing is new
   infrastructure that the self-host needs to compile through.
   Mitigation: stage2 + stage3 compilation through the new
   stdlib must remain green; verify after each phase.

---

## Success criteria

- ✅ Two Node instances on localhost successfully exchange
  messages.
- ✅ Bad-HMAC messages rejected without crash.
- ✅ Network-loss simulation produces `NetworkError::Timeout`
  cleanly.
- ✅ Local supervisor owning a remote child correctly handles
  both "remote child crashed" and "remote child unreachable."
- ✅ TLS connection works against a real cert (self-signed in
  test).
- ✅ 1 MB message round-trips successfully.
- ✅ 10 Da.7 test cases all green.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "agents are local-only" gap. First-class agents are now
  *truly* first-class.
- **Manifesto arc CLOSED for v5.x.** With supervision (v5.42.0)
  + distributed (v5.43.0), agents have production-grade
  primitives. The v6.0 conversation can begin after the package
  runway and closeout panel land.

**Inherits to v5.44.0:**
- Package-aware imports + stdlib extraction runway (Ps.*): make
  installed packages real compiler import roots before v5 closes.
- Service registry / discovery (LOW; downstream).
- Replication / consensus (LOW; downstream).
- mTLS (LOW).
- Binary serde fast path (LOW).
- Dynamic key rotation (LOW).

**Aggregate state entering v5.44.0 (package-system runway):**
manifesto arc complete; stdlib gap-close complete;
foundation arc complete. v5.44.0 makes installed packages
compile like normal dependencies; v5.45.0 is the panel that
green-lights v6.0.
