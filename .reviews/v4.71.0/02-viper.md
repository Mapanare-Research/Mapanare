# Viper — Memory Safety Lens

**Grade: 8/10** | **Verdict: PASS WITH NOTES**

## Assessment

Coroutine frames are heap-allocated. Future structs are heap-allocated. Two
`malloc` calls per async fn invocation with no matching `free` on the happy
path (only in `coro.cleanup`). The cleanup block is reachable via `coro.destroy`
— but who calls `coro.destroy`? The scheduler, which doesn't exist yet.

This is the known half-shipped state. The concern is whether the design
ensures cleanup *will* happen once the scheduler arrives.

## Specific findings

1. **NOTE**: The Future struct (`malloc(16)`) is never freed. The coroutine
   frame is freed in `coro.cleanup`, but the Future itself leaks. Arc 9
   must add `free(%future)` after the caller reads the result.
2. **NOTE**: The return value box (`malloc(8)`) leaks. The caller extracts
   the value via `load`, but nobody frees the box. This needs a free-after-read
   pattern in the scheduler or at the `await` extraction site (v4.72.0).
3. **PASS**: No use-after-free risk in the current code — the frame outlives
   the Future because the final suspend keeps the frame alive until `coro.destroy`.
4. **PASS**: Drop glue in the cleanup block is correctly positioned before
   `coro.free` per DESIGN.md §4.9.
