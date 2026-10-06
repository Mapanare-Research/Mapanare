# v5.42.0 — Phase 0 PRE-PHASE AUDIT

**Status:** AUDIT — surfaces PLAN/PROMPT premise errors that need
lead alignment before Phase 1.

---

## Pre-flight (passed)

- `VERSION` = `5.41.0` ✓
- `git status --short` = `M AGENTS.md`, `M CLAUDE.md` (matches the
  release-prep working-tree pattern) ✓
- v5.41.0 SESSION_REPORT confirmed STRICT 3-stage fixed point at
  242,338 lines / 0 diff and goldens 96/96 (CLAUDE.md release-notes
  entry) ✓

> Note: the execution PROMPT cites `Goldens 98/98 (no new goldens)`
> as the entering baseline. Actual count at v5.41.0 HEAD is **96/96**
> (95 from v5.40.0 + new `96_tensor_reshape.mn` at v5.41.0). This is
> a cosmetic prompt error; v5.42.0 ships **0 new goldens**, so the
> closeout assertion is `96/96`.

---

## Existing agent runtime (confirmed)

`runtime/native/mapanare_runtime.{c,h}` ships a substantive agent
runtime — Phase 4.3-vintage, stable across the entire v4.x and v5.x
arc. Public surface (verbatim, NOT what the PROMPT calls it):

**Type:** `mapanare_agent_t` (NOT `MnAgent`)

**Functions** (all `MAPANARE_EXPORT`, NOT `mn_agent_*`):
- `mapanare_agent_init / new / spawn / send / recv / recv_blocking`
- `mapanare_agent_pause / resume / stop / destroy`
- `mapanare_agent_get_state / messages_processed / avg_latency_us`
- `mapanare_agent_set_restart_policy(agent, policy, max_restarts)`

**State enum** (5 values, exhaustive):
`MAPANARE_AGENT_IDLE | RUNNING | PAUSED | STOPPED | FAILED`

**Restart policy enum** (already exists, but local-only — NOT
supervision):
`MAPANARE_RESTART_STOP | MAPANARE_RESTART_RESTART`

**Existing fields on `mapanare_agent_t`:** id, name, state, paused,
inbox / outbox ring buffers, inbox producer-lock,
backpressure, semaphores, handler fn pointer, agent_data, lifecycle
callbacks (on_init / on_stop / on_pause / on_resume),
**`restart_policy` + `max_restarts` + `restart_count`** (already
present), thread, message_dtor.

**FAILED transition sites** (the supervision hook points):
- `mapanare_runtime.c:606,612` — coop scheduler path: handler
  `rc != 0` → `state = FAILED` (after exhausting `max_restarts`).
- `mapanare_runtime.c:1411` — pthread worker path: same shape.

Both stage1 emitters reference these symbols directly:
- `mapanare/emit_llvm_text.py:5477+` — `mapanare_agent_new`,
  `mapanare_agent_spawn`, `mapanare_agent_send` declared as opaque
  `ptr` returns; struct is never inlined.
- `mapanare/self/emit_llvm.mn:833,914,1044-1048` — same opaque
  `ptr` treatment.

**Binary-compat surface:** the agent struct is **only ever
allocated via the heap-allocating `mapanare_agent_new`** at both
emitter call sites. Neither emitter knows or hard-codes
`sizeof(mapanare_agent_t)`. Appending fields to the struct is
binary-compat-safe by construction.

---

## Premise errors in PLAN.md / PROMPT.md (load-bearing)

### Error 1 — naming throughout

PROMPT references `MnAgent`, `mn_agent_create`, `mn_agent_send`,
`mn_agent_destroy`, `mn_agent_exit`, `mn_agent_arena_create`,
`MN_MSG_CHILD_EXITED`. **None of these symbols exist.** The actual
runtime uses `mapanare_agent_t` and `mapanare_agent_*` exports.
There is also no `mn_agent_arena_create` — agent message lifetime
is opaque to the runtime (each user agent owns its message
allocator).

This is purely cosmetic — the runtime *does* exist; the prompt just
named it wrong. But every file path / symbol name in Phase 1 of
the prompt is incorrect.

### Error 2 — no system-message-kind enum exists

Both PLAN.md (Risk #4) and PROMPT specify "**append
`MN_MSG_CHILD_EXITED` to the existing message-kind enum**" with
prominent binary-compat warnings.

**There is no message-kind enum.** Messages flowing through agent
inboxes are opaque `void *`. Discrimination happens entirely at the
user agent's handler — the runtime never inspects message contents.
The risk PLAN.md #4 names ("appending shifts later enum values,
breaking stage1 binaries built against the old runtime") cannot
materialize because there is no enum to shift.

This collapses an entire piece of the As.6 design surface. The
binary-compat regression test (v5.41.0 pattern) is still worth
keeping — it locks the `mapanare_agent_t` struct-extension case
(see below) — but its target shifts.

### Error 3 — `mn_agent_exit` / `mn_agent_exit_with_reason` don't exist

PROMPT specifies:
- "existing `mn_agent_exit(reason: plain string)` keeps working"
- "add `__mn_agent_exit_with_reason(self, MnExitReason)` export"

Neither symbol exists. There is no caller-visible "exit with
reason" API. An agent's worker thread enters FAILED state purely
when its handler returns `rc != 0`; the FAILED transition is set
internally by the runtime, not by user code.

### Error 4 — As.4 ExitReason carries no error message today

PROMPT and PLAN both posit a structured payload (`reason: String`,
`payload: JsonValue?`) propagating from the crash site to the
supervisor. The current crash site has only `rc != 0` — no string,
no payload. The handler returns an opaque integer error code that
is *not preserved anywhere* (only `trace_emit(MAPANARE_TRACE_ERROR,
...)` runs, which is a side-effect, not a stored value).

To populate `ExitReason::Crashed { reason: String, payload }`, the
handler signature would need to gain a way to communicate the
reason out — either by writing to a per-agent `last_exit_reason`
field (mutating runtime state from inside the handler, which the
agent_data hook could provide), or by changing the handler-fn
signature (breaks binary compat).

The simplest path: extend `mapanare_agent_t` with a
`last_exit_reason` (MnString-shaped) and `last_exit_kind`
(int) field, and add an opt-in helper
`mapanare_agent_set_exit_reason(agent, kind, reason_str)` that the
handler can call before returning `rc != 0`. Default: empty string,
kind = `CRASHED`.

### Error 5 — As.7 example claim "agents are first-class"

`agent ChatBot { input ... output ... fn handle(...) }` parses, but
`examples/ai/chat_agent.mn` (the only `@agent` example in the tree)
is documented at the top: **"this example does not currently
compile"** (Gr.1 multi-line list-literal grammar limitation). It
has been broken since v4.129.0.

The agent surface compiles end-to-end for the simple case (per
`tests/llvm/test_agent_codegen.py`) — but there is no working
multi-agent example in the corpus to model the v5.42.0 supervisor
examples on. The new examples will be the first end-to-end
demonstrations of the agent surface in `examples/`.

---

## As.* items vs. existing state

| ID | PLAN claim | Reality | Adjusted scope |
|---|---|---|---|
| As.1 | Net-new Supervisor stdlib | Confirmed net-new. No `stdlib/agent/`. | NEW — ~250 LOC `.mn` |
| As.2 | Net-new strategy logic | Confirmed net-new. | NEW — ~250 LOC `.mn` |
| As.3 | Net-new restart limits + backoff | Confirmed net-new at supervisor level. (Per-agent `restart_policy` + `restart_count` already exist for *handler-error* retry, but that's not what supervision means.) | NEW — ~80 LOC |
| As.4 | Structured exit reason | **PARTIAL.** FAILED state exists; no reason payload. Need `last_exit_reason` + `last_exit_kind` on the struct + opt-in helper for handlers to populate. | EXTEND — ~30 LOC C |
| As.5 | 8 tests | Net-new. No supervision tests in tree. | NEW — ~400 LOC `.mn` |
| As.6 | Append `MN_MSG_CHILD_EXITED` to enum + supervisor inbox handler | **No enum to append to.** Real work: append fields to `mapanare_agent_t` (parent pointer, on_exit callback, last_exit_*); call the callback at the two FAILED transition sites; supervisor.mn registers a callback that builds a `.mn`-level `ChildExited` message and `mapanare_agent_send`s it to itself. | EXTEND — ~80 LOC C, ~50 LOC `.mn` |
| As.7 | 2 examples | Confirmed net-new. No working multi-agent example in tree. | NEW — ~150 LOC `.mn` |
| As.8 | Extend `docs/stdlib/agent.md` | **No `docs/stdlib/agent.md` exists.** Tree has `docs/stdlib/{ai,crypto,http,json,regex,sql,time}.md` only. | NEW — ~250 LOC docs |

**Compiler edits:** none anticipated. Aligns with PROMPT.
**Runtime edits:** struct extension + 2 fn-pointer fields + ~80 LOC
of dispatch logic at two existing sites. Append-only.
**Stdlib LOC:** ~600 `.mn` + ~80 C + ~250 docs. Aligned with
PLAN's estimate (~600 + ~200), with the C side smaller than PLAN
projected because we wrap an existing runtime instead of building
a parallel one.

---

## Recommended design (lead approval point)

**Path A — pure-`.mn` poll-based supervisor.** Supervisor agent's
handler runs a tick loop; each tick, it polls every child via
`mapanare_agent_get_state()`. On FAILED, run the strategy (stop +
destroy + new + spawn the appropriate set). Pros: zero C runtime
edits; ABI-safe trivially. Cons: poll latency; not push-driven;
restart-decision logic and per-agent state tracking interleaved
with the tick loop; no `ExitReason` payload.

**Path B (recommended) — push-driven via opt-in C callback.**
Append three fields to `mapanare_agent_t`:

```c
mapanare_agent_t  *parent;          /* nullable; ptr to supervisor */
void (*on_exit)(mapanare_agent_t *self, void *cb_data);
void              *on_exit_cb_data; /* opaque, supervisor-side */

/* Optional structured exit reason — populated by handler via
 * mapanare_agent_set_exit_reason() before returning rc != 0 */
int32_t            last_exit_kind;  /* MnExitReasonKind */
char               last_exit_reason[256];  /* '\0'-terminated */
```

Append-only — old `mapanare_agent_new()` callers (the stage1
emitters) keep working because `calloc()` zero-inits the new
fields. NULL `on_exit` means "no parent; don't notify."

At the two FAILED sites (`mapanare_runtime.c:606,612` for the coop
path; `:1411` for the pthread path), insert (after the state
store):

```c
if (agent->on_exit != NULL) {
    agent->on_exit(agent, agent->on_exit_cb_data);
}
```

Add four small public exports:
- `mapanare_agent_set_parent(child, parent)` — sets the field.
- `mapanare_agent_set_on_exit(child, fn, cb_data)` — registers the
  callback.
- `mapanare_agent_set_exit_reason(self, kind, reason)` — handler-
  side helper; stores into `last_exit_*`.
- `mapanare_agent_get_exit_reason(child, *kind, *reason)` — reads
  back, post-FAILED.

The supervisor.mn registers an `on_exit` callback that builds a
Mapanare-side `ChildExited{id, kind, reason}` message (its own
agent's input-message variant) and `mapanare_agent_send`s it to
the parent's inbox. The parent's own handler dispatches on the
message variant.

**Tradeoff:** Path B requires careful FAILED-transition ordering
— the callback must run **before** the agent thread exits so the
supervisor's send can arrive; if we run it after, there's a race
where the child is already destroyed when the parent processes
its inbox. The proposed sites are correct (the FAILED store is
followed only by `running = 0` and breaking the work loop; the
callback runs before any cleanup).

**TSan exposure:** the callback is invoked from the dying child's
worker thread, calling into `mapanare_agent_send` on the parent.
The send path already serializes on the parent's
`inbox_producer_lock` (v4.28.0 fix). No new race.

**Path A as fallback** if Path B's C-side surgery is rejected by
the lead — drop As.4 ExitReason structured payload (or implement
it purely on the `.mn` side via a per-supervisor handle table), and
ship a poll-based supervisor at ~250 ms tick latency.

---

## Open questions for lead

1. **Path A or Path B?** Recommendation: B. Smallest delta to
   close the manifesto-claim ("agents are production-grade");
   ABI-safe by construction; no scheduling latency.
2. **Drop or keep PLAN Risk #4 (binary-compat enum guard)?**
   Recommendation: re-target it — keep the regression test, point
   it at the struct-extension case (build a stage1 binary against
   v5.41.0 runtime; run it against v5.42.0 runtime; expect zero
   crashes / zero behavior change for non-supervised agents).
3. **`MnExitReason` shape** — current `mapanare_agent_t` is
   limited to a fixed-size `char[256]` for the reason string
   (avoids per-FAILED malloc). If unbounded reason strings are
   load-bearing, we go heap-allocated and pay the malloc / free
   discipline. Recommendation: 256-byte truncation is fine;
   anyone shipping a multi-KB exit-reason string is doing the
   wrong thing.
4. **As.7 examples needing working multi-agent code** — the
   existing `chat_agent.mn` is broken (v4.129.0 Gr.1). The new
   examples will need to either (a) sidestep multi-line list
   literals, or (b) we close Gr.1 as a v5.42.x or v5.43.0 LOW
   prereq. Recommendation: (a) — write the examples
   single-line-literal-friendly; Gr.1 is a parser issue separate
   from the supervisor work.

---

## Recommendation

Stop Phase 1 work; surface this audit to the user; get an
explicit Path A vs. B decision and the four open-question
adjudications above. The PROMPT's prescribed Phase 1 ("append
`MN_MSG_CHILD_EXITED` to enum + add `MnExitReason` struct + add
`__mn_agent_exit_with_reason` export") cannot be executed as
written because three of the four named primitives don't exist
in the runtime at HEAD.

This is the v5.41.0 / v5.40.0 PROMPT-deviation pattern: surface
audit findings, lock decisions, document deviations in the
SESSION_REPORT.

