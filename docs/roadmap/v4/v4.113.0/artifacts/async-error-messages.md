# v4.113.0 — Async Error Messages (docket #11)

Boa's v4.99.0 review: *"tell the user what failed in the async
pipeline, not just that something failed."* Four async failure modes
in `runtime/native/mapanare_runtime.c` had silent-drop or generic
behaviour; v4.113.0 replaces each with a specific stderr message +
`exit(1)`.

## Sites updated

### 1. `__mn_coro_scheduler_init` — worker `pthread_create` failure

The return code was discarded. If the per-user thread limit
(`RLIMIT_NPROC`) or the stack-allocation budget was exhausted, the
scheduler would report `num_workers = N` while only running fewer
threads. Every task-steal loop would find empty deques and the
program would hang.

**New:**

```
mapanare: async runtime: failed to spawn worker thread K of N:
<strerror> (errno E). Likely causes: RLIMIT_NPROC exhausted, or
ENOMEM at pthread stack allocation. Try lowering
MAPANARE_ASYNC_THREADS or raising `ulimit -u`.
```

### 2. `__mn_coro_scheduler_register` — scheduler-not-initialised guard

Prior to v4.113.0, spawning a coroutine before
`__mn_coro_scheduler_init` pushed into a zero-initialised deque
(`num_workers = 0`). `__mn_coro_scheduler_run` then spun forever
waiting for `active_tasks` to drain.

**New:** early-return with a message that names the exact missing
init call and the emitter file where the call should be generated.

### 3. `__mn_coro_scheduler_register` — queue-full silent drop

If both the worker-0 deque and the global overflow queue were full,
the task was silently dropped but `active_tasks` had already been
incremented — the scheduler would wait forever for a task it never
held.

**New:** decrement `active_tasks`, report both capacities, point at
the usage pattern (too many spawns without awaits).

### 4. `__mn_coro_register_wait` — overflow-full during suspend

The most damaging silent failure: a coroutine suspended at `await`,
and its resume slot was dropped. The future would resolve but
nothing would restart the awaiter — a permanent hang.

**New:** name the coroutine handle, the awaited Future address, and
the overflow capacity.

### 5. `__mn_file_read_async` — allocation + thread-spawn failures

All three failure modes were unchecked. Each now gets a specific
message naming the failed allocation (Future vs. context vs.
pthread) and the errno.

## Verification

Built the runtime at `-O2`, linked the three async goldens
(`55_async_basic`, `56_async_await`, `57_real_await`) through the
Python bootstrap, re-ran natively → outputs still 42, 43, 110.

Manually triggered site #2 by calling `__mn_coro_scheduler_register`
before `__mn_coro_scheduler_init`:

```
$ /tmp/test_scheduler_uninit
mapanare: async runtime: cannot spawn task — scheduler not
initialised. The main() emitted by the compiler should call
__mn_coro_scheduler_init() before any async function runs; ...
$ echo $?
1
```

Sites #1, #3, #4, #5 are all unreachable in practice on a healthy
host (they require RLIMIT_NPROC exhaustion, queue overflow under
thousands of concurrent spawns, or OOM). The guards exist so that
when they *do* trigger, the failure is named and exit is deterministic
instead of a silent hang or segfault.

## Count

Five distinct failure modes with improved messages (docket #11 asked
for at least three).
