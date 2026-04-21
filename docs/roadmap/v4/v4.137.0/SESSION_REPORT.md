# v4.137.0 — Ch.1 closure (session report)

**Shipped:** 2026-04-15
**Theme:** Close the one HIGH docket. No new fronts.
**Scope:** runtime patch + test hygiene + test un-skip.
**Breaking:** No.
**Prerequisite:** v5.0.0-rc1 (tagged at v4.136.0).

---

## TL;DR

Ch.1 — `mapanare_agent_destroy` UAF before `pthread_join` — is
**CLOSED**. Four v4.136.0 reviewers named it; Viper held her memory-
safety score at 9.0 (not higher) because of it; the TSan gate on the
C runtime agent path had been dark behind three `_CH1_REASON`-skipped
test classes since v4.133.0. All three now pass: Plain, ASan, TSan.

The ledger's last HIGH-severity open docket closes with this release.
**0 CRITICAL / 0 HIGH remain.** Composition: 10 MEDIUM / 13 LOW.

---

## Root cause

`runtime/native/mapanare_runtime.c::mapanare_agent_destroy` drained
the inbox/outbox rings and freed the producer lock + semaphores
*before* waiting for the worker thread to exit. `mapanare_agent_stop`
joined the worker, but `destroy` did not require stop to have been
called — and even when callers did both, the destroy path itself did
no join.

Failure modes by sanitizer (v4.133.0 characterization):
- **Plain:** invalid-free abort when the outbox drain called
  `message_dtor(msg)` with fake-pointer tokens.
- **ASan:** intermittent UAF report (worker load from freed ring
  metadata).
- **TSan:** ~100% data race between worker's `ring_pop` / `sem_wait`
  and destroy's `ring_destroy` / `sem_destroy`.

---

## Fix

### Runtime (`runtime/native/mapanare_runtime.c` + `.h`)

1. New field on `mapanare_agent_t`: `mapanare_atomic_i32 needs_join`.
   Set by `mapanare_agent_spawn` on successful `thread_create`.
2. New helper: `atomic_exchange_i32(p, v)` wrapping
   `__atomic_exchange_n` with `ACQ_REL` ordering.
3. `mapanare_agent_spawn`: on `thread_create` success, set
   `needs_join = 1`. On failure, clear `running`.
4. `mapanare_agent_stop`: only performs the join if
   `atomic_exchange_i32(&needs_join, 0) == 1`. Makes stop idempotent.
5. **`mapanare_agent_destroy`: signals `running = 0` + sem posts,
   claims `needs_join` via atomic exchange, joins if owed, *then*
   drains rings and tears down.** This is the Ch.1 fix.

Net runtime churn: +15 logic lines + 1 new struct field across `.c`
and `.h`. Single-caller, single-owner semantics; no public API
change.

### Test hygiene (`tests/native/test_c_runtime.c`)

`test_agent_metrics` passes pointer-as-token values (`(void*)1..5`)
rather than heap allocations. The default `message_dtor = free`
(added v4.78.0 CARRY_FORWARD #50) would call `free()` on those tokens
during the outbox drain. Added `agent.message_dtor = NULL;` after
init to match the test's actual intent (tokens, not heap memory).
This is a latent test-side issue that the Ch.1 skip had been masking.

### Test un-skip (`tests/native/test_c_hardening.py`)

Removed `@pytest.mark.skip(reason=_CH1_REASON)` from the three test
classes: `TestCRuntimePlain`, `TestCRuntimeASan`, `TestCRuntimeTSan`.
The `_CH1_REASON` constant itself is left in place (no external
consumers — docs reference it by name only, so the string is free to
remain as inline history).

---

## Verification

### Sanitizer tests (the direct Ch.1 tests)

```
tests/native/test_c_hardening.py::TestCRuntimePlain::test_all_c_tests_pass  PASSED
tests/native/test_c_hardening.py::TestCRuntimeASan::test_asan_no_errors     PASSED
tests/native/test_c_hardening.py::TestCRuntimeTSan::test_tsan_no_races      PASSED
3 passed in 15.92s
```

All three previously skipped behind `_CH1_REASON`. All three green.

### Pytest baseline

| Suite | v4.135.0 | v4.137.0 baseline pre-fix | v4.137.0 post-fix |
|---|---|---|---|
| Non-bootstrap | 5,110 / 0 | 5,136 / 0 | **5,139 / 0** (+3 Ch.1 un-skip) |
| Bootstrap | 212 / 13 | 212 / 13 | **212 / 13** (byte-identical) |

*Note:* Non-bootstrap baseline grew organically (5,110 → 5,136) between
v4.135.0 and v4.137.0. The +3 delta at v4.137.0 is exactly the
Ch.1 un-skip.

### Self-hosted invariants

- Goldens through `mnc-stage1`: **53 / 65** (byte-identical to
  v4.135.0/v4.136.0 baseline).
- Strict 3-stage fixed point: **md5
  `0c00ad07fee94f98bb350b359395843b`** on both `/tmp/stage2.ll` and
  `/tmp/stage3.ll` (byte-identical, 108,397 lines). La Culebra sigue
  muerdiéndose la cola.

### Sanitizer sweeps on goldens

| Metric | v4.135.0 | v4.137.0 |
|---|---|---|
| Valgrind ERRORS | 5 | **5** (byte-identical; Ge.1 residuals) |
| Valgrind CLEAN / WARN | 0 / 60 | 0 / 60 |
| ASan ASAN_ERROR | 0 | **0** |
| ASan CLEAN / CRASH_NO_ASAN | 54 / 11 | 54 / 11 |

No regression.

---

## Binary deltas

| Artifact | Pre | Post | Reason |
|---|---|---|---|
| `runtime/native/libmapanare_rt.a` | `d896c83c…` | `1222c056…` | Runtime .c / .h changed (expected) |
| `mapanare/self/mnc-stage1` | — | `3f4e54e3…` (3,480,720 B stripped) | Relinked against new `libmapanare_rt.a` |

Source-tree changes: 5 files (see git diff).

---

## GitNexus impact check

Before editing `mapanare_agent_destroy`:

- `gitnexus_impact({target: "mapanare_agent_destroy", direction:
  "upstream"})` → **risk: LOW**, 0 direct callers in graph, 0
  processes affected, 0 modules affected.
- `gitnexus_context` → outgoing calls to `mapanare_ring_destroy`,
  `mapanare_ring_pop` (expected).

Self-contained runtime internals as the plan predicted.

---

## What this release does NOT do

- Does not touch the Python emitter, self-hosted compiler, or SPEC.
- Does not close other v4.136.0 carry-forward items (Bo.\*, Cb.\*,
  Sh.2-residual, Ge.1). Those are later releases.
- Does not bump to v5.0.0-rc2. v5.0.0-final gates on the v4.143.0
  panel per project convention.

---

## Expected v4.143.0 panel-reviewer impact

From the v4.137.0 PLAN:
- **Viper +0.3** (her explicit 9.0-hold reason closed; TSan gate live)
- **Anaconda +0.1** (v4.133.0 Ch.1 SKIP-docket reopened as pass)
- **Mamba +0.05** (runtime sanitizer-clean depth)

---

## Carry-forward after v4.137.0

Unchanged from v4.136.0 **except Ch.1 CLOSED**. The ledger now has
**zero HIGH-severity open dockets.** Next planned target: v4.138.0
docs sweep (Boa's 8.4 → 8.9 delta; README version-badge drift on
Bo.4 + `mapanare --version` output on Bo.5). No runtime-safety work
remains on the v5.0.0 critical path.
