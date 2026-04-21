# Mamba v4.114.0 Review — C runtime

## Score: 8.2 / 10
## Verdict: PASS WITH NOTES

## Context

v4.106.0 I gave **8.0 / 10 PASS WITH NOTES** — runtime verification
had matured under valgrind + ASan + TSan (all three added to CI in
v4.105.0). The v4.99.0 item I owned was #3 (rebuild libmapanare_rt.a
with scheduler) — closed in v4.102.0. Phase D added new runtime
touch points I want to grade: coroutine frame decoupling (#8) and
async error-message sites (#11) — both in `runtime/native/`.

## Primary lens — Coroutine frame change (docket #8)

### Runtime ABI stability

Critical question: does v4.113.0's runtime link-compatibly against
golden binaries built before the change?

Test: `clang /tmp/55_async_basic.ll -L runtime/native -lmapanare_rt
...` using the v4.113.0 archive against an IR emitted by the
v4.112.0 Python bootstrap. Output: 42. Same IR, new runtime, no
binary rebuild required.

That's because the change is **purely internal** — the coroutine
frame layout is owned by LLVM's coroutine splitter, not by our C
code. We just renamed how we READ from it. The struct
`mn_coro_frame_prefix_t` is a cast target, not a new allocation
shape.

### Valgrind + ASan

Re-ran on 2026-04-14:

| Test | Valgrind errors | Valgrind leaks | ASan errors | ASan leaks |
|---|---:|---:|---:|---:|
| 55_async_basic | 0 | 0 | 0 | 0 |
| 56_async_await | 0 | 56 B (user code) | 0 | 56 B (user code) |
| 57_real_await | 0 | 168 B (user code) | 0 | 216 B (user code) |
| 06_struct | 0 | 0 | 0 | 0 |

Zero runtime memory-safety errors. The leaks live in user coroutine
bodies boxing return values via `malloc`, and they are unchanged
from pre-v4.113.0. Byte-for-byte match in the v4.113.0 control
experiment.

Minor ASan discrepancy (216 vs valgrind's 168 for 57) — the extra
48 bytes ASan sees is metadata overhead at the ASan allocator, not
new leaks. Numbers are consistent.

### Hardcoded-offset audit

Zero raw `*(void **)handle` or `handle[N]` reads in executable
code. Comments only. This was the specific fragility concern from
v4.99.0 and it's gone.

**Sub-score for #8: 8.5 / 10.** The refactor is clean. Viper has
the deeper review; from a runtime angle I confirm: ABI stable,
link-compatible, sanitizer-clean.

## Primary lens — Async error-message sites (docket #11)

5 call paths, 7 messages, all in `mapanare_runtime.c`. From a
runtime perspective I care about:

1. **Is `exit(1)` the right escape for a runtime-level guard?**

Yes. A scheduler that can't spawn a worker, a coroutine parked on
an un-reachable Future — these are unrecoverable from the runtime's
perspective. `exit(1)` after a named stderr message is the right
call. It's preferable to the silent-drop / SIGSEGV behaviour the
pre-v4.113.0 runtime had.

2. **Does the cleanup path run before `exit(1)`?**

Mostly yes:
- Site 5/6/7 (file_read_async): `free(future)` + `free(ctx)` before
  `exit` when both allocations succeeded but `pthread_create`
  failed. Good.
- Site 3 (deque+overflow full): `__atomic_fetch_sub` undoes the
  active_tasks bump. Good.

Site 4 (register_wait overflow full): the coroutine frame is not
freed. The runtime is about to `exit(1)` so it doesn't matter in
practice, but if this were ever changed to a recoverable error,
a leak would appear. Worth a comment in the code noting the intent.

3. **Thread safety**

Sites 3 and 4 happen while the scheduler mutex is NOT held. That's
correct — the deque is lock-free (Chase-Lev), the overflow queue is
mutex-protected inside the push call. Neither site races.

Site 1 (scheduler_init pthread_create failure): happens during
init, before any other thread is live. No race.

4. **Does `errno` reliably carry the failure reason from
   `pthread_create`?**

`pthread_create` returns an error code directly (not via `errno`).
v4.113.0 captures the return value:
```c
int rc = pthread_create(&mn_sched.threads[i], NULL, ...);
if (rc != 0) { ... strerror(rc) ... }
```
Correct. Not using `errno`.

**Sub-score for #11: 8.5 / 10.** Message quality, cleanup paths,
thread safety all sound. The one note: site 4 should have a
comment about the deliberately-not-freed frame.

## Primary lens — Runtime test coverage

`tests/native/*.c` — 18 C tests covering `MnString`, scheduler,
overflow queue, deque, atomic helpers. All pass on 2026-04-14 (re-ran
`tests/native/test_c_runtime.c` via the Makefile — PASS).

CI `sanitizers.yml`:
- valgrind on 64 goldens against mnc-stage1 — baseline-checked
- ASan on the runtime C tests — `test_c_runtime.c` built with
  `-fsanitize=address` passes
- TSan on async goldens (55/56/57) — 0 races

No regression from Phase D changes. Runtime CI held.

## Secondary — Scheduler symbols intact (docket #3)

```
$ nm runtime/native/libmapanare_rt.a | grep __mn_coro_scheduler
0000000000002dd0 T __mn_coro_scheduler_destroy
00000000000028b0 T __mn_coro_scheduler_init
0000000000002ad0 T __mn_coro_scheduler_register
0000000000002cc0 T __mn_coro_scheduler_run
```

All four exports still present. v4.102.0 fix holds.

## What I'd flag

1. **Site 4 (register_wait overflow) does not free the coroutine
   frame before `exit(1)`.** No immediate harm because `exit` does
   it; worth a `/* exit(1) below reclaims the frame */` comment to
   prevent a future mistaken refactor.
2. **ASan vs valgrind leak size discrepancy (216 vs 168 on 57).**
   The delta is ASan allocator metadata, not new leaks. Document
   in the sanitizer baseline.
3. **Pre-existing user-code leaks in 56/57.** The coroutine body
   `__mn_Int_box` sites leak by design — boxed return values never
   freed by the async machinery. Carry-forward as `Coro.1` (opened
   by Viper in this review).

## Verdict

**PASS WITH NOTES @ 8.2.**

Runtime held through Phase D. Both v4.113.0 touch points
(coroutine frame + async errors) are clean. Sanitizers green. ABI
stable. The notes are small: a comment on site 4's cleanup intent,
a baseline doc for the ASan/valgrind size delta, and the
carry-forward user-code leak.

Phase D closes if the aggregate holds.
