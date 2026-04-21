# Mamba — C Runtime Lens

**Grade: 8/10** | **Verdict: PASS WITH NOTES**

## Assessment

The runtime scheduler extension (DESIGN.md §5) is well-specified. The
`mapanare_coro_scheduler_t` API is clean and the step algorithm is correct.
The integration with the existing agent scheduler (§5.5) correctly identifies
the "handler-in-flight" race condition.

Arc 8 didn't touch the runtime — that's Arc 9's job. Grading the design only.

## Specific findings

1. **PASS**: DESIGN.md §5.3 specifies a clean API: `init`, `register`,
   `set_awaited`, `step`, `run`, `stop`, `destroy`. Each function has a
   clear purpose.
2. **NOTE**: The O(n) step function (scan all entries, check readiness) will
   become a bottleneck at ~1000 concurrent coroutines. DESIGN.md acknowledges
   this and defers to v5.x. Acceptable.
3. **NOTE**: The `pending_coro_handle` field on `mapanare_agent_t` (§6.5)
   hasn't been added yet. This MUST happen in v4.73.0 when the scheduler
   ships. Add to the v4.73.0 PLAN.md exit criteria.
4. **PASS**: The Future `{i8, ptr}` layout is runtime-compatible — the
   scheduler's readiness check is a single byte load (`*(i8*)future`).
5. **NOTE**: Two heap allocations per async fn call (frame + Future) with
   an additional allocation per return value (the box). Three mallocs and
   eventually three frees per coroutine lifecycle. This is acceptable for
   correctness but should be optimized in v5.x (promise-based storage
   eliminates the box allocation).
