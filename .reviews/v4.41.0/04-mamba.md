# Mamba -- C/Runtime Review of Mapanare v4.41.0 (Arc 2 Close)

**Reviewer:** Mamba
**Personality:** The C Minimalist -- terse, brutal, "delete this"
**Previous Version Reviewed:** v4.36.0 (PASS, 9.5/10, confidence 9/10)
**Verdict:** PASS
**Score:** 9.5 / 10
**Confidence:** 10 / 10

**Files reviewed:**
- `runtime/native/mapanare_core.c` (3,009 lines -- unchanged since v4.36.0)
- `runtime/native/mapanare_io.c` (1,717 lines -- unchanged)
- `runtime/native/mapanare_runtime.c` (1,369 lines -- unchanged)
- `runtime/native/mapanare_gpu.c` (2,029 lines -- unchanged)
- `runtime/native/mapanare_gpu_builtins.c` (264 lines -- unchanged)
- `runtime/native/mapanare_db.c` (877 lines -- unchanged)
- `runtime/native/mapanare_html.c` (799 lines -- unchanged)
- `runtime/native/mapanare_internal.h` (63 lines -- unchanged)
- `mapanare/lsp/server.py` (lines 182-190, `threading.Timer` debounce)
- `mapanare/lsp/diagnostics.py` (115 lines, semantic recheck)
- `.reviews/CARRY_FORWARD.md`
- `.reviews/v4.41.0/PRE_PANEL_AUDIT.md`
- `.reviews/v4.41.0/MEASUREMENTS.md`

## Executive Summary

Zero runtime changes. Every C file is byte-identical to v4.36.0.
10,127 lines across 7 `.c` files + 1 header. `git diff` between the
v4.36.0 commit and HEAD produces empty output for `runtime/native/`.
This is what an LSP-only arc should look like from the runtime side:
nothing touched, nothing broken.

The only item worth examining is the `threading.Timer` debounce in
`mapanare/lsp/server.py:187`. It spawns a daemon thread per keystroke
(cancelled and replaced on subsequent keystrokes within the 300ms
window). This is a Python `threading.Timer` -- a stdlib
`threading.Thread` subclass that sleeps then calls a callback. It does
**not** interact with the C runtime's thread pool, arena allocator,
agent scheduler, or signal system. The callback (`_debounced_recheck`)
calls `run_semantic_check` which re-parses and re-checks a single
source file in pure Python. No native code is invoked. No runtime
state is mutated. The debounce timer is entirely within the LSP
server's Python process and has zero coupling to any C runtime
primitive.

Score holds at 9.5. The 0.5 dock is the same four items from v4.36.0.
None were addressed this arc (expected -- this was an LSP arc). None
regressed.

## Non-Regression Verification

| File | v4.36.0 lines | v4.41.0 lines | Delta |
|------|---------------|---------------|-------|
| `mapanare_core.c` | 3,009 | 3,009 | 0 |
| `mapanare_io.c` | 1,717 | 1,717 | 0 |
| `mapanare_runtime.c` | 1,369 | 1,369 | 0 |
| `mapanare_gpu.c` | 2,029 | 2,029 | 0 |
| `mapanare_gpu_builtins.c` | 264 | 264 | 0 |
| `mapanare_db.c` | 877 | 877 | 0 |
| `mapanare_html.c` | 799 | 799 | 0 |
| `mapanare_internal.h` | 63 | 63 | 0 |
| **Total** | **10,127** | **10,127** | **0** |

Byte-identical. Confirmed via `git diff`.

## threading.Timer Analysis

`server.py:182-190`:

```python
import threading
old_timer = _debounce_timers.pop(uri, None)
if old_timer is not None and hasattr(old_timer, "cancel"):
    old_timer.cancel()
timer = threading.Timer(_DEBOUNCE_MS / 1000.0, _debounced_recheck, args=[uri])
timer.daemon = True
_debounce_timers[uri] = timer
timer.start()
```

**Does this interact with the runtime's thread pool?** No.

- The C runtime thread pool (`mapanare_core.c`) uses `pthread_create`
  with work-stealing queues and is only activated by compiled Mapanare
  programs that spawn agents or use parallel primitives.
- The LSP server is a Python process using `pygls`. It never calls
  `__mn_alloc`, never spawns agents, never touches signal state.
- `threading.Timer` is a Python-only construct. The callback
  (`_debounced_recheck` at line 62) reads from a Python dict
  (`_sources`), calls `run_semantic_check` (which imports
  `mapanare.parser` and `mapanare.semantic` -- both pure Python), and
  publishes diagnostics via the `pygls` server object.
- The `timer.daemon = True` ensures the timer thread dies with the
  LSP server process. No cleanup needed.

**One minor observation:** `_debounce_timers` is a plain `dict`, not a
`threading.Lock`-guarded dict. The LSP server is single-threaded for
request dispatch (pygls uses an event loop), but the timer callback
fires on a separate thread and reads `_sources` without locking. If
`on_change` fires while `_debounced_recheck` is reading `_sources`,
the dict mutation is not atomic in CPython for all operations (though
`.get()` on a string key is effectively atomic due to the GIL). This
is safe in practice under CPython's GIL but would be a data race
under a no-GIL Python (3.13t+). Not a runtime issue -- purely a
Python-side observation. Noise-level for now.

## Carry-Forward Items 49 and 50

### Item 49: Drop-glue skip-struct-ret (10th cycle)

`mapanare/emit_llvm_text.py:1093-1099`. Still present. The early
return at line 1098 still short-circuits drop-glue for struct returns
containing `ptr` fields. Unchanged from v4.36.0. This is an emitter
item, not a runtime item. Carry forward.

### Item 50: Agent destroy drain-under-contention (4th cycle)

`mapanare_runtime.c:684-696`. Still present. The `message_dtor`
drain loop is intact. The contention edge case (producer pushing
during destroy without `inbox_producer_lock`) is unchanged.
`mapanare_agent_destroy` still does not acquire the producer lock
before draining. Carry forward.

## Carry-Forward Queue (Mamba-owned)

| # | Item | Severity | Cycles | Status | Notes |
|---|------|----------|--------|--------|-------|
| M1 | `__mn_signal_get` lockless read | MEDIUM | 4 | OPEN | `mapanare_core.c:2014-2026`. No change. |
| M2 | `mn_signal_propagate` recursive | MEDIUM | 8 | OPEN | `mapanare_core.c:2201-2247`. No change. |
| L1 | `mn_arena_block_new` malloc+memset | LOW | 9 | OPEN | `mapanare_core.c:187-198`. No change. |
| L2 | db/html handle tables unguarded | LOW | 4 | OPEN | No change. |
| L3 | `g_argc`/`g_argv` non-atomic | LOW | 4 | OPEN | Benign. No change. |
| 49 | Drop-glue skip-struct-ret | LOW | 10 | OPEN | Emitter, not runtime. |
| 50 | Agent destroy drain-under-contention | LOW | 4 | OPEN | Core leak fixed; contention edge remains. |

All cycle counts incremented by 1 from v4.36.0. None addressed this
arc (expected). None regressed.

## Verdict

**PASS.** Zero runtime delta. The LSP debounce timer does not interact
with the C runtime. All carry-forward items are still tracked and
unchanged. The runtime remains at 10,127 lines, in the best shape it
has been in since the project started. Nothing to fix. Nothing broke.
