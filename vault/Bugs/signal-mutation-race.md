---
severity: high
found: "[[v4.26.0]]"
fixed: "[[v4.28.0]]"
status: fixed
tags: [bug, high, concurrency, signals, race-condition]
---

# Signal Value Mutation Race

Signal value reads, writes, and in-place mutations (`signal.mutate(fn)`) were performed without holding any lock. Concurrent threads could observe torn reads on multi-word values or interleave a mutate callback with a direct write, producing corrupted signal state.

## Root Cause
The C runtime `mapanare_signal_t` stored values behind a plain pointer with no synchronization primitive. The original single-threaded agent model never needed locking, but once signals were shared across agent threads (v4.12.0+), the data race became exploitable.

## Fix
Added a per-signal mutex in `runtime/native/mapanare_runtime.c`. All read, write, and mutate operations acquire the lock. Batched subscriber notifications are dispatched after the lock is released to avoid holding it during callbacks. Fixed in v4.28.0 as part of the concurrency hardening pass.
