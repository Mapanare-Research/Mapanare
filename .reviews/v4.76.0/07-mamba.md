# Mamba — C Runtime Lens

**Grade: 9/10** | **Verdict: PASS**

## Assessment

The inline-resume model means no C runtime scheduler was needed for v4.x.
The DESIGN.md §5 scheduler API remains a v5.x deliverable for I/O-bound
async. For CPU-bound coroutines, the inline model is correct and simpler.

The `block_on` cleanup sequence (`coro.destroy` → `free(box)` → `free(future)`)
is correct. No runtime C changes were required — all scheduling logic lives
in the LLVM IR emitter.

## Specific findings

1. **PASS**: `block_on` correctly frees all allocations (my v4.71.0 concern).
2. **PASS**: No C runtime changes needed — clean separation.
3. **NOTE**: The `pending_coro_handle` field on `mapanare_agent_t` (v4.71.0
   item #6) was correctly deferred — the inline model doesn't need it.
   If v5.x adds the real scheduler, the field becomes necessary.
4. **PASS**: Three `malloc` calls per coroutine (frame + future + box) and
   three matching `free` calls. No leaks in the happy path.
5. **PASS**: The cooperative scheduler in `mapanare_runtime.c` is untouched
   and still works for agents. The coroutine and agent schedulers don't
   interfere — they're independent subsystems.
