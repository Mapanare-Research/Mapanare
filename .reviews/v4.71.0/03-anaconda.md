# Anaconda — Toolchain Lens

**Grade: 8/10** | **Verdict: PASS WITH NOTES**

## Assessment

The toolchain integration is clean. The emitter conditionally declares coro
intrinsics only when async fns are present. The `presplitcoroutine` attribute
is the correct mechanism for LLVM to recognize coroutines. No explicit
`opt -passes=coro-*` invocation needed — the standard pipeline handles it.

## Specific findings

1. **PASS**: Conditional intrinsic declarations — only emitted when `any(f.is_async)`.
   No dead declarations in sync-only modules.
2. **PASS**: `malloc`/`free` auto-declared via `_decl_fn` for async modules.
3. **NOTE**: The `coro.end` call returns `i1`, but the emitter calls it as
   `call i1 @llvm.coro.end(...)`. The return value is unused. Minor — LLVM
   accepts this, but `call void` would be cleaner if the result is discarded.
   Actually, `coro.end` does return `i1` in LLVM 17+. Verify the LLVM version
   target.
4. **NOTE**: No CI test compiles an async fn through the full pipeline
   (`emit-llvm` → `llvm-as` → `opt` → `llc`). The tests verify IR string
   patterns but don't invoke LLVM tools. Add a pipeline integration test
   in Arc 9.
5. **PASS**: Delta review from v4.68.0 was properly executed with 3 reviewers.
