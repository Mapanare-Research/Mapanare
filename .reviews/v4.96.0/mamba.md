# Mamba — C Runtime Review (Arc 13)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### StringBuilder (v4.95.0) — MY FINDING FROM v4.51.0

This is the fix I flagged 45 releases ago. The implementation is clean:

**Structure:** `{char *buf, int64_t len, int64_t cap}` — standard triple. Uses the existing `__mn_alloc`/`__mn_free` allocator, which means StringBuilder allocations are profiled alongside everything else. Good.

**Growth strategy:** 2x exponential. `mn_sb_grow` doubles capacity until it fits. This gives amortized O(1) append with at most 2x memory overhead. For a 50KB string (the string_concat benchmark), this means ~14 reallocations instead of 10,000. Correct.

**Transfer ownership (`to_string`):** When `len == cap` (or close), the buffer pointer is transferred directly to MnString via `mn_tag_heap`. When significantly oversized (`cap > len * 2 + 1`), a tight realloc is performed. The builder is zeroed after transfer. This is the right design — avoids a copy in the common case, avoids memory waste in the edge case.

**AI stdlib refactoring:** `escape_json`, `messages_to_json`, `tools_to_json` all converted from `result = result + x` to `sb_append(sb, x)`. The refactoring is mechanical and correct. Each loop now does O(n) work instead of O(n^2).

**One concern:** `__mn_sb_append` calls `mn_untag(s.data)` to strip the heap tag before memcpy. This is correct for heap-allocated strings but **would crash on a null data pointer**. The function should check `s.data != NULL` before untagging. Currently safe because MnString's empty state has `data = NULL` and `len = 0`, and the early `if (s.len <= 0) return` guards against this. But it's fragile.

### Work-stealing scheduler (v4.93.0)

**Chase-Lev deque:** Textbook implementation. Power-of-2 size (1024), bottom/top indices with correct atomic orderings (relaxed for owner, acquire/SEQ_CST for stealer CAS). The `mn_deque_pop` handles the last-element race correctly (CAS on top, reset bottom on failure).

**Global overflow:** Mutex-protected ring buffer (4096 slots). Falls back when local deque is full. This is the right design for bursty spawns.

**Worker loop:** Pop local → pop overflow → steal random peer. Idle parking via `pthread_cond_timedwait` (1ms). No busy-wait. The 1ms timeout is a reasonable compromise between latency and CPU waste.

**Concern:** The `mn_coro_is_done` function reads the suspend index at `frame + 2*sizeof(void*)`. This is LLVM ABI-dependent — if CoroSplit changes the frame layout, this breaks silently. Should use `llvm.coro.done` instead. However, `llvm.coro.done` is an LLVM intrinsic not callable from C. The byte-offset approach is the only practical option for a C scheduler. Acceptable with documentation.

### Async file I/O (v4.92.0)

Thread-based: spawn a pthread, read synchronously, set future to Ready with `__atomic_store_n` release. The release fence ensures the file content is visible to the scheduler thread that reads the future. Correct.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Guard sb_append against null data | LOW | Currently safe due to len check, but fragile |
| Document LLVM frame layout dependency | MEDIUM | mn_coro_is_done reads raw bytes |

## Score justification

9/10 — StringBuilder is exactly what I asked for 45 releases ago. Clean implementation, correct growth, proper transfer. The AI stdlib refactoring eliminates the pathology. The scheduler is well-designed. Minor fragility concerns documented but not blocking.
