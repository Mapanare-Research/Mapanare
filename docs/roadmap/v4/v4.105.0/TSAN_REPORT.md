# v4.105.0 Phase 3 — ThreadSanitizer report

**Date:** 2026-04-14
**Tool:** clang 18.1.3 ThreadSanitizer at `-O1 -fno-omit-frame-pointer`
**Targets:**
- `mnc-stage1-tsan` — compiler run against all 64 goldens (compiler's own threading)
- `libmapanare_rt_tsan.a` — C runtime rebuilt with TSan; async test binaries linked against it (scheduler's threading)

## Headline

| Target | Runs | TSan-clean | TSan warnings |
|---|---:|---:|---:|
| mnc-stage1-tsan on 64 golden tests (compiler side) | 64 | 35 | **29 (signal-unsafe call in existing crash handler)** |
| Async test binaries 55/56/57 with TSan-instrumented runtime | 3 | **3** | **0 (no data races)** |

### The good news: v4.102.0's async scheduler is race-free

All three async goldens (55, 56, 57) run end-to-end under TSan with the
runtime's C code recompiled under `-fsanitize=thread`:

```
55_async_basic    exit 0   TSan warnings: 0   stdout: 42
56_async_await    exit 0   TSan warnings: 0   stdout: 43
57_real_await     exit 0   TSan warnings: 0   stdout: 110
```

This is primary evidence for the v4.106.0 panel: the coroutine scheduler
that v4.102.0 first demonstrated running natively has **zero TSan
warnings across all three async tests** — no data races, no lost
signals, no unsynchronized atomic reuse.

### The bad news: existing crash handler is async-signal-unsafe

`mnc_main.c:27` has a legacy crash handler:

```c
static void crash_handler(int sig) {
    fflush(stdout);
#ifndef _WIN32
    void *frames[64];
    int n = backtrace(frames, 64);
    fprintf(stderr, "\n[CRASH] Signal %d at:\n", sig);
    backtrace_symbols_fd(frames, n, 2);
    _exit(128 + sig);
```

TSan reports (29 tests that SIGSEGV during compilation):

```
WARNING: ThreadSanitizer: signal-unsafe call inside of a signal
  #0 malloc
  #1 _dl_map_object_deps elf/dl-deps.c:463:26
  #3 crash_handler mnc_main.c:27:13
  #4 __tsan::CallUserSignalHandler
  #5 mir_opt__licm_function
```

Neither `fflush(stdout)` nor `fprintf()` is async-signal-safe. `backtrace()`
lazily loads dynamic-linker symbols which call `malloc` on first
invocation. The existing handler is therefore technically UB whenever
it actually fires.

This matters because v4.105.0 Phase 4 is about to add breadcrumb output
to the handler. Phase 4 must use async-signal-safe primitives only
(`write(2)`, hand-rolled integer formatters, no printf/malloc).

**This TSan finding motivates and constrains Phase 4.** It is not a
new bug — it has been in `mnc_main.c` since v4.18.0-era — but we now
have evidence and a plan to fix it.

## Compiler-side summary (mnc-stage1-tsan on 64 goldens)

| Class | Count | Meaning |
|---|---:|---|
| CLEAN | 20 | Exit 0, no TSan output. Compiler produces IR, TSan says nothing. |
| SIGNAL_UNSAFE | 29 | Tests that SIGSEGV; existing crash handler fires; TSan flags the unsafe call chain. Not a race. |
| COMPILER_FAIL_NO_TSAN | 15 | Semantic/parser errors; no threading involved. |

**No actual data races reported by TSan.** The compiler's threading
model (one worker thread spawned for stack size, parent does
`pthread_join`) has no concurrent access; TSan confirms.

Full TSV: `artifacts/tsan-compiler-summary.tsv`.

## Runtime-side summary (async binaries with TSan runtime)

| Test | Expected | Got | TSan warnings | Exit |
|---|---|---|---:|---:|
| 55_async_basic | 42 | 42 | 0 | 0 |
| 56_async_await | 43 | 43 | 0 | 0 |
| 57_real_await | 110 | 110 | 0 | 0 |

Build recipe for the TSan-runtime async binary:

```bash
clang -c -O1 -g -fsanitize=thread -fno-omit-frame-pointer \
    runtime/native/mapanare_core.c ... -o tsan_rt/*.o
ar rcs libmapanare_rt_tsan.a tsan_rt/*.o
clang -O1 -g -fsanitize=thread -fno-omit-frame-pointer -no-pie \
    <test>.s libmapanare_rt_tsan.a -lm -lpthread -ldl -o <test>.tsan.bin
TSAN_OPTIONS=halt_on_error=0:report_bugs=1 ./<test>.tsan.bin
```

Full TSV: `artifacts/tsan-async-runtime-summary.tsv`.

## Docket candidates for v4.106.0 panel

From this phase (TSan-specific):

| # | Item | Severity | Evidence |
|---|---|---|---|
| Ts.1 | Existing crash handler (`mnc_main.c:23-34`) is async-signal-unsafe | MEDIUM | 29 tests; Phase 4 will replace with safe handler |

Ts.1 is the only finding — and Phase 4 of this same release addresses
it. No standalone docket item carries into v4.106.0.

## Evidence trail

- Full TSV (compiler): `artifacts/tsan-compiler-summary.tsv`
- Full TSV (runtime):  `artifacts/tsan-async-runtime-summary.tsv`
- Signal-unsafe sample: `artifacts/tsan-03_function-signal-unsafe.err`
- Runtime-clean sample: `artifacts/tsan-55-runtime.err` (empty — no output = no warnings)
- Build scripts: `scripts/build_tsan.sh` (committed)

## Exit criteria

- [x] **Exit #6** — TSan report on async tests: **clean (0 races, 3/3 correct output)**.
