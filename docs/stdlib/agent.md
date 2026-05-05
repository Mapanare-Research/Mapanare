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

## See also

- `runtime/native/mapanare_runtime.h` — full C runtime API
- `examples/agents/supervisor_strategy_demo.mn` — strategy library
  exercise
- `examples/agents/worker_pool_supervised.mn` — orchestration
  pattern
- `docs/roadmap/v5/v5.42.0/SESSION_REPORT.md` — v5.42.0 release
  notes including the Phase 0 PROMPT-deviation audit
