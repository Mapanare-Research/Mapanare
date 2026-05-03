# v5.42.0 — As.\* — agent supervision trees

**Status:** PLANNING
**Type:** Runtime + stdlib feature. Erlang-style supervision on
top of the existing agent runtime.
**Breaking:** No. Net-new types and functions.
**Prerequisite:** v5.41.0 shipped (tensor closeout).
**Estimated effort:** 1 session. ~600 LOC `.mn` + ~200 LOC C
runtime extensions.

---

## Why this exists

The existing agent runtime has lifecycle (start, send, receive,
fail) and a thread pool. Crashes propagate via exit reasons but
there's no *strategy* for what to do when an agent dies — apps
have to roll their own restart logic.

Erlang's "let it crash" philosophy works because supervision
trees give you principled answers: when a child dies, restart
just it (`one_for_one`), restart it and everything started after
it (`rest_for_one`), or restart everyone in the group
(`one_for_all`). Plus restart limits to prevent crash loops.

This is the natural next manifesto item after `ask`: agents are
already first-class, supervision makes them *production-grade*
first-class.

---

## Goals

1. **As.1** — `Supervisor` type: parent agent that owns a list
   of `ChildSpec`s and applies a `RestartStrategy`.
2. **As.2** — Three strategies: `OneForOne`, `RestForOne`,
   `OneForAll`. Match Erlang/OTP semantics exactly.
3. **As.3** — Restart limits + backoff: `max_restarts: Int,
   max_restart_window_seconds: Int`. If exceeded, supervisor
   itself crashes (escalates to its parent).
4. **As.4** — Exit reason propagation: child crashes carry
   structured `ExitReason { reason: String, payload: Option<JsonValue> }`
   to the supervisor's restart-decision logic.
5. **As.5** — Tests covering all three strategies, restart-limit
   exhaustion, and supervisor-of-supervisors (nested trees).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **As.1** | HIGH | **`Supervisor` type in `stdlib/agent/supervisor.mn`.** `struct Supervisor { children: List<ChildSpec>, strategy: RestartStrategy, max_restarts: Int, max_window_secs: Int }`. `Supervisor::start(spec) -> AgentRef`. The supervisor *is* an agent — runs in the same scheduler, exchanges system messages with children. | 3h |
| **As.2** | HIGH | **Restart strategies.** `enum RestartStrategy { OneForOne, RestForOne, OneForAll }`. Implementation: when a child sends `ChildExited(id, reason)` system message, supervisor consults strategy. `OneForOne`: restart only child `id`. `RestForOne`: restart `id` + all children started after `id`. `OneForAll`: restart every child in the group. ~250 LOC of strategy logic + system-message routing. | 4h |
| **As.3** | HIGH | **Restart limits + backoff.** Supervisor tracks `(timestamp, child_id)` of every restart in a sliding window. If count within `max_window_secs` exceeds `max_restarts`, supervisor itself exits with reason `"restart_limit_exceeded"` — parent supervisor handles per its own strategy. Optional exponential backoff between restarts (`backoff_initial_ms`, `backoff_max_ms`); default no backoff. | 2h |
| **As.4** | HIGH | **Structured exit reasons.** `enum ExitReason { Normal, Shutdown, Killed, Crashed { reason: String, payload: Option<JsonValue> } }`. Crash sites in agent runtime populate `Crashed` automatically (panic message → `reason`; user can attach payload via `agent.exit(reason, payload)`). System messages between supervisor and child use this structured shape. | 2h |
| **As.5** | HIGH (gate) | **Tests in `stdlib/agent/tests/test_supervisor.mn`.** 8 cases minimum: (1) OneForOne restarts only the failed child; (2) RestForOne restarts failed child + later siblings; (3) OneForAll restarts all children; (4) Restart limit exhaustion crashes supervisor; (5) Backoff increases between restarts; (6) Nested supervisors propagate ExitReason up; (7) Normal-exit child does not trigger restart; (8) Shutdown signal terminates all children cleanly. | 4h |
| **As.6** | MEDIUM | **Runtime additions.** `runtime/native/mapanare_agent.c` already supports lifecycle messages; add `MN_MSG_CHILD_EXITED` system message type, supervisor inbox handling, `mapanare_agent_exit_with_reason()` API. ~150 LOC. | 3h |
| **As.7** | LOW | **Examples** at `examples/agents/`. `worker_pool_supervised.mn` (worker pool + supervisor restarting failed workers); `pipeline_supervised.mn` (3-stage pipeline with RestForOne — if stage 2 crashes, restart 2 + 3 to keep order). | 2h |
| **As.8** | LOW | **Doc page** at `docs/stdlib/agent.md` (extend existing). Supervision-tree section: strategies, when to use which, restart-limit tuning. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.41.0 HEAD clean.
- **Phase 1** — As.6 runtime extensions; As.4 ExitReason struct
  in `.mn`.
- **Phase 2** — As.1 Supervisor type; As.2 strategies (OneForOne
  first, others build on it).
- **Phase 3** — As.3 restart limits + backoff.
- **Phase 4** — As.5 tests (the gate).
- **Phase 5** — As.7 examples; As.8 docs.
- **Phase 6** — Bump + tag.

---

## Out of scope

- **Dynamic child addition.** Erlang has `supervisor:start_child`;
  v5.42.0 supervisors are static (children declared at startup).
  Dynamic addition is a v5.42.x or v5.43.x patch.
- **Hot code reloading.** Erlang's killer feature for long-lived
  systems; not v5.x.
- **Distributed supervision.** Supervisors managing remote
  agents on other nodes — slot for v5.43.0 (distributed
  agents) instead.
- **Process registry / `via` syntax.** Erlang's named-process
  lookup; deferred.

---

## Risk

1. **Race conditions in restart logic.** A child crashes while
   the supervisor is mid-decision; another child crashes
   concurrently. Mitigation: supervisor's inbox is the
   serialization point — process system messages one at a time;
   bench under TSan to confirm no races.
2. **Restart loops obscure root causes.** A buggy child might
   crash, restart, crash, restart — supervisor exits but stack
   trace is from the supervisor crash, not the original. Mitigation:
   log each child crash with reason at WARN level; supervisor
   exit log includes the crash history.
3. **OneForAll cascade.** A 100-child supervisor with OneForAll
   takes a long time to restart everyone on a single failure.
   Mitigation: documented; users choose strategy intentionally.
4. **Stage1/2 ABI compatibility.** Adding `MN_MSG_CHILD_EXITED`
   to the runtime message enum can shift later enum values'
   numeric IDs, breaking compiled stage1 binaries that were
   built against the old runtime. Mitigation: append new enum
   value at the end (don't insert in the middle); regression
   test that stage1 binary built against v5.41.0 runtime still
   works against v5.42.0 runtime (binary compat).

---

## Success criteria

- ✅ All 8 supervisor tests pass.
- ✅ Worker-pool example: kill 50 random workers in a 100-worker
  pool, all restart cleanly.
- ✅ Restart-limit exhaustion correctly escalates to parent
  supervisor.
- ✅ TSan-clean run of the supervisor test suite.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "agents lack production supervision primitives" gap.

**Inherits to v5.43.0:**
- Dynamic child addition (LOW).
- Distributed supervision (becomes part of v5.43.0 distributed
  agents scope).
- Process registry / named-process lookup (LOW).
