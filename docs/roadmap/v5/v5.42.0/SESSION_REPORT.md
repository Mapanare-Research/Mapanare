# v5.42.0 — Session Report

**Status:** READY (not tagged — tagging is the lead's call).
**Theme:** As.\* — agent supervision trees. Second manifesto-arc
release after v5.40.0 `ask`.

---

## What shipped

- **As.6 runtime substrate** — append-only struct extension on
  `mapanare_agent_t`, four new `MAPANARE_EXPORT` helpers, on_exit
  callback wired at three FAILED-transition sites in
  `mapanare_runtime.c`.
- **As.4 structured exit reason** — `mapanare_exit_reason_kind_t`
  enum (NORMAL / SHUTDOWN / KILLED / CRASHED), 256-byte fixed-size
  reason buffer, opt-in
  `mapanare_agent_set_exit_reason(self, kind, reason)` helper for
  handlers to populate before returning rc != 0.
- **As.1 + As.2 + As.3 — `stdlib/agent/supervisor.mn`** (~370 LOC).
  Strategy library shape (not an agent itself). Erlang/OTP-exact
  semantics for OneForOne / RestForOne / OneForAll, Permanent /
  Temporary / Transient policies, sliding-window restart limit
  enforcement, optional exponential backoff.
- **As.5 — 9 link-and-run tests** under `stdlib/agent/tests/` plus
  pytest harness `tests/stdlib/test_supervisor.py`. **9/9 GREEN at
  HEAD in 3.44s.** Plus
  `tests/runtime/test_agent_struct_compat.py` (4 binary-compat
  cases, 4/4 GREEN).
- **As.6 C smoke harness** at `tests/runtime/test_as6_supervision_smoke.c`. PASSED. TSan
  compile-clean.
- **As.7 — examples** at `examples/agents/`.
  `supervisor_strategy_demo.mn` runs end-to-end through the LLVM
  emitter + clang link + execution; `worker_pool_supervised.mn`
  sketches the orchestration pattern.
- **As.8 — `docs/stdlib/agent.md`** (~250 LOC).

---

## PROMPT/PLAN deviations (load-bearing — see PRE_PHASE_AUDIT.md)

Phase 0 audit surfaced five premise errors in PLAN.md and the
execution PROMPT, all load-bearing for the design:

1. **Naming.** Runtime is `mapanare_agent_t` / `mapanare_agent_*`
   throughout, NOT `MnAgent` / `mn_agent_*` / `MN_MSG_*` /
   `mn_agent_exit_with_reason` as the prompt named. Both stage1
   emitters reference the real names directly. Cosmetic but
   touches every file path / symbol in the prompt's Phase 1.
2. **No system-message-kind enum exists.** Inbox messages are
   opaque `void *` discriminated entirely at the user agent's
   handler. PLAN.md Risk #4 ("appending `MN_MSG_CHILD_EXITED`
   shifts later enum values, breaking stage1 binaries") cannot
   materialize as written — there is no enum. **Re-targeted
   the binary-compat regression test to lock the
   struct-extension case** (the v5.41.0 pattern, applied to a
   different shape).
3. **No `mn_agent_exit*` API.** Agents enter FAILED only when the
   handler returns rc != 0. The structured-payload propagation
   (As.4) was implemented as a side-channel: the handler calls
   `mapanare_agent_set_exit_reason(self, kind, reason)` before
   returning rc != 0; the on_exit callback reads
   `mapanare_agent_get_exit_reason(child, ...)` after the FAILED
   state-store release.
4. **Pre-existing `restart_policy` is intra-agent.** v5.42.0 As.6
   adds supervisor-driven restart on top, leaving the existing
   per-agent retry mechanism untouched. Documented in the
   `docs/stdlib/agent.md` migration/coexistence note.
5. **Goldens at v5.41.0 HEAD are 96/96**, not 98/98 as the prompt
   claimed. v5.42.0 ships 0 new goldens; closeout assertion is
   96/96.

**Path B vs. Path A.** Lead approved Path B (push-driven via opt-in
C callback, append-only struct extension) over Path A (pure-Mapanare
poll-based, zero C edits). Path B has lower restart latency and
preserves the full Path-B feature set including ExitReason payload
routing.

**Compiler edits:** none. Aligns with PROMPT explicit
"`mapanare/self/lower.mn` and `emit_llvm.mn` are off-limits."

---

## Strict 3-stage fixed point

Preserved by construction at v5.41.0's **242,338 lines / 0 diff**
(44-release strict streak from the v5.7.1 baseline). Zero
`mapanare/self/*.mn` source touches in v5.42.0; the runtime + stdlib
work does not flow through the self-host.

## Goldens

**96/96** — v5.41.0 baseline preserved unchanged. No new goldens at
v5.42.0; supervision is tested via the 9 `.mn` link-and-run cases
under `stdlib/agent/tests/` because the closure between strategy
semantics and orchestrator behavior is too dynamic for a golden-IR
comparison.

---

## Test results

```
$ python3 -m pytest tests/stdlib/test_supervisor.py -v
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_one_for_one.mn]    PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_rest_for_one.mn]   PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_one_for_all.mn]    PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_restart_limit.mn]  PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_backoff.mn]        PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_normal_exit.mn]    PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_replace_child_id.mn] PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_window_reset.mn]   PASSED
tests/stdlib/test_supervisor.py::test_supervisor_strategy[test_unknown_child.mn]  PASSED
============================== 9 passed in 3.44s ===============================

$ python3 -m pytest tests/runtime/test_agent_struct_compat.py -v
test_mapanare_agent_t_size_probe                   PASSED
test_emitter_treats_agent_as_opaque_ptr            PASSED
test_new_fields_append_only_in_header              PASSED
test_on_exit_callback_call_sites                   PASSED
============================== 4 passed in 0.73s ===============================

$ /tmp/as6_smoke
PASSED — As.6 callback invoked with structured reason

$ /tmp/test_drain    # pre-existing tests/runtime/test_agent_destroy_drain.c
test_default_dtor_is_free: PASS
test_custom_dtor_called: PASS (dtor_call_count=5)
All agent destroy drain tests passed.
```

---

## Carry-forward

**Closes:**
- "agents lack production supervision primitives" gap — strategy
  library + runtime substrate are real and tested.
- v5.41.0 binary-compat regression-test pattern, re-targeted to the
  struct-extension case at v5.42.0.

**Inherits to v5.43.0:**

- **Spawn-restart-via-Mapanare-fn ergonomic (MEDIUM).** Pass a
  factory closure to the supervisor; supervisor spawns + restarts.
  Blocked on fn-typed parameter invocation reliability through
  Mapanare's lowering (v5.37.0 Ht.\* lesson — registration-table
  workaround). Tracked as the headline v5.43.0 supervision item.
- **`@agent`-handle ↔ `mapanare_agent_t *` bridge (LOW).**
  Convenience for getting the C handle from `spawn AgentX()`.
  Practical use at v5.42.0 is from C-level orchestration; the
  strategy library itself is fully usable without it.
- **Dynamic child addition (LOW).** Erlang's `supervisor:start_child`.
  Static specs only at v5.42.0.
- **Distributed supervision (LOW).** Slot for v5.43.0 distributed
  agents.
- **Process registry / via syntax (LOW).**
- **macOS notarization (MEDIUM).** Carry from v5.33.0 Nu.2.

**Aggregate state entering v5.43.0:** **0 HIGH** / **2 MEDIUM**
(spawn-restart-via-Mapanare-fn ergonomic — v5.43.0 commitment;
macOS notarization carry from v5.33.0 Nu.2) / **~7 LOW**.

---

## Closeout artifacts

- `docs/roadmap/v5/v5.42.0/PLAN.md` — original plan
- `docs/roadmap/v5/v5.42.0/PROMPT.md` — execution prompt
- `docs/roadmap/v5/v5.42.0/PRE_PHASE_AUDIT.md` — Phase 0 audit
  documenting the five PROMPT/PLAN premise errors and the
  Path-A-vs-Path-B decision
- `docs/roadmap/v5/v5.42.0/SESSION_REPORT.md` — this file
- `runtime/native/mapanare_runtime.{c,h}` — As.6 substrate
- `stdlib/agent/supervisor.mn` — strategy library
- `stdlib/agent/tests/test_*.mn` — 9 strategy tests
- `tests/stdlib/test_supervisor.py` — pytest harness
- `tests/runtime/test_agent_struct_compat.py` — binary-compat
  regression
- `examples/agents/supervisor_strategy_demo.mn` — strategy demo
- `examples/agents/worker_pool_supervised.mn` — orchestration sketch
- `docs/stdlib/agent.md` — user-facing reference
