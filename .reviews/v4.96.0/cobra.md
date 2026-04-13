# Cobra — C++/ABI Review (Arc 13)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### Scheduler ABI compatibility (v4.92.0 → v4.93.0)

The `__mn_coro_scheduler_*` symbol names are preserved across both releases. The function signatures changed subtly:

- `__mn_coro_scheduler_init(uint32_t)`: v4.92.0 interpreted the argument as "initial capacity" (number of slots); v4.93.0 interprets it as "number of threads" (0 = auto-detect). **The emitted IR changed from `i32 64` to `i32 0`.** Old IR compiled against the new runtime would pass 64 as thread count — this would work (64 threads, capped at MN_MAX_WORKERS=64) but is wasteful. Not a real concern since the emitter and runtime are versioned together.

- `__mn_coro_scheduler_step`: removed from v4.93.0 (the multi-threaded scheduler doesn't expose a step function). Not called by emitted IR — only used internally in v4.92.0. **No ABI break.**

- `__mn_coro_spawn`: new in v4.93.0. Additive — no backward compat issue.

### Coroutine frame ABI

The LLVM switched-resume coroutine frame layout (`{ptr resume, ptr destroy, i8 index, ...spills}`) is determined by CoroSplit, not by Mapanare. The C scheduler reads this layout at fixed offsets (`offset 0` for resume fn, `2*sizeof(ptr)` for suspend index). This is ABI-coupled to LLVM's coroutine implementation. Acceptable for a single-compiler project, but would break if LLVM changed the frame layout in a future release.

### StringBuilder ABI

`MnStringBuilder` is `{char*, int64_t, int64_t}` — a stable C struct. Passed by pointer to all functions except `__mn_sb_create` (which returns by value). The by-value return is fine for a 24-byte struct on x86_64 (returned in registers). **Stable ABI.**

### MnString heap tagging

The `mn_tag_heap`/`mn_untag` functions use the low bit of the data pointer to distinguish heap-allocated from static strings. StringBuilder's `to_string` correctly applies `mn_tag_heap` on the transferred buffer. Callers (including `__mn_str_free`) correctly untag before dereferencing. **No ABI issue.**

## Score justification

9/10 — ABI is stable within the arc. The init parameter reinterpretation is benign. The LLVM frame layout dependency is documented as a known coupling. StringBuilder ABI is clean.
