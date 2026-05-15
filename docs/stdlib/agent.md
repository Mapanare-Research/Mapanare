# `stdlib/agent` — supervision

> **Module status (v5.42.0):** ships the supervision *strategy library*
> (`stdlib/agent/supervisor.mn`) plus the C runtime substrate for
> push-based child-exit notifications (As.6 in
> `runtime/native/mapanare_runtime.{c,h}`). The full
> "spawn-restart-via-Mapanare-fn" ergonomic — where you pass a
> factory closure to the supervisor and it spawns and restarts
> children for you — is deferred to v5.43.0 because the
> language-level wiring (fn-typed parameter invocation through the
> `@agent` surface) needs more compiler work than v5.42.0 budgeted
> for. What ships at v5.42.0 is enough to build self-healing
> systems today: the strategy logic answers "which children should
> I restart?" and the orchestrator side does the actual respawn.

## Quick reference

```mn
// Build a supervisor and register children.
let s0 = new_supervisor(STRATEGY_ONE_FOR_ONE(), 5, 60)
let s1 = add_child(s0, new_child_spec(101, "fetcher", RESTART_PERMANENT()))
let s2 = add_child(s1, new_child_spec(102, "parser",  RESTART_PERMANENT()))
let s3 = add_child(s2, new_child_spec(103, "writer",  RESTART_PERMANENT()))

// A child crashed — ask the supervisor what to do.
let t = supervisor_handle_exit(s3, 102, EXIT_CRASHED(), "parser panic")
// t.sup           — updated supervisor state
// t.decision.ids_to_restart  — agent ids the orchestrator should respawn
// t.decision.escalate        — true if restart-limit window exceeded
// t.decision.no_op           — true if the policy says don't restart
```

## Strategies

Three `RestartStrategy` values match Erlang/OTP semantics exactly:

| Strategy | Behavior on child failure | When to use |
|---|---|---|
| `OneForOne`  | Restart only the failed child | Independent workers — failures of one don't affect others |
| `RestForOne` | Restart failed child + every child registered after it | Pipelines where downstream stages depend on upstream order |
| `OneForAll`  | Restart every child in the group | Tightly-coupled groups — any failure invalidates shared state |

Match Erlang's `one_for_one`, `rest_for_one`, `one_for_all`. Don't
invent a fourth — the design space is exhausted by these three.

## Restart policies (per-child)

Each `ChildSpec` carries a `RestartPolicy` controlling whether the
strategy fires for *this* child's exit:

| Policy | Restart on Normal exit? | Restart on Crashed/Killed? |
|---|---|---|
| `Permanent` | yes | yes |
| `Transient` | no  | yes |
| `Temporary` | no  | no  |

`Permanent` is the default for application-level workers — same as
Erlang's default.

## Restart limits

`new_supervisor(strategy, max_restarts, max_window_secs)` — if
the supervisor accumulates more than `max_restarts` restarts within
`max_window_secs` seconds, the next call to `supervisor_handle_exit`
returns `decision.escalate = true`. The orchestrator should treat
this as "*this* supervisor itself failed" and surface up to its own
parent supervisor.

The window is a discrete approximation, not a true sliding window
— Erlang's supervisor uses the same approximation. Empirically, for
crash-loop detection it's equivalent.

### Backoff

`with_backoff(s, initial_ms, max_ms)` — wraps a supervisor with
exponential backoff. After each restart the orchestrator should
call `next_backoff_ms(s)` and `delay_ms` for that long before
respawning. The progression doubles from `initial_ms` up to a
`max_ms` cap.

```mn
let s = with_backoff(new_supervisor(...), 100, 8000)
// 1st restart → 100 ms,  2nd → 200,  3rd → 400 ... cap 8000
```

`reset_consecutive_restarts(s)` — call when a child runs cleanly
for long enough; resets the backoff progression.

## Push-based notification (As.6 substrate)

The C runtime grew four new APIs at v5.42.0 to wire up push-based
ChildExited delivery:

```c
void mapanare_agent_set_parent(mapanare_agent_t *child, mapanare_agent_t *parent);
void mapanare_agent_set_on_exit(mapanare_agent_t *child,
                                 mapanare_on_exit_fn on_exit, void *cb_data);
void mapanare_agent_set_exit_reason(mapanare_agent_t *self,
                                     mapanare_exit_reason_kind_t kind,
                                     const char *reason);
void mapanare_agent_get_exit_reason(mapanare_agent_t *child,
                                     mapanare_exit_reason_kind_t *kind_out,
                                     char *reason_out);
```

The Mapanare-side trampoline `__mn_supervisor_install_child_hook`
in the runtime takes two opaque agent handles (cast through `Int`
in Mapanare) and wires them up: when the child enters `FAILED`,
the runtime allocates a `__mn_child_exit_msg_t { agent_id, kind,
reason[256] }` and `mapanare_agent_send`s it to the parent's
inbox.

The full agent-handle propagation through `@agent`-spawned values
needs a small compiler bridge; until v5.43.0 lands it, the bridge
is exercisable from C-level orchestration code (see
`/tmp/as6_smoke.c` in the v5.42.0 SESSION_REPORT).

## Cookbook

### Recipe 1 — single worker pool, OneForOne

```mn
fn build_pool(size: Int) -> Supervisor {
    let mut s = new_supervisor(STRATEGY_ONE_FOR_ONE(), size * 2, 30)
    let mut i: Int = 1
    while i <= size {
        s = add_child(s, new_child_spec(i, "worker-" + str(i), RESTART_PERMANENT()))
        i = i + 1
    }
    da s
}
```

When a worker crashes, only that worker is restarted. The pool
absorbs up to `2 * size` restarts within 30 seconds before
escalating. See `examples/agents/worker_pool_supervised.mn` for
the full pattern.

### Recipe 2 — ordered pipeline with RestForOne

```mn
let s0 = new_supervisor(STRATEGY_REST_FOR_ONE(), 5, 60)
let s1 = add_child(s0, new_child_spec(1, "reader",      RESTART_PERMANENT()))
let s2 = add_child(s1, new_child_spec(2, "transformer", RESTART_PERMANENT()))
let s3 = add_child(s2, new_child_spec(3, "writer",      RESTART_PERMANENT()))
```

If the transformer crashes, RestForOne restarts transformer +
writer (preserving message ordering); the reader keeps running.

### Recipe 3 — exponential backoff against a flaky downstream

```mn
let s = with_backoff(
    new_supervisor(STRATEGY_ONE_FOR_ONE(), 10, 60),
    100,    // initial 100ms
    8000    // cap 8s
)
```

After each restart, `next_backoff_ms(s)` returns 100, 200, 400,
... up to 8000. Call `delay_ms(next_backoff_ms(s))` between
respawn cycles in your orchestrator.

### Recipe 4 — graceful shutdown

```mn
// Walk children and send each a Shutdown system message; each
// child sets EXIT_SHUTDOWN as its reason via
// mapanare_agent_set_exit_reason() before exiting.
//
// The supervisor's handler sees EXIT_SHUTDOWN and the per-child
// policy of Transient or Temporary returns no_op — no restart
// cascade fires. Permanent children would re-restart, so for a
// real shutdown set every child's policy to Transient before
// initiating shutdown.
```

## What's not here yet

The following items were scoped against the v5.42.0 manifesto-arc
slot but explicitly deferred during Phase 0 audit:

- **Spawn-restart-via-Mapanare-fn ergonomic.** Pass a factory
  closure to the supervisor; supervisor spawns + restarts. Blocked
  on fn-typed parameter invocation reliability through Mapanare's
  lowering (the v5.37.0 Ht.\* lesson — registration-table
  workaround applies here too).
- **Dynamic child addition.** Erlang's `supervisor:start_child`.
  Static specs only at v5.42.0.
- **Distributed supervision.** Supervisors managing remote
  agents — slot for v5.43.0 distributed-agents work.
- **Process registry / `via` syntax.** Erlang's named-process
  lookup.

## Migration / coexistence notes

- The pre-v5.42.0 `mapanare_agent_t::restart_policy` /
  `max_restarts` (binary STOP/RESTART) is **untouched** and
  remains the *intra-agent* handler-error retry mechanism. It is
  orthogonal to v5.42.0 supervision: that policy decides whether
  the agent's worker thread retries the handler before
  transitioning to FAILED; v5.42.0 supervision decides what the
  *parent* does once FAILED has been reached.

- Existing agents not opted in via `mapanare_agent_set_on_exit`
  see no behavior change. The four new struct fields are zeroed
  by `mapanare_agent_init`'s `memset`; the `if (agent->on_exit)`
  guard at every FAILED transition site keeps the path empty.

## Distributed agents (v5.43.0 Da.\*)

> **v0 caveat.** v5.43.0 ships *distributed messaging*, not
> distributed *state*. There is no service registry, no
> replication, no consensus, no anycast across multiple nodes
> hosting the same agent-id. Static URLs only. Don't build a
> database with this. v5.44+ adds richer primitives in
> downstream packages.

v5.43.0 makes `agent.send` network-transparent. A `RemoteAgent`
is a typed handle to an agent on another machine, addressed by
URL:

```mn
let r = remote_agent_connect("tcp://10.0.0.7:9090/worker-1", key)
let payload: String = to_json::<Task>(my_task)
let r2 = remote_agent_send(r.handle, payload)
let recv = remote_agent_recv(r2.handle)
let reply: Reply = from_json::<Reply>(recv.frame.payload)
remote_agent_disconnect(recv.handle)
```

The same supervision semantics — a remote child can be supervised
by a local supervisor. Transport failures become structured
`RemoteExitReason` values that the supervisor's strategy function
matches on.

### URL syntax + scheme matrix

| Scheme   | Status at v5.43.0 | Notes                                  |
|----------|-------------------|----------------------------------------|
| `tcp://` | Supported         | Plaintext over TCP                     |
| `tls://` | Supported         | TLS via system OpenSSL (dlopen)        |
| `unix://`| Reserved          | Returns `UnsupportedScheme` at runtime |

URL form: `<scheme>://<host>:<port>/<agent-id>`. The agent-id is
a path segment; v5.43.0 rejects embedded `/` characters.

### MAPANARE_NODE_KEY — HMAC keying is mandatory

Every frame on the wire is signed with HMAC-SHA256 truncated to
16 bytes. The shared key comes from `MAPANARE_NODE_KEY` in the
environment and **must be at least 32 raw bytes**. Both endpoints
of a connection need the same key; mismatch is rejected before
any deserialization.

Generate a fresh key:

```bash
MAPANARE_NODE_KEY=$(openssl rand -hex 32)
```

The 16-byte HMAC truncation is RFC 4868 secure for keys ≥ 32
bytes. **Never** use a shorter key — `node_listen` and
`remote_agent_connect` reject sub-32-byte keys with `kind=3
NoKey`.

**Key rotation at v5.43.0**: deploy the new key in parallel
(both nodes get the updated env var simultaneously) then
restart. There is no in-band key-rotation handshake at v5.43.0
— that requires registry coordination and is downstream
package territory.

### Wire format (v1)

```
+-------+--------+----------+-----------+----------+
| u32   | u8 v=1 | u8 mt    | u64 seq   | 16 b hmac| <body>
| length|         |          | (BE)      | sha256-  |
| (BE)  |         |          |           | trunc16  |
+-------+--------+----------+-----------+----------+
                           [ body — JSON payload   ]
```

- `length` (u32 BE) covers everything after itself. Capped at
  100 MB; oversize frames rejected before allocation.
- `version` byte is the only escape hatch. v5.43.0 ships v1; v2
  reserves the right to change anything after the version byte.
- `msg_type` enum (append-only):
  `1=Send | 2=Reply | 3=Ping | 4=Pong | 5=ChildExited | 6=ProtoError`.
  Values 7–15 reserved for v1.x. 16+ require a v2 frame.
- `sequence` is a per-connection u64 monotonic counter starting
  at 1. Receivers track `last_seen` and reject `seq <= last_seen`
  with `kind=7 Replay`.
- `hmac` is the first 16 bytes of HMAC-SHA256(key, version ||
  msg_type || sequence_be || payload). Verified with
  `constant_time_eq` (timing-safe).

### Failure-mode matrix

| Variant                  | When                                  | Recommended action            |
|--------------------------|---------------------------------------|-------------------------------|
| `RemoteCrashed(msg)`     | Remote handler returned rc != 0       | Restart per child policy      |
| `RemoteUnreachable(msg)` | Heartbeat missed; transport dead      | Restart + attempt reconnect   |
| `RemoteShutdown`         | Remote agent exited cleanly           | Don't restart Transient policy|

The variant `RemoteUnreachable` is named distinctly from
NetworkError's `TransportLost` to avoid match-pattern collision
in concat-mode (the v5.43.0 lowerer disambiguates by name only).
Both names refer to the same operational event from different
layers.

The bridge to v5.42.0 supervision:

```mn
let exit_reason: RemoteExitReason = ...
let ce: ClassifiedExit = classify_remote_exit(exit_reason)
let transition = supervisor_handle_exit(sup, child_id, ce.exit_kind, ce.reason)
```

`RemoteCrashed` and `RemoteUnreachable` both classify as
`EXIT_CRASHED` so the supervisor's strategy decides per its
configured restart policy; the unreachable case adds a
`"transport-lost: "` prefix to `reason` for downstream telemetry.
`RemoteShutdown` classifies as `EXIT_SHUTDOWN` — `Transient`
policy treats this as no-op; `Permanent` restarts; `Temporary`
no-ops as well.

### Cookbook

#### 1. Two-node setup

Worker side (binds + accepts):

```mn
fn main() {
    let key = node_key_from_env()
    match node_listen("0.0.0.0", 9090, key) {
        Ok(listener) => {
            loop {
                match node_accept_one(listener) {
                    Ok(conn) => { /* dispatch via conn_recv_frame ... */ },
                    Err(e)   => { /* accept failed; continue */ }
                }
            }
        },
        Err(e) => { print("listen failed: " + ne_msg(e)); return }
    }
}
```

Coordinator side (connects + sends):

```mn
fn main() {
    let key = node_key_from_env()
    match remote_agent_connect("tcp://10.0.0.7:9090/worker-1", key) {
        Ok(r) => {
            let task_json = to_json::<Task>(my_task)
            match remote_agent_send(r, task_json) {
                Ok(after_send) => { remote_agent_disconnect(after_send) },
                Err(e)         => { print("send failed: " + ne_msg(e)); remote_agent_disconnect(r) }
            }
        },
        Err(e) => { print("connect failed: " + ne_msg(e)) }
    }
}
```

Both processes run with the same `MAPANARE_NODE_KEY` env var.

#### 2. Supervised remote worker

```mn
let sup = add_child(
    new_supervisor(STRATEGY_ONE_FOR_ONE(), 5, 60),
    new_child_spec(701, "remote-worker", RESTART_PERMANENT())
)

// On a heartbeat miss or crash detection:
let reason = RemoteUnreachable("pong window expired")
let ce = classify_remote_exit(reason)
let transition = supervisor_handle_exit(sup, 701, ce.exit_kind, ce.reason)
if !transition.decision.no_op {
    // Reconnect to the remote node + respawn the worker logic.
}
```

#### 3. Graceful shutdown across nodes

```mn
// Coordinator initiates shutdown by sending a typed shutdown msg.
let payload = to_json::<ShutdownCmd>(my_shutdown)
let r = remote_agent_send(handle, payload)

// Worker side (reading the frame, handling shutdown):
//   on receipt of ShutdownCmd, return rc == 0 to trigger
//   RemoteShutdown classification at the coordinator's
//   supervisor layer.
```

#### 4. Synchronous heartbeat watcher

```mn
// Periodic check (the user's cadence — typically PING_INTERVAL_MS):
match remote_agent_heartbeat_check(handle) {
    Ok(updated) => { /* pong received; updated has fresh last_seen_recv */ },
    Err(e) => {
        // Treat as RemoteUnreachable; route through supervisor.
        let reason = RemoteUnreachable(ne_msg(e))
        let ce = classify_remote_exit(reason)
        supervisor_handle_exit(sup, child_id, ce.exit_kind, ce.reason)
    }
}
```

### What's not here yet (v5.43.x candidates)

- **Async per-connection heartbeat task.** v5.43.0 ships the
  synchronous `remote_agent_heartbeat_check` primitive. v5.43.x
  auto-fires per-connection at `MAPANARE_NODE_PING_INTERVAL_MS`
  cadence once the agent runtime can spawn nameless background
  tasks reliably.
- **Auto-routing of inbound `MSG_CHILD_EXITED` frames** into a
  parent supervisor's inbox. v5.43.0 ships the conversion
  helpers (`encode_child_exited`, `decode_child_exited`,
  `classify_remote_exit`); the auto-route is v5.43.x.
- **Generic `RemoteAgent<T>` with auto-`to_json`.** v5.43.0
  takes the explicit-`to_json::<T>(msg)`-at-call-site fallback
  authorized by v5.40.0 PROMPT (the `_specialize_fn` body-walk
  fix is the v5.43.x prerequisite).
- ~~**Result<T, NetworkError> at every API boundary.**~~ **Shipped
  at v5.54.0 Cl.2** — v5.43.0's flat-tuple workaround
  (`NodeListenResult`, `RemoteConnectResult`, etc.) was removed
  after v5.46.0 Lf.\* closed the wrap-shape default bug; the public
  surface now returns `Result<NodeHandle, NetworkError>` /
  `Result<RemoteAgent, NetworkError>` / `Result<ConnRecvOk,
  NetworkError>` etc. **BREAKING** for v5.43.0–v5.53.x callers.
- **Service registry / discovery, replication, consensus,
  mTLS, dynamic key rotation, binary serde fast path.**
  Downstream package territory — v5.43.0 is "distributed v0".

### Performance characteristics

- Per-frame overhead: 26 bytes header + JSON payload. Round-trip
  latency on localhost loopback is ~1 ms for small messages.
- 1 MB messages round-trip cleanly through both the C transport
  layer and the JSON serde path. Larger messages need
  application-level chunking until v5.43.x ships a binary serde
  fast path.
- HMAC-SHA256 throughput: ~2 GB/s on a modern x86_64. At v5.43.0
  the HMAC is computed twice per frame (once at send, once at
  recv-side verify) — both are well below transport bandwidth.

## See also

- `runtime/native/mapanare_runtime.h` — full C runtime API
- `runtime/native/mapanare_node.h` — distributed-agents transport
  API (v5.43.0)
- `examples/agents/supervisor_strategy_demo.mn` — strategy library
  exercise
- `examples/agents/worker_pool_supervised.mn` — orchestration
  pattern
- `examples/agents/distributed_pool.mn` — coordinator + workers
  topology (v5.43.0)
- `examples/agents/heartbeat_demo.mn` — supervision interop with
  `RemoteCrashed` / `RemoteUnreachable` / `RemoteShutdown` (v5.43.0)
- `docs/roadmap/v5/v5.42.0/SESSION_REPORT.md` — v5.42.0 release
  notes including the Phase 0 PROMPT-deviation audit
- `docs/roadmap/v5/v5.43.0/PRE_PHASE_AUDIT.md` — v5.43.0 audit
  surfacing the server-side TLS gap + lowerer-bug findings
