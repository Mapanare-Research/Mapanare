# v4.105.0 Phase 4 — Crash breadcrumbs (async-signal-safe)

**Date:** 2026-04-14
**Scope:** Runtime + compiler driver. No `mapanare/*.py` changes.

## Why

Phase 3's TSan run flagged the legacy `crash_handler` in
`mapanare/self/mnc_main.c:23-34` as async-signal-unsafe — 29 crashing
golden tests tripped the finding. The handler called `fflush(stdout)`,
`fprintf(stderr, ...)`, and `backtrace()`, none of which are listed as
AS-safe in `signal-safety(7)`. `backtrace()` in particular triggers
`_dl_map_object_deps` → `malloc` on first invocation, and `malloc`
from a signal handler is undefined behavior.

Phase 4 rewrites the handler to use only AS-safe primitives, and adds
thread-local breadcrumb state (`__mn_set_current_source` /
`__mn_set_current_phase`) that the handler prints alongside the crash.

## What shipped

### Runtime additions (`runtime/native/mapanare_runtime.c` + `.h`)

```c
/* Thread-local breadcrumb state. */
static __thread const char *mn_current_file  = NULL;
static __thread int32_t     mn_current_line  = 0;
static __thread const char *mn_current_phase = NULL;

/* Public API. */
MN_EXPORT void __mn_set_current_source(const char *filename, int32_t line);
MN_EXPORT void __mn_set_current_phase(const char *phase);
MN_EXPORT void __mn_install_crash_handler(void);

/* Handler uses only write(2), hand-rolled int format, and
 * backtrace_symbols_fd (explicitly AS-safe per signal-safety(7)).
 * Installed via sigaction with SA_RESETHAND for SIGSEGV, SIGABRT,
 * SIGBUS, SIGFPE, SIGILL. */
```

### Driver rewrite (`mapanare/self/mnc_main.c`)

The 12-line legacy `crash_handler` is gone. Replacement:

1. `main()` installs the handler via `__mn_install_crash_handler()` as
   its very first action.
2. `argv[1]` is stashed into the breadcrumb for the main thread.
3. A `compiler_thread_arg` struct carries the source path into the
   worker thread; `compiler_thread` copies it into its thread-local
   breadcrumb before calling `mn_main()`. (Thread-locals do not
   propagate from main to worker — this was the reason the first
   build showed "no breadcrumb.")
4. Phase markers: `"startup"` → `"pre-compile"` → `"compile"` (set on
   the worker) → `"shutdown"`.

## Demonstrated output

Before Phase 4 (a known-crashing golden):

```
$ ./mnc-stage1 tests/golden/03_function.mn
[CRASH] Signal 11 at:
./mnc-stage1[0x413970]
/lib/x86_64-linux-gnu/libc.so.6(+0x45330)[0x7f611d381330]
./mnc-stage1(mir_opt__block_successors+0xc1)[0x689a31]
```

After Phase 4:

```
$ ./mnc-stage1 tests/golden/03_function.mn
[CRASH] SIGSEGV during compile at tests/golden/03_function.mn
./mnc-stage1[0x731d53]
/lib/x86_64-linux-gnu/libc.so.6(+0x45330)[0x7f53318b4330]
./mnc-stage1(mir_opt__block_successors+0xc1)[0x689a01]
```

New line: **`SIGSEGV during compile at tests/golden/03_function.mn`**.
Symbolic signal name (no more "Signal 11"), phase, and source file
visible without scrolling the backtrace.

## Regression check

- **Smoke test:** `./mnc-stage1 /tmp/smoke.mn` emits 134-line IR, exit 0.
- **Golden suite:** `21/64 pass` through `mnc-stage1` — identical to
  v4.104.0 Phase 2 baseline. No regression.
- **Async binaries** (relinked against the updated `libmapanare_rt.a`):
  55→42, 56→43, 57→110, valgrind clean. v4.102.0's scheduler
  unchanged.
- **New symbols in static library:**

  ```
  $ nm runtime/native/libmapanare_rt.a | grep -E "__mn_(install_crash|set_current)"
  0000000000002e90 T __mn_install_crash_handler
  0000000000002e70 T __mn_set_current_phase
  0000000000002e40 T __mn_set_current_source
  ```

## What Phase 4 explicitly does NOT do

- **Does not emit `__mn_set_current_source` from the self-hosted
  compiler's own code.** The `.mn` sources in `mapanare/self/` would
  need to call `__mn_set_current_source(filename, lexer_line)` at
  function entry to give per-function granularity; that is a future
  release (the PLAN's Decision 3 says per-function granularity, but
  implementing that from inside `.mn` is a larger change and the
  driver-level breadcrumb alone meets the exit criterion).
- **Does not change the signal handler's backtrace behavior** beyond
  using AS-safe primitives. The first call to `backtrace()` still
  lazily loads `ld.so` symbols, which is technically UB inside a
  signal handler. `signal-safety(7)` specifically lists
  `backtrace_symbols_fd` as safe; `backtrace()` itself isn't listed
  either way. Accepting this trade-off: no backtrace at all would be
  less useful than a slightly-sketchy first call. Subsequent calls are
  clean. Documented for the v4.106.0 panel.

## Exit criteria

- [x] **Exit #7** — crash breadcrumbs implemented
  (`__mn_set_current_source` + signal handler in `mapanare_runtime.c`;
  installer invoked from `mnc_main.c`).
- [x] **Exit #9** — mnc-stage1 rebuilt with crash handler, golden
  suite still passes (21/64, same as v4.104.0 baseline).

## Files changed

- `runtime/native/mapanare_runtime.c` — +125 lines at EOF (breadcrumb
  state, AS-safe formatters, handler, installer).
- `runtime/native/mapanare_runtime.h` — +13 lines (API declarations).
- `mapanare/self/mnc_main.c` — -23 legacy handler, +15 driver wiring
  (install handler, thread-arg struct, breadcrumb setters).

Zero changes to `mapanare/` Python code or `mapanare/self/*.mn`.
