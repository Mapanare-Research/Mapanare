# v4.150.0 E6 Hypothesis — Async Agent Pipeline vs Go

## Expected ROI ranking: A > C > B

### Lever A — empty-wake sem_post (expected: 10-25% async geomean improvement)

The unconditional `sem_post` in `mapanare_agent_send` is the single
highest-frequency unnecessary atomic operation in the agent hot path.
For a 100-step sequential chain, every send posts even though the worker
is actively dispatching (not parked in `sem_wait`). The POSIX semaphore
`sem_post` is an atomic increment + potential futex_wake syscall. Even
when uncontended (no futex), the atomic RMW on the semaphore's internal
counter causes a cache-line bounce between the sender's core and the
worker's core.

**Patch sketch (~8 lines):**
```c
int mapanare_agent_send(mapanare_agent_t *agent, void *msg) {
    mapanare_mutex_lock(&agent->inbox_producer_lock);
    int was_empty = mapanare_ring_is_empty(&agent->inbox);
    int rc = mapanare_ring_push(&agent->inbox, msg);
    mapanare_mutex_unlock(&agent->inbox_producer_lock);
    if (rc == 0) {
        mapanare_bp_increment(&agent->bp);
        if (was_empty) {
            mapanare_sem_post(&agent->inbox_ready);
        }
        trace_emit(MAPANARE_TRACE_SEND, agent, msg, 0);
    }
    return rc;
}
```

**Correctness argument:** The ring is SPSC on the consumer side. If
`was_empty` is false, the worker either (a) is dispatching a prior
message and will loop back to `ring_pop` before `sem_wait`, finding our
new item, or (b) is between `ring_pop` (success) and `dispatch`, same
outcome. The only case where the worker could be in `sem_wait` is when
the ring was empty — which is exactly when `was_empty` triggers the
wake. Spurious wakes (worker drains ring before our post) are harmless:
worker retries `ring_pop`, finds empty, re-enters `sem_wait`.

### Lever B — inline small-message payload (expected: 5-15% improvement)

Each agent message round-trip involves `malloc` + `free` for an 8-byte
integer payload. For 100 sequential awaits, that's 200 heap operations.
Go channels avoid this entirely by copying values inline into the ring
buffer. However, strace shows 0 futex/brk calls for the heap path,
meaning glibc's tcmalloc/ptmalloc fast path handles these allocations
from thread-local arenas. The improvement may be smaller than expected
because the heap operations never touch the kernel.

**Risk:** Changing the ring slot type from `void*` to a tagged union
touches `mapanare_ring_push`, `mapanare_ring_pop`, and the destroy
drain loop. This is the widest blast radius of the three levers —
every agent user is affected. Deferred to Phase 6 only if A alone
doesn't close the gap.

### Lever C — spin-before-park (expected: 3-8% improvement)

Adding a brief spin loop (64 PAUSE iterations) before `sem_wait` in the
worker thread catches the case where a message arrives within ~200ns of
the worker finding an empty ring. This is most relevant for `io_bound`
and `mixed_cpu` workloads where message arrival timing is less
predictable. For the sequential chain, Lever A should already prevent
most unnecessary parks.

**Risk:** Low. The spin is bounded (64 iterations), architecture-
portable (`__builtin_ia32_pause()` on x86, `__yield()` on ARM), and
only runs when the ring is empty. TSan implications: the spin reads
the ring's head/tail atomics, which are already `atomic_load` — no new
data race surface.

## Measurement plan

Each lever is measured independently:
1. Baseline → A → measure → record E6a
2. A → A+C → measure → record E6c (C before B due to lower risk)
3. A+C → A+C+B → measure → record E6b (only if gap still > 1.2×)

Reordering B/C from the PLAN: C has lower blast radius and is
independent of A's change surface. B touches the ring data structure
and should be last.
