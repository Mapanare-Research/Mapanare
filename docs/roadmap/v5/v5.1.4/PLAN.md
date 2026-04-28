# Mapanare v5.1.4 — "Perf.2: Lazy Thread Creation"

> **Kill the `MAPANARE_ASYNC_THREADS=2` env-var workaround.** v4.150.0
> (E6) made the headline claim "0.85× Go (faster than Go)" — but it
> only holds if the user sets the env var to 2. The default (auto-
> detect cores) on a 32-core machine is ~1.7× Go. Lazy thread
> creation makes the default production-correct.

**Status:** PLANNED (skeleton)
**Breaking:** No
**Prerequisite:** v5.1.3 shipped
**Estimated work:** 2 sessions (~3 hours total)

---

## Why this release exists

Mamba v4.154.0 lines 174-180:

> E6 ASYNC_THREADS — not a portable claim. The "0.85× Go (faster
> than Go)" headline requires `MAPANARE_ASYNC_THREADS=2`. The default
> (auto-detect cores) on a 32-core machine still gives ~2.3 ms, which
> is ~1.7× Go. The headline should say "0.85× Go with ASYNC_THREADS=2"
> or "1.7× Go at default." Both are true. Using the tuned number as
> the headline without the qualifier is misleading.

Mamba's carry-forward docket text:

> **Perf.2** (NEW LOW) — Lazy thread creation in coro scheduler —
> eliminates ASYNC_THREADS env var workaround

v4.150.0's root cause analysis (from SESSION_REPORT):

> `__mn_coro_scheduler_init` creates one OS thread per CPU core; on
> 32-core machine, 31 `pthread_create` calls take ~2.2 ms, dominating
> the ~2.3 ms benchmark total.

The fix today — setting `MAPANARE_ASYNC_THREADS=2` — is a production-
incompatible hack. A real user's workload doesn't know how many
threads to pre-allocate. The scheduler should create threads on
demand, growing to a cap only as throughput requires.

## Scope

### The fix

In `runtime/native/mapanare_runtime.c::__mn_coro_scheduler_init`:
- Replace the eager thread-pool creation loop with a single-thread
  init
- Add a work-queue length threshold (e.g., 16 pending tasks) that
  triggers a new worker creation
- Add a per-thread idle timeout (e.g., 100ms) that lets workers exit
  when the queue is drained
- Cap at `mapanare_cpu_count()` (or `MAPANARE_ASYNC_THREADS` if set)

Pattern matches Go's runtime scheduler at a high level — threads are
created lazily and parked/exit when idle.

### Measurement

Re-run the async benchmark suite under three scenarios:

| Scenario | ASYNC_THREADS | Before | After (target) |
|---|---|---|---|
| Default, 32-core machine | unset | 2.3 ms (1.7× Go) | ≤ 1.2 ms (0.9× Go) |
| Tuned, 32-core machine | 2 | 1.14 ms (0.85× Go) | ≤ 1.14 ms (no regression) |
| Default, 2-core machine | unset | 2.3 ms | ≤ 1.5 ms |

## Exit criteria

1. Async benchmark geomean at *default settings* (no env var) is
   ≤ 1.0× Go on a 32-core machine — the headline claim holds without
   the knob
2. The `MAPANARE_ASYNC_THREADS` env var is preserved as an override
   (for power users + benchmarks) but documented as optional, not
   required
3. `tests/native/test_coro_scheduler.c` exercises both the lazy
   startup path and the idle-exit path
4. TSan reports 0 races on the lazy-creation + idle-exit transitions
5. Valgrind shows 0 leaks on scheduler teardown
6. `docs/roadmap/v5/PARITY_GAPS.md`: Perf.2 moves to Historical

## Risks

**Risk 1 — lazy creation races with shutdown.**
If a worker exits from idle timeout *exactly* as `scheduler_destroy`
is tearing down, TSan reports data race on the worker list.
*Mitigation:* guard the worker-list mutation with the scheduler lock
on both sides. Specifically: worker-self-removal on idle exit and
scheduler-forcing-exit on destroy both hold the same mutex.

**Risk 2 — work-queue threshold is machine-dependent.**
"16 pending tasks" triggers new worker on a fast machine but may be
too aggressive on a slow one.
*Mitigation:* measure across small/medium/large machines
(2-core VM + 32-core bare metal + anywhere in between). Tune the
threshold to hit the benchmark targets on all three. If tuning can't
satisfy all three, accept 2-3 workers as the minimum (pre-creates
the first 2-3, adds lazily beyond).

**Risk 3 — regresses the tuned-flag case.**
The v4.150.0 claim was 0.85× Go with `ASYNC_THREADS=2`. Lazy creation
with a work-queue threshold may not reach the same number because
the first task pays a `pthread_create` latency.
*Mitigation:* pre-create the first 2 threads eagerly (covers the
common-case benchmarks); lazy-create 3rd..N on demand. This keeps
the 0.85× claim *and* makes the default production-correct.

## Rollback

Revert to eager thread creation. Document in the README that the
async benchmark's headline requires `ASYNC_THREADS=2` (honest story
Mamba asked for). Open Perf.2 again for a future attempt; the
benchmark numbers don't change.
