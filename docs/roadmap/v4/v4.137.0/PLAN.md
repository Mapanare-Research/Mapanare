# Mapanare v4.137.0 — Ch.1 closure (runtime-safety sweep)

> **Close the one HIGH docket on the ledger.** `mapanare_agent_destroy`
> UAF before `pthread_join` was flagged by four of seven v4.136.0
> reviewers (Viper, Anaconda, Mamba, Coral). All three sanitizer test
> classes in `tests/native/test_c_hardening.py` are currently skipped
> behind `_CH1_REASON`. The TSan gate on the C runtime is dark until
> this closes.

**Status:** PLANNED
**Breaking:** No (runtime patch + test un-skip; no API change)
**Prerequisite:** v5.0.0-rc1 tagged (v4.136.0 panel complete)
**Estimated work:** 1 short sprint (~5-line fix + verification)
**Theme:** Close the single HIGH docket. No new fronts.

---

## Why this release, why now

v5.0.0-final cannot ship with Ch.1 open — four reviewers named it,
Viper explicitly held her score at 9.0 (not higher) because of it,
and it silently disables the TSan gate on `mamba_core`. Closing Ch.1
is the cheapest and highest-leverage action on the v4.136.0 carry-
forward ledger.

Expected panel-reviewer impact at v4.143.0:
- **Viper +0.3** (her explicit hold reason closed; TSan gate live)
- **Anaconda +0.1** (v4.133.0 Ch.1 SKIP-docket reopened as pass)
- **Mamba +0.05** (runtime sanitizer-clean depth)

---

## Root cause (from v4.136.0 Viper review + v4.133.0 AN1_REDUCTION)

File: `runtime/native/mapanare_runtime.c`
Function: `mapanare_agent_destroy` (approx. lines 693–715)

The destroy path frees `agent->state` / joins the ring buffer before
calling `pthread_join` on the worker thread. On systems where the
scheduler runs the worker briefly after the main thread has already
proceeded to free state, any load from `agent->state` in the worker
is a UAF on the freed block. Plain harness tolerates this (often the
worker has already exited); ASan catches it intermittently; TSan
catches it ~100%.

All three sanitizer test classes in
`tests/native/test_c_hardening.py`:
- `TestCRuntimePlain::test_agent_metrics` (line 99)
- `TestCRuntimeASan::test_agent_metrics` (line 113)
- `TestCRuntimeTSan::test_agent_metrics` (line 134)

are currently skipped with `@pytest.mark.skip(reason=_CH1_REASON)`.

---

## Phase 1 — Fix

`runtime/native/mapanare_runtime.c::mapanare_agent_destroy`:

1. Set a `state_guard` flag on the agent (or use existing `running`
   field) to signal "shutting down."
2. Call `pthread_join(agent->worker, NULL)` BEFORE freeing
   `agent->state` or tearing down the ring buffer.
3. Only then free.

Estimated: ~5 lines of logic + 1 guard field if needed. Mirror the
pattern already used in `mapanare_scheduler_destroy` if present.

**Do not change the agent API.** The fix is internal to destroy.

## Phase 2 — Un-skip tests

`tests/native/test_c_hardening.py`:
- Remove `@pytest.mark.skip(reason=_CH1_REASON)` on all three
  `test_agent_metrics` methods.
- Remove the `_CH1_REASON` constant if it has no other consumers.

## Phase 3 — Rebuild + verify

```bash
make build-rt                                 # rebuild libmapanare_rt.a
python3 scripts/build_stage1.py               # rebuild mnc-stage1
python3 -m pytest tests/native/test_c_hardening.py -v   # all 3 pass
python3 -m pytest tests/ --ignore=tests/bootstrap -q   # baseline hold
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep     # fixed-point still holds
```

Sanitizer sweeps (confirm no regression):

```bash
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
bash scripts/run_asan_goldens.sh
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `mapanare_agent_destroy` calls `pthread_join` before any free | yes |
| 2 | `TestCRuntimePlain::test_agent_metrics` passes | yes |
| 3 | `TestCRuntimeASan::test_agent_metrics` passes | yes |
| 4 | `TestCRuntimeTSan::test_agent_metrics` passes | yes |
| 5 | `_CH1_REASON` skip marker removed from all three tests | yes |
| 6 | Non-bootstrap pytest: 5,116 passed / 0 failed (baseline hold or +3 from Ch.1 un-skip) | yes |
| 7 | Bootstrap pytest: 212/13 byte-identical | yes |
| 8 | Goldens 53/65 through mnc-stage1 | yes |
| 9 | Strict fixed-point md5 holds | yes |
| 10 | Valgrind ERRORS ≤ 5 (Ge.1 residual) | yes |
| 11 | ASan ASAN_ERROR = 0 | yes |
| 12 | DOCKET_LEDGER.md: Ch.1 CLOSED | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Fix introduces a deadlock (join blocks forever) | low | high | Add timeout-based join or ensure worker exits on `running = false` before join is called |
| TSan test reveals additional races on same path | medium | medium | Scope-expand only if new races are in same destroy window; else docket as Ch.2 and keep v4.137.0 narrow |
| `libmapanare_rt.a` ABI change forces recompile of user binaries | very low | low | Destroy path is internal; no public struct layout change |
| Fix requires a new field on agent struct | medium | low | Acceptable — add it; document in SESSION_REPORT |

## What this release does NOT do

- Does not touch the Python emitter, self-hosted compiler, or SPEC.
- Does not close other v4.136.0 carry-forward items (Bo.*, Cb.*,
  Sh.2-residual, Ge.1, etc.) — those are later releases.
- Does not bump to v5.0.0-rc2 (incremental rc tags are avoided per
  project convention; v5.0.0-final gates on the v4.143.0 panel).

## Carry-forward after v4.137.0

Unchanged from v4.136.0 except Ch.1 CLOSED. Next target: v4.138.0
docs sweep (Boa's 8.4 → 8.9 delta).
