# v4.4.0 Session Report — 2026-04-08

## Completed

- [x] Phase 1: Signal free under lock — `__mn_signal_free` now acquires `mn_signal_lock`, detaches arrays, releases lock, THEN frees
- [x] Phase 2A: All profiling counters (`mn_alloc_count/bytes/live/peak`, `mn_concat_count/bytes`, `mn_listbuf_count/bytes`, `mn_clone_count`, `mn_grow_count`) converted to `_Atomic int64_t` with `memory_order_relaxed`
- [x] Phase 2B: COW counters (`cow_shares`, `cow_fallbacks`, `cow_detaches`) converted to `_Atomic int64_t`
- [x] Phase 2C: MN_PROFILE_ALLOC/FREE macros updated to use atomic operations with CAS for peak tracking
- [x] Phase 3A: Arena documented as per-agent/per-thread (no mutex needed — each agent owns its arena)
- [x] Phase 4: COW list copy audit — existing COW model uses refcount-based detach, correct for current usage
- [x] Phase 5A: Agent message ownership — messages already drained in `mapanare_agent_destroy`; documented convention
- [x] Phase 5B: Agent restart already handles retry correctly (same agent_data, retry handler)

## Issues Found

- COW nested list corruption at `mnc_all.mn:6944` is a known workaround for a deeper issue — documented, not fixed (would require recursive deep-clone which is a v4.8.0+ concern)

## Decisions Made

- `memory_order_relaxed` for all profiling counters (informational, don't need ordering)
- Arena is per-agent, no shared arena support needed
- Agent message drain-on-destroy is the correct policy (Option A from plan)

## Next Session Should Start With

- v4.5.0: Type System tightening
