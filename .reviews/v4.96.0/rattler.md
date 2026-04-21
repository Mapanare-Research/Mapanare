# Rattler — LLVM Review (Arc 13)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

### Real suspension emission (v4.92.0)

The `_do_await_suspend` rewrite correctly implements the three-phase pattern from DESIGN.md §4.7.2:

1. **Fast-path check:** GEP into future state byte, icmp eq 1, branch to ready if already done. Correct — avoids unnecessary suspension for already-completed futures.

2. **Drive-once:** Resume the inner coroutine once via `coro.resume(handle)`, then re-check. This handles the common case where the inner coroutine completes in a single step (e.g., `async fn compute() -> Int { return 42 }`). Correct.

3. **Real suspend:** If still pending after drive-once, emit `__mn_coro_register_wait(handle, future)` + `coro.save` + `coro.suspend` + switch. The switch targets are `coro.ret` (default), resume label (i8 0), `coro.cleanup` (i8 1). This matches the LLVM switched-resume ABI exactly.

**Async return type fix:** The `_sigs` dictionary now maps async functions to `ptr` return type instead of their declared type. This is essential — without it, callers would try to load the Future as `i64`, causing type mismatches. Verified in all 5 golden tests.

**Ret rewriting in non-MIR blocks:** The extension to rewrite `ret` instructions in emitter-generated blocks (await.ready, drop glue) was necessary because the original code only processed MIR labels. This is a correctness fix, not an optimization.

### Concern: presplitcoroutine + multi-threaded resume

The `presplitcoroutine` attribute tells LLVM's CoroSplit pass to split the function. After splitting, the resume function pointer at frame offset 0 is valid for any thread to call. The scheduler correctly reads this pointer and calls it. However, **there is no guarantee that the resumed function's stack-spilled state is visible to the resuming thread** without a memory fence. The Chase-Lev deque uses `__ATOMIC_SEQ_CST` on steal, which provides the necessary fence. This is correct but subtle — should be documented.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Document fence requirement for cross-thread resume | MEDIUM | Correctness depends on deque's SEQ_CST |
| Multi-block callee inlining for async | LOW | Currently single-block only; async callees are multi-block |

## Score justification

8/10 — real suspension emission is correct and matches the design. The return type fix and ret rewriting are essential correctness patches. Deduction for the undocumented fence dependency in cross-thread resume.
