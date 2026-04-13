# Viper — Memory Safety Review (Arc 13)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

### Coroutine frame lifetimes under real suspension

When a coroutine suspends at a real `coro.suspend`, LLVM's CoroSplit spills live values to the heap-allocated coroutine frame. The frame remains valid until `coro.destroy` is called. The scheduler holds a pointer to the frame (via the task entry's `handle` field). As long as:

1. Only one thread resumes the frame at a time ✓ (deque ownership ensures this)
2. The frame is not freed while a thread holds a reference ✓ (destroy only called after done check)
3. The future's state byte is written with release semantics ✓ (`__atomic_store_n` with `__ATOMIC_RELEASE`)

...the frame lifetime is safe. **Verified.**

### Cross-thread ownership in the scheduler

The Chase-Lev deque guarantees that a stolen task is exclusively owned by the stealer (CAS ensures at-most-one-steal). After stealing, the worker owns the task and can resume it. The coroutine frame is touched by at most one thread at a time. **This is correct.**

However, `__mn_coro_register_wait` pushes to the overflow queue, which can be drained by any worker. If the coroutine has already been stolen and is being processed on thread A, and thread B drains a wait-registration for the same handle, there could be a double-enqueue. The current code doesn't check for duplicates. **This is a potential double-resume bug** if a coroutine registers a wait while it's already in a deque.

In practice, `__mn_coro_register_wait` is called from within the coroutine's own execution (just before `coro.suspend`), and the coroutine hasn't been re-enqueued yet (it's about to suspend). So the timing is safe: the wait registration happens before the suspend, and the task isn't re-enqueued until `mn_process_task` sees it's not done. But this invariant is implicit, not enforced.

### StringBuilder memory safety

`__mn_sb_to_string` transfers the buffer pointer and zeros the builder. After transfer, the builder is consumed — calling `sb_append` on a zeroed builder would `__mn_alloc(0)` (since `cap == 0`), grow to default, and continue safely. No use-after-free. **Safe.**

`__mn_sb_destroy` checks `buf != NULL` before freeing. Safe for double-destroy (second call is a no-op). **Safe.**

### Cancel-before-complete

If a coroutine is destroyed (via `coro.destroy`) before it completes, the LLVM cleanup block frees the frame. The scheduler's `__mn_coro_scheduler_destroy` joins all threads but doesn't explicitly destroy pending coroutines. **This leaks frames for coroutines that never completed.** Not a safety issue (no UAF), but a resource leak.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Enforce single-enqueue invariant | MEDIUM | Implicit timing correctness, not enforced by code |
| Destroy pending coroutines on scheduler shutdown | MEDIUM | Currently leaks frames for incomplete coroutines |
| Double-resume detection (debug mode) | LOW | Assertion for coroutine resumed while already running |

## Score justification

8/10 — no use-after-free or data races in the shipped code. The frame lifetime model is correct under the implicit single-owner invariant. Deductions for the unenforced invariant and the incomplete-coroutine leak on shutdown.
